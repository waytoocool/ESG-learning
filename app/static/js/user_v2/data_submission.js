/**
 * Data Submission Handler
 * Handles data submission logic for both simple and dimensional data
 */

class DataSubmissionHandler {
    constructor() {
        this.submitBtn = null;
        this.init();
    }

    init() {
        // Initialize handlers - check if DOM is already loaded
        const initializeHandlers = () => {
            this.initializeDimensionalHandler();
            this.initializeComputationContext();
            this.attachSubmitHandler();
            console.log('[DataSubmission] All handlers initialized');
        };

        // Check if DOM is already loaded
        if (document.readyState === 'loading') {
            // DOM is still loading, wait for it
            document.addEventListener('DOMContentLoaded', initializeHandlers);
            console.log('[DataSubmission] Waiting for DOM to load');
        } else {
            // DOM is already loaded, initialize immediately
            console.log('[DataSubmission] DOM already loaded, initializing immediately');
            initializeHandlers();
        }
    }

    /**
     * Initialize dimensional data handler
     */
    initializeDimensionalHandler() {
        const dimensionContainer = document.getElementById('dimensionMatrixContainer');
        if (dimensionContainer && typeof DimensionalDataHandler !== 'undefined') {
            window.dimensionalDataHandler = new DimensionalDataHandler(dimensionContainer);
            console.log('[DataSubmission] Dimensional data handler initialized');
        }

        // Save original entry-tab HTML for restoration
        const entryTab = document.getElementById('entry-tab');
        if (entryTab && !window.originalEntryTabHTML && entryTab.innerHTML.trim().length > 0) {
            window.originalEntryTabHTML = entryTab.innerHTML;
            console.log('[DataSubmission] Original entry-tab HTML saved');
        }
    }

    /**
     * Initialize computation context handlers
     */
    initializeComputationContext() {
        document.querySelectorAll('.show-computation-context').forEach(button => {
            button.addEventListener('click', function() {
                const fieldId = this.dataset.fieldId;
                const entityId = window.currentEntityId || null;
                const reportingDate = document.getElementById('selectedDate')?.value || '';

                if (window.showComputationContext) {
                    window.showComputationContext(fieldId, entityId, reportingDate);
                } else {
                    console.error('[DataSubmission] Computation context handler not loaded');
                }
            });
        });
    }

    /**
     * Attach submit button event handler
     */
    attachSubmitHandler() {
        this.submitBtn = document.getElementById('submitDataBtn');
        if (this.submitBtn) {
            console.log('[DataSubmission] Found submit button:', this.submitBtn.id);

            this.submitBtn.addEventListener('click', async (event) => {
                console.log('[DataSubmission] ✅ Button clicked! Starting validation flow...');
                await this.handleSubmit(event);
            });

            console.log('[DataSubmission] ✅ Click listener attached successfully');
        } else {
            console.error('[DataSubmission] ❌ Submit button not found! Element #submitDataBtn does not exist');
        }
    }

    /**
     * Handle form submission
     * @param {Event} event - Click event
     */
    async handleSubmit(event) {
        try {
            const matrixContainer = document.getElementById('dimensionMatrixContainer');
            const reportingDate = document.getElementById('reportingDate')?.value;
            const fieldId = window.currentFieldId;
            const entityId = window.currentEntityId || null;

            // Validate inputs
            if (!reportingDate) {
                alert('Please select a reporting date first.');
                return;
            }

            if (!fieldId) {
                alert('Error: Field information not available.');
                return;
            }

            // Disable button while validating
            this.setSubmitButtonState(true, 'Validating...');

            // Run validation before submission
            const isDimensional = matrixContainer && matrixContainer.style.display !== 'none' &&
                window.dimensionalDataHandler && window.dimensionalDataHandler.currentMatrix;

            const shouldProceed = await this.runValidation(fieldId, entityId, reportingDate, isDimensional);

            if (!shouldProceed) {
                // User cancelled or validation failed
                this.setSubmitButtonState(false, 'Save Data');
                return;
            }

            // Proceed with submission
            this.setSubmitButtonState(true, 'Saving...');

            // Check if this is dimensional or simple data
            if (isDimensional) {
                await this.submitDimensionalData(fieldId, entityId, reportingDate);
            } else {
                await this.submitSimpleData(fieldId, entityId, reportingDate);
            }

            // Close modal and reload dashboard
            this.closeModalAndReload();

        } catch (error) {
            console.error('[DataSubmission] Error submitting data:', error);
            alert('Failed to save data: ' + error.message);
        } finally {
            // Re-enable button
            this.setSubmitButtonState(false, 'Save Data');
        }
    }

