# Enhancement #1: Computed Field Modal - MANUAL TESTING GUIDE

**Date:** 2025-11-15
**Version:** 1.0
**Status:** Ready for Manual Execution

---

## 🎯 Testing Objective

Verify that Enhancement #1 (Computed Field Modal) correctly displays calculation details instead of input forms for computed fields, with complete dependency tracking and editing capabilities.

---

## 🔧 Prerequisites

### System Requirements
- Flask application running on: `http://127-0-0-1.nip.io:8000/`
- Browser: Chrome, Firefox, Safari, or Edge (latest version)
- Network: Local development environment

### Test User Credentials
- **URL:** `http://test-company-alpha.127-0-0-1.nip.io:8000/login`
- **Username:** `bob@alpha.com`
- **Password:** `user123`
- **Role:** USER (data entry)

### Test Data Requirements
You will need to create test data for computed field dependencies during this test.

---

## 📋 Complete Test Suite

### Pre-Test Setup

#### Step 0: Verify Application is Running
1. Open terminal
2. Navigate to project directory
3. If not running, start Flask: `python3 run.py`
4. Verify server starts successfully (check for "Running on http://...")
5. Open browser to: `http://test-company-alpha.127-0-0-1.nip.io:8000/login`
6. **Screenshot:** `00-server-running.png`

#### Step 1: Login
1. Navigate to login page
2. Enter username: `bob@alpha.com`
3. Enter password: `user123`
4. Click "Login" button
5. Wait for dashboard to load
6. **Screenshot:** `01-dashboard-loaded.png`
7. **Verify:** User dashboard displays with field cards

#### Step 2: Identify Test Fields
1. On the dashboard, locate the following fields:
   - **Computed Field:** "Total rate of new employee hires during the reporting period, by age group, gen.." (has "Computed" badge)
   - **Dependency A:** "Total new hires" (raw input field)
   - **Dependency B:** "Total number of emloyees" (raw input field)
2. **Screenshot:** `02-field-cards-identified.png`
3. **Note:** If you don't see these fields, select a date using the date picker at the top

---

## 🧪 Test Cases

### TC1: Computed Field with Complete Data

#### Setup: Create Dependency Data

**Part A: Add Data for "Total new hires"**
1. Scroll to find the "Total new hires" field card
2. Verify it has a "Raw Input" badge
3. Click the "Enter Data" button
4. **Screenshot:** `tc1-setup-a1-total-new-hires-modal.png`
5. **Verify modal opens:**
   - Title: "Enter Data: Total new hires"
   - Tab: "Current Entry"
   - Input form visible
   - Submit button visible
6. Select the current date from date picker (if not pre-selected)
7. Enter value: `15`
8. If dimensional grid appears (entities, geography, etc.):
   - Fill in all required dimensions
   - **Screenshot:** `tc1-setup-a2-dimensional-data.png`
9. Click "Save Data" button
10. **Verify:** Success message appears (e.g., "Data saved successfully")
11. **Screenshot:** `tc1-setup-a3-save-success.png`
12. Close the modal

**Part B: Add Data for "Total number of emloyees"**
1. Scroll to find the "Total number of emloyees" field card
2. Click the "Enter Data" button
3. **Screenshot:** `tc1-setup-b1-total-employees-modal.png`
4. Use the SAME date as Part A
5. Enter value: `150`
6. Fill in any required dimensional data
7. Click "Save Data"
8. **Verify:** Success message
9. **Screenshot:** `tc1-setup-b2-save-success.png`
10. Close the modal

#### Test: View Computed Field with Complete Data

1. Refresh the page to ensure calculations are complete
2. Scroll to the computed field: "Total rate of new employee hires..."
3. **Screenshot:** `tc1-1-computed-field-card.png`
4. Click the "View Data" button
5. **Screenshot:** `tc1-2-modal-opened.png`

