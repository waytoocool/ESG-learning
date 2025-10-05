# Phase 9.4: Popups & Modals - Testing Plan

**Date**: 2025-09-30
**Phase**: 9.4 - Popups & Modals (CRITICAL Testing)
**Parent**: Phase 9 Comprehensive Testing
**Status**: Ready for Execution
**Total Tests**: 25 tests (focusing on 15 critical tests)
**Estimated Time**: 4-5 hours
**Priority**: 🔴 **CRITICAL** (Completely untested high-risk area)

---

## Context & Background

### Purpose

Phase 9.4 focuses on testing **modals and popups** - the interactive overlay dialogs that handle core business operations. This includes entity assignment, data point configuration, import/export functionality, and potentially computed fields.

### Why This Phase is CRITICAL 🔴

**Risk Level**: 🔴 **CRITICAL - HIGHEST RISK REMAINING**

**Reasons**:
1. **Never Been Tested**: Modals have NOT been tested at all in Phases 9.0-9.3
2. **Core Business Logic**: Entity assignment and configuration are CRITICAL operations
3. **Data Persistence**: Modal save operations write to database - bugs could cause data loss
4. **Complex UI**: Modals involve overlays, forms, validation - high complexity
5. **User Blocking**: If modals don't work, users cannot complete their workflows

**This is the most important phase remaining before production deployment.**

### Prerequisites

**Must Be Complete Before Starting**:
- ✅ Phase 9.1: Foundation & Services (COMPLETE)
- ✅ Phase 9.2: UI Components (COMPLETE)
- ✅ Phase 9.3: Selected Items & Bulk Ops (COMPLETE)

**Why Prerequisites Matter**:
- Modals depend on AppState (validated in 9.1)
- Modals depend on selection mechanisms (validated in 9.2)
- Modals depend on selected items panel (validated in 9.3)

### Test Environment

**Test Page:**
- **URL**: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2
- **Login**: alice@alpha.com / admin123

**Browser**: Chrome (Playwright MCP)

**Key Modals to Test**:
1. **Entity Assignment Modal** - Assign data points to entities
2. **Configuration Modal** - Configure FY, frequency, units
3. **Import/Export Modals** - CSV import/export workflows
4. **Computed Fields Modal** (if exists) - Formula editing

---

## Test Coverage

### Prioritized Test Strategy

Given the critical nature and time constraints, we'll focus on **15 highest-priority tests** out of 25 total.

#### Tier 1: MUST TEST (10 tests - P0/P1)
These are absolutely critical for production:

**Entity Assignment Modal (6 tests)**:
1. T6.1: Modal opens on "Assign to Entities" click (P0)
2. T6.2: Entity tree renders correctly (P0)
3. T6.4: Multi-entity selection works (P0)
4. T6.7: Modal "Save" button saves assignments (P0 - CRITICAL)
5. T6.8: Modal "Cancel" button closes without saving (P1)
6. T6.9: Modal ESC key closes modal (P1)

**Configuration Modal (4 tests)**:
11. T6.11: Modal opens on "Configure" button click (P0)
12. T6.12-16: Form fields functional (FY, frequency, units) (P0)
13. T6.17: Form validation works (P1)
14. T6.18: Save configuration persists data (P0 - CRITICAL)

#### Tier 2: SHOULD TEST (5 tests - P1)
Important but can defer if time-constrained:

3. T6.3: Entity tree expand/collapse (P1)
5. T6.5: Select all entities option (P1)
6. T6.6: Entity search filtering (P1)
10. T6.10: Modal backdrop click closes modal (P1)
19-22. T6.19-22: Import/Export modals (P1)

#### Tier 3: NICE TO TEST (10 tests - P2/P3)
Can defer to later phases or post-launch:

23-25. T6.23-25: Computed fields modal (P2 - may not exist)
- Additional edge case tests

---

## Detailed Test Specifications

### Group 1: Entity Assignment Modal (10 tests)

#### T6.1: Modal Opens on "Assign to Entities" Click
**Priority**: P0 - CRITICAL
**Complexity**: Low

**Description**: Verify "Assign to Entities" button opens the entity assignment modal

**Prerequisites**:
- At least 1 data point selected

**Steps**:
1. Load page: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2
2. Select at least 1 data point (e.g., from existing 17 assignments or add new)
3. Click "Assign to Entities" button in toolbar
4. Verify modal appears

