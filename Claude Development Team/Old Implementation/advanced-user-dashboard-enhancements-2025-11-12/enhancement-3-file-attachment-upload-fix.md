# Enhancement #3: File Attachment Upload Bug Fix & Complete Implementation

**Date Created:** 2025-11-12
**Status:** Bug Confirmed - Implementation Plan Ready
**Priority:** High
**Complexity:** Medium
**Type:** Bug Fix + Feature Completion

---

## Problem Statement

### Bug Discovery (Chrome DevTools Testing)

**Test Date:** 2025-11-12
**Testing Tool:** Chrome DevTools MCP
**Status:** ❌ Bug Confirmed - File Upload UI Not Working

### What Works ✅

1. **File Input Element:** Present and functional in DOM
2. **File Selection:** Works via both click and drag-drop
3. **File Loading:** Files successfully load into `<input type="file">` element
4. **Change Detection:** Modal shows "Unsaved changes" indicator
5. **Event Handlers:** Properly attached and triggering
6. **Console Logging:** Confirms file selection ("Files selected: 1")

### What Doesn't Work ❌

**Critical Bug:** Uploaded files are NOT displayed in the UI

**Root Cause:**
The file upload event handler in `app/templates/user_v2/dashboard.html` (lines 1387-1390) is incomplete:

```javascript
fileInput.addEventListener('change', (e) => {
    const files = e.target.files;
    console.log('Files selected:', files.length);  // Only logs, doesn't display
});
```

The code:
- ✅ Detects file selection
- ✅ Logs to console
- ❌ **Does NOT populate the `fileList` div** with file names/details
- ❌ **Does NOT track files for submission**
- ❌ **Does NOT provide file removal option**

### Evidence

**Test Scenario:**
- File uploaded: `test-attachment.txt` (58 bytes)
- `fileInput.files.length = 1` ✓
- `fileList.innerHTML = ""` (empty) ✗

**Screenshots Captured:**
- `.playwright-mcp/attachment-upload-modal.png` - Initial modal state
- `.playwright-mcp/file-uploaded-state.png` - After file upload
- `.playwright-mcp/bug-file-upload-not-displaying.png` - Final state showing bug

---

## Existing Infrastructure Analysis

### Database Layer ✅ (Complete)

**ESGDataAttachment Model** exists in `app/models/esg_data.py`:

```python
class ESGDataAttachment(db.Model):
    """Model for storing ESG data attachments."""
    __tablename__ = 'esg_data_attachments'

    id = db.Column(db.String(36), primary_key=True)
    data_id = db.Column(db.String(36), ForeignKey('esg_data.data_id'))
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(127), nullable=False)
    uploaded_at = db.Column(db.DateTime)
    uploaded_by = db.Column(db.Integer, ForeignKey('user.id'))

    # Relationships
    esg_data = db.relationship('ESGData', back_populates='attachments')
    user = db.relationship('User', backref='uploaded_attachments')
```

**Status:** ✅ Database model is complete and production-ready

### Configuration ✅ (Complete)

**Found in `app/config.py`:**

```python
MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB max file size
ALLOWED_EXTENSIONS = {
    # Documents
    'pdf', 'doc', 'docx', 'txt', 'rtf',
    # Spreadsheets
    'xls', 'xlsx', 'csv', 'ods',
    # Images
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff',
    # Archives
    'zip', 'rar', '7z',
    # Presentations
    'ppt', 'pptx'
}
UPLOAD_FOLDER = 'uploads/'
```

**Status:** ✅ Configuration is complete

### Legacy Backend API ✅ (Exists but needs V2 version)

**Found in `app/routes/user.py` (lines 640-678):**
- Upload endpoint exists for legacy dashboard
- **Requires data to be saved first** (line 640)
- Stores files in: `uploads/{entity_id}/{data_id}_{filename}`
- Already has validation and ESGDataAttachment creation
- Also has GET and DELETE endpoints for attachments

**Status:** ⚠️ Needs to be copied/adapted for V2 dashboard

### Frontend UI ⚠️ (Partially Complete)

**What Exists:**
- ✅ HTML structure (fileUploadArea, fileInput, fileList)
- ✅ Basic event handlers (click, drag, drop, change)
- ✅ Visual upload area with icons

**What's Missing:**
- ❌ File list rendering logic
- ❌ File preview/display
- ❌ Remove file functionality
- ❌ File size/type validation
- ❌ Progress indicators
- ❌ Error handling UI

---

## Solution Design

### Implementation Decisions (Confirmed)