**Verification Checklist:**
- [ ] **Modal Title:** "View Computed Field: Total rate of new employee hires during the reporting period, by age group, gen.."
- [ ] **Tab Label:** "Calculation & Dependencies" (NOT "Current Entry")
- [ ] **Submit Button:** Hidden/Not present
- [ ] **Result Section Visible:** Yes
  - [ ] Calculated value displayed (should be 15/150 = 0.1 or 10%)
  - [ ] Status badge shows "Complete" with green color
  - [ ] Timestamp displayed ("Last calculated: ...")
  - **Screenshot:** `tc1-3-result-section.png`
- [ ] **Formula Section Visible:** Yes
  - [ ] Human-readable formula: "Total new hires / Total number of emloyees"
  - [ ] Variable mapping shown:
    - A = Total new hires
    - B = Total number of emloyees
  - **Screenshot:** `tc1-4-formula-section.png`
- [ ] **Dependencies Table Visible:** Yes
  - [ ] Variable column shows "A" and "B"
  - [ ] Field names correct
  - [ ] Values shown: A=15, B=150
  - [ ] Status icons: Green checkmarks (✓)
  - [ ] Status text: "Available"
  - [ ] Action buttons: "Edit Data" (NOT "Add Data")
  - **Screenshot:** `tc1-5-dependencies-table.png`
- [ ] **No Warning Message:** Missing data warning should NOT appear
- [ ] **No Input Form:** No text inputs, date pickers, or file upload sections visible

**Expected Result:** ✅ PASS if all checkboxes verified

---

### TC2: Raw Input Field Still Works (Regression Test)

**Objective:** Ensure raw input fields were not affected by Enhancement #1

1. Find any raw input field (e.g., "Total new hires")
2. Click "Enter Data" button
3. **Screenshot:** `tc2-1-raw-field-modal.png`

**Verification Checklist:**
- [ ] **Modal Title:** "Enter Data: [Field Name]" (NOT "View Computed Field")
- [ ] **Tab Label:** "Current Entry" (NOT "Calculation & Dependencies")
- [ ] **Input Form Visible:** Yes
  - [ ] Date picker present
  - [ ] Value input field present
  - [ ] Dimensional grid (if applicable) present
- [ ] **Submit Button:** "Save Data" button visible and enabled
- [ ] **No Calculation View:** No formula, dependencies table, or calculation sections visible
- **Screenshot:** `tc2-2-input-form-visible.png`

**Expected Result:** ✅ PASS if all checkboxes verified

---

### TC3: Computed Field with Missing Dependencies

**Objective:** Verify warning displays when dependencies have no data

**Setup:** Select a date without dependency data
1. On the dashboard, change the date picker to a date far in the future (e.g., December 31, 2025)
2. **Screenshot:** `tc3-1-date-changed.png`
3. Find the computed field "Total rate of new employee hires..."
4. Click "View Data"
5. **Screenshot:** `tc3-2-modal-with-missing-data.png`

**Verification Checklist:**
- [ ] **Warning Box Visible:** Red/orange warning box at top
  - [ ] Icon: ⚠️ or warning icon
  - [ ] Text: "Cannot Calculate - Missing Data"
  - [ ] Lists missing dependencies:
    - "Total new hires (Variable A) - No data for selected date"
    - "Total number of emloyees (Variable B) - No data for selected date"
  - **Screenshot:** `tc3-3-warning-box-detail.png`
- [ ] **Result Section:**
  - [ ] Shows "No Calculated Value" or similar message
  - [ ] Status badge: "No Data" (gray color)
- [ ] **Dependencies Table:**
  - [ ] Variable column shows "A" and "B"
  - [ ] Values: "N/A" or empty
  - [ ] Status icons: Red X (✗)
  - [ ] Status text: "Missing"
  - [ ] Action buttons: "Add Data" (NOT "Edit Data")
  - **Screenshot:** `tc3-4-dependencies-missing-status.png`

**Expected Result:** ✅ PASS if all checkboxes verified

---

### TC4: Formula Display

**Objective:** Verify formula displays in human-readable format

1. Open any computed field (with or without data)
2. Scroll to the "Calculation Formula" section
3. **Screenshot:** `tc4-1-formula-section.png`

