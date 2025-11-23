# Comprehensive Test Plan

**Feature:** Computed Field Dependency Auto-Management
**Test Plan Version:** 1.0.0
**Last Updated:** 2025-11-10

## 📋 Test Strategy

### Testing Approach
- **Unit Testing:** Backend service methods
- **Integration Testing:** API endpoints
- **UI Testing:** Frontend behavior and user interactions
- **E2E Testing:** Complete workflow scenarios
- **Regression Testing:** Existing functionality preservation

### Testing Priorities
1. **P0 (Critical):** Auto-cascade selection, frequency validation
2. **P1 (High):** Removal protection, entity assignment
3. **P2 (Medium):** Visual indicators, notifications
4. **P3 (Low):** Edge cases, performance

---

## 🧪 UI Test Cases

### TC-001: Basic Auto-Cascade Selection
**Priority:** P0
**Type:** Functional

**Preconditions:**
- Admin logged in at assign-data-points page
- Computed field "Employee Turnover Rate" exists with dependencies:
  - "Total Employee Turnover" (A)
  - "Total Number of Employees" (B)

**Test Steps:**
1. Navigate to Assign Data Points page
2. Search for "Employee Turnover Rate"
3. Click "+" button to add the field
4. Observe the selection panel

**Expected Results:**
- ✅ All 3 fields appear in selected panel:
  - Employee Turnover Rate (with 🧮 badge)
  - Total Employee Turnover (as dependency)
  - Total Number of Employees (as dependency)
- ✅ Notification shows: "Added 'Employee Turnover Rate' and 2 dependencies"
- ✅ Counter shows "3 data points selected"
- ✅ Dependencies visually grouped under computed field

**Test Data:**
```javascript
// Expected state after selection
AppState.selectedDataPoints = {
  'e98a1bc5-xxx': {name: 'Employee Turnover Rate', is_computed: true},
  'a37da5a6-xxx': {name: 'Total Employee Turnover', is_dependency: true},
  '43267341-xxx': {name: 'Total Number of Employees', is_dependency: true}
}
```

---

### TC-002: Partial Dependency Already Selected
**Priority:** P0
**Type:** Functional

**Preconditions:**
- "Total Number of Employees" already selected
- "Employee Turnover Rate" not selected

**Test Steps:**
1. Verify "Total Number of Employees" in selected panel
2. Add "Employee Turnover Rate"
3. Observe behavior

**Expected Results:**
- ✅ Only "Total Employee Turnover" is auto-added
- ✅ Notification: "Added 'Employee Turnover Rate' and 1 dependency"
- ✅ Info message: "'Total Number of Employees' already selected"
- ✅ No duplicate of "Total Number of Employees"
- ✅ Counter increments by 2 (not 3)

---

### TC-003: Removal Protection - Blocking Case
**Priority:** P0
**Type:** Functional

**Preconditions:**
- All 3 fields from TC-001 are selected

**Test Steps:**
1. Try to remove "Total Number of Employees"
2. Observe warning modal
3. Click "Cancel"

**Expected Results:**
- ✅ Warning modal appears:
  ```
  ⚠️ Cannot Remove Dependency
  'Total Number of Employees' is required by:
  • Employee Turnover Rate
  Remove anyway? (Computed field will be removed too)
  [Cancel] [Remove Both]
  ```
- ✅ After cancel: Field remains selected
- ✅ No changes to selection state

---

### TC-004: Removal with Cascade
**Priority:** P1
**Type:** Functional

**Preconditions:**
- Same as TC-003

**Test Steps:**
1. Try to remove "Total Number of Employees"
2. Click "Remove Both" in warning

**Expected Results:**
- ✅ Both fields removed:
  - Total Number of Employees
  - Employee Turnover Rate
- ✅ "Total Employee Turnover" remains (can exist independently)
- ✅ Counter updates correctly

---

### TC-005: Frequency Compatibility - Valid Configuration
**Priority:** P0
**Type:** Functional

**Preconditions:**
- Fields selected from TC-001

**Test Steps:**
1. Click "Configure Selected"
2. Set "Employee Turnover Rate" to Quarterly
3. Dependencies auto-set to Quarterly
4. Change "Total Employees" to Monthly
5. Click "Apply"

**Expected Results:**
- ✅ Configuration accepted (Monthly ≤ Quarterly is valid)
- ✅ No warnings shown
- ✅ Configurations saved:
  - Employee Turnover Rate: Quarterly
  - Total Employee Turnover: Quarterly
  - Total Number of Employees: Monthly

---

### TC-006: Frequency Conflict Detection
**Priority:** P0
**Type:** Functional

**Preconditions:**
- Fields configured as in TC-005

