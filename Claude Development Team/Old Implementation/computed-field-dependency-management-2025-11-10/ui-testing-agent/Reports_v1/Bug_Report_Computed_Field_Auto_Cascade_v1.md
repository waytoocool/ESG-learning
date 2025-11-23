# Bug Report: Computed Field Auto-Cascade Feature Failure

**Report ID:** BUG-CF-001
**Feature:** Computed Field Dependency Auto-Management
**Date:** 2025-11-10
**Severity:** CRITICAL (P0)
**Status:** BLOCKING
**Tested By:** UI Testing Agent (Claude Code)

---

## Executive Summary

The Computed Field Dependency Auto-Management feature **FAILS** at its core functionality. When attempting to add a computed field with dependencies, the auto-cascade mechanism throws a JavaScript error and fails to add any dependency fields. Only the computed field itself is added, leaving the assignment incomplete and invalid.

**Impact:** This completely breaks the primary value proposition of the feature - automatic dependency addition. Users cannot benefit from the auto-cascade functionality.

---

## Test Environment

- **URL:** http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points
- **User:** alice@alpha.com (ADMIN)
- **Browser:** Playwright (Chromium)
- **Timestamp:** 2025-11-10 09:50 UTC

---

## Bug Details

### What Was Tested

**Test Scenario:** Test 1 - Auto-Cascade Selection
**Objective:** Verify that when selecting a computed field, all its dependencies are automatically added

**Test Steps:**
1. Navigate to Assign Data Points page
2. Clear any existing selections
3. Expand all topics in the topic tree
4. Locate "GRI 401: Employment 2016" topic
5. Find "Total rate of employee turnover during the reporting period, by age group, gender and region" (computed field with 2 dependencies)
6. Click the "+" button to add this field

**Expected Behavior:**
- Computed field is added to selected panel
- 2 dependency fields are automatically added
- Notification appears: "Added 'Total rate of employee turnover...' and 2 dependencies"
- Selected panel shows 3 total fields (1 computed + 2 dependencies)

**Actual Behavior:**
- Only 1 field is added (the computed field itself)
- No dependencies are added
- JavaScript error in console: `TypeError: Cannot read properties of undefined (reading 'find')`
- No notification about dependencies

---

## Error Details

### JavaScript Error

```
TypeError: Cannot read properties of undefined (reading 'find')
    at http://test-company-alpha.127-0-0-1.nip.io:8000/static/js/admin/assign_data_points/DependencyManager.js?v=1762746197:254:41
    at Array.forEach (<anonymous>)
    at Object.fetchFieldData (http://test-company-alpha.127-0-0-1.nip.io:8000/static/js/admin/assign_data_points/DependencyManager.js?v=1762746197:253:22)
    at Object.handleFieldSelection (http://test-company-alpha.127-0-0-1.nip.io:8000/static/js/admin/assign_data_points/DependencyManager.js?v=1762746197:192:46)
```

### Console Logs

```
[LOG] [DependencyManager] Auto-adding 2 dependencies for e98a1bc5-7541-4cc0-8d57-77706fc65e1b
TypeError: Cannot read properties of undefined (reading 'find')
```

### Root Cause

**File:** `/app/static/js/admin/assign_data_points/DependencyManager.js`
**Line:** 254
**Code:**
```javascript
const field = allFields.find(f => (f.field_id || f.id) === fieldId);
```

**Issue:** The variable `allFields` is `undefined` because `AppState.availableDataPoints` is not populated at the time the DependencyManager tries to fetch dependency field data.

**Code Context (lines 248-271):**
```javascript
async fetchFieldData(fieldIds) {
    // Get fields from current framework's available fields
    const allFields = AppState.availableDataPoints;  // ⚠️ This is undefined!
    const dependencyFields = [];

    fieldIds.forEach(fieldId => {
        const field = allFields.find(f => (f.field_id || f.id) === fieldId);  // ❌ Error here
        if (field) {
            dependencyFields.push(field);
        } else {
            // Fallback logic...
        }
    });

    return dependencyFields;
}
```

---

## Visual Evidence

### Screenshot 1: Initial State with Purple Badges
**File:** `screenshots/02-purple-badges-visible-on-computed-fields.png`
**Description:** Shows the computed fields with purple badges displaying "(2)" to indicate 2 dependencies. Visual indicators are working correctly.

