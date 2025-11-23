# Manual Testing Guide: Computed Field Dependency Feature

**Purpose:** Step-by-step instructions for manual browser testing
**Target Users:** QA Engineers, Product Managers, Developers
**Estimated Time:** 30-45 minutes
**Prerequisites:** Flask app running, test data loaded

---

## Setup Instructions

### 1. Start the Application

```bash
# Navigate to project directory
cd /Users/prateekgoyal/Desktop/Prateek/ESG\ DataVault\ Development/Claude/sakshi-learning/

# Start Flask server
python3 run.py

# Expected output:
# * Running on http://127-0-0-1.nip.io:8000/
```

### 2. Open Browser

**Recommended Browsers:**
- Chrome (latest version)
- Firefox (latest version)

**URL:** http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points

### 3. Login

**Credentials:**
- **Email:** alice@alpha.com
- **Password:** admin123
- **Role:** ADMIN

### 4. Open Developer Tools

**Chrome/Firefox:**
- Press `F12` or `Cmd+Option+I` (Mac) or `Ctrl+Shift+I` (Windows)
- Switch to **Console** tab
- Keep DevTools open throughout testing

---

## Pre-Test Verification

Before running test cases, verify the environment is ready:

### Checklist:

```javascript
// Type these commands in browser console:

// 1. Check DependencyManager exists
window.DependencyManager
// Expected: Object with methods (init, handleFieldSelection, etc.)

// 2. Check if DependencyManager is ready
window.DependencyManager.isReady()
// Expected: true

// 3. Check dependency map has data
window.DependencyManager.getDependencyMap()
// Expected: Map with 2 or more entries

// 4. Check SelectDataPointsPanel exists
window.SelectDataPointsPanel
// Expected: Object with methods

// 5. Check for console errors
// Expected: No red error messages
```

**If any check fails:** Refresh the page and wait 5 seconds, then retry

---

## Test Case 1: Auto-Cascade Selection

**Priority:** P0 (CRITICAL)
**Estimated Time:** 5 minutes

### Objective
Verify that selecting a computed field automatically adds its dependencies

### Steps

1. **Clear any existing selections**
   - If selected panel has items, click "Remove" on each to clear

2. **Search for computed field**
   - Type in search box: `employee turnover`
   - Wait for search results to filter

3. **Identify the computed field**
   - Look for: "Total rate of employee turnover during the reporting period, by age group, gender and region"
   - Should have **purple badge** with calculator icon 🧮
   - Badge should show **(2)** indicating 2 dependencies

4. **Add the computed field**
   - Click the **"+"** button next to the field name
   - Watch the selected panel on the right

### Expected Results

✅ **Pass Criteria:**
- [ ] 3 fields appear in selected panel (1 computed + 2 dependencies)
- [ ] Success notification appears at top: "Added 'Total rate of employee turnover...' and 2 dependencies"
- [ ] Counter shows "3 data points selected"
- [ ] No errors in console
- [ ] The 2 dependency fields are:
  - "Number of employees who left the organization during the reporting period"
  - "Total number of employees"

❌ **Fail Criteria:**
- Only 1 field appears (computed field alone)
- Console shows TypeError or other errors
- No notification appears

### Screenshot Checklist
- [ ] Before adding field (showing purple badge)
- [ ] After adding field (showing 3 fields in panel)
- [ ] Success notification
- [ ] Console logs (should show no errors)

---

## Test Case 2: Partial Dependency Already Selected

**Priority:** P0 (CRITICAL)
**Estimated Time:** 5 minutes

### Objective
Verify system doesn't duplicate dependencies that are already selected

### Steps

1. **Clear selections** (start fresh)

2. **Manually add one dependency first**
   - Search for: `total number of employees`
   - Find: "Total number of employees"
   - Click "+" to add it
   - Verify: 1 field in selected panel

3. **Now add the computed field**
   - Search for: `employee turnover`
   - Find: "Total rate of employee turnover during the reporting period..."
   - Click "+" to add it

### Expected Results

✅ **Pass Criteria:**
- [ ] Only 2 fields added total (not 3)
- [ ] "Total number of employees" is NOT duplicated
- [ ] Notification says: "Added 'Total rate of employee turnover...' and 1 dependency"
- [ ] Info message mentions: "'Total number of employees' already selected"
- [ ] Counter shows "2 data points selected"
- [ ] Only the missing dependency is auto-added

❌ **Fail Criteria:**
- 3 fields appear (duplicate "Total number of employees")
- Counter shows incorrect count
- Notification doesn't mention already-selected field

### Screenshot Checklist
- [ ] After manually adding first dependency (1 field)
- [ ] After adding computed field (2 fields total)
- [ ] Notification with "1 dependency" message
- [ ] Console logs

