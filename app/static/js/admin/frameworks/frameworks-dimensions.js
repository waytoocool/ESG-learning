/**
 * Frameworks Dimensions Module
 * Handles dimension management, assignment, and filtering functionality
 * REFACTORED: Now uses shared dimension component from /static/js/shared/
 */

window.FrameworksDimensions = (function() {
    'use strict';

    // Private variables (exact copies from original)
    let availableDimensions = [];
    let currentDimensionRow = null;
    let drawerSaveCallback = null;
    let drawerAssignedDimensions = []; // Temporary storage for dimensions in drawer context
    let drawerInitialDimensions = [];
    let useSharedComponent = true; // Feature flag for shared dimension component

    // Dimension Management Functions (exact copies from original)
    function setupDimensionManagement(row) {
        const manageDimensionsBtn = row.querySelector('.manage-dimensions-btn');
        if (manageDimensionsBtn) {
            manageDimensionsBtn.addEventListener('click', function() {
                const rowId = this.getAttribute('data-row-id');
                const fieldNameInput = row.querySelector('.field-name-input');
                const fieldName = fieldNameInput ? fieldNameInput.value : 'New Field';
                openDimensionModal(rowId, fieldName, row);
            });
        }
    }
    
    function openDimensionModal(rowId, fieldName, row) {
        currentDimensionRow = row;
        const modal = document.getElementById('dimensionModal');
        const fieldNameSpan = document.getElementById('dimensionFieldName');
        
        if (fieldNameSpan) {
            fieldNameSpan.textContent = fieldName;
        }
        
        // Load available dimensions
        loadAvailableDimensions();
        
        // Load currently assigned dimensions for this field
        loadFieldDimensions(row);
        
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }
    
    function loadAvailableDimensions() {
        fetch('/admin/dimensions')
            .then(response => response.json())
            .then(data => {
                availableDimensions = data.dimensions || [];
                displayAvailableDimensions();
            })
            .catch(error => {
                availableDimensions = [];
                displayAvailableDimensions();
            });
    }
    
    function displayAvailableDimensions() {
        const container = document.getElementById('availableDimensions');
        if (!container) return;
        
        if (availableDimensions.length === 0) {
            container.innerHTML = '<p class="text-muted">No dimensions available. Create one first.</p>';
            return;
        }
        
        container.innerHTML = availableDimensions.map(dim => `
            <div class="dimension-card border rounded p-2 mb-2">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${dim.name}</strong>
                        <div class="text-muted small">${dim.description || 'No description'}</div>
                        <div class="mt-1">
                            ${dim.values.map(val => `
                                <span class="badge bg-light text-dark me-1">${val.display_name || val.value}</span>
                            `).join('')}
                        </div>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-primary assign-dimension-btn" 
                            data-dimension-id="${dim.dimension_id}" data-dimension-name="${dim.name}">
                        <i class="fas fa-plus"></i> Assign
                    </button>
                </div>
            </div>
        `).join('');
        
        // Add event listeners for assign buttons
        container.querySelectorAll('.assign-dimension-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const dimensionId = this.getAttribute('data-dimension-id');
                const dimensionName = this.getAttribute('data-dimension-name');
                addDimensionToDrawerAssignedList(dimensionId, dimensionName); // Changed to new function
            });
        });
    }
    
    // Dimension Creation Functions (exact copies from original)
    function initializeDimensionCreation() {
        const createDimensionBtn = document.getElementById('createDimensionBtn');
        const saveDimensionBtn = document.getElementById('saveDimension');
        const addValueBtn = document.getElementById('addDimensionValue');
        
        if (createDimensionBtn) {
            createDimensionBtn.addEventListener('click', function() {
                const createModal = new bootstrap.Modal(document.getElementById('createDimensionModal'));
                resetDimensionForm();
                createModal.show();
            });
        }
        
        if (saveDimensionBtn) {
            saveDimensionBtn.addEventListener('click', createNewDimension);
        }
        
        if (addValueBtn) {
            addValueBtn.addEventListener('click', addDimensionValueRow);
        }
        
        // Initialize remove value button handlers
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('remove-value-btn') || e.target.closest('.remove-value-btn')) {
                const button = e.target.closest('.remove-value-btn');
                const row = button.closest('.input-group');
                if (document.querySelectorAll('.dimension-value-input').length > 1) {
                    row.remove();
                }
            }
        });
    }
    
    function resetDimensionForm() {
        document.getElementById('dimensionName').value = '';
        document.getElementById('dimensionDescription').value = '';
        
        // Reset dimension values to single row
        const valuesContainer = document.getElementById('dimensionValues');
        valuesContainer.innerHTML = `
            <div class="input-group mb-2">
                <input type="text" class="form-control dimension-value-input" placeholder="e.g., Male" required>
                <input type="text" class="form-control" placeholder="Display name (optional)">
                <button type="button" class="btn btn-outline-danger remove-value-btn">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
    }
    
    function addDimensionValueRow() {
        const valuesContainer = document.getElementById('dimensionValues');
        const newRow = document.createElement('div');
        newRow.className = 'input-group mb-2';
        newRow.innerHTML = `
            <input type="text" class="form-control dimension-value-input" placeholder="e.g., Female" required>
            <input type="text" class="form-control" placeholder="Display name (optional)">
            <button type="button" class="btn btn-outline-danger remove-value-btn">
                <i class="fas fa-trash"></i>
            </button>
        `;
        valuesContainer.appendChild(newRow);
    }
    
    function createNewDimension() {
        const name = document.getElementById('dimensionName').value.trim();
        const description = document.getElementById('dimensionDescription').value.trim();
        
        if (!name) {
            alert('Dimension name is required');
            return;
        }
        
        // Collect dimension values
        const valueInputs = document.querySelectorAll('.dimension-value-input');
        const displayInputs = document.querySelectorAll('#dimensionValues .input-group input[type="text"]:nth-child(2)');
        
        const values = [];
        valueInputs.forEach((input, index) => {
            const value = input.value.trim();
            if (value) {
                const displayName = displayInputs[index] ? displayInputs[index].value.trim() : '';
                values.push({
                    value: value,
                    display_name: displayName || value,
                    display_order: index + 1
                });
            }
        });
        
        if (values.length === 0) {
            alert('At least one dimension value is required');
            return;
        }
        
        const dimensionData = {
            name: name,
            description: description || null,
            values: values
        };
        
        // Save dimension via API
        fetch('/admin/dimensions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dimensionData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.error || 'Unknown server error');
                });
            }
            return response.json();
        })
        .then(data => {
            // Close the modal
            const createModal = bootstrap.Modal.getInstance(document.getElementById('createDimensionModal'));
            createModal.hide();
            
            if (data.success && data.dimension) {
                availableDimensions.push(data.dimension);
                displayAvailableDimensions();
                alert('Dimension created successfully!');
            } else {
                // This case should ideally not be hit if response.ok is true and backend follows contract
                alert('Error creating dimension: ' + (data.error || 'Unexpected response format'));
            }
            
            // Refresh available dimensions (as a fallback/synchronization)
            loadAvailableDimensions();
        })
        .catch(error => {
            console.error('Error creating dimension:', error);
            alert('Error creating dimension: ' + (error.message || 'Please try again.'));
        });
    }
    
    function loadFieldDimensions(row) {
        const dimensionsInput = row.querySelector('.field-dimensions-input');
        const assignedContainer = document.getElementById('assignedDimensions');
        
        if (!assignedContainer) return;
        
        try {
            const assignedDimensions = dimensionsInput.value ? JSON.parse(dimensionsInput.value) : [];
            displayAssignedDimensions(assignedDimensions);
        } catch (error) {
            displayAssignedDimensions([]);
        }
    }
    
    function displayAssignedDimensions(assignedDimensions) {
        const container = document.getElementById('assignedDimensions');
        if (!container) return;
        
        if (assignedDimensions.length === 0) {
            container.innerHTML = '<p class="text-muted">No dimensions assigned to this field.</p>';
            return;
        }
        
        container.innerHTML = assignedDimensions.map(dim => `
            <div class="dimension-card border rounded p-2 mb-2 bg-light" data-dimension-id="${dim.dimension_id}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${dim.name}</strong>
                        <div class="form-check mt-1">
                            <input class="form-check-input dimension-required-cb" type="checkbox" 
                                   ${dim.is_required ? 'checked' : ''} 
                                   data-dimension-id="${dim.dimension_id}">
                            <label class="form-check-label small">Required for data entry</label>
                        </div>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-dimension-btn" 
                            data-dimension-id="${dim.dimension_id}">
                        <i class="fas fa-times"></i> Remove
                    </button>
                </div>
            </div>
        `).join('');
        
        // Add event listeners
        container.querySelectorAll('.remove-dimension-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const dimensionId = this.getAttribute('data-dimension-id');
                removeDimensionFromDrawerAssignedList(dimensionId); // Changed to new function
            });
        });
        
        container.querySelectorAll('.dimension-required-cb').forEach(cb => {
            cb.addEventListener('change', function() {
                const dimensionId = this.getAttribute('data-dimension-id');
                updateDimensionRequirementInDrawer(dimensionId, this.checked); // Changed to new function
            });
        });
    }
    
    function assignDimensionToField(dimensionId, dimensionName) {
        if (!currentDimensionRow) return;
        
        const dimensionsInput = currentDimensionRow.querySelector('.field-dimensions-input');
        let assignedDimensions;
        
        try {
            assignedDimensions = dimensionsInput.value ? JSON.parse(dimensionsInput.value) : [];
        } catch (error) {
            assignedDimensions = [];
        }
        
        // Check if already assigned
        if (assignedDimensions.find(dim => dim.dimension_id === dimensionId)) {
            alert('This dimension is already assigned to the field.');
            return;
        }
        
        // Add the dimension
        assignedDimensions.push({
            dimension_id: dimensionId,
            name: dimensionName,
            is_required: false
        });
        
        // Update the hidden input
        dimensionsInput.value = JSON.stringify(assignedDimensions);
        
        // Refresh the display
        displayAssignedDimensions(assignedDimensions);
        updateDimensionSummary(currentDimensionRow, assignedDimensions);
    }
    
    function removeDimensionFromField(dimensionId) {
        if (!currentDimensionRow) return;
        
        const dimensionsInput = currentDimensionRow.querySelector('.field-dimensions-input');
        let assignedDimensions;
        
        try {
            assignedDimensions = dimensionsInput.value ? JSON.parse(dimensionsInput.value) : [];
        } catch (error) {
            assignedDimensions = [];
        }
        
        // Remove the dimension
        assignedDimensions = assignedDimensions.filter(dim => dim.dimension_id !== dimensionId);
        
        // Update the hidden input
        dimensionsInput.value = JSON.stringify(assignedDimensions);
        
        // Refresh the display
        displayAssignedDimensions(assignedDimensions);
        updateDimensionSummary(currentDimensionRow, assignedDimensions);
    }
    
    function updateDimensionRequirement(dimensionId, isRequired) {
        if (!currentDimensionRow) return;
        
        const dimensionsInput = currentDimensionRow.querySelector('.field-dimensions-input');
        let assignedDimensions;
        
        try {
            assignedDimensions = dimensionsInput.value ? JSON.parse(dimensionsInput.value) : [];
        } catch (error) {
            assignedDimensions = [];
        }
        
        // Update the requirement flag
        const dimension = assignedDimensions.find(dim => dim.dimension_id === dimensionId);
        if (dimension) {
            dimension.is_required = isRequired;
            dimensionsInput.value = JSON.stringify(assignedDimensions);
            updateDimensionSummary(currentDimensionRow, assignedDimensions);
        }
    }
    
    function updateDimensionSummary(row, assignedDimensions) {
        const summaryDiv = row.querySelector('.dimension-summary');
        if (!summaryDiv) return;
        
        if (assignedDimensions.length === 0) {
            summaryDiv.innerHTML = '<small class="text-muted">No dimensions assigned</small>';
        } else {
            const requiredCount = assignedDimensions.filter(dim => dim.is_required).length;
            summaryDiv.innerHTML = `
                <small class="text-success">
                    ${assignedDimensions.length} dimension(s) assigned
                    ${requiredCount > 0 ? `(${requiredCount} required)` : ''}
                </small>
            `;
        }
    }

    // Dimension Filter Functions (exact copies from original)
    function loadAvailableDimensionsForFilter(mappingDiv) {
        // Use the same availableDimensions array loaded earlier
        if (availableDimensions.length === 0) {
            loadAvailableDimensions(); // Reload if not available
        }
    }
    
    function addDimensionFilterRule(mappingDiv) {
        const filtersContainer = mappingDiv.querySelector('.dimension-filters-container');
        const ruleId = Date.now() + Math.random();
        
        const ruleDiv = document.createElement('div');
        ruleDiv.className = 'dimension-filter-rule';
        ruleDiv.setAttribute('data-rule-id', ruleId);
        
        ruleDiv.innerHTML = `
            <select class="form-select dimension-select" required>
                <option value="">Select Dimension</option>
                ${availableDimensions.map(dim => 
                    `<option value="${dim.dimension_id}">${dim.name}</option>`
                ).join('')}
            </select>
            <select class="form-select dimension-value-select" disabled required>
                <option value="">Select Dimension First</option>
            </select>
            <button type="button" class="btn btn-outline-danger btn-sm remove-filter-btn">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        filtersContainer.appendChild(ruleDiv);
        
        // Setup event listeners for this rule
        const dimensionSelect = ruleDiv.querySelector('.dimension-select');
        const valueSelect = ruleDiv.querySelector('.dimension-value-select');
        const removeBtn = ruleDiv.querySelector('.remove-filter-btn');
        
        dimensionSelect.addEventListener('change', function() {
            if (this.value) {
                const dimension = availableDimensions.find(dim => dim.dimension_id === this.value);
                if (dimension) {
                    valueSelect.innerHTML = '<option value="">Select Value</option>';
                    dimension.values.forEach(value => {
                        const option = document.createElement('option');
                        option.value = value.value;
                        option.textContent = value.effective_display_name || value.display_name || value.value;
                        valueSelect.appendChild(option);
                    });
                    valueSelect.disabled = false;
                }
            } else {
                valueSelect.innerHTML = '<option value="">Select Dimension First</option>';
                valueSelect.disabled = true;
            }
        });
        
        removeBtn.addEventListener('click', function() {
            ruleDiv.remove();
        });
    }

    // Drawer-specific dimension functions (exact copies from original)

    function openDrawerDimensionModal(initialDimensions, saveCallback) {
        console.log('openDrawerDimensionModal called');
        drawerSaveCallback = saveCallback;
        drawerAssignedDimensions = initialDimensions || [];

        const modal = document.getElementById('dimensionModal');
        console.log('dimensionModal element:', modal); // Check if modal element is found
        
        if (!modal) {
            console.error('Dimension modal element not found!');
            return; // Exit if modal element is not found
        }

        const fieldNameSpan = document.getElementById('dimensionFieldName');
        
        if (fieldNameSpan) {
            fieldNameSpan.textContent = 'Data Point Dimensions';
        }
        
        loadAvailableDimensions();
        displayAssignedDimensions(drawerAssignedDimensions);

        initializeDimensionCreation();
        
        const bootstrapModal = new bootstrap.Modal(modal);
        console.log('Bootstrap modal instance:', bootstrapModal); // Check if Bootstrap modal is initialized
        bootstrapModal.show();
        
        const saveDimensionsBtn = document.getElementById('saveDimensions');
        if (saveDimensionsBtn) {
            saveDimensionsBtn.onclick = function() {
                saveDrawerDimensions();
                bootstrapModal.hide();
            };
        }
    }

    function addDimensionToDrawerAssignedList(dimensionId, dimensionName) {
        // Check if already assigned
        if (drawerAssignedDimensions.find(dim => dim.dimension_id === dimensionId)) {
            alert('This dimension is already assigned to the field.');
            return;
        }
        
        drawerAssignedDimensions.push({
            dimension_id: dimensionId,
            name: dimensionName,
            is_required: false // Default to not required when assigning
        });
        displayAssignedDimensions(drawerAssignedDimensions);
    }

    function removeDimensionFromDrawerAssignedList(dimensionId) {
        drawerAssignedDimensions = drawerAssignedDimensions.filter(dim => dim.dimension_id !== dimensionId);
        displayAssignedDimensions(drawerAssignedDimensions);
    }

    function updateDimensionRequirementInDrawer(dimensionId, isRequired) {
        const dimension = drawerAssignedDimensions.find(dim => dim.dimension_id === dimensionId);
        if (dimension) {
            dimension.is_required = isRequired;
            // Re-render to reflect the change if needed, or just update the internal state
            // displayAssignedDimensions(drawerAssignedDimensions); // Not strictly necessary for checkbox change
        }
    }

    function saveDrawerDimensions() {
        // The drawerAssignedDimensions array already holds the current state
        if (drawerSaveCallback) {
            drawerSaveCallback(drawerAssignedDimensions);
        }
    }

    function updateDrawerDimensionSummary(dimensions) {
        const dimensionSummary = document.querySelector('#dataPointDrawer .dimension-summary');
        if (dimensions && dimensions.length > 0) {
            const dimensionTags = dimensions.map(dim => 
                `<span class="dimension-tag">${dim.name}</span>`
            ).join('');
            dimensionSummary.innerHTML = dimensionTags;
        } else {
            dimensionSummary.innerHTML = '<small class="text-muted">No dimensions assigned</small>';
        }
    }

    // Public API
    return {
        initialize: function() {
            initializeDimensionCreation();
            loadAvailableDimensions(); // Load dimensions on initialization
        },
        
        // Core functions
        setupDimensionManagement: setupDimensionManagement,
        openDimensionModal: openDimensionModal,
        loadAvailableDimensions: loadAvailableDimensions,
        displayAvailableDimensions: displayAvailableDimensions,
        initializeDimensionCreation: initializeDimensionCreation,
        resetDimensionForm: resetDimensionForm,
        addDimensionValueRow: addDimensionValueRow,
        createNewDimension: createNewDimension,
        loadFieldDimensions: loadFieldDimensions,
        displayAssignedDimensions: displayAssignedDimensions,
        assignDimensionToField: assignDimensionToField,
        removeDimensionFromField: removeDimensionFromField,
        updateDimensionRequirement: updateDimensionRequirement,
        updateDimensionSummary: updateDimensionSummary,
        loadAvailableDimensionsForFilter: loadAvailableDimensionsForFilter,
        addDimensionFilterRule: addDimensionFilterRule,
        
        // Drawer-specific functions
        openDrawerDimensionModal: openDrawerDimensionModal,
        saveDrawerDimensions: saveDrawerDimensions,
        updateDrawerDimensionSummary: updateDrawerDimensionSummary,
        
        // Utility functions
        getAvailableDimensions: function() {
            return availableDimensions;
        },
        
        setCurrentDimensionRow: function(row) {
            currentDimensionRow = row;
        },
        
        refresh: function() {
            loadAvailableDimensions();
        },

        /**
         * Check if module is ready
         */
        isReady: function() {
            return true; // Dimensions module is ready when initialized
        }
    };
})();

