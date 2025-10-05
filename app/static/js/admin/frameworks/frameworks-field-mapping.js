/**
 * Frameworks Field Mapping Module
 * Handles field mapping, computed fields, and dimension configuration
 */

window.FrameworksFieldMapping = (function() {
    'use strict';

    // Private variables
    let availableDimensions = [];

    // Row Event Listeners (exact copy from original)
    function addRowEventListeners(row) {
        // Auto-generate field code
        const nameInput = row.querySelector('.field-name-input');
        const codeInput = row.querySelector('.field-code-input');
        
        nameInput.addEventListener('input', function() {
            if (!codeInput.value || codeInput.hasAttribute('data-auto-generated')) {
                const slug = window.FrameworksCommon ? window.FrameworksCommon.generateSlug(this.value) : this.value.toLowerCase().replace(/[^a-zA-Z0-9\s-]/g, '').replace(/[\s-]+/g, '_');
                codeInput.value = slug;
                codeInput.setAttribute('data-auto-generated', 'true');
            }
        });
        
        codeInput.addEventListener('input', function() {
            if (this.value) {
                this.removeAttribute('data-auto-generated');
            }
        });

        // Toggle computed field inputs
        const computedCheckbox = row.querySelector('.is-computed-checkbox');
        const formulaInputs = row.querySelector('.formula-inputs');
        
        if (computedCheckbox && formulaInputs) {
            computedCheckbox.addEventListener('change', function() {
                if (this.checked) {
                    formulaInputs.classList.remove('d-none');
                } else {
                    formulaInputs.classList.add('d-none');
                }
            });
        }

        // Remove row
        const removeBtn = row.querySelector('.remove-data-point');
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                row.remove();
            });
        }

        // Add raw field mapping for computed fields
        const addRawFieldBtn = row.querySelector('.add-raw-field');
        if (addRawFieldBtn) {
            addRawFieldBtn.addEventListener('click', function() {
                addRawFieldMapping(row);
            });
        }

        // Setup unit-aware inputs for new row
        if (window.FrameworksUnitManagement && window.FrameworksUnitManagement.setupUnitAwareInputs) {
            window.FrameworksUnitManagement.setupUnitAwareInputs(row);
        }
        
        // Setup dimension management for new row
        if (window.FrameworksDimensions && window.FrameworksDimensions.setupDimensionManagement) {
            window.FrameworksDimensions.setupDimensionManagement(row);
        }
    }

    // Raw Field Mapping with Dimension Support for Computed Fields (exact copy from original)
    function addRawFieldMapping(row, preselectData = null) {
        const rawFieldsContainer = row.querySelector('.raw-fields-container');
        if (!rawFieldsContainer) return;
        
        const mappingId = Date.now() + Math.random();
        const mappingDiv = document.createElement('div');
        mappingDiv.className = 'raw-field-mapping border rounded p-3 mb-3';
        mappingDiv.setAttribute('data-mapping-id', mappingId);
        
        // Set preselect data immediately if provided
        if (preselectData) {
            mappingDiv.setAttribute('data-framework-id', preselectData.framework_id || '');
            mappingDiv.setAttribute('data-field-id', preselectData.raw_field_id || '');
        }
        
        mappingDiv.innerHTML = `
            <div class="row g-3">
                <div class="col-md-2">
                    <label class="form-label">Variable</label>
                    <input type="text" class="form-control form-control-sm variable-input" 
                           placeholder="A" maxlength="1" pattern="[A-Z]" required>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Framework</label>
                    <select class="form-control form-control-sm framework-select" required>
                        <option value="">Select Framework</option>
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label">Field</label>
                    <select class="form-control form-control-sm field-select" disabled required>
                        <option value="">Select Framework First</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <label class="form-label">Coefficient</label>
                    <input type="number" class="form-control form-control-sm coefficient-input" 
                           value="1" step="any" required>
                </div>
                <div class="col-md-1">
                    <label class="form-label">&nbsp;</label>
                    <button type="button" class="btn btn-danger btn-sm d-block remove-mapping-btn">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            
            <!-- Dimension Configuration for Computed Fields -->
            <div class="computed-field-dimension-config">
                <h6><i class="fas fa-tags"></i> Dimension Aggregation</h6>
                
                <div class="aggregation-type-selector">
                    <div class="form-check">
                        <input class="form-check-input aggregation-type-radio" type="radio" 
                               name="aggregation_type_${mappingId}" 
                               id="sum_all_${mappingId}" 
                               value="SUM_ALL_DIMENSIONS" checked>
                        <label class="form-check-label" for="sum_all_${mappingId}">
                            <strong>Sum All Dimensions</strong>
                            <small class="d-block text-muted">Aggregate all dimensional values (e.g., All Male + Female employees)</small>
                        </label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input aggregation-type-radio" type="radio" 
                               name="aggregation_type_${mappingId}" 
                               id="specific_dimension_${mappingId}" 
                               value="SPECIFIC_DIMENSION">
                        <label class="form-check-label" for="specific_dimension_${mappingId}">
                            <strong>Specific Dimension Filter</strong>
                            <small class="d-block text-muted">Filter to specific dimensional values (e.g., Only Male employees under 30)</small>
                        </label>
                    </div>
                </div>
                
                <div class="dimension-filter-section" style="display: none;">
                    <div class="dimension-filter-builder">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <label class="form-label mb-0">Dimension Filters</label>
                            <button type="button" class="btn btn-outline-primary btn-sm add-dimension-filter-btn">
                                <i class="fas fa-plus"></i> Add Filter
                            </button>
                        </div>
                        <div class="dimension-filters-container">
                            <!-- Dimension filter rules will be added here -->
                        </div>
                        <small class="text-muted">
                            Only data matching all selected dimension values will be included in the calculation.
                        </small>
                    </div>
                </div>
            </div>
        `;

        rawFieldsContainer.appendChild(mappingDiv);
        
        // Set basic values if preselect data provided
        if (preselectData) {
            const variableInput = mappingDiv.querySelector('.variable-input');
            const coefficientInput = mappingDiv.querySelector('.coefficient-input');
            if (variableInput) variableInput.value = preselectData.variable_name || '';
            if (coefficientInput) coefficientInput.value = preselectData.coefficient || 1;
        }
        
        // Setup event listeners for this mapping
        setupMappingEventListeners(mappingDiv, mappingId);
        
        // Load available frameworks (now with preselect data already set)
        loadFrameworksForMapping(mappingDiv);
        
        return mappingDiv; // Return the created mapping div
    }
    
    function setupMappingEventListeners(mappingDiv, mappingId) {
        // Framework selection
        const frameworkSelect = mappingDiv.querySelector('.framework-select');
        const fieldSelect = mappingDiv.querySelector('.field-select');

        // If mappingDiv has preselected framework/field IDs (set by initVariableMappingUI) choose them
        const preFrameworkId = mappingDiv.getAttribute('data-framework-id');
        const preFieldId = mappingDiv.getAttribute('data-field-id');

        frameworkSelect.addEventListener('change', function() {
            if (this.value) {
                loadFieldsForFramework(this.value, fieldSelect);
            } else {
                fieldSelect.innerHTML = '<option value="">Select Framework First</option>';
                fieldSelect.disabled = true;
            }
        });

        // If a preselected framework exists, set it and trigger change
        if (preFrameworkId) {
            // frameworks will be loaded later, so set value after loadFrameworksForMapping
            frameworkSelect.dataset.preselectFramework = preFrameworkId;
        }

        // Store desired field to preselect later
        if (preFieldId) {
            fieldSelect.dataset.preselectField = preFieldId;
        }

        // Remove mapping
        const removeBtn = mappingDiv.querySelector('.remove-mapping-btn');
        removeBtn.addEventListener('click', function() {
            mappingDiv.remove();
        });
        
        // Aggregation type change
        const aggregationRadios = mappingDiv.querySelectorAll('.aggregation-type-radio');
        const dimensionFilterSection = mappingDiv.querySelector('.dimension-filter-section');
        
        aggregationRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'SPECIFIC_DIMENSION') {
                    dimensionFilterSection.style.display = 'block';
                    loadAvailableDimensionsForFilter(mappingDiv);
                } else {
                    dimensionFilterSection.style.display = 'none';
                }
            });
        });
        
        // Add dimension filter
        const addFilterBtn = mappingDiv.querySelector('.add-dimension-filter-btn');
        addFilterBtn.addEventListener('click', function() {
            addDimensionFilterRule(mappingDiv);
        });
    }
    
    function loadFrameworksForMapping(mappingDiv) {
        const frameworkSelect = mappingDiv.querySelector('.framework-select');
        frameworkSelect.innerHTML = '<option value="">Loading...</option>';
        
        fetch('/admin/frameworks/list?include_global=true', { credentials: 'include' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    frameworkSelect.innerHTML = '<option value="">Select Framework</option>';
                    data.frameworks.forEach(fw => {
                        const option = document.createElement('option');
                        option.value = fw.framework_id;
                        option.textContent = fw.framework_name;
                        frameworkSelect.appendChild(option);
                    });
                    
                    // Apply preselect if present - check both dataset and data attributes
                    const preselectFrameworkId = frameworkSelect.dataset.preselectFramework || 
                                                mappingDiv.getAttribute('data-framework-id');
                    
                    if (preselectFrameworkId) {
                        // Find if the framework exists in the loaded options
                        const foundFramework = data.frameworks.find(fw => fw.framework_id === preselectFrameworkId);
                        
                        if (foundFramework) {
                            frameworkSelect.value = preselectFrameworkId;
                            
                            // Trigger change event to load fields
                            const changeEvent = new Event('change');
                            frameworkSelect.dispatchEvent(changeEvent);
                        } else {
                            console.error('Framework not found in loaded frameworks:', preselectFrameworkId);
                        }
                        
                        // Clean up dataset
                        delete frameworkSelect.dataset.preselectFramework;
                    }
                } else {
                    console.error('Failed to load frameworks:', data);
                    frameworkSelect.innerHTML = '<option value="">Error loading frameworks</option>';
                }
            })
            .catch(error => {
                console.error('Error loading frameworks:', error);
                frameworkSelect.innerHTML = '<option value="">Error loading frameworks</option>';
            });
    }
    
    function loadFieldsForFramework(frameworkId, fieldSelect) {
        fieldSelect.innerHTML = '<option value="">Loading...</option>';
        fieldSelect.disabled = true;
        
        fetch(`/admin/frameworks/${frameworkId}/data_points`, { credentials: 'include' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    fieldSelect.innerHTML = '<option value="">Select Field</option>';
                    data.data_points.forEach(field => {
                        const option = document.createElement('option');
                        option.value = field.field_id;
                        option.textContent = field.field_name;
                        fieldSelect.appendChild(option);
                    });
                    fieldSelect.disabled = false;

                    // Check for preselection from multiple sources
                    const mappingDiv = fieldSelect.closest('.raw-field-mapping');
                    const preselectFieldId = fieldSelect.dataset.preselectField || 
                                           (mappingDiv ? mappingDiv.getAttribute('data-field-id') : null);

                    if (preselectFieldId) {
                        // Find if the field exists in the loaded options
                        const foundField = data.data_points.find(field => field.field_id === preselectFieldId);
                        
                        if (foundField) {
                            fieldSelect.value = preselectFieldId;
                        } else {
                            console.error('Field not found in loaded fields:', preselectFieldId);
                        }
                        
                        // Clean up dataset
                        delete fieldSelect.dataset.preselectField;
                    }
                } else {
                    console.error('Failed to load fields:', data);
                    fieldSelect.innerHTML = '<option value="">Error loading fields</option>';
                }
            })
            .catch(error => {
                console.error('Error loading fields:', error);
                fieldSelect.innerHTML = '<option value="">Error loading fields</option>';
            });
    }
    
    function loadAvailableDimensionsForFilter(mappingDiv) {
        // Use the same availableDimensions array from dimensions module
        if (window.FrameworksDimensions && window.FrameworksDimensions.getAvailableDimensions) {
            availableDimensions = window.FrameworksDimensions.getAvailableDimensions();
        }
        
        if (availableDimensions.length === 0) {
            // Load dimensions if not available
            fetch('/admin/dimensions')
                .then(response => response.json())
                .then(data => {
                    availableDimensions = data.dimensions || [];
                })
                .catch(error => {
                    availableDimensions = [];
                });
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

    // Public API
    return {
        initialize: function() {
            loadAvailableDimensionsForFilter();
        },
        
        // Core functions
        addRowEventListeners: addRowEventListeners,
        addRawFieldMapping: addRawFieldMapping,
        setupMappingEventListeners: setupMappingEventListeners,
        loadFrameworksForMapping: loadFrameworksForMapping,
        loadFieldsForFramework: loadFieldsForFramework,
        loadAvailableDimensionsForFilter: loadAvailableDimensionsForFilter,
        addDimensionFilterRule: addDimensionFilterRule,
        
        // Utility functions
        setAvailableDimensions: function(dimensions) {
            availableDimensions = dimensions;
        },
        
        getAvailableDimensions: function() {
            return availableDimensions;
        },
        
        refresh: function() {
            loadAvailableDimensionsForFilter();
        },
        
        isReady: function() {
            return true;
        }
    };
})(); 