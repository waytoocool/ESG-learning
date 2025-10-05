# Phase 2: Dimensional Data Support - Testing Quick Start Guide

**For:** UI Testing Agent & QA Team
**Date:** 2025-01-04
**Status:** Ready for Testing

---

## 🚀 Quick Start

### Prerequisites
1. Application running: `python3 run.py`
2. Access to User Dashboard V2: `http://{company-slug}.127-0-0-1.nip.io:8000/user/v2/dashboard`
3. Test company with dimensional fields configured

---

## 🎯 What to Test

### 1. Dimensional Field Types

#### 1D Field (Simple List)
- **Example:** Gender breakdown (3 values: Male, Female, Other)
- **Expected UI:** Vertical list with notes field
- **Test:** Enter values, verify total calculation

#### 2D Field (Matrix Table)
- **Example:** Gender x Age (3x3 = 9 combinations)
- **Expected UI:** Interactive matrix table with row/column totals
- **Test:** Enter values, verify row/column/grand totals

#### 3+ Dimensional Field (Combination List)
- **Example:** Gender x Age x Department (3x3x3 = 27 combinations)
- **Expected UI:** List of combinations with grand total
- **Test:** Enter values, verify grand total

---

## 🧪 Test Scenarios

### Scenario 1: New Dimensional Data Entry

**Steps:**
1. Navigate to `/user/v2/dashboard`
2. Click "Enter Data" on a dimensional field
3. Modal opens showing dimension matrix
4. Enter values in matrix inputs
5. Observe real-time total calculations
6. Click "Submit Data"
7. Verify success message
8. Refresh page
9. Open same field modal
10. Verify data loaded correctly

**Expected Results:**
- ✓ Matrix renders correctly based on dimensions
- ✓ Totals calculate in real-time
- ✓ Data submits without errors
- ✓ Data persists and reloads correctly

---

### Scenario 2: Update Existing Data

**Steps:**
1. Open field with existing dimensional data
2. Modal shows pre-filled matrix
3. Modify some values
4. Observe total recalculation
5. Submit updated data
6. Reload and verify changes

**Expected Results:**
- ✓ Existing data loads into matrix
- ✓ Totals update on value change
- ✓ Updates save correctly

---

### Scenario 3: Validation Testing

**Test Cases:**

#### Missing Required Values
1. Open modal for required dimensional field
2. Leave some combinations empty
3. Click submit
4. **Expected:** Validation error (currently allows partial submission)

#### Invalid Numeric Values
1. Enter non-numeric value (e.g., "abc")
2. Click submit
3. **Expected:** HTML5 validation prevents submission

#### Network Error
1. Disconnect network
2. Submit data
3. **Expected:** Error message displayed

---

### Scenario 4: Responsive Design

**Breakpoints to Test:**

#### Desktop (>768px)
- Full matrix table visible
- Hover effects working
- All features accessible

#### Tablet (768px)
- Matrix scrollable horizontally
- Touch-friendly inputs
- Readable layout

#### Mobile (<480px)
- Combination list for 3+ dimensions
- Compact matrix for 2D
- Single column layout
- Thumb-friendly buttons

---

## 📊 API Endpoints to Test

### GET /user/v2/api/dimension-matrix/{field_id}

**Test:**
```bash
curl -X GET "http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/api/dimension-matrix/FIELD_ID?entity_id=1&reporting_date=2024-01-31" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Expected Response:**
- `success: true`
- `dimensions` array
- `dimension_values` object
- `combinations` array

---

### POST /user/v2/api/submit-dimensional-data

**Test:**
```bash
curl -X POST "http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/api/submit-dimensional-data" \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{
    "field_id": "FIELD_ID",
    "entity_id": 1,
    "reporting_date": "2024-01-31",
    "dimensional_data": {
      "dimensions": ["gender", "age"],
      "breakdowns": [
        {
          "dimensions": {"gender": "Male", "age": "<30"},
          "raw_value": 100,
          "notes": null
        }
      ]
    }
  }'
```

**Expected Response:**
- `success: true`
- `totals` object with `overall` and `by_dimension`
- `data_id` returned

---

### POST /user/v2/api/calculate-totals

**Test:**
```bash
curl -X POST "http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/api/calculate-totals" \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{
    "dimensional_data": {
      "dimensions": ["gender"],
      "breakdowns": [
        {"dimensions": {"gender": "Male"}, "raw_value": 100},
        {"dimensions": {"gender": "Female"}, "raw_value": 120}
      ]
    }
  }'
