# Enhancement #4: Bulk Excel Upload - Testing Guide

**Date Created:** 2025-11-14
**Related Specification:** requirements-and-specs.md
**Total Test Cases:** 90

This guide contains comprehensive UI test cases for the Bulk Excel Upload feature.

---

## Comprehensive UI Test Cases

### Test Suite Overview

```
Test Categories:
├── 1. Template Generation (10 test cases)
├── 2. File Upload & Parsing (12 test cases)
├── 3. Data Validation (20 test cases)
├── 4. Attachment Upload (8 test cases)
├── 5. Data Submission (10 test cases)
├── 6. Error Handling (15 test cases)
├── 7. Edge Cases (10 test cases)
└── 8. Performance & Load (5 test cases)

Total: 90 test cases
```

---

### 1. Template Generation Test Cases

#### TC-TG-001: Download Template - Overdue Only
**Objective:** Verify template downloads with only overdue assignments

**Preconditions:**
- User logged in as bob@alpha.com
- User has 15 overdue assignments

**Steps:**
1. Navigate to dashboard
2. Click "Bulk Upload Data" button
3. Select "Overdue Only" radio button
4. Click "Download Template"

**Expected Results:**
- Excel file downloads: `Template_overdue_[timestamp].xlsx`
- File contains "Data Entry" sheet with 15 rows (if no dimensions)
- File contains "Instructions" sheet
- Hidden columns present: Field_ID, Entity_ID, Assignment_ID
- All rows have Status = "OVERDUE"
- Reporting dates are in the past

**Test Data:**
- Company: test-company-alpha
- User: bob@alpha.com

---

#### TC-TG-002: Download Template - Pending Only
**Objective:** Verify template downloads with only pending assignments

**Preconditions:**
- User has 23 pending (not overdue) assignments

**Steps:**
1. Click "Bulk Upload Data"
2. Select "Pending Only"
3. Click "Download Template"

**Expected Results:**
- Excel downloads with 23+ rows (more if dimensional)
- All rows have Status = "PENDING"
- Reporting dates are in the future

---

#### TC-TG-003: Download Template - Overdue + Pending
**Objective:** Verify combined filter works

**Preconditions:**
- User has 15 overdue + 23 pending = 38 total

**Steps:**
1. Click "Bulk Upload Data"
2. Select "Overdue + Pending"
3. Download template

**Expected Results:**
- Excel contains 38+ rows
- Mix of "OVERDUE" and "PENDING" statuses

---

#### TC-TG-004: Template with Dimensional Fields
**Objective:** Verify dimensional fields expand into multiple rows

**Preconditions:**
- User has assignment for "Total Employees" field
- Field has dimensions: Gender (Male/Female), Age (<30, 30-50, >50)
- Expected combinations: 2 × 3 = 6 rows

**Steps:**
1. Download template (any filter)
2. Open Excel
3. Locate "Total Employees" field

**Expected Results:**
- 6 rows for "Total Employees":
  - Row 1: Male, <30
  - Row 2: Female, <30
  - Row 3: Male, 30-50
  - Row 4: Female, 30-50
  - Row 5: Male, >50
  - Row 6: Female, >50
- All dimension columns filled
- Same Field_ID for all 6 rows

---

#### TC-TG-005: Template Column Protection
**Objective:** Verify read-only columns are protected

**Steps:**
1. Download template
2. Open in Excel
3. Try to edit "Field_Name" column (cell A2)

**Expected Results:**
- Excel shows "This cell is protected" warning
- Cell cannot be edited
- Only "Value" and "Notes" columns editable

---

#### TC-TG-006: Template Hidden Columns
**Objective:** Verify ID columns are hidden

**Steps:**
1. Download template
2. Check columns AA, AB, AC

**Expected Results:**
- Column AA (Field_ID): Hidden, contains UUID values
- Column AB (Entity_ID): Hidden, contains integer IDs
- Column AC (Assignment_ID): Hidden, contains UUID values

---

#### TC-TG-007: Template Instructions Sheet
**Objective:** Verify instructions sheet is comprehensive

**Steps:**
1. Download template
2. Navigate to "Instructions" sheet

**Expected Results:**
- Sheet exists
- Contains sections:
  - How to Use This Template
  - Dimensional Data explanation
  - Validation Rules
  - Data Type Reference
  - After Upload instructions

