# Version Timeline Analysis
## Complete Framework Field 1 - Assignment Versioning History

**Field ID:** b33f7556-17dd-49a8-80fe-f6f5bd893d51
**Framework:** Complete Framework
**Topic:** Energy Management
**Test Date:** October 2, 2025

---

## Timeline of Events

### Event 1: Initial State (Before Test)
**Status:** Multiple active and inactive versions exist
**Total Versions:** 13 assignment records

### Event 2: Soft Delete Operation
**Time:** Test execution
**Action:** Clicked delete button on field in assign-data-points-v2
**Expected Result:** All assignment versions should become inactive
**Actual Result:** Field marked inactive, but assignments remain as-is

### Event 3: Assignment History Check
**Time:** Immediately after soft delete
**Observation:** Bug confirmed - active versions still showing as active

---

## Complete Version History

### Before Soft Delete

| # | Version | Entity | Status | Notes |
|---|---------|--------|--------|-------|
| 1 | v5 | Alpha HQ | Active | Latest version for Alpha HQ |
| 2 | v4 | Alpha Factory | Active | Latest version for Alpha Factory |
| 3 | v3 | Alpha HQ | Active | Duplicate entry issue |
| 4 | v3 | Alpha HQ | Active | Duplicate entry issue |
| 5 | v2 | Alpha Factory | Inactive | Pre-existing inactive |
| 6 | v4 | Alpha HQ | Superseded | Superseded by v5 |
| 7 | v3 | Alpha Factory | Superseded | Superseded by v4 |
| 8 | v2 | Alpha HQ | Superseded | Multiple v2 entries |
| 9 | v3 | Alpha HQ | Superseded | Superseded by v4 or v5 |
| 10 | v2 | Alpha HQ | Superseded | Multiple v2 entries |
| 11 | v2 | Alpha Factory | Inactive | Pre-existing inactive |
| 12 | v1 | Alpha HQ | Inactive | Original assignment |
| 13 | v1 | Alpha Factory | Superseded | Superseded by v2 |

### After Soft Delete

| # | Version | Entity | Actual Status | Expected Status | Bug? |
|---|---------|--------|---------------|-----------------|------|
| 1 | v5 | Alpha HQ | **Active** | Inactive | ❌ YES |
| 2 | v4 | Alpha Factory | **Active** | Inactive | ❌ YES |
| 3 | v3 | Alpha HQ | **Active** | Inactive | ❌ YES |
| 4 | v3 | Alpha HQ | **Active** | Inactive | ❌ YES |
| 5 | v2 | Alpha Factory | Inactive | Inactive | ✓ OK |
| 6 | v4 | Alpha HQ | Superseded | Inactive | ❌ YES |
| 7 | v3 | Alpha Factory | Superseded | Inactive | ❌ YES |
| 8 | v2 | Alpha HQ | Superseded | Inactive | ❌ YES |
| 9 | v3 | Alpha HQ | Superseded | Inactive | ❌ YES |
| 10 | v2 | Alpha HQ | Superseded | Inactive | ❌ YES |
| 11 | v2 | Alpha Factory | Inactive | Inactive | ✓ OK |
| 12 | v1 | Alpha HQ | Inactive | Inactive | ✓ OK |
| 13 | v1 | Alpha Factory | Superseded | Inactive | ❌ YES |

---

## Version Analysis by Entity

### Alpha HQ Versions

| Version | Count | Statuses Found | Expected After Delete |
|---------|-------|----------------|----------------------|
| v1 | 1 | Inactive | Inactive ✓ |
| v2 | 2+ | Superseded | Inactive ❌ |
| v3 | 3+ | Active (2), Superseded (1+) | Inactive ❌ |
| v4 | 1+ | Superseded | Inactive ❌ |
| v5 | 1 | **Active** | Inactive ❌ |

**Issues:**
1. v5 still showing as Active (should be Inactive)
2. v3 has DUPLICATE Active entries
3. Multiple v2 and v3 versions with different statuses