### Screenshot 2: After Failed Auto-Cascade
**File:** `screenshots/05-bug-auto-cascade-failed-only-1-field-added.png`
**Description:** Shows only 1 field in the selected panel after clicking the "+" button. The "+" button is highlighted in blue, but dependencies were not added.

**Key Observations:**
- Selection counter shows "1 data points selected" (should be 3)
- Selected panel shows only the computed field
- No dependency fields visible in selected panel
- No success notification visible

---

## Analysis

### Why This Is Critical

1. **Core Feature Broken:** The entire purpose of this feature is to auto-add dependencies. Without this, the feature provides zero value.

2. **Data Integrity Risk:** Users can now assign computed fields without their dependencies, creating invalid/incomplete data configurations.

3. **Poor User Experience:** Users expect auto-cascade based on the purple badges, but it silently fails with no user-friendly error message.

4. **Blocks All Testing:** Cannot proceed with other test scenarios (partial dependencies, deletion protection, etc.) because the basic functionality is broken.

### State Management Issue

The problem appears to be related to the timing and population of `AppState.availableDataPoints`:

- **DependencyManager** expects `AppState.availableDataPoints` to contain all available fields
- When `handleFieldSelection()` is called, this state is not yet populated
- The error suggests the topic tree loads fields differently or at a different time than expected

### Potential Solutions

1. **Defensive Check:** Add null/undefined check for `allFields` before using `.find()`
2. **State Initialization:** Ensure `AppState.availableDataPoints` is populated before DependencyManager needs it
3. **Alternative Data Source:** Use a different data source that's guaranteed to be available (e.g., from the dependency tree itself)
4. **Lazy Loading:** Fetch dependency field data from the API instead of relying on in-memory state

---

## Impact Assessment

### Feature Status
- ✅ Visual Indicators (Purple Badges): **WORKING**
- ✅ DependencyManager Initialization: **WORKING**
- ✅ Dependency Tree Loading: **WORKING**
- ❌ Auto-Cascade Selection: **BROKEN**
- ⚠️ Deletion Protection: **UNTESTED** (blocked)
- ⚠️ Frequency Validation: **UNTESTED** (blocked)
- ⚠️ Partial Dependencies: **UNTESTED** (blocked)

### Test Results Summary
- **Test 1:** Auto-Cascade Selection - **FAILED** ❌
- **Test 2:** Partial Dependencies - **BLOCKED** ⚠️
- **Test 3:** Deletion Protection - **BLOCKED** ⚠️
- **Test 4:** Configuration & Frequency - **BLOCKED** ⚠️
- **Test 5:** Save and Persistence - **BLOCKED** ⚠️

---

## Recommendations

### Immediate Actions Required

1. **Fix the Root Cause:**
   - Investigate why `AppState.availableDataPoints` is undefined
   - Add defensive programming to handle this case
   - Consider alternative data sources for dependency field data

2. **Add Error Handling:**
   - Catch the error and show user-friendly message
   - Prevent partial selection when auto-cascade fails

3. **Testing:**
   - Add unit tests for `fetchFieldData()` function
   - Test with both populated and empty `AppState.availableDataPoints`
   - Verify timing of state population during page load

### Code Review Needed

**File:** `DependencyManager.js` - Lines 248-272
**Review Focus:**
- Why is `AppState.availableDataPoints` undefined?
- When is this state populated in the page lifecycle?
- Should we use a different data source?

---

## Next Steps

1. **DO NOT PROCEED** with deployment until this critical bug is fixed
2. Developer should investigate `AppState.availableDataPoints` population
3. Once fixed, re-run full test suite (all 5 test scenarios)
4. Add regression tests to prevent this issue in future

---

## Additional Notes

### What's Working Well
- Purple badges correctly show dependency count
- DependencyManager initializes successfully
- Visual styling is consistent and clear
- Error is caught (doesn't crash the page)

### What Needs Attention
- State management timing issues
- Error handling and user feedback
- Data source reliability for dependency resolution

---

**Report Generated:** 2025-11-10 09:55 UTC
**Report Version:** v1
**Status:** Open - Awaiting Developer Fix
