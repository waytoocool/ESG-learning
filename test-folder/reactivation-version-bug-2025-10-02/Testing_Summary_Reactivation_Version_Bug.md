# Testing Summary: Reactivation Versioning Bug Investigation
**Date:** October 2, 2025
**Tester:** UI Testing Agent
**Page Tested:** assign-data-points-v2
**Bug Status:** Partially Validated - UI Limitation Discovered

---

## Executive Summary

Testing was conducted to verify a reported bug where inactive fields reactivate to **version 1** instead of the **newest/latest version** when an entity is assigned. During testing, we successfully validated the soft delete cascade functionality and version status management, but encountered a **UI design limitation** that prevents direct testing of the reactivation scenario through the UI.

---

## Test Environment

- **URL:** http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2
- **Login:** alice@alpha.com / admin123
- **Role:** ADMIN
- **Company:** Test Company Alpha

---

## Test Results

### Phase 1: Field Version Identification ✅ PASSED

**Objective:** Identify a field with multiple versions to test reactivation behavior.

**Field Identified:** Complete Framework Field 1

**Version History (from Assignment History page):**
- **v5 (Alpha HQ):** Inactive - **HIGHEST/NEWEST VERSION**
- v4 (Alpha Factory): Inactive
- v4 (Alpha HQ): Inactive
- v3 (Alpha Factory): Inactive
- v3 (Alpha HQ): Inactive (multiple entries)
- v2 (Alpha Factory): Inactive
- v2 (Alpha HQ): Inactive (multiple entries)
- v1 (Alpha Factory): **Active** ← Currently active before test
- v1 (Alpha HQ): Inactive

**Evidence:** Screenshot `02_field1_all_versions_before_test.png`

**Key Finding:** v5 is the newest/highest version for this field.

---

### Phase 2: Soft Delete Execution ✅ PASSED

**Objective:** Soft delete the field and verify it becomes inactive.

**Actions Taken:**
1. Navigated to assign-data-points-v2 page
2. Clicked "Select All" to load all assigned fields (19 active fields)
3. Located "Complete Framework Field 1" in the unassigned section
4. Clicked the delete (trash) button on the field

**Console Output:**
```
[LOG] [SelectedDataPointsPanel] Remove clicked for: b33f7556-17dd-49a8-80fe-f6f5bd893d51
[LOG] [SelectedDataPointsPanel] Soft deleting item (marking as inactive): b33f7556-17dd-49a8-80fe-f6f5bd893d51
[LOG] [SelectedDataPointsPanel] Backend cascade delete successful: {message: All assignments deactivated...}
[LOG] [SelectedDataPointsPanel] All assignments deactivated for field "Complete Framework Field 1"
```

**Result:**
- ✅ Field successfully marked as inactive
- ✅ Active count decreased from 20 to 19
- ✅ Inactive count increased to 1
- ✅ Field shows "Inactive" badge when "Show Inactive" is toggled

**Evidence:** Screenshot `03_field1_inactive_badge.png`

---

### Phase 3: Cascade Delete Verification ✅ PASSED

**Objective:** Verify that ALL versions of the field were marked as inactive (not just one version).

**Actions Taken:**
1. Navigated to Assignment History page
2. Filtered by "Complete Framework Field 1"
3. Reviewed all version statuses

**Results - ALL Versions Now Inactive:**
- v1 Alpha Factory: **Inactive** ✅
- v1 Alpha HQ: **Inactive** ✅
- v2 Alpha Factory: **Inactive** ✅
- v2 Alpha HQ: **Inactive** (multiple) ✅
- v3 Alpha Factory: **Inactive** ✅
- v3 Alpha HQ: **Inactive** (multiple) ✅
- v4 Alpha Factory: **Inactive** ✅
- v4 Alpha HQ: **Inactive** ✅
- **v5 Alpha HQ: Inactive** ✅ (Highest version)

**Key Finding:** The cascade delete correctly deactivated ALL versions across ALL entities, not just the current active version. This confirms the cascade delete fix is working as expected.

**Evidence:** Screenshot `04_all_versions_inactive_after_delete.png`

---

### Phase 4: Reactivation Testing ⚠️ **BLOCKED - UI LIMITATION**

**Objective:** Reactivate the field by assigning an entity and verify which version becomes active.

**Expected Behavior:**
- Field should reactivate to **v5** (the newest/highest version)
- OR create a new **v6** version

**Bug Hypothesis:**
- Field incorrectly reactivates to **v1** instead of the newest version

**Issue Encountered:**
The assign-data-points-v2 UI **does not allow selection or interaction with inactive fields**. The "Show Inactive" toggle only makes inactive fields visible in the selected panel, but they cannot be:
- Selected for entity assignment
- Configured
- Reactivated through the UI

**Attempts Made:**
1. ✗ Clicked "Show Inactive" - Field visible but grayed out
2. ✗ Attempted to load inactive fields via `ServicesModule.loadExistingDataPoints(true)` - Field not added to selection
3. ✗ Attempted to manually inject inactive field into StateModule - Display did not update to allow interaction

