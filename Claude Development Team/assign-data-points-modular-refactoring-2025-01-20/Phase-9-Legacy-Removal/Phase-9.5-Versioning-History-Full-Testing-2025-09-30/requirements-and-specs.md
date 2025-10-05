# Phase 9.5: Versioning & History - Full Testing Plan
## Requirements and Specifications

**Date**: 2025-09-30
**Phase**: 9.5 - Versioning & History (FULL TESTING)
**Status**: Ready for Execution
**Total Tests**: 45 tests (Phase 7: 18 tests + Phase 8: 27 tests)
**Estimated Time**: 4-5 hours
**Priority**: CRITICAL (Data integrity at stake)

---

## Context & Background

### Why This Phase is Critical

**Previous Status**: Phase 9.5 was "streamlined" in earlier testing with only 4 basic tests. This full testing phase will execute ALL 45 planned tests to ensure:

1. **Data Integrity**: Assignment versioning and history tracking are core to application data integrity
2. **Version Management**: Version creation, updates, rollback, and conflict handling must work flawlessly
3. **Import/Export**: CSV import/export operations must handle all edge cases
4. **History Tracking**: Complete audit trail must be accurate and queryable

**Risk Level**: CRITICAL - Bugs in versioning could cause data loss or corruption in production

---

## Test Pages

**NEW Modular Page (Under Test)**:
- **URL**: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points
- **Status**: Production-ready frontend (pending full versioning validation)

**Test Credentials**:
```
Company: test-company-alpha
Admin: alice@alpha.com / admin123
```

---

## Phase 7: Versioning Module Tests (18 tests)

### Focus Areas
- Version creation and lifecycle management
- Version number increments
- Status transitions (DRAFT → ACTIVE → SUPERSEDED)
- Fiscal year validation and conflict detection
- Version comparison and rollback
- Concurrent edit handling
- Audit trail

### Test Cases

#### Group 1: Version Creation & Lifecycle (6 tests)

**T7.1: Version Creation on First Save** (P0 - CRITICAL)
- **Objective**: Verify that saving assignments for the first time creates a new version
- **Steps**:
  1. Login as alice@alpha.com
  2. Navigate to assign-data-points page
  3. Select 5 data points from GRI framework
  4. Assign to entities
  5. Configure with FY settings
  6. Click "Save All"
  7. Check database for new version record
- **Expected**: Version 1 created with status=DRAFT or ACTIVE
- **Priority**: P0

**T7.2: Version Number Increments Correctly** (P0 - CRITICAL)
- **Objective**: Verify version numbers increment without gaps (1, 2, 3...)
- **Steps**:
  1. Create first version (should be version 1)
  2. Modify assignments
  3. Save again (should create version 2)
  4. Modify again
  5. Save again (should create version 3)
  6. Verify no gaps in version numbers
- **Expected**: Versions increment sequentially: 1, 2, 3, 4...
- **Priority**: P0

**T7.3: Version Status: DRAFT → ACTIVE** (P1)
- **Objective**: Verify version status transitions from DRAFT to ACTIVE
- **Steps**:
  1. Create new version (check initial status)
  2. If DRAFT, activate the version
  3. Verify status changed to ACTIVE
- **Expected**: Status transitions correctly
- **Priority**: P1

**T7.4: Version Status: ACTIVE → SUPERSEDED** (P1)
- **Objective**: Verify old ACTIVE versions become SUPERSEDED when new version created
- **Steps**:
  1. Create version 1 (ACTIVE)
  2. Create version 2 (should become ACTIVE)
  3. Verify version 1 status changed to SUPERSEDED
- **Expected**: Only one ACTIVE version at a time, old versions marked SUPERSEDED
- **Priority**: P1

**T7.5: Date-Based Version Resolution** (P1)
- **Objective**: Verify system can retrieve correct version for a given date
- **Steps**:
  1. Create version 1 for FY 2023
  2. Create version 2 for FY 2024
  3. Query for version applicable to date in 2023
  4. Query for version applicable to date in 2024
- **Expected**: Correct version returned based on FY date range
- **Priority**: P1

