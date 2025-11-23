/**
 * Dimension Manager Shared Component
 * Reusable dimension management for Frameworks and Assign Data Points pages
 *
 * Part of Phase 1: Shared Dimension Component
 * Feature: Dimension Configuration in Assign Data Points
 */

window.DimensionManagerShared = (function() {
    'use strict';

    // Configuration
    let config = {
        context: 'generic',
        containerId: 'dimensionManagementModal',
        onDimensionAssigned: null,
        onDimensionRemoved: null,
        onDimensionCreated: null,
        onValidationError: null
    };

    // State
    let currentFieldId = null;
    let currentFieldName = null;
    let availableDimensions = [];
    let assignedDimensions = [];
    let modal = null;
    let isInitialized = false;

    // Event listeners
    const listeners = {};

    /**
     * Initialize the dimension manager
     * @param {Object} userConfig - Configuration object
     */
    function init(userConfig) {
        if (isInitialized) {
            console.warn('[DimensionManagerShared] Already initialized');
            return;
        }

        config = { ...config, ...userConfig };
        modal = document.getElementById(config.containerId);

        if (!modal) {
            console.error(`[DimensionManagerShared] Modal not found: ${config.containerId}`);
            return;
        }

        setupEventListeners();
        isInitialized = true;
    }

    /**
     * Setup event listeners for modal
     */
    function setupEventListeners() {
        // Assign dimension buttons (event delegation)
        modal.addEventListener('click', async (e) => {
            const assignBtn = e.target.closest('.assign-dimension-btn');
            if (assignBtn) {
                const dimensionId = assignBtn.getAttribute('data-dimension-id');
                await assignDimension(dimensionId);
            }

            const removeBtn = e.target.closest('.remove-dimension-btn');
            if (removeBtn) {
                const dimensionId = removeBtn.getAttribute('data-dimension-id');
                const fieldDimensionId = removeBtn.getAttribute('data-field-dimension-id');
                await removeDimension(dimensionId, fieldDimensionId);
            }
        });

        // Create new dimension button
        const createBtn = modal.querySelector('#createNewDimensionBtn');
        if (createBtn) {
            createBtn.addEventListener('click', showInlineDimensionForm);
        }

        // Save inline dimension button
        const saveInlineBtn = modal.querySelector('#saveInlineDimension');
        if (saveInlineBtn) {
            saveInlineBtn.addEventListener('click', createInlineDimension);
        }

        // Cancel inline dimension
        const cancelInlineBtn = modal.querySelector('#cancelInlineDimension');
        if (cancelInlineBtn) {
            cancelInlineBtn.addEventListener('click', hideInlineDimensionForm);
        }

        // Modal shown event
        modal.addEventListener('shown.bs.modal', () => {
            emit('modal-opened', { fieldId: currentFieldId, fieldName: currentFieldName });
        });

        // Modal hidden event
        modal.addEventListener('hidden.bs.modal', () => {
            emit('modal-closed', { fieldId: currentFieldId });
            resetState();
        });
    }

    /**
     * Open dimension modal for a field
     * @param {string} fieldId - Field ID
     * @param {string} fieldName - Field name
     * @param {string} context - Context (frameworks, assign-data-points, etc.)
     */
    async function openDimensionModal(fieldId, fieldName, context) {
        if (!isInitialized) {
            console.error('[DimensionManagerShared] Not initialized. Call init() first.');
            return;
        }

        currentFieldId = fieldId;
        currentFieldName = fieldName;

        // Update modal title
        const titleEl = modal.querySelector('#dimModalFieldName');
        if (titleEl) {
            titleEl.textContent = fieldName;
        }

        // Show loading state
        showLoading();

        // Load data
        try {
            await Promise.all([
                loadAvailableDimensions(),
                loadFieldDimensions(fieldId)
            ]);

            renderDimensions();
        } catch (error) {
            console.error('[DimensionManagerShared] Error loading dimensions:', error);
            showError('Failed to load dimensions');
        }

        // Open modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    /**
     * Close dimension modal
     */
    function closeDimensionModal() {
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) {
            bsModal.hide();
        }
    }

    /**
     * Load available dimensions for the company
     */
    async function loadAvailableDimensions() {
        try {
            const url = '/admin/dimensions';
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error('Failed to load dimensions');
            }

            const data = await response.json();
            availableDimensions = data.dimensions || [];
        } catch (error) {
            console.error('[DimensionManagerShared] Error loading available dimensions:', error);
            availableDimensions = [];
            throw error;
        }
    }

    /**
     * Load dimensions currently assigned to the field
     * @param {string} fieldId - Field ID
     */
    async function loadFieldDimensions(fieldId) {
        try {
            const url = `/admin/fields/${fieldId}/dimensions`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error('Failed to load field dimensions');
            }

            const data = await response.json();
            assignedDimensions = data.dimensions || [];
        } catch (error) {
            console.error('[DimensionManagerShared] Error loading field dimensions:', error);
            assignedDimensions = [];
            throw error;
        }
    }

    /**
     * Render dimensions in modal
     */
    function renderDimensions() {
        renderAssignedDimensions();
        renderAvailableDimensions();
        hideLoading();
    }

    /**
     * Render assigned dimensions section
     */
    function renderAssignedDimensions() {
        const container = modal.querySelector('#assignedDimensionsList');
        const emptyState = modal.querySelector('#noAssignedDimensions');

        if (!container) return;

        if (assignedDimensions.length === 0) {
            container.innerHTML = '';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        if (emptyState) emptyState.style.display = 'none';

        container.innerHTML = assignedDimensions.map(dim => `
            <div class="dimension-card assigned-dimension" data-dimension-id="${dim.dimension_id}">
                <div class="dimension-card-header">
                    <div class="dimension-info">
                        <strong>${dim.name}</strong>
                        ${dim.description ? `<small class="text-muted d-block">${dim.description}</small>` : ''}
                    </div>
                    <button type="button"
                            class="btn btn-sm btn-outline-danger remove-dimension-btn"
                            data-dimension-id="${dim.dimension_id}"
                            data-field-dimension-id="${dim.field_dimension_id || ''}">
                        <i class="fas fa-times"></i> Remove
                    </button>
                </div>
                <div class="dimension-values mt-2">
                    ${dim.values.map(val => `
                        <span class="badge bg-light text-dark me-1">${val.display_name || val.value}</span>
                    `).join('')}
                </div>
            </div>
        `).join('');
    }

    /**
     * Render available dimensions section
     */
    function renderAvailableDimensions() {
        const container = modal.querySelector('#availableDimensionsList');
        const emptyState = modal.querySelector('#noAvailableDimensions');

        if (!container) return;

        // Filter out already assigned dimensions
        const assignedIds = new Set(assignedDimensions.map(d => d.dimension_id));
        const unassigned = availableDimensions.filter(d => !assignedIds.has(d.dimension_id));

        if (unassigned.length === 0) {
            container.innerHTML = '';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        if (emptyState) emptyState.style.display = 'none';

        container.innerHTML = unassigned.map(dim => `
            <div class="dimension-card available-dimension" data-dimension-id="${dim.dimension_id}">
                <div class="dimension-card-header">
                    <div class="dimension-info">
                        <strong>${dim.name}</strong>
                        ${dim.description ? `<small class="text-muted d-block">${dim.description}</small>` : ''}
                    </div>
                    <button type="button"
                            class="btn btn-sm btn-outline-primary assign-dimension-btn"
                            data-dimension-id="${dim.dimension_id}">
                        <i class="fas fa-plus"></i> Add
                    </button>
                </div>
                <div class="dimension-values mt-2">
                    ${dim.values.map(val => `
                        <span class="badge bg-light text-dark me-1">${val.display_name || val.value}</span>
                    `).join('')}
                </div>
            </div>
        `).join('');
    }

    /**
     * Assign dimension to field
     * @param {string} dimensionId - Dimension ID
     */
    async function assignDimension(dimensionId) {
        if (!currentFieldId) return;

        // Show loading on button
        const btn = modal.querySelector(`.assign-dimension-btn[data-dimension-id="${dimensionId}"]`);
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
        }

        try {
            // Validate if computed field
            const newDimensionIds = [...assignedDimensions.map(d => d.dimension_id), dimensionId];
            const validationResult = await window.ComputedFieldDimensionValidator.validateBeforeAssignment(
                currentFieldId,
                newDimensionIds
            );

            if (!validationResult.valid) {
                const errorData = window.ComputedFieldDimensionValidator.formatValidationErrors(validationResult);
                window.ComputedFieldDimensionValidator.showValidationErrorModal(errorData);

                if (config.onValidationError) {
                    config.onValidationError(errorData);
                }

                emit('validation-error', errorData);

                // Reset button
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-plus"></i> Add';
                }
                return;
            }

            // Assign dimension
            const response = await fetch(`/admin/fields/${currentFieldId}/dimensions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dimension_ids: newDimensionIds
                })
            });

            if (!response.ok) throw new Error('Failed to assign dimension');

            const data = await response.json();

            // Reload dimensions and refresh display
            await loadFieldDimensions(currentFieldId);
            renderDimensions();

            // Find dimension data
            const dimension = availableDimensions.find(d => d.dimension_id === dimensionId);

            // Emit event and callback
            const eventData = {
                fieldId: currentFieldId,
                fieldName: currentFieldName,
                dimension: dimension,
                dimensionId: dimensionId
            };

            if (config.onDimensionAssigned) {
                config.onDimensionAssigned(eventData);
            }

            emit('dimension-assigned', eventData);

            showNotification('success', `Dimension "${dimension?.name}" assigned successfully`);

        } catch (error) {
            console.error('[DimensionManagerShared] Error assigning dimension:', error);
            showNotification('error', 'Failed to assign dimension');

            // Reset button
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-plus"></i> Add';
            }
        }
    }

    /**
     * Remove dimension from field
     * @param {string} dimensionId - Dimension ID
     * @param {string} fieldDimensionId - Field dimension ID (junction table)
     */
    async function removeDimension(dimensionId, fieldDimensionId) {
        if (!currentFieldId) return;

        // Show loading on button
        const btn = modal.querySelector(`.remove-dimension-btn[data-dimension-id="${dimensionId}"]`);
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Removing...';
        }

        try {
            // Validate removal
            const validationResult = await window.ComputedFieldDimensionValidator.validateBeforeRemoval(
                currentFieldId,
                dimensionId
            );

            if (!validationResult.valid) {
                const errorData = window.ComputedFieldDimensionValidator.formatValidationErrors(validationResult);
                window.ComputedFieldDimensionValidator.showValidationErrorModal(errorData);

                if (config.onValidationError) {
                    config.onValidationError(errorData);
                }

                emit('validation-error', errorData);

                // Reset button
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-times"></i> Remove';
                }
                return;
            }

            // Remove dimension
            const url = fieldDimensionId ?
                `/admin/fields/${currentFieldId}/dimensions/${fieldDimensionId}` :
                `/admin/fields/${currentFieldId}/dimensions/${dimensionId}`;

            const response = await fetch(url, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error('Failed to remove dimension');

            // Reload dimensions and refresh display
            await loadFieldDimensions(currentFieldId);
            renderDimensions();

            // Find dimension data
            const dimension = availableDimensions.find(d => d.dimension_id === dimensionId);

            // Emit event and callback
            const eventData = {
                fieldId: currentFieldId,
                fieldName: currentFieldName,
                dimension: dimension,
                dimensionId: dimensionId
            };

            if (config.onDimensionRemoved) {
                config.onDimensionRemoved(eventData);
            }

            emit('dimension-removed', eventData);

            showNotification('success', `Dimension "${dimension?.name}" removed successfully`);

        } catch (error) {
            console.error('[DimensionManagerShared] Error removing dimension:', error);
            showNotification('error', 'Failed to remove dimension');

            // Reset button
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-times"></i> Remove';
            }
        }
    }

    /**
     * Show inline dimension creation form
     */
    function showInlineDimensionForm() {
        const form = modal.querySelector('#inlineDimensionForm');
        const createBtn = modal.querySelector('#createNewDimensionBtn');

        if (form) {
            form.style.display = 'block';
            resetInlineDimensionForm();
        }

        if (createBtn) {
            createBtn.style.display = 'none';
        }
    }

    /**
     * Hide inline dimension creation form
     */
    function hideInlineDimensionForm() {
        const form = modal.querySelector('#inlineDimensionForm');
        const createBtn = modal.querySelector('#createNewDimensionBtn');

        if (form) form.style.display = 'none';
        if (createBtn) createBtn.style.display = 'block';
    }

    /**
     * Reset inline dimension form
     */
    function resetInlineDimensionForm() {
        const nameInput = modal.querySelector('#inlineDimensionName');
        const descInput = modal.querySelector('#inlineDimensionDescription');
        const valuesContainer = modal.querySelector('#inlineDimensionValues');

        if (nameInput) nameInput.value = '';
        if (descInput) descInput.value = '';

        if (valuesContainer) {
            valuesContainer.innerHTML = `
                <div class="input-group mb-2">
                    <input type="text" class="form-control inline-dimension-value-input" placeholder="e.g., Value 1" required>
                    <input type="text" class="form-control" placeholder="Display name (optional)">
                    <button type="button" class="btn btn-outline-danger remove-inline-value-btn" disabled>
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
        }

        // Setup add value button
        const addValueBtn = modal.querySelector('#addInlineDimensionValue');
        if (addValueBtn) {
            addValueBtn.onclick = addInlineDimensionValueRow;
        }
    }

    /**
     * Add dimension value row to inline form
     */
    function addInlineDimensionValueRow() {
        const valuesContainer = modal.querySelector('#inlineDimensionValues');
        if (!valuesContainer) return;

        const newRow = document.createElement('div');
        newRow.className = 'input-group mb-2';
        newRow.innerHTML = `
            <input type="text" class="form-control inline-dimension-value-input" placeholder="e.g., Value ${valuesContainer.children.length + 1}" required>
            <input type="text" class="form-control" placeholder="Display name (optional)">
            <button type="button" class="btn btn-outline-danger remove-inline-value-btn">
                <i class="fas fa-trash"></i>
            </button>
        `;

        // Add remove handler
        newRow.querySelector('.remove-inline-value-btn').addEventListener('click', function() {
            if (valuesContainer.children.length > 1) {
                newRow.remove();
            }
        });

        valuesContainer.appendChild(newRow);

        // Enable remove buttons if more than one row
        const removeButtons = valuesContainer.querySelectorAll('.remove-inline-value-btn');
        removeButtons.forEach(btn => btn.disabled = valuesContainer.children.length === 1);
    }

    /**
     * Create new dimension inline
     */
    async function createInlineDimension() {
        const nameInput = modal.querySelector('#inlineDimensionName');
        const descInput = modal.querySelector('#inlineDimensionDescription');
        const valueInputs = modal.querySelectorAll('.inline-dimension-value-input');
        const displayInputs = modal.querySelectorAll('#inlineDimensionValues .input-group input[type="text"]:nth-child(2)');

        const name = nameInput?.value.trim();
        const description = descInput?.value.trim();

        if (!name) {
            showNotification('error', 'Dimension name is required');
            return;
        }

        // Collect values
        const values = [];
        valueInputs.forEach((input, index) => {
            const value = input.value.trim();
            if (value) {
                const displayName = displayInputs[index]?.value.trim() || value;
                values.push({
                    value: value,
                    display_name: displayName,
                    display_order: index
                });
            }
        });

        if (values.length === 0) {
            showNotification('error', 'At least one dimension value is required');
            return;
        }

        const saveBtn = modal.querySelector('#saveInlineDimension');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
        }

        try {
            const response = await fetch('/admin/dimensions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    description: description || null,
                    values: values
                })
            });

            if (!response.ok) throw new Error('Failed to create dimension');

            const data = await response.json();
            const newDimension = data.dimension;

            // Reload available dimensions
            await loadAvailableDimensions();

            // Auto-assign to current field
            await assignDimension(newDimension.dimension_id);

            // Hide form
            hideInlineDimensionForm();

            // Emit event and callback
            const eventData = {
                dimension: newDimension
            };

            if (config.onDimensionCreated) {
                config.onDimensionCreated(eventData);
            }

            emit('dimension-created', eventData);

            showNotification('success', `Dimension "${newDimension.name}" created and assigned successfully`);

        } catch (error) {
            console.error('[DimensionManagerShared] Error creating dimension:', error);
            showNotification('error', 'Failed to create dimension');
        } finally {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="fas fa-save"></i> Save & Assign';
            }
        }
    }

    /**
     * Show loading state
     */
    function showLoading() {
        const assignedContainer = modal.querySelector('#assignedDimensionsList');
        const availableContainer = modal.querySelector('#availableDimensionsList');

        if (assignedContainer) {
            assignedContainer.innerHTML = '<div class="text-center py-3"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
        }

        if (availableContainer) {
            availableContainer.innerHTML = '<div class="text-center py-3"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
        }
    }

    /**
     * Hide loading state
     */
    function hideLoading() {
        // Handled by renderDimensions()
    }

    /**
     * Show error message
     * @param {string} message - Error message
     */
    function showError(message) {
        const assignedContainer = modal.querySelector('#assignedDimensionsList');
        const availableContainer = modal.querySelector('#availableDimensionsList');

        const errorHTML = `<div class="alert alert-danger">${message}</div>`;

        if (assignedContainer) assignedContainer.innerHTML = errorHTML;
        if (availableContainer) availableContainer.innerHTML = errorHTML;
    }

    /**
     * Show notification
     * @param {string} type - Notification type (success, error, warning)
     * @param {string} message - Notification message
     */
    function showNotification(type, message) {
        if (window.showNotification) {
            window.showNotification(type, message);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    /**
     * Reset state
     */
    function resetState() {
        currentFieldId = null;
        currentFieldName = null;
        assignedDimensions = [];
    }

    /**
     * Refresh field dimensions
     * @param {string} fieldId - Field ID
     */
    async function refreshFieldDimensions(fieldId) {
        await loadFieldDimensions(fieldId);
        if (currentFieldId === fieldId) {
            renderDimensions();
        }
    }

    /**
     * Event system - register listener
     * @param {string} event - Event name
     * @param {Function} callback - Callback function
     */
    function on(event, callback) {
        if (!listeners[event]) {
            listeners[event] = [];
        }
        listeners[event].push(callback);
    }

    /**
     * Event system - unregister listener
     * @param {string} event - Event name
     * @param {Function} callback - Callback function
     */
    function off(event, callback) {
        if (!listeners[event]) return;
        listeners[event] = listeners[event].filter(cb => cb !== callback);
    }

    /**
     * Event system - emit event
     * @param {string} event - Event name
     * @param {*} data - Event data
     */
    function emit(event, data) {
        console.log(`[DimensionManagerShared] Event: ${event}`, data);
        if (!listeners[event]) return;
        listeners[event].forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`[DimensionManagerShared] Error in ${event} listener:`, error);
            }
        });
    }

    // Public API
    return {
        init,
        openDimensionModal,
        closeDimensionModal,
        refreshFieldDimensions,
        on,
        off
    };
})();
