# Comprehensive Testing Plan: Assignment Versioning System
**Date Created**: 2025-11-12
**Testing Environment**: Live application with Firefox browser + Playwright MCP
**Database**: SQLite (instance/esg_data.db)
**Test Company**: test-company-alpha
**Admin User**: alice@alpha.com / admin123
**Status:** 🔄 READY FOR EXECUTION

---

## Executive Summary

This comprehensive testing plan validates the assignment versioning system through live browser-based testing with real-time database verification. It covers all edge cases including field configuration, entity assignment, deactivation, reactivation, and complex lifecycle scenarios. Each test includes UI actions via Firefox browser and database queries to verify backend state.

---

## Testing Objectives

1. **Verify Assignment Versioning Logic**: Ensure all configuration changes trigger correct versioning
2. **Database Integrity**: Validate data_series_id, series_version, and series_status consistency
3. **Edge Case Coverage**: Test complex scenarios that may break versioning
4. **User Experience**: Ensure UI reflects versioning changes accurately
5. **Data Isolation**: Verify tenant boundaries are maintained
6. **Lifecycle Management**: Test complete assignment lifecycle from creation to deletion
7. **Cross-Feature Integration**: Validate versioning with dimensional data, computed fields, etc.

---

## Pre-Test Setup

### Database Query Templates
```sql
-- View all assignments with versioning data
SELECT
    id,
    field_id,
    entity_id,
    data_series_id,
    series_version,
    series_status,
    frequency,
    start_date,
    end_date,
    is_active
FROM data_point_assignment
WHERE entity_id = ?
ORDER BY data_series_id, series_version;

-- Check for duplicate active assignments
SELECT
    data_series_id,
    field_id,
    entity_id,
    COUNT(*) as active_count
FROM data_point_assignment
WHERE series_status = 'active' AND is_active = 1
GROUP BY data_series_id, field_id, entity_id
HAVING COUNT(*) > 1;

-- View assignment history for a field
SELECT
    id,
    series_version,
    series_status,
    frequency,
    start_date,
    end_date,
    created_at,
    updated_at
FROM data_point_assignment
WHERE field_id = ?
ORDER BY series_version DESC;

-- Check versioning consistency
SELECT
    data_series_id,
    COUNT(DISTINCT series_version) as version_count,
    MAX(series_version) as latest_version,
    GROUP_CONCAT(series_status) as statuses
FROM data_point_assignment
GROUP BY data_series_id
HAVING COUNT(*) > 1;
```

### Environment Checklist
- [ ] Flask app running: `python3 run.py`
- [ ] Firefox MCP started: `npm run mcp:start` (use Firefox if Chrome busy)
- [ ] Database accessible: `sqlite3 instance/esg_data.db`
- [ ] Admin credentials verified: alice@alpha.com / admin123
- [ ] Database backup created: `cp instance/esg_data.db instance/esg_data.db.backup`

---

## Test Suite Overview

### Phase 1: Configuration Changes (Core Functionality)
**Purpose:** Test basic configuration changes work correctly

| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| 1.1 | Simple frequency change (Annual→Quarterly) | v1→v2, v1=superseded |
| 1.2 | Repeated frequency change (Quarterly→Monthly→Annual) | v2→v3→v4, forward progression |
| 1.3 | Change back to original (Annual→Quarterly→Annual) | v1→v2→v3, NEW v3 created |
| 1.4 | Rapid successive changes (A→B→C→D) | v1→v2→v3→v4→v5, all transitions |
| 1.5 | Multiple fields simultaneously | All fields version correctly |
| 1.6 | Change with inactive matching config | NEW version created, inactive stays inactive |
| 1.7 | Change with superseded matching config | NEW version created, superseded stays superseded |

### Phase 2: Multi-Entity Operations
**Purpose:** Test entity isolation and multi-entity scenarios

| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| 2.1 | Same field, 2 entities, separate configs | Independent version histories |
| 2.2 | Same field, 2 entities, same config change | Both version correctly, no interference |
| 2.3 | Config change affects only selected entities | Other entities unchanged |
| 2.4 | Add new entity with existing field | New v1 for new entity |
| 2.5 | Delete entity assignment | Specific entity only |

### Phase 3: Entity Assignment Operations
**Purpose:** Test adding fields to entities

| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| 3.1 | Assign new field to entity | Creates v1 (active) |
| 3.2 | Assign multiple fields to entity | All create v1 |
| 3.3 | Assign field to multiple entities | v1 for each entity |
| 3.4 | Assign already-assigned field | No duplicate, graceful handling |
| 3.5 | Assign with custom config | v1 has specified config |
| 3.6 | Assign computed field with dependencies | Dependencies assigned correctly |