**T7.6: Version Metadata (created_by, created_at)** (P2)
- **Objective**: Verify version metadata is captured correctly
- **Steps**:
  1. Create new version as alice@alpha.com
  2. Check database for version record
  3. Verify created_by = alice@alpha.com
  4. Verify created_at = current timestamp
- **Expected**: Metadata accurate
- **Priority**: P2

#### Group 2: Fiscal Year Validation (6 tests)

**T7.7: FY Validation Prevents Invalid Entries** (P0 - CRITICAL)
- **Objective**: Verify system prevents invalid FY dates (e.g., end before start)
- **Steps**:
  1. Try to configure assignment with FY start = 2024-01-01, FY end = 2023-12-31
  2. Click Save
- **Expected**: Error message shown, save blocked
- **Priority**: P0

**T7.8: Overlapping FY Detection** (P0 - CRITICAL)
- **Objective**: Verify system detects and prevents overlapping FY periods for same data point
- **Steps**:
  1. Create version 1 with FY 2023-01-01 to 2023-12-31
  2. Try to create version 2 with FY 2023-06-01 to 2024-06-30 (overlaps)
- **Expected**: Error message, overlap detected and blocked
- **Priority**: P0

**T7.9: Gap Detection in FY Coverage** (P1)
- **Objective**: Verify system warns about gaps in FY coverage
- **Steps**:
  1. Create version 1 for FY 2023
  2. Create version 2 for FY 2025 (gap: 2024 missing)
  3. Check for warning message
- **Expected**: Warning shown about missing FY 2024
- **Priority**: P1

**T7.10: Valid FY Date Ranges Accepted** (P1)
- **Objective**: Verify valid FY dates are accepted without error
- **Steps**:
  1. Configure assignment with FY start = 2023-01-01, end = 2023-12-31
  2. Save
  3. Verify saved successfully
- **Expected**: No errors, version created
- **Priority**: P1

**T7.11: FY Validation with Different Start Months** (P2)
- **Objective**: Verify FY validation works with non-calendar years (e.g., Apr-Mar)
- **Steps**:
  1. Configure FY start month = April
  2. Set FY start = 2023-04-01, end = 2024-03-31
  3. Save and verify
- **Expected**: Accepted without error
- **Priority**: P2

**T7.12: FY Validation Handles Leap Years** (P3)
- **Objective**: Verify FY validation handles Feb 29 correctly
- **Steps**:
  1. Configure FY with date = 2024-02-29 (leap year)
  2. Save and verify
- **Expected**: Date accepted
- **Priority**: P3

#### Group 3: Version Comparison & Rollback (6 tests)

**T7.13: Version Comparison UI** (P1)
- **Objective**: Verify version comparison shows differences between versions
- **Steps**:
  1. Create version 1 with 5 data points assigned
  2. Create version 2 with 7 data points assigned (2 added)
  3. Open version comparison UI
  4. Compare version 1 vs version 2
- **Expected**: Differences highlighted (2 additions shown)
- **Priority**: P1

**T7.14: Version History Display** (P1)
- **Objective**: Verify version history timeline displays all versions
- **Steps**:
  1. Create 3 versions
  2. Open "History" button/modal
  3. Verify all 3 versions listed with metadata
- **Expected**: All versions shown with version number, date, user, status
- **Priority**: P1

**T7.15: Rollback to Previous Version** (P0 - CRITICAL)
- **Objective**: Verify rollback functionality restores previous version
- **Steps**:
  1. Create version 1 (5 data points)
  2. Create version 2 (7 data points)
  3. Rollback to version 1
  4. Verify current assignments match version 1 (5 data points)
- **Expected**: Rollback successful, data restored
- **Priority**: P0

**T7.16: Version Restore Functionality** (P1)
- **Objective**: Verify soft-deleted versions can be restored
- **Steps**:
  1. Create version 1
  2. Soft delete version 1
  3. Restore version 1
  4. Verify version 1 visible again
- **Expected**: Restore successful
- **Priority**: P1

**T7.17: Version Approval Workflow (if applicable)** (P2)
- **Objective**: If version approval exists, verify workflow
- **Steps**:
  1. Create version as alice@alpha.com
  2. Submit for approval
  3. Approve as admin
  4. Verify status changes
- **Expected**: Approval workflow works
- **Priority**: P2 (if feature exists)