**Expected**:
- ✅ Modal overlay appears (background dims)
- ✅ Modal contains entity selection interface
- ✅ Modal title/header visible (e.g., "Assign to Entities")
- ✅ Modal has close button (X)
- ✅ No console errors

**Bug Risk**: 🔴 **HIGH** - If modal doesn't open, entire assignment workflow broken

**Evidence Required**:
- Screenshot of modal opened
- Console log (no errors)

---

#### T6.2: Entity Tree Renders Correctly
**Priority**: P0 - CRITICAL
**Complexity**: Medium

**Description**: Verify entity tree structure renders with proper hierarchy

**Steps**:
1. Open entity assignment modal (from T6.1)
2. Inspect entity tree structure
3. Verify entities display in tree/list format
4. Check for company entities (test-company-alpha has entities)

**Expected**:
- ✅ Entity tree renders
- ✅ Entities visible (at least root entities)
- ✅ Hierarchy clear (if nested entities exist)
- ✅ Entity names display correctly
- ✅ Checkboxes next to each entity

**Bug Risk**: 🔴 **HIGH** - Users cannot select entities if tree doesn't render

**Evidence Required**:
- Screenshot of entity tree
- Count of entities displayed

---

#### T6.3: Entity Tree Expand/Collapse Works
**Priority**: P1 - HIGH
**Complexity**: Medium

**Description**: Test expand/collapse functionality for nested entities

**Steps**:
1. Open entity assignment modal
2. Look for entities with children (nested entities)
3. Click expand icon/button
4. Verify children appear
5. Click collapse icon/button
6. Verify children hide

**Expected**:
- ✅ Expand button expands nested entities
- ✅ Collapse button collapses nested entities
- ✅ Visual indicator of expanded/collapsed state
- ✅ Smooth transitions

**If Feature Doesn't Exist**: Document as "Feature Not Applicable" if no nested entities

**Evidence**: Screenshot showing expanded and collapsed states

---

#### T6.4: Multi-Entity Selection (Checkboxes)
**Priority**: P0 - CRITICAL
**Complexity**: Medium

**Description**: Verify users can select multiple entities via checkboxes

**Steps**:
1. Open entity assignment modal
2. Click checkbox for Entity 1
3. Verify checkbox checked
4. Click checkbox for Entity 2
5. Verify both checkboxes checked
6. Click checkbox for Entity 1 again
7. Verify Entity 1 unchecks (toggle behavior)

**Expected**:
- ✅ Checkboxes toggle on/off
- ✅ Multiple entities can be selected simultaneously
- ✅ Visual feedback (checked state visible)
- ✅ No limit on number of selections (unless by design)

**Bug Risk**: 🔴 **HIGH** - Core functionality for entity assignment

**Evidence**:
- Screenshot with multiple entities selected
- Console log of selected entity IDs (if accessible)

---

#### T6.5: Select All Entities Option
**Priority**: P1 - HIGH
**Complexity**: Low

**Description**: Test "Select All" or equivalent bulk selection feature

**Steps**:
1. Open entity assignment modal
2. Look for "Select All" checkbox/button
3. If exists:
   - Click "Select All"
   - Verify all entity checkboxes check
   - Click "Select All" again
   - Verify all uncheck (toggle behavior)

**Expected** (if feature exists):
- ✅ "Select All" selects all entities
- ✅ "Deselect All" or toggle unchecks all
- ✅ Efficient for bulk assignment

**If Feature Doesn't Exist**: Document as "Feature Not Implemented"

**Evidence**: Screenshot showing all entities selected

---

#### T6.6: Entity Search Filtering
**Priority**: P1 - HIGH
**Complexity**: Medium

**Description**: Test search/filter functionality within entity modal

**Steps**:
1. Open entity assignment modal
2. Look for search input field
3. If exists:
   - Type entity name (e.g., "Facility")
   - Verify entity tree filters to matching entities
   - Clear search
   - Verify all entities reappear

**Expected** (if feature exists):
- ✅ Search filters entity list in real-time
- ✅ Matching entities highlighted or isolated
- ✅ Clear search restores full list

**If Feature Doesn't Exist**: Document as "Feature Not Implemented"

**Evidence**: Screenshot showing filtered results

---

#### T6.7: Modal "Save" Button Saves Assignments
**Priority**: P0 - CRITICAL (MOST IMPORTANT TEST)
**Complexity**: High