---

## Test Case 3: Visual Indicators (Purple Badges)

**Priority:** P0 (CRITICAL)
**Estimated Time:** 5 minutes

### Objective
Verify computed fields show purple badges with dependency counts

### Steps

1. **Clear selections**

2. **Check Topic Tree view**
   - Expand topic: "GRI 401: Employment 2016"
   - Locate fields:
     - GRI401-1-a: "Total rate of new employee hires..."
     - GRI401-1-b: "Total rate of employee turnover..."

3. **Check badges in topic tree**
   - Look for purple/lavender badge next to field name
   - Badge should have calculator icon (🧮)
   - Badge should show "(2)" or similar number

4. **Switch to "All Fields" view**
   - Click "All Fields" tab/view
   - Search for same fields
   - Verify badges still appear

### Expected Results

✅ **Pass Criteria:**
- [ ] Purple badges visible in Topic Tree view
- [ ] Purple badges visible in All Fields view
- [ ] Calculator icon (🧮) present
- [ ] Dependency count "(2)" visible
- [ ] Badges have consistent styling
- [ ] Hover tooltip shows: "Computed Field - Depends on X fields"

❌ **Fail Criteria:**
- No badges visible
- Badges only show in one view but not the other
- Missing calculator icon
- Missing dependency count

### Screenshot Checklist
- [ ] Topic tree with expanded GRI 401 (showing badges)
- [ ] All Fields view (showing badges)
- [ ] Close-up of badge (with tooltip if possible)

---

## Test Case 4: Collapsible Dependency Grouping

**Priority:** P0 (NEW FEATURE)
**Estimated Time:** 10 minutes

### Objective
Verify dependencies can be collapsed/expanded under computed fields

### Steps

1. **Clear selections**

2. **Add a computed field with dependencies**
   - Search for: `employee turnover`
   - Add: "Total rate of employee turnover..."
   - Verify: 3 fields added

3. **Inspect the selected panel structure**
   - Look for computed field at the top
   - Look for **chevron/toggle button** (▾ or ▸) to the left of computed field name
   - Verify dependencies appear **indented** below computed field
   - Dependencies should be **expanded** by default (visible)

4. **Click the toggle button**
   - Click the chevron button next to computed field
   - Watch the dependencies

5. **Click again to re-expand**
   - Click chevron again
   - Watch dependencies reappear

### Expected Results

✅ **Pass Criteria:**
- [ ] Toggle button (chevron) is visible next to computed field
- [ ] Dependencies are grouped/indented under computed field
- [ ] Clicking toggle collapses dependencies (fade out, slide up)
- [ ] Chevron changes from ▾ (down) to ▸ (right) when collapsed
- [ ] Clicking again re-expands dependencies
- [ ] Chevron changes back to ▾ when expanded
- [ ] Smooth CSS transition (not instant jump)
- [ ] Console log shows: "[SelectedDataPointsPanel] Generating flat HTML with dependency grouping..."

❌ **Fail Criteria:**
- No toggle button visible
- Dependencies not grouped/indented
- Clicking toggle does nothing
- No CSS transition
- Console shows: "[SelectedDataPointsPanel] DependencyManager not ready"

### Special Debugging Steps (If Feature Not Working)

**If you don't see the toggle button or grouping:**

```javascript
// In browser console, run:

// 1. Check if DependencyManager is ready
console.log('DM Ready:', window.DependencyManager.isReady());
// Should be: true

// 2. Check if grouping HTML was generated
console.log('Grouping elements:', document.querySelectorAll('.computed-field-group').length);
// Should be: > 0

// 3. Check for toggle buttons
console.log('Toggle buttons:', document.querySelectorAll('.dependency-toggle-btn').length);
// Should be: > 0

// 4. Check for dependencies container
const depDiv = document.querySelector('.computed-field-dependencies');
console.log('Dependencies div:', depDiv);
console.log('Classes:', depDiv ? depDiv.classList : 'NOT FOUND');
// Should show: expanded or collapsed

// 5. Force a click on toggle button
const toggleBtn = document.querySelector('.dependency-toggle-btn');
if (toggleBtn) {
    console.log('Clicking toggle button...');
    toggleBtn.click();
    console.log('After click classes:', document.querySelector('.computed-field-dependencies').classList);
} else {
    console.log('ERROR: No toggle button found!');
}
```

### Screenshot Checklist
- [ ] Expanded state (dependencies visible)
- [ ] Collapsed state (dependencies hidden)
- [ ] Toggle button with chevron icon
- [ ] Console logs showing grouping generation
- [ ] (If not working) Console logs showing DependencyManager status

---

## Test Case 5: Removal Protection

**Priority:** P1 (HIGH)
**Estimated Time:** 5 minutes

