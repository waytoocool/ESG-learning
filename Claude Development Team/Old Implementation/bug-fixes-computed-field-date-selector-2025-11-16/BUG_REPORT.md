# Bug Report: Computed Field Date Selector Issues

**Date**: 2025-11-16
**Reporter**: User
**Status**: Identified - Ready for Fix
**Priority**: High
**Affected Component**: User Dashboard - Computed Field View Modal

---

## Executive Summary

Two critical usability issues have been identified in the computed field "View Data" modal that prevent users from:
1. Selecting which date to view computed values for
2. Successfully adding data for dependencies from within the computed field modal

## Bug #1: Missing Date Selector in Computed Field View

### Description
When users click "View Data" for a computed field, the modal displays "No Calculated Value" with messages referencing "selected date", but provides **no way to select a date**. Users cannot change the date to view computed values for different time periods.

### Steps to Reproduce
1. Login as user (e.g., bob@alpha.com)
2. Navigate to user dashboard
3. Find a computed field (e.g., "Total rate of new employee hires...")
4. Click "View Data" button
5. Modal opens showing "Cannot Calculate - Missing Data"
6. Message states "No data for selected date" for dependencies
7. **ISSUE**: No date selector is visible anywhere in the modal

### Expected Behavior
- Modal should display a date selector (similar to raw input fields)
- Users should be able to select different dates based on field frequency (Monthly/Annual)
- Computed result should update when date changes
- Clear indication of which date is currently being viewed

### Actual Behavior
- No date selector is present
- Modal shows results for a single fixed date (passed when modal opens)
- Users cannot change the date to view other periods
- Messages reference "selected date" but no date selection interface exists

### Evidence
- Screenshot: `.playwright-mcp/bug-issue1-no-date-selector.png`
- Console Error: `[DateSelector] Container not found: dateSelectorContainer`

---

## Bug #2: Dependency Date Loading Failure

### Description
When attempting to add data for a dependency field from within the computed field modal (by clicking "ADD DATA" button), the dependency modal fails to properly initialize the date selector, preventing users from adding the required data.

