# Automated Validation Engine - Testing Manual

**Project:** Validation Engine Implementation
**Version:** 1.0
**Date:** 2025-11-20
**Status:** Ready for Testing

---

## 📋 Testing Overview

This document provides comprehensive test cases for the Automated Validation Engine. All tests should be executed after implementation is complete and before merging to production.

---

## 🧪 Test Environment Setup

### **Prerequisites**
1. Application running on `http://test-company-alpha.127-0-0-1.nip.io:8000/`
2. Test user accounts:
   - ADMIN: `alice@alpha.com` / `admin123`
   - USER: `bob@alpha.com` / `user123`
3. Chrome DevTools MCP or Playwright MCP server running
4. Clean test data (or known baseline data)

### **Test Data Requirements**
1. At least one entity with assigned data points
2. Historical data for trend comparison (at least 2 previous periods)
3. Fields with computed field relationships
4. Fields configured with attachment requirements

---

## 📊 Test Categories

---

## **Category 1: Database Schema & Model Tests**

### **Test 1.1: Company Model - Validation Threshold**
**Objective:** Verify validation_trend_threshold_pct field exists and defaults correctly

**Steps:**
1. Open Python shell: `python3 manage.py shell`
2. Query company:
   ```python
   from app.models import Company
   company = Company.query.first()
   print(company.validation_trend_threshold_pct)
   ```

**Expected Result:**
- Field exists
- Default value is 20.0
- Can be updated to any float value between 0-100

**Pass/Fail:** ☐

---

### **Test 1.2: DataPointAssignment Model - Attachment Required**
**Objective:** Verify attachment_required field exists and defaults correctly

**Steps:**
1. Open Python shell
2. Query assignment:
   ```python
   from app.models import DataPointAssignment
   assignment = DataPointAssignment.query.first()
   print(assignment.attachment_required)
   ```

**Expected Result:**
- Field exists
- Default value is False
- Can be updated to True/False

**Pass/Fail:** ☐

---

### **Test 1.3: ESGData Model - Review Status Fields**
**Objective:** Verify review_status, submitted_at, validation_results fields exist

**Steps:**
1. Open Python shell
2. Create or query ESG data:
   ```python
   from app.models import ESGData
   data = ESGData.query.first()
   print(data.review_status)
   print(data.submitted_at)
   print(data.validation_results)
   ```

**Expected Result:**
- All fields exist
- review_status defaults to 'draft'
- submitted_at is None by default
- validation_results is None by default
- Can store JSON in validation_results

**Pass/Fail:** ☐

---

## **Category 2: Validation Service Tests**

### **Test 2.1: Required Attachment Validation - Missing Attachment**
**Objective:** Verify validation flags missing attachments

**Setup:**
```python
from app.services.validation_service import ValidationService

result = ValidationService._check_required_attachments(attachments=None)
```

**Expected Result:**
```python
{
    "type": "required_attachment",
    "severity": "warning",
    "message": "Supporting document is required for this field",
    "details": {"attachment_count": 0}
}
```

**Pass/Fail:** ☐

---

### **Test 2.2: Required Attachment Validation - Attachment Present**
**Objective:** Verify validation passes when attachment exists

**Setup:**
```python
result = ValidationService._check_required_attachments(
    attachments=[{'filename': 'test.pdf'}]
)
```

**Expected Result:**
- Returns None (no warning)

**Pass/Fail:** ☐

---

### **Test 2.3: Variance Calculation**
**Objective:** Verify percentage variance calculation

**Setup:**
```python
# Test increase
variance = ValidationService._calculate_variance(150, 100)
assert variance == 50.0

# Test decrease
variance = ValidationService._calculate_variance(75, 100)
assert variance == -25.0

# Test zero old value
variance = ValidationService._calculate_variance(100, 0)
assert variance == 100.0

# Test no change
variance = ValidationService._calculate_variance(100, 100)
assert variance == 0.0
```

**Expected Result:**
- All assertions pass
- Variance calculated correctly

**Pass/Fail:** ☐

---

### **Test 2.4: Risk Score Calculation**
**Objective:** Verify risk score calculation from flags

