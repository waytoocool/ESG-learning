# BUG REPORT: Enhancement #1 - Computed Field Modal
## Critical Functionality Issues

**Report Date:** 2025-11-15
**Reporter:** UI Testing Agent
**Test Session:** Enhancement #1 Complete Validation v2
**Environment:** Test Company Alpha - Firefox (Playwright MCP)

---

## Bug #1: Computed Field Calculation Not Displaying in UI

### Severity: 🔴 CRITICAL (BLOCKER)

**Status:** Open
**Priority:** P0 - Must fix before release
**Affected Component:** Computed Field Modal - Calculation Display
**Impact:** Users cannot view calculated values, rendering the feature unusable

---

### Description

The computed field modal displays "No Calculated Value" despite all dependencies having data and the backend API successfully returning the computed result. This completely blocks the core functionality of viewing computed field values.

---

### Steps to Reproduce

1. Login as bob@alpha.com
2. Navigate to user dashboard
3. Submit data for "Total new hires": value = 15, date = 2026-01-31
4. Submit data for "Total number of employees": value = 150, date = 2026-01-31
5. Set dashboard reporting date to 2026-01-31
6. Click "View Data" on computed field "Total rate of new employee hires..."
7. Observe the "Computed Result" section

---

### Expected Behavior

The "Computed Result" section should display:
- Calculated value: **0.1** or **10%**
- Clear formatting showing the result
- Status indicator showing successful calculation
- Data source date information

---

### Actual Behavior

The "Computed Result" section shows:
- "No Calculated Value" (gray text)
- Info badge: "No Data"
- No calculation displayed

**However:**
- Dependencies table correctly shows values: 15 and 150
- Status shows "Available" with check marks for both dependencies
- API call returns 200 OK successfully

---

### Technical Details

**Frontend State Issue:**
```javascript
// Console log shows:
[LOG] Opening modal for field: 0f944ca1-4052-45c8-8e9e-3fbcf84ba44c computed with date: 2026-01-31
[LOG] reportingDate: undefined fieldId: 0f944ca1-4052-45c8-8e9e-3fbcf84ba44c entityId: 3
```

**Problem:** Despite modal being opened with `date: 2026-01-31`, the `reportingDate` becomes `undefined` in the modal's state.

**API Call (Successful):**
```
GET /api/user/v2/computed-field-details/0f944ca1-4052-45c8-8e9e-3fbcf84ba44c?entity_id=3&reporting_date=2026-01-31
Status: 200 OK
```

**Additional Errors:**
```
[ERROR] Error loading dimension matrix: Error
[ERROR] [DateSelector] Container not found: dateSelectorContainer
```

---

### Root Cause Analysis

**Primary Issue:** Frontend state management problem
- Modal initialization receives `date: 2026-01-31`
- However, `reportingDate` becomes `undefined` during initialization
- This prevents the calculation result from being rendered

**Secondary Issues:**
1. Computed field modal attempts to load dimension matrix (not applicable for computed fields)
2. Missing date selector container (computed field modal lacks date selection UI)

**Hypothesized Code Path:**
1. `openModal()` called with `date: 2026-01-31` ✅
2. API call made with correct date parameter ✅
3. API returns successful response (200 OK) ✅
4. Response data not properly parsed/stored in modal state ❌
5. `reportingDate` set to `undefined` instead of `2026-01-31` ❌
6. Calculation display logic checks `reportingDate` and finds it undefined ❌
7. UI displays "No Calculated Value" ❌

---

### Evidence

**Screenshots:**
1. `08-computed-field-with-dependencies-data.png`
   - Shows "No Calculated Value" in result section
   - Dependencies table correctly shows 15 and 150

2. `09-dependencies-table-with-values-and-edit.png`
   - Detailed view of dependencies with values
   - "Available" status with check marks

**Console Logs:**
```
[LOG] Opening modal for field: 0f944ca1-4052-45c8-8e9e-3fbcf84ba44c computed with date: 2026-01-31
[LOG] [Enhancement #1] Opening computed field modal
[LOG] [Date Validation] Form inputs DISABLED
[LOG] [Date Validation] Modal opened without date - inputs disabled
[ERROR] Error loading dimension matrix: Error
[ERROR] [DateSelector] Container not found: dateSelectorContainer
[LOG] [Phase 4] reportingDate: undefined fieldId: 0f944ca1-4052-45c8-8e9e-3fbcf84ba44c entityId: 3
```