### Phase 4: Deactivation Operations
**Purpose:** Test making assignments inactive

| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| 4.1 | Deactivate active assignment (no data) | v1 active→inactive directly |
| 4.2 | Deactivate active assignment (with data) | Create inactive v2, v1→superseded |
| 4.3 | Deactivate multiple assignments | All deactivate correctly |
| 4.4 | Deactivate computed field | Handle dependencies |
| 4.5 | Deactivate already inactive | No change, idempotent |

### Phase 5: Reactivation Operations
**Purpose:** Test bringing back inactive assignments

| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| 5.1 | Reactivate inactive (no data, no active exists) | Direct reactivation OK |
| 5.2 | Reactivate inactive (with data, no active exists) | Create new version |
| 5.3 | Reactivate when active exists | Block or error |
| 5.4 | Reactivate superseded | Should NOT reactivate |
| 5.5 | Reactivate multiple | All reactivate correctly |

### Phase 6: New Field Addition
**Purpose:** Test adding completely new fields

| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| 6.1 | Add new raw field | Field created, ready for assignment |
| 6.2 | Add new computed field | Field created with formula |
| 6.3 | Assign newly created field | v1 assignment created |
| 6.4 | Configure newly assigned field | v1→v2 correctly |

### Phase 7: Edge Cases & Stress Tests
**Purpose:** Test unusual scenarios and limits

| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| 7.1 | Configure with empty selection | Error or no-op |
| 7.2 | Configure with invalid config | Validation error |
| 7.3 | Concurrent config changes | Transaction isolation |
| 7.4 | Very high version number (v50→v51) | No overflow, continues |
| 7.5 | Duplicate version numbers exist | Auto-fix or error |
| 7.6 | Config change during data entry | Graceful handling |
| 7.7 | Rollback scenario | Database consistency |

### Phase 8: Version History Validation
**Purpose:** Validate version progression rules

| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| 8.1 | No gaps in version sequence | v1,v2,v3,v4 (no missing v3) |
| 8.2 | No duplicate versions | Each version unique per series |
| 8.3 | Exactly one active per field-entity | Database query confirms |
| 8.4 | Superseded never become active | Immutability check |
| 8.5 | Status transitions valid | Only allowed transitions occur |
| 8.6 | Version creation timestamps | Newer versions have later timestamps |

### Phase 9: Cross-Operation Testing
**Purpose:** Test operation sequences

| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| 9.1 | Assign→Configure→Deactivate→Reactivate | Full lifecycle works |
| 9.2 | Configure→Delete→Re-assign→Configure | Versions restart at v1 for new series |
| 9.3 | Multi-entity: Assign→Configure entity1→Configure entity2 | Isolation maintained |
| 9.4 | Computed field: Assign deps→Assign computed→Configure | Dependency chain intact |

### Phase 10: Database Consistency
**Purpose:** Validate database state

| Test ID | Check | Query |
|---------|-------|-------|
| 10.1 | No duplicate actives | COUNT(active) ≤ 1 per field-entity |
| 10.2 | Version sequences | No gaps, no duplicates |
| 10.3 | Referential integrity | All FKs valid |
| 10.4 | Status counts | active + superseded + inactive = total |
| 10.5 | Orphaned records | No assignments without fields/entities |

---

## Test Execution Plan

### Setup Phase (5 minutes)
1. Implement code fix
2. Restart Flask server
3. Document initial database state
4. Create test data snapshot

### Execution Phase (60-90 minutes)
1. **Phase 1-3:** Core functionality (30 min)
2. **Phase 4-6:** Lifecycle operations (20 min)
3. **Phase 7:** Edge cases (15 min)
4. **Phase 8-9:** Validation & sequences (15 min)
5. **Phase 10:** Database consistency (10 min)

### Documentation Phase (15 minutes)
1. Record all test results
2. Document any failures
3. Create summary report
4. Generate recommendations

---

## Test Data Requirements

### Initial State
```
Company: Test Company Alpha (ID=2)
Entities:
  - Entity 2: Alpha HQ (Office)
  - Entity 3: Alpha Factory (Manufacturing)

Fields (5):
  - 067d135a: Field A
  - 0f944ca1: Field B (Computed)
  - 43267341: Field C
  - a37da5a6: Field D
  - b27c0050: Field E

Initial Assignments:
  - Entity 3: All 5 fields assigned (various versions)
  - Entity 2: None or some fields
```

### Clean State Between Tests
- Option A: Use transactions and rollback
- Option B: Recreate database
- Option C: Archive and restore snapshots

---

## Expected Outcomes

### Version Progression Patterns