    /**
     * Run validation before submission
     * @param {string} fieldId - Field ID
     * @param {number} entityId - Entity ID
     * @param {string} reportingDate - Reporting date
     * @param {boolean} isDimensional - Whether this is dimensional data
     * @returns {Promise<boolean>} - Whether to proceed with submission
     */
    async runValidation(fieldId, entityId, reportingDate, isDimensional) {
        try {
            // Get value to validate
            let value;
            if (isDimensional) {
                // For dimensional data, skip validation for now
                // TODO: Implement dimensional data validation
                console.log('[DataSubmission] Skipping validation for dimensional data');
                return true;
            } else {
                value = document.getElementById('dataValue')?.value;
                if (!value || value.trim() === '') {
                    // No value entered, skip validation
                    return true;
                }
            }

            // Check if attachments are present
            const hasAttachments = this.checkAttachments();

            // Call validation API
            console.log('[DataSubmission] Calling validation API');
            const response = await fetch('/api/user/validate-submission', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    field_id: fieldId,
                    entity_id: entityId,
                    value: parseFloat(value),
                    reporting_date: reportingDate,
                    assignment_id: null, // Will be resolved by backend
                    dimension_values: null,
                    has_attachments: hasAttachments
                })
            });

            // SESSION FIX: Check for session expiration before parsing JSON
            if (window.handleSessionExpiration) {
                await window.handleSessionExpiration(response);
            }

            if (!response.ok) {
                console.error('[DataSubmission] Validation API failed:', response.status);
                // Proceed with submission even if validation fails
                return true;
            }

            const result = await response.json();

            if (!result.success) {
                console.error('[DataSubmission] Validation failed:', result.error);
                // Proceed with submission even if validation fails
                return true;
            }

            const validation = result.validation;
            console.log('[DataSubmission] Validation result:', validation);

            // If passed with no warnings/errors, proceed immediately
            if (validation.passed && validation.flags.length === 0) {
                return true;
            }

            // If there are only info flags, proceed immediately
            const hasWarningsOrErrors = validation.flags.some(
                f => f.severity === 'error' || f.severity === 'warning'
            );

            if (!hasWarningsOrErrors) {
                console.log('[DataSubmission] Only info flags, proceeding');
                return true;
            }

            // Show validation modal and wait for user decision
            return await this.showValidationModal(validation);

        } catch (error) {
            console.error('[DataSubmission] Validation error:', error);
            // Proceed with submission even if validation fails
            return true;
        }
    }

    /**
     * Show validation modal and wait for user decision
     * @param {Object} validation - Validation result
     * @returns {Promise<boolean>} - Whether user confirmed submission
     */
    async showValidationModal(validation) {
        return new Promise((resolve) => {
            if (!window.validationModal) {
                console.error('[DataSubmission] ValidationModal not available');
                resolve(true); // Proceed anyway
                return;
            }

            // Show modal with callbacks
            window.validationModal.show(
                validation,
                async (notes) => {
                    // User confirmed - store notes for submission
                    this.validationNotes = notes;
                    resolve(true);
                },
                () => {
                    // User cancelled
                    resolve(false);
                }
            );
        });
    }

    /**
     * Check if file attachments are present
     * @returns {boolean} - Whether attachments are present
     */
    checkAttachments() {
        // Check if file upload handler exists and has files
        if (window.fileUploadHandler && window.fileUploadHandler.getUploadedFiles) {
            const files = window.fileUploadHandler.getUploadedFiles();
            return files && files.length > 0;
        }
        return false;
    }

    /**
     * Submit dimensional data
     * @param {string} fieldId - Field ID
     * @param {number} entityId - Entity ID
     * @param {string} reportingDate - Reporting date
     */
    async submitDimensionalData(fieldId, entityId, reportingDate) {
        console.log('[DataSubmission] Submitting dimensional data');

        const result = await window.dimensionalDataHandler.submitDimensionalData();

        // Enable file uploads after dimensional data save
        if (result && result.data_id && window.fileUploadHandler) {
            window.fileUploadHandler.setDataId(result.data_id);
        }

        return result;
    }

    /**
     * Submit simple (non-dimensional) data
     * @param {string} fieldId - Field ID
     * @param {number} entityId - Entity ID
     * @param {string} reportingDate - Reporting date
     */
    async submitSimpleData(fieldId, entityId, reportingDate) {
        console.log('[DataSubmission] Submitting simple data');

        const dataValue = document.getElementById('dataValue')?.value;
        let notesValue = document.getElementById('fieldNotes')?.value || '';

        // Append validation notes if present
        if (this.validationNotes) {
            const validationSection = `\n\n--- Validation Explanation ---\n${this.validationNotes}`;
            notesValue = notesValue ? notesValue + validationSection : this.validationNotes;
            console.log('[DataSubmission] Including validation notes');
        }

        const response = await fetch('/user/v2/api/submit-simple-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                field_id: fieldId,
                entity_id: entityId,
                reporting_date: reportingDate,
                raw_value: dataValue,
                notes: notesValue || null
            })
        });

        if (!response.ok) {
            throw new Error('Failed to submit data');
        }

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'Failed to submit data');
        }

        console.log('[DataSubmission] Simple data saved successfully:', result);

        // Clear validation notes after submission
        this.validationNotes = null;

        // Enable file uploads after first save
        if (result.data_id && window.fileUploadHandler) {
            window.fileUploadHandler.setDataId(result.data_id);
        }

        return result;
    }

    /**
     * Set submit button state
     * @param {boolean} disabled - Whether button should be disabled
     * @param {string} text - Button text
     */
    setSubmitButtonState(disabled, text) {
        if (!this.submitBtn) return;

        this.submitBtn.disabled = disabled;
        if (disabled) {
            this.submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>' + text;
        } else {
            this.submitBtn.innerHTML = text;
        }
    }

    /**
     * Close modal and reload dashboard
     */
    closeModalAndReload() {
        const modalElement = document.getElementById('dataCollectionModal');
        if (modalElement) {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.hide();
            }
        }

        // Reload dashboard data
        if (window.loadDashboardData) {
            window.loadDashboardData();
        } else {
            // Fallback: reload page
            window.location.reload();
        }
    }
}

// Make available globally
window.DataSubmissionHandler = DataSubmissionHandler;

// Auto-initialize with DOM ready check
if (!window.dataSubmissionHandler) {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.dataSubmissionHandler = new DataSubmissionHandler();
            console.log('[DataSubmission] Handler created after DOM loaded');
        });
    } else {
        window.dataSubmissionHandler = new DataSubmissionHandler();
        console.log('[DataSubmission] Handler created immediately (DOM already loaded)');
    }
}

// Debug verification - confirms attachment status after initialization
setTimeout(() => {
    const handler = window.dataSubmissionHandler;
    const btn = document.getElementById('submitDataBtn');
    if (handler && btn) {
        console.log('[DataSubmission] 🔍 Verification:', {
            handlerExists: true,
            buttonExists: true,
            handlerHasButton: handler.submitBtn === btn,
            buttonId: btn.id
        });
    } else {
        console.warn('[DataSubmission] ⚠️ Verification failed:', {
            handlerExists: !!handler,
            buttonExists: !!btn
        });
    }
}, 1000);