---

#### TC-TG-008: Template Empty Case - No Assignments
**Objective:** Verify behavior when user has no pending/overdue assignments

**Preconditions:**
- User has submitted all assignments (nothing pending)

**Steps:**
1. Click "Bulk Upload Data"
2. Select any filter
3. Click "Download Template"

**Expected Results:**
- Error message: "No assignments available for bulk upload"
- OR: Download empty template with headers only
- User sees helpful message

---

#### TC-TG-009: Template with Multiple Entities
**Objective:** Verify template includes all user's accessible entities

**Preconditions:**
- User assigned to multiple entities: Alpha Factory, Beta Office

**Steps:**
1. Download template

**Expected Results:**
- Rows include assignments from both entities
- Entity column shows "Alpha Factory" and "Beta Office"

---

#### TC-TG-010: Template Computed Fields Exclusion
**Objective:** Verify computed fields are NOT in template

**Preconditions:**
- User has assignment for computed field "Total Employee Count"

**Steps:**
1. Download template
2. Search for "Total Employee Count"

**Expected Results:**
- Computed field NOT present in template
- Only raw input fields included

---

### 2. File Upload & Parsing Test Cases

#### TC-UP-001: Upload Valid XLSX File
**Objective:** Verify successful upload of .xlsx file

**Preconditions:**
- Template downloaded and filled with valid data

**Steps:**
1. Click "Bulk Upload Data" → Step 2
2. Drag template.xlsx onto upload zone
3. Click "Upload & Validate"

**Expected Results:**
- File uploads successfully
- Progress bar shows 100%
- Moves to validation step
- Shows "Parsing rows... (23 found)"

---

#### TC-UP-002: Upload Valid CSV File
**Objective:** Verify CSV format support

**Steps:**
1. Save template as CSV (comma-delimited)
2. Upload CSV file

**Expected Results:**
- CSV parsed correctly
- All data extracted
- Moves to validation

---

#### TC-UP-003: Upload Valid XLS File (Legacy Format)
**Objective:** Verify .xls support

**Steps:**
1. Convert template to .xls (Excel 97-2003)
2. Upload file

**Expected Results:**
- File accepted
- Parses correctly

---

#### TC-UP-004: Reject Invalid File Format
**Objective:** Verify only allowed formats accepted

**Steps:**
1. Try uploading .pdf file
2. Try uploading .docx file
3. Try uploading .txt file

**Expected Results:**
- Error: "Invalid file format. Supported: .xlsx, .xls, .csv"
- File not accepted
- User can try again

---

#### TC-UP-005: Reject Oversized File
**Objective:** Verify 5MB file size limit

**Steps:**
1. Create Excel file > 5MB (e.g., 6MB)
2. Try uploading

**Expected Results:**
- Error: "File exceeds 5MB limit"
- File rejected
- Suggestion to reduce file size

---

#### TC-UP-006: Upload File with Modified Columns
**Objective:** Verify system handles column modifications

**Steps:**
1. Download template
2. Delete "Notes" column
3. Upload modified file

**Expected Results:**
- Parsing succeeds
- Missing "Notes" treated as empty
- OR: Error if required column missing

---

#### TC-UP-007: Upload File with Extra Columns
**Objective:** Verify system ignores extra columns

**Steps:**
1. Add column "My_Custom_Field" to template
2. Fill with data
3. Upload

**Expected Results:**
- Upload succeeds
- Extra column ignored
- Warning: "Unknown column 'My_Custom_Field' will be ignored"

---

#### TC-UP-008: Upload File with Missing Hidden Columns
**Objective:** Verify system detects tampered template

**Steps:**
1. Delete hidden columns (Field_ID, Entity_ID, Assignment_ID)
2. Upload

**Expected Results:**
- Error: "Template missing required system columns"
- Upload rejected
- Suggestion to download fresh template

---

#### TC-UP-009: Upload Empty File
**Objective:** Verify handling of empty upload

**Steps:**
1. Create Excel with headers only (no data rows)
2. Upload

**Expected Results:**
- Error: "No data rows found"
- Upload rejected

---

#### TC-UP-010: Drag & Drop Upload
**Objective:** Verify drag-drop functionality

