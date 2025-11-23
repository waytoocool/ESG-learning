# Testing Summary: Save Data Functionality - Initial Test
**Date:** 2025-11-09
**Tester:** UI Testing Agent
**Application URL:** http://test-company-alpha.127-0-0-1.nip.io:8000/
**User Role:** USER (bob@alpha.com)
**Version:** v1

---

## Executive Summary

Comprehensive testing of the save data functionality revealed a **critical bug affecting normal/raw input fields** while computed/dimensional fields work correctly. The issue manifests as a server-side 500 Internal Server Error when attempting to save simple field data.

**Overall Result:** FAILED - Partial Functionality
**Severity:** HIGH - Blocks core data entry functionality for raw input fields

---

## Test Results Overview

| Field Type | Save Functionality | API Endpoint | HTTP Status | Result |
|-----------|-------------------|--------------|-------------|---------|
| Normal/Raw Input | FAILED | `/user/v2/api/submit-simple-data` | 500 Error | ❌ |
| Computed/Dimensional | SUCCESS | `/user/v2/api/submit-dimensional-data` | 200 OK | ✅ |

---

## Detailed Test Findings

### 1. Normal/Raw Input Field Test

**Field Tested:** "Benefits provided to full-time employees that are not provided to temporary or parttime employees"
**Field Type:** Raw Input (Monthly)
**Category:** Energy Management

#### Test Steps Executed:
1. Opened data entry modal for raw input field
2. Selected reporting date: 30 April 2025
3. Entered test value: "Test Value 123"
4. Clicked "Save Data" button

#### Observed Behavior:
- Modal opened successfully
- Date selector displayed all 12 months correctly
- Value input field accepted text input
- "Unsaved changes" indicator appeared (yellow badge)
- Auto-save draft functionality worked (showed "Saved at 23:30")
- **Critical Issue:** Alert dialog displayed: "Failed to save data: Failed to submit data"

#### Technical Evidence:
**Console Errors:**
```
[ERROR] Failed to load resource: the server responded with a status of 500 (INTERNAL SERVER ERROR)
@ http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/api/submit-simple-data

[ERROR] Error submitting data: Error: Failed to submit data
```

**Network Request:**
```
[POST] /user/v2/api/submit-simple-data => [500] INTERNAL SERVER ERROR
```

**Screenshots:**
- `02-raw-input-field-modal-opened.png` - Modal initial state
- `03-raw-input-date-selector-opened.png` - Date selector UI
- `04-raw-input-date-selected.png` - Selected date (30 April 2025)
- `05-raw-input-value-entered.png` - Value entered with "Unsaved changes" indicator
- `06-raw-input-after-save-error.png` - Auto-save success but main save failed

**Result:** ❌ FAILED

---

### 2. Computed/Dimensional Field Test

**Field Tested:** "Total rate of employee turnover during the reporting period, by age group, gender and region"
**Field Type:** Computed (Annual)
**Category:** Social Impact

#### Test Steps Executed:
1. Opened data entry modal for computed field
2. Selected reporting date: 31 March 2026
3. Existing data loaded successfully into dimensional grid
4. Modified value: Male - Age <=30 from 20.00 to 2025 (test modification)
5. Clicked "Save Data" button

#### Observed Behavior:
- Modal opened successfully
- Date selector displayed 1 annual date (31 March 2026)
- Dimensional breakdown table loaded with existing data:
  - Male: 20.00, 5.00, 10.00 (Total: 35.00)
  - Female: 20.00, 1.00, 1.00 (Total: 22.00)
  - Grand Total: 57.00
- Modified value accepted
- **Success:** Data saved successfully, page reloaded
- No error dialogs or console errors

#### Technical Evidence:
**Console Success Message:**
```
[LOG] SUCCESS: Data saved successfully!
```

**Network Request:**
```
[POST] /user/v2/api/submit-dimensional-data => [200] OK
[GET] /user/v2/dashboard => [200] OK (page reload after save)
```

