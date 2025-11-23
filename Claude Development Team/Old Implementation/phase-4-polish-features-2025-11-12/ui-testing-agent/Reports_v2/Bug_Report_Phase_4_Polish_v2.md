# Bug Report: Phase 4 Polish Features - Critical Issues

**Report Date:** 2025-11-12
**Report Version:** v2
**Testing Phase:** Post-Implementation Bug Fix Verification
**Severity:** HIGH - Blocking Production Deployment

---

## Overview

This bug report documents two critical issues discovered during verification testing of Phase 4 Polish Features bug fixes. Both issues prevent successful completion of the implementation and block production deployment.

---

## Bug #1: Historical Data Export Function Not Implemented

### Severity: HIGH (BLOCKER)

### Status: OPEN

### Summary
The historical data export functionality (CSV and Excel) is completely non-functional. Clicking either export button results in a JavaScript error indicating the export function is not defined.

### Steps to Reproduce
1. Navigate to http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/dashboard
2. Log in as bob@alpha.com / user123
3. Click "Enter Data" on any field with historical submissions
4. Click "Historical Data" tab
5. Click either "CSV" or "Excel" export button

### Expected Behavior
- Clicking "CSV" button should:
  - Show loading state ("Exporting...")
  - Download a CSV file containing all historical data for the field
  - Return button to normal state
- Clicking "Excel" button should:
  - Show loading state ("Exporting...")
  - Download an XLSX file containing all historical data for the field
  - Return button to normal state

### Actual Behavior
- Clicking either button triggers JavaScript error
- Error: `ReferenceError: exportFieldHistory is not defined`
- No file download occurs
- No loading state displayed
- Buttons remain clickable but non-functional

### Error Details
```
ReferenceError: exportFieldHistory is not defined
    at HTMLButtonElement.onclick (http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/dashboard)
```

### Root Cause
The function `exportFieldHistory(fieldId, format)` is called by the export buttons via onclick handlers, but this function is not defined anywhere in the dashboard.html template or associated JavaScript files.

**Initial Bug Report Claimed:** This was a cache issue that would be resolved by restarting Flask.

**Actual Finding:** Testing with a fresh Flask restart confirms the function genuinely does not exist. This is not a cache issue - the implementation is missing.

### Evidence
- Screenshot: `screenshots/05-historical-data-tab-with-export-buttons.png`
  - Shows Historical Data tab with 2 entries
  - Shows CSV and Excel export buttons visible and apparently functional
- Screenshot: `screenshots/06-csv-export-error-function-not-defined.png`
  - Shows the same view after clicking export button
  - Error visible in browser console

### Impact
- **User Impact:** Users cannot export their historical ESG data to CSV or Excel formats
- **Business Impact:** Critical functionality for data analysis and reporting is unavailable
- **Scope:** Affects all fields with historical data across all user dashboards

### Technical Details

**Location:**
- Template: `app/templates/user_v2/dashboard.html`
- Expected function: `exportFieldHistory(fieldId, format)`

**Button HTML (from Historical Data tab):**
```html
<button onclick="exportFieldHistory('{{ field_id }}', 'csv')" class="btn">CSV</button>
<button onclick="exportFieldHistory('{{ field_id }}', 'excel')" class="btn">Excel</button>
```

**Missing Implementation:**
The function needs to:
1. Accept fieldId and format parameters
2. Fetch historical data from API endpoint
3. Format data as CSV or Excel
4. Trigger browser download
5. Handle errors appropriately
6. Show loading state during processing

### Recommended Fix

**Option 1: Implement JavaScript function in dashboard.html**
Add the following function to the dashboard.html template:

```javascript
async function exportFieldHistory(fieldId, format) {
    const btn = event.target;
    const originalText = btn.textContent;

    try {
        btn.textContent = 'Exporting...';
        btn.disabled = true;

        const response = await fetch(`/api/user/v2/export-history/${fieldId}?format=${format}`);

        if (!response.ok) {
            throw new Error('Export failed');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `field_${fieldId}_history.${format === 'csv' ? 'csv' : 'xlsx'}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

    } catch (error) {
        console.error('Export error:', error);
        alert('Failed to export data. Please try again.');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}