**Steps:**
1. Drag file from desktop to upload zone
2. Release mouse

**Expected Results:**
- File captured
- Upload initiates automatically
- Progress indicator shows

---

#### TC-UP-011: Browse & Upload
**Objective:** Verify file browser upload

**Steps:**
1. Click "Choose File" button
2. Browse to file
3. Select and confirm

**Expected Results:**
- File browser opens
- Selected file name displayed
- Upload initiates

---

#### TC-UP-012: Cancel Upload Mid-Process
**Objective:** Verify upload can be cancelled

**Steps:**
1. Start uploading large file
2. Click "Cancel" during upload

**Expected Results:**
- Upload stops
- File discarded
- Returns to upload screen

---

### 3. Data Validation Test Cases

#### TC-DV-001: Validate All Valid Rows
**Objective:** Verify successful validation of clean data

**Preconditions:**
- Template filled with all valid data (23 rows)

**Steps:**
1. Upload file
2. Wait for validation

**Expected Results:**
- Validation succeeds
- Message: "✅ Validation Successful"
- Shows: "23 total rows validated"
- No errors
- Proceeds to preview step

---

#### TC-DV-002: Reject on Invalid Data Type - Text in Number Field
**Objective:** Verify data type validation for numeric fields

**Test Data:**
- Row 5: Energy Consumption = "ABCD" (should be number)

**Steps:**
1. Fill "Value" with text "ABCD" for numeric field
2. Upload

**Expected Results:**
- Validation fails
- Error: "Row 5: Invalid DECIMAL format: 'ABCD'"
- Expected: Numeric value
- Entire upload rejected

---

#### TC-DV-003: Reject on Invalid Reporting Date
**Objective:** Verify reporting date validation

**Test Data:**
- Field: Quarterly frequency (valid: 03-31, 06-30, 09-30, 12-31)
- Row 8: Rep_Date = 2024-05-15 (invalid)

**Steps:**
1. Change reporting date to invalid value
2. Upload

**Expected Results:**
- Error: "Row 8: Invalid reporting date 2024-05-15"
- Shows valid dates: "2024-03-31, 2024-06-30, ..."
- Upload rejected

---

#### TC-DV-004: Reject on Field Not Assigned
**Objective:** Verify assignment validation