**Normal Configuration Change:**
```
Before: v4 (active, Quarterly)
Action: Change to Monthly
After: v5 (active, Monthly), v4 (superseded, Quarterly)
```

**Deactivation:**
```
Before: v3 (active)
Action: Deactivate
After: v3 (inactive) [if no data]
   OR: v4 (inactive), v3 (superseded) [if has data]
```

**Reactivation:**
```
Before: v2 (inactive), no active exists
Action: Reactivate
After: v3 (active), v2 (superseded) [if has data]
   OR: v2 (active) [if no data, direct reactivation]
```

### Status Transition Matrix

| From | To | Valid? | When |
|------|-----|--------|------|
| active | superseded | ✅ | New version created |
| active | inactive | ⚠️ | Only if no data & deactivating |
| inactive | active | ⚠️ | Only via reactivate, creates new version |
| inactive | superseded | ✅ | During reactivation with data |
| superseded | * | ❌ | NEVER - immutable |

---

## Failure Criteria

Any test fails if:
1. ❌ Duplicate active assignments created
2. ❌ Version numbers go backward
3. ❌ Superseded version changes status
4. ❌ HTTP 500 error
5. ❌ Database constraint violation
6. ❌ Wrong entity affected
7. ❌ Version gap or duplicate
8. ❌ Referential integrity violated

---

## Success Metrics

| Metric | Target | Critical? |
|--------|--------|-----------|
| Tests passed | 100% | ✅ |
| Duplicate actives | 0 | ✅ |
| HTTP errors | 0 | ✅ |
| Version progression correct | 100% | ✅ |
| Status transitions valid | 100% | ✅ |
| Multi-entity isolation | 100% | ✅ |
| Performance (per operation) | < 2s | ⚠️ |

---

## Test Documentation Template

For each test:
```markdown
### Test X.Y: [Test Name]

**Pre-conditions:**
- Database state: ...
- Active assignments: ...

**Action:**
1. Step 1
2. Step 2

**Expected Result:**
- Version progression: v1→v2
- Status: v1=superseded, v2=active
- HTTP: 200

**Actual Result:**
- [Record actual outcome]

**Status:** ✅ PASS / ❌ FAIL

**Evidence:**
- Database query results
- Screenshot (if UI)
- Log excerpt
```

---

## Risk Assessment

### High Risk Areas
1. **Inactive Reactivation Logic** - Currently buggy
2. **Multi-Entity Operations** - Complex isolation
3. **Concurrent Changes** - Transaction handling
4. **Computed Fields** - Dependency management

### Mitigation
- Thorough testing of each risk area
- Database backups before testing
- Transaction rollback capability
- Detailed logging

---

## Post-Testing Actions

### If All Tests Pass ✅
1. Update all documentation
2. Mark fix as production-ready
3. Create deployment checklist
4. Archive test results

### If Tests Fail ❌
1. Document all failures
2. Analyze root causes
3. Implement additional fixes
4. Re-run failed tests
5. Repeat until 100% pass rate

---

## Appendix A: SQL Validation Queries

```sql
-- Check for duplicate active assignments
SELECT field_id, entity_id, company_id, COUNT(*) as active_count
FROM data_point_assignments
WHERE series_status = 'active'
GROUP BY field_id, entity_id, company_id
HAVING active_count > 1;

-- Check version sequences
SELECT field_id, entity_id,
       GROUP_CONCAT(series_version ORDER BY series_version) as versions,
       MAX(series_version) as max_version
FROM data_point_assignments
GROUP BY field_id, entity_id;

-- Check status distribution
SELECT series_status, COUNT(*)
FROM data_point_assignments
GROUP BY series_status;

-- Check for superseded that changed
SELECT id, series_version, series_status,
       datetime(assigned_date, 'localtime') as assigned_date
FROM data_point_assignments
WHERE series_status = 'superseded'
ORDER BY assigned_date DESC;
```

---

## Appendix B: Test Result Summary Template

```markdown
# Test Execution Summary
**Date:** 2025-11-12
**Duration:** XX minutes
**Tester:** Claude AI

## Results Overview
- **Total Tests:** XX
- **Passed:** XX (XX%)
- **Failed:** XX (XX%)
- **Skipped:** XX

## Phase Results
- Phase 1: XX/XX passed
- Phase 2: XX/XX passed
- ...

## Critical Findings
1. [Finding 1]
2. [Finding 2]

## Recommendations
1. [Recommendation 1]
2. [Recommendation 2]

## Conclusion
[Overall assessment]
```

---

**Test Plan Version:** 1.0
**Review Status:** Approved for execution
**Next Steps:** Implement fix, then execute all test phases