```

**Option 2: Backend API endpoint may also need implementation**
Verify that the backend endpoint `/api/user/v2/export-history/<field_id>` exists and properly handles both CSV and Excel format parameters.

### Priority: HIGH
This is a blocking issue for production deployment. Historical data export is a core feature for ESG reporting and data analysis.

---

## Bug #2: Dimensional Data Draft Not Saved on Modal Close

### Severity: MEDIUM

### Status: OPEN

### Summary
The dimensional data draft save functionality does not work when closing the modal with the Cancel button. Users lose all unsaved dimensional data entries, creating a poor user experience and potential data loss.

### Steps to Reproduce
1. Navigate to user dashboard v2
2. Open the dimensional field: "Total rate of new employee hires during the reporting period..."
3. Select reporting date: "30 June 2025"
4. Enter dimensional data in multiple cells:
   - Male, Age <=30: 100
   - Male, 30 < Age <= 50: 150
   - Female, Age <=30: 120
   - Female, Age > 50: 80
5. Verify totals calculate (should show 450.00)
6. Click "Cancel" button (do not click "Save Data")
7. Wait 2 seconds
8. Reopen the same field
9. Select the same date: "30 June 2025"
10. Observe the dimensional data values

### Expected Behavior
- When modal is closed (even with Cancel), dimensional data should be saved to localStorage as a draft
- Console should log: "[Phase 4] Saving draft before closing modal..."
- Console should log: "[Phase 4] Draft saved successfully on modal close"
- When reopening the modal with the same date, all entered values should be restored
- Totals should recalculate automatically

### Actual Behavior
- All dimensional data fields show 0.00 values
- No draft save attempt is logged to console
- Modal hidden event fires correctly
- Auto-save stops correctly
- **But no draft save is triggered**
- All entered data is completely lost

### Error Details
**Console Logs (What Happened):**
```
[LOG] [Phase 4] Modal hidden event fired
[LOG] Auto-save stopped for field 0f944ca1-4052-45c8-8e9e-3fbcf84ba44c
[LOG] [Phase 4] Auto-save stopped
```

**Console Logs (What Should Have Happened):**
```
[LOG] [Phase 4] Modal hidden event fired
[LOG] [Phase 4] Saving draft before closing modal...
[LOG] [Phase 4] Draft saved successfully on modal close
[LOG] Auto-save stopped for field 0f944ca1-4052-45c8-8e9e-3fbcf84ba44c
[LOG] [Phase 4] Auto-save stopped
```

### Root Cause Analysis

**Bug Fix Code Review:**
The bug fix was implemented in `app/templates/user_v2/dashboard.html` at lines 1808-1816:

```javascript
// Save draft immediately if there are unsaved changes
if (window.autoSaveHandler && window.autoSaveHandler.isDirty) {
    console.log('[Phase 4] Saving draft before closing modal...');
    try {
        await window.autoSaveHandler.saveDraft();
        console.log('[Phase 4] Draft saved successfully on modal close');
    } catch (error) {
        console.error('[Phase 4] Error saving draft on modal close:', error);
    }
}
```

**Issue Identified:**
The conditional check `window.autoSaveHandler.isDirty` is false, so the draft save code never executes.

**Why isDirty is False:**
From `app/static/js/user_v2/auto_save_handler.js` line 109:
```javascript
handleFormChange() {
    if (!this.isActive) return;
    this.isDirty = true;  // Only set to true here
    // ... rest of method
}
```

The `isDirty` flag is only set to true when `handleFormChange()` is called. However, **dimensional data inputs do not have event listeners attached** that call this method.

**Evidence from Code Review:**
- AutoSaveHandler is initialized correctly (console confirms this)
- handleFormChange() method exists and works correctly
- But dimensional input fields are not wired up to call handleFormChange() when values change
- Therefore isDirty remains false throughout data entry
- Modal close handler checks isDirty, finds it false, skips draft save

### Evidence
- Screenshot: `screenshots/03-dimensional-data-entered.png`
  - Shows dimensional data entry form
  - Values entered: 100, 150, 120, 80
  - Total calculated: 450.00
  - Date selected: 30 June 2025

- Screenshot: `screenshots/04-draft-not-recovered-BUG.png`
  - Shows same modal after reopening
  - Same date selected: 30 June 2025
  - All values showing: 0.00
  - Total showing: 0.00
  - Data completely lost

### Impact
- **User Impact:** Users lose dimensional data entries when accidentally closing modal
- **Severity:** Dimensional data entry can be time-consuming with multiple cells to fill
- **Scope:** Affects all dimensional fields across user dashboard
- **Frequency:** Occurs every time user closes modal without explicitly saving

### Technical Details

**Files Involved:**
1. `app/templates/user_v2/dashboard.html` - Modal close handler (lines 1808-1816)
2. `app/static/js/user_v2/auto_save_handler.js` - AutoSaveHandler class
3. Dimensional data input rendering (needs event listener attachment)

**Current Flow:**
1. User opens modal → AutoSaveHandler initialized
2. User enters dimensional data → **No handleFormChange() called**
3. isDirty remains false
4. User clicks Cancel → Modal close handler checks isDirty
5. isDirty is false → Draft save skipped
6. Data lost

**Required Flow:**
1. User opens modal → AutoSaveHandler initialized
2. User enters dimensional data → **handleFormChange() called on input change**
3. isDirty set to true
4. User clicks Cancel → Modal close handler checks isDirty
5. isDirty is true → Draft save triggered
6. Data saved to localStorage
7. Next time modal opens → Draft restored

### Recommended Fix

**Step 1: Attach Event Listeners to Dimensional Inputs**

Add event listener attachment when dimensional grid is rendered. In dashboard.html, find where dimensional inputs are created and add:

```javascript
// After dimensional grid is rendered
function attachDimensionalInputListeners() {
    const dimensionalInputs = document.querySelectorAll('.dimensional-grid input[type="number"]');

    dimensionalInputs.forEach(input => {
        input.addEventListener('input', () => {
            if (window.autoSaveHandler) {
                window.autoSaveHandler.handleFormChange();
            }
        });
    });
}
```

**Step 2: Call Attachment Function**

Ensure this function is called:
- After dimensional grid HTML is inserted into DOM
- When switching between different reporting dates
- After any AJAX-based grid updates

**Step 3: Verify with Console Logs**

Add temporary logging to verify:
```javascript
input.addEventListener('input', () => {
    console.log('[DEBUG] Dimensional input changed, calling handleFormChange');
    if (window.autoSaveHandler) {
        window.autoSaveHandler.handleFormChange();
    }
});
```

### Alternative Fix: Force isDirty True on Modal Close

If event listener attachment is complex, a simpler alternative:

```javascript
// In modal close handler, before checking isDirty
if (window.autoSaveHandler) {
    // Check if any dimensional data exists in form
    const hasData = document.querySelectorAll('.dimensional-grid input[type="number"]')
        .some(input => input.value && parseFloat(input.value) !== 0);

    if (hasData) {
        window.autoSaveHandler.isDirty = true;
    }

    if (window.autoSaveHandler.isDirty) {
        // ... existing save logic
    }
}
```

This is less elegant but would work as a quick fix.

### Priority: MEDIUM
While this doesn't completely break functionality (users can still explicitly save), it creates a poor user experience and potential data loss scenario. Should be fixed before production deployment.

---

## Testing Recommendations

After fixes are implemented, the following tests should be performed:

### For Bug #1 (Export Function):
1. Verify CSV export downloads a valid CSV file
2. Verify Excel export downloads a valid XLSX file
3. Verify export button shows loading state during processing
4. Verify export handles errors gracefully
5. Verify exported data matches historical data in database
6. Test with fields containing various data types (text, numbers, dimensional data)

### For Bug #2 (Draft Recovery):
1. Verify console logs show "[Phase 4] Saving draft before closing modal..."
2. Verify draft is actually saved to localStorage (check browser DevTools)
3. Verify draft is restored when reopening modal
4. Verify dimensional totals recalculate after draft restore
5. Test with various dimensional data patterns (partial fills, all filled, etc.)
6. Test draft expiration (should not restore very old drafts)

---

## Dependencies

**Bug #1 Dependencies:**
- Backend API endpoint `/api/user/v2/export-history/<field_id>` must exist
- Backend must support both CSV and Excel format generation
- Backend must handle dimensional data properly in exports

**Bug #2 Dependencies:**
- None - purely frontend fix

---

## Additional Notes

### Good News
- Bug #3 (Keyboard shortcuts) is working perfectly and can be deployed independently
- AutoSaveHandler infrastructure is correctly implemented and functioning
- Modal close handler is properly integrated
- The bug fixes were on the right track, just incomplete

### Pattern Recognition
Both bugs share a common theme: **incomplete implementation**
- Bug #1: Buttons exist, but function doesn't
- Bug #2: Save logic exists, but event wiring doesn't

This suggests the implementation may have been rushed or not fully tested before being marked as complete.

---

## Contact Information

**Reported By:** UI Testing Agent
**Report Date:** 2025-11-12
**Report File:** Bug_Report_Phase_4_Polish_v2.md
**Screenshots:** Available in `screenshots/` directory
**Related Document:** Testing_Summary_Phase_4_Polish_v2.md

---

**Status:** OPEN - Awaiting fixes from development team
**Next Review:** After fixes implemented, schedule Testing v3
