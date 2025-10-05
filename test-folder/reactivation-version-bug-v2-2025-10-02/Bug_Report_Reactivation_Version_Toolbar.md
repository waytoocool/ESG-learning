# Bug Report: Reactivation Version Bug in Assign Data Points V2

**Bug ID**: REACTIVATION-VERSION-BUG-001
**Date Reported**: October 2, 2025
**Severity**: HIGH
**Priority**: HIGH
**Status**: CONFIRMED
**Reporter**: UI Testing Agent
**Affected Component**: Assign Data Points V2 - Toolbar Entity Assignment Workflow

---

## Executive Summary

When reactivating an inactive field using the **checkbox + toolbar "Assign Entity" workflow** in the assign-data-points-v2 page, the system incorrectly creates a **v1 assignment** instead of either:
1. Reactivating the **latest existing version** (e.g., v5), OR
2. Creating the **next version** in the series (e.g., v6)

This bug causes version history to become fragmented and creates confusion about which version is active.

---

## Bug Details

### Issue Description
The reactivation workflow via toolbar "Assign Entity" button does not properly handle version selection for fields with multiple existing versions. Instead of using the latest version or creating the next sequential version, it always creates/activates version 1.

### Expected Behavior
When reactivating an inactive field that previously had multiple versions (v1, v2, v3, v4, v5):
- **Option A**: Reactivate the highest existing version (v5) for the selected entity
- **Option B**: Create the next version in sequence (v6) as a new active assignment

### Actual Behavior
The system creates a NEW v1 assignment for the selected entity, ignoring all existing higher versions.

### Impact Assessment
- **Data Integrity**: Version history becomes misleading with multiple v1 assignments for different entities
- **User Confusion**: Admins cannot determine which version represents the latest configuration
- **Audit Trail**: Version progression is broken, making it difficult to track assignment evolution
- **Business Logic**: Downstream processes relying on version numbers may fail or produce incorrect results

---

## Reproduction Steps

### Prerequisites
- User: alice@alpha.com (ADMIN role)
- Company: Test Company Alpha
- Test Field: "Complete Framework Field 1" (Code: COMPLETE_FRAMEWORK_F1)
- Framework: Complete Framework
- Initial State: Field has versions v1, v2, v3, v4, v5 (all inactive after cascade delete)

### Step-by-Step Reproduction

1. **Login as Admin**
   - Navigate to: `http://test-company-alpha.127-0-0-1.nip.io:8000/login`
   - Credentials: alice@alpha.com / admin123
   - Screenshot: `screenshots/01-login-page.png`

2. **Navigate to Assign Data Points V2**
   - URL: `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2`
   - Screenshot: `screenshots/02-assign-data-points-page.png`

3. **Verify Field Has Multiple Versions**
   - Navigate to Assignment History: `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assignment-history/`
   - Filter by: "Complete Framework Field 1"
   - Confirm: Field has versions v1-v5 for various entities
   - Highest version: **v5 (Alpha HQ) - Inactive**
   - Screenshot: `screenshots/1-phase1-assignment-history-before-delete-v5-highest.png`

4. **Verify Field is Inactive**
   - Return to assign-data-points-v2 page
   - Click "Show Inactive" button to enable inactive view
   - Confirm: "Complete Framework Field 1" appears in "Unassigned" section
   - Screenshot: `screenshots/2-phase2-field-inactive-no-assignments.png`

5. **Execute Reactivation Workflow**
   - Find "Complete Framework Field 1" in the selection panel
   - Click the checkbox next to the field to select it
   - Screenshot: `screenshots/3-phase3-field-checkbox-selected.png`

   - Click the toolbar button: "🏢 Assign Entities"
   - Screenshot: `screenshots/4-phase3-assign-entity-modal-opened.png`

   - In the modal, select entity: "Alpha Factory"
   - Screenshot: `screenshots/5-phase3-entity-selected-alpha-factory.png`

   - Click "Assign Entities" button in modal
   - Wait for success confirmation
   - Screenshot: `screenshots/6-phase3-field-reactivated-with-entity.png`

6. **Verify Bug - Check Activated Version**
   - Navigate back to Assignment History
   - Filter by: "Complete Framework Field 1"
   - **OBSERVED BUG**:
     - Complete Framework Field 1 - Alpha Factory - **v1 - Active** ❌
     - Complete Framework Field 1 - Alpha HQ - **v5 - Inactive** (highest version)
   - Screenshot: `screenshots/7-BUG-CONFIRMED-v1-active-instead-of-v5.png`
   - Screenshot: `screenshots/8-filtered-view-showing-v1-active-v5-exists.png`