**Verification Checklist:**
- [ ] **Section Header:** "📐 Calculation Formula" or similar with icon
- [ ] **Human-Readable Formula:** Shows field names, not raw variables
  - Example: "Total new hires / Total number of emloyees"
  - NOT: "A / B"
- [ ] **Variable Mapping Section Present:** Yes
  - [ ] Shows "Variable Mapping:" or "Variables:" header
  - [ ] Lists each variable with field name:
    - "A = Total new hires"
    - "B = Total number of emloyees"
- [ ] **Clean Formatting:** Formula is easy to read, not code-like
- **Screenshot:** `tc4-2-formula-close-up.png`

**Expected Result:** ✅ PASS if all checkboxes verified

---

### TC5: Dependencies Table Structure

**Objective:** Verify dependencies table has all required columns and data

1. Open computed field modal (with data if possible)
2. Scroll to dependencies table
3. **Screenshot:** `tc5-1-dependencies-table-full.png`

**Verification Checklist:**
- [ ] **Table Headers Present:**
  - [ ] "Variable" column
  - [ ] "Field Name" column
  - [ ] "Current Value" column
  - [ ] "Status" column
  - [ ] "Action" column
  - **Screenshot:** `tc5-2-table-headers.png`
- [ ] **Data Rows:**
  - [ ] At least 2 rows (for variables A and B)
  - [ ] Each row has all columns filled
- [ ] **Variable Column:** Shows letters (A, B, C, etc.)
- [ ] **Field Name Column:**
  - [ ] Shows full field names
  - [ ] May include field type badge (e.g., "Raw Input")
- [ ] **Current Value Column:**
  - [ ] Shows numeric value with unit (if data available)
  - [ ] Shows "N/A" if no data
- [ ] **Status Column:**
  - [ ] Icon (✓ for available, ✗ for missing)
  - [ ] Text ("Available" or "Missing")
  - [ ] Color-coded (green for available, red for missing)
- [ ] **Action Column:**
  - [ ] Button for each dependency
  - [ ] Text: "Edit Data" (if data exists) or "Add Data" (if missing)
  - [ ] Button is clickable

**Expected Result:** ✅ PASS if all checkboxes verified

---

### TC6: Edit Dependency Flow (End-to-End)

**Objective:** Verify clicking "Edit Data" on a dependency opens its modal

**Prerequisites:** Computed field with at least one dependency that has data (use TC1 setup)

1. Open the computed field modal
2. In the dependencies table, find a dependency with data (e.g., "Total new hires")
3. **Screenshot:** `tc6-1-before-click-edit.png`
4. Click the "Edit Data" button for that dependency
5. **IMPORTANT:** Watch what happens next
6. **Screenshot:** `tc6-2-after-click-edit.png`

**Verification Checklist:**
- [ ] **Current Modal Closes:** Computed field modal closes
- [ ] **Dependency Modal Opens:** New modal appears
  - [ ] Modal title: "Enter Data: Total new hires" (the dependency field name)
  - [ ] Shows input form (NOT calculation view)
  - [ ] Pre-populated with existing data
  - **Screenshot:** `tc6-3-dependency-modal-opened.png`
- [ ] **Can Edit Data:**
  - [ ] Change the value (e.g., from 15 to 20)
  - **Screenshot:** `tc6-4-value-changed.png`
  - [ ] Click "Save Data"
  - [ ] Success message appears
  - **Screenshot:** `tc6-5-save-success.png`
- [ ] **Reopen Computed Field:**
  - [ ] Close dependency modal
  - [ ] Click "View Data" on computed field again
  - [ ] Verify dependency value updated to new value (20)
  - [ ] Verify computed result recalculated (20/150 = 0.133 or 13.3%)
  - **Screenshot:** `tc6-6-reopen-updated-value.png`

**Expected Result:** ✅ PASS if all checkboxes verified

**Note:** If clicking "Edit Data" shows an alert like "Field card not found", this is a known limitation when the dependency field is filtered out. Verify the console shows the attempt to open the modal.

---