```

**Expected Response:**
- `success: true`
- `totals.overall: 220`
- `totals.by_dimension.gender.Male: 100`

---

## 🔍 Visual Testing Checklist

### Matrix Rendering
- [ ] 1D list renders correctly
- [ ] 2D matrix table renders correctly
- [ ] 3D combination list renders correctly
- [ ] Headers display dimension names
- [ ] Inputs have proper placeholders
- [ ] Totals cells highlighted (blue for subtotals, green for grand)

### Styling
- [ ] Gradient header on matrix
- [ ] Row hover effects
- [ ] Input focus states (blue border + shadow)
- [ ] Total cells properly colored
- [ ] Responsive layout works
- [ ] Print styles apply correctly

### Interactions
- [ ] Click input to focus
- [ ] Type numbers
- [ ] Tab to next input
- [ ] Totals update immediately
- [ ] Submit button enabled/disabled appropriately
- [ ] Success/error messages display

---

## 🧮 Calculation Verification

### 2D Matrix Example

**Input:**
```
Gender/Age | <30  | 30-50 | >50  | Total
-----------|------|-------|------|------
Male       | 100  | 150   | 80   | 330
Female     | 120  | 100   | 70   | 290
-----------|------|-------|------|------
Total      | 220  | 250   | 150  | 620
```

**Verify:**
1. Male total = 100 + 150 + 80 = 330 ✓
2. Female total = 120 + 100 + 70 = 290 ✓
3. <30 total = 100 + 120 = 220 ✓
4. 30-50 total = 150 + 100 = 250 ✓
5. >50 total = 80 + 70 = 150 ✓
6. Grand total = 620 ✓

---

## 🔐 Security Testing

### Authentication
- [ ] Unauthenticated access redirects to login
- [ ] Invalid session returns 401

### Authorization
- [ ] USER role can submit data
- [ ] ADMIN role can submit data
- [ ] Data scoped to correct company (tenant isolation)

### Input Validation
- [ ] SQL injection attempts blocked
- [ ] XSS attempts sanitized
- [ ] Invalid JSON rejected
- [ ] Invalid dimension values rejected

---

## 📱 Accessibility Testing

### Keyboard Navigation
- [ ] Tab through all inputs
- [ ] Enter submits form
- [ ] Escape closes modal
- [ ] Focus visible indicators

### Screen Reader
- [ ] Matrix table announced correctly
- [ ] Input labels read
- [ ] Total cells identified
- [ ] Error messages announced

### Color Contrast
- [ ] Text readable (WCAG AA: 4.5:1)
- [ ] Total cells distinguishable without color
- [ ] Focus indicators visible

---

## ⚡ Performance Testing

### Load Time
- [ ] Matrix loads < 500ms
- [ ] Large matrix (100+ combinations) < 2s

### Calculation Speed
- [ ] Real-time totals update < 100ms
- [ ] No lag when typing

### API Response Time
- [ ] GET dimension-matrix < 300ms
- [ ] POST submit-data < 500ms

---

## 🐛 Error Scenarios to Test

### Network Errors
1. Disconnect network during submission
2. **Expected:** Error message displayed
3. **Expected:** Data not lost (can retry)

### Invalid Data
1. Submit empty breakdowns
2. **Expected:** Validation error
3. Submit invalid dimension values
4. **Expected:** Validation error

### Server Errors
1. Submit to non-existent field
2. **Expected:** 404 error with message
3. Submit without authentication
4. **Expected:** 401 error with redirect

---

## 📝 Test Data Setup

### Create Test Fields

#### 1D Field: Gender
```python
# Dimension: Gender
# Values: Male, Female, Other
# Field: "Employee Count by Gender"
```

#### 2D Field: Gender x Age
```python
# Dimension 1: Gender (Male, Female, Other)
# Dimension 2: Age (<30, 30-50, >50)
# Field: "Employee Demographics"
# Combinations: 3 x 3 = 9
```

#### 3D Field: Gender x Age x Department
```python
# Dimension 1: Gender (Male, Female, Other)
# Dimension 2: Age (<30, 30-50, >50)
# Dimension 3: Department (IT, Finance, HR)
# Field: "Detailed Employee Breakdown"
# Combinations: 3 x 3 x 3 = 27
```

---

## 🎨 Visual Regression Testing

### Screenshots to Capture

1. **Matrix Views:**
   - 1D list view
   - 2D matrix table
   - 3D combination list

2. **States:**
   - Empty matrix
   - Partially filled matrix
   - Complete matrix
   - Loading state
   - Error state
   - Success state

3. **Responsive:**
   - Desktop view
   - Tablet view
   - Mobile view

---

## 🔄 Integration Testing

### Cross-Feature Testing
- [ ] Dimensional data displays in historical tab
- [ ] Entity switcher works with dimensional fields
- [ ] File attachments work with dimensional fields
- [ ] Computed fields calculate using dimensional totals

### Database Verification
```sql
-- Check dimensional data storage
SELECT
    data_id,
    field_id,
    entity_id,
    raw_value,
    dimension_values
FROM esg_data
WHERE dimension_values IS NOT NULL
AND JSON_EXTRACT(dimension_values, '$.version') = 2;
```

---

## ✅ Testing Completion Checklist

### Functional Testing
- [ ] All 1D fields working
- [ ] All 2D fields working
- [ ] All 3+ dimensional fields working
- [ ] Data submission working
- [ ] Data loading working
- [ ] Validation working

### UI/UX Testing
- [ ] Rendering correct for all dimension counts
- [ ] Real-time calculations accurate
- [ ] Styling consistent
- [ ] Responsive design working
- [ ] Error/success messages clear

### Technical Testing
- [ ] All API endpoints working
- [ ] Performance acceptable
- [ ] Security measures in place
- [ ] Error handling robust

### Accessibility
- [ ] Keyboard navigation working
- [ ] Screen reader compatible
- [ ] Color contrast passing
- [ ] Focus indicators visible

### Cross-Browser
- [ ] Chrome tested
- [ ] Firefox tested
- [ ] Safari tested
- [ ] Edge tested
- [ ] Mobile browsers tested

---

## 📞 Support

**Questions or Issues:**
- Check backend-developer-report.md for detailed documentation
- Review IMPLEMENTATION_COMPLETE.md for overview
- Contact backend developer agent for clarifications

**Test Results:**
- Document findings in testing report
- Create bug tickets for issues found
- Mark completion status for each test case

---

*Phase 2 Testing Quick Start Guide*
*Ready for UI Testing Agent - January 4, 2025*