**T7.18: Version Audit Trail** (P1)
- **Objective**: Verify all version operations logged in audit trail
- **Steps**:
  1. Create version 1
  2. Update to version 2
  3. Rollback to version 1
  4. Check audit log for all 3 operations
- **Expected**: All operations logged with user, timestamp, action
- **Priority**: P1

---

## Phase 8: Import/Export & History Tests (27 tests)

### Focus Areas
- CSV import validation (valid and invalid data)
- CSV export functionality
- Import preview and confirmation
- Error handling and rollback
- History timeline and filtering
- Large dataset handling

### Test Cases

#### Group 1: CSV Import Tests (10 tests)

**T8.1: Import Valid CSV (10 rows)** (P0 - CRITICAL)
- **Objective**: Verify valid CSV with 10 rows imports successfully
- **Steps**:
  1. Download import template
  2. Fill template with 10 valid assignment rows
  3. Click "Import" button
  4. Upload CSV file
  5. Review preview
  6. Confirm import
- **Expected**: All 10 rows imported, success message shown
- **Priority**: P0

**T8.2: Import Valid CSV (100 rows)** (P1)
- **Objective**: Verify large CSV imports successfully
- **Steps**:
  1. Create CSV with 100 valid rows
  2. Import CSV
  3. Monitor progress indicator
  4. Verify all 100 rows imported
- **Expected**: Import completes in <3 seconds, all rows imported
- **Priority**: P1

**T8.3: Import Invalid CSV (Missing Columns)** (P0 - CRITICAL)
- **Objective**: Verify system rejects CSV with missing required columns
- **Steps**:
  1. Create CSV missing "field_id" column
  2. Upload CSV
- **Expected**: Error message "Missing required column: field_id", import blocked
- **Priority**: P0

**T8.4: Import Invalid CSV (Invalid Data Types)** (P0 - CRITICAL)
- **Objective**: Verify system validates data types in CSV
- **Steps**:
  1. Create CSV with text in numeric field (e.g., "abc" for field_id)
  2. Upload CSV
- **Expected**: Error message "Invalid data type in row X", import blocked
- **Priority**: P0

**T8.5: Import Duplicate Entries Handling** (P1)
- **Objective**: Verify how system handles duplicate assignments in CSV
- **Steps**:
  1. Create CSV with same field_id assigned twice
  2. Upload CSV
- **Expected**: Error or warning shown, duplicates handled (skip or merge)
- **Priority**: P1

**T8.6: Import Preview Before Confirm** (P1)
- **Objective**: Verify import preview shows data before final confirmation
- **Steps**:
  1. Upload valid CSV
  2. Check preview screen
  3. Verify preview shows first 10-20 rows
  4. Verify "Confirm" and "Cancel" buttons available
- **Expected**: Preview accurate, user can cancel before import
- **Priority**: P1

**T8.7: Import Progress Indicator** (P2)
- **Objective**: Verify progress bar/spinner shows during import
- **Steps**:
  1. Upload large CSV (100 rows)
  2. Watch for progress indicator
- **Expected**: Progress bar or spinner visible during import
- **Priority**: P2

**T8.8: Import Success Message** (P2)
- **Objective**: Verify success message shows count of imported rows
- **Steps**:
  1. Import valid CSV with 10 rows
  2. Wait for completion
- **Expected**: Message "Successfully imported 10 assignments"
- **Priority**: P2

**T8.9: Import Error Report with Line Numbers** (P1)
- **Objective**: Verify error report shows which rows failed and why
- **Steps**:
  1. Create CSV with 10 rows, 3 invalid
  2. Upload CSV
- **Expected**: Error report lists row numbers (e.g., "Error in row 3: Invalid field_id")
- **Priority**: P1

**T8.10: Import Rollback on Error** (P0 - CRITICAL)
- **Objective**: Verify import rolls back if critical error occurs mid-import
- **Steps**:
  1. Create CSV with 50 valid rows, 1 critical error at row 51
  2. Upload CSV
  3. Verify import fails and no partial data saved
- **Expected**: All-or-nothing import, no partial data in database
- **Priority**: P0

#### Group 2: CSV Export Tests (7 tests)