**Description**: Verify clicking "Save" persists entity assignments to database

**Steps**:
1. Select 2-3 data points in main page
2. Open entity assignment modal
3. Select 2-3 entities
4. Click "Save" button in modal
5. Verify modal closes
6. **CRITICAL**: Check if assignments saved:
   - Option A: Reload page, check if assignments persist
   - Option B: Check database (if accessible)
   - Option C: Check API response in network logs
   - Option D: Look for success message/toast notification

**Expected**:
- ✅ Modal closes after save
- ✅ Assignments persist (verified via reload or API)
- ✅ Success message displayed (if implemented)
- ✅ Counter updates (if entity assignment affects counter)
- ✅ No console errors
- ✅ Database updated (if verifiable)

**Bug Risk**: 🔴 **CRITICAL** - If save doesn't work, data loss occurs

**Evidence Required**:
- Screenshot before save (selected entities)
- Screenshot after save (modal closed)
- Screenshot after page reload (assignments persist)
- Network log showing successful API call
- Console log (no errors)

**This is the single most important test in Phase 9.4**

---

#### T6.8: Modal "Cancel" Button Closes Without Saving
**Priority**: P1 - HIGH
**Complexity**: Medium

**Description**: Verify "Cancel" closes modal and discards changes

**Steps**:
1. Select data points
2. Open entity assignment modal
3. Select some entities
4. Click "Cancel" button
5. Verify modal closes
6. Re-open modal
7. Verify previous selections NOT saved (entities unchecked)

**Expected**:
- ✅ "Cancel" closes modal
- ✅ No changes saved to database
- ✅ Modal state resets on next open

**Bug Risk**: 🟡 **MEDIUM** - Accidental saves could confuse users

**Evidence**:
- Screenshot showing cancel action
- Verification that changes not saved

---

#### T6.9: Modal ESC Key Closes Modal
**Priority**: P1 - HIGH
**Complexity**: Low

**Description**: Verify pressing ESC key closes modal (keyboard accessibility)

**Steps**:
1. Open entity assignment modal
2. Press ESC key on keyboard
3. Verify modal closes

**Expected**:
- ✅ ESC key closes modal
- ✅ Behavior same as clicking "Cancel" (no save)

**Evidence**: Video or screenshot showing modal closed after ESC

---

#### T6.10: Modal Backdrop Click Closes Modal
**Priority**: P1 - HIGH
**Complexity**: Low

**Description**: Verify clicking outside modal (on backdrop) closes it

**Steps**:
1. Open entity assignment modal
2. Click on dimmed background area (outside modal box)
3. Verify modal closes

**Expected**:
- ✅ Backdrop click closes modal
- ✅ Behavior same as "Cancel" (no save)

**Can Differ**: Some modals require explicit close button - acceptable UX

**Evidence**: Screenshot or video

---

### Group 2: Configuration Modal (8 tests)

#### T6.11: Modal Opens on "Configure" Button Click
**Priority**: P0 - CRITICAL
**Complexity**: Low

**Description**: Verify "Configure" button opens configuration modal

**Prerequisites**:
- At least 1 data point selected

**Steps**:
1. Select data point(s)
2. Click "Configure" button in toolbar
3. Verify modal appears

**Expected**:
- ✅ Configuration modal opens
- ✅ Form fields visible (FY, frequency, units)
- ✅ Modal has close button
- ✅ No console errors

**Bug Risk**: 🔴 **HIGH** - Configuration is core functionality

**Evidence**: Screenshot of configuration modal opened

---

#### T6.12-16: Form Fields Functional (Combined Test)
**Priority**: P0 - CRITICAL
**Complexity**: Medium

**Description**: Test all configuration form fields work correctly

**Fields to Test**:
1. **FY Start Month**: Dropdown or input (e.g., January, April)
2. **FY Start Year**: Input field (e.g., 2024)
3. **FY End Year**: Input field (e.g., 2024)
4. **Frequency**: Dropdown (Annual, Quarterly, Monthly)
5. **Unit**: Dropdown or input (e.g., kg, metric tons, USD)

**Steps**:
1. Open configuration modal
2. For each field:
   - Verify field renders
   - Interact with field (select dropdown, type in input)
   - Verify input accepted
3. Fill all fields with valid data

**Expected**:
- ✅ All fields render correctly
- ✅ All fields accept input
- ✅ Dropdowns populate with options
- ✅ No visual glitches

