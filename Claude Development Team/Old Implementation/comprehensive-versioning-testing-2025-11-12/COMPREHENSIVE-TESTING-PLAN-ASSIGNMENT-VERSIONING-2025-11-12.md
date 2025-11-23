# Comprehensive Assignment Versioning Testing Plan
**Date**: 2025-11-12  
**Environment**: Live application with Firefox + Playwright MCP  
**Database**: SQLite (`instance/esg_data.db`)  
**Test Company**: test-company-alpha  
**Admin User**: alice@alpha.com / admin123  
**Status**: 🎯 READY FOR EXECUTION

---

## Executive Summary

This testing plan provides a comprehensive validation strategy for the assignment versioning system. It combines **live browser-based UI testing** with **real-time database verification** to ensure:

- ✅ Zero duplicate active assignments
- ✅ Correct version progression (always forward: v1→v2→v3...)
- ✅ Proper status transitions (active→superseded, not reactivation)
- ✅ Multi-entity isolation (changes to one entity don't affect others)
- ✅ Data integrity across all lifecycle operations

**Estimated Duration**: 6-8 hours for comprehensive execution and documentation

---

## Testing Objectives

### Primary Validations
1. **Versioning Logic**: Configuration changes create correct new versions
2. **Database Integrity**: Consistent data_series_id, series_version, series_status
3. **Edge Case Handling**: Complex scenarios don't break versioning
4. **UI Accuracy**: Dashboard correctly reflects database state
5. **Tenant Isolation**: No cross-company data leakage
6. **Lifecycle Management**: Assignment creation → configuration → deactivation → reactivation

### Critical "MUST NEVER" Rules
- ❌ Duplicate active assignments for same field+entity
- ❌ Reactivate superseded versions
- ❌ Create version number gaps or duplicates
- ❌ Allow backward version progression

### Critical "MUST ALWAYS" Rules
- ✅ Create new versions for configuration changes
- ✅ Supersede old versions when creating new ones
- ✅ Maintain sequential version numbering
- ✅ Preserve immutable version history

---

## Pre-Test Setup

### 1. Environment Preparation

```bash
# Terminal 1: Start Flask application
cd /Users/prateekgoyal/Desktop/Prateek/ESG\ DataVault\ Development/Claude/sakshi-learning
python3 run.py

# Terminal 2: Start Firefox MCP
npm run mcp:start
# If Chrome busy, config will use Firefox automatically

# Terminal 3: Database access
sqlite3 instance/esg_data.db
```

### 2. Create Database Backup

```bash
cp instance/esg_data.db instance/esg_data.db.backup-$(date +%Y%m%d-%H%M%S)
```

### 3. Essential Database Queries

**Save these queries for quick access during testing:**

```sql
-- QUERY 1: View all assignments for an entity
SELECT
    id, field_id, entity_id, data_series_id,
    series_version, series_status, frequency,
    start_date, end_date, is_active,
    datetime(assigned_date, 'localtime') as assigned
FROM data_point_assignment
WHERE entity_id = ?
ORDER BY field_id, series_version;

-- QUERY 2: CHECK FOR DUPLICATE ACTIVES (SHOULD ALWAYS = 0 ROWS!)
SELECT
    field_id, entity_id, data_series_id,
    COUNT(*) as active_count,
    GROUP_CONCAT(id) as ids
FROM data_point_assignment
WHERE series_status = 'active' AND is_active = 1
GROUP BY field_id, entity_id, data_series_id
HAVING COUNT(*) > 1;

-- QUERY 3: Version history for a data series
SELECT
    id, series_version, series_status, frequency,
    start_date, end_date, is_active,
    datetime(assigned_date, 'localtime') as assigned
FROM data_point_assignment
WHERE data_series_id = ?
ORDER BY series_version;

-- QUERY 4: Check version sequence integrity
SELECT
    data_series_id,
    GROUP_CONCAT(series_version ORDER BY series_version) as versions,
    MAX(series_version) as max_version,
    COUNT(*) as total_versions
FROM data_point_assignment
GROUP BY data_series_id
HAVING COUNT(*) > 1;

-- QUERY 5: Status distribution
SELECT series_status, COUNT(*) as count
FROM data_point_assignment
WHERE company_id = 2
GROUP BY series_status;

-- QUERY 6: Find assignments with data entries
SELECT dpa.id, dpa.field_id, dpa.series_version,
       dpa.series_status, COUNT(ed.id) as data_entries
FROM data_point_assignment dpa
LEFT JOIN esg_data ed ON ed.assignment_id = dpa.id
WHERE dpa.entity_id = ?
GROUP BY dpa.id;
```

### 4. Document Initial State

```sql
-- Get entities for test-company-alpha
SELECT id, name, entity_type FROM entity WHERE company_id = 2;

-- Get fields
SELECT id, name, data_type, is_computed FROM field WHERE company_id = 2 LIMIT 10;

-- Current assignment count
SELECT COUNT(*) FROM data_point_assignment
WHERE entity_id IN (SELECT id FROM entity WHERE company_id = 2);

-- Status distribution baseline
SELECT series_status, COUNT(*) FROM data_point_assignment
WHERE entity_id IN (SELECT id FROM entity WHERE company_id = 2)
GROUP BY series_status;
```

---

## Testing Phases

---

## Phase 1: Field Configuration Testing (Configure Fields Modal)

**Objective**: Verify configuration changes trigger correct versioning

---

### Test 1.1: Initial Assignment Creation
**Purpose**: Create baseline assignments with versioning

**Browser Actions**:
1. Navigate to: `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points`
2. Select entity: "Alpha HQ" (note entity_id from database)
3. Assign 3 NEW fields (not currently assigned)
4. For each, configure:
   - Frequency: Yearly
   - Start Date: 2024-01-01
   - End Date: 2024-12-31
5. Click "Save Assignments"

**Database Verification**:
```sql
SELECT id, field_id, data_series_id, series_version,
       series_status, frequency, is_active
FROM data_point_assignment
WHERE entity_id = ?  -- Your entity ID
AND datetime(assigned_date, 'localtime') > datetime('now', '-5 minutes')
ORDER BY id DESC;
```

**Expected Results**:
- ✅ 3 new assignments created
- ✅ Each has unique data_series_id (UUID format)
- ✅ series_version = 1 for all
- ✅ series_status = 'active'
- ✅ is_active = 1
- ✅ frequency = 'Yearly'
- ✅ Dates match input

**Screenshots**: `phase1-test1-initial-assignments.png`

**Record**:
```
Field 1 ID: _____ | data_series_id: _____
Field 2 ID: _____ | data_series_id: _____
Field 3 ID: _____ | data_series_id: _____
```

---

### Test 1.2: Simple Frequency Change (Yearly → Monthly)
**Purpose**: Verify frequency change triggers versioning

**Pre-conditions**: Field 1 from Test 1.1 at v1 (active, Yearly)

**Browser Actions**:
1. Locate Field 1 assignment
2. Click "Configure Fields"
3. Change frequency: Yearly → Monthly
4. Keep dates same
5. Save configuration

**Database Verification**:
```sql
SELECT id, series_version, series_status, frequency,
       start_date, end_date, is_active
FROM data_point_assignment
WHERE data_series_id = '?'  -- Field 1's data_series_id
ORDER BY series_version;
```

**Expected Results**:
- ✅ 2 versions exist
- ✅ **v1**: series_status='superseded', is_active=0, frequency='Yearly'
- ✅ **v2**: series_status='active', is_active=1, frequency='Monthly'
- ✅ Same data_series_id for both
- ✅ v1's end_date adjusted to before v2 start

**Screenshots**: `phase1-test2-frequency-change.png`

---

### Test 1.3: Date Range Extension
**Purpose**: Verify date-only changes trigger versioning

**Pre-conditions**: Field 2 at v1 (Yearly, 2024-01-01 to 2024-12-31)

**Browser Actions**:
1. Configure Field 2
2. Keep frequency: Yearly
3. Extend end date: 2024-12-31 → 2025-12-31
4. Save

**Database Check**:
```sql
SELECT series_version, frequency, start_date, end_date, series_status
FROM data_point_assignment
WHERE data_series_id = ?
ORDER BY series_version;
```

**Expected**: v1 superseded, v2 active with extended date

---

### Test 1.4: Multiple Configuration Changes (Frequency + Dates)
**Purpose**: Verify compound changes create single new version

**Browser Actions**:
1. Configure Field 3 with simultaneous changes:
   - Frequency: Yearly → Quarterly
   - Start Date: 2024-01-01 → 2024-03-01
   - End Date: 2024-12-31 → 2025-06-30
2. Save

**Expected**: Only 2 versions total (v1, v2), all changes in v2

---

### Test 1.5: Rapid Successive Changes (v1→v2→v3→v4)
**Purpose**: Test multiple sequential configuration changes

**Browser Actions**:
1. Using Field 1 (currently v2 from Test 1.2)
2. Change 1: Monthly → Quarterly
3. Change 2: Quarterly → Semi-Annually
4. Change 3: Semi-Annually → Yearly

**Database Check**:
```sql
SELECT series_version, series_status, frequency
FROM data_point_assignment
WHERE data_series_id = ?
ORDER BY series_version;
```

**Expected**:
- ✅ 5 versions (v1, v2, v3, v4, v5)
- ✅ Only v5 is active
- ✅ v1-v4 all superseded
- ✅ No gaps in version sequence

---

### Test 1.6: Configuration Back to Original (Critical Test!)
**Purpose**: Verify returning to original config creates NEW version (not reactivation)

**Pre-conditions**:
- Field 1 at v5 (Yearly)
- Original v1 was also Yearly

**Browser Actions**:
1. Change v5: Yearly → Monthly (creates v6)
2. Change v6: Monthly → Yearly (creates v7)

**Database Check**:
```sql
SELECT series_version, series_status, frequency
FROM data_point_assignment
WHERE data_series_id = ?
ORDER BY series_version;
```

**Expected**:
- ✅ v7 created (NEW version)
- ✅ v7 has frequency = Yearly
- ✅ v1 remains superseded (NOT reactivated!)
- ✅ v6 now superseded
- ✅ Only v7 is active

**CRITICAL**: System MUST create NEW v7, not reactivate old v1!

---

### Test 1.7: Cancel Configuration (No Version)
**Purpose**: Verify cancel doesn't trigger versioning

**Browser Actions**:
1. Open "Configure Fields"
2. Make changes
3. Click "Cancel" or close modal

**Database Check**: Version count unchanged

---

## Phase 2: Entity Assignment Testing

**Objective**: Test multi-entity scenarios and entity isolation

---

### Test 2.1: Assign Same Field to New Entity
**Purpose**: Verify independent versioning per entity

**Browser Actions**:
1. Select different entity (e.g., "Alpha Factory")
2. Assign Field 1 (already assigned to Alpha HQ)
3. Configure with DIFFERENT settings:
   - Frequency: Monthly
   - Dates: 2024-02-01 to 2024-11-30

**Database Check**:
```sql
SELECT field_id, entity_id, data_series_id, series_version, frequency
FROM data_point_assignment
WHERE field_id = ?
ORDER BY entity_id, series_version;
```

**Expected**:
- ✅ Two separate data_series_id values
- ✅ Entity 1: Multiple versions (from Phase 1)
- ✅ Entity 2: v1 only
- ✅ Complete independence

---

### Test 2.2: Bulk Configure Multiple Entities
**Purpose**: Verify bulk changes affect entities independently

**Browser Actions**:
1. Select both entities with Field 1
2. Bulk configure: Change all to Quarterly
3. Save

**Database Check**:
```sql
SELECT entity_id, data_series_id, series_version, frequency, series_status
FROM data_point_assignment
WHERE field_id = ?
ORDER BY entity_id, series_version;
```

**Expected**:
- ✅ Entity 1: New version created (next in sequence)
- ✅ Entity 2: New version created (next in sequence)
- ✅ Different data_series_id values
- ✅ Independent version numbers

---

### Test 2.3: Remove Entity Assignment (Soft Delete)
**Purpose**: Test unassigning marks as inactive

**Browser Actions**:
1. Uncheck Field 1 from Entity 2
2. Save

**Database Check**:
```sql
SELECT id, series_version, series_status, is_active
FROM data_point_assignment
WHERE field_id = ? AND entity_id = ?
ORDER BY series_version;
```

**Expected**:
- ✅ Latest version: is_active=0
- ✅ series_status remains 'active' (not superseded)
- ✅ No new version created
- ✅ All versions preserved

---

### Test 2.4: Re-assign Previously Removed Assignment
**Purpose**: Verify re-assignment creates NEW series

**Pre-conditions**: Field 1 unassigned from Entity 2

**Browser Actions**:
1. Re-check Field 1 for Entity 2
2. Configure with NEW settings (Yearly, 2025 dates)

**Database Check**:
```sql
SELECT data_series_id, series_version, is_active, frequency,
       datetime(assigned_date, 'localtime') as assigned
FROM data_point_assignment
WHERE field_id = ? AND entity_id = ?
ORDER BY assigned_date;
```

**Expected**:
- ✅ NEW data_series_id created
- ✅ New series starts at v1
- ✅ Old series remains inactive
- ✅ Clean separation

**CRITICAL**: Must create NEW series, not reactivate old!

---

## Phase 3: Assignment Lifecycle Testing

---

### Test 3.1: View Version History UI
**Purpose**: Verify UI displays version history

**Browser Actions**:
1. Locate Field 1 for Entity 1 (should have 7+ versions)
2. Click "View History"

**Expected**:
- ✅ All versions displayed
- ✅ Active version marked clearly
- ✅ Shows: version, frequency, dates, status
- ✅ Reverse chronological order

**Screenshot**: `phase3-test1-history-modal.png`

---

### Test 3.2: Assignment with Data Entries
**Purpose**: Test versioning with actual data

**Setup**:
1. As USER (bob@alpha.com), enter data for one assignment
2. Record assignment_id

**Browser Actions (as ADMIN)**:
1. Configure that assignment
2. Change frequency
3. Save

**Database Check**:
```sql
SELECT dpa.id, dpa.series_version, dpa.series_status,
       COUNT(ed.id) as data_count
FROM data_point_assignment dpa
LEFT JOIN esg_data ed ON ed.assignment_id = dpa.id
WHERE dpa.data_series_id = ?
GROUP BY dpa.id
ORDER BY dpa.series_version;
```

**Expected**:
- ✅ Old version (with data) superseded
- ✅ New version (no data) active
- ✅ Data preserved on old version

---

## Phase 4: Edge Cases and Complex Scenarios

---

### Test 4.1: Concurrent Configuration Changes
**Purpose**: Test race condition handling

**Browser Actions**:
1. Open two browser tabs
2. Login as admin in both
3. Tab 1: Open Configure for Field X, change to Monthly, WAIT
4. Tab 2: Open Configure for Field X, change to Quarterly, SAVE
5. Tab 1: Now SAVE

**Database Check**:
```sql
SELECT * FROM data_point_assignment
WHERE data_series_id = ? AND series_status = 'active';
-- Should return ONLY 1 row
```

**Expected**:
- ✅ One change succeeds
- ✅ Other shows error OR overwritten
- ✅ No duplicate actives
- ✅ Sequential versions

---

### Test 4.2: Configuration with Past Dates
**Purpose**: Test backdating

**Browser Actions**:
1. Create assignment: 2024-01-01 to 2024-12-31
2. Immediately reconfigure: 2023-01-01 to 2024-12-31

**Expected**: New version created, past dates accepted

---

### Test 4.3: Very High Version Numbers
**Purpose**: Test system at high version counts

**Browser Actions**: Create 25+ versions through repeated configuration changes

**Expected**: No overflow, versioning continues normally

---

### Test 4.4: Validation Tests
**Purpose**: Test input validation

**Browser Actions**:
1. Try empty frequency
2. Try empty dates
3. Try invalid date formats

**Expected**: Validation errors, no versions created

---

## Phase 5: Data Integrity Validation

---

### Test 5.1: No Duplicate Active Assignments (CRITICAL!)
**Purpose**: Verify database constraint works

```sql
SELECT field_id, entity_id, data_series_id, COUNT(*) as active_count
FROM data_point_assignment
WHERE series_status = 'active' AND is_active = 1
GROUP BY field_id, entity_id, data_series_id
HAVING COUNT(*) > 1;
```

**Expected**: **ZERO ROWS** (If fails, entire system broken!)

---

### Test 5.2: Version Sequence Integrity
**Purpose**: Verify no gaps in version numbers

```sql
WITH version_series AS (
    SELECT data_series_id, series_version,
           LEAD(series_version) OVER (
               PARTITION BY data_series_id ORDER BY series_version
           ) as next_version
    FROM data_point_assignment
)
SELECT data_series_id, series_version, next_version
FROM version_series
WHERE next_version IS NOT NULL
  AND next_version != series_version + 1;
```

**Expected**: ZERO ROWS (no gaps)

---

### Test 5.3: Exactly One Active Per Series

```sql
SELECT data_series_id,
       COUNT(CASE WHEN series_status = 'active' THEN 1 END) as active_count,
       COUNT(*) as total_versions
FROM data_point_assignment
GROUP BY data_series_id
HAVING active_count > 1 OR (active_count = 0 AND total_versions > 0);
```

**Expected**: ZERO ROWS (all series have exactly 1 active OR all inactive)

---

### Test 5.4: Referential Integrity

```sql
-- Orphaned field references
SELECT COUNT(*) FROM data_point_assignment dpa
LEFT JOIN field f ON f.id = dpa.field_id
WHERE f.id IS NULL;

-- Orphaned entity references  
SELECT COUNT(*) FROM data_point_assignment dpa
LEFT JOIN entity e ON e.id = dpa.entity_id
WHERE e.id IS NULL;
```

**Expected**: All counts = 0

---

## Success Criteria

### Critical Requirements (MUST Pass)
- ✅ Test 5.1: Zero duplicate active assignments
- ✅ Test 5.2: No version sequence gaps
- ✅ Test 5.3: Exactly one active per series
- ✅ Test 1.6: No reactivation of old versions
- ✅ Test 2.2: Multi-entity isolation

### Important Requirements (SHOULD Pass)
- ✅ UI displays version history correctly
- ✅ Edge cases handled gracefully
- ✅ Referential integrity maintained
- ✅ Data entries preserved across versioning

---

## Test Execution Checklist

**Pre-Test**:
- [ ] Flask running
- [ ] Firefox MCP started
- [ ] Database backup created
- [ ] Admin logged in
- [ ] Initial state documented
- [ ] Screenshot folder created: `.playwright-mcp/versioning-tests-$(date +%Y%m%d)/`

**During Testing**:
- [ ] Screenshot each test
- [ ] Run database queries before/after each action
- [ ] Document unexpected behavior
- [ ] Check browser console for errors
- [ ] Record all data_series_id values

**Post-Test**:
- [ ] Run all Phase 5 integrity checks
- [ ] Compile test results report
- [ ] Create GitHub issues for bugs
- [ ] Archive test data and screenshots

---

## Bug Report Template

```markdown
## Bug: [Description]

**Test**: Phase X, Test X.X
**Severity**: Critical / High / Medium / Low
**Date**: 2025-11-12

### Reproduce
1.
2.

### Expected
[Expected behavior]

### Actual
[Actual behavior]

### Database State
```sql
[Query results]
```

### Screenshots
[files]
```

---

## Test Report Template

```markdown
# Assignment Versioning Test Report

**Date**: 2025-11-12
**Tester**: [Name]
**Duration**: [hours]

## Summary
- Total Tests: X
- Passed: X (XX%)
- Failed: X (XX%)
- Blocked: X

## Phase Results
### Phase 1: Field Configuration
- Test 1.1: ✅ PASS
- Test 1.2: ✅ PASS
- Test 1.3: ❌ FAIL - [reason]
[...]

## Critical Findings
1. [Issue]
2. [Issue]

## Database Integrity
- Duplicate actives: X
- Version gaps: X
- Orphaned versions: X

## Recommendations
1.
2.
```

---

**ESTIMATED TIMELINE**: 6-8 hours total
- Setup: 15 min
- Phase 1: 90 min
- Phase 2: 60 min
- Phase 3: 30 min
- Phase 4: 60 min
- Phase 5: 45 min
- Documentation: 30 min

---

**END OF TESTING PLAN**