### TC7: Dark Mode Support

**Objective:** Verify computed field modal is readable in dark mode

**Note:** This test depends on dark mode being available in the application

1. On the dashboard, look for a dark mode toggle (usually in header or settings)
2. If found, enable dark mode
3. **Screenshot:** `tc7-1-dark-mode-enabled.png`
4. If not found, try opening browser DevTools console and run:
   ```javascript
   document.body.classList.add('dark-mode');
   ```
5. Open a computed field modal
6. **Screenshot:** `tc7-2-computed-modal-dark-mode.png`

**Verification Checklist:**
- [ ] **Overall Readability:** All text is readable against dark background
- [ ] **Result Section:**
  - [ ] Background color adapted for dark mode
  - [ ] Text color has good contrast
  - [ ] Status badge readable
- [ ] **Formula Section:**
  - [ ] Text readable
  - [ ] Background appropriate
- [ ] **Dependencies Table:**
  - [ ] Table headers visible
  - [ ] Row backgrounds alternate or have clear separation
  - [ ] Text in all cells readable
  - [ ] Status icons visible
- [ ] **Buttons:**
  - [ ] "Edit Data" / "Add Data" buttons visible
  - [ ] Hover state works
  - [ ] Colors appropriate for dark theme
- [ ] **No Visual Glitches:** No white boxes, invisible text, or broken styling

**Expected Result:** ✅ PASS if dark mode exists and all checkboxes verified
**Expected Result:** ⏭️ SKIP if dark mode not available in application

---

### TC8: Missing Data Warning

**Objective:** Verify prominent warning when dependencies are missing

**Prerequisites:** Use TC3 setup (date without data)

1. Open computed field with missing dependencies
2. Look for the warning box
3. **Screenshot:** `tc8-1-warning-box.png`

**Verification Checklist:**
- [ ] **Warning Box Visible:** Prominent red/orange alert box
- [ ] **Icon Present:** Warning icon (⚠️) or similar
- [ ] **Clear Message:** "Cannot Calculate - Missing Data" or similar
- [ ] **Lists Dependencies:** Shows which dependencies are missing
  - [ ] Each missing dependency listed by name
  - [ ] Indicates no data for selected date
- [ ] **Visual Prominence:**
  - [ ] Warning box stands out (color, size, position)
  - [ ] Located near top of modal content
  - [ ] Easy to notice immediately
- [ ] **Action Guidance:** User understands what to do (add data for dependencies)

**Expected Result:** ✅ PASS if all checkboxes verified

---

### TC9: Console Error Check

**Objective:** Verify no JavaScript errors related to Enhancement #1

1. Open browser DevTools (F12 or Right-click > Inspect)
2. Go to Console tab
3. Clear console
4. Open a computed field modal
5. Check console for errors
6. **Screenshot:** `tc9-1-console-clean.png`

**Verification Checklist:**
- [ ] **No Enhancement #1 Errors:** No errors mentioning:
  - "ComputedFieldView"
  - "computed-field-details"
  - "computed field"
- [ ] **No Critical Errors:** No red error messages
- [ ] **Success Messages Present (Optional):**
  - "[Enhancement #1] ✅ Computed field view initialized"
  - "[Enhancement #1] Opening computed field modal"
  - Other Enhancement #1 log messages

**Note:** Errors from other parts of the application (chatbot, etc.) are acceptable for this test

**Expected Result:** ✅ PASS if no Enhancement #1 errors found

---

### TC10: Network Request Verification

**Objective:** Verify API endpoint is called correctly

1. Open browser DevTools (F12)
2. Go to Network tab
3. Clear network log
4. Open a computed field modal
5. Look for network request
6. **Screenshot:** `tc10-1-network-requests.png`

**Verification Checklist:**
- [ ] **API Request Made:** Request to `/api/user/v2/computed-field-details/<some-id>`
- [ ] **Request Method:** GET
- [ ] **Status Code:** 200 (Success)
- [ ] **Query Parameters Present:**
  - [ ] `entity_id=<number>`
  - [ ] `reporting_date=<YYYY-MM-DD>`
