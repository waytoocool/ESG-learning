/**
 * Enhancement #4: Bulk Excel Upload Handler
 *
 * Orchestrates the multi-step bulk upload workflow:
 * 1. Template selection
 * 2. File upload
 * 3. Validation
 * 4. Attachments (optional)
 * 5. Submission
 */

class BulkUploadHandler {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 5;
        this.uploadId = null;
        this.selectedFilter = 'pending';
        this.uploadedFile = null;
        this.validationResult = null;
        this.attachments = {};

        // Session timeout management
        this.SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes in milliseconds
        this.sessionStartTime = null;
        this.warningShown = false;
        this.criticalWarningShown = false;
        this.countdownInterval = null;

        // Concurrent submission protection
        this.isSubmitting = false;

        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Open modal button
        const openBtn = document.getElementById('open-bulk-upload');
        if (openBtn) {
            openBtn.addEventListener('click', () => this.openModal());
        }

        // Close modal
        const closeBtn = document.querySelector('.bulk-upload-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeModal());
        }

        // Filter selection
        document.querySelectorAll('input[name="upload-filter"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.selectedFilter = e.target.value;
                this.updateFilterSelection();
            });
        });

        // File upload
        const fileInput = document.getElementById('bulk-file-input');
        const dropZone = document.getElementById('file-drop-zone');

        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }

        if (dropZone) {
            dropZone.addEventListener('click', () => fileInput?.click());
            dropZone.addEventListener('dragover', (e) => this.handleDragOver(e));
            dropZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            dropZone.addEventListener('drop', (e) => this.handleDrop(e));
        }

        // Navigation buttons
        document.getElementById('btn-next')?.addEventListener('click', () => this.nextStep());
        document.getElementById('btn-prev')?.addEventListener('click', () => this.prevStep());
        document.getElementById('btn-cancel')?.addEventListener('click', () => this.cancelUpload());
        document.getElementById('btn-submit')?.addEventListener('click', () => this.submitData());
    }

    openModal() {
        document.getElementById('bulk-upload-modal').classList.add('active');
        this.reset();
        this.goToStep(1);
    }

    closeModal() {
        if (this.uploadId && this.currentStep < this.totalSteps) {
            if (!confirm('Upload in progress. Are you sure you want to close?')) {
                return;
            }
            this.cancelUpload();
        }
        document.getElementById('bulk-upload-modal').classList.remove('active');
    }

    reset() {
        this.currentStep = 1;
        this.uploadId = null;
        this.selectedFilter = 'pending';
        this.uploadedFile = null;
        this.validationResult = null;
        this.attachments = {};

        // Reset session timer
        this.stopSessionTimer();
        this.sessionStartTime = null;
        this.warningShown = false;
        this.criticalWarningShown = false;

        // Reset UI
        document.querySelectorAll('.upload-step').forEach(step => {
            step.classList.remove('active');
        });
        document.querySelectorAll('.progress-step').forEach(step => {
            step.classList.remove('active', 'completed');
        });

        // Hide session timer display
        this.hideSessionTimer();
    }

    goToStep(step) {
        this.currentStep = step;

        // Update step visibility
        document.querySelectorAll('.upload-step').forEach((el, idx) => {
            el.classList.toggle('active', idx + 1 === step);
        });

        // Update progress indicators
        document.querySelectorAll('.progress-step').forEach((el, idx) => {
            const stepNum = idx + 1;
            el.classList.toggle('active', stepNum === step);
            el.classList.toggle('completed', stepNum < step);
        });

        // Update button states
        this.updateButtons();
    }

    updateButtons() {
        const prevBtn = document.getElementById('btn-prev');
        const nextBtn = document.getElementById('btn-next');
        const submitBtn = document.getElementById('btn-submit');

        if (prevBtn) prevBtn.style.display = this.currentStep > 1 ? 'inline-block' : 'none';
        if (nextBtn) {
            nextBtn.style.display = this.currentStep < this.totalSteps ? 'inline-block' : 'none';
            nextBtn.disabled = !this.canProceedFromCurrentStep();

            // Update button text based on current step
            switch (this.currentStep) {
                case 1: nextBtn.textContent = 'Download Template'; break;
                case 2: nextBtn.textContent = 'Upload & Validate'; break;
                case 3: nextBtn.textContent = 'Continue'; break;
                case 4: nextBtn.textContent = 'Review'; break;
                default: nextBtn.textContent = 'Next'; break;
            }
        }
        if (submitBtn) {
            submitBtn.style.display = this.currentStep === this.totalSteps ? 'inline-block' : 'none';
        }
    }

    canProceedFromCurrentStep() {
        switch (this.currentStep) {
            case 1: return true; // Template selection always ready
            case 2: return this.uploadedFile !== null; // File uploaded
            case 3: return this.validationResult?.valid === true; // Validation passed
            case 4: return true; // Attachments optional
            default: return false;
        }
    }

    async nextStep() {
        switch (this.currentStep) {
            case 1:
                const templateSuccess = await this.downloadTemplate();
                // Only advance to step 2 if template download succeeded
                if (templateSuccess) {
                    this.goToStep(2);
                }
                break;
            case 2:
                await this.uploadAndParse();
                break;
            case 3:
                this.goToStep(4); // Skip attachments for now, go to confirmation
                break;
            case 4:
                this.showConfirmation();
                this.goToStep(5);
                break;
            default:
                this.goToStep(this.currentStep + 1);
        }
    }

    prevStep() {
        if (this.currentStep > 1) {
            this.goToStep(this.currentStep - 1);
        }
    }

    // === Step 1: Template Download ===
    async downloadTemplate() {
        this.showLoading('Generating template...');

        try {
            const response = await fetch('/api/user/v2/bulk-upload/template', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filter: this.selectedFilter
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to generate template');
            }

            // Download file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Template_${this.selectedFilter}_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            this.hideLoading();
            this.showSuccess('Template downloaded successfully! Fill it out and upload in the next step.');

            return true; // Success

        } catch (error) {
            this.hideLoading();
            this.showError('Template Download Failed', error.message);
            return false; // Failure - stay on current step
        }
    }

    updateFilterSelection() {
        document.querySelectorAll('.filter-option').forEach(option => {
            const radio = option.querySelector('input[type="radio"]');
            option.classList.toggle('selected', radio?.checked);
        });
    }

    // === Step 2: File Upload ===
    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.add('drag-over');
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    processFile(file) {
        // Validate file type
        const validTypes = ['.xlsx', '.xls', '.csv'];
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();

        if (!validTypes.includes(fileExt)) {
            this.showError('Invalid File Type', `Please upload an Excel file (${validTypes.join(', ')})`);
            return;
        }

        // Validate file size (5MB)
        const maxSize = 5 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showError('File Too Large', `Maximum file size is 5MB. Your file is ${(file.size / 1024 / 1024).toFixed(2)}MB`);
            return;
        }

        this.uploadedFile = file;
        this.displayFileInfo(file);
        this.updateButtons();
    }

    displayFileInfo(file) {
        const fileInfo = document.getElementById('file-info');
        const fileName = document.getElementById('file-name');
        const fileSize = document.getElementById('file-size');

        if (fileName) fileName.textContent = file.name;
        if (fileSize) fileSize.textContent = this.formatFileSize(file.size);
        if (fileInfo) fileInfo.classList.add('visible');
    }

    async uploadAndParse() {
        if (!this.uploadedFile) return;

        this.showLoading('Uploading and parsing file...');

        try {
            const formData = new FormData();
            formData.append('file', this.uploadedFile);

            const response = await fetch('/api/user/v2/bulk-upload/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.errors?.join(', ') || 'Upload failed');
            }

            this.uploadId = result.upload_id;
            this.hideLoading();

            // Start session timeout timer
            this.startSessionTimer();

            // Proceed to validation
            await this.validateUpload();

        } catch (error) {
            this.hideLoading();
            this.showError('Upload Failed', error.message);
        }
    }

    // === Step 3: Validation ===
    async validateUpload() {
        this.showLoading('Validating data...');

        try {
            const response = await fetch('/api/user/v2/bulk-upload/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    upload_id: this.uploadId
                })
            });

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || 'Validation failed');
            }

            this.validationResult = result;
            this.hideLoading();
            this.displayValidationResults(result);
            this.goToStep(3);

        } catch (error) {
            this.hideLoading();
            this.showError('Validation Failed', error.message);
        }
    }

    displayValidationResults(result) {
        // Update summary stats
        document.getElementById('valid-count').textContent = result.valid_count || 0;
        document.getElementById('invalid-count').textContent = result.invalid_count || 0;
        document.getElementById('warning-count').textContent = result.warning_count || 0;
        document.getElementById('overwrite-count').textContent = result.overwrite_count || 0;

        // Display errors
        const errorSection = document.getElementById('error-section');
        const errorList = document.getElementById('error-list');
        if (result.invalid_count > 0) {
            errorSection.style.display = 'block';
            errorList.innerHTML = result.invalid_rows.map(row => `
                <div class="issue-item error">
                    <div class="issue-row">Row ${row.row_number}</div>
                    <div class="issue-field">${row.field_name}</div>
                    <div class="issue-message">${row.errors.join(', ')}</div>
                </div>
            `).join('');
        } else {
            errorSection.style.display = 'none';
        }

        // Display warnings
        const warningSection = document.getElementById('warning-section');
        const warningList = document.getElementById('warning-list');
        if (result.warning_count > 0) {
            warningSection.style.display = 'block';
            warningList.innerHTML = result.warning_rows.map(row => `
                <div class="issue-item warning">
                    <div class="issue-row">Row ${row.row_number}</div>
                    <div class="issue-field">${row.field_name}</div>
                    <div class="issue-message">${row.warnings.join(', ')}</div>
                </div>
            `).join('');
        } else {
            warningSection.style.display = 'none';
        }

        // Display overwrites
        const overwriteWarning = document.getElementById('overwrite-warning');
        if (result.overwrite_count > 0) {
            overwriteWarning.style.display = 'block';
        } else {
            overwriteWarning.style.display = 'none';
        }

        this.updateButtons();
    }

    // === Step 5: Confirmation & Submission ===
    showConfirmation() {
        const result = this.validationResult;
        document.getElementById('confirm-new-count').textContent = result.valid_count - result.overwrite_count;
        document.getElementById('confirm-update-count').textContent = result.overwrite_count;
        document.getElementById('confirm-total-count').textContent = result.valid_count;
    }

    async submitData() {
        // Concurrent submission protection
        if (this.isSubmitting) {
            console.log('Submission already in progress');
            return;
        }

        this.isSubmitting = true;
        const submitBtn = document.getElementById('btn-submit');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';
        }

        this.showLoading('Submitting data...');

        try {
            const formData = new FormData();
            formData.append('upload_id', this.uploadId);

            // Add attachments if any
            Object.keys(this.attachments).forEach(key => {
                formData.append(key, this.attachments[key]);
            });

            const response = await fetch('/api/user/v2/bulk-upload/submit', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || 'Submission failed');
            }

            this.hideLoading();
            this.stopSessionTimer(); // Clear timer on successful submission
            this.showSuccessMessage(result);

        } catch (error) {
            this.hideLoading();
            this.showError('Submission Failed', error.message);

            // Re-enable button on error
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Data';
            }
        } finally {
            this.isSubmitting = false;
        }
    }

    showSuccessMessage(result) {
        const successStep = document.getElementById('success-step');
        if (successStep) {
            successStep.innerHTML = `
                <div class="success-message">
                    <div class="success-icon">✓</div>
                    <h3>Upload Successful!</h3>
                    <p>Your data has been submitted successfully.</p>
                    <div class="success-stats">
                        <div class="validation-stat success">
                            <div class="validation-stat-label">New Entries</div>
                            <div class="validation-stat-value">${result.new_entries}</div>
                        </div>
                        <div class="validation-stat warning">
                            <div class="validation-stat-label">Updated Entries</div>
                            <div class="validation-stat-value">${result.updated_entries}</div>
                        </div>
                        <div class="validation-stat">
                            <div class="validation-stat-label">Total Submitted</div>
                            <div class="validation-stat-value">${result.total}</div>
                        </div>
                    </div>
                    <button class="btn-bulk btn-bulk-primary" onclick="location.reload()" style="margin-top: 32px;">
                        Return to Dashboard
                    </button>
                </div>
            `;
        }

        // Hide navigation buttons
        document.getElementById('btn-prev').style.display = 'none';
        document.getElementById('btn-submit').style.display = 'none';
    }

    async cancelUpload() {
        if (this.uploadId) {
            try {
                await fetch('/api/user/v2/bulk-upload/cancel', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        upload_id: this.uploadId
                    })
                });
            } catch (error) {
                console.error('Failed to cancel upload:', error);
            }
        }
        this.stopSessionTimer();
        this.closeModal();
    }

    // === Session Timeout Management ===
    startSessionTimer() {
        this.sessionStartTime = Date.now();
        this.warningShown = false;
        this.criticalWarningShown = false;

        // Show countdown display
        this.showSessionTimer();

        // Warning at 25 minutes (5 minutes remaining)
        setTimeout(() => {
            if (this.sessionStartTime && !this.warningShown) {
                this.showSessionWarning('⚠️ Your session will expire in 5 minutes. Please complete submission soon.', 'warning');
                this.warningShown = true;
            }
        }, 25 * 60 * 1000);

        // Critical warning at 29 minutes (1 minute remaining)
        setTimeout(() => {
            if (this.sessionStartTime && !this.criticalWarningShown) {
                this.showSessionWarning('🚨 SESSION EXPIRING IN 1 MINUTE! Complete submission now or re-upload.', 'critical');
                this.criticalWarningShown = true;
            }
        }, 29 * 60 * 1000);

        // Start countdown display (update every minute)
        this.startCountdown();
    }

    stopSessionTimer() {
        this.sessionStartTime = null;
        this.warningShown = false;
        this.criticalWarningShown = false;
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }
        this.hideSessionTimer();
    }

    startCountdown() {
        // Clear any existing interval
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }

        // Update countdown every 30 seconds
        this.countdownInterval = setInterval(() => {
            if (!this.sessionStartTime) {
                clearInterval(this.countdownInterval);
                return;
            }

            const elapsed = Date.now() - this.sessionStartTime;
            const remaining = this.SESSION_TIMEOUT - elapsed;

            if (remaining <= 0) {
                clearInterval(this.countdownInterval);
                this.showSessionExpired();
                return;
            }

            this.updateCountdownDisplay(remaining);
        }, 30000); // Update every 30 seconds

        // Initial update
        this.updateCountdownDisplay(this.SESSION_TIMEOUT);
    }

    updateCountdownDisplay(remainingMs) {
        const minutes = Math.floor(remainingMs / 60000);
        const seconds = Math.floor((remainingMs % 60000) / 1000);
        const timerElement = document.getElementById('session-timer-countdown');

        if (timerElement) {
            timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;

            // Change color based on time remaining
            if (minutes < 1) {
                timerElement.style.color = '#dc2626'; // Red for critical
            } else if (minutes < 5) {
                timerElement.style.color = '#f59e0b'; // Orange for warning
            } else {
                timerElement.style.color = '#10b981'; // Green for normal
            }
        }
    }

    showSessionTimer() {
        const timerContainer = document.getElementById('session-timer-container');
        if (timerContainer) {
            timerContainer.style.display = 'block';
        } else {
            // Create timer display if it doesn't exist
            const modal = document.getElementById('bulk-upload-modal');
            if (modal) {
                const timerDiv = document.createElement('div');
                timerDiv.id = 'session-timer-container';
                timerDiv.style.cssText = 'position: absolute; top: 16px; right: 16px; background: #f3f4f6; padding: 8px 16px; border-radius: 6px; font-size: 14px; font-weight: 500; box-shadow: 0 1px 3px rgba(0,0,0,0.1);';
                timerDiv.innerHTML = `
                    <span style="color: #6b7280;">Session expires in:</span>
                    <span id="session-timer-countdown" style="margin-left: 8px; color: #10b981; font-weight: 600;">30:00</span>
                `;
                modal.querySelector('.bulk-upload-content')?.prepend(timerDiv);
            }
        }
    }

    hideSessionTimer() {
        const timerContainer = document.getElementById('session-timer-container');
        if (timerContainer) {
            timerContainer.style.display = 'none';
        }
    }

    showSessionWarning(message, severity) {
        // Create warning banner
        const warningDiv = document.createElement('div');
        warningDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: ${severity === 'critical' ? '#dc2626' : '#f59e0b'};
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
            animation: slideDown 0.3s ease-out;
        `;
        warningDiv.textContent = message;
        document.body.appendChild(warningDiv);

        // Auto-remove after 8 seconds
        setTimeout(() => {
            warningDiv.remove();
        }, 8000);
    }

    showSessionExpired() {
        this.stopSessionTimer();
        this.showError(
            'Session Expired',
            'Your upload session has expired after 30 minutes. Please re-upload your file to continue.'
        );
        this.reset();
        this.goToStep(1);
    }

    // === Utility Functions ===
    showLoading(message) {
        const overlay = document.getElementById('loading-overlay');
        const text = document.getElementById('loading-text');
        if (overlay) overlay.style.display = 'flex';
        if (text) text.textContent = message;
    }

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';
    }

    showError(title, message) {
        alert(`${title}\n\n${message}`);
    }

    showSuccess(message) {
        // Could be replaced with a toast notification
        console.log('Success:', message);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('bulk-upload-modal')) {
        window.bulkUploadHandler = new BulkUploadHandler();
    }
});