**Test Steps:**
1. Try to change "Employee Turnover Rate" to Monthly
2. Observe validation

**Expected Results:**
- ✅ Warning appears:
  ```
  ⚠️ Frequency Conflict
  'Total Employee Turnover' has Quarterly frequency
  but 'Employee Turnover Rate' needs Monthly or higher

  Options:
  [Change dependency to Monthly] [Keep current] [Cancel]
  ```
- ✅ Cannot save with conflict unresolved

---

### TC-007: Entity Assignment Cascade
**Priority:** P1
**Type:** Functional

**Preconditions:**
- Fields selected from TC-001
- Entities exist: Facility A, Facility B, Facility C

**Test Steps:**
1. Click "Assign Entities"
2. Select Facility A and B for "Employee Turnover Rate"
3. Click "Apply"
4. Check entity assignments

**Expected Results:**
- ✅ All 3 fields assigned to Facility A and B
- ✅ Can additionally assign dependencies to Facility C
- ✅ Cannot remove Facility A/B from dependencies
- ✅ Summary shows: "3 fields × 2 entities = 6 assignments"

---

### TC-008: Visual Indicators Verification
**Priority:** P2
**Type:** UI/UX

**Test Steps:**
1. Load assign-data-points page
2. Observe field display in topic tree
3. Hover over computed fields
4. Check selected panel display

**Expected Results:**
- ✅ Computed fields show 🧮 badge
- ✅ Badge shows dependency count "(2)"
- ✅ Hover tooltip: "Depends on: Field A, Field B"
- ✅ Dependencies indented under computed field
- ✅ Different background colors for computed vs raw

---

### TC-009: Multi-Level Dependencies
**Priority:** P2
**Type:** Functional

**Preconditions:**
- Field C depends on Field B
- Field B depends on Field A
- All are computed fields

**Test Steps:**
1. Select Field C
2. Observe cascade

**Expected Results:**
- ✅ All 3 fields selected
- ✅ Correct hierarchy shown:
  ```
  Field C (computed)
    ↳ Field B (computed, dependency)
      ↳ Field A (raw, dependency)
  ```
- ✅ Notification: "Added 'Field C' and 2 dependencies"

---

### TC-010: Circular Dependency Prevention
**Priority:** P1
**Type:** Functional

**Test Steps:**
1. Try to create circular dependency via API
2. Observe validation

**Expected Results:**
- ✅ Error: "Circular dependency detected"
- ✅ Operation blocked
- ✅ Clear error message

---

### TC-011: Bulk Operations
**Priority:** P1
**Type:** Functional

**Test Steps:**
1. Select 5 computed fields at once
2. Configure all
3. Assign to entities
4. Save

**Expected Results:**
- ✅ All dependencies auto-added (no duplicates)
- ✅ Bulk configuration applied correctly
- ✅ Entity assignments cascaded
- ✅ Save processes all assignments
- ✅ Success message with count

---

### TC-012: Search and Filter with Dependencies
**Priority:** P2
**Type:** Functional

**Test Steps:**
1. Search for "employee"
2. Results include computed and raw fields
3. Filter by "Computed fields only"

**Expected Results:**
- ✅ Search finds all matching fields
- ✅ Computed fields clearly marked
- ✅ Filter works correctly
- ✅ Dependency relationships visible

---

### TC-013: Save Validation
**Priority:** P0
**Type:** Functional

**Preconditions:**
- Computed field selected WITHOUT dependencies

**Test Steps:**
1. Manually remove dependencies
2. Click "Save All"
3. Observe validation

**Expected Results:**
- ✅ Validation error:
  ```
  ❌ Cannot Save
  Missing dependencies for:
  • Employee Turnover Rate
    - Missing: Total Employee Turnover
    - Missing: Total Number of Employees

  [Add Missing] [Cancel]
  ```
- ✅ "Add Missing" auto-adds dependencies
- ✅ Then save succeeds

---

### TC-014: Performance Test
**Priority:** P2
**Type:** Non-Functional

**Test Steps:**
1. Load page with 100+ computed fields
2. Select computed field with 10+ dependencies
3. Measure response time

**Expected Results:**
- ✅ Page load < 2 seconds
- ✅ Selection cascade < 200ms
- ✅ No UI freezing
- ✅ Smooth scrolling

---

### TC-015: Accessibility Test
**Priority:** P2
**Type:** Non-Functional

**Test Steps:**
1. Navigate with keyboard only
2. Use screen reader
3. Check color contrast

**Expected Results:**
- ✅ All interactive elements keyboard accessible
- ✅ Proper ARIA labels
- ✅ Screen reader announces dependencies
- ✅ WCAG AA compliance

---

## 🔄 Regression Test Cases

### RT-001: Existing Manual Selection
**Priority:** P0

