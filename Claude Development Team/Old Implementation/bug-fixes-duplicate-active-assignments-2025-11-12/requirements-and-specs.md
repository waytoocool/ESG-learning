# Bug Fix: Duplicate Active Assignments in Versioning System

## Issue ID
BUG-2025-11-12-001

## Discovery Date
2025-11-12 during Phase 1.1 edge case testing of assignment versioning system

## Severity
**CRITICAL** - Database constraint violation, data integrity issue

---

## Problem Statement

The assignment versioning system is creating multiple active assignments for the same field-entity-company combination, violating the single-active-assignment business rule. This occurs when:
1. A new version is created (v2) from an existing assignment (v1)
2. v1 is not properly marked as 'superseded'
3. v1 remains 'active' while v2 or v3 is also 'active'

### Expected Behavior
For any given field-entity-company combination:
- **Exactly ONE** assignment should have `series_status = 'active'`
- All previous versions should have `series_status = 'superseded'`
- Inactive assignments should have `series_status = 'inactive'`

### Actual Behavior
Multiple assignments have `series_status = 'active'` for the same field-entity-company combination.

---

## Evidence & Impact

### Database Evidence

**Test Case**: Field `0f944ca1-4052-45c8-8e9e-3fbcf84ba44c`, Entity `3`

```sql
-- Query executed
SELECT id, series_version, series_status, assigned_topic_id,
       datetime(assigned_date, 'localtime') as assigned_date,
       (SELECT name FROM topics WHERE topic_id = data_point_assignments.assigned_topic_id) as topic_name
FROM data_point_assignments
WHERE field_id = '0f944ca1-4052-45c8-8e9e-3fbcf84ba44c' AND entity_id = 3
ORDER BY assigned_date DESC;

-- Results
v3: 738634c8... | version=3 | status=active     | Energy Management | 2025-11-12 18:37:33
v2: 8572ae9d... | version=2 | status=superseded | Social Impact     | 2025-11-12 12:36:49
v1: 80e7351b... | version=1 | status=active     | Energy Management | 2025-11-09 22:52:23
                                       ^^^^^^ VIOLATION - should be 'superseded'
```

**Constraint Violation Query:**
```sql
SELECT field_id, entity_id, COUNT(*) as active_count
FROM data_point_assignments
WHERE series_status = 'active' AND field_id = '0f944ca1-4052-45c8-8e9e-3fbcf84ba44c' AND entity_id = 3
GROUP BY field_id, entity_id
HAVING COUNT(*) > 1;

-- Result: 1 row (VIOLATION DETECTED - 2 active assignments)
```

### Impact Assessment

| Impact Area | Severity | Description |
|-------------|----------|-------------|
| Data Integrity | **CRITICAL** | Database constraint violated, core business rule broken |
| User Experience | **HIGH** | Users may see incorrect assignment counts, duplicate data points |
| Reporting | **HIGH** | Analytics queries may return inflated counts |
| System Stability | **MEDIUM** | Future versioning operations may fail or cascade errors |
| Performance | **LOW** | Minimal performance impact currently |

---

## Root Cause Analysis

### Primary Causes

#### 1. **Two-Phase Flush Not Applied to v1→v2 Transition**

The Two-Phase Flush fix was implemented in `assignment_versioning.py:105-113` but v1 was not superseded when v2 was created. This indicates:
- Either the fix wasn't in place during v1→v2 transition
- Or there's a code path that bypasses the versioning service

#### 2. **v1 Was Modified After Supersession**

Evidence shows v1's `assigned_topic_id` changed:
- Original: `7a523072-4b63-4ce0-940d-fa966a786a0a` (Water Management)
- Current: `35b943f2-ba1e-4983-a862-790408a6f191` (Energy Management)

This suggests v1 was accessed and modified directly, potentially by:
- A configuration update that didn't check version status
- A database operation that bypassed ORM validations
- Manual database modification (unlikely but possible)

#### 3. **Configure Fields Query Scope Issue**

Location: `app/routes/admin_assignDataPoints_Additional.py:115-120`

```python
# Current implementation
all_assignments = DataPointAssignment.query.filter(
    and_(
        DataPointAssignment.field_id == field_id,
        DataPointAssignment.company_id == company_id
    )
).all()  # ← Finds ALL assignments for field across ALL entities

# Then processes ALL active assignments
active_assignments = [a for a in all_assignments if a.series_status == 'active']
```

**Issue**: If a field is assigned to multiple entities, configuration changes affect all of them. If old versions have incorrect 'active' status, they will be versioned again, perpetuating the issue.

---

## Affected Code Files

### Core Files
1. **`app/services/assignment_versioning.py`** (lines 98-164)
   - Two-Phase Flush implementation
   - Supersede operation (line 101-113)
   - New version creation (line 145-164)

2. **`app/routes/admin_assignDataPoints_Additional.py`** (lines 30-250)
   - `configure_fields` endpoint
   - Query for existing assignments (line 115-120)
   - Active assignment processing (line 131-170)

3. **`app/models/data_assignment.py`** (lines 384-459)
   - `validate_single_active_assignment` hook
   - Versioning context bypass mechanism

---

## Solution Requirements

### Must Have (P0)

1. **Database Cleanup**: Remove all duplicate active assignments
2. **Root Cause Fix**: Ensure v1 is properly superseded when v2 is created
3. **Validation Enhancement**: Add runtime checks for duplicate active assignments
4. **Logging**: Add detailed logging for all status transitions