**T8.11: Export All Assignments (CSV)** (P1)
- **Objective**: Verify export downloads CSV with all current assignments
- **Steps**:
  1. Create 10 assignments in UI
  2. Click "Export" button
  3. Download CSV file
  4. Open CSV and verify all 10 assignments present
- **Expected**: CSV contains all 10 assignments with correct data
- **Priority**: P1

**T8.12: Export Filtered Assignments (By Framework)** (P2)
- **Objective**: Verify export can filter by framework
- **Steps**:
  1. Create assignments for GRI and TCFD frameworks
  2. Export with filter: Framework = GRI only
  3. Verify CSV contains only GRI assignments
- **Expected**: Only GRI assignments in export
- **Priority**: P2

**T8.13: Export Filtered Assignments (By Entity)** (P2)
- **Objective**: Verify export can filter by entity
- **Steps**:
  1. Create assignments for Entity A and Entity B
  2. Export with filter: Entity = Entity A only
  3. Verify CSV contains only Entity A assignments
- **Expected**: Only Entity A assignments in export
- **Priority**: P2

**T8.14: Export Includes All Metadata** (P1)
- **Objective**: Verify export includes all relevant columns
- **Steps**:
  1. Export assignments
  2. Verify CSV headers include: field_id, field_name, entity_id, entity_name, fy_start, fy_end, frequency, unit, status, created_by, created_at, etc.
- **Expected**: All metadata columns present
- **Priority**: P1

**T8.15: Export File Naming Convention** (P2)
- **Objective**: Verify export file has meaningful name
- **Steps**:
  1. Export assignments
  2. Check downloaded filename
- **Expected**: Filename like "assignments_export_2025-09-30_143025.csv"
- **Priority**: P2

**T8.16: Export Large Datasets (500+ rows)** (P1)
- **Objective**: Verify export handles large datasets without timeout
- **Steps**:
  1. Create 500+ assignments (or use existing data)
  2. Export all
  3. Monitor for timeout/errors
- **Expected**: Export completes in <2 seconds, all rows exported
- **Priority**: P1

**T8.17: Template Download (Empty CSV with Headers)** (P1)
- **Objective**: Verify template download provides correct CSV structure
- **Steps**:
  1. Click "Download Template" button
  2. Open template CSV
  3. Verify headers match expected format
  4. Verify 0 data rows (empty template)
- **Expected**: Template has correct headers, ready for data entry
- **Priority**: P1

#### Group 3: History & Timeline Tests (10 tests)

**T8.18: History Timeline Displays** (P1)
- **Objective**: Verify history timeline opens and shows change history
- **Steps**:
  1. Create 3 versions of assignments
  2. Click "History" button
  3. Verify timeline/list displays
- **Expected**: History modal/page opens with all 3 versions listed
- **Priority**: P1

**T8.19: History Shows All Changes** (P1)
- **Objective**: Verify history shows what changed in each version
- **Steps**:
  1. Create version 1 (5 data points)
  2. Create version 2 (add 2 data points, remove 1)
  3. Open history
  4. View version 2 details
- **Expected**: Details show "+2 added, -1 removed"
- **Priority**: P1

**T8.20: History Filtering by Date** (P2)
- **Objective**: Verify history can be filtered by date range
- **Steps**:
  1. Create versions on different dates (if possible, or use existing)
  2. Open history
  3. Apply date filter: Last 7 days
  4. Verify only recent versions shown
- **Expected**: Filter works correctly
- **Priority**: P2

**T8.21: History Filtering by User** (P2)
- **Objective**: Verify history can be filtered by user
- **Steps**:
  1. Create versions as alice@alpha.com and carol@alpha.com (if possible)
  2. Open history
  3. Filter by user: alice@alpha.com
  4. Verify only alice's versions shown
- **Expected**: User filter works
- **Priority**: P2

**T8.22: History Filtering by Entity** (P2)
- **Objective**: Verify history can be filtered by entity
- **Steps**:
  1. Create assignments for Entity A and Entity B
  2. Open history
  3. Filter by entity: Entity A
  4. Verify only Entity A assignments shown
- **Expected**: Entity filter works
- **Priority**: P2

