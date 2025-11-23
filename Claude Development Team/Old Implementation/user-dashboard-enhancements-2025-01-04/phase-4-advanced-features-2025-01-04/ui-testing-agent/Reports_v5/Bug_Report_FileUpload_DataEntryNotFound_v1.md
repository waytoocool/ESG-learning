# Bug Report: File Upload Fails for Existing Data Entries

**Bug ID:** BUG-FILEUPLOAD-001
**Date Reported:** November 14, 2025
**Reported By:** UI Testing Agent
**Severity:** 🔴 **CRITICAL BLOCKER**
**Priority:** **P0**
**Status:** **NEW**
**Component:** File Upload Feature (Enhancement #3)
**Affects Version:** User Dashboard V2 - Phase 4 Advanced Features

---

## Summary

File upload functionality fails with "Data entry not found" error when attempting to attach files to existing saved data entries, despite the data being successfully saved and visible in the UI.

---

## Environment

- **Application:** ESG DataVault
- **URL:** http://test-company-alpha.127-0-0-1.nip.io:8000/
- **User:** bob@alpha.com (Test Company Alpha)
- **Browser:** Chrome (Chrome DevTools MCP)
- **Database:** SQLite
- **Field Type:** Dimensional Data (Monthly frequency)

---

## Steps to Reproduce

1. Login as `bob@alpha.com`
2. Navigate to User Dashboard V2
3. Click "Enter Data" for field "Total new hires"
4. Select reporting date: April 30, 2025
5. Enter data in dimensional grid (e.g., Male/Age ≤30 = 15)
6. Click "SAVE DATA" button
7. Wait for modal to close (confirming save)
8. Click "Enter Data" again for the same field
9. Select the same reporting date (April 30, 2025)
10. Verify data loads correctly (shows 15.00)
11. Scroll to "File Attachments" section
12. Click on file upload area or select a file
13. **BUG OCCURS:** Upload fails with error

---

## Expected Behavior

1. File selection dialog should open
2. After selecting a file, it should upload to the server
3. File should appear in the file list with:
   - Filename
   - File size
   - Upload status changing from "uploading" to "uploaded" with green checkmark
   - Remove (X) button
4. File should be associated with the data entry for April 30, 2025

---

## Actual Behavior

1. ✅ File selection works
2. ❌ Upload immediately fails
3. ❌ Alert dialog appears with error message:
   ```
   Failed to upload test-esg-attachment.txt:
   Data entry not found. Please save data before uploading attachments.
   ```
4. File appears in UI with "Error" status
5. File is NOT uploaded to server

---

## Error Messages

### User-Facing Error:
```
Failed to upload test-esg-attachment.txt: Data entry not found.
Please save data before uploading attachments.
```

### Console Error Log:
```javascript
[FileUpload] Files selected: 1
[FileUpload] Upload error: JSHandle@error
[FileUpload] Failed to upload test-esg-attachment.txt:
  Data entry not found. Please save data before uploading attachments.
```

### Network Error:
- HTTP 404 (NOT FOUND) response from upload endpoint
- Suggests the data entry ID is not being found in the database

---

## Root Cause Analysis

### Hypothesis 1: Missing data_entry_id Parameter (Most Likely)
The file upload handler is not receiving or passing the `data_entry_id` when uploading files to existing entries. Possible causes:

1. **Modal State Issue:**
   - When modal reopens, the `data_entry_id` may not be set in the file upload handler's context
   - The handler may be looking for `currentEntryId` but it's not populated

2. **Timing Issue:**
   - File upload handler initializes before data loads
   - Entry ID becomes available after handler has already initialized

3. **Data Loading Logic:**
   - The dimensional data loads correctly (we see the values)
   - But the entry ID may not be stored in the same state/context that the file upload handler uses

### Hypothesis 2: API Endpoint Issue
The upload API endpoint may be:
- Not receiving the entry ID parameter
- Receiving it but looking in the wrong database table
- Using an incorrect query to find the entry

### Hypothesis 3: Data Save Timing
- Data appears to save (modal closes)
- But database commit may not be complete
- Upload handler tries to find entry before it's fully saved

---

## Technical Investigation Points

### Frontend Investigation Needed:

1. **File Upload Handler Initialization:**
   ```javascript
   // Check how currentEntryId is set
   // Located in: app/static/js/user_v2/file_upload_handler.js
   ```
   - Verify `this.currentEntryId` is populated when modal reopens
   - Check if `loadExistingAttachments()` is called
   - Verify data entry ID is passed to upload function

2. **Modal State Management:**
   ```javascript
   // Check modal shown event
   // When modal reopens, is the entry ID properly set?
   ```

3. **Upload Request:**
   - Check FormData being sent to `/user/v2/fields/{field_id}/dimensional-data/upload`
   - Verify `data_entry_id` parameter is included
   - Check if date/dimension parameters are being sent

### Backend Investigation Needed:

1. **Upload Endpoint:**
   ```python
   # app/routes/user_v2/dimensional_data_api.py or similar
   # Check how data_entry_id is extracted from request
   # Verify database query to find entry
   ```

2. **Database Query:**
   - Verify the entry was actually saved (check esg_data table)
   - Check if query is looking for correct combination of:
     - field_id
     - entity_id
     - reporting_date
     - dimension combination

3. **Data Model:**
   - Check if dimensional data entries are created differently than regular entries
   - Verify primary key and foreign key relationships

---

## Code Locations to Investigate

### Frontend Files:
```
app/static/js/user_v2/
├── file_upload_handler.js           # Main file upload logic
├── dimensional_data_handler.js      # Dimensional data modal handler
└── phase4_features.js               # Integration point
```

### Backend Files:
```
app/routes/user_v2/
├── dimensional_data_api.py          # Dimensional data save/load endpoints
└── (upload endpoint file)           # File upload endpoint

app/models/
└── esg_data.py                      # ESGData model
```

### Key Functions to Review:
1. Frontend: `FileUploadHandler.uploadFile()`
2. Frontend: `FileUploadHandler.setCurrentEntry()`
3. Frontend: Modal reopen data loading
4. Backend: Upload endpoint handler
5. Backend: Data entry lookup query

---

## Impact Assessment

### User Impact:
- **Severity:** CRITICAL
- **Frequency:** Every time a user tries to upload files to existing data
- **Workaround:** NONE - Feature completely broken for primary use case
- **Affected Users:** All users attempting to attach documents to data entries

### Business Impact:
- **Data Quality:** Users cannot provide supporting documentation
- **Compliance:** May violate audit/compliance requirements for documented evidence
- **Trust:** Users may lose confidence in the application
- **Adoption:** Feature cannot be released to production

---

## Workarounds

**No workaround available.** The feature is fundamentally broken for the primary use case.

**Note:** Upload works for NEW, UNSAVED entries (shows warning), but fails for SAVED entries.

---

## Suggested Fix

### Short-term Fix (Immediate):

1. **Ensure data_entry_id is captured on modal open:**
   ```javascript
   // In dimensional_data_handler.js or file_upload_handler.js
   window.addEventListener('modalShown', (event) => {
     if (event.detail.entryId) {
       fileUploadHandler.setCurrentEntry(event.detail.entryId);
     }
   });
   ```

2. **Pass entry ID when loading dimensional data:**
   ```javascript
   // When data loads successfully, set the entry ID
   if (response.data.entry_id) {
     this.currentEntryId = response.data.entry_id;
   }
   ```

3. **Backend: Improve error messaging:**
   ```python
   # Return more specific error with debugging info
   # Include what parameters were received
   ```

### Long-term Fix (Comprehensive):

1. **Refactor entry ID management:**
   - Create a centralized state manager for current data entry
   - Ensure all handlers (dimensional, file upload, notes) use same source

2. **Add validation:**
   - Frontend: Validate entry ID exists before allowing upload
   - Backend: Return detailed error with missing parameters

3. **Add logging:**
   - Log entry ID when data saves
   - Log entry ID when modal reopens
   - Log entry ID when file upload initiates

4. **Add unit tests:**
   - Test file upload with new entries
   - Test file upload with existing entries
   - Test file upload after data modification

---

## Testing Requirements

Before marking as fixed, verify:

1. ✅ File uploads successfully to NEW data entry (after save)
2. ✅ File uploads successfully to EXISTING data entry (after reopen)
3. ✅ Multiple files can be uploaded
4. ✅ Files can be removed
5. ✅ Files persist across modal sessions
6. ✅ Files appear in historical data view
7. ✅ Error handling shows appropriate messages
8. ✅ Upload progress indicators work correctly

---

## Related Issues

- Enhancement #3: File Upload Feature Implementation
- Phase 4 Advanced Features
- User Dashboard V2 Development

---

## Attachments

### Screenshots:
1. `screenshots/test-case-1-warning-alert.png` - Warning system works
2. `screenshots/test-case-2-data-entered-before-save.png` - Data entry screen
3. `screenshots/test-case-2-data-loaded-ready-for-upload.png` - Data loaded, ready to upload
4. (File with error status would be visible if screenshot tool worked)

### Console Logs:
See Testing Summary document for complete console log output.

---

## Priority Justification

**Why P0 Critical Blocker:**

1. **Core Functionality:** File upload is a primary feature of Enhancement #3
2. **No Workaround:** Users cannot complete their workflow
3. **Blocking Testing:** Cannot test 4 out of 7 test scenarios
4. **Production Risk:** Feature cannot be released in this state
5. **User Impact:** Affects 100% of file upload attempts on existing data

**Timeline:** Must be fixed before any production deployment.

---

## Next Steps

1. ⏭️ Assign to backend developer for investigation
2. ⏭️ Frontend developer to verify entry ID handling
3. ⏭️ Add debugging/logging to track entry ID flow
4. ⏭️ Implement fix
5. ⏭️ Unit test the fix
6. ⏭️ Request re-test from UI testing agent
7. ⏭️ Complete full test suite (all 7 test cases)

---

**Report Created:** November 14, 2025
**Last Updated:** November 14, 2025
**Assignee:** TBD
**Estimated Fix Time:** TBD