---

## Evidence and Screenshots

### Timeline Evidence

| Step | Screenshot | Description |
|------|------------|-------------|
| Baseline | `1-phase1-assignment-history-before-delete-v5-highest.png` | Shows v5 as highest version before reactivation |
| Phase 2 | `2-phase2-field-inactive-no-assignments.png` | Field is inactive with no active assignments |
| Phase 3a | `3-phase3-field-checkbox-selected.png` | Field selected via checkbox |
| Phase 3b | `4-phase3-assign-entity-modal-opened.png` | Assign Entity modal opened |
| Phase 3c | `5-phase3-entity-selected-alpha-factory.png` | Alpha Factory entity selected |
| Phase 3d | `6-phase3-field-reactivated-with-entity.png` | Assignment completed |
| BUG | `7-BUG-CONFIRMED-v1-active-instead-of-v5.png` | Shows v1 active instead of v5 |
| BUG Detail | `8-filtered-view-showing-v1-active-v5-exists.png` | Filtered view showing the version discrepancy |

### Assignment History State (Post-Bug)

From Assignment History page showing "Complete Framework Field 1":

**Active Assignment** (BUG):
- **Entity**: Alpha Factory
- **Version**: v1 ❌ (INCORRECT - should be v5 or v6)
- **Status**: Active
- **Assigned By**: Alice Admin
- **Assigned Date**: Oct 2, 2025

**Inactive Versions** (Historical):
1. **Alpha Factory - v1** - Inactive (duplicate of active v1)
2. **Alpha Factory - v2** - Inactive
3. **Alpha Factory - v3** - Inactive
4. **Alpha Factory - v4** - Inactive
5. **Alpha HQ - v1** - Inactive
6. **Alpha HQ - v2** - Inactive (3 instances)
7. **Alpha HQ - v3** - Inactive (4 instances)
8. **Alpha HQ - v4** - Inactive (2 instances)
9. **Alpha HQ - v5** - Inactive ✓ (HIGHEST VERSION in system)

---

## Root Cause Analysis

### Frontend Analysis

Based on console logs from the assign-data-points-v2 page, the following was observed:

**Console Logs During Assignment**:
```
[LOG] [PopupsModule] Apply Entity Assignment button listener attached
[LOG] [PopupsModule] Loading material topics...
[LOG] [ServicesModule] Loading company topics...
[LOG] Entity assignment completed: 1 new assignments created
```

**Critical Observation**:
- No version selection logic is visible in the frontend console logs
- The frontend does not appear to query for existing versions before submitting the assignment
- No log entry shows version calculation or selection

### Backend Analysis (Inferred)

The API endpoint likely has one of these issues:

1. **Missing Version Query**: The backend endpoint `/admin/assignments/bulk-assign-entities` (or similar) does not check for existing versions in the data series
2. **Default Version Assignment**: The backend defaults to v1 when no version is explicitly specified
3. **Version Selection Logic Missing**: No logic exists to find the max version for a field+entity combination

### Suspected Code Location

Based on the application structure, the issue likely resides in:

**Backend Endpoint**:
- File: `/app/routes/admin_assignments_api.py` or `/app/routes/admin_assignments/`
- Function: Entity assignment handler for bulk operations
- Missing Logic: Query to find `MAX(series_version)` for the given field's data_series_id

**Potential Fix Location**:
```python
# Suspected missing logic in backend
def assign_entities_to_fields(field_ids, entity_ids, ...):
    for field_id in field_ids:
        for entity_id in entity_ids:
            # MISSING: Query for existing assignments
            existing_assignments = DataPointAssignment.query.filter_by(
                field_id=field_id,
                entity_id=entity_id,
                series_status='inactive'
            ).order_by(DataPointAssignment.series_version.desc()).first()

            # MISSING: Use existing version or calculate next
            if existing_assignments:
                version = existing_assignments.series_version  # Reactivate highest
                # OR
                version = existing_assignments.series_version + 1  # Create next
            else:
                version = 1  # Only use v1 for truly new assignments
```

---

## Network Traffic Analysis

### API Calls Observed

From browser network logs during the bug reproduction:

**Entity Assignment API Call**:
```
POST /admin/assignments/bulk-assign-entities (or similar endpoint)
Status: 200 OK
Response: "Entity assignment completed: 1 new assignments created"
```

**Critical Finding**:
- The API response does not indicate which version was assigned
- No version information is returned in the success message
- The frontend has no way to validate if the correct version was used

---

## Testing Summary

