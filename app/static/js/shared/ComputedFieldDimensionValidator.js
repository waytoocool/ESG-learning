/**
 * Computed Field Dimension Validator
 * Validates dimension consistency between computed fields and their dependencies
 *
 * Business Rule: When assigning dimensions to a computed field, all dependencies
 * (raw fields) MUST have AT LEAST the same dimensions. Dependencies can have MORE
 * dimensions but CANNOT have FEWER.
 *
 * Part of Phase 1: Shared Dimension Component
 * Feature: Dimension Configuration in Assign Data Points
 */

window.ComputedFieldDimensionValidator = (function() {
    'use strict';

    /**
     * Validate before assigning dimensions to a computed field
     * @param {string} fieldId - Computed field ID
     * @param {Array<string>} dimensionIds - Dimension IDs to assign
     * @returns {Promise<Object>} Validation result
     */
    async function validateBeforeAssignment(fieldId, dimensionIds) {
        try {
            const response = await fetch(`/admin/fields/${fieldId}/dimensions/validate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: 'assign',
                    dimension_ids: dimensionIds
                })
            });

            if (!response.ok) {
                throw new Error('Validation request failed');
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('[DimensionValidator] Assignment validation error:', error);
            return {
                valid: false,
                error: 'Failed to validate dimension assignment'
            };
        }
    }

    /**
     * Validate before removing a dimension from a raw field
     * @param {string} fieldId - Raw field ID
     * @param {string} dimensionId - Dimension ID to remove
     * @returns {Promise<Object>} Validation result
     */
    async function validateBeforeRemoval(fieldId, dimensionId) {
        try {
            const response = await fetch(`/admin/fields/${fieldId}/dimensions/validate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: 'remove',
                    dimension_id: dimensionId
                })
            });

            if (!response.ok) {
                throw new Error('Validation request failed');
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('[DimensionValidator] Removal validation error:', error);
            return {
                valid: false,
                error: 'Failed to validate dimension removal'
            };
        }
    }

    /**
     * Format validation errors for user display
     * @param {Object} validationResult - Result from validation
     * @returns {Object|null} Formatted error object
     */
    function formatValidationErrors(validationResult) {
        if (validationResult.valid) {
            return null;
        }

        // Format assignment errors
        if (validationResult.errors && validationResult.errors.length > 0) {
            const details = validationResult.errors.map(err => {
                const missingDimNames = err.missing_dimension_names ||
                    err.missing_dimensions?.map(d => d.name || d) || [];
                const currentDimNames = err.current_dimension_names ||
                    err.current_dimensions?.map(d => d.name || d) || [];

                return {
                    fieldName: err.field_name,
                    fieldId: err.field_id,
                    missing: missingDimNames,
                    current: currentDimNames
                };
            });

            return {
                type: 'assignment',
                title: 'Cannot assign dimensions',
                message: 'The following dependencies are missing required dimensions:',
                details: details,
                htmlMessage: formatAssignmentErrorHTML(details)
            };
        }

        // Format removal errors
        if (validationResult.conflicts && validationResult.conflicts.length > 0) {
            const details = validationResult.conflicts.map(conflict => {
                const requiredDimNames = conflict.required_dimension_names ||
                    conflict.required_dimensions?.map(d => d.name || d) || [];

                return {
                    fieldName: conflict.field_name,
                    fieldId: conflict.field_id,
                    required: requiredDimNames
                };
            });

            return {
                type: 'removal',
                title: 'Cannot remove dimension',
                message: 'This dimension is required by the following computed fields:',
                details: details,
                htmlMessage: formatRemovalErrorHTML(details)
            };
        }

        // Generic error
        return {
            type: 'generic',
            title: 'Validation Error',
            message: validationResult.error || validationResult.message || 'An error occurred during validation',
            details: [],
            htmlMessage: `<p class="text-danger">${validationResult.error || validationResult.message || 'An error occurred during validation'}</p>`
        };
    }

    /**
     * Format assignment error as HTML
     * @param {Array} details - Error details
     * @returns {string} HTML string
     */
    function formatAssignmentErrorHTML(details) {
        let html = '<div class="validation-error-details">';
        html += '<p class="mb-3"><strong>The following dependencies are missing required dimensions:</strong></p>';
        html += '<ul class="list-unstyled">';

        details.forEach(err => {
            html += '<li class="mb-3">';
            html += `<div class="fw-bold text-danger">• ${err.fieldName}</div>`;
            html += '<div class="ms-3 mt-1">';
            html += `<small class="text-muted">Missing: <span class="text-danger fw-semibold">${err.missing.join(', ')}</span></small><br>`;
            html += `<small class="text-muted">Current: ${err.current.length > 0 ? err.current.join(', ') : 'None'}</small>`;
            html += '</div>';
            html += '</li>';
        });

        html += '</ul>';
        html += '<p class="mt-3 text-muted"><small>Please add the missing dimensions to the dependencies before assigning them to the computed field.</small></p>';
        html += '</div>';

        return html;
    }

    /**
     * Format removal error as HTML
     * @param {Array} details - Error details
     * @returns {string} HTML string
     */
    function formatRemovalErrorHTML(details) {
        let html = '<div class="validation-error-details">';
        html += '<p class="mb-3"><strong>This dimension is required by the following computed fields:</strong></p>';
        html += '<ul class="list-unstyled">';

        details.forEach(conflict => {
            html += '<li class="mb-2">';
            html += `<div class="fw-bold text-warning">• ${conflict.fieldName}</div>`;
            html += '<div class="ms-3 mt-1">';
            html += `<small class="text-muted">Required dimensions: ${conflict.required.join(', ')}</small>`;
            html += '</div>';
            html += '</li>';
        });

        html += '</ul>';
        html += '<p class="mt-3 text-muted"><small>Please remove the dimension from the computed fields first, or add it to all their dependencies.</small></p>';
        html += '</div>';

        return html;
    }

    /**
     * Check if a field is computed
     * @param {string} fieldId - Field ID
     * @returns {Promise<boolean>} True if computed
     */
    async function isComputedField(fieldId) {
        try {
            const response = await fetch(`/admin/fields/${fieldId}`);
            if (!response.ok) return false;

            const data = await response.json();
            return data.is_computed === true;
        } catch (error) {
            console.error('[DimensionValidator] Error checking if field is computed:', error);
            return false;
        }
    }

    /**
     * Get field dependencies (for computed fields)
     * @param {string} fieldId - Computed field ID
     * @returns {Promise<Array>} Array of dependency field objects
     */
    async function getFieldDependencies(fieldId) {
        try {
            const response = await fetch(`/admin/fields/${fieldId}/dependencies`);
            if (!response.ok) return [];

            const data = await response.json();
            return data.dependencies || [];
        } catch (error) {
            console.error('[DimensionValidator] Error fetching dependencies:', error);
            return [];
        }
    }

    /**
     * Show validation error modal
     * @param {Object} errorData - Formatted error data
     */
    function showValidationErrorModal(errorData) {
        if (!errorData) return;

        // Create or get error modal
        let modal = document.getElementById('dimensionValidationErrorModal');

        if (!modal) {
            modal = createErrorModal();
            document.body.appendChild(modal);
        }

        // Update modal content
        const titleEl = modal.querySelector('.modal-title');
        const bodyEl = modal.querySelector('.modal-body');

        if (titleEl) titleEl.textContent = errorData.title;
        if (bodyEl) bodyEl.innerHTML = errorData.htmlMessage;

        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    /**
     * Create error modal element
     * @returns {HTMLElement} Modal element
     */
    function createErrorModal() {
        const modal = document.createElement('div');
        modal.id = 'dimensionValidationErrorModal';
        modal.className = 'modal fade';
        modal.setAttribute('tabindex', '-1');
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title">Validation Error</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <!-- Error content will be inserted here -->
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;
        return modal;
    }

    // Public API
    return {
        validateBeforeAssignment,
        validateBeforeRemoval,
        formatValidationErrors,
        isComputedField,
        getFieldDependencies,
        showValidationErrorModal
    };
})();