**Test:** Verify manual selection still works

**Steps:**
1. Manually select individual raw fields
2. Configure and save

**Expected:** Works as before, no auto-cascade for raw fields

---

### RT-002: Import/Export Unchanged
**Priority:** P0

**Test:** CSV import/export works as before

**Expected:** No changes to import/export behavior

---

### RT-003: Existing Assignments
**Priority:** P0

**Test:** Existing assignments remain intact

**Expected:** No data loss, backward compatible

---

## 🎭 Edge Cases

### EC-001: Dependency of Multiple Computed Fields

**Scenario:** Field A is used by both Field B and Field C

**Test:**
1. Select Field B (auto-adds A)
2. Select Field C
3. Remove Field A

**Expected:**
- Step 2: A not duplicated
- Step 3: Warning shows both B and C affected

---

### EC-002: Framework Change Mid-Selection

**Test:**
1. Select computed field from Framework 1
2. Switch to Framework 2
3. Return to Framework 1

**Expected:**
- Selections preserved
- Dependencies maintained
- No data corruption

---

### EC-003: Session Timeout During Configuration

**Test:**
1. Select fields
2. Wait for session timeout
3. Try to save

**Expected:**
- Graceful error handling
- Redirect to login
- State recovered after login

---

## 📊 Test Data Requirements

### Required Test Data

```sql
-- Computed fields
INSERT INTO framework_data_fields (field_id, field_name, is_computed, formula_expression)
VALUES
  ('comp-1', 'Turnover Rate', true, 'A / B'),
  ('comp-2', 'New Hire Rate', true, 'A / B'),
  ('comp-3', 'Complex Metric', true, '(A + B) / C');

-- Dependencies
INSERT INTO field_variable_mappings (computed_field_id, raw_field_id, variable_name)
VALUES
  ('comp-1', 'raw-1', 'A'),
  ('comp-1', 'raw-2', 'B'),
  ('comp-2', 'raw-3', 'A'),
  ('comp-2', 'raw-2', 'B'),
  ('comp-3', 'raw-1', 'A'),
  ('comp-3', 'raw-3', 'B'),
  ('comp-3', 'raw-4', 'C');

-- Test entities
INSERT INTO entities (name, company_id)
VALUES
  ('Test Facility A', 1),
  ('Test Facility B', 1),
  ('Test Facility C', 1);
```

---

## 🚀 Test Execution Plan

### Phase 1: Development Testing (Day 1-3)
- Unit tests during development
- Developer testing of happy paths
- Basic integration tests

### Phase 2: QA Testing (Day 4)
- Complete test case execution
- Edge case testing
- Regression testing
- Bug logging and fixes

### Phase 3: UAT (Day 5)
- Business user testing
- Real-world scenarios
- Sign-off

---

## 🐛 Bug Tracking Template

```markdown
**Bug ID:** BUG-CFDM-XXX
**Priority:** P0/P1/P2/P3
**Component:** Frontend/Backend/API
**Test Case:** TC-XXX

**Description:**
Brief description of the issue

**Steps to Reproduce:**
1. Step 1
2. Step 2

**Expected Result:**
What should happen

**Actual Result:**
What actually happened

**Screenshots:**
[Attach if applicable]

**Environment:**
- Browser:
- User Role:
- Test Data:
```

---

## ✅ Test Exit Criteria

### Pass Criteria
- All P0 test cases pass
- 95% of P1 test cases pass
- No P0/P1 bugs open
- Performance benchmarks met
- Regression tests pass

### Fail Criteria
- Any P0 test case fails
- More than 5% P1 test cases fail
- Critical bug found
- Performance degradation > 20%

---

## 📈 Test Metrics

### Metrics to Track
1. **Test Coverage:** Target 90%
2. **Pass Rate:** Target 95%
3. **Bug Detection Rate:** Track by priority
4. **Test Execution Time:** < 4 hours for full suite
5. **Automation Coverage:** Target 70%

### Reporting
- Daily test status report
- Bug trend analysis
- Final test report with recommendations

---

## 🔧 Test Environment

### Required Setup
```yaml
Environment:
  - Flask app running
  - Database with test data
  - Chrome/Firefox latest
  - Test user accounts

Test Users:
  - admin@test.com (ADMIN role)
  - user@test.com (USER role)

Test Data:
  - 10+ computed fields
  - 50+ raw fields
  - 5+ test entities
  - Multiple frameworks
```

---

## 📝 Sign-off

### Test Lead
- Name: ________________
- Date: ________________
- Signature: ________________

### Product Owner
- Name: ________________
- Date: ________________
- Signature: ________________

### Development Lead
- Name: ________________
- Date: ________________
- Signature: ________________