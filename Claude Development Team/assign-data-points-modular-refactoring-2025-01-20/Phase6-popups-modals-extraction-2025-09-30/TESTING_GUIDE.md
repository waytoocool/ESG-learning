# Phase 6: PopupsModule Testing Guide

**Date**: September 30, 2025
**Module**: PopupsModule.js
**Test Environment**: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Manual Testing Checklist](#manual-testing-checklist)
3. [Playwright Automated Testing](#playwright-automated-testing)
4. [Expected Behaviors](#expected-behaviors)
5. [Known Issues & Limitations](#known-issues--limitations)
6. [Test Results Template](#test-results-template)

---

## Prerequisites

### Environment Setup
```bash
# 1. Ensure Flask server is running
cd /Users/prateekgoyal/Desktop/Prateek/ESG\ DataVault\ Development/Claude/sakshi-learning
python3 run.py

# 2. Ensure MCP server is running for Playwright tests
npm run mcp:start

# 3. Access the test URL
# http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2
```

### Test Credentials
- **Company**: test-company-alpha
- **Admin User**: alice@alpha.com / admin123
- **Test URL**: `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2`

### Browser Console Checks
Before starting tests, open browser console and verify:
```javascript
// All modules should be loaded
typeof window.PopupsModule !== 'undefined'    // ✅ Should be true
typeof window.AppEvents !== 'undefined'        // ✅ Should be true
typeof window.AppState !== 'undefined'         // ✅ Should be true
```

---

## Manual Testing Checklist

### Test Suite 1: Configuration Modal

#### TC-CM-001: Open Configuration Modal
**Steps:**
1. Navigate to assign-data-points-v2
2. Select 2-3 data points from left panel
3. Click "Configure Selected" in toolbar

**Expected Results:**
- [ ] Configuration modal opens with fade-in animation
- [ ] Modal title shows "Configure Data Points"
- [ ] Selected data points count displayed correctly
- [ ] Console log: `[PopupsModule] Opening Configuration Modal`
- [ ] Event emitted: `modal-opened` with type 'configuration'

#### TC-CM-002: Mixed Configuration Detection
**Steps:**
1. Select data points with different frequencies (one monthly, one quarterly)
2. Open configuration modal
3. Observe frequency field

**Expected Results:**
- [ ] Frequency dropdown shows "Mixed Values" or first item
- [ ] Console shows mixed state detection
- [ ] No pre-selection if values differ

#### TC-CM-003: Form Validation
**Steps:**
1. Open configuration modal
2. Leave frequency field empty
3. Click Save

**Expected Results:**
- [ ] Validation error displayed
- [ ] Field highlighted in red
- [ ] Modal does not close
- [ ] Event: `configuration-validation-error` emitted

#### TC-CM-004: Save Configuration
**Steps:**
1. Fill all required fields
2. Click Save button

**Expected Results:**
- [ ] Event: `configuration-save-requested` emitted
- [ ] Modal closes with fade-out
- [ ] Console: `[PopupsModule] Configuration save requested`
- [ ] Event data includes all form values

#### TC-CM-005: Close Without Saving
**Steps:**
1. Open modal, make changes
2. Click X button or press ESC

**Expected Results:**
- [ ] Modal closes
- [ ] Changes not saved
- [ ] Event: `modal-closed` emitted
- [ ] No `configuration-save-requested` event

---

### Test Suite 2: Entity Assignment Modal

#### TC-EA-001: Open Entity Assignment Modal
**Steps:**
1. Select data points
2. Click "Assign to Entities"

**Expected Results:**
- [ ] Entity assignment modal opens
- [ ] Available entities displayed
- [ ] Entity hierarchy visible (if hierarchical view)
- [ ] Console: `[PopupsModule] Opening Entity Assignment Modal`

#### TC-EA-002: Entity Selection - Flat View
**Steps:**
1. Open entity assignment modal
2. Check individual entity checkbox

**Expected Results:**
- [ ] Checkbox toggles on
- [ ] Entity added to "Selected Entities" section
- [ ] Event: `entity-toggle-requested` emitted
- [ ] Count updates

#### TC-EA-003: Entity Selection - Hierarchy
**Steps:**
1. Switch to hierarchical view
2. Click on parent entity checkbox

**Expected Results:**
- [ ] Parent and all children checked
- [ ] All child entities added to selection
- [ ] Hierarchy expands to show children
- [ ] Console shows entity IDs selected

#### TC-EA-004: Entity Badge Display
**Steps:**
1. Select 3 entities
2. Observe selected entities section

**Expected Results:**
- [ ] 3 entity badges displayed
- [ ] Each badge shows entity name
- [ ] Badge has X button for removal
- [ ] Entity type icon shown (if available)

#### TC-EA-005: Save Entity Assignments
**Steps:**
1. Select entities
2. Click Save

**Expected Results:**
- [ ] Event: `entity-assignments-save-requested` emitted
- [ ] Modal closes
- [ ] Console: `[PopupsModule] Entity assignments save requested`
- [ ] Event includes dataPointIds and entityIds arrays

---

### Test Suite 3: Field Information Modal

#### TC-FI-001: Open Field Info Modal
**Steps:**
1. Click info icon (i) on any data point

**Expected Results:**
- [ ] Field information modal opens
- [ ] Field name displayed
- [ ] Description shown
- [ ] Framework and topic visible
- [ ] Console: `[PopupsModule] Opening Field Information Modal for field: {id}`

#### TC-FI-002: Display Field Metadata
**Steps:**
1. Open field info for a standard field

**Expected Results:**
- [ ] Field type displayed (Text/Number/Computed)
- [ ] Unit category shown
- [ ] Default unit displayed
- [ ] Topic hierarchy shown
- [ ] Framework name visible

#### TC-FI-003: Computed Field Details
**Steps:**
1. Open field info for a computed field

**Expected Results:**
- [ ] "Computed Field" badge shown
- [ ] Calculation formula displayed
- [ ] Dependency list shown
- [ ] Dependency depth calculated
- [ ] Each dependency is a clickable link

#### TC-FI-004: Unit Override Section
**Steps:**
1. Open field info
2. Check unit override section

**Expected Results:**
- [ ] Current default unit shown
- [ ] Unit override dropdown populated with category units
- [ ] Can select alternative unit
- [ ] Unit category label visible

#### TC-FI-005: Conflict Warnings
**Steps:**
1. Open field info for field with conflicts

**Expected Results:**
- [ ] Conflict warning section visible
- [ ] Conflicts listed with details
- [ ] Severity indicators shown
- [ ] Resolution suggestions provided

---

### Test Suite 4: Conflict Resolution Modal

#### TC-CR-001: Trigger Conflict Modal
**Prerequisite:** Create conflicting configuration

**Steps:**
1. Configure a computed field
2. Change frequency that conflicts with dependency
3. Save configuration

**Expected Results:**
- [ ] Conflict resolution modal opens
- [ ] Configuration modal closes
- [ ] Conflicts listed with details
- [ ] Console: `[PopupsModule] Showing conflict resolution modal`

#### TC-CR-002: Display Conflict Details
**Steps:**
1. Open conflict resolution modal
2. Observe conflict display

**Expected Results:**
- [ ] Each conflict shows:
  - Field name
  - Dependency name
  - Issue description
  - Severity level (High/Medium/Low)
- [ ] Severity color-coded (red/orange/yellow)

#### TC-CR-003: Auto-Resolve Conflicts
**Steps:**
1. Open conflict modal with resolvable conflicts
2. Click "Auto-Resolve All"

**Expected Results:**
- [ ] Event: `conflicts-auto-resolve-requested` emitted
- [ ] Modal closes
- [ ] Console: Conflicts to auto-resolve logged

#### TC-CR-004: Force Apply Configuration
**Steps:**
1. Open conflict modal
2. Click "Force Apply Anyway"

**Expected Results:**
- [ ] Warning confirmation shown
- [ ] Event: `configuration-force-apply-requested` emitted
- [ ] Modal closes after confirmation
- [ ] Console warning logged

#### TC-CR-005: Cancel Conflict Resolution
**Steps:**
1. Open conflict modal
2. Click Cancel or X

**Expected Results:**
- [ ] Modal closes
- [ ] No events emitted for save/resolve
- [ ] Returns to previous state

---

### Test Suite 5: Generic Confirmation Dialogs

#### TC-GC-001: Show Success Message
**Test via Console:**
```javascript
PopupsModule.showSuccess("Operation completed successfully!");
```

**Expected Results:**
- [ ] Success notification appears
- [ ] Green checkmark or success icon
- [ ] Message displayed correctly
- [ ] Event: `show-message` emitted with type 'success'
- [ ] Auto-dismisses after timeout (if implemented)

#### TC-GC-002: Show Error Message
**Test via Console:**
```javascript
PopupsModule.showError("An error occurred!");
```

**Expected Results:**
- [ ] Error notification appears
- [ ] Red X or error icon
- [ ] Message displayed
- [ ] Event emitted with type 'error'
- [ ] Console error logged

#### TC-GC-003: Show Warning Message
**Test via Console:**
```javascript
PopupsModule.showWarning("This action cannot be undone");
```

**Expected Results:**
- [ ] Warning notification appears
- [ ] Orange warning icon
- [ ] Message displayed
- [ ] Event emitted with type 'warning'

#### TC-GC-004: Show Confirmation Dialog
**Test via Console:**
```javascript
PopupsModule.showConfirmation({
    title: "Confirm Action",
    message: "Are you sure you want to proceed?",
    confirmText: "Yes, proceed",
    cancelText: "Cancel",
    onConfirm: () => console.log("Confirmed"),
    onCancel: () => console.log("Cancelled")
});
```

**Expected Results:**
- [ ] Confirmation modal appears
- [ ] Title and message displayed
- [ ] Two buttons: Confirm and Cancel
- [ ] Clicking Confirm triggers onConfirm callback
- [ ] Clicking Cancel triggers onCancel callback
- [ ] Events emitted: `confirmation-confirmed` or `confirmation-cancelled`

---

### Test Suite 6: Modal Management

#### TC-MM-001: Open Multiple Modals (Modal Stack)
**Steps:**
1. Open configuration modal
2. Click field info icon from within modal

**Expected Results:**
- [ ] Field info modal opens on top
- [ ] Configuration modal remains behind
- [ ] Modal stack managed correctly
- [ ] Z-index layering correct
- [ ] Both modals in AppState

#### TC-MM-002: Close All Modals
**Test via Console:**
```javascript
PopupsModule.closeAllModals();
```

**Expected Results:**
- [ ] All open modals close
- [ ] Event: `all-modals-closed` emitted
- [ ] Modal stack cleared
- [ ] Console: All modals closed

#### TC-MM-003: Get Active Modal
**Test via Console:**
```javascript
// Open a modal first, then:
PopupsModule.getActiveModal();
```

**Expected Results:**
- [ ] Returns current modal ID (e.g., 'configurationModal')
- [ ] Returns null if no modal open
- [ ] Console shows active modal

#### TC-MM-004: Check Modal Open State
**Test via Console:**
```javascript
PopupsModule.isModalOpen('configurationModal');
```

**Expected Results:**
- [ ] Returns true if modal is open
- [ ] Returns false if modal is closed
- [ ] Accurately reflects modal state

---

### Test Suite 7: Event Integration

#### TC-EI-001: Toolbar Event Triggers Modal
**Steps:**
1. Click "Configure Selected" toolbar button

**Expected Results:**
- [ ] CoreUI emits `toolbar-configure-clicked`
- [ ] PopupsModule listens and responds
- [ ] Configuration modal opens
- [ ] Event flow logged in console

#### TC-EI-002: Modal Emits Save Event
**Steps:**
1. Fill and save configuration

**Expected Results:**
- [ ] PopupsModule emits `configuration-save-requested`
- [ ] Event includes full configuration data
- [ ] Other modules can listen and respond
- [ ] Console shows event emission

#### TC-EI-003: Field Info from Panel
**Steps:**
1. Click (i) icon in data point card

**Expected Results:**
- [ ] Panel emits `show-field-info` with fieldId
- [ ] PopupsModule listens and opens modal
- [ ] Correct field info displayed
- [ ] Event chain logged

---

## Playwright Automated Testing

### Test File Location
Create: `/Users/prateekgoyal/Desktop/Prateek/ESG DataVault Development/Claude/sakshi-learning/Claude Development Team/assign-data-points-modular-refactoring-2025-01-20/Phase6-popups-modals-extraction-2025-09-30/ui-testing-agent/playwright-tests.js`

### Sample Playwright Test

```javascript
const { test, expect } = require('@playwright/test');

test.describe('Phase 6: PopupsModule Tests', () => {
    test.beforeEach(async ({ page }) => {
        // Login as admin
        await page.goto('http://test-company-alpha.127-0-0-1.nip.io:8000/login');
        await page.fill('input[name="email"]', 'alice@alpha.com');
        await page.fill('input[name="password"]', 'admin123');
        await page.click('button[type="submit"]');

        // Navigate to assign-data-points-v2
        await page.goto('http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2');
        await page.waitForLoadState('networkidle');
    });

    test('TC-CM-001: Configuration Modal Opens', async ({ page }) => {
        // Select data points
        await page.click('.data-point-checkbox:first-of-type');
        await page.click('.data-point-checkbox:nth-of-type(2)');

        // Open configuration modal
        await page.click('#configureSelected');

        // Verify modal opened
        await expect(page.locator('#configurationModal')).toBeVisible();

        // Verify console log (requires console event listener)
        const consoleMessages = [];
        page.on('console', msg => consoleMessages.push(msg.text()));

        expect(consoleMessages.some(msg =>
            msg.includes('[PopupsModule] Opening Configuration Modal')
        )).toBeTruthy();
    });

    test('TC-EA-001: Entity Assignment Modal Opens', async ({ page }) => {
        // Select data points
        await page.click('.data-point-checkbox:first-of-type');

        // Click assign to entities
        await page.click('#assignEntities');

        // Verify modal
        await expect(page.locator('#entityModal')).toBeVisible();

        // Verify entities listed
        const entityCount = await page.locator('.entity-item').count();
        expect(entityCount).toBeGreaterThan(0);
    });

    test('TC-FI-001: Field Info Modal Opens', async ({ page }) => {
        // Click info icon on first data point
        await page.click('.field-info-icon:first-of-type');

        // Verify modal opened
        await expect(page.locator('#fieldInfoModal')).toBeVisible();

        // Verify field name displayed
        await expect(page.locator('#fieldInfoModal .field-name')).not.toBeEmpty();
    });

    test('TC-GC-004: Confirmation Dialog Shows', async ({ page }) => {
        // Trigger confirmation via console
        await page.evaluate(() => {
            window.PopupsModule.showConfirmation({
                title: "Test Confirmation",
                message: "Test message",
                confirmText: "Yes",
                cancelText: "No"
            });
        });

        // Verify confirmation dialog visible
        // (Depends on PopupManager implementation)
        await page.waitForTimeout(1000);
        // Add assertions based on actual confirmation dialog structure
    });

    test('TC-MM-002: Close All Modals', async ({ page }) => {
        // Open multiple modals
        await page.click('.data-point-checkbox:first-of-type');
        await page.click('#configureSelected');
        await page.waitForSelector('#configurationModal');

        // Close all modals via console
        await page.evaluate(() => window.PopupsModule.closeAllModals());

        // Verify all closed
        await expect(page.locator('#configurationModal')).not.toBeVisible();
    });
});
```

### Run Playwright Tests
```bash
npx playwright test playwright-tests.js --headed
```

---

## Expected Behaviors

### Modal Opening Sequence
1. User triggers action (button click, event)
2. Event emitted to AppEvents
3. PopupsModule listens and responds
4. Modal DOM elements cached (if not already)
5. Modal data populated
6. Bootstrap Modal.show() called
7. `modal-opened` event emitted
8. Console log confirms opening

### Modal Closing Sequence
1. User clicks X, Cancel, or presses ESC
2. PopupsModule.closeModal() called
3. Bootstrap Modal.hide() called
4. Modal removed from stack
5. `modal-closed` event emitted
6. State cleaned up

### Event Flow Pattern
```
User Action
  ↓
UI Event (click, keypress)
  ↓
Module Method Call
  ↓
AppEvents.emit()
  ↓
Other Modules Listen
  ↓
State Updates
  ↓
UI Updates
```

---

## Known Issues & Limitations

### 1. Import Modal Integration
**Issue:** Import functionality still uses `AssignmentImporter` class from `assign_data_points_import.js`

**Workaround:** Phase 6 provides the modal structure; import logic will be fully integrated in Phase 7

**Test Impact:** Import modal tests may show mixed old/new behavior

### 2. Confirmation Dialog Implementation
**Issue:** Generic confirmation relies on `PopupManager` from `common/popup.js`

**Expected:** PopupsModule provides wrapper, actual rendering via PopupManager

**Test Note:** Verify event emission rather than visual display

### 3. Modal Backdrop Stacking
**Issue:** Multiple modals may have z-index conflicts

**Workaround:** Bootstrap handles basic stacking; complex scenarios may need adjustment

**Test:** Open 3+ nested modals and verify visibility

### 4. Form Validation
**Issue:** Validation logic may still reference legacy code

**Status:** Basic validation in PopupsModule; comprehensive validation in Phase 7

**Test:** Some validation errors may not prevent submission

---

## Test Results Template

### Test Execution Summary

**Date:** ___________________
**Tester:** ___________________
**Environment:** test-company-alpha
**Browser:** ___________________
**Version:** ___________________

### Results

| Test Suite | Total Tests | Passed | Failed | Skipped | Pass Rate |
|------------|-------------|--------|--------|---------|-----------|
| Configuration Modal | 5 | ___ | ___ | ___ | ___% |
| Entity Assignment | 5 | ___ | ___ | ___ | ___% |
| Field Information | 5 | ___ | ___ | ___ | ___% |
| Conflict Resolution | 5 | ___ | ___ | ___ | ___% |
| Generic Confirmations | 4 | ___ | ___ | ___ | ___% |
| Modal Management | 4 | ___ | ___ | ___ | ___% |
| Event Integration | 3 | ___ | ___ | ___ | ___% |
| **TOTAL** | **31** | ___ | ___ | ___ | ___% |

### Critical Issues Found

1. _______________________________________________________________
2. _______________________________________________________________
3. _______________________________________________________________

### Non-Critical Issues

1. _______________________________________________________________
2. _______________________________________________________________

### Performance Observations

- Modal open time: ______ ms
- Modal close time: ______ ms
- Event propagation delay: ______ ms
- Memory usage after 50 open/close cycles: ______ MB

### Browser Compatibility

| Browser | Version | Status | Notes |
|---------|---------|--------|-------|
| Chrome | ___ | ⬜ Pass / ⬜ Fail | ___________ |
| Firefox | ___ | ⬜ Pass / ⬜ Fail | ___________ |
| Safari | ___ | ⬜ Pass / ⬜ Fail | ___________ |
| Edge | ___ | ⬜ Pass / ⬜ Fail | ___________ |

### Recommendations

1. _______________________________________________________________
2. _______________________________________________________________
3. _______________________________________________________________

### Sign-off

**Tester Signature:** ___________________
**Date:** ___________________
**Status:** ⬜ Approved ⬜ Approved with Issues ⬜ Not Approved

---

## Appendix: Console Command Reference

### Useful Console Commands for Testing

```javascript
// Check module loaded
typeof window.PopupsModule

// Check initialization
window.PopupsModule.state

// Manually trigger modals
window.AppEvents.emit('toolbar-configure-clicked');
window.AppEvents.emit('toolbar-assign-clicked');
window.AppEvents.emit('show-field-info', 'field-id-here');

// Show messages
window.PopupsModule.showSuccess("Test success");
window.PopupsModule.showError("Test error");
window.PopupsModule.showWarning("Test warning");
window.PopupsModule.showInfo("Test info");

// Modal management
window.PopupsModule.getActiveModal();
window.PopupsModule.isModalOpen('configurationModal');
window.PopupsModule.closeAllModals();

// Check event listeners
window.AppEvents.listeners

// Check state
window.AppState.selectedDataPoints
window.AppState.configurations
```

---

**Document Version:** 1.0
**Last Updated:** September 30, 2025
**Status:** ✅ Ready for Use