**Screenshots:**
- `07-computed-field-modal-opened.png` - Modal initial state
- `08-computed-field-date-selected-with-data.png` - Existing data loaded
- `09-computed-field-value-modified.png` - Value modified
- `10-after-computed-save-success.png` - Dashboard after successful save

**Result:** ✅ PASSED

---

## Additional Technical Findings

### Browser Console Errors
1. **Regex Pattern Error:**
   ```
   [ERROR] Pattern attribute value [0-9,.-]* is not a valid regular expression:
   Uncaught SyntaxError: Invalid regular expression: /[0-9,.-]*/v:
   Invalid character in character class
   ```
   - This is a non-blocking validation pattern error in the HTML form

2. **Missing Favicon:** 404 error (non-critical)

### Auto-Save Functionality
- Auto-save draft feature works correctly for raw input fields
- Draft saves to local storage/session but does not submit to server
- Misleading UX: Shows "Saved at [time]" but only refers to draft, not actual data submission

---

## Root Cause Analysis

**Primary Issue:** Server-side error in `/user/v2/api/submit-simple-data` endpoint

**API Endpoint Comparison:**
- `/user/v2/api/submit-simple-data` - Returns 500 Internal Server Error ❌
- `/user/v2/api/submit-dimensional-data` - Works correctly with 200 OK ✅

**Likely Causes:**
1. Backend route handler error in simple data submission endpoint
2. Missing or incorrect request payload processing
3. Database operation failure for simple field data
4. Potential schema mismatch between frontend payload and backend expectations

**Impact Assessment:**
- Users cannot save data for normal/raw input fields
- Only computed/dimensional field data can be saved
- Draft auto-save may confuse users into thinking data is saved when it's not
- Blocks primary data entry workflow for simple metrics

---

## User Experience Issues

### Confusing "Saved" Indicator
The modal shows "Saved at 23:30" (green checkmark) after auto-save, but this only indicates the draft was saved locally, not that the data was successfully submitted to the server. This creates a false sense of completion.

**Recommendation:** Distinguish between draft auto-save and actual data submission status.

---

## Environment Details

**Browser:** Chromium (Playwright)
**Application:** ESG Datavault User Dashboard v2
**Company:** Test Company Alpha
**Entity:** Alpha Factory (Manufacturing)
**Fiscal Year:** Apr 2025 - Mar 2026
**Total Data Requests:** 3
**Completed Requests:** 0
**Overdue Requests:** 1

---

## Recommendations

1. **Immediate Fix Required:** Debug and fix `/user/v2/api/submit-simple-data` endpoint
2. **Error Logging:** Add server-side logging to capture the exact error causing the 500 response
3. **UX Improvement:** Differentiate between draft auto-save status and actual data submission status
4. **Validation:** Fix the regex pattern validation error in form inputs
5. **Testing:** Add automated tests for both simple and dimensional data submission endpoints

---

## Test Artifacts

All screenshots and evidence are stored in:
`Claude Development Team/save-data-fix-2025-11-09/ui-testing-agent/initial-test/screenshots/`

**Screenshot Inventory:**
1. `01-dashboard-initial-state.png` - Dashboard overview
2. `02-raw-input-field-modal-opened.png` - Raw input modal
3. `03-raw-input-date-selector-opened.png` - Date selector UI
4. `04-raw-input-date-selected.png` - Selected date
5. `05-raw-input-value-entered.png` - Value entered
6. `06-raw-input-after-save-error.png` - After save error
7. `07-computed-field-modal-opened.png` - Computed field modal
8. `08-computed-field-date-selected-with-data.png` - Loaded data
9. `09-computed-field-value-modified.png` - Modified value
10. `10-after-computed-save-success.png` - After successful save

---

## Next Steps

1. Backend developer should investigate the `/user/v2/api/submit-simple-data` endpoint
2. Check server logs for detailed error stack trace
3. Verify database schema and ORM model for simple field data
4. Test fix with same test data used in this report
5. Re-run UI testing after fix is deployed

---

**Test Status:** COMPLETED
**Overall Result:** FAILED - Critical bug identified in raw input field save functionality
**Recommended Action:** Escalate to backend developer for immediate investigation