// Helper function to encapsulate save and hide logic for the drawer dimension modal
function saveDrawerDimensionsAndHideModal() {
    window.FrameworksDimensions.saveDrawerDimensions();
    const modal = document.getElementById('dimensionModal');
    if (modal) {
        const bootstrapModal = bootstrap.Modal.getInstance(modal);
        if (bootstrapModal) {
            bootstrapModal.hide();
        }
    }
}

// Override the save button's behavior for the drawer dimension modal
document.addEventListener('DOMContentLoaded', function() {
    const saveDimensionsBtn = document.getElementById('saveDimensions');
    if (saveDimensionsBtn) {
        // Remove any existing event listeners to prevent multiple bindings
        saveDimensionsBtn.removeEventListener('click', saveDrawerDimensionsAndHideModal);
        // Add the new event listener
        saveDimensionsBtn.addEventListener('click', saveDrawerDimensionsAndHideModal);
    }

    // Initialize Shared Dimension Component if available
    if (typeof window.DimensionManagerShared !== 'undefined') {
        console.log('[Frameworks] Initializing shared dimension component...');
        try {
            window.DimensionManagerShared.init({
                context: 'frameworks',
                containerId: 'dimensionManagementModal',

                onDimensionAssigned: function(fieldId, dimensionData) {
                    console.log('[Frameworks] Dimension assigned via shared component:', fieldId, dimensionData);
                    // The shared component handles the assignment automatically
                    // We just log it here for tracking
                },

                onDimensionRemoved: function(fieldId, dimensionId) {
                    console.log('[Frameworks] Dimension removed via shared component:', fieldId, dimensionId);
                    // The shared component handles the removal automatically
                },

                onDimensionCreated: function(dimensionData) {
                    console.log('[Frameworks] New dimension created via shared component:', dimensionData);
                },

                onValidationError: function(errorData) {
                    console.error('[Frameworks] Dimension validation error:', errorData);
                    // Error modal is shown automatically by the shared component
                }
            });
            console.log('[Frameworks] Shared dimension component initialized successfully');
        } catch (error) {
            console.error('[Frameworks] Error initializing shared dimension component:', error);
        }
    } else {
        console.warn('[Frameworks] DimensionManagerShared not available - using legacy dimension management');
    }
}); 