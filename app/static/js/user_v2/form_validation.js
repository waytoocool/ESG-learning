/**
 * Form Validation Handler
 * Manages form input enable/disable state based on date selection
 */

class FormValidationHandler {
    constructor() {
        this.tooltipMessage = 'Please select a reporting date first';
        this.formInputsEnabled = false;

        // Store globally for access by other modules
        window.formInputsEnabled = this.formInputsEnabled;
    }

    /**
     * Toggle form inputs based on date selection
     * @param {boolean} enable - True to enable inputs, false to disable
     */
    toggleFormInputs(enable) {
        const dataCollectionModal = document.getElementById('dataCollectionModal');
        if (!dataCollectionModal) return;

        // Store the current state globally so dimensional inputs can check it when they're dynamically created
        this.formInputsEnabled = enable;
        window.formInputsEnabled = enable;

        // Get all input elements that should be controlled
        const valueInput = document.getElementById('dataValue');
        const notesInput = document.getElementById('fieldNotes');
        const dimensionInputs = dataCollectionModal.querySelectorAll('#dimensionMatrixContainer input, #dimensionMatrixContainer textarea');
        const fileUploadArea = document.getElementById('fileUploadArea');
        const fileInput = document.getElementById('fileInput');
        const submitBtn = document.getElementById('submitDataBtn');

        if (enable) {
            this.enableInputs([valueInput, notesInput, fileInput, submitBtn], dimensionInputs, fileUploadArea);
        } else {
            this.disableInputs([valueInput, notesInput, fileInput, submitBtn], dimensionInputs, fileUploadArea);
        }

        console.log(`[Form Validation] Form inputs ${enable ? 'ENABLED' : 'DISABLED'}`);
    }

    /**
     * Enable form inputs
     * @param {Array} standardInputs - Array of standard input elements
     * @param {NodeList} dimensionInputs - Dimensional input elements
     * @param {HTMLElement} fileUploadArea - File upload area element
     */
    enableInputs(standardInputs, dimensionInputs, fileUploadArea) {
        // Enable standard inputs
        standardInputs.forEach(input => {
            if (input) {
                input.disabled = false;
                input.style.cursor = 'text';
                input.style.backgroundColor = '';
                input.removeAttribute('title');
            }
        });

        // Enable dimensional inputs
        dimensionInputs.forEach(input => {
            input.disabled = false;
            input.style.cursor = 'text';
            input.style.backgroundColor = '';
            input.removeAttribute('title');
        });

        // Enable file upload area
        if (fileUploadArea) {
            fileUploadArea.style.pointerEvents = 'auto';
            fileUploadArea.style.opacity = '1';
            fileUploadArea.removeAttribute('title');
        }
    }

    /**
     * Disable form inputs
     * @param {Array} standardInputs - Array of standard input elements
     * @param {NodeList} dimensionInputs - Dimensional input elements
     * @param {HTMLElement} fileUploadArea - File upload area element
     */
    disableInputs(standardInputs, dimensionInputs, fileUploadArea) {
        // Disable standard inputs
        standardInputs.forEach(input => {
            if (input) {
                input.disabled = true;
                input.style.cursor = 'not-allowed';
                input.style.backgroundColor = '#f3f4f6';
                input.setAttribute('title', this.tooltipMessage);
            }
        });

        // Disable dimensional inputs
        dimensionInputs.forEach(input => {
            input.disabled = true;
            input.style.cursor = 'not-allowed';
            input.style.backgroundColor = '#f3f4f6';
            input.setAttribute('title', this.tooltipMessage);
        });

        // Disable file upload area
        if (fileUploadArea) {
            fileUploadArea.style.pointerEvents = 'none';
            fileUploadArea.style.opacity = '0.5';
            fileUploadArea.setAttribute('title', this.tooltipMessage);
        }
    }

    /**
     * Check if form inputs are currently enabled
     * @returns {boolean} - True if enabled
     */
    isFormEnabled() {
        return this.formInputsEnabled;
    }
}

// Make available globally
window.FormValidationHandler = FormValidationHandler;

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    if (!window.formValidationHandler) {
        window.formValidationHandler = new FormValidationHandler();

        // Expose toggleFormInputs globally for backward compatibility
        window.toggleFormInputs = function(enable) {
            window.formValidationHandler.toggleFormInputs(enable);
        };
    }
});