**Bug Risk**: 🔴 **HIGH** - Forms must work for configuration to succeed

**Evidence**:
- Screenshot of modal with all fields filled
- List of available options for dropdowns

---

#### T6.17: Form Validation (Invalid FY Dates)
**Priority**: P1 - HIGH
**Complexity**: Medium

**Description**: Test form validation catches invalid inputs

**Test Cases**:
1. **Invalid Date Range**: FY Start Year > FY End Year (e.g., 2025 > 2024)
2. **Missing Required Fields**: Leave FY year blank
3. **Invalid Characters**: Enter text in year field

**Steps**:
1. Open configuration modal
2. Enter invalid data (e.g., Start Year: 2025, End Year: 2024)
3. Try to save
4. Verify validation error appears
5. Correct the error
6. Verify save now works

**Expected**:
- ✅ Validation catches invalid inputs
- ✅ Error messages display clearly
- ✅ Form doesn't submit with invalid data
- ✅ Users guided to fix errors

**Bug Risk**: 🟡 **MEDIUM** - Poor validation could allow bad data

**Evidence**:
- Screenshot showing validation error message
- Description of validation rules

---

#### T6.18: Save Configuration Persists Data
**Priority**: P0 - CRITICAL (SECOND MOST IMPORTANT TEST)
**Complexity**: High

**Description**: Verify configuration saves to database

**Steps**:
1. Select data point
2. Open configuration modal
3. Fill all fields:
   - FY Start: April 2024
   - FY End: March 2025
   - Frequency: Quarterly
   - Unit: metric tons
4. Click "Save"
5. Verify modal closes
6. **CRITICAL**: Verify configuration saved:
   - Reload page
   - Check if configuration persists for that data point
   - Or check network logs for successful API call

**Expected**:
- ✅ Modal closes after save
- ✅ Configuration persists (verified via reload)
- ✅ Success message (if implemented)
- ✅ No console errors
- ✅ Database updated

**Bug Risk**: 🔴 **CRITICAL** - Configuration loss would break workflows

**Evidence**:
- Screenshot before save (form filled)
- Screenshot after save (modal closed)
- Screenshot after reload (configuration persists)
- Network log showing API success
- Console log (no errors)

**This is the second most important test in Phase 9.4**

---

### Group 3: Import/Export Modals (4 tests)

#### T6.19: Import Modal Opens
**Priority**: P1 - HIGH
**Complexity**: Low

**Description**: Verify "Import" button opens import modal

**Steps**:
1. Click "Import" button in toolbar
2. Verify import modal appears

**Expected**:
- ✅ Import modal opens
- ✅ File upload field visible
- ✅ Instructions/help text present
- ✅ Template download option (if exists)

**Evidence**: Screenshot of import modal

---

#### T6.20: File Upload Field Functional
**Priority**: P1 - HIGH
**Complexity**: Medium

**Description**: Test file upload functionality

**Steps**:
1. Open import modal
2. Click file upload field or "Choose File" button
3. Select a CSV file (create dummy test file if needed)
4. Verify file name displays
5. Verify "Upload" or "Import" button enabled

**Expected**:
- ✅ File picker opens
- ✅ File selection works
- ✅ File name displays after selection
- ✅ Import button enables

**Note**: Full import testing (file parsing, data validation) is in Phase 9.5

**Evidence**: Screenshot showing file selected

---

#### T6.21: Template Download Button
**Priority**: P2 - MEDIUM
**Complexity**: Low

**Description**: Test CSV template download feature

**Steps**:
1. Open import modal
2. Look for "Download Template" or similar button
3. If exists:
   - Click button
   - Verify CSV file downloads
   - Open CSV and verify headers correct

**Expected** (if feature exists):
- ✅ Template downloads
- ✅ CSV contains proper column headers
- ✅ Users can use template for bulk import

**If Feature Doesn't Exist**: Document as "Feature Not Implemented"

**Evidence**: Screenshot of download button, CSV file headers

---

#### T6.22: Export Modal Opens with Options
**Priority**: P1 - HIGH
**Complexity**: Low

**Description**: Verify "Export" button opens export modal

**Steps**:
1. Click "Export" button in toolbar
2. Verify export modal appears
3. Check for export options (if any):
   - Export all assignments
   - Export selected assignments
   - File format options

**Expected**:
- ✅ Export modal opens
- ✅ Export options clear
- ✅ Export button functional