**Setup:**
```python
flags = [
    {'severity': 'error'},      # +25
    {'severity': 'warning'},    # +10
    {'severity': 'warning'},    # +10
    {'severity': 'info'}        # +2
]

score = ValidationService._calculate_risk_score(flags)
assert score == 47
```

**Expected Result:**
- Score calculated correctly (25 + 10 + 10 + 2 = 47)
- Score capped at 100 for many flags

**Pass/Fail:** ☐

---

### **Test 2.5: Historical Trend Analysis - With Historical Data**
**Objective:** Verify trend comparison with existing historical data

**Prerequisites:**
- Field with 2+ historical data entries
- New submission exceeds threshold

**Setup:**
```python
# Create historical data
# Then test validation
result = ValidationService._check_historical_trends(
    field_id="test-field",
    entity_id=1,
    value=1500,  # 25% increase from 1200
    reporting_date=date(2024, 12, 31),
    company=company,
    assignment=assignment,
    dimension_values=None
)
```

**Expected Result:**
- Returns list of warning flags
- Flags contain variance percentages
- Flags contain historical values for context

**Pass/Fail:** ☐

---

### **Test 2.6: Historical Trend Analysis - No Historical Data**
**Objective:** Verify handling when no historical data exists

**Setup:**
```python
result = ValidationService._check_historical_trends(
    field_id="new-field",  # No historical data
    entity_id=1,
    value=1500,
    reporting_date=date(2024, 12, 31),
    company=company,
    assignment=assignment,
    dimension_values=None
)
```

**Expected Result:**
- Returns info message flag
- Message: "No historical data available for comparison"
- Severity: "info"

**Pass/Fail:** ☐

---

### **Test 2.7: Computed Field Impact - Complete Dependencies**
**Objective:** Verify computed field impact detection when all dependencies exist

**Prerequisites:**
- Computed field with 3 dependencies (e.g., Total = Scope1 + Scope2 + Scope3)
- All dependencies have existing data

**Setup:**
```python
result = ValidationService._check_computed_field_impact(
    field_id="scope1-field",
    entity_id=1,
    value=5000,  # Significant increase
    reporting_date=date(2024, 12, 31),
    company=company
)
```

**Expected Result:**
- Returns warning flag
- Message indicates computed field will increase
- Contains projected value for computed field

**Pass/Fail:** ☐

---

### **Test 2.8: Computed Field Impact - Incomplete Dependencies**
**Objective:** Verify computed field validation is skipped when dependencies incomplete

**Prerequisites:**
- Computed field with 3 dependencies
- Only 1 dependency has existing data

**Setup:**
```python
result = ValidationService._check_computed_field_impact(
    field_id="scope1-field",
    entity_id=1,
    value=5000,
    reporting_date=date(2024, 12, 31),
    company=company
)
```

**Expected Result:**
- Returns empty list (no warnings)
- Validation skipped due to incomplete dependencies

**Pass/Fail:** ☐

---

## **Category 3: API Endpoint Tests**

### **Test 3.1: Validation API - Successful Validation**
**Objective:** Test validation API endpoint with valid data

**Steps:**
1. Login as USER (`bob@alpha.com`)
2. Make API request:
   ```bash
   curl -X POST http://test-company-alpha.127-0-0-1.nip.io:8000/api/user/validate-submission \
     -H "Content-Type: application/json" \
     -d '{
       "field_id": "test-field-id",
       "entity_id": 1,
       "value": 1500,
       "reporting_date": "2024-12-31",
       "has_attachments": true
     }'
   ```

**Expected Result:**
```json
{
    "success": true,
    "validation": {
        "passed": false,
        "risk_score": 10,
        "flags": [
            {
                "type": "trend_variance",
                "severity": "warning",
                "message": "..."
            }
        ],
        "timestamp": "2024-12-31T10:00:00Z"
    }
}
```

**Pass/Fail:** ☐

---

### **Test 3.2: Company Settings API - Update Threshold**
**Objective:** Test updating validation threshold via API

**Steps:**
1. Login as ADMIN (`alice@alpha.com`)
2. Make API request:
   ```bash
   curl -X POST http://test-company-alpha.127-0-0-1.nip.io:8000/api/admin/company-settings \
     -H "Content-Type: application/json" \
     -d '{
       "validation_trend_threshold_pct": 25.0
     }'
   ```