- [ ] **Response Body (Preview):**
  - [ ] `success: true`
  - [ ] `field_name: "..."`
  - [ ] `result: { value, unit, status, calculated_at }`
  - [ ] `formula: "..."`
  - [ ] `dependencies: [...]`
  - **Screenshot:** `tc10-2-response-preview.png`
- [ ] **Response Time:** < 1 second (reasonable performance)

**Expected Result:** ✅ PASS if all checkboxes verified

---

## 📊 Test Results Summary Template

After completing all tests, fill out this summary:

```
=== ENHANCEMENT #1 TESTING RESULTS ===

Date: [YYYY-MM-DD]
Tester: [Your Name]
Browser: [Chrome/Firefox/Safari/Edge + Version]
Environment: Test Company Alpha (bob@alpha.com)

Test Case Results:
[ ] TC1: Computed Field with Complete Data - PASS / FAIL / SKIP
    Issues: [if any]

[ ] TC2: Raw Input Field Regression - PASS / FAIL / SKIP
    Issues: [if any]

[ ] TC3: Computed Field with Missing Dependencies - PASS / FAIL / SKIP
    Issues: [if any]

[ ] TC4: Formula Display - PASS / FAIL / SKIP
    Issues: [if any]

[ ] TC5: Dependencies Table Structure - PASS / FAIL / SKIP
    Issues: [if any]

[ ] TC6: Edit Dependency Flow - PASS / FAIL / SKIP
    Issues: [if any]

[ ] TC7: Dark Mode Support - PASS / FAIL / SKIP
    Issues: [if any]

[ ] TC8: Missing Data Warning - PASS / FAIL / SKIP
    Issues: [if any]

[ ] TC9: Console Error Check - PASS / FAIL / SKIP
    Issues: [if any]

[ ] TC10: Network Request Verification - PASS / FAIL / SKIP
    Issues: [if any]

OVERALL RESULT: [X/10 PASSED]

CRITICAL ISSUES FOUND: [Number]
- [List critical issues]

MINOR ISSUES FOUND: [Number]
- [List minor issues]

RECOMMENDATION:
[ ] READY FOR PRODUCTION
[ ] NEEDS FIXES BEFORE PRODUCTION
[ ] MAJOR REWORK REQUIRED

Additional Notes:
[Any other observations]
```

---

## 📁 Test Artifacts

Save all screenshots to:
```
Claude Development Team/advanced-user-dashboard-enhancements-2025-11-12/
enhancement-1-computed-field-modal/manual-testing/screenshots/
```

Save test results summary to:
```
Claude Development Team/advanced-user-dashboard-enhancements-2025-11-12/
enhancement-1-computed-field-modal/manual-testing/TEST_RESULTS_[DATE].md
```

---

## 🐛 Issue Reporting Template

If you find issues, document them using this template:

```markdown
### Issue #[Number]: [Short Title]

**Severity:** CRITICAL / HIGH / MEDIUM / LOW

**Test Case:** TC[X]

**Description:**
[Detailed description of the issue]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happened]

**Screenshot:**
[Filename of screenshot showing the issue]

**Browser/Environment:**
[Browser, OS, etc.]

**Console Errors:**
[Any console errors, if applicable]

**Workaround:**
[If any workaround exists]
```

---

## ✅ Post-Testing Checklist

After completing all tests:
- [ ] All screenshots captured and organized
- [ ] Test results summary completed
- [ ] All issues documented with severity levels
- [ ] Screenshots uploaded to correct folder
- [ ] Test results file created
- [ ] Critical issues communicated to development team
- [ ] Final recommendation provided

---

## 📞 Support

If you encounter issues during testing:
1. Document the issue with screenshots
2. Check browser console for error messages
3. Verify test data was created correctly
4. Try in a different browser
5. Contact development team with full details

---

**End of Manual Testing Guide**

✅ Ready for execution
🎯 Expected completion time: 45-60 minutes
📊 10 comprehensive test cases
🔍 Thorough validation of Enhancement #1
