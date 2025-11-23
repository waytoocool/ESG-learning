# Bug Report: Critical - Save Data Failure for Normal/Raw Input Fields
**Report ID:** BUG-2025-11-09-001
**Date:** 2025-11-09
**Reporter:** UI Testing Agent
**Severity:** HIGH
**Priority:** CRITICAL
**Status:** NEW
**Version:** v1

---

## Bug Summary

The save data functionality fails with a 500 Internal Server Error when attempting to save normal/raw input field data in the user dashboard. This completely blocks users from submitting data for simple metric fields.

---

## Environment

**Application:** ESG Datavault User Dashboard v2
**URL:** http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/dashboard
**User Role:** USER
**Test Account:** bob@alpha.com
**Company:** Test Company Alpha
**Entity:** Alpha Factory (Manufacturing)
**Browser:** Chromium (Playwright)
**Platform:** macOS

---

## Bug Classification

**Type:** Backend API Error
**Severity:** HIGH - Blocks core functionality
**Priority:** CRITICAL - Immediate fix required
**Component:** Data Submission API
**Affected Endpoint:** `/user/v2/api/submit-simple-data`

---

## Description

When users attempt to save data for normal/raw input fields through the data entry modal, the submission fails with a server-side 500 Internal Server Error. The error is consistent and reproducible. Interestingly, the save functionality works correctly for computed/dimensional fields, indicating the issue is specific to the simple data submission endpoint.

---

## Steps to Reproduce

1. Navigate to user dashboard: http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/dashboard
2. Login as user: bob@alpha.com / user123
3. Locate the "Benefits provided to full-time employees..." field (Raw Input, Monthly)
4. Click "Enter Data" button
5. Select a reporting date from the date selector (e.g., "30 April 2025")
6. Enter any value in the "Value" field (e.g., "Test Value 123")
7. Click "Save Data" button
8. Observe the error alert dialog

---

## Expected Behavior

- Data should be successfully saved to the server
- Success message should be displayed
- Modal should close or show confirmation
- Dashboard should update to reflect the saved data
- No error dialogs or console errors

---

## Actual Behavior

- Browser alert dialog appears with message: "Failed to save data: Failed to submit data"
- Console shows 500 Internal Server Error
- Network request to `/user/v2/api/submit-simple-data` fails
- Data is NOT saved to the server
- Auto-save draft functionality still works (misleading "Saved at [time]" indicator)

---

## Technical Details

### Failed API Request

**Endpoint:** `POST /user/v2/api/submit-simple-data`
**HTTP Status:** 500 Internal Server Error
**Request Type:** POST

**Console Error Output:**
```
[ERROR] Failed to load resource: the server responded with a status of 500 (INTERNAL SERVER ERROR)
@ http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/api/submit-simple-data

[ERROR] Error submitting data: Error: Failed to submit data
    at HTMLButtonElement.<anonymous> (http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/dashboard:1588:31)
@ http://test-company-alpha.127-0-0-1.nip.io:8000/static/js/chatbot/data-capture.js?v=1759679840:85
```

### Working Comparison

**Endpoint:** `POST /user/v2/api/submit-dimensional-data`
**HTTP Status:** 200 OK
**Result:** Data saved successfully

This confirms the issue is isolated to the simple data submission endpoint.

---

## Request Payload (Expected)

Based on the field configuration, the request should contain:
- Field ID: `067d135a-f4a3-4de8-96f2-5125860ce347`
- Entity ID: `3` (Alpha Factory)
- Reporting Date: `2025-04-30`
- Value: `"Test Value 123"`
- Fiscal Year: `2026` (Apr 2025 - Mar 2026)

---

## Evidence

### Screenshots

1. **Modal with unsaved changes:**
   - File: `screenshots/05-raw-input-value-entered.png`
   - Shows value entered and "Unsaved changes" indicator

2. **After save error:**
   - File: `screenshots/06-raw-input-after-save-error.png`
   - Shows auto-save succeeded but main save failed

### Network Request Details

```
[POST] http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/api/submit-simple-data
Status: 500 INTERNAL SERVER ERROR
```

### Full Console Log

Complete console messages available in Testing Summary document.

---

## Impact Analysis