**Network Evidence:**
```
Request:  GET /api/user/v2/computed-field-details/0f944ca1-4052-45c8-8e9e-3fbcf84ba44c?entity_id=3&reporting_date=2026-01-31
Response: 200 OK
```

---

### Test Data

**Computed Field:**
- Field ID: `0f944ca1-4052-45c8-8e9e-3fbcf84ba44c`
- Name: "Total rate of new employee hires during the reporting period, by age group, gender and region."
- Formula: `Total new hires / Total number of employees`
- Type: Computed (Monthly)

**Dependencies:**
1. **Total new hires** (Variable A)
   - Field ID: `b27c0050-82cd-46ff-aad6-b4c9156539e8`
   - Value: 15
   - Date: 2026-01-31
   - Status: Saved successfully

2. **Total number of employees** (Variable B)
   - Field ID: `43267341-4891-40d9-970c-8d003aab8302`
   - Value: 150
   - Date: 2026-01-31
   - Status: Saved successfully

**Expected Calculation:** 15 / 150 = 0.1 (10%)

---

### Recommended Fix

**Immediate Actions Required:**

1. **Debug Frontend State Management**
   - File: `computed_field_view.js`
   - Verify `reportingDate` is properly captured from modal initialization
   - Add console logging to track state changes
   - Ensure date parameter is not lost during modal setup

2. **API Response Handling**
   - Verify API response is being parsed correctly
   - Check if calculated value is included in API response
   - Ensure response data is stored in modal state
   - Add error handling for missing/malformed responses

3. **Calculation Display Logic**
   - Review conditional rendering logic for calculation section
   - Ensure it triggers when `reportingDate` is defined AND API data available
   - Add fallback error messages for debugging

4. **Remove Unnecessary API Calls**
   - Skip dimension matrix loading for computed fields
   - Add type checking before attempting to load dimension data

5. **Add Date Selector (Enhancement)**
   - Implement date selector in computed field modal
   - Allow users to view calculations for different dates
   - Fix missing container error

**Code Areas to Investigate:**
```javascript
// File: /app/static/js/user_v2/computed_field_view.js

// Line ~1932: Modal opening logic
function openComputedFieldModal(fieldId, reportingDate) {
    // Verify reportingDate is captured here
    console.log("Opening modal with date:", reportingDate);

    // ... modal initialization code

    // Ensure reportingDate is stored in modal state
    modalState.reportingDate = reportingDate;  // Verify this line exists and works
}

// Line ~XXXX: Calculation display logic
function displayCalculatedResult(data, reportingDate) {
    // Verify reportingDate is passed and used
    if (!reportingDate) {
        console.error("Cannot display result: reportingDate is undefined");
        return;
    }

    // Display the calculated value from data
}
```

---

### Workaround

**None available.** This is a complete blocker for computed field functionality. Users cannot view calculated values through any alternative method in the UI.

---

### Testing Notes

**Verified Working:**
- ✅ Backend API responding correctly (200 OK)
- ✅ Dependencies data submission working
- ✅ Dependencies table displaying values correctly
- ✅ Formula display showing correct calculation
- ✅ Variable mapping displaying correctly

**Not Working:**
- ❌ Calculated result not displaying in UI
- ❌ Date context lost in modal initialization
- ❌ Dimension matrix error for computed fields

---

### Related Issues

This bug blocks testing of:
- Calculation accuracy verification
- Calculation updates after dependency changes
- Historical calculations view
- Export/download of computed values

---

### Acceptance Criteria for Fix

The bug will be considered fixed when:

1. ✅ Computed field modal displays calculated value (0.1 or 10%)
2. ✅ `reportingDate` properly maintained throughout modal lifecycle
3. ✅ Console shows no `undefined` errors for reportingDate
4. ✅ Dimension matrix loading skipped for computed fields
5. ✅ Calculation updates when dependencies are modified
6. ✅ Multiple dates can be viewed (if date selector added)

**Verification Test:**
1. Submit dependency data for date 2026-01-31
2. Open computed field modal
3. **VERIFY:** Calculated value displays as 0.1 or 10%
4. Edit one dependency value
5. **VERIFY:** Calculated value updates automatically

---

## Bug #2: Edit Dependency Button Non-Functional

### Severity: 🟠 MAJOR

**Status:** Open
**Priority:** P1 - Should fix before release
**Affected Component:** Computed Field Modal - Edit Dependency Flow
**Impact:** Poor UX - users cannot edit dependencies directly from computed field view