### Should Have (P1)

5. **Database Constraint**: Add unique index to enforce single active assignment at database level
6. **Query Fix**: Ensure configure_fields only processes intended assignments
7. **Integration Tests**: Add tests for all versioning edge cases

### Nice to Have (P2)

8. **Monitoring**: Add alerts for constraint violations
9. **Admin Tool**: Create UI for detecting and fixing orphaned active assignments
10. **Audit Trail**: Log all status changes to audit_log table

---

## Proposed Solution

### Phase 1: Immediate Cleanup (Priority: P0)

```python
# Cleanup script to fix existing duplicates
def fix_duplicate_active_assignments():
    """
    For each field-entity-company with multiple active assignments:
    1. Identify the highest version number
    2. Keep that one as 'active'
    3. Mark all others as 'superseded'
    """
    duplicates = db.session.execute(text("""
        SELECT field_id, entity_id, company_id,
               GROUP_CONCAT(id || ':' || series_version ORDER BY series_version) as versions
        FROM data_point_assignments
        WHERE series_status = 'active'
        GROUP BY field_id, entity_id, company_id
        HAVING COUNT(*) > 1
    """))

    for dup in duplicates:
        # Parse versions, keep highest, mark others as superseded
        # ...
```

### Phase 2: Database Constraint (Priority: P1)

```sql
-- Add unique partial index (SQLite 3.8.0+)
CREATE UNIQUE INDEX idx_single_active_assignment
ON data_point_assignments(field_id, entity_id, company_id)
WHERE series_status = 'active';
```

### Phase 3: Code Fixes (Priority: P0)

#### Fix 1: Add Validation in configure_fields

```python
# Before processing, verify no duplicates exist
def validate_no_duplicate_actives(field_id, entity_id, company_id):
    count = DataPointAssignment.query.filter(
        and_(
            DataPointAssignment.field_id == field_id,
            DataPointAssignment.entity_id == entity_id,
            DataPointAssignment.company_id == company_id,
            DataPointAssignment.series_status == 'active'
        )
    ).count()

    if count > 1:
        raise ValueError(f"Duplicate active assignments detected: {count} found")
```

#### Fix 2: Enhanced Logging

```python
# In assignment_versioning.py, before and after supersede
current_app.logger.info(f"[VERSIONING] Before supersede: assignment={assignment_id}, status={current_assignment.series_status}")
current_assignment.series_status = 'superseded'
db.session.flush()
current_app.logger.info(f"[VERSIONING] After supersede flush: assignment={assignment_id}, new_status={current_assignment.series_status}")
```

---

## Testing Plan

### Test Cases

1. **Single Field, Single Entity**
   - Create v1 → Verify v1 active
   - Update config → Verify v2 active, v1 superseded
   - Update again → Verify v3 active, v1,v2 superseded

2. **Single Field, Multiple Entities**
   - Assign to 3 entities → Verify 3 active (one per entity)
   - Configure all → Verify still 3 active (new versions)
   - No cross-contamination between entities

3. **Rapid Changes**
   - 3 config changes within 5 seconds
   - Verify proper version sequence
   - No duplicate actives at any point

4. **Database Constraint**
   - Attempt to manually create duplicate active
   - Should fail with constraint violation

### Validation Queries

```sql
-- Run after each test
-- 1. Check for any duplicates
SELECT field_id, entity_id, company_id, COUNT(*) as active_count
FROM data_point_assignments
WHERE series_status = 'active'
GROUP BY field_id, entity_id, company_id
HAVING COUNT(*) > 1;
-- Expected: 0 rows

-- 2. Verify version sequences
SELECT field_id, entity_id, series_version, series_status
FROM data_point_assignments
WHERE field_id = ?
ORDER BY series_version;
-- Expected: Only highest version is active
```

---

## Success Criteria

1. ✅ All duplicate active assignments cleaned up
2. ✅ Database constraint prevents future duplicates
3. ✅ All edge case tests pass
4. ✅ No constraint violations in production data
5. ✅ Enhanced logging shows proper status transitions
6. ✅ Integration tests added and passing

---

## Timeline

- **Phase 1 (Immediate)**: Database cleanup - 30 minutes
- **Phase 2 (Same day)**: Add database constraint - 15 minutes
- **Phase 3 (Same day)**: Code fixes and testing - 2 hours
- **Phase 4 (Next day)**: Integration tests and monitoring - 3 hours

**Total Estimated Time**: 6 hours

---

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Cleanup breaks existing data | Low | High | Test on copy first, backup database |
| Constraint blocks legitimate operations | Medium | High | Thorough testing of all workflows |
| Performance impact from new index | Low | Low | Index is partial, minimal overhead |
| Other dormant bugs revealed | High | Medium | Continue edge case testing |

---

## Approval

- **Reported By**: Claude Code (Automated Testing)
- **Date**: 2025-11-12
- **Priority**: P0 (Critical)
- **Status**: Ready for Implementation

---

## Related Documents

- `CRITICAL-BUG-DUPLICATE-ACTIVE-ASSIGNMENTS.md` - Initial bug report
- `app/services/assignment_versioning.py` - Versioning service implementation
- `app/routes/admin_assignDataPoints_Additional.py` - Configure endpoint