### User Impact
- **Severity:** HIGH - Users cannot save data for normal/raw input fields
- **Frequency:** 100% - Consistent failure across all simple field types
- **Workaround:** None - No alternative method to save simple field data
- **Affected Users:** All users attempting to enter data for raw input fields

### Business Impact
- Core data entry functionality is broken for simple metrics
- Users may believe data is saved due to misleading auto-save indicator
- Data collection workflow is blocked
- Potential data loss if users assume auto-save = actual save

### Scope
- **Working:** Computed/dimensional field data submission ✅
- **Broken:** Normal/raw input field data submission ❌

---

## Root Cause Hypothesis

Based on the symptoms, the likely root causes are:

1. **Backend Route Handler Error**
   - Exception thrown in `/user/v2/api/submit-simple-data` endpoint
   - Unhandled error in data processing logic
   - Missing error handling/try-catch block

2. **Database Operation Failure**
   - ORM query error when inserting/updating simple field data
   - Schema mismatch between model and database
   - Foreign key constraint violation

3. **Request Payload Processing**
   - Missing required field in request data
   - Incorrect data type or format
   - Validation error not properly caught

4. **API Route Configuration**
   - Incorrect route parameters
   - Missing middleware or authentication check
   - Tenant isolation issue

---

## Debug Recommendations

### Immediate Investigation Steps

1. **Check Server Logs**
   - Review Flask application logs for the exact stack trace
   - Look for Python exception details around the time of the failed request
   - Check for database query errors

2. **Backend Code Review**
   - Examine `app/routes/user_v2/` files for simple data submission endpoint
   - Compare implementation with working dimensional data endpoint
   - Check data validation and ORM model usage

3. **Database Verification**
   - Verify table schema for simple field data storage
   - Check for any recent schema changes
   - Validate foreign key relationships

4. **Request Inspection**
   - Add detailed logging to capture incoming request payload
   - Verify all required fields are present
   - Check data types and format

### Code Locations to Check

```
Likely affected files:
- app/routes/user_v2/*.py (API route handlers)
- app/services/user_v2/*.py (Business logic)
- app/models/esg_data.py (Data model)
- app/templates/user_v2/dashboard.html (Frontend template)
- app/static/js/user_v2/*.js (JavaScript handlers)
```

---

## Temporary Workaround

**None available.** There is no workaround for users to save simple field data. The functionality is completely broken for raw input fields.

**Note:** The auto-save draft feature still works, but this only saves data locally and does not persist to the server database.

---

## Fix Verification Criteria

To verify the bug is fixed, the following must work:

1. User can open raw input field data entry modal
2. User can select a reporting date
3. User can enter a value
4. User can click "Save Data" button
5. Data is successfully saved to server (200 OK response)
6. No error dialogs or console errors appear
7. Success message is displayed
8. Dashboard updates to show saved data
9. Data persists after page reload

---

## Related Issues

### Secondary UX Issue: Misleading Auto-Save Indicator

**Issue:** The modal displays "Saved at [time]" with a green checkmark after auto-save completes, even though the main save to server has failed. This creates confusion as users may believe their data has been successfully submitted.

**Recommendation:** Clearly distinguish between:
- Draft auto-save status (local only)
- Actual server submission status (persistent)

**Severity:** MEDIUM - Confusing UX that may lead to data loss assumptions

---

## Attachments

**Testing Summary:** `Testing_Summary_SaveDataFix_v1.md`
**Screenshots Directory:** `screenshots/`
**Total Screenshots:** 10

---

## Next Actions

1. **Backend Developer:** Investigate `/user/v2/api/submit-simple-data` endpoint immediately
2. **DevOps:** Check server logs for detailed error stack trace
3. **QA:** Prepare test cases for regression testing after fix
4. **Product:** Consider user communication if fix timeline extends beyond 24 hours

---

## Assignee Recommendations

**Primary:** Backend Developer (Python/Flask expertise)
**Support:** Database Administrator (if schema issues suspected)
**Review:** Tech Lead

---

**Bug Status:** OPEN - Awaiting Developer Investigation
**Created:** 2025-11-09
**Last Updated:** 2025-11-09
**Reporter:** UI Testing Agent