### Alpha Factory Versions

| Version | Count | Statuses Found | Expected After Delete |
|---------|-------|----------------|----------------------|
| v1 | 1 | Superseded | Inactive ❌ |
| v2 | 2 | Inactive (2) | Inactive ✓ |
| v3 | 1 | Superseded | Inactive ❌ |
| v4 | 1 | **Active** | Inactive ❌ |

**Issues:**
1. v4 still showing as Active (should be Inactive)
2. v1 showing as Superseded (should be Inactive)
3. v3 showing as Superseded (should be Inactive)

---

## Status Transition Map

### What Should Happen on Soft Delete

```
Before Soft Delete          After Soft Delete
------------------          ------------------
Active       →              Inactive
Superseded   →              Inactive
Inactive     →              Inactive (no change)
```

### What Actually Happens

```
Before Soft Delete          After Soft Delete
------------------          ------------------
Active       →              Active (BUG!)
Superseded   →              Superseded (BUG!)
Inactive     →              Inactive (correct)
```

---

## Data Integrity Issues Identified

### Issue 1: Active Versions Not Updated
**Severity:** Critical
**Description:** Latest active versions (v5 for Alpha HQ, v4 for Alpha Factory) remain marked as "Active" even though parent field is soft deleted.
**Impact:** Users may attempt to enter data for assignments that reference a deleted field.

### Issue 2: Superseded Versions Not Updated
**Severity:** High
**Description:** Historical superseded versions don't transition to inactive when field is deleted.
**Impact:** Assignment history shows incorrect lifecycle state.

### Issue 3: Duplicate Active Versions
**Severity:** High
**Description:** Multiple v3 versions for Alpha HQ are both marked as "Active" simultaneously.
**Impact:** Violates data integrity constraints - only one version should be active per entity.

### Issue 4: Inconsistent Version Numbering
**Severity:** Medium
**Description:** Same version numbers (v2, v3) appearing multiple times with different statuses.
**Impact:** Makes version history confusing and hard to track.

---

## Expected Behavior After Soft Delete

When a framework field is soft deleted, the system should:

1. **Mark field as inactive** ✓ (Working)
2. **Update ALL related assignments to inactive** ❌ (NOT Working)
3. **Prevent data entry on inactive assignments** ⚠️ (Not tested)
4. **Show clear field deletion status in history** ❌ (Assignments still show as active)

---

## Recommended Database Queries for Investigation

### Query 1: Check All Assignment Versions
```sql
SELECT
    id,
    field_id,
    entity_id,
    series_version,
    is_active,
    series_status,
    created_at,
    updated_at
FROM data_point_assignment
WHERE field_id = 'b33f7556-17dd-49a8-80fe-f6f5bd893d51'
ORDER BY entity_id, series_version DESC;
```

### Query 2: Check Field Status
```sql
SELECT
    id,
    name,
    is_active,
    deleted_at
FROM framework_field
WHERE id = 'b33f7556-17dd-49a8-80fe-f6f5bd893d51';
```

### Query 3: Count Active vs Inactive Assignments
```sql
SELECT
    is_active,
    series_status,
    COUNT(*) as count
FROM data_point_assignment
WHERE field_id = 'b33f7556-17dd-49a8-80fe-f6f5bd893d51'
GROUP BY is_active, series_status;
```

---

## Conclusion

The version timeline clearly shows that soft delete operation:
- ✓ Updates the field's `is_active` status
- ❌ Does NOT update related assignment records' `is_active` status
- ❌ Does NOT update assignment `series_status` values
- ❌ Leaves active assignments orphaned with inactive parent field

This creates a broken relationship where assignments point to a deleted field but still appear as active and available for data entry.

**Fix Required:** Implement cascade update logic to set all related DataPointAssignment records to inactive when parent field is soft deleted.

---

**Document Version:** 1.0
**Last Updated:** October 2, 2025
**Status:** Bug Confirmed