**T8.23: History Detail View (What Changed)** (P1)
- **Objective**: Verify clicking on history item shows detailed changes
- **Steps**:
  1. Open history timeline
  2. Click on a version entry
  3. Verify detail view shows before/after comparison
- **Expected**: Detail modal shows field-by-field changes
- **Priority**: P1

**T8.24: Version Comparison Side-by-Side** (P1)
- **Objective**: Verify version comparison shows two versions side by side
- **Steps**:
  1. Open history
  2. Select version 1 and version 2
  3. Click "Compare" button
  4. Verify side-by-side comparison view
- **Expected**: Differences highlighted in side-by-side view
- **Priority**: P1

**T8.25: History Pagination (20 items per page)** (P2)
- **Objective**: Verify history pagination works for large history
- **Steps**:
  1. Create 25+ versions (if possible, or simulate)
  2. Open history
  3. Verify pagination controls appear
  4. Navigate to page 2
- **Expected**: Pagination works, 20 items per page
- **Priority**: P2

**T8.26: History Search Functionality** (P2)
- **Objective**: Verify history search finds versions by keyword
- **Steps**:
  1. Open history
  2. Enter search term (e.g., field name or entity name)
  3. Verify results filtered
- **Expected**: Search works, relevant results shown
- **Priority**: P2

**T8.27: History Export** (P2)
- **Objective**: Verify history can be exported to CSV
- **Steps**:
  1. Open history
  2. Click "Export History" button (if available)
  3. Download and verify CSV contains history records
- **Expected**: History export works
- **Priority**: P2

---

## Success Criteria

Phase 9.5 is COMPLETE and APPROVED when:

### Versioning Module (Phase 7)
- ✅ All 18 versioning tests executed
- ✅ Version creation, increments, and status transitions working
- ✅ FY validation prevents invalid/overlapping dates
- ✅ Version comparison and rollback functional
- ✅ Zero P0 bugs, zero P1 bugs

### Import/Export & History (Phase 8)
- ✅ All 27 import/export/history tests executed
- ✅ CSV import handles valid and invalid data correctly
- ✅ CSV export works for all scenarios
- ✅ History timeline accurate and filterable
- ✅ Zero P0 bugs, zero P1 bugs

### Overall Phase 9.5
- ✅ All 45 tests executed (100% coverage)
- ✅ All P0/P1 bugs fixed
- ✅ P2/P3 bugs documented (defer to post-launch if needed)
- ✅ UI-testing-agent approval received
- ✅ Bug-fixer reports (if bugs found)
- ✅ Documentation complete

---

## Bug Management

### Priority Definitions
- **P0 (Critical)**: Blocks core functionality, data loss risk, must fix immediately
- **P1 (High)**: Major feature broken, fix before phase completion
- **P2 (Medium)**: Minor issue, can defer to post-launch
- **P3 (Low)**: Cosmetic, backlog for future

### Process
1. **Bug Found**: Document immediately, invoke bug-fixer if P0/P1
2. **Bug Fixed**: Re-test same scenario to verify fix
3. **Phase Complete**: Only when all P0/P1 bugs fixed

---

## Testing Methodology

### For UI-Testing-Agent
- Execute tests in order (T7.1 → T7.18 → T8.1 → T8.27)
- Capture screenshots for each test
- Document PASS/FAIL with evidence
- Report bugs immediately with reproduction steps
- Test on correct page URL: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points

### For Bug-Fixer
- Fix P0/P1 bugs immediately
- Document fix in bug-fixer report
- Notify when fix is ready for re-test

---

## Deliverables

1. **Test Execution Report**: Results for all 45 tests
2. **Screenshots**: Evidence for key tests
3. **Bug Reports**: If any bugs found
4. **Bug Fix Reports**: If bug-fixer invoked
5. **Completion Verification**: Summary report with approval

---

## Notes

- This is FULL testing (not streamlined)
- Previous Phase 9.5 only executed 4 tests
- This phase will execute ALL 45 tests as originally planned
- Focus on data integrity and versioning logic
- Import/export must handle edge cases robustly

---

**Phase 9.5 Status**: READY TO START
**Estimated Duration**: 4-5 hours
**Next Step**: Invoke ui-testing-agent to execute tests