### Steps to Reproduce
1. Open computed field "View Data" modal (following steps from Bug #1)
2. In the Dependencies table, click "ADD DATA" button for any missing dependency
3. **ISSUE**: Modal may not open, or opens without proper date selector initialization

### Expected Behavior
- Clicking "ADD DATA" should open the data entry modal for that dependency
- Date selector should be properly initialized with valid dates
- User should be able to select a date and enter data
- After saving, computed field view should refresh with new data

### Actual Behavior
- Dependency modal attempts to open but encounters errors
- DateSelector initialization fails because container element is missing
- User cannot properly add data for dependencies from this workflow

### Evidence
- Screenshot: `.playwright-mcp/bug-issue2-add-data-no-modal.png`
- Console Error: `[DateSelector] Container not found: dateSelectorContainer`

---

## Root Cause Analysis

### Technical Investigation

#### Issue #1 Root Cause
**Location**: `app/static/js/user_v2/computed_field_view.js` + `app/templates/user_v2/dashboard.html`

The computed field view modal reuses the same `dataCollectionModal` as raw input fields, but the workflow is different:

1. **Raw Input Fields**:
   - Keep original `entry-tab` HTML intact
   - Include `dateSelectorContainer` div (line 451 in dashboard.html)
   - DateSelector component initializes successfully

2. **Computed Fields**:
   - `ComputedFieldView.render()` **completely replaces** `entry-tab` innerHTML (line 93 in computed_field_view.js)
   - Destroys the original form structure including `dateSelectorContainer`
   - Renders only computed field-specific content (result, formula, dependencies)
   - **No date selector is included in the rendered HTML**

**Code Reference**:
```javascript
// computed_field_view.js:79-95
render() {
    if (!this.data || !this.container) {
        return;
    }

    const html = `
        <div class="computed-field-view">
            ${this.renderComputedResult()}
            ${this.renderMissingDataWarning()}
            ${this.renderFormula()}
            ${this.renderDependencies()}
        </div>
    `;

    this.container.innerHTML = html;  // ← DESTROYS dateSelectorContainer
    this.attachEditHandlers();
}
```

#### Issue #2 Root Cause
**Location**: `app/static/js/user_v2/computed_field_view.js:345-467`

When clicking "ADD DATA" for a dependency:

1. The `openDependencyModal()` method tries to restore the original form structure (lines 1329-1334 in dashboard.html)
2. However, the DateSelector component tries to initialize and looks for `dateSelectorContainer`
3. Since the container was destroyed and restoration timing may not be perfect, initialization fails
4. Error is logged: `[DateSelector] Container not found: dateSelectorContainer`

**Code Reference**:
```javascript
// dashboard.html:1329-1334
const hasFormStructure = document.getElementById('dateSelectorContainer') !== null;
if (!hasFormStructure) {
    console.log('[Modal Init] Restoring original entry-tab HTML...');
    entryTabContent.innerHTML = window.originalEntryTabHTML;
}
```

The restoration happens, but the DateSelector component may attempt to initialize before the DOM is fully updated, causing intermittent failures.

### System Impact

1. **User Workflow Blocked**: Users cannot view computed values for different time periods
2. **Data Entry Friction**: Adding dependency data from computed field view is unreliable
3. **Confusing UX**: Messages reference "selected date" but no selection mechanism exists
4. **Workaround Required**: Users must close modal, find dependency field in dashboard, then enter data separately

---

## Proposed Solution

### Solution Overview
Add a date selector component to the computed field view modal that:
- Allows users to select which date to view computed results for
- Properly integrates with the computed field frequency (Monthly/Annual)
- Triggers reloading of computed field data when date changes
- Ensures dependency modals can properly initialize their date selectors

### Implementation Approach

#### 1. Add Date Selector to ComputedFieldView
Modify `app/static/js/user_v2/computed_field_view.js`:

```javascript
render() {
    if (!this.data || !this.container) {
        return;
    }

    const html = `
        <div class="computed-field-view">
            ${this.renderDateSelector()}  // ← NEW
            ${this.renderComputedResult()}
            ${this.renderMissingDataWarning()}
            ${this.renderFormula()}
            ${this.renderDependencies()}
        </div>
    `;

    this.container.innerHTML = html;
    this.initializeDateSelector();  // ← NEW
    this.attachEditHandlers();
}

renderDateSelector() {
    return `
        <div class="date-selector-section">
            <div id="computedFieldDateSelectorContainer">
                <!-- Date selector will be rendered here -->
            </div>
        </div>
    `;
}

async initializeDateSelector() {
    // Initialize DateSelector component for computed field
    // Hook up change event to reload computed field data
}
```

#### 2. Fix Dependency Modal Opening
Ensure proper sequencing when opening dependency modals:
- Save current selected date from computed field date selector
- Restore original form structure completely before DateSelector initializes
- Pass correct date context to dependency modal

#### 3. Add CSS Styling
Create appropriate styles for the date selector within computed field view to maintain consistent design.

### Benefits
- ✅ Users can view computed values for any valid date
- ✅ Clear indication of which date is being viewed
- ✅ Dependency data entry workflow works reliably
- ✅ Consistent UX with raw input fields
- ✅ Eliminates confusing error messages

---

## Testing Requirements

### Test Cases

#### TC1: Date Selector Displays in Computed Field Modal
1. Open computed field "View Data" modal
2. **Verify**: Date selector is visible at top of modal
3. **Verify**: Current/default date is selected
4. **Verify**: Available dates match field frequency

#### TC2: Changing Date Reloads Computed Result
1. Open computed field modal
2. Change selected date in date selector
3. **Verify**: Loading indicator appears
4. **Verify**: Computed result refreshes for new date
5. **Verify**: Dependencies table updates with new values

#### TC3: Dependency Modal Opens with Correct Date
1. Open computed field modal
2. Select a specific date
3. Click "ADD DATA" for a dependency
4. **Verify**: Dependency modal opens successfully
5. **Verify**: Date selector in dependency modal shows same date
6. **Verify**: Can enter and save data

#### TC4: Data Entry Persists and Refreshes Computed Field
1. Follow TC3 to add dependency data
2. Save data and close dependency modal
3. **Verify**: Returns to computed field modal
4. **Verify**: Computed field view refreshes automatically
5. **Verify**: New dependency value appears in table
6. **Verify**: Computed result recalculates if all dependencies met

### Regression Testing
- Ensure raw input field modals still work correctly
- Verify date selector works for both Monthly and Annual frequencies
- Test with multiple dependencies
- Test when dependencies are already populated

---

## Files Affected

### Primary Files to Modify
1. `app/static/js/user_v2/computed_field_view.js` - Add date selector rendering and logic
2. `app/static/css/user_v2/computed_field_view.css` - Add date selector styles
3. `app/templates/user_v2/dashboard.html` - Ensure proper modal state management

### Supporting Files (May need review)
1. `app/static/js/user_v2/date_selector.js` - Verify compatibility with computed field use case
2. `app/routes/user_v2/field_api.py` - Ensure API supports date parameter for computed fields

---

## Success Criteria

1. ✅ Date selector visible in computed field view modal
2. ✅ Users can select different dates to view computed values
3. ✅ Computed results update correctly when date changes
4. ✅ Dependency "ADD DATA" buttons work reliably
5. ✅ No console errors related to date selector
6. ✅ Smooth user experience with proper loading states
7. ✅ All existing functionality remains intact

---

## References

- **Screenshots**: `.playwright-mcp/bug-issue1-no-date-selector.png`, `.playwright-mcp/bug-issue2-add-data-no-modal.png`
- **Dashboard Initial**: `.playwright-mcp/bug-test-dashboard-initial.png`
- **Related Components**:
  - ComputedFieldView class: `app/static/js/user_v2/computed_field_view.js`
  - DateSelector class: `app/static/js/user_v2/date_selector.js`
  - Main template: `app/templates/user_v2/dashboard.html`
