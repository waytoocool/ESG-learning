# 🚨 CRITICAL BUG FOUND - Enhancement #4 Bulk Upload

**Bug ID:** BUG-ENH4-003
**Severity:** CRITICAL - BLOCKS UPLOAD WORKFLOW
**Found Date:** 2025-11-19
**Found During:** Automated UI Testing with Playwright MCP
**Status:** NEEDS FIX

---

## Bug Description

**Summary:** File upload in Bulk Upload modal is incorrectly routing to the attachment API instead of the bulk upload API.

**Error Message:**
```
Failed to upload Template-overdue-2025-11-19-FILLED.xlsx:
Data entry not found. Please save data before uploading attachments.
```

**Expected Behavior:**
- User uploads filled Excel template on Step 2 (Upload File)
- File is sent to `/api/user/v2/bulk-upload/upload` endpoint
- File is parsed and validated
- User proceeds to Step 3 (Validate)

**Actual Behavior:**
- User uploads Excel file
- File upload triggers the wrong API endpoint (likely attachment upload API)
- Error message appears about "Data entry not found"
- Upload fails completely

---

## Technical Analysis

### Root Cause

The file upload component in the Bulk Upload modal appears to be using the **file upload handler** for attachments (`file_upload_handler.js`) instead of a dedicated bulk upload file handler.

**Evidence:**
1. Error message references "Data entry not found"
2. This is the exact error from the attachment upload API (requires existing ESGData entry)
3. The bulk upload flow should NOT require an existing data entry

### Code Location

**Suspected Issue:**
```javascript
// File: app/static/js/user_v2/file_upload_handler.js
// This handler is designed for attachments to EXISTING data entries
// It should NOT be used for bulk upload templates
```

**Expected Fix Location:**
```javascript
// File: app/static/js/user_v2/bulk_upload_handler.js (IF IT EXISTS)
// OR needs to be created

// Should handle file upload for bulk upload modal specifically
// Should POST to: /api/user/v2/bulk-upload/upload
```

---

## Reproduction Steps

1. Login as bob@alpha.com / user123
2. Navigate to dashboard: http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/dashboard
3. Click "Bulk Upload Data" button
4. Select "Overdue Only" filter
5. Click "Download Template"
6. Fill template with test data (any values)
7. On Step 2 (Upload File), select the filled template
8. Observe error: "Data entry not found. Please save data before uploading attachments."

**Result:** Upload fails ❌

---

## Impact Assessment

### Severity: CRITICAL

**Why Critical:**
- **Blocks entire upload workflow** - Users cannot proceed past Step 2
- **Feature is completely non-functional** - Template download works, but upload doesn't
- **Production Impact:** If deployed, users would see a broken feature
- **User Experience:** Confusing error message (mentions "data entry" and "attachments")

### Affected Functionality

✅ **Working:**
- Template download (all 3 filters)
- Modal UI/UX
- Step 1 navigation

❌ **Broken:**
- File upload (Step 2)
- Validation (Step 3) - cannot reach
- Submission (Step 5) - cannot reach
- Entire end-to-end workflow

---

## Fix Required

### Option 1: Create Dedicated Bulk Upload Handler (RECOMMENDED)

**Create:** `app/static/js/user_v2/bulk_upload_handler.js`

```javascript
class BulkUploadHandler {
    constructor() {
        this.uploadEndpoint = '/api/user/v2/bulk-upload/upload';
        this.validateEndpoint = '/api/user/v2/bulk-upload/validate';
        this.submitEndpoint = '/api/user/v2/bulk-upload/submit';
    }

    async handleFileUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(this.uploadEndpoint, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(await response.text());
        }

        return await response.json();
    }
}
```

### Option 2: Modify Existing Handler

**Modify:** `app/static/js/user_v2/file_upload_handler.js`

Add conditional logic to detect bulk upload context:

```javascript
if (isBulkUploadModal) {
    // Use bulk upload endpoint
    endpoint = '/api/user/v2/bulk-upload/upload';
} else {
    // Use attachment endpoint
    endpoint = '/api/user/v2/attachment/upload';
}
```

---

## Testing Required After Fix

### Unit Tests
- [ ] Verify bulk upload handler uses correct endpoint
- [ ] Verify file upload returns session data
- [ ] Verify error handling for invalid files

### Integration Tests
- [ ] Upload valid template → Should succeed
- [ ] Upload invalid file format (.pdf) → Should show error
- [ ] Upload oversized file (>5MB) → Should show error
- [ ] Upload empty template → Should show validation errors

### E2E Tests
- [ ] Complete workflow: Download → Fill → Upload → Validate → Submit
- [ ] Verify database entries created
- [ ] Verify dashboard stats updated

---

## Workaround

**None available.** The upload feature is completely blocked.

**Users must use individual data entry** until this bug is fixed.

---

## Related Files

### Frontend
- `app/templates/user_v2/_bulk_upload_modal.html` - Modal template
- `app/static/js/user_v2/file_upload_handler.js` - Current (incorrect) handler
- `app/static/js/user_v2/bulk_upload_handler.js` - Needs to be created

### Backend
- `app/routes/user_v2/bulk_upload_api.py` - API endpoints (likely correct)
- `app/services/user_v2/bulk_upload/file_upload_service.py` - Upload service

---

## Recommendations

### Immediate (Before Production)
1. **DO NOT DEPLOY** this feature until bug is fixed
2. Create dedicated bulk upload handler
3. Test complete upload workflow
4. Verify all API endpoints are correctly wired

### Short-term
1. Add integration tests for upload flow
2. Add E2E tests for complete workflow
3. Improve error messages (don't show attachment errors in bulk upload context)

### Long-term
1. Consider separating file upload handlers more clearly
2. Add upload progress indicators
3. Add client-side file validation before upload

---

## Test Evidence

### Screenshot
- File: `07-ready-for-upload.png` - Shows Step 2 ready state
- File: Upload failed (screenshot blocked by alert dialog)

### Console Logs
```
Alert dialog: "Failed to upload Template-overdue-2025-11-19-FILLED.xlsx:
Data entry not found. Please save data before uploading attachments."
```

### Network Request
- Expected: POST to `/api/user/v2/bulk-upload/upload`
- Actual: POST to `/api/user/v2/attachment/upload` (or similar)

---

## Priority

**P0 - CRITICAL**

This bug completely blocks the bulk upload feature. Without fixing this, the feature cannot be released to production.

**Estimated Fix Time:** 2-4 hours
- 1 hour: Create bulk_upload_handler.js
- 1 hour: Wire up to modal HTML
- 1-2 hours: Test and verify

---

## Assignee

**Recommended:** Backend Developer + Frontend Developer (pair programming)

**Skills Needed:**
- JavaScript (ES6+)
- Flask/Python
- File upload handling
- Session management

---

**Report Generated:** 2025-11-19
**Reported By:** Claude Code (Automated Testing)
**Testing Tool:** Playwright MCP
