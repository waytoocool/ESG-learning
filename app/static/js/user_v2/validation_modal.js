/**
 * Validation Modal Component
 * Displays validation warnings before data submission
 * Allows users to add explanation notes for variance
 */

class ValidationModal {
    constructor() {
        this.overlay = null;
        this.modal = null;
        this.notesTextarea = null;
        this.submitCallback = null;
        this.cancelCallback = null;
        this.validationResult = null;
        this.init();
    }

    /**
     * Initialize modal HTML structure
     */
    init() {
        // Create modal overlay if it doesn't exist
        if (!document.getElementById('validationModalOverlay')) {
            const overlayHTML = `
                <div id="validationModalOverlay" class="validation-modal-overlay">
                    <div class="validation-modal" role="dialog" aria-labelledby="validationModalTitle" aria-modal="true">
                        <!-- Header -->
                        <div class="validation-modal-header" id="validationModalHeader">
                            <h2 class="validation-modal-title" id="validationModalTitle">
                                <span class="validation-modal-icon">⚠️</span>
                                <span>Validation Warning</span>
                            </h2>
                            <button class="validation-modal-close" id="validationModalClose" aria-label="Close">
                                <span>&times;</span>
                            </button>
                        </div>

                        <!-- Body -->
                        <div class="validation-modal-body" id="validationModalBody">
                            <!-- Dynamic content will be inserted here -->
                        </div>

                        <!-- Footer -->
                        <div class="validation-modal-footer">
                            <button class="validation-modal-btn validation-modal-btn-cancel" id="validationModalBtnCancel">
                                Cancel
                            </button>
                            <button class="validation-modal-btn validation-modal-btn-submit" id="validationModalBtnSubmit">
                                Continue & Submit
                            </button>
                        </div>
                    </div>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', overlayHTML);
        }

        // Get references
        this.overlay = document.getElementById('validationModalOverlay');
        this.modal = this.overlay.querySelector('.validation-modal');
        this.closeBtn = document.getElementById('validationModalClose');
        this.cancelBtn = document.getElementById('validationModalBtnCancel');
        this.submitBtn = document.getElementById('validationModalBtnSubmit');

        // Attach event listeners
        this.attachEventListeners();

        console.log('[ValidationModal] Initialized');
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Close button
        this.closeBtn.addEventListener('click', () => this.hide());

        // Cancel button
        this.cancelBtn.addEventListener('click', () => this.handleCancel());

        // Submit button
        this.submitBtn.addEventListener('click', () => this.handleSubmit());

        // Close on overlay click (outside modal)
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.hide();
            }
        });

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.overlay.classList.contains('active')) {
                this.hide();
            }
        });
    }

    /**
     * Show validation modal with results
     * @param {Object} validationResult - Validation result from API
     * @param {Function} onSubmit - Callback when user confirms submission
     * @param {Function} onCancel - Callback when user cancels
     */
    show(validationResult, onSubmit, onCancel) {
        this.validationResult = validationResult;
        this.submitCallback = onSubmit;
        this.cancelCallback = onCancel;

        // Render modal content
        this.renderContent();

        // Show overlay
        this.overlay.classList.add('active');
        document.body.style.overflow = 'hidden';

        // Focus on notes textarea if present
        setTimeout(() => {
            if (this.notesTextarea) {
                this.notesTextarea.focus();
            }
        }, 300);

        console.log('[ValidationModal] Shown with', validationResult.flags.length, 'flags');
    }

    /**
     * Hide validation modal
     */
    hide() {
        this.overlay.classList.remove('active');
        document.body.style.overflow = '';
        this.validationResult = null;
        this.submitCallback = null;
        this.cancelCallback = null;

        console.log('[ValidationModal] Hidden');
    }

    /**
     * Render modal content based on validation result
     */
    renderContent() {
        const { passed, risk_score, flags } = this.validationResult;

        // Determine severity
        const severity = this.getSeverity(flags);
        const severityLabel = severity === 'error' ? 'Error' : severity === 'warning' ? 'Warning' : 'Info';
        const severityIcon = severity === 'error' ? '❌' : severity === 'warning' ? '⚠️' : 'ℹ️';

        // Update header
        const header = document.getElementById('validationModalHeader');
        header.className = `validation-modal-header ${severity}`;

        const title = document.getElementById('validationModalTitle');
        title.innerHTML = `
            <span class="validation-modal-icon">${severityIcon}</span>
            <span>Validation ${severityLabel}</span>
        `;

        // Build body content
        const bodyHTML = `
            <div class="validation-modal-intro">
                ${this.getIntroMessage(flags)}
            </div>

            ${risk_score > 0 ? this.renderRiskScore(risk_score) : ''}

            <div class="validation-flags-list">
                ${flags.map(flag => this.renderFlag(flag)).join('')}
            </div>

            ${this.hasWarningsOrErrors(flags) ? this.renderNotesSection() : ''}
        `;

        document.getElementById('validationModalBody').innerHTML = bodyHTML;

        // Get reference to textarea
        this.notesTextarea = document.getElementById('validationNotesTextarea');

        // Attach textarea event listeners
        if (this.notesTextarea) {
            this.notesTextarea.addEventListener('input', () => this.handleNotesInput());
        }
    }

    /**
     * Get intro message based on flags
     */
    getIntroMessage(flags) {
        const hasErrors = flags.some(f => f.severity === 'error');
        const hasWarnings = flags.some(f => f.severity === 'warning');

        if (hasErrors) {
            return 'Critical issues were detected with your submission. Please review the errors below and make necessary corrections.';
        } else if (hasWarnings) {
            return 'Your data has been validated and some warnings were detected. Please review them below and provide an explanation if needed.';
        } else {
            return 'Your data has been validated successfully. Some informational notes are shown below.';
        }
    }

    /**
     * Render risk score badge
     */
    renderRiskScore(score) {
        const level = score >= 50 ? 'high' : score >= 20 ? 'medium' : 'low';
        const label = level === 'high' ? 'High Risk' : level === 'medium' ? 'Medium Risk' : 'Low Risk';

        return `
            <div class="validation-risk-score ${level}">
                <span>Risk Score: <strong>${score}/100</strong></span>
                <span>•</span>
                <span>${label}</span>
            </div>
        `;
    }

    /**
     * Render individual validation flag
     */
    renderFlag(flag) {
        const { type, severity, message, details } = flag;
        const icon = severity === 'error' ? '❌' : severity === 'warning' ? '⚠️' : 'ℹ️';

        return `
            <div class="validation-flag ${severity}">
                <div class="validation-flag-header">
                    <span class="validation-flag-icon">${icon}</span>
                    <div class="validation-flag-message">${message}</div>
                </div>
                ${details && Object.keys(details).length > 0 ? this.renderFlagDetails(details) : ''}
            </div>
        `;
    }

    /**
     * Render flag details
     */
    renderFlagDetails(details) {
        const detailsHTML = Object.entries(details)
            .filter(([key, value]) => value !== null && value !== undefined)
            .map(([key, value]) => {
                const label = this.formatDetailLabel(key);
                const formattedValue = this.formatDetailValue(key, value);
                return `
                    <div class="validation-flag-details-item">
                        <span class="validation-flag-details-label">${label}:</span>
                        <span class="validation-flag-details-value">${formattedValue}</span>
                    </div>
                `;
            })
            .join('');

        return `<div class="validation-flag-details">${detailsHTML}</div>`;
    }

    /**
     * Format detail label for display
     */
    formatDetailLabel(key) {
        return key.replace(/_/g, ' ')
            .replace(/\b\w/g, char => char.toUpperCase());
    }

    /**
     * Format detail value for display
     */
    formatDetailValue(key, value) {
        if (key.includes('pct') || key.includes('variance')) {
            return `${value.toFixed(1)}%`;
        } else if (typeof value === 'number') {
            return value.toLocaleString();
        } else {
            return value;
        }
    }

    /**
     * Render notes section
     */
    renderNotesSection() {
        return `
            <div class="validation-notes-section">
                <label class="validation-notes-label" for="validationNotesTextarea">
                    Explanation for Variance
                    <span class="validation-notes-required">*</span>
                </label>
                <p class="validation-notes-help">
                    Please explain why the data differs significantly from historical values.
                    This helps reviewers understand the context of your submission.
                </p>
                <textarea
                    id="validationNotesTextarea"
                    class="validation-notes-textarea"
                    placeholder="Example: The increase is due to expansion of our operations in Q4, adding two new facilities..."
                    maxlength="2000"
                ></textarea>
                <span class="validation-notes-char-count" id="validationNotesCharCount">0 / 2000</span>
                <div class="validation-notes-error" id="validationNotesError">
                    Please provide an explanation before submitting.
                </div>
            </div>
        `;
    }

    /**
     * Handle notes textarea input
     */
    handleNotesInput() {
        const value = this.notesTextarea.value;
        const length = value.length;
        const maxLength = 2000;

        // Update character count
        const charCount = document.getElementById('validationNotesCharCount');
        if (charCount) {
            charCount.textContent = `${length} / ${maxLength}`;

            // Update color based on length
            if (length > maxLength * 0.9) {
                charCount.className = 'validation-notes-char-count error';
            } else if (length > maxLength * 0.7) {
                charCount.className = 'validation-notes-char-count warning';
            } else {
                charCount.className = 'validation-notes-char-count';
            }
        }

        // Clear error if notes are provided
        if (length > 0) {
            this.notesTextarea.classList.remove('error');
            const errorElement = document.getElementById('validationNotesError');
            if (errorElement) {
                errorElement.classList.remove('active');
            }
        }
    }

    /**
     * Handle cancel button click
     */
    handleCancel() {
        if (this.cancelCallback) {
            this.cancelCallback();
        }
        this.hide();
    }

    /**
     * Handle submit button click
     */
    async handleSubmit() {
        // Validate notes if warnings/errors are present
        if (this.hasWarningsOrErrors(this.validationResult.flags)) {
            const notes = this.notesTextarea ? this.notesTextarea.value.trim() : '';

            if (!notes || notes.length < 10) {
                // Show error
                if (this.notesTextarea) {
                    this.notesTextarea.classList.add('error');
                }
                const errorElement = document.getElementById('validationNotesError');
                if (errorElement) {
                    errorElement.textContent = notes.length === 0
                        ? 'Please provide an explanation before submitting.'
                        : 'Please provide a more detailed explanation (at least 10 characters).';
                    errorElement.classList.add('active');
                }
                return;
            }
        }

        // Disable submit button
        this.submitBtn.disabled = true;
        this.submitBtn.innerHTML = `
            <span class="validation-modal-btn-spinner"></span>
            Submitting...
        `;

        // Get notes
        const notes = this.notesTextarea ? this.notesTextarea.value.trim() : null;

        // Call submit callback with notes
        if (this.submitCallback) {
            try {
                await this.submitCallback(notes);
                this.hide();
            } catch (error) {
                console.error('[ValidationModal] Submit error:', error);
                alert('Failed to submit data: ' + error.message);

                // Re-enable submit button
                this.submitBtn.disabled = false;
                this.submitBtn.innerHTML = 'Continue & Submit';
            }
        }
    }

    /**
     * Get severity level from flags
     */
    getSeverity(flags) {
        if (flags.some(f => f.severity === 'error')) return 'error';
        if (flags.some(f => f.severity === 'warning')) return 'warning';
        return 'info';
    }

    /**
     * Check if flags contain warnings or errors
     */
    hasWarningsOrErrors(flags) {
        return flags.some(f => f.severity === 'error' || f.severity === 'warning');
    }
}

// Make available globally
window.ValidationModal = ValidationModal;

// Auto-initialize on DOM ready
if (!window.validationModal) {
    document.addEventListener('DOMContentLoaded', () => {
        window.validationModal = new ValidationModal();
        console.log('[ValidationModal] Auto-initialized');
    });
}
