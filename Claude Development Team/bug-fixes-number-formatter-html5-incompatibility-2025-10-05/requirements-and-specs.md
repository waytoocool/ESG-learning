# Bug Fix: Number Formatter HTML5 Input Type Incompatibility

## Bug Overview
- **Bug ID/Issue**: Bug #3 from Phase 4 v4 UI Testing
- **Date Reported**: 2025-10-05
- **Severity**: Critical
- **Affected Components**:
  - `app/static/js/user_v2/dimensional_data_handler.js`
  - `app/static/js/user_v2/number_formatter.js`
  - Dimensional data entry matrix (all dimensions)
- **Affected Tenants**: All companies
- **Reporter**: UI Testing Agent (Phase 4 Advanced Features v4)

## Bug Description
The number formatter applies thousand separators (e.g., "1,234,567.00") to formatted values, but HTML5 `<input type="number">` elements reject these formatted strings because they only accept plain numeric values. This causes ALL dimensional data inputs to clear to empty after the formatter is applied.

**Browser Error:**
```
The specified value '1,234,567.00' cannot be parsed, or is out of range
```

## Expected Behavior
1. User enters "12345" in dimensional matrix input
2. Number formatter formats it to "12,345" for display
3. Value persists in the input field
4. On focus, raw value "12345" shows for editing
5. On blur, formatted value "12,345" shows
6. Form submission sends raw numeric value to backend

## Actual Behavior
1. User enters "12345" in dimensional matrix input
2. Number formatter attempts to format it to "12,345"
3. HTML5 `<input type="number">` rejects the formatted value
4. Input field clears to empty
5. Browser console logs validation error
6. **100% of dimensional data entry workflows broken**

## Reproduction Steps
1. Login as bob@alpha.com at http://test-company-alpha.127-0-0-1.nip.io:8000/
2. Navigate to User V2 Dashboard
3. Click on "High Coverage Framework Field 1" (has Gender dimension)
4. Enter "12345" in any dimensional matrix input
5. Tab out or click elsewhere (triggers blur event)
6. **Observe**: Input clears to empty
7. **Console**: See error "The specified value '12,345' cannot be parsed"

## Root Cause
**HTML5 Incompatibility**: The `<input type="number">` HTML5 input type only accepts plain numeric strings (e.g., "12345", "12345.67"). When the number formatter applies formatting with thousand separators (e.g., "12,345.00"), the browser's built-in validation rejects it.

**Code Location:**
- `dimensional_data_handler.js` lines 118, 176, 223 create inputs with `type="number"`
- `number_formatter.js` applies formatting but doesn't account for HTML5 restrictions

## Fix Requirements
- [x] Change dimensional matrix inputs from `type="number"` to `type="text"`
- [x] Add `inputmode="numeric"` for mobile numeric keyboard
- [x] Add `pattern` attribute for basic client-side validation
- [x] Update number formatter to handle text inputs correctly
- [x] Ensure raw values are stored and submitted to backend
- [x] Maintain formatted display for user experience
- [x] Must maintain tenant isolation
- [x] Must not break existing auto-save functionality
- [x] Must be tested across all user roles

## Success Criteria
1. ✅ Dimensional inputs accept formatted values without clearing
2. ✅ No browser console errors
3. ✅ Values persist after formatting
4. ✅ On focus: raw value shows for editing
5. ✅ On blur: formatted value shows for display
6. ✅ Backend receives raw numeric values
7. ✅ All dimensional data entry workflows functional
8. ✅ Auto-save functionality still working
9. ✅ Number formatting working correctly across all field types
10. ✅ Ready for v5 testing with 90-100% coverage

## Impact Analysis
- **Production Ready**: NO - Complete blocker
- **Test Coverage**: 35% (4/11 suites) - 7 suites blocked by this bug
- **User Impact**: Cannot enter any dimensional data
- **Regression**: Yes - introduced in Iteration 1 when number formatter was added
