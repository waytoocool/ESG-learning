/**
 * FileUploadHandler
 * Manages file upload UI, validation, and submission for ESG data attachments
 *
 * Key Features:
 * - Display selected files with details
 * - Immediate upload on selection
 * - Requires ESGData to exist before upload
 * - Remove uploaded files
 * - Validation (size, type)
 * - Multi-tenant safe
 *
 * Usage:
 *   const handler = new FileUploadHandler({
 *     uploadAreaId: 'fileUploadArea',
 *     fileInputId: 'fileInput',
 *     fileListId: 'fileList'
 *   });
 *
 *   // After saving data, enable uploads
 *   handler.setDataId(dataId);
 *
 *   // Load existing attachments when modal opens
 *   await handler.loadExistingAttachments(dataId);
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
            console.error('[FileUpload] Required elements not found');
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
        this.uploadArea.addEventListener('click', (e) => {
            if (!this.currentDataId) {
                e.preventDefault();
                e.stopPropagation();
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
        // Use Bootstrap alert or custom notification system
        if (window.showNotification) {
            window.showNotification(message, 'warning');
        } else {
            alert(message);
        }
    }

    showError(message) {
        console.error('[FileUpload]', message);
        if (window.showNotification) {
            window.showNotification(message, 'danger');
        } else {
            alert(message);
        }
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
