# CRITICAL BUG REPORT: Computed Field Modal Not Opening

**Date**: 2025-11-15
**Tester**: ui-testing-agent
**Environment**: test-company-alpha (bob@alpha.com)
**Severity**: CRITICAL - BLOCKS ALL TESTING
**Status**: PRODUCTION NOT READY

---

## Executive Summary

Enhancement #1 (Computed Field Modal) has a critical bug that completely blocks its functionality. When clicking "View Data" on a computed field, the system opens the **WRONG MODAL TYPE** - it opens the raw input modal instead of the computed field modal with calculation view.

This means **Enhancement #1 is not working at all** - the computed field modal feature has never been triggered.

---

## Bug Description

### Expected Behavior
When clicking "View Data" button on a computed field:
1. Should detect field type as "computed"
2. Should open modal with title "View Computed Field: [field name]"
3. Should show tab labeled "Calculation & Dependencies" (NOT "Current Entry")
4. Should display:
   - Calculation result
   - Formula display
   - Dependencies table with "Edit" buttons
   - NO input fields
   - NO "Save Data" button

### Actual Behavior
When clicking "View Data" button on a computed field:
1. System logs: `[Enhancement #1] Opening raw input field modal`
2. Opens modal with title "Enter Data: [field name]"
3. Shows tab labeled "Current Entry"
4. Shows **dimensional input grid** with editable fields
5. Shows "Save Data" button
6. **Completely wrong modal type!**

---

## Steps to Reproduce

1. Login as bob@alpha.com
2. Navigate to dashboard (no date selection required)
3. Scroll to "Energy Management" section
4. Find computed field: "Total rate of new employee hires during the reporting period, by age group, gender and region."
   - Field card shows "Computed" badge
   - Field card shows "View Data" button
5. Click "View Data" button
6. **BUG**: Wrong modal opens (raw input instead of computed)

---

## Evidence

### Database Verification
Field is correctly configured as computed:
```sql
SELECT field_id, field_name, is_computed, formula_expression
FROM framework_data_fields
WHERE field_name LIKE '%Total rate of new employee%';

Result:
field_id: 0f944ca1-4052-45c8-8e9e-3fbcf84ba44c
field_name: Total rate of new employee hires...
is_computed: 1  ← CORRECTLY SET
formula_expression: A / B  ← CORRECTLY SET
```

### Console Logs
```
Opening modal for field: 0f944ca1-4052-45c8-8e9e-3fbcf84ba44c computed with date: 2025-11-15
[Enhancement #1] Opening raw input field modal  ← WRONG!
```

### Screenshots
- `validation-tc1-before-computed-field-click.png`: Field card with "Computed" badge
- `validation-tc1-ISSUE-wrong-modal-type.png`: Wrong modal opened (raw input instead of computed)

---

## Root Cause Analysis

The issue appears to be in the frontend JavaScript modal routing logic:

1. **Field Type Detection Issue**: The system is not correctly identifying computed fields
2. **Modal Routing Bug**: Even though the backend knows it's a computed field, the frontend is routing to the wrong modal
3. **Console Log Mismatch**: The log says "Opening raw input field modal" but the field type in the API call shows "computed"

**Likely Location**:
- Field click handler in dashboard.js or field_api.js
- Modal routing logic that decides which modal to open
- Check: `openFieldModal()` or similar function

---

## Impact Assessment

### Critical Impact
- ✗ **Enhancement #1 completely non-functional**
- ✗ **ALL computed field testing blocked**
- ✗ **Bug Fix #1 (Date Fallback) cannot be tested**
- ✗ **Bug Fix #2 (Edit Dependency Button) cannot be tested**
- ✗ **TC1-TC7 test cases cannot proceed**

### User Impact
- Users cannot view computed field calculations
- Users cannot see dependency status
- Users cannot edit dependency data via computed field modal
- Computed fields are essentially useless - showing wrong interface

---

## Blocked Test Cases

All Enhancement #1 test cases are blocked:

- ✗ **TC1**: Bug Fix #1 - Date Fallback Logic validation
- ✗ **TC2**: Bug Fix #2 - Edit Dependency Button validation
- ✗ **TC3**: End-to-End Edit Workflow validation
- ✗ **TC4**: Second Dependency Edit Test
- ✗ **TC5**: Missing Dependencies Scenario
- ✗ **TC6**: Raw Input Field Regression Test (can proceed)
- ✗ **TC7**: Console Error Check

---

## Testing Status Summary

### Completed Setup
✓ Login successful
✓ Created dependency data: Total new hires = 20
✓ Created dependency data: Total number of emloyees = 150
✓ Data saved successfully

### Test Results
- **TC1**: BLOCKED - Cannot test, wrong modal opens
- **TC2**: BLOCKED - Cannot test, wrong modal opens
- **TC3-TC5**: BLOCKED - Depends on TC1 and TC2
- **TC6**: Can proceed (raw input fields work)
- **TC7**: BLOCKED - Need computed modal to check

### Overall Status
**0/7 test cases passed**
**6/7 test cases blocked by critical bug**
**1/7 test cases can still be tested**

---

## Recommendation

**IMMEDIATE ACTION REQUIRED**

1. **DO NOT DEPLOY** Enhancement #1 to production
2. **Debug frontend modal routing** to fix computed field detection
3. **Re-test all scenarios** after fix
4. **Estimated Fix Time**: 1-2 hours (frontend JavaScript bug)

---

## Next Steps for Developer

### Investigation Steps
1. Check `app/static/js/user_v2/dashboard.js` for field click handlers
2. Search for modal opening logic that routes based on field type
3. Look for condition: `if (fieldType === 'computed')` or `if (isComputed)`
4. Verify the field data being passed from backend includes `is_computed` flag
5. Check `field_api.js` response to ensure backend is sending correct field type

### Expected Fix
The modal routing should be:
```javascript
if (field.is_computed) {
    // Open computed field modal (Enhancement #1)
    openComputedFieldModal(fieldId, date);
} else {
    // Open raw input modal
    openRawInputModal(fieldId, date);
}
```

Currently it appears to be always opening the raw input modal regardless of field type.

---

## Tester Notes

- Testing conducted using Playwright MCP (Firefox)
- All screenshots saved to: `.playwright-mcp/validation-*.png`
- Database queries confirmed backend configuration is correct
- Issue is definitely in frontend JavaScript

**This is a blocking bug that prevents any meaningful testing of Enhancement #1.**