### Objective
Verify user cannot accidentally remove dependency without removing computed field

### Steps

1. **Setup**
   - Clear selections
   - Add computed field: "Total rate of employee turnover..."
   - Verify: 3 fields in panel (1 computed + 2 dependencies)

2. **Try to remove a dependency**
   - Find one of the dependency fields in selected panel
   - Click the **"×"** (remove) button next to the dependency field
   - Watch for warning modal

3. **Check warning modal**
   - Read the message
   - Verify it lists the computed field that depends on this field
   - Look for buttons: "Cancel" and "Remove Both"

4. **Click "Cancel"**
   - Click "Cancel" button
   - Modal should close
   - Verify field is still in selected panel

### Expected Results

✅ **Pass Criteria:**
- [ ] Warning modal appears when trying to remove dependency
- [ ] Modal title: "Cannot Remove Dependency" or similar
- [ ] Modal message shows which computed field(s) depend on this field
- [ ] "Cancel" button present
- [ ] "Remove Both" button present
- [ ] Clicking "Cancel" keeps field selected
- [ ] No fields are removed

❌ **Fail Criteria:**
- Dependency is removed without warning
- No modal appears
- Modal missing critical information

### Screenshot Checklist
- [ ] Before removing (3 fields visible)
- [ ] Warning modal (showing computed field dependency)
- [ ] After clicking Cancel (still 3 fields)

---

## Test Case 6: Cascade Removal

**Priority:** P1 (HIGH)
**Estimated Time:** 5 minutes

### Objective
Verify "Remove Both" option removes dependency and computed field

### Steps

1. **Setup** (same as TC-5)
   - Clear selections
   - Add: "Total rate of employee turnover..." (3 fields total)

2. **Try to remove a dependency**
   - Click "×" next to one dependency field
   - Warning modal appears

3. **Click "Remove Both"**
   - Click "Remove Both" button in modal
   - Watch selected panel

### Expected Results