### Test Environment
- **URL**: http://test-company-alpha.127-0-0-1.nip.io:8000/
- **User**: alice@alpha.com (ADMIN)
- **Company**: Test Company Alpha
- **Date**: October 2, 2025
- **Browser**: Playwright Chrome

### Test Results

| Test Case | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Reactivate field with multiple versions | v5 or v6 | v1 | FAIL ❌ |
| Version continuity | Maintain highest version | Created duplicate v1 | FAIL ❌ |
| Assignment status | Single active per entity | Correct (1 active) | PASS ✓ |
| Entity selection | Alpha Factory assigned | Alpha Factory assigned | PASS ✓ |
| Assignment creation | 1 assignment created | 1 assignment created | PASS ✓ |

**Overall Test Result**: **FAILED - Critical Bug Confirmed**

---

## Recommended Fix

### Priority
**HIGH** - This bug affects data integrity and version history tracking

### Suggested Implementation

1. **Backend Fix** (Primary):
   ```python
   # In admin_assignments_api.py or equivalent
   def determine_version_for_assignment(field_id, entity_id):
       """Determine the correct version for a new/reactivated assignment."""
       # Query for existing assignments for this field+entity
       existing = DataPointAssignment.query.filter_by(
           field_id=field_id,
           entity_id=entity_id
       ).order_by(DataPointAssignment.series_version.desc()).first()

       if existing:
           # Check if we're reactivating or creating new
           if existing.series_status == 'inactive':
               # Option A: Reactivate highest version
               return existing.series_version

               # Option B: Create next version (if configuration changed)
               # return existing.series_version + 1
           else:
               # Already active, this shouldn't happen
               raise ValueError("Assignment already active")
       else:
           # Truly new assignment for this field+entity combination
           return 1
   ```

2. **Frontend Enhancement** (Secondary):
   - Add version display in success messages
   - Show version number in entity assignment modal
   - Validate version selection before submission

3. **API Response Enhancement**:
   - Return version information in assignment API response
   - Include version in success messages for user feedback

### Testing Requirements After Fix

1. Test reactivation of fields with multiple versions (v1-v5)
2. Test reactivation for different entities
3. Test that truly new assignments still get v1
4. Verify version continuity in Assignment History
5. Test bulk entity assignments with version handling

---

## Additional Notes

### Workaround
Until fixed, admins should:
1. Manually check Assignment History before reactivating fields
2. Be aware that reactivation creates v1, not latest version
3. Consider manually updating version numbers in database if critical

### Related Issues
This bug may be related to:
- Assignment versioning system implementation
- Cascade delete functionality
- Bulk assignment operations

### Browser Console Errors
No JavaScript errors were observed during the bug reproduction. The issue is purely related to backend version selection logic.

---

## Appendix: Complete Version History

**Complete Framework Field 1 - Full Version Timeline** (from Assignment History):

| Entity | Version | Status | Assigned Date | Assigned By |
|--------|---------|--------|---------------|-------------|
| Alpha Factory | v1 | **Active** ❌ | Oct 2, 2025 | Alice Admin |
| Alpha Factory | v1 | Inactive | Oct 2, 2025 | Alice Admin |
| Alpha Factory | v2 | Inactive | Oct 2, 2025 | Alice Admin |
| Alpha Factory | v2 | Inactive | Oct 2, 2025 | Alice Admin |
| Alpha Factory | v3 | Inactive | Oct 2, 2025 | Alice Admin |
| Alpha Factory | v4 | Inactive | Oct 2, 2025 | Alice Admin |
| Alpha HQ | v1 | Inactive | Oct 2, 2025 | Alice Admin |
| Alpha HQ | v2 | Inactive | Oct 2, 2025 | Alice Admin |
| Alpha HQ | v2 | Inactive | Oct 2, 2025 | Alice Admin |
| Alpha HQ | v2 | Inactive | Oct 2, 2025 | Alice Admin |
| Alpha HQ | v3 | Inactive | Oct 2, 2025 | Alice Admin |
| Alpha HQ | v3 | Inactive | Oct 2, 2025 | Alice Admin |
| Alpha HQ | v3 | Inactive | Oct 2, 2025 | Alice Admin |
| Alpha HQ | v3 | Inactive | Oct 2, 2025 | Alice Admin |
| Alpha HQ | v4 | Inactive | Oct 2, 2025 | Alice Admin |
| Alpha HQ | v4 | Inactive | Oct 2, 2025 | Alice Admin |
| Alpha HQ | v5 | Inactive ✓ | Oct 2, 2025 | Alice Admin |

**Note**: v5 (Alpha HQ) is the highest version in the system but was not used for reactivation.

---

**End of Bug Report**