**Root Cause of Limitation:**
The UI architecture loads only **active** assignments from the backend by default:
```
[LOG] [ServicesModule] Loading existing data points (includeInactive: false)...
```

When inactive fields are shown, they are display-only and cannot be interacted with. This is a fundamental design pattern of the assign-data-points-v2 interface.

---

## Critical Design Question Discovered

**How is reactivation supposed to occur in the current UI?**

The assign-data-points-v2 page does not appear to have a mechanism for:
1. Reactivating an inactive field
2. Assigning entities to inactive fields
3. "Undeleting" a soft-deleted field

**Possible Reactivation Workflows:**
1. ❓ **Through the Frameworks page** - Add the field again from the framework's field list?
2. ❓ **Through Assignment History** - Click a "Reactivate" button on an inactive version?
3. ❓ **Through API only** - Direct backend call to create a new assignment?
4. ❓ **Automatic** - When data is submitted for that field by a user?

**This is a critical finding:** If there's no UI mechanism for reactivation, then the bug scenario (reactivating to v1 instead of v5) may only occur through:
- Backend API calls
- Import/bulk operations
- Or there's a UI workflow we haven't discovered

---

## Recommendations

### Immediate Next Steps:

1. **Clarify Reactivation Workflow**
   - Determine the intended user workflow for reactivating an inactive/soft-deleted field
   - Is reactivation even a supported feature, or are deleted fields permanently inactive?

2. **If Reactivation is Supported:**
   - **Option A:** Test via API
     - Make direct POST request to `/api/admin/assignments` endpoint
     - Include the inactive field_id with entity assignment
     - Monitor response to see which version is created/activated

   - **Option B:** Test via Import
     - Export current assignments
     - Add the inactive field with an entity assignment
     - Import the file
     - Check which version becomes active

3. **Alternative Test Approach:**
   - Instead of testing "reactivation of deleted field," test "adding back a previously deleted field"
   - Navigate to the framework page
   - Re-add "Complete Framework Field 1" from the field list
   - Assign it to an entity
   - Check if it creates v6 or incorrectly reuses v1

### Bug Verification Strategy:

Given the UI limitation, the bug can still be validated by:

1. **Database Query Before:** Check `data_point_assignment` table for all versions of field_id `b33f7556-17dd-49a8-80fe-f6f5bd893d51`
2. **Reactivation Action:** Perform reactivation through whichever supported method exists
3. **Database Query After:** Check which `series_version` is now marked as `Active`
4. **Expected:** v6 (new) or v5 (highest)
5. **Bug Condition:** v1 (lowest version reactivated)

---

## Screenshots Captured

1. **01_assignment_history_overview.png** - Initial Assignment History page showing all assignments
2. **02_field1_all_versions_before_test.png** - Complete Framework Field 1 with all versions (v1-v5) before deletion
3. **03_field1_inactive_badge.png** - Field showing "Inactive" badge after soft delete
4. **04_all_versions_inactive_after_delete.png** - All versions confirmed inactive in Assignment History
5. **05_before_showing_inactive.png** - Assign-data-points-v2 page state before attempting reactivation

---

## Validated Findings

✅ **Soft Delete Works Correctly**
- Single delete action deactivates field in UI
- Backend cascade correctly deactivates ALL versions

✅ **Version History Tracking Works**
- Assignment History correctly shows all versions (v1-v5)
- Version statuses accurately reflect Active/Inactive states
- Cascade updates properly propagate to all versions

✅ **UI State Management**
- Active/Inactive toggle functions correctly
- Field counts update accurately
- Delete operation provides proper feedback

⚠️ **Reactivation Cannot Be Tested via Current UI**
- No mechanism discovered for reactivating inactive fields
- Further investigation needed to identify reactivation workflow

---

## Questions for Development Team

1. **Is field reactivation a supported feature?** If a field is soft-deleted, how is it meant to be "undeleted" or reactivated?

2. **What triggers reactivation?**
   - User action in UI?
   - API call?
   - Import operation?
   - Automatic when field is added back from framework?

3. **Expected version behavior on reactivation:**
   - Should it create a new version (v6)?
   - Should it reactivate the highest version (v5)?
   - Is the "reactivates to v1" behavior the actual bug being reported?

4. **Where does reactivation occur?**
   - Assignment History page?
   - Frameworks page?
   - Assign Data Points page (hidden feature)?
   - API only?

---

## Conclusion

Testing successfully validated that:
- Soft delete cascade functionality works correctly (all versions become inactive)
- Version history tracking is accurate
- The field has multiple versions (v1-v5) suitable for testing

However, **direct UI testing of the reactivation bug is blocked** due to the discovery that inactive fields cannot be interacted with in the assign-data-points-v2 interface.

**The bug can still be verified** through alternative methods (API testing, database inspection, or import testing), but we need clarification on the intended reactivation workflow first.

**Status:** Testing incomplete - awaiting guidance on reactivation workflow to complete bug verification.