---

### Description

Clicking the "Edit" button for a dependency in the computed field modal shows an alert message instead of opening an edit modal. Users must navigate away from the computed field modal to edit dependency data.

---

### Steps to Reproduce

1. Open computed field modal with dependency data available
2. Scroll to Dependencies table
3. Click "Edit" button for "Total new hires" dependency
4. Observe behavior

---

### Expected Behavior

1. Edit modal should open for the dependency field
2. Current value (15) should be pre-loaded
3. User can modify the value
4. Save button updates the dependency
5. Computed field recalculates automatically
6. Updated value shows in dependencies table

---

### Actual Behavior

1. Alert dialog appears: "Please navigate to 'Total new hires' field to enter data."
2. User must click OK
3. Modal closes (or stays open)
4. No edit functionality provided

---

### Technical Details

**Console Messages:**
```
[LOG] [ComputedFieldView] Opening dependency modal: JSHandle@object
[WARNING] [ComputedFieldView] No data modal button found for field: b27c0050-82cd-46ff-aad6-b4c9156539e8
```

**Analysis:**
The Edit button functionality tries to:
1. Find the dependency field's "Enter Data" button on the main dashboard
2. Programmatically click it to open the edit modal
3. This fails because the button is not found or not accessible from within the computed field modal context

**Current Implementation:** Edit button triggers `openDependencyModal()` which searches for the field card button on the dashboard, but this doesn't work when the computed field modal is open.

---

### Recommended Fix

**Option 1: Direct Edit Modal (Recommended)**
Implement a dedicated edit modal that:
- Opens directly from computed field modal
- Pre-loads current dependency data
- Allows editing without leaving computed field context
- Refreshes computed field calculation after save

**Option 2: Improved Navigation**
- Close computed field modal
- Scroll to dependency field card
- Auto-open dependency edit modal
- After save, reopen computed field modal with updated calculation

**Option 3: Inline Editing**
- Allow editing dependency value directly in the dependencies table
- Show save/cancel buttons
- Update calculation in real-time

---

### Workaround

**Manual Navigation:**
1. Close computed field modal
2. Find dependency field card on dashboard
3. Click "Enter Data" button
4. Edit value and save
5. Reopen computed field modal to see updated calculation

---

### Impact Assessment

**User Experience:**
- Adds 4-5 extra clicks to edit a dependency
- Breaks workflow continuity
- Confusing for users (alert message not helpful)

**Business Impact:**
- Medium - Feature is usable but with poor UX
- Users can complete tasks but inefficiently
- May lead to user frustration and support tickets

---

### Evidence

**Screenshot:**
- Dependencies table showing "Edit" buttons: `09-dependencies-table-with-values-and-edit.png`

**Console Log:**
```
[WARNING] [ComputedFieldView] No data modal button found for field: b27c0050-82cd-46ff-aad6-b4c9156539e8
```

---

### Acceptance Criteria for Fix

1. ✅ Clicking "Edit" opens a functional edit modal
2. ✅ Current dependency value pre-loaded
3. ✅ Save button updates dependency data
4. ✅ Computed field recalculates with new value
5. ✅ No alerts or error messages
6. ✅ User remains in computed field context

---

## Summary

### Critical Bugs Summary

| Bug ID | Title | Severity | Status | Blocker? |
|--------|-------|----------|--------|----------|
| #1 | Computed Field Calculation Not Displaying | CRITICAL | Open | ✅ YES |
| #2 | Edit Dependency Button Non-Functional | MAJOR | Open | ❌ NO |

### Immediate Actions Required

**Priority 1 (Blocker):**
- Fix Bug #1: Computed field calculation display

**Priority 2 (UX Enhancement):**
- Fix Bug #2: Direct dependency editing

### Risk Assessment

**If Released As-Is:**
- Users cannot view computed values (complete feature failure)
- User frustration and confusion
- Increased support burden
- Potential data entry errors (users won't know if calculations are correct)

**Recommendation:** **DO NOT RELEASE** until Bug #1 is resolved.

---

**Report End**

**Next Steps:**
1. Backend developer: Verify API response payload
2. Frontend developer: Debug modal state management
3. Frontend developer: Implement direct dependency edit
4. QA: Re-test after fixes deployed

---

**Attachments:**
- Testing_Summary_Enhancement1_Complete_v2.md
- 10 screenshots in `/screenshots/` folder
- Console logs captured
- Network request logs captured