**Expected Result:**
```json
{
    "success": true,
    "message": "Validation settings updated successfully"
}
```

**Verification:**
- Query company and verify threshold is now 25.0

**Pass/Fail:** ☐

---

### **Test 3.3: Company Settings API - Invalid Threshold**
**Objective:** Test validation of threshold values

**Steps:**
1. Attempt to set threshold > 100:
   ```bash
   curl -X POST ... -d '{"validation_trend_threshold_pct": 150}'
   ```

**Expected Result:**
```json
{
    "success": false,
    "error": "Threshold must be between 0 and 100"
}
```

**Pass/Fail:** ☐

---

## **Category 4: UI Integration Tests**

### **Test 4.1: Validation Modal - Display with Warnings**
**Objective:** Verify validation modal displays correctly when warnings exist

**Prerequisites:**
- Login as USER
- Navigate to data entry form
- Select field with historical data

**Steps:**
1. Using Chrome DevTools MCP:
   ```
   mcp__chrome-devtools__navigate_page("http://test-company-alpha.127-0-0-1.nip.io:8000/user/dashboard")
   ```
2. Enter value that exceeds threshold (e.g., 25% increase)
3. Click "Save" button
4. Take snapshot:
   ```
   mcp__chrome-devtools__take_snapshot()
   ```

**Expected Result:**
- Validation modal appears
- Warning messages displayed with context
- Historical values shown
- Notes textarea present and empty
- Character counter shows "0 / 2000"
- "Review & Submit" button present

**Screenshot:** ☐
**Pass/Fail:** ☐

---

### **Test 4.2: Validation Modal - Required Notes**
**Objective:** Verify notes are required before submission

**Steps:**
1. Continue from Test 4.1
2. Click "Review & Submit" without adding notes
3. Verify alert appears

**Expected Result:**
- Alert message: "Please add a note explaining these changes."
- Form not submitted
- Modal remains open

**Pass/Fail:** ☐

---

### **Test 4.3: Validation Modal - Submit with Notes**
**Objective:** Verify successful submission after adding notes

**Steps:**
1. Continue from Test 4.2
2. Enter notes in textarea: "New facility opened in December"
3. Click "Review & Submit"
4. Wait for success message

**Expected Result:**
- Modal closes
- Data saved successfully
- Success notification appears
- Data status changes to "pending_review"
- validation_results stored in database

**Verification:**
```python
data = ESGData.query.filter_by(field_id="...", entity_id=1).first()
assert data.review_status == "pending_review"
assert data.validation_results is not None
assert "new facility" in data.notes.lower()
```

**Pass/Fail:** ☐

---

### **Test 4.4: Validation Modal - Character Counter**
**Objective:** Verify character counter updates correctly

**Steps:**
1. Open validation modal
2. Type in notes textarea
3. Observe character counter

**Expected Result:**
- Counter updates in real-time
- Shows "X / 2000" format
- Cannot exceed 2000 characters (enforced by maxlength)

**Pass/Fail:** ☐

---

### **Test 4.5: Validation Modal - Grouped Warnings**
**Objective:** Verify warnings are grouped by type

**Setup:**
- Create scenario with multiple warning types:
  - 2 trend warnings (sequential + seasonal)
  - 1 computed field warning
  - 1 missing attachment warning

**Steps:**
1. Submit data with multiple warnings
2. Take snapshot of validation modal

**Expected Result:**
- Warnings grouped into sections:
  - "Trend Analysis Warnings" (with both sequential and seasonal)
  - "Computed Field Impact"
  - "Missing Attachment"
- Each section clearly labeled with icon
- Historical context shown for trend warnings

**Screenshot:** ☐
**Pass/Fail:** ☐

---

### **Test 4.6: No Warnings - Direct Save**
**Objective:** Verify submission proceeds directly when no warnings

**Steps:**
1. Submit data that doesn't trigger any warnings:
   - Within threshold variance
   - Has attachment if required
   - No computed field impact
2. Click "Save"

**Expected Result:**
- Validation runs silently
- No modal appears
- Data saved directly
- Success notification appears immediately

**Pass/Fail:** ☐