**Test Data:**
- Row 10: Field_ID = "xyz-fake-id" (not assigned to user's entity)

**Steps:**
1. Manually edit Field_ID to invalid value
2. Upload

**Expected Results:**
- Error: "Row 10: Field not assigned to this entity"
- Upload rejected

---

#### TC-DV-005: Reject on Invalid Dimension Value
**Objective:** Verify dimension validation

**Test Data:**
- Field has dimension "Gender" with values: Male, Female
- Row 3: Gender = "Other" (not in allowed values)

**Steps:**
1. Enter invalid dimension value
2. Upload

**Expected Results:**
- Error: "Row 3: Invalid value 'Other' for dimension 'Gender'"
- Shows: "Valid values: Male, Female"
- Upload rejected

---

#### TC-DV-006: Reject on Dimension Version Change
**Objective:** Verify dimension change detection

**Preconditions:**
- User downloads template at 10:00 AM
- Admin adds new dimension option "Location" at 10:30 AM
- User uploads at 11:00 AM

**Steps:**
1. Upload old template with outdated dimensions

**Expected Results:**
- Error: "Row X: Field dimensions changed. Download new template"
- Shows current dimensions
- Upload rejected

---

#### TC-DV-007: Validate Missing Required Dimension
**Objective:** Verify required dimensions are enforced

**Test Data:**
- Field has required dimension "Gender"
- Row 4: Gender column is empty

**Steps:**
1. Leave required dimension empty
2. Upload

**Expected Results:**
- Error: "Row 4: Required dimension 'Gender' is missing"
- Upload rejected

---

#### TC-DV-008: Validate Percentage Format - Both Styles
**Objective:** Verify percentage accepts 15 and 0.15

**Test Data:**
- Row 1: Percentage field = "15" (means 15%)
- Row 2: Percentage field = "0.15" (means 15%)

**Steps:**
1. Enter both formats
2. Upload

**Expected Results:**
- Both accepted
- Normalized to 0.15 internally
- Validation succeeds

---

#### TC-DV-009: Validate Currency Format with Symbols
**Objective:** Verify currency parsing

**Test Data:**
- Row 5: Revenue = "$1,000,000.50"
- Row 6: Revenue = "1000000.50"

**Steps:**
1. Enter both formats
2. Upload

**Expected Results:**
- Both accepted
- Symbols and commas stripped
- Stored as 1000000.50

---

#### TC-DV-010: Validate Boolean - Multiple Formats
**Objective:** Verify boolean accepts various inputs

**Test Data:**
- Row 1: TRUE
- Row 2: FALSE
- Row 3: Yes
- Row 4: No
- Row 5: 1
- Row 6: 0

**Steps:**
1. Enter all formats
2. Upload

**Expected Results:**
- All accepted
- TRUE/Yes/1 → true
- FALSE/No/0 → false

---

#### TC-DV-011: Validate Date Format
**Objective:** Verify date field parsing

**Test Data:**
- Row 1: Date = "2024-12-31" (YYYY-MM-DD)
- Row 2: Date = Excel date serial (45290)

**Steps:**
1. Enter both formats
2. Upload

**Expected Results:**
- Both accepted
- Parsed to date object

---

#### TC-DV-012: Warn on Negative Value
**Objective:** Verify business rule warnings

**Test Data:**
- Row 5: Employee Count = -10 (unusual)

**Steps:**
1. Enter negative value for positive field
2. Upload

**Expected Results:**
- Validation succeeds (warning only)
- Warning: "Row 5: Negative value (-10) - please verify"
- Upload proceeds to preview with warning shown

---

#### TC-DV-013: Warn on Very Large Value
**Objective:** Verify large number warning

**Test Data:**
- Row 8: Energy = 5000000000 (5 billion)

**Steps:**
1. Enter extremely large value
2. Upload

**Expected Results:**
- Warning: "Row 8: Very large value (5,000,000,000) - please verify"
- Proceeds with warning

---

#### TC-DV-014: Detect Overwrite - Show Warning
**Objective:** Verify existing data detection

**Preconditions:**
- Row 5: Total Employees (Alpha, 2024-Q1, Male <30)
- Existing data: 20 (submitted 2024-04-05)
- Template value: 25

**Steps:**
1. Upload template with new value
2. Review validation

**Expected Results:**
- Validation succeeds
- Overwrite warning shown:
  - "Row 5 will overwrite existing data"
  - Current: 20, New: 25, Change: +5 (+25%)
  - Submitted: 2024-04-05
- User can proceed or cancel

---

#### TC-DV-015: Validate Empty Value
**Objective:** Verify required value validation

**Test Data:**
- Row 10: Value column is empty

**Steps:**
1. Leave value blank
2. Upload

**Expected Results:**
- Error: "Row 10: Value is required"
- Upload rejected

---

#### TC-DV-016: Validate Notes Length
**Objective:** Verify notes character limit

**Test Data:**
- Row 3: Notes = 1100 characters (exceeds 1000 limit)

**Steps:**
1. Enter very long notes
2. Upload

**Expected Results:**
- Error: "Row 3: Notes exceed maximum length of 1000 characters"
- Upload rejected

---

#### TC-DV-017: Validate Duplicate Rows
**Objective:** Verify duplicate detection

**Test Data:**
- Row 1 and Row 2 identical:
  - Field: Total Employees
  - Entity: Alpha
  - Date: 2024-Q1
  - Gender: Male
  - Age: <30

**Steps:**
1. Create duplicate rows
2. Upload

**Expected Results:**
- Warning or Error: "Duplicate row detected: Row 2 duplicates Row 1"
- User can proceed or fix

---

#### TC-DV-018: Multiple Errors - Show All
**Objective:** Verify all errors displayed

**Test Data:**
- Row 5: Invalid data type
- Row 8: Invalid date
- Row 12: Field not assigned

**Steps:**
1. Upload file with 3 errors

**Expected Results:**
- Shows all 3 errors
- Each with row number and description
- Upload rejected
- User can download error report

---

#### TC-DV-019: Error + Warning - Reject on Error
**Objective:** Verify errors take precedence

**Test Data:**
- Row 3: Warning (negative value)
- Row 7: Error (invalid type)

**Steps:**
1. Upload mixed file

**Expected Results:**
- Upload rejected due to error
- Both error and warning shown
- Must fix error to proceed

---

#### TC-DV-020: Concurrent Upload Validation
**Objective:** Verify session handling for multiple uploads

**Steps:**
1. User A starts upload (Upload 1)
2. During Upload 1 validation, user A starts another upload (Upload 2)

**Expected Results:**
- Warning: "You have an in-progress upload. Resume or cancel?"
- Options: Resume Upload 1, Cancel Upload 1 and start Upload 2
- Only one upload active per session

---

### 4. Attachment Upload Test Cases

#### TC-AT-001: Attach File to Single Entry
**Objective:** Verify single file attachment

**Steps:**
1. Complete validation successfully
2. On attachment step, attach file to Row 1
3. Click "Continue"

**Expected Results:**
- File uploads
- Shows file name and size
- Proceeds to confirmation

---

#### TC-AT-002: Attach Same File to Multiple Entries
**Objective:** Verify file reuse and deduplication

**Steps:**
1. Attach Q1_Report.pdf to Row 1
2. Attach same Q1_Report.pdf to Row 2
3. Attach same Q1_Report.pdf to Row 3

**Expected Results:**
- All 3 uploads accepted
- Hint shown: "Same file detected - will deduplicate"
- Backend stores 1 file, creates 3 attachment records

---

#### TC-AT-003: Skip All Attachments
**Objective:** Verify attachment is optional

**Steps:**
1. On attachment step, click "Skip All Attachments"

**Expected Results:**
- Proceeds to confirmation
- No attachments uploaded
- Data submission succeeds without files

---

#### TC-AT-004: Attach Different Files
**Objective:** Verify multiple unique attachments

**Steps:**
1. Attach Q1_Report.pdf to Row 1
2. Attach Q2_Meter.pdf to Row 5
3. Attach Annual_Summary.xlsx to Row 10

**Expected Results:**
- All 3 files uploaded
- Shows: "Files attached: 3 / 23"
- Proceeds to confirmation

---

#### TC-AT-005: Remove Attached File
**Objective:** Verify file can be removed

**Steps:**
1. Attach file to Row 1
2. Click "Remove" button

**Expected Results:**
- File removed
- Shows: "No file" again
- Can attach different file

---

#### TC-AT-006: Attach Oversized File
**Objective:** Verify 20MB per file limit

**Steps:**
1. Try attaching 25MB PDF

**Expected Results:**
- Error: "File exceeds 20MB limit"
- File rejected
- Can try different file

---

#### TC-AT-007: Attach Invalid File Type
**Objective:** Verify allowed file types

**Test Data:**
- Allowed: pdf, xlsx, docx, csv, jpg, png, zip
- Not allowed: .exe, .bat, .sh

**Steps:**
1. Try attaching .exe file

**Expected Results:**
- Error: "Invalid file type. Allowed: pdf, xlsx, docx, ..."
- File rejected

---

#### TC-AT-008: Total Upload Size Limit
**Objective:** Verify 200MB batch limit

**Steps:**
1. Attach 15 files, each 15MB = 225MB total
2. Try proceeding

**Expected Results:**
- Error: "Total attachment size exceeds 200MB limit"
- Must remove some files to proceed

---

### 5. Data Submission Test Cases

#### TC-DS-001: Submit New Entries Only
**Objective:** Verify creation of new ESGData records

**Preconditions:**
- 23 rows, all new (no existing data)

**Steps:**
1. Complete all steps
2. Click "Confirm & Submit"

**Expected Results:**
- 23 ESGData records created
- 23 audit logs created (type: "Excel Upload")
- BulkUploadLog created with:
  - new_entries: 23
  - updated_entries: 0
- Success message shown
- Dashboard updated: Pending -23, Complete +23

---

#### TC-DS-002: Submit Updates Only
**Objective:** Verify overwrite of existing data

**Preconditions:**
- All 23 rows have existing data

**Steps:**
1. Upload with new values
2. Confirm overwrites
3. Submit

**Expected Results:**
- 0 new ESGData records
- 23 ESGData records updated
- 23 audit logs created (type: "Excel Upload Update")
- BulkUploadLog:
  - new_entries: 0
  - updated_entries: 23

---

#### TC-DS-003: Submit Mix of New and Updates
**Objective:** Verify mixed submission

**Preconditions:**
- 20 rows new, 3 rows existing

**Steps:**
1. Submit

**Expected Results:**
- 20 ESGData created
- 3 ESGData updated
- 23 audit logs total
- BulkUploadLog:
  - new_entries: 20
  - updated_entries: 3

---

#### TC-DS-004: Submit with Attachments
**Objective:** Verify attachment linking

**Preconditions:**
- 3 files attached (2 unique after deduplication)

**Steps:**
1. Submit

**Expected Results:**
- 3 ESGDataAttachment records created
- 2 physical files saved on disk
- file_hash column populated
- BulkUploadLog.attachments_uploaded: 3

---

#### TC-DS-005: Submit with Notes
**Objective:** Verify notes are saved

**Preconditions:**
- All 23 rows have notes filled

**Steps:**
1. Submit

**Expected Results:**
- All ESGData records have notes populated
- Notes visible in data history

---

#### TC-DS-006: Audit Trail - New Entry
**Objective:** Verify audit log for new data

**Steps:**
1. Submit 1 new entry
2. Query ESGDataAuditLog

**Expected Results:**
```sql
SELECT * FROM esg_data_audit_log WHERE data_id = 'new-entry-id'
```
- change_type: "Excel Upload"
- old_value: NULL
- new_value: 25
- changed_by: current_user.id
- metadata: {
    "source": "bulk_upload",
    "filename": "template.xlsx",
    "row_number": 1,
    "batch_id": "batch-abc-123"
  }

---

#### TC-DS-007: Audit Trail - Update Entry
**Objective:** Verify audit log for overwrite

**Preconditions:**
- Existing: Total Employees = 20

**Steps:**
1. Upload with value 25
2. Submit
3. Query audit log

**Expected Results:**
- change_type: "Excel Upload Update"
- old_value: 20
- new_value: 25
- metadata includes: previous_submission_date

---

#### TC-DS-008: Rollback on Error
**Objective:** Verify transaction rollback on failure

**Steps:**
1. Mock database error during submission
2. Trigger submission

**Expected Results:**
- All changes rolled back
- No ESGData created/updated
- No audit logs created
- BulkUploadLog.status: "Failed"
- Error message shown to user

---

#### TC-DS-009: Dashboard Statistics Update
**Objective:** Verify dashboard reflects changes

**Preconditions:**
- Before: Overdue 15, Pending 23, Complete 142

**Steps:**
1. Submit 38 rows (15 overdue + 23 pending)
2. Return to dashboard

**Expected Results:**
- After: Overdue 0, Pending 0, Complete 180
- Field cards update accordingly
- Submitted fields show "Complete" status

---

#### TC-DS-010: Batch ID Generation
**Objective:** Verify unique batch ID

**Steps:**
1. Submit bulk upload
2. Check BulkUploadLog

**Expected Results:**
- upload_id is valid UUID
- Same batch_id in all audit logs
- Batch ID shown in success message

---

### 6. Error Handling Test Cases

#### TC-EH-001: Network Error During Upload
**Objective:** Verify graceful handling of network failure

**Steps:**
1. Start file upload
2. Disconnect network mid-upload

**Expected Results:**
- Error: "Network error. Please check connection and try again"
- Upload can be retried
- No partial data saved

---

#### TC-EH-002: Session Timeout
**Objective:** Verify session expiry handling

**Steps:**
1. Download template
2. Wait 35 minutes (exceed 30 min timeout)
3. Try uploading

**Expected Results:**
- Error: "Session expired. Please log in again"
- Redirect to login
- Upload lost (must restart)

---

#### TC-EH-003: Database Connection Error
**Objective:** Verify DB error handling

**Steps:**
1. Stop database
2. Try submitting upload

**Expected Results:**
- Error: "System error. Please try again later"
- No data corrupted
- BulkUploadLog.status: "Failed"

---

#### TC-EH-004: Disk Full Error
**Objective:** Verify file upload handling when disk full

**Steps:**
1. Fill server disk to capacity
2. Try uploading attachments

**Expected Results:**
- Error: "Storage error. Please contact support"
- Transaction rolled back
- No partial files saved

---

#### TC-EH-005: Corrupt Excel File
**Objective:** Verify handling of damaged files

**Steps:**
1. Corrupt Excel file (edit with text editor)
2. Try uploading

**Expected Results:**
- Error: "Unable to parse file. File may be corrupt"
- Upload rejected
- Suggestion to download new template

---

#### TC-EH-006: Malicious File Upload
**Objective:** Verify security against malicious uploads

**Steps:**
1. Rename virus.exe to template.xlsx
2. Try uploading

**Expected Results:**
- File type detection prevents execution
- Virus scanner (if enabled) blocks
- Error shown

---

#### TC-EH-007: SQL Injection Attempt
**Objective:** Verify protection against SQL injection

**Test Data:**
- Notes field: "'; DROP TABLE esg_data; --"

**Steps:**
1. Enter malicious SQL in notes
2. Upload

**Expected Results:**
- Input sanitized
- Stored as plain text
- No SQL executed
- Database safe

---

#### TC-EH-008: XSS Attempt in Notes
**Objective:** Verify XSS protection

**Test Data:**
- Notes: "<script>alert('XSS')</script>"

**Steps:**
1. Enter script tag in notes
2. Submit
3. View data in dashboard

**Expected Results:**
- Script not executed
- Displayed as text: `&lt;script&gt;...`
- No JavaScript runs

---

#### TC-EH-009: Concurrent Submission
**Objective:** Verify handling of duplicate submissions

**Steps:**
1. Click "Submit" button
2. Immediately click "Submit" again (double-click)

**Expected Results:**
- First submission processes
- Second submission ignored (button disabled after first click)
- Only one batch created

---

#### TC-EH-010: File Upload Timeout
**Objective:** Verify timeout handling for large files

**Steps:**
1. Start uploading 100MB file on slow connection
2. Wait 5 minutes

**Expected Results:**
- Timeout error after 5 min
- Error: "Upload timeout. Please try again"
- Can retry

---

#### TC-EH-011: Invalid Hidden Column Values
**Objective:** Verify tampering detection

**Steps:**
1. Edit Field_ID to invalid UUID
2. Upload

**Expected Results:**
- Error: "Invalid field ID in row X"
- Upload rejected

---

#### TC-EH-012: Missing Dimension After Template Download
**Objective:** Verify dimension deletion handling

**Preconditions:**
- Template downloaded with dimension "Location"
- Admin deletes "Location" dimension before upload

**Steps:**
1. Upload template with deleted dimension

**Expected Results:**
- Error: "Dimension 'Location' no longer exists. Download new template"
- Upload rejected

---

#### TC-EH-013: Assignment Deactivated Between Download and Upload
**Objective:** Verify assignment status checking

**Preconditions:**
- Assignment active when template downloaded
- Admin deactivates assignment before upload

**Steps:**
1. Upload template with deactivated assignment

**Expected Results:**
- Error: "Assignment no longer active. Download new template"
- Upload rejected

---

#### TC-EH-014: Company/Entity Deleted
**Objective:** Verify data integrity checks

**Preconditions:**
- Admin deletes entity referenced in template

**Steps:**
1. Upload template

**Expected Results:**
- Error: "Entity no longer exists"
- Upload rejected

---

#### TC-EH-015: Browser Crash Recovery
**Objective:** Verify user can resume after crash

**Steps:**
1. Start upload (upload_id created)
2. Close browser (simulate crash)
3. Reopen and try again

**Expected Results:**
- Previous upload session expired
- User can start fresh upload
- No orphaned data

---

### 7. Edge Cases Test Cases

#### TC-EC-001: Maximum Rows - 1000
**Objective:** Verify 1000 row limit

**Steps:**
1. Create template with 1000 rows
2. Upload

**Expected Results:**
- Upload succeeds
- All 1000 rows processed
- Performance acceptable (<30 seconds)

---

#### TC-EC-002: Exceed Maximum Rows
**Objective:** Verify rejection over limit

**Steps:**
1. Create template with 1001 rows
2. Upload

**Expected Results:**
- Error: "Maximum 1000 rows allowed"
- Upload rejected
- Suggestion to split into multiple uploads

---

#### TC-EC-003: Single Row Upload
**Objective:** Verify minimum case works

**Steps:**
1. Upload template with 1 row only

**Expected Results:**
- Upload succeeds
- 1 ESGData created
- Audit log created

---

#### TC-EC-004: All Rows Dimensional
**Objective:** Verify handling of many dimension combinations

**Preconditions:**
- Field has 3 dimensions: Type (5 values), Location (4 values), Category (3 values)
- Total combinations: 5 × 4 × 3 = 60 rows

**Steps:**
1. Download template (expands to 60 rows)
2. Fill all rows
3. Upload

**Expected Results:**
- 60 rows validated
- 60 ESGData created with proper dimension_values
- All combinations saved

---

#### TC-EC-005: Special Characters in Notes
**Objective:** Verify unicode/special character handling

**Test Data:**
- Notes: "Value in €, data from 北京 office 🏢"

**Steps:**
1. Enter special characters in notes
2. Upload

**Expected Results:**
- All characters preserved
- Displayed correctly in dashboard
- No encoding errors

---

#### TC-EC-006: Very Long Field Names
**Objective:** Verify UI handles long text

**Preconditions:**
- Field name: "Total number of new employee hires during the reporting period, by age group, gender, and geographic region (annual turnover rate calculation base)"

**Steps:**
1. Download template (includes long field name)
2. View in Excel and upload UI

**Expected Results:**
- Field name displayed correctly (truncated with tooltip)
- No layout breaks
- Upload succeeds

---

#### TC-EC-007: Leap Year Date Validation
**Objective:** Verify date handling for Feb 29

**Test Data:**
- Reporting date: 2024-02-29 (leap year)

**Steps:**
1. Upload with Feb 29 date

**Expected Results:**
- Date accepted for leap year
- Error for non-leap year (2023-02-29)

---

#### TC-EC-008: Zero Value
**Objective:** Verify zero is valid

**Test Data:**
- Row 5: Employee Count = 0

**Steps:**
1. Enter zero
2. Upload

**Expected Results:**
- Accepted as valid
- Stored as 0 (not NULL)

---

#### TC-EC-009: Decimal Precision
**Objective:** Verify decimal handling

**Test Data:**
- Value: 1.23456789012345

**Steps:**
1. Enter high-precision decimal
2. Upload
3. View saved data

**Expected Results:**
- Precision preserved (up to DB limit)
- No rounding errors

---

#### TC-EC-010: Internationalization - Different Decimal Separators
**Objective:** Verify regional number formats

**Test Data:**
- European format: 1.234,56 (period thousands, comma decimal)
- US format: 1,234.56 (comma thousands, period decimal)

**Steps:**
1. Upload with different formats

**Expected Results:**
- System detects based on locale or rejects ambiguous formats
- Clear error if format unclear
- Recommendation: Use standard format (1234.56)

---

### 8. Performance & Load Test Cases

#### TC-PL-001: Large File Upload Speed
**Objective:** Measure upload time for max size file

**Test Data:**
- Excel file: 5MB (near limit)

**Steps:**
1. Upload 5MB file
2. Measure time

**Expected Results:**
- Upload completes in <10 seconds on standard connection
- Progress indicator updates smoothly

---

#### TC-PL-002: Validation Performance - 1000 Rows
**Objective:** Measure validation speed

**Test Data:**
- 1000 rows, all valid

**Steps:**
1. Upload 1000 rows
2. Measure validation time

**Expected Results:**
- Validation completes in <30 seconds
- UI remains responsive
- Progress updates shown

---

#### TC-PL-003: Submission Performance - 1000 Rows
**Objective:** Measure database insert speed

**Steps:**
1. Submit 1000 valid rows

**Expected Results:**
- Submission completes in <60 seconds
- Transaction commits successfully
- No timeout errors

---

#### TC-PL-004: Concurrent Users - 10 Simultaneous Uploads
**Objective:** Verify system handles multiple users

**Steps:**
1. 10 users upload simultaneously
2. Monitor server resources

**Expected Results:**
- All uploads succeed
- No deadlocks
- Acceptable response times (<30 sec each)

---

#### TC-PL-005: Memory Usage - Large Upload
**Objective:** Verify no memory leaks

**Steps:**
1. Upload 1000 rows repeatedly (5 times)
2. Monitor server memory

**Expected Results:**
- Memory usage stable
- No memory leaks
- Garbage collection works properly

---