✅ **Pass Criteria:**
- [ ] Both the dependency AND the computed field are removed
- [ ] The other dependency remains (if it's not dependent on the computed field)
- [ ] Counter updates correctly (decreases by 2)
- [ ] Success/info notification appears
- [ ] No errors in console

❌ **Fail Criteria:**
- Only dependency removed, computed field remains (invalid state!)
- All 3 fields removed (should only remove 2)
- Console errors

### Screenshot Checklist
- [ ] Before removal (3 fields)
- [ ] Warning modal with "Remove Both" button
- [ ] After removal (1 field remaining)
- [ ] Success notification

---

## Test Case 7: Search and Filter

**Priority:** P2 (MEDIUM)
**Estimated Time:** 3 minutes

### Objective
Verify purple badges remain visible in search results

### Steps

1. **Use search**
   - Type in search box: `employee`
   - Wait for results to filter

2. **Check search results**
   - Look for computed fields in results
   - Verify purple badges are still visible
   - Badges should show dependency count

3. **Toggle "Show Inactive"**
   - If toggle exists, click it
   - Verify badges remain on computed fields

### Expected Results

✅ **Pass Criteria:**
- [ ] Purple badges visible in search results
- [ ] Badges show correct dependency counts
- [ ] Badges remain when toggling filters
- [ ] Search doesn't break badge rendering

---

## Test Case 8: Regression - Manual Selection

**Priority:** P0 (REGRESSION)
**Estimated Time:** 3 minutes

### Objective
Verify non-computed fields still work normally

### Steps

1. **Clear selections**

2. **Manually add regular (raw) fields**
   - Search for: `scope 1`
   - Find a regular field (without purple badge)
   - Add 3-4 regular fields

3. **Verify behavior**
   - Each field should add individually
   - No auto-cascade should occur
   - Counter increments by 1 per field

### Expected Results

✅ **Pass Criteria:**
- [ ] Regular fields add normally (one at a time)
- [ ] No auto-cascade for non-computed fields
- [ ] Counter increments correctly
- [ ] No unexpected dependencies added
- [ ] No errors in console

---

## Test Case 9: Edge Case - Shared Dependency

**Priority:** P1 (EDGE CASE)
**Estimated Time:** 7 minutes

### Objective
Verify shared dependencies aren't duplicated

### Steps

1. **Clear selections**

2. **Find two computed fields that share a dependency**
   - GRI401-1-a: "Total rate of new employee hires..." (depends on "Total number of employees")
   - GRI401-1-b: "Total rate of employee turnover..." (depends on "Total number of employees")

3. **Add first computed field**
   - Add GRI401-1-a
   - Verify: 3 fields added (including "Total number of employees")

4. **Add second computed field**
   - Add GRI401-1-b
   - Watch selected panel carefully

5. **Try to remove shared dependency**
   - Click "×" next to "Total number of employees"
   - Check warning modal

### Expected Results

✅ **Pass Criteria:**
- [ ] After adding 2nd computed field: "Total number of employees" is NOT duplicated
- [ ] Total fields: 5 (2 computed + 3 unique dependencies)
- [ ] Warning modal shows BOTH computed fields will be affected
- [ ] Removing shared dependency removes both computed fields

❌ **Fail Criteria:**
- "Total number of employees" appears twice
- Warning only shows one computed field
- Incorrect count of fields

### Screenshot Checklist
- [ ] After first computed field (3 fields)
- [ ] After second computed field (5 fields, no duplicates)
- [ ] Warning modal showing both computed fields

---

## Post-Test Checklist

### Summary

After completing all tests, fill out:

| Test Case | Status | Notes |
|-----------|--------|-------|
| TC-1: Auto-Cascade | ⬜ PASS / ⬜ FAIL | |
| TC-2: Partial Dependency | ⬜ PASS / ⬜ FAIL | |
| TC-3: Visual Indicators | ⬜ PASS / ⬜ FAIL | |
| TC-4: Collapsible Grouping | ⬜ PASS / ⬜ FAIL | |
| TC-5: Removal Protection | ⬜ PASS / ⬜ FAIL | |
| TC-6: Cascade Removal | ⬜ PASS / ⬜ FAIL | |
| TC-7: Search & Filter | ⬜ PASS / ⬜ FAIL | |
| TC-8: Manual Selection | ⬜ PASS / ⬜ FAIL | |
| TC-9: Shared Dependency | ⬜ PASS / ⬜ FAIL | |

### Overall Result

- ✅ **PASS**: 8+ test cases pass, no P0 failures
- ⚠️ **CONDITIONAL PASS**: 6-7 test cases pass, collapsible grouping fails but other features work
- ❌ **FAIL**: Any P0 test fails (auto-cascade, visual indicators, manual selection)

### Bug Reporting

If any test fails, record:
1. Test case number and name
2. Expected behavior
3. Actual behavior
4. Console error messages (if any)
5. Screenshots
6. Browser and version

---

## Console Logs Reference

### Good Console Logs (Feature Working)

```
[DependencyManager] Loading dependency tree...
[DependencyManager] Loaded 2 computed fields with dependencies
[DependencyManager] Ready
[DependencyManager] Auto-adding 2 dependencies for [field-id]
[DependencyManager] Added dependencies: [field-id-1], [field-id-2]
[SelectedDataPointsPanel] Generating flat HTML...
[SelectedDataPointsPanel] Generating flat HTML with dependency grouping...
[NotificationManager] Success: Added 'Field Name' and 2 dependencies
```

### Bad Console Logs (Feature Broken)

```
❌ TypeError: Cannot read properties of undefined (reading 'find')
❌ [DependencyManager] Failed to load dependency tree
❌ [SelectedDataPointsPanel] DependencyManager not ready
❌ ReferenceError: DependencyManager is not defined
```

---

## Troubleshooting

### Issue: No purple badges visible

**Check:**
1. Refresh page (hard refresh: Cmd+Shift+R / Ctrl+Shift+F5)
2. Clear browser cache
3. Verify API endpoint returns `is_computed: true`
4. Check browser console for JavaScript errors

### Issue: Auto-cascade doesn't work

**Check:**
1. Console for TypeError
2. `window.DependencyManager.isReady()` returns true
3. Field is actually a computed field (has purple badge)
4. Try waiting 5 seconds after page load, then try again

### Issue: Collapsible grouping doesn't appear

**Check:**
1. `window.DependencyManager.isReady()` returns true BEFORE adding field
2. Console shows: "[SelectedDataPointsPanel] Generating flat HTML with dependency grouping..."
3. If shows "DependencyManager not ready", wait longer after page load
4. Check DOM: `document.querySelector('.computed-field-group')`

### Issue: Toggle button doesn't work

**Check:**
1. Button exists in DOM
2. Click event registered
3. CSS classes changing (expanded ↔ collapsed)
4. Browser DevTools > Elements > watch classes change on click

---

## Quick Reference: Test Data

### Computed Fields to Test

**GRI 401: Employment 2016**
- GRI401-1-a: "Total rate of new employee hires during the reporting period, by age group, gender and region"
  - Depends on: 2 fields
- GRI401-1-b: "Total rate of employee turnover during the reporting period, by age group, gender and region"
  - Depends on: 2 fields

**Shared Dependency:**
- "Total number of employees" (used by both GRI401-1-a and GRI401-1-b)

---

**Testing Guide Version:** 1.0
**Last Updated:** 2025-11-10
**Prepared By:** UI Testing Agent