---

### **Test 4.7: Info Message Display**
**Objective:** Verify info messages display for first-time submissions

**Setup:**
- Field with no historical data

**Steps:**
1. Submit data for field with no historical data
2. Click "Save"
3. Observe validation modal

**Expected Result:**
- Modal appears with info alert (blue)
- Message: "No historical data available for comparison. This is your first submission for this period."
- Notes textarea still required
- Can submit after adding notes

**Screenshot:** ☐
**Pass/Fail:** ☐

---

### **Test 4.8: Company Settings UI - Validation Threshold**
**Objective:** Verify admin can configure validation threshold

**Steps:**
1. Login as ADMIN (`alice@alpha.com`)
2. Navigate to Company Settings
3. Find "Validation Settings" section
4. Change threshold from 20 to 30
5. Click "Save Validation Settings"
6. Refresh page and verify value persists

**Expected Result:**
- Validation Settings section visible
- Threshold input accepts values 0-100
- Save button works
- Success notification appears
- Value persists after refresh

**Screenshot:** ☐
**Pass/Fail:** ☐

---

### **Test 4.9: Assign Data Points - Attachment Required Checkbox**
**Objective:** Verify admin can set attachment requirement during assignment

**Steps:**
1. Login as ADMIN
2. Navigate to "Assign Data Points"
3. Select a field and entities
4. In configuration modal, check "Require attachment for this field"
5. Complete assignment
6. Verify in database

**Expected Result:**
- Checkbox visible in assignment modal
- Checkbox labeled clearly with icon
- After assignment, attachment_required = True in DataPointAssignment
- Help text explains what this does

**Verification:**
```python
assignment = DataPointAssignment.query.filter_by(
    field_id="...", entity_id=1
).first()
assert assignment.attachment_required == True
```

**Screenshot:** ☐
**Pass/Fail:** ☐

---

## **Category 5: Integration & Workflow Tests**

### **Test 5.1: End-to-End Workflow - With Warnings**
**Objective:** Test complete workflow from data entry to save with validation

**Steps:**
1. Login as USER
2. Navigate to dashboard
3. Select field with historical data and attachment required
4. Enter value 30% higher than last period
5. Upload attachment
6. Click Save
7. Review validation modal
8. Add explanation notes
9. Click "Review & Submit"
10. Verify data saved

**Expected Result:**
- Complete workflow works smoothly
- Validation modal appears with appropriate warnings
- Data saved with validation_results
- Audit log entries created

**Pass/Fail:** ☐

---

### **Test 5.2: Update Existing Data - Re-validation**
**Objective:** Verify validation runs again when updating existing data

**Steps:**
1. Edit previously submitted data
2. Change value to trigger new warning
3. Click Save
4. Verify validation modal appears again

**Expected Result:**
- Validation runs on updates (not just new submissions)
- New validation results overwrite old results
- User can add additional notes

**Pass/Fail:** ☐

---

### **Test 5.3: Dimensional Data Validation**
**Objective:** Verify validation works for dimensional data

**Prerequisites:**
- Field with dimensional breakdowns (e.g., gender, department)

**Steps:**
1. Submit dimensional data with significant change in one dimension
2. Click Save
3. Review validation warnings

**Expected Result:**
- Validation compares both:
  - Total aggregated value
  - Individual dimension values
- Warnings show which dimension(s) exceeded threshold
- Can add notes and submit

**Pass/Fail:** ☐

---

### **Test 5.4: Multiple Frequencies - Monthly**
**Objective:** Verify seasonal comparison for monthly data

**Prerequisites:**
- Monthly assignment
- Historical data for same month last year

**Steps:**
1. Submit data for December 2024
2. System should compare with:
   - November 2024 (last month)
   - October 2024 (2 months ago)
   - December 2023 (same month last year)

**Expected Result:**
- All three comparisons shown if any exceed threshold
- Seasonal comparison clearly labeled "(same month last year)"

**Pass/Fail:** ☐

---

### **Test 5.5: Multiple Frequencies - Quarterly**
**Objective:** Verify seasonal comparison for quarterly data

**Prerequisites:**
- Quarterly assignment
- Historical data for same quarter last year

