# Manual Test Script: Collapsible Dependency Grouping Feature
**Feature:** Collapsible Dependency Grouping in Selected Data Points Panel
**Date:** 2025-11-10
**Tester:** QA Team
**Status:** PENDING MANUAL TEST

---

## Background

### Bug Fixed
The DependencyManager was not exposing its internal state through public API methods, causing the SelectedDataPointsPanel to fail to render the collapsible dependency grouping feature.

### Fix Applied
Added three public getter methods to DependencyManager:
- `getDependencyMap()` - returns computed field to dependencies mapping
- `getReverseDependencyMap()` - returns reverse mapping
- `getAllFieldMetadata()` - returns all field metadata

Updated SelectedDataPointsPanel.js to use these getter methods instead of accessing private state.

---

## Test Environment Setup

1. **Flask Server**: http://127-0-0-1.nip.io:8000 (RUNNING)
2. **Login Credentials**: alice@alpha.com / admin123
3. **Test URL**: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points
4. **Browser**: Chrome/Firefox (latest)
5. **Screen Resolution**: 1280x720 or higher

---

## Pre-Test Checklist

- [ ] Clear browser cache and cookies
- [ ] Open browser DevTools (F12)
- [ ] Switch to Console tab
- [ ] Navigate to login page
- [ ] Login as admin (alice@alpha.com / admin123)

---

## CRITICAL TEST CASE 1: Visual Elements Render Correctly

### Steps:
1. Navigate to: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points
2. Wait for page to fully load (watch console for "DependencyManager Initialized")
3. In the left panel, find a computed field:
   - Look for purple badge 🧮
   - Example field: "Total rate of new employee hires"
4. Click to select the computed field
5. Watch the right panel (Selected Data Points Panel)

### Expected Results:

#### Visual Elements (ALL must be present):
- [ ] **Toggle Button**: Chevron button on left side of computed field
- [ ] **Purple Border**: Left border on computed field (color: #8b5cf6)
- [ ] **Calculator Icon**: 🧮 icon next to field name
- [ ] **Dependency Count Badge**: Blue badge showing number like "(2)"
- [ ] **Dependencies Listed**: Child fields listed below (when expanded)
- [ ] **Arrow Indicator**: ➘ icon on each dependency field
- [ ] **Blue Border**: Left border on dependency fields (color: #3b82f6)

#### Console Messages:
- [ ] Console shows: "[SelectedDataPointsPanel] Generating flat HTML with dependency grouping..."
- [ ] Console shows: "[DependencyManager] Auto-adding X dependencies for..."
- [ ] **NO errors** about "state" being undefined
- [ ] **NO warnings** about missing properties

### Screenshot Requirements:
- Take screenshot showing computed field EXPANDED with all visual elements
- Take screenshot showing computed field COLLAPSED
- Take screenshot of browser console showing log messages

---

## TEST CASE 2: Toggle Functionality

### Steps:
1. Continue from Test Case 1
2. Click the chevron toggle button (left side of computed field)
3. Observe the animation
4. Click again to toggle back
5. Repeat 3-4 times

### Expected Results:
- [ ] **Collapse Animation**: Dependencies collapse smoothly (0.3s transition)
- [ ] **Expand Animation**: Dependencies expand smoothly (0.3s transition)
- [ ] **Chevron Rotation**:
  - → (right arrow) when COLLAPSED
  - ↓ (down arrow) when EXPANDED
- [ ] **State Persistence**: After toggling multiple times, state remains consistent
- [ ] **No Flickering**: Animation is smooth without visual glitches

### Screenshot Requirements:
- Take screenshot showing transition mid-animation (if possible)
- Take screenshot of final collapsed state
- Take screenshot of final expanded state

---

## TEST CASE 3: Multiple Computed Fields

### Steps:
1. Select TWO different computed fields from the left panel
2. Verify both appear in the right panel
3. Expand the first computed field
4. Expand the second computed field
5. Collapse the first computed field
6. Verify the second remains expanded

### Expected Results:
- [ ] **Independent State**: Each computed field has its own collapse/expand state
- [ ] **No Duplication**: Dependencies appear only once (under their parent)
- [ ] **Correct Grouping**: Each dependency is grouped under the correct computed field
- [ ] **Visual Separation**: Clear visual separation between computed field groups

### Screenshot Requirements:
- Take screenshot showing 2 computed fields: one expanded, one collapsed
- Take screenshot showing both expanded
- Take screenshot showing both collapsed

---

## TEST CASE 4: Styling Validation

### Steps:
1. Using browser DevTools, inspect the computed field element
2. Verify CSS styles are applied correctly
3. Hover over toggle button
4. Hover over computed field
5. Hover over dependency fields

### Expected Results:

#### Color Verification:
- [ ] **Computed field border**: #8b5cf6 (purple)
- [ ] **Computed field toggle button**: #8b5cf6 (purple)
- [ ] **Dependency border**: #3b82f6 (blue)
- [ ] **Dependency count badge background**: #3b82f6 (blue)
- [ ] **Dependency count badge text**: white

#### Hover Effects:
- [ ] **Toggle button scales up** on hover (transform: scale(1.1))
- [ ] **Computed field background** lightens on hover
- [ ] **Dependency background** lightens on hover
- [ ] **Cursor changes** to pointer on interactive elements

#### Layout:
- [ ] **Toggle button** aligned to left
- [ ] **Checkbox** next to toggle button
- [ ] **Content** flows naturally
- [ ] **Dependency indent** visible (left padding)

### Screenshot Requirements:
- Screenshot of DevTools showing computed field CSS
- Screenshot of toggle button hover state
- Screenshot showing color values in DevTools

---

## TEST CASE 5: Console Error Check (CRITICAL)

### Steps:
1. Open browser console (F12)
2. Clear console
3. Navigate to assign data points page
4. Select a computed field
5. Observe console messages
6. Look for any errors or warnings

### Expected Results:
- [ ] **NO errors** about "Cannot read property 'dependencyMap' of undefined"
- [ ] **NO errors** about "state is not defined"
- [ ] **NO errors** about "getDependencyMap is not a function"
- [ ] **SHOULD see**: "[SelectedDataPointsPanel] Generating flat HTML with dependency grouping..."
- [ ] **SHOULD see**: "[DependencyManager] Auto-adding X dependencies..."

### Screenshot Requirements:
- Screenshot of console showing ONLY success messages (no errors)
- If errors exist, screenshot the full error stack trace

---

## TEST CASE 6: Dependency Removal Protection

### Steps:
1. Select a computed field with dependencies
2. Verify dependencies auto-select
3. Try to remove ONE dependency (click trash icon)
4. Observe warning dialog

### Expected Results:
- [ ] **Warning Dialog**: Appears saying dependency is required
- [ ] **Lists Computed Fields**: Shows which computed fields depend on it
- [ ] **Confirm/Cancel Options**: User can choose to proceed or cancel
- [ ] **If Confirmed**: Both dependency and computed field removed
- [ ] **If Cancelled**: Dependency remains selected

---

## TEST CASE 7: State Persistence

### Steps:
1. Select multiple computed fields
2. Expand some, collapse others
3. Navigate away from the page (e.g., go to dashboard)
4. Navigate back to assign data points page
5. Observe the state

### Expected Results:
- [ ] **Collapse state persists**: Groups remain in their collapsed/expanded state
- [ ] **Session storage used**: State stored in sessionStorage
- [ ] **Clears on new session**: State resets when browser tab is closed

---

## PASS/FAIL CRITERIA

### CRITICAL (Must Pass All):
- [ ] Test Case 1: Visual elements render correctly
- [ ] Test Case 2: Toggle functionality works
- [ ] Test Case 5: No console errors

### IMPORTANT (Must Pass At Least 80%):
- [ ] Test Case 3: Multiple computed fields work independently
- [ ] Test Case 4: Styling matches design specifications
- [ ] Test Case 6: Dependency removal protection works

### NICE TO HAVE:
- [ ] Test Case 7: State persistence works

---

## Bug Report Template (Use if test fails)

### Bug Title:
[Descriptive title of the issue]

### Severity:
- [ ] P0 - Critical (Feature completely broken)
- [ ] P1 - High (Major functionality impaired)
- [ ] P2 - Medium (Minor functionality impaired)
- [ ] P3 - Low (Cosmetic issue)

### Steps to Reproduce:
1.
2.
3.

### Expected Result:
[What should happen]

### Actual Result:
[What actually happened]

### Screenshots:
[Attach screenshots]

### Console Errors:
```
[Paste console errors here]
```

### Browser Info:
- Browser:
- Version:
- OS:

### Additional Notes:
[Any other relevant information]

---

## Test Completion

**Date Completed:** _______________
**Tester Name:** _______________
**Overall Result:** [ ] PASS [ ] FAIL

**Summary:**
[Brief summary of test results]

**Issues Found:**
1.
2.
3.

**Recommendations:**
[Any recommendations for improvement]

---

## Notes for QA Team

### Known Limitations:
1. Playwright MCP connection issue prevented automated testing
2. Manual testing required for this verification
3. Focus on console messages to confirm API fix

### Key Focus Areas:
1. **Console Messages**: This is the primary indicator that the fix worked
2. **Visual Rendering**: All 7 elements must be present (see Test Case 1)
3. **No JavaScript Errors**: Critical indicator of API fix success

### Quick Smoke Test:
If time is limited, perform Test Cases 1 and 5 only. These are the critical indicators that the bug is fixed.