**Note**: Full export testing (file generation, data accuracy) is in Phase 9.5

**Evidence**: Screenshot of export modal

---

### Group 4: Computed Fields Modal (3 tests - OPTIONAL)

#### T6.23-25: Computed Fields Modal (Combined)
**Priority**: P2 - MEDIUM (OPTIONAL)
**Complexity**: High

**Description**: Test computed field modal if it exists

**Steps**:
1. Look for "Computed Fields" or formula-related button
2. If exists:
   - Open modal
   - Test formula editor
   - Test validation
3. If doesn't exist:
   - Document as "Feature Not Implemented"

**Expected** (if feature exists):
- Formula editor works
- Validation catches syntax errors
- Save persists formula

**Can Defer**: This is advanced functionality, can test post-launch

**Evidence**: Screenshot or "Feature Not Implemented" note

---

## Success Criteria

Phase 9.4 is COMPLETE and can proceed to Phase 9.5 when:

### Critical Requirements (Must Pass)
- ✅ All P0 tests passed (T6.1, T6.2, T6.4, T6.7, T6.11, T6.12-16, T6.18)
- ✅ Zero P0 bugs found (or all fixed)
- ✅ Entity assignment saves successfully (T6.7)
- ✅ Configuration saves successfully (T6.18)

### Quality Requirements
- ✅ At least 15/25 tests executed (60%)
- ✅ All modals open/close correctly
- ✅ All save operations persist data
- ✅ No data loss in any modal operation

### Documentation Requirements
- ✅ Test execution report created
- ✅ All critical tests documented as PASS/FAIL
- ✅ Screenshots for all modal states
- ✅ Any bugs documented with priority

---

## Bug Priority Definitions

**P0 (Critical)**: Modal doesn't open, save doesn't persist, data loss
- Must fix immediately, blocks Phase 9.5

**P1 (High)**: Form validation broken, cancel doesn't work, UX issues
- Fix before Phase 9 completion

**P2 (Medium)**: Missing features, cosmetic issues
- Can defer to post-launch

**P3 (Low)**: Nice-to-have features
- Backlog

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Entity assignment save fails | 🟡 MEDIUM | 🔴 CRITICAL | T6.7 will catch this, test thoroughly |
| Configuration save fails | 🟡 MEDIUM | 🔴 CRITICAL | T6.18 will catch this |
| Modal doesn't open | 🟢 LOW | 🔴 HIGH | Test T6.1, T6.11 first |
| Form validation missing | 🟡 MEDIUM | 🟡 MEDIUM | T6.17 will identify |
| Import/export broken | 🟡 MEDIUM | 🟡 MEDIUM | Full testing in Phase 9.5 |

**Overall Phase Risk**: 🔴 **CRITICAL - HIGHEST PRIORITY**

---

## Test Execution Strategy

### Phase 1: Entity Assignment Modal (2 hours)
1. T6.1: Open modal ✅
2. T6.2: Entity tree renders ✅
3. T6.4: Multi-select works ✅
4. **T6.7: SAVE WORKS ✅ (MOST IMPORTANT)**
5. T6.8-10: Close behaviors

### Phase 2: Configuration Modal (1.5 hours)
1. T6.11: Open modal ✅
2. T6.12-16: All form fields work ✅
3. **T6.18: SAVE WORKS ✅ (SECOND MOST IMPORTANT)**
4. T6.17: Validation

### Phase 3: Import/Export (1 hour)
1. T6.19-22: Import/export modals open and basic functionality

### Phase 4: Cleanup (30 min)
- Screenshot organization
- Report writing
- Bug documentation (if any)

**Total**: 4-5 hours

---

## Deliverables

**Test Report**: `/Claude Development Team/.../Phase-9.4-Popups-Modals-2025-09-30/ui-testing-agent/Phase_9.4_Test_Execution_Report.md`

**Screenshots**: `ui-testing-agent/screenshots/`

**Required Screenshots**:
- Entity modal opened
- Entity tree with selections
- Entity modal after save (closed)
- Configuration modal with fields filled
- Configuration modal after save
- Import modal
- Export modal

---

## References

**Main Plan**: Lines 268-320
**Specs**: This file

---

**Ready to Begin Testing**: ✅ YES
**Prerequisites Met**: ✅ YES
**Estimated Completion**: 4-5 hours from start
**CRITICALITY**: 🔴 HIGHEST - This phase is make-or-break for production readiness