**Steps:**
1. Submit data for Q4 2024
2. System should compare with:
   - Q3 2024 (last quarter)
   - Q2 2024 (2 quarters ago)
   - Q4 2023 (same quarter last year)

**Expected Result:**
- All three comparisons shown if any exceed threshold
- Seasonal comparison clearly labeled "(same quarter last year)"

**Pass/Fail:** ☐

---

### **Test 5.6: Multiple Frequencies - Annual**
**Objective:** Verify comparison for annual data

**Prerequisites:**
- Annual assignment
- Historical data for previous years

**Steps:**
1. Submit data for FY 2024
2. System should compare with:
   - FY 2023 (last year)
   - FY 2022 (2 years ago)

**Expected Result:**
- Both comparisons shown if exceed threshold
- No seasonal comparison for annual (same as sequential)

**Pass/Fail:** ☐

---

## **Category 6: Edge Cases & Error Handling**

### **Test 6.1: Zero Historical Value**
**Objective:** Verify handling of division by zero in variance calculation

**Setup:**
```python
variance = ValidationService._calculate_variance(100, 0)
```

**Expected Result:**
- Returns 100 (or handles gracefully without error)
- No division by zero error

**Pass/Fail:** ☐

---

### **Test 6.2: Negative Values**
**Objective:** Verify validation works with negative values

**Steps:**
1. Submit negative value (e.g., -50 for offset/reduction)
2. Verify validation calculates variance correctly

**Expected Result:**
- Validation works correctly
- Variance calculated as percentage change

**Pass/Fail:** ☐

---

### **Test 6.3: Very Large Values**
**Objective:** Verify validation handles large numbers

**Steps:**
1. Submit very large value (e.g., 1,000,000,000)
2. Verify validation works and modal displays correctly

**Expected Result:**
- No overflow errors
- Values formatted with appropriate precision
- Modal displays correctly

**Pass/Fail:** ☐

---

### **Test 6.4: Malformed API Request**
**Objective:** Verify API handles invalid requests gracefully

**Steps:**
1. Send invalid JSON to validation API
2. Send missing required fields
3. Send invalid data types

**Expected Result:**
- Returns 400/500 error with clear message
- No application crash
- Error logged appropriately

**Pass/Fail:** ☐

---

### **Test 6.5: Computed Field Circular Dependency**
**Objective:** Verify handling of circular dependencies

**Prerequisites:**
- Create scenario where Field A depends on Field B, which depends on Field A

**Expected Result:**
- System detects circular dependency
- Either skips validation or shows appropriate error
- No infinite loop

**Pass/Fail:** ☐

---

## **Category 7: Performance Tests**

### **Test 7.1: Validation Speed - Simple Case**
**Objective:** Measure validation performance for simple case

**Setup:**
- Single field, no dimensions
- 2 historical values

**Steps:**
1. Record start time
2. Run validation
3. Record end time
4. Calculate duration

**Expected Result:**
- Validation completes in < 1 second

**Duration:** _____ ms
**Pass/Fail:** ☐

---

### **Test 7.2: Validation Speed - Complex Case**
**Objective:** Measure validation performance for complex case

**Setup:**
- Dimensional data (5 dimensions)
- 10 historical values
- 3 computed fields

**Steps:**
1. Record start time
2. Run validation
3. Record end time
4. Calculate duration

**Expected Result:**
- Validation completes in < 2 seconds

**Duration:** _____ ms
**Pass/Fail:** ☐

---

### **Test 7.3: Database Query Performance**
**Objective:** Verify historical data queries are efficient

**Steps:**
1. Enable SQL query logging
2. Run validation
3. Review query count and execution time

**Expected Result:**
- Queries use proper indexes
- No N+1 query problems
- Total query time < 500ms

**Pass/Fail:** ☐

---

## **Category 8: Security Tests**

### **Test 8.1: Access Control - Validation API**
**Objective:** Verify non-authenticated users cannot access validation API

**Steps:**
1. Logout
2. Attempt to call validation API without authentication

**Expected Result:**
- Returns 401 Unauthorized
- No data exposed

**Pass/Fail:** ☐

---

### **Test 8.2: Access Control - Company Settings**
**Objective:** Verify regular users cannot update company settings