1. ✅ **Upload Immediately:** Files upload as soon as selected (don't wait for Save Data)
2. ✅ **Require Data First:** Show warning if user tries to upload before saving data at least once
3. ✅ **All Field Types:** Raw, computed, and dimensional fields all support attachments (uniform UX)
4. ✅ **File Limits:** 20MB per file (from config), multiple files allowed per entry
5. ✅ **Single Attachment List:** Same approach for all field types (no special handling for dimensional)
6. ✅ **File Structure:** `uploads/{company_id}/{entity_id}/{uuid}_{filename}` (multi-tenant safe)
7. ✅ **Editing:** Show existing attachments, allow add/remove
8. ✅ **Permissions:** Anyone with ESGData access can delete attachments (entity-level)
9. ✅ **No Preview:** Download only (preview is future enhancement)
10. ✅ **Display:** Show attachment icons/links inline in historical data table

### Architecture

```
┌─────────────────────────────────────────────────┐
│          Frontend: File Upload UI               │
├─────────────────────────────────────────────────┤
│ • Display selected files with details           │
│ • File validation (size, type)                  │
│ • Remove file button per file                   │
│ • Drag & drop enhancement                       │
│ • Upload on selection (immediate)               │
│ • Warn if no ESGData exists yet                 │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│          Backend: File Upload API (V2)           │
├─────────────────────────────────────────────────┤
│ • POST /user/v2/api/upload-attachment            │
│ • GET /user/v2/api/attachments/<data_id>         │
│ • DELETE /user/v2/api/attachment/<attachment_id> │
│ • File validation (server-side)                 │
│ • Secure file storage                           │
│ • Database record creation                      │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│          Storage: Multi-Tenant File System       │
├─────────────────────────────────────────────────┤
│ • Directory: uploads/{company_id}/{entity_id}/  │
│ • Filename: {uuid}_{original_name}              │
│ • Max size: 20MB per file                       │
│ • Extensions: 17 types (docs, sheets, images)   │
└─────────────────────────────────────────────────┘
```

### File Upload Flow

```
User opens modal
    ↓
User saves data (creates ESGData entry)
    ↓
User selects file(s)
    ↓
[1] Frontend validates file (size, type)
    ↓
[2] Display file in UI with "Uploading..." status
    ↓
[3] Upload file to server immediately
    ↓
[4] Server validates and stores file
    ↓
[5] Create ESGDataAttachment record linked to data_id
    ↓
[6] Return success, update UI to "Uploaded"
    ↓
User can remove file (deletes from server + DB)
    ↓
Modal close (files remain on server, linked to ESGData)
```

---

## Implementation Plan

### Phase 1: Frontend Bug Fix - Display Selected Files

#### 1.1 Create File Manager Class
**File:** `app/static/js/user_v2/file_upload_handler.js` (NEW)

```javascript
/**
 * FileUploadHandler
 * Manages file upload UI, validation, and submission
 *
 * Key Features:
 * - Display selected files with details
 * - Immediate upload on selection
 * - Requires ESGData to exist before upload
 * - Remove uploaded files
 * - Validation (size, type)
 */
class FileUploadHandler {
    constructor(options = {}) {
        this.uploadArea = document.getElementById(options.uploadAreaId || 'fileUploadArea');
        this.fileInput = document.getElementById(options.fileInputId || 'fileInput');
        this.fileList = document.getElementById(options.fileListId || 'fileList');

        // Configuration from app/config.py
        this.maxFileSize = 20 * 1024 * 1024; // 20MB
        this.allowedExtensions = [
            // Documents
            'pdf', 'doc', 'docx', 'txt', 'rtf',
            // Spreadsheets
            'xls', 'xlsx', 'csv', 'ods',
            // Images
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff',
            // Archives
            'zip', 'rar', '7z',
            // Presentations
            'ppt', 'pptx'
        ];

        // State
        this.currentDataId = null; // ESGData data_id
        this.uploadedFiles = []; // Track uploaded files

        // Initialize
        this.init();
    }

    init() {
        if (!this.uploadArea || !this.fileInput || !this.fileList) {
            console.error('[FileUpload] Elements not found');
            return;
        }

        this.attachEventHandlers();
        console.log('[FileUpload] Handler initialized');
    }

    setDataId(dataId) {
        /**
         * Set the current ESGData data_id.
         * Must be called before allowing uploads.
         */
        this.currentDataId = dataId;
        console.log('[FileUpload] Data ID set:', dataId);
    }

    attachEventHandlers() {
        // Click to select
        this.uploadArea.addEventListener('click', () => {
            if (!this.currentDataId) {
                this.showWarning('Please save data before uploading attachments.');
                return;
            }
            this.fileInput.click();
        });

        // Drag and drop
        this.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();

            if (!this.currentDataId) {
                return;
            }

            this.uploadArea.classList.add('drag-over');
        });

        this.uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.uploadArea.classList.remove('drag-over');
        });

        this.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.uploadArea.classList.remove('drag-over');

            if (!this.currentDataId) {
                this.showWarning('Please save data before uploading attachments.');
                return;
            }

            const files = Array.from(e.dataTransfer.files);
            this.handleFileSelection(files);
        });

        // File input change
        this.fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            this.handleFileSelection(files);
        });
    }

    handleFileSelection(files) {
        console.log(`[FileUpload] Files selected: ${files.length}`);

        // Validate and upload files
        files.forEach(file => {
            const validation = this.validateFile(file);

            if (validation.valid) {
                this.uploadFile(file);
            } else {
                this.showError(validation.error);
            }
        });

        // Clear file input to allow re-selection
        this.fileInput.value = '';
    }

    validateFile(file) {
        // Check file size
        if (file.size > this.maxFileSize) {
            return {
                valid: false,
                error: `File "${file.name}" exceeds maximum size of ${this.formatFileSize(this.maxFileSize)}`
            };
        }

        // Check file extension
        const ext = file.name.split('.').pop().toLowerCase();
        if (!this.allowedExtensions.includes(ext)) {
            return {
                valid: false,
                error: `File type ".${ext}" is not allowed. Allowed types: ${this.allowedExtensions.join(', ')}`
            };
        }

        // Check duplicate
        const isDuplicate = this.uploadedFiles.some(f => f.filename === file.name);
        if (isDuplicate) {
            return {
                valid: false,
                error: `File "${file.name}" is already uploaded`
            };
        }

        return { valid: true };
    }

    async uploadFile(file) {
        const fileId = this.generateId();

        // Add to display with "uploading" status
        const fileObj = {
            id: fileId,
            filename: file.name,
            size: file.size,
            status: 'uploading',
            attachmentId: null
        };

        this.uploadedFiles.push(fileObj);
        this.renderFileList();

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('data_id', this.currentDataId);

            const response = await fetch('/user/v2/api/upload-attachment', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok || !result.success) {
                throw new Error(result.error || 'Upload failed');
            }

            // Update file object with success
            fileObj.status = 'uploaded';
            fileObj.attachmentId = result.attachment_id;

            console.log('[FileUpload] File uploaded:', result);

        } catch (error) {
            console.error('[FileUpload] Upload error:', error);
            fileObj.status = 'error';
            fileObj.error = error.message;
            this.showError(`Failed to upload ${file.name}: ${error.message}`);
        }

        this.renderFileList();
    }

    async removeFile(fileId) {
        const fileObj = this.uploadedFiles.find(f => f.id === fileId);
        if (!fileObj) return;

        // If uploaded, delete from server
        if (fileObj.status === 'uploaded' && fileObj.attachmentId) {
            try {
                const response = await fetch(`/user/v2/api/attachment/${fileObj.attachmentId}`, {
                    method: 'DELETE'
                });

                if (!response.ok) {
                    throw new Error('Failed to delete file from server');
                }

                console.log('[FileUpload] File deleted from server:', fileObj.attachmentId);

            } catch (error) {
                console.error('[FileUpload] Delete error:', error);
                this.showError(`Failed to delete ${fileObj.filename}`);
                return; // Don't remove from UI if server delete failed
            }
        }

        // Remove from list
        this.uploadedFiles = this.uploadedFiles.filter(f => f.id !== fileId);
        this.renderFileList();
    }

    renderFileList() {
        if (this.uploadedFiles.length === 0) {
            this.fileList.innerHTML = '';
            return;
        }

        let html = '<div class="file-list-container">';

        this.uploadedFiles.forEach(fileObj => {
            html += this.renderFileItem(fileObj);
        });

        html += '</div>';

        this.fileList.innerHTML = html;

        // Attach remove button handlers
        this.uploadedFiles.forEach(fileObj => {
            const removeBtn = document.querySelector(`[data-file-id="${fileObj.id}"]`);
            if (removeBtn) {
                removeBtn.onclick = (e) => {
                    e.stopPropagation();
                    this.removeFile(fileObj.id);
                };
            }
        });
    }

    renderFileItem(fileObj) {
        const statusIcon = this.getStatusIcon(fileObj.status);
        const statusClass = `file-status-${fileObj.status}`;

        return `
            <div class="file-item ${statusClass}">
                <div class="file-icon">
                    ${this.getFileIcon(fileObj.filename)}
                </div>
                <div class="file-info">
                    <div class="file-name" title="${this.escapeHtml(fileObj.filename)}">
                        ${this.escapeHtml(this.truncateFilename(fileObj.filename, 40))}
                    </div>
                    <div class="file-meta">
                        <span class="file-size">${this.formatFileSize(fileObj.size)}</span>
                        ${fileObj.status === 'error' ? `
                            <span class="file-error" title="${this.escapeHtml(fileObj.error || 'Upload failed')}">
                                Error
                            </span>
                        ` : ''}
                    </div>
                </div>
                <div class="file-status">
                    ${statusIcon}
                </div>
                <button class="file-remove" data-file-id="${fileObj.id}" title="Remove file" type="button">
                    <span class="material-icons">close</span>
                </button>
            </div>
        `;
    }

    getStatusIcon(status) {
        const icons = {
            'uploading': '<div class="spinner-border spinner-border-sm text-primary"></div>',
            'uploaded': '<span class="material-icons text-success">check_circle</span>',
            'error': '<span class="material-icons text-danger">error</span>'
        };
        return icons[status] || '';
    }

    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();

        if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'].includes(ext)) {
            return '<span class="material-icons">image</span>';
        } else if (ext === 'pdf') {
            return '<span class="material-icons">picture_as_pdf</span>';
        } else if (['xls', 'xlsx', 'csv', 'ods'].includes(ext)) {
            return '<span class="material-icons">table_chart</span>';
        } else if (['doc', 'docx', 'txt', 'rtf'].includes(ext)) {
            return '<span class="material-icons">description</span>';
        } else if (['ppt', 'pptx'].includes(ext)) {
            return '<span class="material-icons">slideshow</span>';
        } else if (['zip', 'rar', '7z'].includes(ext)) {
            return '<span class="material-icons">folder_zip</span>';
        } else {
            return '<span class="material-icons">attach_file</span>';
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }

    truncateFilename(filename, maxLength) {
        if (filename.length <= maxLength) return filename;
        const ext = filename.split('.').pop();
        const nameWithoutExt = filename.substring(0, filename.lastIndexOf('.'));
        const truncated = nameWithoutExt.substring(0, maxLength - ext.length - 4) + '...';
        return truncated + '.' + ext;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    generateId() {
        return 'file_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    showWarning(message) {
        // Use existing notification system
        alert(message); // Replace with your notification system
    }

    showError(message) {
        console.error('[FileUpload]', message);
        alert(message); // Replace with your notification system
    }

    async loadExistingAttachments(dataId) {
        /**
         * Load existing attachments for a data entry.
         * Called when modal opens with existing data.
         */
        if (!dataId) return;

        this.currentDataId = dataId;
        this.uploadedFiles = [];

        try {
            const response = await fetch(`/user/v2/api/attachments/${dataId}`);

            if (!response.ok) {
                throw new Error('Failed to load attachments');
            }

            const result = await response.json();

            if (result.success && result.attachments) {
                result.attachments.forEach(att => {
                    this.uploadedFiles.push({
                        id: this.generateId(),
                        filename: att.filename,
                        size: att.file_size,
                        status: 'uploaded',
                        attachmentId: att.id
                    });
                });

                this.renderFileList();
                console.log('[FileUpload] Loaded existing attachments:', result.attachments.length);
            }

        } catch (error) {
            console.error('[FileUpload] Error loading attachments:', error);
        }
    }

    reset() {
        this.currentDataId = null;
        this.uploadedFiles = [];
        this.renderFileList();
    }
}

// Export for global use
window.FileUploadHandler = FileUploadHandler;
```

#### 1.2 Add CSS Styling
**File:** `app/static/css/user_v2/file_upload.css` (NEW)

```css
/* File Upload Styling */
.file-upload-area {
    border: 2px dashed #e2e8f0;
    border-radius: 0.5rem;
    padding: 2rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    background: #f9fafb;
}

.file-upload-area:hover {
    border-color: #3f6212;
    background: #f0fdf4;
}

.file-upload-area.drag-over {
    border-color: #3f6212;
    background: #dcfce7;
    transform: scale(1.02);
}

.file-upload-area .material-icons-outlined {
    font-size: 2.5rem;
    color: #64748b;
    margin-bottom: 0.5rem;
}

.file-upload-area p {
    font-size: 0.875rem;
    color: #64748b;
    margin: 0;
}

/* File List Container */
.file-list-container {
    margin-top: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

/* File Item */
.file-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
    transition: all 0.2s;
}

.file-item:hover {
    border-color: #cbd5e1;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.file-item.file-status-uploaded {
    border-color: #86efac;
    background: #f0fdf4;
}

.file-item.file-status-error {
    border-color: #fca5a5;
    background: #fef2f2;
}

.file-item.file-status-uploading {
    border-color: #93c5fd;
    background: #eff6ff;
}

/* File Icon */
.file-icon {
    flex-shrink: 0;
    width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f1f5f9;
    border-radius: 0.375rem;
}

.file-icon .material-icons {
    font-size: 1.5rem;
    color: #64748b;
}

/* File Info */
.file-info {
    flex: 1;
    min-width: 0;
}

.file-name {
    font-size: 0.875rem;
    font-weight: 500;
    color: #1e293b;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.file-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.25rem;
}

.file-size {
    font-size: 0.75rem;
    color: #64748b;
}

.file-error {
    font-size: 0.75rem;
    color: #dc2626;
    cursor: help;
}

/* File Status */
.file-status {
    flex-shrink: 0;
}

.file-status .material-icons {
    font-size: 1.25rem;
}

/* Remove Button */
.file-remove {
    flex-shrink: 0;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    border-radius: 0.25rem;
    cursor: pointer;
    color: #64748b;
    transition: all 0.2s;
}

.file-remove:hover {
    background: #fee2e2;
    color: #dc2626;
}

.file-remove .material-icons {
    font-size: 1.125rem;
}

/* Dark Mode */
.dark .file-upload-area {
    border-color: #3f3f46;
    background: #18181b;
}

.dark .file-upload-area:hover {
    border-color: #3f6212;
    background: #1c2617;
}

.dark .file-item {
    background: #27272a;
    border-color: #3f3f46;
}

.dark .file-item:hover {
    border-color: #52525b;
}

.dark .file-name {
    color: #e2e8f0;
}

.dark .file-icon {
    background: #18181b;
}

.dark .file-remove:hover {
    background: #3f1f1f;
}
```

#### 1.3 Update Dashboard HTML
**File:** `app/templates/user_v2/dashboard.html`

**Add script and CSS includes (after line 1617):**

```html
<!-- File Upload Handler -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/user_v2/file_upload.css') }}">
<script src="{{ url_for('static', filename='js/user_v2/file_upload_handler.js') }}"></script>
```

**Replace file upload initialization (lines 1362-1391):**

```javascript
// Initialize File Upload Handler
window.fileUploadHandler = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize file upload handler
    window.fileUploadHandler = new FileUploadHandler({
        uploadAreaId: 'fileUploadArea',
        fileInputId: 'fileInput',
        fileListId: 'fileList'
    });

    console.log('[Dashboard] File upload handler initialized');
});

// Reset file handler when modal closes
const dataCollectionModalEl = document.getElementById('dataCollectionModal');
if (dataCollectionModalEl) {
    dataCollectionModalEl.addEventListener('hidden.bs.modal', function() {
        if (window.fileUploadHandler) {
            window.fileUploadHandler.reset();
        }
    });
}
```

**Update modal open handler to set data_id and load attachments:**

```javascript
// In the .open-data-modal click handler (around line 1466)
document.querySelectorAll('.open-data-modal').forEach(button => {
    button.addEventListener('click', async function() {
        const fieldId = this.dataset.fieldId;
        const fieldName = this.dataset.fieldName;
        const entityId = {{ current_entity.id if current_entity else 'null' }};
        const reportingDate = document.getElementById('selectedDate')?.value || new Date().toISOString().split('T')[0];

        // ... existing modal setup code ...

        // Check if ESGData exists for this field+entity+date
        const dataId = await getOrCreateDataId(fieldId, entityId, reportingDate);

        if (dataId) {
            // Set data ID in file handler and load existing attachments
            window.fileUploadHandler.setDataId(dataId);
            await window.fileUploadHandler.loadExistingAttachments(dataId);
        }

        modal.show();
    });
});

// Helper function to get existing data_id or create placeholder
async function getOrCreateDataId(fieldId, entityId, reportingDate) {
    try {
        const response = await fetch(
            `/api/user/v2/field-data/${fieldId}?entity_id=${entityId}&reporting_date=${reportingDate}`
        );

        if (response.ok) {
            const data = await response.json();
            if (data.success && data.data_id) {
                return data.data_id;
            }
        }

        // No data exists yet - return null
        // User will need to save data before uploading files
        return null;

    } catch (error) {
        console.error('Error checking for existing data:', error);
        return null;
    }
}
```

**Update submit handler to set data_id after first save:**

```javascript
// After successful data save (around line 1550)
const response = await fetch('/user/v2/api/submit-simple-data', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        field_id: fieldId,
        entity_id: entityId,
        reporting_date: reportingDate,
        raw_value: dataValue,
        notes: document.getElementById('fieldNotes')?.value || null
    })
});

const result = await response.json();

if (result.success && result.data_id) {
    // Enable file uploads now that data exists
    window.fileUploadHandler.setDataId(result.data_id);

    showSuccessMessage('Data saved successfully');
}
```

---

### Phase 2: Backend API Implementation (V2)

#### 2.1 Create V2 Attachment API
**File:** `app/routes/user_v2/attachment_api.py` (NEW)

Copy and adapt from `app/routes/user.py` lines 640-710:

```python
"""
Attachment API for User Dashboard V2
Handles file upload, download, and deletion for ESGData attachments.

Adapted from legacy upload implementation with improvements:
- Multi-tenant file structure: uploads/{company_id}/{entity_id}/
- UUID-based filenames for uniqueness
- Immediate upload on file selection
- Requires ESGData to exist before upload
"""

from flask import jsonify, request, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

from . import user_v2_bp
from app.decorators.auth import tenant_required_for
from app.models.esg_data import ESGData, ESGDataAttachment
from app.extensions import db
import logging

logger = logging.getLogger(__name__)


def allowed_file(filename):
    """Check if file extension is allowed (from config)."""
    if not filename or '.' not in filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower()
    return extension in current_app.config.get('ALLOWED_EXTENSIONS', set())


@user_v2_bp.route('/api/upload-attachment', methods=['POST'])
@login_required
@tenant_required_for('USER')
def upload_attachment():
    """
    Upload file attachment for ESG data.

    Form Data:
        file: File to upload (required)
        data_id: ESGData data_id (required)

    Returns:
        {
            "success": true,
            "attachment_id": "uuid",
            "filename": "original_name.pdf",
            "file_size": 12345,
            "mime_type": "application/pdf"
        }

    Errors:
        400: No file provided, invalid file type, file too large, no data_id
        404: ESGData not found
        500: Server error
    """
    try:
        # Validate file in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Validate file extension
        if not allowed_file(file.filename):
            allowed = current_app.config.get('ALLOWED_EXTENSIONS', set())
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Allowed types: {", ".join(sorted(allowed))}'
            }), 400

        # Get data_id from form
        data_id = request.form.get('data_id')
        if not data_id:
            return jsonify({
                'success': False,
                'error': 'data_id is required'
            }), 400

        # Verify ESGData exists and belongs to current tenant
        esg_data = ESGData.query.filter_by(
            data_id=data_id,
            company_id=current_user.company_id
        ).first()

        if not esg_data:
            return jsonify({
                'success': False,
                'error': 'Data entry not found. Please save data before uploading attachments.'
            }), 404

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 20 * 1024 * 1024)
        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            return jsonify({
                'success': False,
                'error': f'File size exceeds maximum of {max_mb}MB'
            }), 400

        # Generate secure filename with UUID
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}_{original_filename}"

        # Create multi-tenant directory structure
        # uploads/{company_id}/{entity_id}/
        upload_base = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        company_dir = os.path.join(
            upload_base,
            str(current_user.company_id),
            str(esg_data.entity_id)
        )
        os.makedirs(company_dir, exist_ok=True)

        # Save file
        file_path = os.path.join(company_dir, unique_filename)
        file.save(file_path)

        # Create attachment record
        attachment = ESGDataAttachment(
            data_id=data_id,
            filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type or 'application/octet-stream',
            uploaded_by=current_user.id
        )

        db.session.add(attachment)
        db.session.commit()

        logger.info(f"[Upload] File uploaded: {original_filename} ({file_size} bytes) "
                   f"for data_id={data_id} by user={current_user.id}")

        return jsonify({
            'success': True,
            'attachment_id': attachment.id,
            'filename': attachment.filename,
            'file_size': attachment.file_size,
            'mime_type': attachment.mime_type
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"[Upload] Error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_v2_bp.route('/api/attachments/<data_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_attachments(data_id):
    """
    Get all attachments for an ESGData entry.

    Args:
        data_id: ESGData data_id

    Returns:
        {
            "success": true,
            "attachments": [
                {
                    "id": "uuid",
                    "filename": "report.pdf",
                    "file_size": 12345,
                    "mime_type": "application/pdf",
                    "uploaded_at": "2025-01-12T10:30:00",
                    "uploaded_by": 1
                }
            ]
        }
    """
    try:
        # Verify ESGData exists and belongs to current tenant
        esg_data = ESGData.query.filter_by(
            data_id=data_id,
            company_id=current_user.company_id
        ).first()

        if not esg_data:
            return jsonify({
                'success': False,
                'error': 'Data entry not found'
            }), 404

        # Get attachments
        attachments = ESGDataAttachment.query.filter_by(data_id=data_id).all()

        return jsonify({
            'success': True,
            'attachments': [
                {
                    'id': att.id,
                    'filename': att.filename,
                    'file_size': att.file_size,
                    'mime_type': att.mime_type,
                    'uploaded_at': att.uploaded_at.isoformat() if att.uploaded_at else None,
                    'uploaded_by': att.uploaded_by
                }
                for att in attachments
            ]
        })

    except Exception as e:
        logger.error(f"[Get Attachments] Error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_v2_bp.route('/api/attachment/<attachment_id>', methods=['DELETE'])
@login_required
@tenant_required_for('USER')
def delete_attachment(attachment_id):
    """
    Delete an attachment.

    Permissions: Anyone with access to the ESGData can delete attachments.

    Args:
        attachment_id: Attachment ID to delete

    Returns:
        {
            "success": true,
            "message": "File deleted successfully"
        }
    """
    try:
        # Find attachment
        attachment = ESGDataAttachment.query.filter_by(id=attachment_id).first()

        if not attachment:
            return jsonify({
                'success': False,
                'error': 'Attachment not found'
            }), 404

        # Verify ESGData belongs to current tenant
        esg_data = ESGData.query.filter_by(
            data_id=attachment.data_id,
            company_id=current_user.company_id
        ).first()

        if not esg_data:
            return jsonify({
                'success': False,
                'error': 'Permission denied'
            }), 403

        # Delete file from filesystem
        if os.path.exists(attachment.file_path):
            os.remove(attachment.file_path)
            logger.info(f"[Delete] File removed from filesystem: {attachment.file_path}")

        # Delete database record
        db.session.delete(attachment)
        db.session.commit()

        logger.info(f"[Delete] Attachment deleted: {attachment.filename} "
                   f"(id={attachment_id}) by user={current_user.id}")

        return jsonify({
            'success': True,
            'message': 'File deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"[Delete] Error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_v2_bp.route('/api/download-attachment/<attachment_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def download_attachment(attachment_id):
    """
    Download an attachment file.

    Args:
        attachment_id: Attachment ID to download

    Returns:
        File download response
    """
    try:
        # Find attachment
        attachment = ESGDataAttachment.query.filter_by(id=attachment_id).first()

        if not attachment:
            return jsonify({
                'success': False,
                'error': 'Attachment not found'
            }), 404

        # Verify ESGData belongs to current tenant
        esg_data = ESGData.query.filter_by(
            data_id=attachment.data_id,
            company_id=current_user.company_id
        ).first()

        if not esg_data:
            return jsonify({
                'success': False,
                'error': 'Permission denied'
            }), 403

        # Check if file exists
        if not os.path.exists(attachment.file_path):
            return jsonify({
                'success': False,
                'error': 'File not found on server'
            }), 404

        # Send file
        return send_file(
            attachment.file_path,
            as_attachment=True,
            download_name=attachment.filename,
            mimetype=attachment.mime_type
        )

    except Exception as e:
        logger.error(f"[Download] Error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

#### 2.2 Update Field API to Return data_id
**File:** `app/routes/user_v2/field_api.py`

Update the `get_field_data` endpoint to return `data_id`:

```python
# In get_field_data endpoint (line ~50-70)
return jsonify({
    'success': True,
    'data_id': esg_data.data_id,  # ADD THIS
    'field_id': esg_data.field_id,
    'entity_id': esg_data.entity_id,
    'reporting_date': esg_data.reporting_date.isoformat(),
    'raw_value': esg_data.raw_value,
    'calculated_value': esg_data.calculated_value,
    'notes': esg_data.notes,
    # ... rest of fields
})
```

#### 2.3 Update Submit API to Return data_id
**File:** `app/routes/user_v2/dimensional_data_api.py`

```python
# In submit_simple_data (around line 125)
return jsonify({
    'success': True,
    'message': 'Data saved successfully',
    'data_id': esg_data.data_id  # ADD THIS
})
```

---

### Phase 3: Display Attachments in Historical Data

#### 3.1 Update Historical Data API
**File:** `app/routes/user_v2/field_api.py` (get_field_history endpoint, line ~585)

```python
# In the history list building
history.append({
    'reporting_date': entry.reporting_date.isoformat(),
    'value': value,
    'unit': entry.unit or field.default_unit,
    'has_dimensions': has_dimensions,
    'dimension_values': entry.dimension_values if has_dimensions else None,
    'notes': entry.notes,
    'has_notes': entry.has_notes(),
    'attachments': [  # ADD THIS
        {
            'id': att.id,
            'filename': att.filename,
            'file_size': att.file_size,
            'mime_type': att.mime_type,
            'uploaded_at': att.uploaded_at.isoformat() if att.uploaded_at else None
        }
        for att in entry.attachments
    ],
    'created_at': entry.created_at.isoformat() if entry.created_at else None,
    'updated_at': entry.updated_at.isoformat() if entry.updated_at else None
})
```

#### 3.2 Update Historical Data UI
**File:** `app/templates/user_v2/dashboard.html` (renderHistoryTable function)

```javascript
// Add attachments column to table header
html += '<thead><tr>';
html += '<th>Reporting Date</th>';
html += '<th>Value</th>';
html += '<th>Notes</th>';
html += '<th>Attachments</th>';  // ADD THIS
html += '<th>Submitted On</th>';
html += '</tr></thead>';

// In the loop, add attachments cell
const attachmentsDisplay = entry.attachments && entry.attachments.length > 0
    ? entry.attachments.map(att => `
        <a href="/user/v2/api/download-attachment/${att.id}"
           class="attachment-link"
           title="${escapeHtml(att.filename)} (${formatFileSize(att.file_size)})"
           download>
          <span class="material-icons text-sm">attach_file</span>
          ${escapeHtml(truncateText(att.filename, 20))}
        </a>
      `).join('<br>')
    : '<span class="text-muted">-</span>';

html += `<td class="attachments-cell">${attachmentsDisplay}</td>`;

// Add CSS for attachment links
/*
.attachment-link {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    background: #eff6ff;
    border-radius: 0.25rem;
    color: #1e40af;
    text-decoration: none;
    font-size: 0.875rem;
    transition: all 0.2s;
}

.attachment-link:hover {
    background: #dbeafe;
    color: #1e3a8a;
}

.dark .attachment-link {
    background: #1e3a5f;
    color: #93c5fd;
}
*/
```

---

## Test Cases

### Test Case 1: Upload File After Saving Data
**Steps:**
1. Open data entry modal
2. Enter value: "85"
3. Click "Save Data"
4. After save succeeds, click file upload area
5. Select a PDF file (< 20MB)

**Expected:**
- ✅ File picker opens after save
- ✅ File uploads immediately
- ✅ File appears in list with name, size, and "Uploading..." status
- ✅ Status changes to "Uploaded" with green checkmark
- ✅ Remove button (X) appears

---

### Test Case 2: Try to Upload Before Saving Data
**Steps:**
1. Open new field modal (no existing data)
2. Try to click file upload area (without saving data first)

**Expected:**
- ✅ Warning message: "Please save data before uploading attachments"
- ✅ File picker does NOT open
- ✅ No upload attempt

---

### Test Case 3: Remove Uploaded File
**Steps:**
1. Upload a file (wait for upload to complete)
2. Click remove (X) button

**Expected:**
- ✅ File disappears from list
- ✅ File deleted from server (check uploads folder)
- ✅ ESGDataAttachment record deleted from database

---

### Test Case 4: File Size Validation
**Steps:**
1. Try to upload a file > 20MB

**Expected:**
- ✅ Error message: "File size exceeds maximum of 20MB"
- ✅ File NOT added to list
- ✅ No upload attempt

---

### Test Case 5: File Type Validation
**Steps:**
1. Try to upload .exe or .sh file

**Expected:**
- ✅ Error message: "File type not allowed. Allowed types: pdf, xlsx, ..."
- ✅ File NOT added to list

---

### Test Case 6: Multiple File Upload
**Steps:**
1. Save data first
2. Select 3 different files at once (or drag-drop multiple)

**Expected:**
- ✅ All 3 files appear in list
- ✅ Each uploads independently
- ✅ Status shows for each file individually

---

### Test Case 7: Edit Existing Data - Load Attachments
**Steps:**
1. Open modal for data entry with existing attachments
2. View file list

**Expected:**
- ✅ Existing attachments load and display
- ✅ Each shows with "Uploaded" status
- ✅ Can remove existing attachments
- ✅ Can add new attachments

---

### Test Case 8: View Attachments in Historical Data
**Steps:**
1. Submit data with 2 attachments
2. Open "Historical Data" tab
3. Find the entry in the table

**Expected:**
- ✅ Attachments column shows both file icons/links
- ✅ Each attachment is clickable
- ✅ Filenames are truncated if too long
- ✅ Hover shows full filename + file size

---

### Test Case 9: Download Attachment
**Steps:**
1. View historical data with attachment
2. Click on attachment filename/icon

**Expected:**
- ✅ File downloads with correct original filename
- ✅ File can be opened correctly
- ✅ File size matches uploaded file

---

### Test Case 10: Computed Field Attachments
**Steps:**
1. Open computed field modal
2. Save (even though value is calculated)
3. Upload attachment

**Expected:**
- ✅ File upload works same as raw fields
- ✅ Can upload proof/supporting documents
- ✅ Attachments link to computed field's ESGData

---

## Success Criteria

✅ **Bug Fixed:** Files display in UI when selected
✅ **Upload works:** Files upload immediately after selection
✅ **Validation works:** Size (20MB) and type validation prevent invalid files
✅ **Remove works:** Users can remove uploaded files
✅ **Download works:** Users can download attachments from historical data
✅ **Delete works:** Users can delete attachments (entity-level permissions)
✅ **Data required:** Warning shows if user tries to upload before saving data
✅ **All field types:** Works for raw, computed, and dimensional fields
✅ **Historical data:** Attachments visible and downloadable in historical view
✅ **Dark mode:** File upload UI works in dark mode
✅ **All 10 test cases pass**

---

## Implementation Effort

**Estimated Time:**
- Frontend File Handler: 4-5 hours
- CSS Styling: 1-2 hours
- Backend API (copy/adapt): 2-3 hours
- Integration & Testing: 3-4 hours
- **Total: 10-14 hours**

**Complexity:** Medium
- Frontend state management (moderate)
- File upload logic (straightforward - reusing existing)
- Multi-tenant file structure (low complexity)
- Security already handled in legacy code

---

## Security Considerations

1. ✅ **File Type Validation:** Server-side and client-side (from config)
2. ✅ **File Size Limits:** 20MB per file (configurable)
3. ✅ **Secure Filenames:** `secure_filename()` + UUID prevents path traversal
4. ✅ **Multi-Tenant Isolation:** Files stored in company-specific directories
5. ✅ **Access Control:** Tenant middleware enforces data access
6. ✅ **Permissions:** Entity-level permissions (anyone with ESGData access)
7. ⚠️ **Virus Scanning:** (Future) Integrate with antivirus API
8. ⚠️ **Storage Quotas:** (Future) Implement per-company storage limits

---

## Deployment Notes

### File Structure Migration

**Current (Legacy):**
```
uploads/
  └── {entity_id}/
      └── {data_id}_{filename}
```

**New (V2):**
```
uploads/
  └── {company_id}/
      └── {entity_id}/
          └── {uuid}_{filename}
```

**No migration needed** - old and new can coexist:
- Legacy dashboard uses old structure
- V2 dashboard uses new structure
- Both work independently

---

## Future Enhancements (Out of Scope)

1. **Image Previews:** Show thumbnails for image files
2. **Inline PDF Viewer:** View PDFs without downloading (PDF.js)
3. **Batch Upload:** Upload entire folder
4. **Cloud Storage:** AWS S3 / Azure Blob integration
5. **Compression:** Auto-compress large files
6. **OCR:** Extract text from scanned documents
7. **Version Control:** Track file versions
8. **Virus Scanning:** Integrate ClamAV or cloud antivirus API

---

## Rollback Plan

1. **Quick Fix:** Disable file upload UI
   ```javascript
   document.getElementById('fileUploadArea').style.display = 'none';
   document.getElementById('fileList').style.display = 'none';
   ```

2. **Partial Rollback:** Keep display fix, disable upload API
   - Comment out upload endpoint
   - Show files but disable upload button

3. **Full Rollback:** Revert all changes
   - Remove new JS/CSS files
   - Revert dashboard.html changes
   - Database and uploaded files remain (safe - no data loss)

---

## Sign-off

**Prepared By:** Claude Code (AI Agent)
**Date:** 2025-11-12
**Bug Confirmed By:** Chrome DevTools Testing
**Review Status:** Ready for implementation
**Approved By:** [Pending]

---

## Notes

- This enhancement fixes a critical UX bug AND completes the file attachment feature
- Reuses existing infrastructure (database model, config, legacy API patterns)
- Multi-tenant file structure prevents file conflicts between companies
- Immediate upload provides instant feedback while requiring data to exist first
- Uniform experience across all field types (raw, computed, dimensional)
