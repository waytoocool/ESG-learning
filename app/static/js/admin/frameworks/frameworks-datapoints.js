/**
 * Frameworks Data Points Module - Clean Implementation
 * Extracted from original frameworks.js without over-engineering
 * Enhanced with wizard support and improved patterns
 * Enhanced with wizard support and improved patterns
 */

window.FrameworksDataPoints = (function() {
    'use strict';

    // Private variables
    let dataPoints = [];
    let editingDataPointIndex = -1;
    let currentContext = null; // 'wizard' or 'standalone'
    let wizardState = null; // Reference to the wizard state object
    let tempDimensionsForNewDataPoint = []; // Store dimensions for new data points before saving

    // DOM elements - cached on initialize
    let elements = {};

    // Public API
    return {
        /**
         * Initialize the data points module
         */
        initialize: function() {
            console.log('FrameworksDataPoints: Initializing clean module...');
            this.cacheElements();
            this.setupEventListeners();
            this.detectContext();
            console.log('FrameworksDataPoints: Initialized successfully');
        },

        /**
         * Cache DOM elements
         */
        cacheElements: function() {
            elements = {
                // Drawer elements
                dataPointDrawer: document.getElementById('dataPointDrawer'),
                drawerOverlay: document.getElementById('drawerOverlay'),
                closeDrawerBtn: document.getElementById('closeDrawer'),
                cancelDataPointBtn: document.getElementById('cancelDataPoint'),
                saveDataPointBtn: document.getElementById('saveDataPoint'),
                dataPointForm: document.getElementById('dataPointForm'),
                drawerTitle: document.getElementById('drawerTitle'),
                
                // Container elements (context-dependent)
                dataPointsContainer: document.getElementById('dataPointsContainer'),
                dataPointsWizardContainer: document.getElementById('dataPointsWizardContainer'),
                emptyState: document.getElementById('emptyDataPointsState'),
                emptyWizardState: document.getElementById('emptyDataPointsWizardState'),
                
                // Add buttons (context-dependent)
                addDataPointBtn: document.getElementById('addDataPoint'),
                addDataPointWizardBtn: document.getElementById('addDataPointWizard'),
                
                // Form elements
                formulaSection: document.getElementById('formulaSection'),
                dpComputedCheckbox: document.getElementById('dpComputed'),
                dpFieldCodeInput: document.getElementById('dpFieldCode'),
                manageDimensionsBtn: document.getElementById('manageDimensionsBtn')
            };
        },

        /**
         * Detect current context (framework vs wizard)
         */
        detectContext: function() {
            if (window.editMode !== undefined || elements.addDataPointWizardBtn || window.frameworkWizardState) {
                currentContext = 'wizard';
                if (window.frameworkWizardState) {
                    wizardState = window.frameworkWizardState;
                    dataPoints = wizardState.formData.dataPoints || [];
                }
            } else {
                currentContext = 'framework';
            }
            console.log('FrameworksDataPoints: Context detected -', currentContext);
        },

        /**
         * Setup event listeners
         */
        setupEventListeners: function() {
            // Add data point buttons (context-dependent)
            if (elements.addDataPointBtn) {
                elements.addDataPointBtn.addEventListener('click', async () => await this.openDataPointDrawer());
            }
            if (elements.addDataPointWizardBtn) {
                elements.addDataPointWizardBtn.addEventListener('click', async () => await this.openDataPointDrawer());
            }
            
            if (elements.closeDrawerBtn) {
                elements.closeDrawerBtn.addEventListener('click', () => this.closeDataPointDrawer());
            }
            
            if (elements.cancelDataPointBtn) {
                elements.cancelDataPointBtn.addEventListener('click', () => this.closeDataPointDrawer());
            }
            
            if (elements.drawerOverlay) {
                elements.drawerOverlay.addEventListener('click', () => this.closeDataPointDrawer());
            }

            // Add Escape key listener to close drawer
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && elements.dataPointDrawer && elements.dataPointDrawer.classList.contains('open')) {
                    this.closeDataPointDrawer();
                }
            });

            if (elements.saveDataPointBtn) {
                elements.saveDataPointBtn.addEventListener('click', () => this.saveDataPoint());
            }

            if (elements.manageDimensionsBtn) {
                elements.manageDimensionsBtn.addEventListener('click', () => {
                    if (window.FrameworksDimensions) {
                        // Pass the current data point's dimensions to the dimension module
                        const currentDimensions = editingDataPointIndex >= 0 ? dataPoints[editingDataPointIndex].dimensions : [];
                        window.FrameworksDimensions.openDrawerDimensionModal(currentDimensions, (updatedDimensions) => {
                            // Callback to update the data point with new dimensions
                            if (editingDataPointIndex >= 0) {
                                dataPoints[editingDataPointIndex].dimensions = updatedDimensions;
                            } else {
                                // For new data points, store dimensions temporarily
                                tempDimensionsForNewDataPoint = updatedDimensions;
                            }
                            this.updateDrawerDimensionSummary(updatedDimensions);
                        });
                    }
                });
            }

            // === NEW: Toggle formula inputs for computed fields ===
            if (elements.dpComputedCheckbox && elements.formulaSection) {
                elements.dpComputedCheckbox.addEventListener('change', () => {
                    if (elements.dpComputedCheckbox.checked) {
                        elements.formulaSection.style.display = 'block';
                        // Initialize variable mapping UI for new computed field
                        setTimeout(() => {
                            this.initVariableMappingUI();
                        }, 100); // Small delay to ensure DOM is ready
                    } else {
                        elements.formulaSection.style.display = 'none';
                        // Clear mappings UI
                        const mappingsContainer = document.getElementById('fieldMappings');
                        if (mappingsContainer) {
                            const rawContainer = mappingsContainer.querySelector('.raw-fields-container');
                            if (rawContainer) rawContainer.innerHTML = '';
                        }
                        const formulaInput = document.getElementById('dpFormula');
                        if (formulaInput) formulaInput.value = '';
                    }
                });
            }
        },

        /**
         * Generate slug from field name - Enhanced version from wizard
         */
        generateSlug: function(fieldName) {
            if (!fieldName) return '';
            // Match backend slug logic (underscores)
            return fieldName.toLowerCase()
                .replace(/[^a-zA-Z0-9\s-]/g, '')
                .replace(/[\s-]+/g, '_')
                .replace(/^_+|_+$/g, '');
        },

        /**
         * Show notification - Enhanced error handling
         */
        showNotification: function(message, type = 'info') {
            if (window.FrameworksCommon && window.FrameworksCommon.showNotification) {
                window.FrameworksCommon.showNotification(message, type);
            } else {
                // Fallback to alert
                alert(message);
            }
        },

        /**
         * Get current container based on context
         */
        getCurrentContainer: function() {
            if (currentContext === 'wizard') {
                return elements.dataPointsWizardContainer || elements.dataPointsContainer;
            }
            return elements.dataPointsContainer;
        },

        /**
         * Get current empty state based on context
         */
        getCurrentEmptyState: function() {
            if (currentContext === 'wizard') {
                return elements.emptyWizardState || elements.emptyState;
            }
            return elements.emptyState;
        },

        /**
         * Open data point drawer
         */
        openDataPointDrawer: async function(dataPointIndex = -1) {
            editingDataPointIndex = dataPointIndex;
            
            if (dataPointIndex >= 0) {
                // Editing existing data point
                elements.drawerTitle.textContent = 'Edit Data Point';
                this.populateDrawerForm(dataPoints[dataPointIndex]);
            } else {
                // Adding new data point
                elements.drawerTitle.textContent = 'Add Data Point';
                this.resetDrawerForm();
                // Clear any previously stored temporary dimensions
                tempDimensionsForNewDataPoint = [];
            }
            
            // Update topic dropdown (await since it may fetch from API)
            await this.updateDrawerTopicDropdown();
            
            // If editing, set the topic value after dropdown is populated
            if (dataPointIndex >= 0 && dataPoints[dataPointIndex].topic_id) {
                const topicSelect = document.getElementById('dpTopic');
                topicSelect.value = dataPoints[dataPointIndex].topic_id;
            }
            
            // Show drawer
            elements.dataPointDrawer.classList.add('open');
            elements.drawerOverlay.classList.add('show');
            document.body.style.overflow = 'hidden';
        },

        /**
         * Close data point drawer
         */
        closeDataPointDrawer: function() {
            elements.dataPointDrawer.classList.remove('open');
            elements.drawerOverlay.classList.remove('show');
            document.body.style.overflow = '';
            this.resetDrawerForm();
            editingDataPointIndex = -1;
            // Clear temporary dimensions when closing drawer
            tempDimensionsForNewDataPoint = [];
        },

        /**
         * Reset drawer form
         */
        resetDrawerForm: function() {
            elements.dataPointForm.reset();
            elements.formulaSection.style.display = 'none';
            elements.dpComputedCheckbox.checked = false;
            
            // Reset auto-generated attribute
            elements.dpFieldCodeInput.removeAttribute('data-auto-generated');
            
            // Reset dimension summary
            const dimensionSummary = document.querySelector('#dataPointDrawer .dimension-summary');
            if (dimensionSummary) {
                dimensionSummary.innerHTML = '<small class="text-muted">No dimensions assigned</small>';
            }
            
            // Reset field mappings
            const fieldMappings = document.getElementById('fieldMappings');
            if (fieldMappings) {
                fieldMappings.innerHTML = '';
            }
        },

        /**
         * Populate drawer form with data point data
         */
        populateDrawerForm: function(dataPoint) {
            document.getElementById('dpName').value = dataPoint.name || '';
            document.getElementById('dpFieldCode').value = dataPoint.field_code || '';
            const vtSelect = document.getElementById('dpValueType');
            let vt = dataPoint.value_type || '';
            if (vt === 'NUMBER') vt = 'Numeric';
            else if (vt === 'TEXT') vt = 'Text';
            else if (vt === 'BOOLEAN') vt = 'Boolean';
            else if (vt === 'DATE') vt = 'Date';
            vtSelect.value = vt;
            document.getElementById('dpUnitCategory').value = dataPoint.unit_category || '';
            document.getElementById('dpDefaultUnit').value = dataPoint.default_unit || '';
            // Note: Topic will be set after dropdown is populated in openDataPointDrawer
            document.getElementById('dpDescription').value = dataPoint.description || '';
            document.getElementById('dpComputed').checked = dataPoint.is_computed || false;
            document.getElementById('dpFormula').value = dataPoint.formula_expression || dataPoint.formula || '';
            
            // Show formula section if computed
            if (dataPoint.is_computed) {
                elements.formulaSection.style.display = 'block';
            }
            
            // Populate dimensions if any
            if (dataPoint.dimensions && dataPoint.dimensions.length > 0) {
                this.updateDrawerDimensionSummary(dataPoint.dimensions);
            }

            // === NEW: Initialize variable mapping UI inside drawer ===
            this.initVariableMappingUI(dataPoint.variable_mappings || []);
        },

        /**
         * Update topic dropdown in drawer
         */
        updateDrawerTopicDropdown: async function() {
            const topicSelect = document.getElementById('dpTopic');
            topicSelect.innerHTML = '<option value="">-- Select Topic --</option>';
            
            // Try to get topics from topics module first
            if (window.FrameworksTopics && window.FrameworksTopics.getAllTopics) {
                const allTopics = window.FrameworksTopics.getAllTopics();
                if (allTopics && allTopics.length > 0) {
                    allTopics.forEach(topic => {
                        if (window.FrameworksTopics.addTopicOptionRecursive) {
                            window.FrameworksTopics.addTopicOptionRecursive(topicSelect, topic, '');
                        }
                    });
                    return;
                }
            }
            
            // If no topics loaded in the module, fetch from API
            const frameworkId = this.getCurrentFrameworkId();
            if (frameworkId) {
                try {
                    const response = await fetch(`/admin/frameworks/${frameworkId}/topics`);
                    const data = await response.json();
                    const topics = Array.isArray(data) ? data : (data.success ? data.topics : []);
                    
                    topics.forEach(topic => {
                        this.addTopicOptionRecursive(topicSelect, topic, '');
                    });
                } catch (error) {
                    console.error('Error loading topics for dropdown:', error);
                }
            }
        },

        /**
         * Get current framework ID for API calls
         */
        getCurrentFrameworkId: function() {
            // Try wizard state first
            if (currentContext === 'wizard' && wizardState && wizardState.formData && wizardState.formData.framework_id) {
                return wizardState.formData.framework_id;
            }
            
            // Try to get from URL or global variables
            if (window.location.pathname.includes('/frameworks/')) {
                const pathParts = window.location.pathname.split('/');
                const frameworkIndex = pathParts.indexOf('frameworks');
                if (frameworkIndex >= 0 && pathParts[frameworkIndex + 1]) {
                    return pathParts[frameworkIndex + 1];
                }
            }
            
            // Try global framework data
            if (window.frameworkData && window.frameworkData.framework_id) {
                return window.frameworkData.framework_id;
            }
            
            return null;
        },

        /**
         * Add topic option recursively (helper for dropdown population)
         */
        addTopicOptionRecursive: function(select, topic, prefix) {
            const option = document.createElement('option');
            option.value = topic.topic_id;
            option.textContent = prefix + topic.name;
            select.appendChild(option);
            
            if (topic.children && topic.children.length > 0) {
                topic.children.forEach(child => {
                    this.addTopicOptionRecursive(select, child, prefix + '  ');
                });
            }
        },

        /**
         * Update dimension summary in drawer
         */
        updateDrawerDimensionSummary: function(dimensions) {
            const dimensionSummary = document.querySelector('#dataPointDrawer .dimension-summary');
            if (dimensions && dimensions.length > 0) {
                const dimensionTags = dimensions.map(dim => 
                    `<span class="dimension-tag">${dim.name}</span>`
                ).join('');
                dimensionSummary.innerHTML = dimensionTags;
            } else {
                dimensionSummary.innerHTML = '<small class="text-muted">No dimensions assigned</small>';
            }
        },

        /**
         * === NEW: Initialize variable mapping UI inside drawer ===
         */
        initVariableMappingUI: function(existingMappings = []) {
            const mappingsContainer = document.getElementById('fieldMappings');
            if (!mappingsContainer) return;

            // Ensure a raw-fields-container exists inside
            let rawFieldsContainer = mappingsContainer.querySelector('.raw-fields-container');
            if (!rawFieldsContainer) {
                rawFieldsContainer = document.createElement('div');
                rawFieldsContainer.className = 'raw-fields-container';
                mappingsContainer.prepend(rawFieldsContainer);
            } else {
                rawFieldsContainer.innerHTML = '';
            }

            const addRawMappingBtn = document.getElementById('addFieldMapping');
            const addEmptyMapping = () => {
                if (window.FrameworksFieldMapping && window.FrameworksFieldMapping.addRawFieldMapping) {
                    const wrapperRow = mappingsContainer.querySelector('.raw-fields-container')?.parentNode || mappingsContainer;
                    window.FrameworksFieldMapping.addRawFieldMapping(wrapperRow, null);
                } else {
                    console.error('FrameworksFieldMapping.addRawFieldMapping not available');
                }
            };

            if (addRawMappingBtn && !addRawMappingBtn.dataset.listenerAttached) {
                addRawMappingBtn.dataset.listenerAttached = 'true';
                addRawMappingBtn.addEventListener('click', addEmptyMapping);
            }

            if (Array.isArray(existingMappings) && existingMappings.length) {
                existingMappings.forEach((map, index) => {
                    // Create mapping with preselect data
                    if (window.FrameworksFieldMapping && window.FrameworksFieldMapping.addRawFieldMapping) {
                        const wrapperRow = mappingsContainer.querySelector('.raw-fields-container')?.parentNode || mappingsContainer;
                        window.FrameworksFieldMapping.addRawFieldMapping(wrapperRow, map);
                    } else {
                        console.error('FrameworksFieldMapping.addRawFieldMapping not available');
                    }
                });
            } else {
                addEmptyMapping();
            }
        },

        /**
         * Collect variable mappings from drawer
         */
        collectVariableMappings: function() {
            const mappingsContainer = document.getElementById('fieldMappings');
            if (!mappingsContainer) {
                // No UI container, fall back to original data if editing
                if (editingDataPointIndex >= 0 && dataPoints[editingDataPointIndex] && dataPoints[editingDataPointIndex].variable_mappings) {
                    return dataPoints[editingDataPointIndex].variable_mappings;
                }
                return [];
            }
            
            const mappingDivs = mappingsContainer.querySelectorAll('.raw-field-mapping');
            const mappings = [];
            mappingDivs.forEach(div => {
                const variable = div.querySelector('.variable-input')?.value?.trim().toUpperCase();
                const frameworkId = div.querySelector('.framework-select')?.value;
                const fieldId = div.querySelector('.field-select')?.value;
                const coefficient = parseFloat(div.querySelector('.coefficient-input')?.value) || 1;
                if (variable && fieldId) {
                    mappings.push({
                        variable_name: variable,
                        raw_field_id: fieldId,
                        coefficient: coefficient,
                        framework_id: frameworkId
                    });
                }
            });
            
            // If no mappings found in UI but we're editing, fall back to original data
            if (mappings.length === 0 && editingDataPointIndex >= 0 && dataPoints[editingDataPointIndex] && dataPoints[editingDataPointIndex].variable_mappings) {
                return dataPoints[editingDataPointIndex].variable_mappings;
            }
            
            return mappings;
        },

        /**
         * Collect dimensions from dimension management
         */
        collectDimensions: function() {
            // Try to get dimensions from the current editing data point
            if (editingDataPointIndex >= 0 && dataPoints[editingDataPointIndex] && dataPoints[editingDataPointIndex].dimensions) {
                console.log('collectDimensions: Using dimensions from existing data point:', dataPoints[editingDataPointIndex].dimensions);
                return dataPoints[editingDataPointIndex].dimensions;
            }
            
            // For new data points, return temporarily stored dimensions
            if (editingDataPointIndex < 0 && tempDimensionsForNewDataPoint.length > 0) {
                console.log('collectDimensions: Using temporary dimensions for new data point:', tempDimensionsForNewDataPoint);
                return tempDimensionsForNewDataPoint;
            }
            
            // If no dimensions in current data, return empty array
            console.log('collectDimensions: No dimensions found, returning empty array');
            return [];
        },

        /**
         * Save data point - Enhanced with context separation
         */
        saveDataPoint: async function() {
            // Validate required fields
            const name = document.getElementById('dpName').value.trim();
            const valueType = document.getElementById('dpValueType').value;
            
            if (!name) {
                this.showNotification('Data point name is required', 'error');
                return;
            }
            
            if (!valueType) {
                this.showNotification('Value type is required', 'error');
                return;
            }
            
            // Normalize value type to match backend enum
            let normalizedValueType = valueType.toUpperCase();
            if (normalizedValueType === 'NUMERIC' || normalizedValueType === 'NUMBERIC') {
                normalizedValueType = 'NUMBER';
            } else if (normalizedValueType === 'TEXT') {
                normalizedValueType = 'TEXT';
            } else if (normalizedValueType === 'BOOLEAN') {
                normalizedValueType = 'BOOLEAN';
            } else if (normalizedValueType === 'DATE') {
                normalizedValueType = 'DATE';
            }
            
            // Collect dimensions and variable mappings
            const collectedDimensions = this.collectDimensions();
            const collectedMappings = this.collectVariableMappings();
            
            // Create data point object
            const dataPoint = {
                name: name,
                field_code: document.getElementById('dpFieldCode').value.trim() || this.generateSlug(name),
                value_type: normalizedValueType,
                unit_category: document.getElementById('dpUnitCategory').value,
                default_unit: document.getElementById('dpDefaultUnit').value.trim(),
                topic_id: document.getElementById('dpTopic').value,
                description: document.getElementById('dpDescription').value.trim(),
                is_computed: document.getElementById('dpComputed').checked,
                formula_expression: document.getElementById('dpFormula').value.trim(), // Changed from 'formula' to 'formula_expression'
                dimensions: collectedDimensions, // Collect dimensions from management UI
                variable_mappings: collectedMappings, // Collect variable mappings
                // id: editingDataPointIndex >= 0 ? dataPoints[editingDataPointIndex].id : Date.now() // ID will be from backend
            };

            // If editing, include the existing field_id
            if (editingDataPointIndex >= 0 && dataPoints[editingDataPointIndex].field_id) {
                dataPoint.field_id = dataPoints[editingDataPointIndex].field_id;
            }
            
            // Duplicate field_code check within current working set
            const normCode = dataPoint.field_code.toLowerCase();
            const duplicate = dataPoints.find((dp, idx) => idx !== editingDataPointIndex && dp.field_code.toLowerCase() === normCode);
            if (duplicate) {
                this.showNotification('Field code already exists in this framework: ' + dataPoint.field_code, 'error');
                return;
            }
            
            // Save based on context
            if (currentContext === 'wizard') {
                if (!wizardState || !wizardState.formData || !wizardState.formData.framework_id) {
                    this.showNotification('Framework not yet saved. Please save framework basics first.', 'error');
                    return;
                }
                const frameworkId = wizardState.formData.framework_id;
                try {
                    const url = editingDataPointIndex >= 0 ? `/admin/frameworks/${frameworkId}/data_points/${dataPoint.field_id}` : `/admin/frameworks/add_data_points/${frameworkId}`;
                    const method = editingDataPointIndex >= 0 ? 'PUT' : 'POST';
                    const body = editingDataPointIndex >= 0 ? JSON.stringify(dataPoint) : JSON.stringify([dataPoint]);

                    const response = await fetch(url, {
                        method: method,
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: body
                    });
                    const data = await response.json();
                    if (data.success) {
                        this.showNotification(`Data point ${editingDataPointIndex >= 0 ? 'updated' : 'added'} successfully`, 'success');
                        // For new data points, clear temporary dimensions after successful save
                        if (editingDataPointIndex < 0) {
                            tempDimensionsForNewDataPoint = [];
                        }
                        // Re-fetch all data points to ensure local state is in sync with DB
                        await this.fetchDataPoints(frameworkId);
                        // Close drawer after successful save
                        this.closeDataPointDrawer();
                    } else {
                        this.showNotification(`Error saving data point: ${data.error || 'Unknown error'}`, 'error');
                    }
                } catch (error) {
                    console.error('Error saving data point:', error);
                    this.showNotification('Error saving data point.', 'error');
                }
            } else { // Existing framework context (not wizard)
                // This part would need a separate API for updating/adding single data points
                // For now, we'll keep the local array update for non-wizard context
                if (editingDataPointIndex >= 0) {
                    dataPoints[editingDataPointIndex] = dataPoint;
                } else {
                    dataPoints.push(dataPoint);
                }
                this.showNotification(`Data point ${editingDataPointIndex >= 0 ? 'updated' : 'added'} successfully`, 'success');
            }
            
            // Refresh display and close drawer
            this.renderDataPointCards();
            this.closeDataPointDrawer();
        },

        /**
         * Fetch data points from the backend and update local state.
         */
        fetchDataPoints: async function(frameworkId) {
            try {
                const response = await fetch(`/admin/frameworks/${frameworkId}/data_points`);
                const data = await response.json();
                if (data.success) {
                    dataPoints = data.data_points.map(field => ({
                        id: field.field_id, // Use field_id as the unique ID
                        field_id: field.field_id,
                        name: field.field_name,
                        field_code: field.field_code,
                        description: field.description,
                        value_type: field.value_type,
                        unit_category: field.unit_category,
                        default_unit: field.default_unit,
                        topic_id: field.topic_id,
                        is_computed: field.is_computed,
                        formula_expression: field.formula_expression,
                        formula: field.formula_expression, // Alias for backward compatibility
                        topic_name: field.topic_name, // Include topic_name for display
                        dimensions: field.dimensions || [], // Include dimensions array
                        variable_mappings: field.variable_mappings || [] // Include variable mappings
                    }));
                    if (currentContext === 'wizard' && wizardState) {
                        wizardState.formData.dataPoints = dataPoints;
                    }
                    this.renderDataPointCards();
                } else {
                    console.error('Error fetching data points:', data.error);
                    this.showNotification('Error loading data points.', 'error');
                }
            } catch (error) {
                console.error('Error fetching data points:', error);
                this.showNotification('Error loading data points.', 'error');
            }
        },

        

        /**
         * Render data point cards
         */
        renderDataPointCards: function() {
            const container = this.getCurrentContainer();
            const emptyState = this.getCurrentEmptyState();
            
            if (!container || !emptyState) return;
            
            if (dataPoints.length === 0) {
                emptyState.style.display = 'block';
                return;
            }
            
            emptyState.style.display = 'none';
            
            const cardsHtml = dataPoints.map((dataPoint, index) => {
                const badges = [];
                
                if (dataPoint.value_type) {
                    badges.push(`<span class="data-point-badge badge-type">${dataPoint.value_type}</span>`);
                }
                
                if (dataPoint.unit_category) {
                    badges.push(`<span class="data-point-badge badge-unit">${dataPoint.unit_category}</span>`);
                }
                
                if (dataPoint.is_computed) {
                    badges.push(`<span class="data-point-badge badge-computed">Computed</span>`);
                }
                
                if (dataPoint.topic_name) {
                    badges.push(`<span class="data-point-badge badge-topic">${dataPoint.topic_name}</span>`);
                }
                
                return `
                    <div class="data-point-card" data-index="${index}">
                        <div class="data-point-card-header">
                            <h6 class="data-point-card-title">${dataPoint.name}</h6>
                            <span class="data-point-card-code">${dataPoint.field_code}</span>
                        </div>
                        <div class="data-point-card-meta">
                            ${badges.join('')}
                        </div>
                        ${dataPoint.description ? `<div class="data-point-card-description">${dataPoint.description}</div>` : ''}
                        <div class="data-point-card-actions">
                            <button type="button" class="btn btn-sm btn-outline-primary edit-data-point" data-index="${index}">
                                <i class="fas fa-edit"></i> Edit
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-danger delete-data-point" data-index="${index}">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        </div>
                    </div>
                `;
            }).join('');

            container.innerHTML = cardsHtml;
            
            // Add event listeners to cards
            this.addDataPointCardListeners();
        },

        /**
         * Add event listeners to data point cards
         */
        addDataPointCardListeners: function() {
            // Edit buttons
            document.querySelectorAll('.edit-data-point').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const index = parseInt(btn.getAttribute('data-index'));
                    await this.openDataPointDrawer(index);
                });
            });
            
            // Delete buttons
            document.querySelectorAll('.delete-data-point').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const index = parseInt(btn.getAttribute('data-index'));
                    if (confirm('Are you sure you want to delete this data point?')) {
                        this.deleteDataPoint(index);
                    }
                });
            });
            
            // Card click to edit
            document.querySelectorAll('.data-point-card').forEach(card => {
                card.addEventListener('click', async () => {
                    const index = parseInt(card.getAttribute('data-index'));
                    await this.openDataPointDrawer(index);
                });
            });
        },

        /**
         * Delete data point - Enhanced with context support
         */
        deleteDataPoint: async function(index) {
            const dataPointToDelete = dataPoints[index];
            if (!dataPointToDelete || !dataPointToDelete.field_id) {
                this.showNotification('Error: Data point not found or has no ID.', 'error');
                return;
            }

            if (currentContext === 'wizard' && wizardState && wizardState.formData.framework_id) {
                const frameworkId = wizardState.formData.framework_id;
                try {
                    const response = await fetch(`/admin/frameworks/${frameworkId}/data_points/${dataPointToDelete.field_id}`, {
                        method: 'DELETE'
                    });
                    const data = await response.json();
                    if (data.success) {
                        this.showNotification('Data point deleted successfully', 'success');
                        // Re-fetch all data points to ensure local state is in sync with DB
                        await this.fetchDataPoints(frameworkId);
                    } else {
                        this.showNotification(`Error deleting data point: ${data.error || 'Unknown error'}`, 'error');
                    }
                } catch (error) {
                    console.error('Error deleting data point:', error);
                    this.showNotification('Error deleting data point.', 'error');
                }
            } else { // Existing framework context (not wizard)
                // This part would need a separate API for deleting single data points
                // For now, we'll keep the local array update for non-wizard context
                dataPoints.splice(index, 1);
                this.showNotification('Data point deleted successfully', 'success');
            }
            
            this.renderDataPointCards();
        },

        /**
         * Load unit options for unit category
         */
        loadUnitOptionsForDrawer: function(unitCategory, unitInput) {
            if (!unitCategory) {
                unitInput.placeholder = 'Enter custom unit';
                return;
            }
            
            fetch(`/admin/unit_categories`)
                .then(response => response.json())
                .then(data => {
                    const categoryUnits = data[unitCategory] || [];
                    const datalist = document.createElement('datalist');
                    datalist.id = `drawer-units-${Date.now()}`;
                    
                    categoryUnits.forEach(unit => {
                        const option = document.createElement('option');
                        option.value = unit;
                        datalist.appendChild(option);
                    });
                    
                    // Remove existing datalist if any
                    const existingDatalist = document.querySelector(`#${unitInput.getAttribute('list')}`);
                    if (existingDatalist) {
                        existingDatalist.remove();
                    }
                    
                    unitInput.setAttribute('list', datalist.id);
                    unitInput.placeholder = `e.g., ${categoryUnits.slice(0, 3).join(', ')}`;
                    document.body.appendChild(datalist);
                })
                .catch(error => console.error('Error loading unit options:', error));
        },

        // === WIZARD-SPECIFIC FUNCTIONS (Category 2) ===

        /**
         * Import template data points - Enhanced version from wizard
         */
        importTemplate: function(templateKey) {
            // Show loading state
            const importBtn = document.querySelector(`[data-template="${templateKey}"]`);
            if (!importBtn) return;
            
            const originalText = importBtn.textContent;
            importBtn.textContent = 'Importing...';
            importBtn.disabled = true;
            
            fetch('/admin/import_template', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ template_key: templateKey })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.data_points) {
                    // Add imported data points
                    data.data_points.forEach(dp => {
                        dp.id = Date.now() + Math.random();
                        if (currentContext === 'wizard' && wizardState) {
                            wizardState.formData.dataPoints.push(dp);
                            dataPoints = wizardState.formData.dataPoints;
                        } else {
                            dataPoints.push(dp);
                        }
                    });
                    
                    this.renderDataPointCards();
                    this.showNotification(`Successfully imported ${data.data_points.length} data points from ${templateKey.toUpperCase()}`, 'success');
                } else {
                    this.showNotification('Error importing template: ' + (data.error || 'Unknown error'), 'error');
                }
            })
            .catch(error => {
                console.error('Import error:', error);
                this.showNotification('Error importing template', 'error');
            })
            .finally(() => {
                importBtn.textContent = originalText;
                importBtn.disabled = false;
            });
        },

        /**
         * Toggle data points view (wizard-specific)
         */
        toggleDataPointsView: function(view) {
            const container = this.getCurrentContainer();
            if (!container) return;
            
            if (view === 'list') {
                container.classList.add('list-view');
            } else {
                container.classList.remove('list-view');
            }
        },

        /**
         * Validate data points step (wizard-specific)
         */
        validateDataPointsStep: function() {
            if (dataPoints.length === 0) {
                this.showNotification('Please add at least one data point to your framework', 'error');
                return false;
            }
            return true;
        },

        // === PUBLIC API METHODS ===

        /**
         * Set context for the module
         */
        setContext: function(context, state = null) {
            currentContext = context;
            if (context === 'wizard' && state) {
                wizardState = state;
                dataPoints = state.formData.dataPoints || [];
            }
        },

        /**
         * Get all data points
         */
        getDataPoints: function() {
            return dataPoints;
        },

        /**
         * Set data points (for external updates)
         */
        setDataPoints: async function(newDataPoints) {
            // If in wizard context and framework_id is available, fetch from backend
            if (currentContext === 'wizard' && wizardState && wizardState.formData.framework_id) {
                await this.fetchDataPoints(wizardState.formData.framework_id);
            } else {
                dataPoints = newDataPoints || [];
                this.renderDataPointCards();
            }
        },

        /**
         * Refresh data points display
         */
        refresh: function() {
            this.renderDataPointCards();
        },

        /**
         * Check if module is ready
         */
        isReady: function() {
            return elements.dataPointDrawer !== null;
        }
    };
})();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.FrameworksDataPoints) {
        window.FrameworksDataPoints.initialize();
    }
}); 