**Steps:**
1. Login as USER (not ADMIN)
2. Attempt to call company settings API

**Expected Result:**
- Returns 403 Forbidden
- Settings not changed

**Pass/Fail:** ☐

---

### **Test 8.3: Tenant Isolation**
**Objective:** Verify validation respects multi-tenant boundaries

**Steps:**
1. Login as user from Company A
2. Attempt to validate against Company B's data

**Expected Result:**
- Validation only uses Company A's historical data
- No cross-tenant data leakage

**Pass/Fail:** ☐

---

## **Category 9: Audit Logging Tests**

### **Test 9.1: Validation Event Logging**
**Objective:** Verify validation events are logged in audit trail

**Steps:**
1. Submit data that triggers warnings
2. Add notes and submit
3. Query audit log

**Expected Result:**
- Audit log entries created:
  - Data_Submitted
  - Validation_Warning (for each warning)
  - User_Acknowledged_Warning

**Verification:**
```python
from app.models import AuditLog
logs = AuditLog.query.filter_by(
    entity_type='ESGData',
    entity_id=data_id
).all()

# Verify expected action types present
action_types = [log.action_type for log in logs]
assert 'Data_Submitted' in action_types
assert 'Validation_Warning' in action_types
```

**Pass/Fail:** ☐

---

### **Test 9.2: Configuration Change Logging**
**Objective:** Verify threshold changes are logged

**Steps:**
1. Update validation threshold via admin UI
2. Query audit log

**Expected Result:**
- Audit log entry created for threshold change
- Old and new values recorded

**Pass/Fail:** ☐

---

## 📝 Test Summary Template

After completing all tests, fill in this summary:

**Testing Date:** _______________
**Tester:** _______________
**Environment:** _______________

### Results Summary

| Category | Total Tests | Passed | Failed | Skipped |
|----------|-------------|---------|---------|---------|
| Database Schema | 3 | ___ | ___ | ___ |
| Validation Service | 8 | ___ | ___ | ___ |
| API Endpoints | 3 | ___ | ___ | ___ |
| UI Integration | 9 | ___ | ___ | ___ |
| Integration & Workflow | 6 | ___ | ___ | ___ |
| Edge Cases | 5 | ___ | ___ | ___ |
| Performance | 3 | ___ | ___ | ___ |
| Security | 3 | ___ | ___ | ___ |
| Audit Logging | 2 | ___ | ___ | ___ |
| **TOTAL** | **42** | ___ | ___ | ___ |

### Critical Issues Found
1. _______________
2. _______________
3. _______________

### Non-Critical Issues Found
1. _______________
2. _______________
3. _______________

### Recommendations
1. _______________
2. _______________
3. _______________

### Sign-off

- [ ] All critical tests passed
- [ ] No blocking issues found
- [ ] Performance meets requirements
- [ ] Security verified
- [ ] Documentation updated

**Approved By:** _______________
**Date:** _______________

---

## 🔧 Troubleshooting Common Issues

### Issue: Validation modal not appearing
**Possible Causes:**
- JavaScript error (check browser console)
- Modal HTML not rendering
- ValidationModal class not loaded

**Resolution:**
1. Check browser console for errors
2. Verify validation_modal.js loaded
3. Check if validation API returns warnings

---

### Issue: Historical data not found
**Possible Causes:**
- No historical ESGData entries
- Date mismatch
- Tenant isolation filtering data

**Resolution:**
1. Query ESGData table directly
2. Verify reporting_date values
3. Check company_id filtering

---

### Issue: Computed field validation not working
**Possible Causes:**
- DependencyService not implemented
- Circular dependencies
- Missing dependency data

**Resolution:**
1. Verify DependencyService.get_dependent_computed_fields() works
2. Check for circular dependencies
3. Ensure all dependencies have data

---

## 📚 Additional Resources

- **Implementation Plan:** `backend-developer/implementation-plan.md`
- **Requirements:** `requirements-and-specs.md`
- **Chrome DevTools MCP Guide:** `../../MCP_SERVERS_CONFIG.md`
- **Application Documentation:** `../../CLAUDE.md`

---

**Version History**
- v1.0 (2025-11-20): Initial testing manual created
