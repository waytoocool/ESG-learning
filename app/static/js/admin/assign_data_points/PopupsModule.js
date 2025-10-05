/**
 * PopupsModule - Centralized Modal Management for Assign Data Points
 * Phase 6: Extracted from assign_data_points_redesigned_v2.js
 *
 * Manages all modal dialogs including:
 * - Configuration Modal (frequency, unit, topic assignment)
 * - Entity Assignment Modal (hierarchical and flat entity selection)
 * - Field Information Modal (detailed field metadata and dependencies)
 * - Conflict Resolution Modal (configuration conflict handling)
 * - Confirmation Dialogs (generic and specific confirmations)
 * - Import Validation Modal (CSV import preview and validation)
 *
 * Dependencies:
 * - window.AppEvents (global event system)
 * - window.AppState (global state management)
 * - window.ServicesModule (API calls)
 * - Bootstrap 5 Modal
 */

(function() {
    'use strict';

    const PopupsModule = {
        // ===========================
        // STATE MANAGEMENT
        // ===========================

        state: {
            activeModal: null,
            modalStack: [],
            currentModalData: {},
            originalConfigurationState: null,
            currentConflicts: null,
            currentConflictConfig: null,
            currentFieldInfoId: null,
            // BUG FIX #2: Track selected entities in modal
            selectedEntities: new Set()
        },

        // ===========================
        // DOM REFERENCES
        // ===========================

        elements: {
            // Configuration Modal
            configurationModal: null,
            configPointCount: null,
            modalFrequency: null,
            modalUnitOverrideSelect: null,
            modalTopicSelect: null,
            modalCollectionMethod: null,
            modalValidationRules: null,
            modalApprovalRequired: null,
            unitOverrideToggle: null,
            materialTopicToggle: null,
            configChangeSummary: null,

            // Entity Assignment Modal
            entityModal: null,
            entityPointCount: null,
            modalAvailableEntities: null,
            modalSelectedEntities: null,
            modalSelectedEntitiesCount: null,
            entityHierarchyContainer: null,

            // Field Information Modal
            fieldInfoModal: null,
            fieldInfoName: null,
            fieldInfoType: null,
            fieldInfoTopic: null,
            fieldInfoFramework: null,
            fieldInfoUnitCategory: null,
            fieldInfoDefaultUnit: null,
            fieldInfoComputedIndicator: null,
            fieldInfoDescription: null,
            fieldInfoDescriptionText: null,
            fieldInfoComputedDetails: null,
            fieldInfoFormula: null,
            fieldInfoDependencies: null,
            fieldInfoTreeInfo: null,
            fieldInfoConflicts: null,
            fieldInfoConflictList: null,

            // Conflict Resolution Modal
            conflictResolutionModal: null,
            conflictsList: null,
            autoResolveConflicts: null,
            forceApplyConfiguration: null,

            // Import Validation Modal
            importValidationModal: null
        },

        // ===========================
        // INITIALIZATION
        // ===========================

        /**
         * Initialize the PopupsModule
         */
        init() {
            console.log('[PopupsModule] Initializing...');

            this.cacheElements();
            this.bindEvents();
            this.setupEventListeners();
            this.loadMaterialTopics(); // Load company-level material topics

            console.log('[PopupsModule] Initialized successfully');
            window.AppEvents.emit('popups-module-initialized');
        },

        /**
         * Load material topics from API and populate dropdown
         */
        async loadMaterialTopics() {
            console.log('[PopupsModule] Loading material topics...');

            try {
                const response = await window.ServicesModule.loadCompanyTopics();

                if (response && response.topics) {
                    this.populateTopicsDropdown(response.topics);
                    console.log('[PopupsModule] Loaded', response.topics.length, 'material topics');
                } else {
                    console.warn('[PopupsModule] No topics returned from API');
                }
            } catch (error) {
                console.error('[PopupsModule] Error loading material topics:', error);
            }
        },

        /**
         * Populate the topics dropdown with loaded topics
         */
        populateTopicsDropdown(topics) {
            const topicSelect = this.elements.modalTopicSelect;
            if (!topicSelect) {
                console.warn('[PopupsModule] Topic select element not found');
                return;
            }

            // Clear existing options except the placeholder and separator
            while (topicSelect.options.length > 2) {
                topicSelect.remove(2);
            }

            // Add topics to dropdown
            topics.forEach(topic => {
                const option = document.createElement('option');
                option.value = topic.topic_id;
                option.textContent = topic.name;
                topicSelect.appendChild(option);
            });

            console.log('[PopupsModule] Populated', topics.length, 'topics into dropdown');
        },

        /**
         * Cache all DOM element references
         */
        cacheElements() {
            console.log('[PopupsModule] Caching DOM elements...');

            // Configuration Modal elements
            this.elements.configurationModal = document.getElementById('configurationModal');
            this.elements.configPointCount = document.getElementById('configPointCount');
            this.elements.modalFrequency = document.getElementById('modalFrequency');
            this.elements.modalUnitOverrideSelect = document.getElementById('modalUnitOverrideSelect');
            this.elements.modalTopicSelect = document.getElementById('modalTopicSelect');
            this.elements.modalCollectionMethod = document.getElementById('modalCollectionMethod');
            this.elements.modalValidationRules = document.getElementById('modalValidationRules');
            this.elements.modalApprovalRequired = document.getElementById('modalApprovalRequired');
            this.elements.unitOverrideToggle = document.getElementById('unitOverrideToggle');
            this.elements.materialTopicToggle = document.getElementById('materialTopicToggle');
            this.elements.configChangeSummary = document.getElementById('configChangeSummary');

            // Entity Assignment Modal elements
            this.elements.entityModal = document.getElementById('entityModal');
            this.elements.entityPointCount = document.getElementById('entityPointCount');
            this.elements.modalAvailableEntities = document.getElementById('modalAvailableEntities');
            this.elements.modalSelectedEntities = document.getElementById('modalSelectedEntities');
            this.elements.modalSelectedEntitiesCount = document.getElementById('modalSelectedEntitiesCount');
            this.elements.entityHierarchyContainer = document.getElementById('entityHierarchyContainer');

            // Field Information Modal elements
            this.elements.fieldInfoModal = document.getElementById('fieldInfoModal');
            this.elements.fieldInfoName = document.getElementById('fieldInfoName');
            this.elements.fieldInfoType = document.getElementById('fieldInfoType');
            this.elements.fieldInfoTopic = document.getElementById('fieldInfoTopic');
            this.elements.fieldInfoFramework = document.getElementById('fieldInfoFramework');
            this.elements.fieldInfoUnitCategory = document.getElementById('fieldInfoUnitCategory');
            this.elements.fieldInfoDefaultUnit = document.getElementById('fieldInfoDefaultUnit');
            this.elements.fieldInfoComputedIndicator = document.getElementById('fieldInfoComputedIndicator');
            this.elements.fieldInfoDescription = document.getElementById('fieldInfoDescription');
            this.elements.fieldInfoDescriptionText = document.getElementById('fieldInfoDescriptionText');
            this.elements.fieldInfoComputedDetails = document.getElementById('fieldInfoComputedDetails');
            this.elements.fieldInfoFormula = document.getElementById('fieldInfoFormula');
            this.elements.fieldInfoDependencies = document.getElementById('fieldInfoDependencies');
            this.elements.fieldInfoTreeInfo = document.getElementById('fieldInfoTreeInfo');
            this.elements.fieldInfoConflicts = document.getElementById('fieldInfoConflicts');
            this.elements.fieldInfoConflictList = document.getElementById('fieldInfoConflictList');

            // Conflict Resolution Modal elements
            this.elements.conflictResolutionModal = document.getElementById('conflictResolutionModal');
            this.elements.conflictsList = document.getElementById('conflictsList');
            this.elements.autoResolveConflicts = document.getElementById('autoResolveConflicts');
            this.elements.forceApplyConfiguration = document.getElementById('forceApplyConfiguration');

            // Import Validation Modal
            this.elements.importValidationModal = document.getElementById('importValidationModal');

            console.log('[PopupsModule] DOM elements cached');
        },

        /**
         * Bind event handlers to DOM elements
         */
        bindEvents() {
            console.log('[PopupsModule] Binding events...');

            // Configuration Modal toggles
            if (this.elements.unitOverrideToggle) {
                this.elements.unitOverrideToggle.addEventListener('change', (e) => {
                    this.handleUnitOverrideToggle(e);
                });
            }

            if (this.elements.materialTopicToggle) {
                this.elements.materialTopicToggle.addEventListener('change', (e) => {
                    this.handleMaterialTopicToggle(e);
                });
            }

            // BUG FIX #3: Add Apply Configuration button event listener
            const applyConfigButton = document.getElementById('applyConfiguration');
            if (applyConfigButton) {
                applyConfigButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    console.log('[PopupsModule] Apply Configuration button clicked');
                    this.handleApplyConfiguration();
                });
                console.log('[PopupsModule] Apply Configuration button listener attached');
            } else {
                console.error('[PopupsModule] Apply Configuration button not found (#applyConfiguration)');
            }

            // BUG FIX #2: Add Apply Entity Assignment button event listener
            const applyEntityButton = document.getElementById('applyEntityAssignment');
            if (applyEntityButton) {
                applyEntityButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    console.log('[PopupsModule] Apply Entity Assignment button clicked');
                    this.handleApplyEntityAssignment();
                });
                console.log('[PopupsModule] Apply Entity Assignment button listener attached');
            } else {
                console.error('[PopupsModule] Apply Entity Assignment button not found (#applyEntityAssignment)');
            }

            // Conflict Resolution Modal buttons
            if (this.elements.autoResolveConflicts) {
                this.elements.autoResolveConflicts.addEventListener('click', () => {
                    this.autoResolveConflicts();
                });
            }

            if (this.elements.forceApplyConfiguration) {
                this.elements.forceApplyConfiguration.addEventListener('click', () => {
                    this.forceApplyConfiguration();
                });
            }

            // BUG FIX #1: Global Escape key handler for all modals
            document.addEventListener('keydown', (e) => {
                // Check if Escape key was pressed
                if (e.key === 'Escape' || e.keyCode === 27) {
                    this.handleEscapeKey();
                }
            });

            console.log('[PopupsModule] Events bound');
        },

        /**
         * Setup AppEvents listeners
         */
        setupEventListeners() {
            console.log('[PopupsModule] Setting up AppEvents listeners...');

            // Listen for toolbar actions
            window.AppEvents.on('toolbar-configure-clicked', (data) => {
                this.showConfigurationModal(null, data.selectedCount);
            });

            window.AppEvents.on('toolbar-assign-clicked', (data) => {
                this.showEntityAssignmentModal(null, data.selectedCount);
            });

            // Listen for field info requests
            window.AppEvents.on('show-field-info', (data) => {
                this.showFieldInformationModal(data.fieldId);
            });

            // Listen for configuration save requests
            window.AppEvents.on('save-configuration', (data) => {
                this.saveConfiguration(data);
            });

            // Listen for entity assignment save requests
            window.AppEvents.on('save-entity-assignments', (data) => {
                this.saveEntityAssignments(data);
            });

            // BUG FIX #2: Listen for entity toggle requests and handle entity selection
            window.AppEvents.on('entity-toggle-requested', (data) => {
                this.handleEntityToggle(data.entityId);
            });

            // Listen for single item configure button clicks
            window.AppEvents.on('configure-single-clicked', (data) => {
                this.handleSingleConfigure(data.fieldId, data.itemData);
            });

            // Listen for single item assign entity button clicks
            window.AppEvents.on('assign-single-clicked', (data) => {
                this.handleSingleAssign(data.fieldId, data.itemData);
            });

            console.log('[PopupsModule] AppEvents listeners setup complete');
        },

        // ===========================
        // CONFIGURATION MODAL
        // ===========================

        /**
         * Show Configuration Modal for selected data points
         */
        showConfigurationModal(dataPoints, selectedCount) {
            console.log('[PopupsModule] Opening Configuration Modal');

            // Get current selected points from AppState if not provided
            const currentSelectedPoints = dataPoints || window.AppState.selectedDataPoints;

            if (!currentSelectedPoints || currentSelectedPoints.size === 0) {
                this.showWarning('Please select data points to configure');
                return;
            }

            // Use the provided selectedCount from the event, otherwise fallback to AppState size
            const displayCount = selectedCount !== undefined ? selectedCount : currentSelectedPoints.size;

            // Update modal count
            if (this.elements.configPointCount) {
                this.elements.configPointCount.textContent = displayCount;
            }

            // Analyze current configurations and populate modal intelligently
            this.analyzeCurrentConfigurations(currentSelectedPoints);

            // Initialize toggle states
            this.initializeModalToggles();

            // Show modal using Bootstrap
            if (this.elements.configurationModal) {
                const modal = new bootstrap.Modal(this.elements.configurationModal);
                modal.show();

                this.state.activeModal = 'configuration';
                window.AppEvents.emit('modal-opened', { modalType: 'configuration' });
            }
        },

        /**
         * Analyze current configurations of selected data points
         */
        analyzeCurrentConfigurations(selectedPoints) {
            console.log('[PopupsModule] Analyzing current configurations...');

            const frequencies = new Set();
            const units = new Set();
            const topics = new Set();
            let hasAssignments = false;

            // Iterate through selected data points
            for (const [fieldId, field] of selectedPoints) {
                if (field && field.current_assignment && field.current_assignment.has_assignments) {
                    hasAssignments = true;

                    // Use enhanced mixed state detection from API
                    if (field.current_assignment.all_frequencies) {
                        field.current_assignment.all_frequencies.forEach(freq => frequencies.add(freq));
                    } else if (field.current_assignment.frequency) {
                        frequencies.add(field.current_assignment.frequency);
                    }

                    if (field.current_assignment.all_units) {
                        field.current_assignment.all_units.forEach(unit => units.add(unit));
                    } else if (field.current_assignment.unit) {
                        units.add(field.current_assignment.unit);
                    }

                    if (field.current_assignment.all_topic_ids) {
                        field.current_assignment.all_topic_ids.forEach(topicId => topics.add(topicId));
                    } else if (field.current_assignment.assigned_topic_id) {
                        topics.add(field.current_assignment.assigned_topic_id);
                    }
                }
            }

            // Store original configuration state for comparison
            this.state.originalConfigurationState = {
                frequencies: Array.from(frequencies),
                units: Array.from(units),
                topics: Array.from(topics),
                hasAssignments: hasAssignments
            };

            // Update modal to show current state
            this.populateModalWithCurrentConfig();

            // Show change summary if there are existing configurations
            if (this.elements.configChangeSummary && hasAssignments) {
                this.elements.configChangeSummary.style.display = 'block';
            }

            console.log('[PopupsModule] Configuration analysis complete', this.state.originalConfigurationState);
        },

        /**
         * Populate modal form with current configuration
         */
        populateModalWithCurrentConfig() {
            const state = this.state.originalConfigurationState;
            if (!state) return;

            // Set frequency dropdown
            if (this.elements.modalFrequency) {
                if (state.frequencies.length === 1) {
                    this.elements.modalFrequency.value = state.frequencies[0];
                } else if (state.frequencies.length > 1) {
                    this.addMixedOption(this.elements.modalFrequency, '__MIXED__',
                        `Mixed (${state.frequencies.join(', ')})`);
                }
            }

            // Set unit dropdown
            if (this.elements.modalUnitOverrideSelect) {
                if (state.units.length === 1) {
                    this.elements.modalUnitOverrideSelect.value = state.units[0];
                } else if (state.units.length > 1) {
                    this.addMixedOption(this.elements.modalUnitOverrideSelect, '__MIXED__',
                        `Mixed units (${state.units.join(', ')})`);
                }
            }

            // Set topic dropdown
            if (this.elements.modalTopicSelect) {
                if (state.topics.length === 1) {
                    this.elements.modalTopicSelect.value = state.topics[0];
                } else if (state.topics.length > 1) {
                    this.addMixedOption(this.elements.modalTopicSelect, '__MIXED__', 'Mixed topics');
                }
            }
        },

        /**
         * Add a "mixed" option to a select element
         */
        addMixedOption(selectElement, value, text) {
            if (!selectElement) return;

            // Check if mixed option already exists
            if (!selectElement.querySelector(`option[value="${value}"]`)) {
                const mixedOption = document.createElement('option');
                mixedOption.value = value;
                mixedOption.textContent = text;
                mixedOption.style.fontStyle = 'italic';
                mixedOption.style.color = '#666';
                selectElement.insertBefore(mixedOption, selectElement.firstChild);
            }
            selectElement.value = value;
        },

        /**
         * Initialize modal toggle states
         */
        initializeModalToggles() {
            // Initialize Unit Override Toggle - off by default (hidden)
            if (this.elements.unitOverrideToggle) {
                const unitSelectContainer = this.elements.modalUnitOverrideSelect?.closest('.config-form-group');

                this.elements.unitOverrideToggle.checked = false;
                if (unitSelectContainer) {
                    unitSelectContainer.style.display = 'none';
                }
                if (this.elements.modalUnitOverrideSelect) {
                    this.elements.modalUnitOverrideSelect.value = '';
                }
            }

            // Initialize Material Topic Toggle - on by default (visible)
            if (this.elements.materialTopicToggle) {
                const topicSelectContainer = this.elements.modalTopicSelect?.closest('.config-form-group');

                this.elements.materialTopicToggle.checked = true;
                if (topicSelectContainer) {
                    topicSelectContainer.style.display = 'block';
                    topicSelectContainer.style.opacity = '1';
                    topicSelectContainer.style.transform = 'translateY(0)';
                }
            }
        },

        /**
         * Handle unit override toggle change
         */
        handleUnitOverrideToggle(event) {
            const unitSelectContainer = this.elements.modalUnitOverrideSelect?.closest('.config-form-group');

            if (unitSelectContainer) {
                if (event.target.checked) {
                    unitSelectContainer.style.display = 'block';
                } else {
                    unitSelectContainer.style.display = 'none';
                    if (this.elements.modalUnitOverrideSelect) {
                        this.elements.modalUnitOverrideSelect.value = '';
                    }
                }
            }
        },

        /**
         * Handle material topic toggle change
         */
        handleMaterialTopicToggle(event) {
            const topicSelectContainer = this.elements.modalTopicSelect?.closest('.config-form-group');

            if (topicSelectContainer) {
                if (event.target.checked) {
                    topicSelectContainer.style.display = 'block';
                } else {
                    topicSelectContainer.style.display = 'none';
                }
            }
        },

        /**
         * Get configuration from modal form
         */
        getModalConfiguration() {
            const frequencyValue = this.elements.modalFrequency?.value;
            const unitValue = this.elements.modalUnitOverrideSelect?.value;
            const topicValue = this.elements.modalTopicSelect?.value;

            const config = {
                frequency: frequencyValue && frequencyValue !== '__MIXED__' ? frequencyValue : null,
                unit: unitValue && unitValue !== '__MIXED__' ? (unitValue || null) : null,
                collection_method: this.elements.modalCollectionMethod?.value || 'Manual Entry',
                validation_rules: this.elements.modalValidationRules?.value || 'Required',
                approval_required: this.elements.modalApprovalRequired?.value === 'Yes',
                assigned_topic_id: topicValue && topicValue !== '__MIXED__' ? (topicValue || null) : null
            };

            // Track which fields were actually changed from original values
            const state = this.state.originalConfigurationState || {};
            config.changedFields = {};

            // Check frequency changes
            if (frequencyValue && frequencyValue !== '__MIXED__') {
                if (state.frequencies.length === 0 || !state.frequencies.includes(frequencyValue)) {
                    config.changedFields.frequency = true;
                }
            }

            // Check unit changes
            if (unitValue && unitValue !== '__MIXED__') {
                if (state.units.length === 0 || !state.units.includes(unitValue)) {
                    config.changedFields.unit = true;
                }
            } else if (unitValue === '') {
                config.changedFields.unit = true;
            }

            // Check topic changes
            if (topicValue && topicValue !== '__MIXED__') {
                if (state.topics.length === 0 || !state.topics.includes(topicValue)) {
                    config.changedFields.assigned_topic_id = true;
                }
            } else if (topicValue === '') {
                config.changedFields.assigned_topic_id = true;
            }

            return config;
        },

        /**
         * Validate configuration form
         */
        validateConfigurationForm(config) {
            if (!config.frequency) {
                this.showError('Please select a frequency');
                return false;
            }

            return true;
        },

        /**
         * Save configuration (to be called by external modules)
         */
        async saveConfiguration(data) {
            console.log('[PopupsModule] Saving configuration...', data);

            const { fieldId, config } = data;

            try {
                // Emit event for ServicesModule to handle
                window.AppEvents.emit('configuration-save-requested', { fieldId, config });

                console.log('[PopupsModule] Configuration save requested');
            } catch (error) {
                console.error('[PopupsModule] Error saving configuration:', error);
                this.showError('Failed to save configuration');
            }
        },

        // ===========================
        // ENTITY ASSIGNMENT MODAL
        // ===========================

        /**
         * Show Entity Assignment Modal
         * BUG FIX: Made async to support entity loading
         */
        async showEntityAssignmentModal(dataPoints, selectedCount) {
            console.log('[PopupsModule] Opening Entity Assignment Modal');

            // Get current selected points from AppState if not provided
            const currentSelectedPoints = dataPoints || window.AppState.selectedDataPoints;

            if (!currentSelectedPoints || currentSelectedPoints.size === 0) {
                this.showWarning('Please select data points to assign entities');
                return;
            }

            // Use the provided selectedCount from the event, otherwise fallback to AppState size
            const displayCount = selectedCount !== undefined ? selectedCount : currentSelectedPoints.size;

            // Update modal count
            if (this.elements.entityPointCount) {
                this.elements.entityPointCount.textContent = displayCount;
            }

            // Populate entity modal (now async)
            await this.populateEntityModal(currentSelectedPoints);

            // Show modal
            if (this.elements.entityModal) {
                const modal = new bootstrap.Modal(this.elements.entityModal);
                modal.show();

                this.state.activeModal = 'entity-assignment';
                window.AppEvents.emit('modal-opened', { modalType: 'entity-assignment' });
            }
        },

        /**
         * Populate entity modal with available and selected entities
         */
        async populateEntityModal(selectedPoints) {
            console.log('[PopupsModule] Populating entity modal...');

            if (!this.elements.modalAvailableEntities || !this.elements.modalSelectedEntities) return;

            // BUG FIX: Load entities asynchronously if not already cached
            let availableEntities = window.ServicesModule?.getAvailableEntities() || [];

            // If no cached entities, load them now
            if (availableEntities.length === 0 && window.ServicesModule?.loadEntities) {
                console.log('[PopupsModule] No cached entities found, loading from server...');
                try {
                    availableEntities = await window.ServicesModule.loadEntities();
                } catch (error) {
                    console.error('[PopupsModule] Error loading entities:', error);
                    this.showError('Failed to load entities');
                    return;
                }
            }

            // Get currently assigned entities for selected points
            const currentlyAssigned = new Set();
            for (const [fieldId, field] of selectedPoints) {
                const entities = field.assigned_entities || [];
                entities.forEach(entityId => currentlyAssigned.add(entityId.toString()));
            }

            // BUG FIX #2: Initialize state.selectedEntities with currently assigned entities
            this.state.selectedEntities = new Set(currentlyAssigned);
            console.log('[PopupsModule] Initialized selectedEntities state:', Array.from(this.state.selectedEntities));

            // Render available entities list (flat list)
            this.elements.modalAvailableEntities.innerHTML = availableEntities
                .map(entity => this.createEntityItemHTML(entity, currentlyAssigned.has(entity.id.toString())))
                .join('');

            // Render entity hierarchy (structured view)
            if (this.elements.entityHierarchyContainer) {
                this.populateEntityHierarchy(availableEntities, currentlyAssigned);
            }

            // Render selected entities as badges
            this.updateSelectedEntityBadges(availableEntities, currentlyAssigned);

            // Update count
            if (this.elements.modalSelectedEntitiesCount) {
                this.elements.modalSelectedEntitiesCount.textContent = currentlyAssigned.size;
            }

            // Add event listeners
            this.setupModalEntityListeners();
        },

        /**
         * Create HTML for a single entity item
         */
        createEntityItemHTML(entity, isSelected) {
            const iconText = entity.name.split(' ').map(word => word[0]).join('').substring(0, 2).toUpperCase();
            const selectedClass = isSelected ? 'selected' : '';

            return `
                <div class="entity-item ${selectedClass}" data-entity-id="${entity.id}">
                    <div class="entity-icon">${iconText}</div>
                    <div class="entity-name">${entity.name}</div>
                </div>
            `;
        },

        /**
         * Populate entity hierarchy view
         */
        populateEntityHierarchy(entities, currentlyAssigned) {
            if (!this.elements.entityHierarchyContainer) return;

            const hierarchyHTML = this.buildEntityHierarchyHTML(entities, currentlyAssigned);
            this.elements.entityHierarchyContainer.innerHTML = hierarchyHTML ||
                '<div class="hierarchy-empty">No entities available</div>';
        },

        /**
         * Build entity hierarchy HTML
         */
        buildEntityHierarchyHTML(entities, currentlyAssigned) {
            if (!entities || entities.length === 0) {
                return '<div class="hierarchy-empty">No entities available</div>';
            }

            // Group entities by parent_id
            const entitiesByParent = {};
            const rootEntities = [];

            entities.forEach(entity => {
                const parentId = entity.parent_id ? parseInt(entity.parent_id) : null;

                if (!parentId) {
                    rootEntities.push(entity);
                } else {
                    if (!entitiesByParent[parentId]) {
                        entitiesByParent[parentId] = [];
                    }
                    entitiesByParent[parentId].push(entity);
                }
            });

            // Build HTML recursively
            let html = '';
            rootEntities.forEach(entity => {
                html += this.renderEntityHierarchyNode(entity, entitiesByParent, currentlyAssigned, 0);
            });

            return html || '<div class="hierarchy-empty">No hierarchy structure found</div>';
        },

        /**
         * Render a single entity hierarchy node
         */
        renderEntityHierarchyNode(entity, entitiesByParent, currentlyAssigned, level) {
            const isSelected = currentlyAssigned.has(entity.id.toString());
            const hasChildren = entitiesByParent[entity.id] && entitiesByParent[entity.id].length > 0;
            const selectedClass = isSelected ? 'selected' : '';
            const indentStyle = `margin-left: ${level * 20}px;`;

            let html = `
                <div class="hierarchy-item">
                    <div class="hierarchy-node entity-selectable ${selectedClass}" data-entity-id="${entity.id}" style="${indentStyle}">
                        ${hasChildren ? '<i class="fas fa-chevron-right toggle-icon"></i>' : '<span class="hierarchy-spacer"></span>'}
                        <i class="${this.getEntityTypeIcon(entity.entity_type)} hierarchy-icon"></i>
                        <span class="hierarchy-label">${entity.name}</span>
                        <span class="hierarchy-type">(${entity.entity_type})</span>
                    </div>
            `;

            // Add children if they exist
            if (hasChildren) {
                html += '<div class="hierarchy-children" style="display: none;">';
                entitiesByParent[entity.id].forEach(child => {
                    html += this.renderEntityHierarchyNode(child, entitiesByParent, currentlyAssigned, level + 1);
                });
                html += '</div>';
            }

            html += '</div>';
            return html;
        },

        /**
         * Get icon class for entity type
         */
        getEntityTypeIcon(entityType) {
            const iconMap = {
                'Company': 'fas fa-building',
                'Division': 'fas fa-sitemap',
                'Department': 'fas fa-users',
                'Facility': 'fas fa-industry',
                'Location': 'fas fa-map-marker-alt',
                'default': 'fas fa-cube'
            };

            return iconMap[entityType] || iconMap['default'];
        },

        /**
         * Update selected entity badges
         */
        updateSelectedEntityBadges(availableEntities, currentlyAssigned) {
            if (!this.elements.modalSelectedEntities) return;

            if (currentlyAssigned.size === 0) {
                this.elements.modalSelectedEntities.innerHTML = '';
                return;
            }

            const selectedEntities = availableEntities.filter(entity =>
                currentlyAssigned.has(entity.id.toString())
            );

            this.elements.modalSelectedEntities.innerHTML = selectedEntities.map(entity => `
                <div class="selected-entity-badge" data-entity-id="${entity.id}">
                    <span>${entity.name}</span>
                    <i class="fas fa-times remove-entity" data-entity-id="${entity.id}"></i>
                </div>
            `).join('');
        },

        /**
         * Setup entity modal event listeners
         */
        setupModalEntityListeners() {
            console.log('[PopupsModule] Setting up entity modal listeners...');

            // BUG FIX #2 ROUND 5: Add listeners for flat entity list (LEFT PANE - Available Entities)
            if (this.elements.modalAvailableEntities) {
                this.elements.modalAvailableEntities.querySelectorAll('.entity-item').forEach(entityItem => {
                    entityItem.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const entityId = entityItem.dataset.entityId;

                        console.log('[PopupsModule] Flat list entity clicked:', entityId);

                        // Emit event for external handling
                        window.AppEvents.emit('entity-toggle-requested', { entityId });
                    });
                });
                console.log('[PopupsModule] Attached listeners to', this.elements.modalAvailableEntities.querySelectorAll('.entity-item').length, 'flat list entity items');
            }

            // Hierarchy toggle listeners (LEFT PANE - Company Hierarchy)
            if (this.elements.entityHierarchyContainer) {
                this.elements.entityHierarchyContainer.querySelectorAll('.toggle-icon').forEach(toggleBtn => {
                    toggleBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const hierarchyItem = toggleBtn.closest('.hierarchy-item');
                        const childrenContainer = hierarchyItem.querySelector('.hierarchy-children');

                        if (childrenContainer) {
                            const isExpanded = childrenContainer.style.display !== 'none';
                            childrenContainer.style.display = isExpanded ? 'none' : 'block';
                            toggleBtn.classList.toggle('fa-chevron-right', isExpanded);
                            toggleBtn.classList.toggle('fa-chevron-down', !isExpanded);
                        }
                    });
                });

                // Entity selection listeners (LEFT PANE - Company Hierarchy)
                this.elements.entityHierarchyContainer.querySelectorAll('.entity-selectable').forEach(entityNode => {
                    entityNode.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const entityId = entityNode.dataset.entityId;

                        console.log('[PopupsModule] Hierarchy entity clicked:', entityId);

                        // Emit event for external handling
                        window.AppEvents.emit('entity-toggle-requested', { entityId });
                    });
                });
                console.log('[PopupsModule] Attached listeners to', this.elements.entityHierarchyContainer.querySelectorAll('.entity-selectable').length, 'hierarchy entity nodes');
            }

            // Remove entity badge listeners (RIGHT PANE - Selected Entities)
            if (this.elements.modalSelectedEntities) {
                this.elements.modalSelectedEntities.querySelectorAll('.remove-entity').forEach(removeBtn => {
                    removeBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const entityId = removeBtn.dataset.entityId;

                        console.log('[PopupsModule] Remove badge clicked:', entityId);

                        // Emit event for external handling
                        window.AppEvents.emit('entity-toggle-requested', { entityId });
                    });
                });
                console.log('[PopupsModule] Attached listeners to', this.elements.modalSelectedEntities.querySelectorAll('.remove-entity').length, 'remove badges');
            }
        },

        /**
         * Save entity assignments (to be called by external modules)
         */
        async saveEntityAssignments(data) {
            console.log('[PopupsModule] Saving entity assignments...', data);

            try {
                // Emit event for ServicesModule to handle
                window.AppEvents.emit('entity-assignments-save-requested', data);

                console.log('[PopupsModule] Entity assignments save requested');
            } catch (error) {
                console.error('[PopupsModule] Error saving entity assignments:', error);
                this.showError('Failed to save entity assignments');
            }
        },

        // ===========================
        // FIELD INFORMATION MODAL
        // ===========================

        /**
         * Show Field Information Modal
         */
        async showFieldInformationModal(fieldId) {
            console.log('[PopupsModule] Opening Field Information Modal for field:', fieldId);

            // Get field data from AppState - try selectedDataPoints first, then dataPoints
            let field = window.AppState.selectedDataPoints.get(fieldId);

            if (!field) {
                // Try to get from dataPoints (contains all fields loaded)
                field = window.AppState.dataPoints?.get(fieldId);
            }

            if (!field) {
                this.showError('Field not found');
                return;
            }

            // Populate field information
            this.populateFieldInformation(field);

            // Setup unit override
            await this.setupUnitOverride(field);

            // Store current field ID
            this.state.currentFieldInfoId = fieldId;

            // Setup assignment history tab with field name
            this.setupAssignmentHistoryTab(fieldId, field.field_name || field.name);

            // Show modal
            if (this.elements.fieldInfoModal) {
                const modal = new bootstrap.Modal(this.elements.fieldInfoModal);
                modal.show();

                this.state.activeModal = 'field-info';
                window.AppEvents.emit('modal-opened', { modalType: 'field-info', fieldId });

                // Load assignment history when modal is shown
                await this.loadAssignmentHistory(fieldId);
            }
        },

        /**
         * Populate field information in modal
         */
        populateFieldInformation(field) {
            // Basic information
            if (this.elements.fieldInfoName) {
                this.elements.fieldInfoName.textContent = field.field_name || field.name || '-';
            }

            if (this.elements.fieldInfoType) {
                this.elements.fieldInfoType.textContent = field.value_type || 'NUMBER';
            }

            if (this.elements.fieldInfoTopic) {
                this.elements.fieldInfoTopic.textContent = field.topic || 'General';
            }

            if (this.elements.fieldInfoFramework) {
                this.elements.fieldInfoFramework.textContent = field.framework_name || '-';
            }

            if (this.elements.fieldInfoUnitCategory) {
                this.elements.fieldInfoUnitCategory.textContent = field.unit_category || '-';
            }

            if (this.elements.fieldInfoDefaultUnit) {
                this.elements.fieldInfoDefaultUnit.textContent = field.default_unit || field.unit || '-';
            }

            // Field Code
            const fieldCodeElement = document.getElementById('fieldInfoCode');
            if (fieldCodeElement) {
                fieldCodeElement.textContent = field.field_code || '-';
            }

            // Field ID
            const fieldIdElement = document.getElementById('fieldInfoFieldId');
            if (fieldIdElement) {
                fieldIdElement.textContent = field.field_id || '-';
            }

            // Computed field indicator
            if (this.elements.fieldInfoComputedIndicator) {
                if (field.is_computed) {
                    this.elements.fieldInfoComputedIndicator.style.display = 'block';
                    this.elements.fieldInfoComputedIndicator.innerHTML =
                        '<i class="fas fa-calculator text-warning"></i> <strong>Computed Field</strong>';
                } else {
                    this.elements.fieldInfoComputedIndicator.style.display = 'none';
                }
            }

            // Description
            if (this.elements.fieldInfoDescription && this.elements.fieldInfoDescriptionText) {
                if (field.description) {
                    this.elements.fieldInfoDescriptionText.textContent = field.description;
                    this.elements.fieldInfoDescription.style.display = 'block';
                } else {
                    this.elements.fieldInfoDescription.style.display = 'none';
                }
            }

            // Computed field details
            this.populateComputedFieldDetails(field);

            // Conflict warnings
            this.populateConflictWarnings(field);
        },

        /**
         * Populate computed field details
         */
        populateComputedFieldDetails(field) {
            if (!this.elements.fieldInfoComputedDetails) return;

            if (field.is_computed && field.dependencies && field.dependencies.length > 0) {
                this.elements.fieldInfoComputedDetails.style.display = 'block';

                // Formula
                if (this.elements.fieldInfoFormula) {
                    if (field.calculation_formula) {
                        this.elements.fieldInfoFormula.textContent = field.calculation_formula;
                        this.elements.fieldInfoFormula.parentElement.style.display = 'block';
                    } else {
                        this.elements.fieldInfoFormula.parentElement.style.display = 'none';
                    }
                }

                // Dependencies list
                if (this.elements.fieldInfoDependencies) {
                    this.elements.fieldInfoDependencies.innerHTML = field.dependencies.map(dep => `
                        <div class="dependency-item">
                            <i class="fas fa-arrow-right text-muted"></i>
                            <span class="dependency-name">${dep.field_name || dep.name}</span>
                            <span class="dependency-meta text-muted">(${dep.framework_name || 'Unknown Framework'})</span>
                            ${dep.is_computed ? '<i class="fas fa-calculator text-warning ms-2" title="Also computed"></i>' : ''}
                        </div>
                    `).join('');
                }

                // Dependency tree info
                if (this.elements.fieldInfoTreeInfo) {
                    const maxDepth = this.calculateDependencyDepth(field);
                    this.elements.fieldInfoTreeInfo.textContent =
                        `Dependency depth: ${maxDepth} level${maxDepth !== 1 ? 's' : ''}`;
                }
            } else if (field.is_computed) {
                this.elements.fieldInfoComputedDetails.style.display = 'block';
                if (this.elements.fieldInfoDependencies) {
                    this.elements.fieldInfoDependencies.innerHTML =
                        '<div class="text-muted">No dependencies defined</div>';
                }
                if (this.elements.fieldInfoTreeInfo) {
                    this.elements.fieldInfoTreeInfo.textContent = 'Simple computed field';
                }
            } else {
                this.elements.fieldInfoComputedDetails.style.display = 'none';
            }
        },

        /**
         * Calculate dependency tree depth
         */
        calculateDependencyDepth(field, visited = new Set()) {
            if (!field.is_computed || !field.dependencies || field.dependencies.length === 0) {
                return 0;
            }

            // Prevent circular dependencies
            if (visited.has(field.field_id)) {
                return 0;
            }

            visited.add(field.field_id);

            let maxDepth = 0;
            for (const dep of field.dependencies) {
                const depField = window.AppState.selectedDataPoints.get(dep.field_id);
                if (depField) {
                    const depDepth = this.calculateDependencyDepth(depField, new Set(visited));
                    maxDepth = Math.max(maxDepth, depDepth + 1);
                }
            }

            return maxDepth;
        },

        /**
         * Populate conflict warnings
         */
        populateConflictWarnings(field) {
            if (!this.elements.fieldInfoConflicts) return;

            // Get conflicts from ServicesModule or calculate
            const conflicts = this.getFieldConflicts(field);

            if (field.is_computed && conflicts.length > 0) {
                this.elements.fieldInfoConflicts.style.display = 'block';

                if (this.elements.fieldInfoConflictList) {
                    this.elements.fieldInfoConflictList.innerHTML = conflicts.map(conflict => `
                        <div class="alert alert-warning py-2">
                            <i class="fas fa-exclamation-triangle"></i>
                            <strong>${conflict.type}:</strong> ${conflict.message}
                            ${conflict.suggestion ? `<br><small class="text-muted">${conflict.suggestion}</small>` : ''}
                        </div>
                    `).join('');
                }
            } else {
                this.elements.fieldInfoConflicts.style.display = 'none';
            }
        },

        /**
         * Get conflicts for a field
         */
        getFieldConflicts(field) {
            // Placeholder - should be implemented based on business logic
            return [];
        },

        /**
         * Setup unit override functionality
         */
        async setupUnitOverride(field) {
            const currentUnitDisplay = document.getElementById('currentUnitDisplay');
            const unitOverrideSelect = document.getElementById('unitOverrideSelect');

            if (!currentUnitDisplay || !unitOverrideSelect) {
                console.log('[PopupsModule] Unit override elements not found');
                return;
            }

            // Get current assignment unit or field default
            const assignment = await this.getFieldAssignment(field.field_id);
            const currentUnit = assignment?.unit || field.default_unit || field.unit || 'units';
            currentUnitDisplay.textContent = currentUnit;

            // Clear previous options
            unitOverrideSelect.innerHTML = '<option value="">Use default unit</option>';

            // Load unit options if unit category is available
            if (field.unit_category) {
                try {
                    const response = await fetch('/admin/unit_categories');
                    const unitCategories = await response.json();
                    const categoryData = unitCategories[field.unit_category];

                    if (categoryData && categoryData.units) {
                        categoryData.units.forEach(unit => {
                            const option = document.createElement('option');
                            option.value = unit;
                            option.textContent = unit;
                            if (unit === currentUnit) {
                                option.selected = true;
                            }
                            unitOverrideSelect.appendChild(option);
                        });
                    }
                } catch (error) {
                    console.error('[PopupsModule] Error loading unit options:', error);
                }
            }
        },

        /**
         * Get field assignment data
         */
        async getFieldAssignment(fieldId) {
            try {
                const response = await fetch('/admin/get_existing_data_points');
                const assignments = await response.json();
                return assignments.find(a => a.field_id.toString() === fieldId.toString());
            } catch (error) {
                console.error('[PopupsModule] Error getting field assignment:', error);
                return null;
            }
        },

        // ===========================
        // ASSIGNMENT HISTORY (FIELD INFO MODAL)
        // ===========================

        /**
         * Setup assignment history tab
         */
        setupAssignmentHistoryTab(fieldId, fieldName) {
            console.log('[PopupsModule] Setting up assignment history tab for field:', fieldName);

            // Update field name in history header
            const historyFieldName = document.getElementById('historyFieldName');
            if (historyFieldName) {
                historyFieldName.textContent = fieldName || '-';
            }

            // Show loading state
            this.showHistoryLoading();

            // Add event listener for refresh button
            const refreshBtn = document.getElementById('refreshHistory');
            if (refreshBtn) {
                // Remove existing listeners
                const newRefreshBtn = refreshBtn.cloneNode(true);
                refreshBtn.parentNode.replaceChild(newRefreshBtn, refreshBtn);

                // Add new listener
                newRefreshBtn.addEventListener('click', async () => {
                    console.log('[PopupsModule] Refresh history clicked');
                    await this.loadAssignmentHistory(fieldId);
                });
            }
        },

        /**
         * Load assignment history for a specific field
         */
        async loadAssignmentHistory(fieldId) {
            console.log('[PopupsModule] Loading assignment history for field:', fieldId);

            this.showHistoryLoading();

            try {
                // Call the correct API endpoint for field-specific history
                const response = await fetch(`/admin/assignment-history/api/timeline?field_id=${fieldId}&per_page=50`);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                console.log('[PopupsModule] Assignment history loaded:', data);

                // Display the history timeline
                this.displayAssignmentHistory(data);

                // Update Field Details from assignment history
                this.updateFieldDetailsFromAssignmentHistory(data.timeline || []);

            } catch (error) {
                console.error('[PopupsModule] Error loading assignment history:', error);
                this.showHistoryError('Failed to load assignment history');
            }
        },

        /**
         * Display assignment history timeline
         */
        displayAssignmentHistory(data) {
            console.log('[PopupsModule] Displaying assignment history');

            const timeline = data.timeline || [];

            // Update summary statistics
            this.updateHistorySummary(timeline);

            // Show appropriate content
            if (timeline.length === 0) {
                this.showHistoryEmpty();
            } else {
                this.showHistoryContent(timeline);
            }
        },

        /**
         * Update Field Details tab from assignment history
         * Populates Field Code, Frequency, Status, and Field ID from active assignment
         */
        updateFieldDetailsFromAssignmentHistory(timeline) {
            console.log('[PopupsModule] Updating Field Details from assignment history:', timeline);

            // Find the current active assignment
            // First try: both is_active=true AND series_status='active'
            let activeAssignment = timeline.find(item => item.is_active && item.series_status === 'active');

            // Fallback: if series_status is undefined/null, just use is_active=true
            if (!activeAssignment) {
                activeAssignment = timeline.find(item => item.is_active);
            }

            console.log('[PopupsModule] Active assignment found:', activeAssignment);

            if (activeAssignment) {
                // Note: Field Code is set from field data in populateFieldInformation, not from assignment history

                // Update Frequency
                const frequencyElement = document.getElementById('fieldInfoFrequency');
                if (frequencyElement) {
                    const frequency = activeAssignment.frequency || '-';
                    console.log('[PopupsModule] Setting frequency to:', frequency);
                    frequencyElement.textContent = frequency;
                }

                // Update Version with active version number
                const versionElement = document.getElementById('fieldInfoVersion');
                if (versionElement) {
                    const version = activeAssignment.series_version || activeAssignment.version;
                    const versionText = version ? `v${version}` : '-';
                    console.log('[PopupsModule] Setting version to:', versionText);
                    versionElement.textContent = versionText;
                }

                // Update Topic (already populated in populateFieldInformation, but can override from assignment)
                const topicElement = document.getElementById('fieldInfoTopic');
                if (topicElement) {
                    const topicName = activeAssignment.effective_topic_name ||
                                     activeAssignment.assigned_topic_name ||
                                     activeAssignment.field_topic_name ||
                                     activeAssignment.topic_name ||
                                     activeAssignment.material_topic_name;
                    if (topicName) {
                        console.log('[PopupsModule] Updating topic to:', topicName);
                        topicElement.textContent = topicName;
                    }
                }
            } else {
                console.log('[PopupsModule] No active assignment found in timeline, using defaults');
            }
        },

        /**
         * Update history summary statistics
         */
        updateHistorySummary(timeline) {
            const totalCount = timeline.length;
            const activeCount = timeline.filter(item => item.is_active).length;
            const supersededCount = timeline.filter(item => !item.is_active || item.series_status === 'superseded').length;

            const totalCountEl = document.getElementById('historyTotalCount');
            const activeCountEl = document.getElementById('historyActiveCount');
            const supersededCountEl = document.getElementById('historySupersededCount');

            if (totalCountEl) totalCountEl.textContent = totalCount;
            if (activeCountEl) activeCountEl.textContent = activeCount;
            if (supersededCountEl) supersededCountEl.textContent = supersededCount;
        },

        /**
         * Show history content with timeline
         */
        showHistoryContent(timeline) {
            const historyLoading = document.getElementById('historyLoading');
            const historyContent = document.getElementById('historyContent');
            const historyEmpty = document.getElementById('historyEmpty');
            const historyTimeline = document.getElementById('historyTimeline');

            if (historyLoading) historyLoading.style.display = 'none';
            if (historyEmpty) historyEmpty.style.display = 'none';
            if (historyContent) historyContent.style.display = 'block';

            // Generate timeline HTML
            if (historyTimeline) {
                historyTimeline.innerHTML = this.generateTimelineHTML(timeline);
            }
        },

        /**
         * Generate timeline HTML with new design
         */
        generateTimelineHTML(timeline) {
            if (!timeline || timeline.length === 0) {
                return '<div class="text-muted text-center py-3">No assignment history available</div>';
            }

            // Group assignments by version
            const groupedByVersion = {};
            timeline.forEach(item => {
                const version = item.series_version || item.version || 1;
                if (!groupedByVersion[version]) {
                    groupedByVersion[version] = {
                        version: version,
                        timestamp: item.assigned_date,
                        status: item.is_active ? 'active' : 'superseded',
                        series_status: item.series_status,
                        assignments: []
                    };
                }
                groupedByVersion[version].assignments.push(item);
            });

            // Sort versions in descending order
            const versions = Object.keys(groupedByVersion).sort((a, b) => b - a);

            return versions.map(versionKey => {
                const versionGroup = groupedByVersion[versionKey];
                const timestamp = versionGroup.timestamp ?
                    new Date(versionGroup.timestamp).toLocaleString('en-GB', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    }).replace(/\//g, '/').replace(',', ',') :
                    'Date not available';

                const isActive = versionGroup.status === 'active' || versionGroup.series_status === 'active';
                const statusClass = isActive ? 'status-active' : 'status-superseded';
                const statusText = isActive ? 'Active' : 'Superseded';

                // Generate assignment cards
                const assignmentCards = versionGroup.assignments.map((assignment, index) => {
                    const changesId = `changes-v${versionGroup.version}-${index}`;
                    const hasChanges = assignment.changes_summary && assignment.changes_summary.trim() !== '';

                    // Check if this specific assignment is inactive (status='inactive')
                    // This handles the case where an assignment within an active version is marked inactive
                    // Note: Backend sends series_status as 'status' property
                    const isAssignmentInactive = assignment.status === 'inactive';
                    const cardClass = isAssignmentInactive ? 'superseded' : (isActive ? '' : 'superseded');

                    return `
                        <div class="assignment-card ${cardClass}">
                            <div class="assignment-card-grid">
                                <div class="assignment-field">
                                    <p class="assignment-field-label">Frequency</p>
                                    <p class="assignment-field-value">${assignment.frequency || 'Annual'}</p>
                                </div>
                                <div class="assignment-field">
                                    <p class="assignment-field-label">Entity</p>
                                    <p class="assignment-field-value">${assignment.entity_name || '-'}</p>
                                </div>
                                <div class="assignment-field">
                                    <p class="assignment-field-label">Topic</p>
                                    <p class="assignment-field-value">${assignment.effective_topic_name || assignment.topic_name || '-'}</p>
                                </div>
                                <div class="assignment-field">
                                    <p class="assignment-field-label">Assigned by</p>
                                    <p class="assignment-field-value">${assignment.assigned_by || '-'}</p>
                                </div>
                                <div class="assignment-action">
                                    ${hasChanges ? `
                                        <button class="view-changes-btn" onclick="window.PopupsModule.toggleChanges('${changesId}')">
                                            View Changes
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                            ${hasChanges ? `
                                <div class="assignment-changes" id="${changesId}">
                                    <p class="changes-label">Changes:</p>
                                    <p class="changes-text">${assignment.changes_summary}</p>
                                </div>
                            ` : ''}
                        </div>
                    `;
                }).join('');

                return `
                    <div class="history-version-group">
                        <div class="history-version-header">
                            <h4 class="version-number">Version ${versionGroup.version}</h4>
                            <span class="version-timestamp">${timestamp}</span>
                            <span class="version-status-badge ${statusClass}">${statusText}</span>
                        </div>
                        <div class="version-assignments">
                            ${assignmentCards}
                        </div>
                    </div>
                `;
            }).join('');
        },

        /**
         * Toggle changes visibility
         */
        toggleChanges(changesId) {
            const changesElement = document.getElementById(changesId);
            if (changesElement) {
                changesElement.classList.toggle('show');

                // Update button text
                const button = changesElement.previousElementSibling.querySelector('.view-changes-btn');
                if (button) {
                    const isVisible = changesElement.classList.contains('show');
                    button.textContent = isVisible ? 'Hide Changes' : 'View Changes';
                }
            }
        },

        /**
         * Get status badge HTML
         */
        getStatusBadge(status) {
            const statusMap = {
                'active': '<span class="badge bg-success">Active</span>',
                'superseded': '<span class="badge bg-warning">Superseded</span>',
                'deleted': '<span class="badge bg-danger">Deleted</span>'
            };
            return statusMap[status] || '<span class="badge bg-secondary">Unknown</span>';
        },

        /**
         * Show history loading state
         */
        showHistoryLoading() {
            const historyLoading = document.getElementById('historyLoading');
            const historyContent = document.getElementById('historyContent');
            const historyEmpty = document.getElementById('historyEmpty');

            if (historyLoading) historyLoading.style.display = 'block';
            if (historyContent) historyContent.style.display = 'none';
            if (historyEmpty) historyEmpty.style.display = 'none';
        },

        /**
         * Show history empty state
         */
        showHistoryEmpty() {
            const historyLoading = document.getElementById('historyLoading');
            const historyContent = document.getElementById('historyContent');
            const historyEmpty = document.getElementById('historyEmpty');

            if (historyLoading) historyLoading.style.display = 'none';
            if (historyContent) historyContent.style.display = 'none';
            if (historyEmpty) historyEmpty.style.display = 'block';
        },

        /**
         * Show history error state
         */
        showHistoryError(message) {
            const historyLoading = document.getElementById('historyLoading');
            const historyContent = document.getElementById('historyContent');
            const historyEmpty = document.getElementById('historyEmpty');

            if (historyLoading) {
                historyLoading.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i> ${message}
                    </div>
                `;
            }
            if (historyContent) historyContent.style.display = 'none';
            if (historyEmpty) historyEmpty.style.display = 'none';
        },

        // ===========================
        // CONFLICT RESOLUTION MODAL
        // ===========================

        /**
         * Show Configuration Conflict Modal
         */
        showConflictResolutionModal(conflicts, config) {
            console.log('[PopupsModule] Opening Conflict Resolution Modal', conflicts);

            // Create modal if it doesn't exist
            if (!this.elements.conflictResolutionModal) {
                this.createConflictResolutionModal();
            }

            // Populate conflict modal
            this.populateConflictModal(conflicts, config);

            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('conflictResolutionModal'));
            modal.show();

            this.state.activeModal = 'conflict-resolution';
            window.AppEvents.emit('modal-opened', { modalType: 'conflict-resolution' });
        },

        /**
         * Create Conflict Resolution Modal (if not in HTML)
         */
        createConflictResolutionModal() {
            const modalHTML = `
            <div class="modal fade" id="conflictResolutionModal" tabindex="-1" aria-labelledby="conflictResolutionModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header bg-warning">
                            <h5 class="modal-title" id="conflictResolutionModalLabel">
                                <i class="fas fa-exclamation-triangle"></i> Configuration Conflicts Detected
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-warning">
                                <strong>Cannot proceed:</strong> The configuration you're trying to apply conflicts with existing dependency configurations.
                                Please resolve these conflicts to continue.
                            </div>

                            <div id="conflictsList">
                                <!-- Conflicts will be populated here -->
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" id="autoResolveConflicts" class="btn btn-warning">
                                <i class="fas fa-magic"></i> Auto-Resolve All
                            </button>
                            <button type="button" id="forceApplyConfiguration" class="btn btn-danger">
                                <i class="fas fa-exclamation-circle"></i> Force Apply (Not Recommended)
                            </button>
                        </div>
                    </div>
                </div>
            </div>`;

            document.body.insertAdjacentHTML('beforeend', modalHTML);

            // Re-cache elements
            this.elements.conflictResolutionModal = document.getElementById('conflictResolutionModal');
            this.elements.conflictsList = document.getElementById('conflictsList');
            this.elements.autoResolveConflicts = document.getElementById('autoResolveConflicts');
            this.elements.forceApplyConfiguration = document.getElementById('forceApplyConfiguration');

            // Add event listeners
            if (this.elements.autoResolveConflicts) {
                this.elements.autoResolveConflicts.addEventListener('click', () => {
                    this.autoResolveConflicts();
                });
            }

            if (this.elements.forceApplyConfiguration) {
                this.elements.forceApplyConfiguration.addEventListener('click', () => {
                    this.forceApplyConfiguration();
                });
            }
        },

        /**
         * Populate conflict modal with conflict data
         */
        populateConflictModal(conflicts, config) {
            if (!this.elements.conflictsList) return;

            this.elements.conflictsList.innerHTML = conflicts.map(conflict => `
                <div class="conflict-item card mb-3">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <div class="conflict-title">
                            <i class="fas fa-exclamation-circle text-${this.getConflictSeverityColor(conflict.severity)}"></i>
                            <strong>${conflict.fieldName}</strong> → ${conflict.dependencyName}
                        </div>
                        <span class="badge bg-${this.getConflictSeverityColor(conflict.severity)}">${conflict.severity.toUpperCase()}</span>
                    </div>
                    <div class="card-body">
                        <p class="conflict-description">${conflict.issue}</p>
                        <div class="resolution-options">
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="resolution_${conflict.fieldId}_${conflict.dependencyId}"
                                       id="update_dependency_${conflict.fieldId}_${conflict.dependencyId}" value="update_dependency" checked>
                                <label class="form-check-label" for="update_dependency_${conflict.fieldId}_${conflict.dependencyId}">
                                    Update dependency configuration to match
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="resolution_${conflict.fieldId}_${conflict.dependencyId}"
                                       id="keep_dependency_${conflict.fieldId}_${conflict.dependencyId}" value="keep_dependency">
                                <label class="form-check-label" for="keep_dependency_${conflict.fieldId}_${conflict.dependencyId}">
                                    Keep dependency configuration and update main field
                                </label>
                            </div>
                            ${!conflict.autoResolvable ? `
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="resolution_${conflict.fieldId}_${conflict.dependencyId}"
                                       id="ignore_${conflict.fieldId}_${conflict.dependencyId}" value="ignore">
                                <label class="form-check-label" for="ignore_${conflict.fieldId}_${conflict.dependencyId}">
                                    <span class="text-danger">Ignore conflict (may cause calculation errors)</span>
                                </label>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `).join('');

            this.state.currentConflicts = conflicts;
            this.state.currentConflictConfig = config;
        },

        /**
         * Get conflict severity color
         */
        getConflictSeverityColor(severity) {
            switch (severity) {
                case 'high': return 'danger';
                case 'medium': return 'warning';
                case 'low': return 'info';
                default: return 'secondary';
            }
        },

        /**
         * Auto-resolve conflicts
         */
        async autoResolveConflicts() {
            console.log('[PopupsModule] Auto-resolving conflicts...');

            if (!this.state.currentConflicts || !this.state.currentConflictConfig) return;

            try {
                // Emit event for external handling
                window.AppEvents.emit('conflicts-auto-resolve-requested', {
                    conflicts: this.state.currentConflicts,
                    config: this.state.currentConflictConfig
                });

                // Close modal
                this.closeModal('conflictResolutionModal');

                this.showSuccess('Conflicts auto-resolved successfully');
            } catch (error) {
                console.error('[PopupsModule] Error auto-resolving conflicts:', error);
                this.showError('Error resolving conflicts');
            }
        },

        /**
         * Force apply configuration
         */
        async forceApplyConfiguration() {
            console.log('[PopupsModule] Force applying configuration...');

            if (!this.state.currentConflictConfig) return;

            if (!confirm('Force applying this configuration may cause calculation errors. Are you sure you want to continue?')) {
                return;
            }

            try {
                // Emit event for external handling
                window.AppEvents.emit('configuration-force-apply-requested', {
                    config: this.state.currentConflictConfig
                });

                // Close modal
                this.closeModal('conflictResolutionModal');

                this.showWarning('Configuration force applied (conflicts remain unresolved)');
            } catch (error) {
                console.error('[PopupsModule] Error force applying configuration:', error);
                this.showError('Error applying configuration');
            }
        },

        // ===========================
        // CONFIRMATION DIALOGS
        // ===========================

        /**
         * Show generic confirmation dialog
         */
        showConfirmation(options) {
            const { title, message, confirmText, cancelText, onConfirm, onCancel } = options;

            return new Promise((resolve) => {
                const result = confirm(`${title}\n\n${message}`);

                if (result && onConfirm) {
                    onConfirm();
                } else if (!result && onCancel) {
                    onCancel();
                }

                resolve(result);
            });
        },

        /**
         * Show success message
         */
        showSuccess(message) {
            console.log('[PopupsModule] Success:', message);
            window.AppEvents.emit('show-message', { type: 'success', message });
        },

        /**
         * Show error message
         */
        showError(message) {
            console.error('[PopupsModule] Error:', message);
            window.AppEvents.emit('show-message', { type: 'error', message });
        },

        /**
         * Show warning message
         */
        showWarning(message) {
            console.warn('[PopupsModule] Warning:', message);
            window.AppEvents.emit('show-message', { type: 'warning', message });
        },

        /**
         * Show info message
         */
        showInfo(message) {
            console.info('[PopupsModule] Info:', message);
            window.AppEvents.emit('show-message', { type: 'info', message });
        },

        // ===========================
        // MODAL MANAGEMENT
        // ===========================

        /**
         * Handle Escape key press
         * BUG FIX #1: Close active modal when Escape is pressed
         */
        handleEscapeKey() {
            // Check if any Bootstrap modal is currently shown
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modalInstance = bootstrap.Modal.getInstance(openModal);
                if (modalInstance) {
                    console.log('[PopupsModule] Closing modal via Escape key:', openModal.id);
                    modalInstance.hide();

                    // Update state
                    if (this.state.activeModal === openModal.id) {
                        this.state.activeModal = null;
                        this.state.currentModalData = {};
                    }

                    window.AppEvents.emit('modal-closed-by-escape', { modalId: openModal.id });
                }
            }
        },

        /**
         * Open a modal by ID
         */
        openModal(modalId, data) {
            console.log('[PopupsModule] Opening modal:', modalId);

            const modalElement = document.getElementById(modalId);
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();

                this.state.activeModal = modalId;
                this.state.currentModalData = data || {};

                window.AppEvents.emit('modal-opened', { modalId, data });
            } else {
                console.error('[PopupsModule] Modal not found:', modalId);
            }
        },

        /**
         * Close a modal by ID
         */
        closeModal(modalId) {
            console.log('[PopupsModule] Closing modal:', modalId);

            const modalElement = document.getElementById(modalId);
            if (modalElement) {
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                }

                if (this.state.activeModal === modalId) {
                    this.state.activeModal = null;
                    this.state.currentModalData = {};
                }

                window.AppEvents.emit('modal-closed', { modalId });
            }
        },

        /**
         * Close all modals
         */
        closeAllModals() {
            console.log('[PopupsModule] Closing all modals');

            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modalElement => {
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                }
            });

            this.state.activeModal = null;
            this.state.currentModalData = {};

            window.AppEvents.emit('all-modals-closed');
        },

        /**
         * Get active modal
         */
        getActiveModal() {
            return this.state.activeModal;
        },

        /**
         * Check if a modal is open
         */
        isModalOpen(modalId) {
            if (modalId) {
                return this.state.activeModal === modalId;
            }
            return this.state.activeModal !== null;
        },

        // ===========================
        // BUG FIX #2 & #3: MODAL BUTTON HANDLERS
        // ===========================

        /**
         * BUG FIX #2: Handle entity toggle (selection/deselection)
         */
        handleEntityToggle(entityId) {
            console.log('[PopupsModule] Entity toggle requested:', entityId);

            // Convert to string for consistent comparison
            const entityIdStr = entityId.toString();

            // Toggle selection
            if (this.state.selectedEntities.has(entityIdStr)) {
                this.state.selectedEntities.delete(entityIdStr);
                console.log('[PopupsModule] Entity deselected:', entityIdStr);
            } else {
                this.state.selectedEntities.add(entityIdStr);
                console.log('[PopupsModule] Entity selected:', entityIdStr);
            }

            // Update UI
            this.updateEntitySelectionUI(entityIdStr);
            this.updateSelectedEntityCount();

            console.log('[PopupsModule] Currently selected entities:', Array.from(this.state.selectedEntities));
        },

        /**
         * BUG FIX #2: Update entity selection UI
         */
        updateEntitySelectionUI(entityId) {
            const entityIdStr = entityId.toString();
            const isSelected = this.state.selectedEntities.has(entityIdStr);

            console.log('[PopupsModule] Updating UI for entity:', entityIdStr, 'isSelected:', isSelected);

            // BUG FIX #2 ROUND 5: Update flat list view (LEFT PANE - Available Entities)
            if (this.elements.modalAvailableEntities) {
                const entityItem = this.elements.modalAvailableEntities.querySelector(
                    `.entity-item[data-entity-id="${entityIdStr}"]`
                );
                if (entityItem) {
                    if (isSelected) {
                        entityItem.classList.add('selected');
                    } else {
                        entityItem.classList.remove('selected');
                    }
                    console.log('[PopupsModule] Updated flat list item:', entityIdStr);
                }
            }

            // Update hierarchy view (LEFT PANE - Company Hierarchy)
            if (this.elements.entityHierarchyContainer) {
                const entityNode = this.elements.entityHierarchyContainer.querySelector(
                    `.entity-selectable[data-entity-id="${entityIdStr}"]`
                );
                if (entityNode) {
                    if (isSelected) {
                        entityNode.classList.add('selected');
                    } else {
                        entityNode.classList.remove('selected');
                    }
                    console.log('[PopupsModule] Updated hierarchy node:', entityIdStr);
                }
            }

            // Update selected entities badges (RIGHT PANE)
            this.updateSelectedEntityBadgesFromState();
        },

        /**
         * BUG FIX #2: Update selected entity count
         */
        updateSelectedEntityCount() {
            if (this.elements.modalSelectedEntitiesCount) {
                this.elements.modalSelectedEntitiesCount.textContent = this.state.selectedEntities.size;
            }
        },

        /**
         * BUG FIX #2: Update selected entity badges from current state
         */
        updateSelectedEntityBadgesFromState() {
            if (!this.elements.modalSelectedEntities) return;

            if (this.state.selectedEntities.size === 0) {
                this.elements.modalSelectedEntities.innerHTML = '';
                return;
            }

            // Get entity data from ServicesModule
            const availableEntities = window.ServicesModule?.getAvailableEntities() || [];
            const selectedEntities = availableEntities.filter(entity =>
                this.state.selectedEntities.has(entity.id.toString())
            );

            this.elements.modalSelectedEntities.innerHTML = selectedEntities.map(entity => `
                <div class="selected-entity-badge" data-entity-id="${entity.id}">
                    <span>${entity.name}</span>
                    <i class="fas fa-times remove-entity" data-entity-id="${entity.id}"></i>
                </div>
            `).join('');

            // Reattach remove listeners
            this.elements.modalSelectedEntities.querySelectorAll('.remove-entity').forEach(removeBtn => {
                removeBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const entityId = removeBtn.dataset.entityId;
                    window.AppEvents.emit('entity-toggle-requested', { entityId });
                });
            });
        },

        /**
         * BUG FIX #3: Handle Apply Configuration button click
         */
        handleApplyConfiguration() {
            console.log('[PopupsModule] Apply Configuration handler called');

            // Get configuration from form
            const config = this.getModalConfiguration();

            // Validate configuration
            if (!this.validateConfigurationForm(config)) {
                console.error('[PopupsModule] Configuration validation failed');
                return;
            }

            console.log('[PopupsModule] Configuration validated:', config);

            // BUG FIX #5: Get ONLY checked data points (not all in AppState)
            // This matches old behavior where only checked items are processed
            const selectedDataPoints = this.getCheckedDataPoints();

            if (!selectedDataPoints || selectedDataPoints.size === 0) {
                this.showError('No data points selected');
                return;
            }

            console.log('[PopupsModule] Operating on checked data points:', selectedDataPoints.size);

            // Make API call to save configuration
            this.applyConfigurationToServer(config, selectedDataPoints);
        },

        /**
         * BUG FIX #3: Apply configuration to server
         */
        async applyConfigurationToServer(config, selectedDataPoints) {
            try {
                console.log('[PopupsModule] Sending configuration to server...');

                // Prepare field IDs
                const fieldIds = Array.from(selectedDataPoints.keys());

                // Build request payload in the format expected by /admin/configure_fields
                const payload = {
                    field_ids: fieldIds,
                    configuration: {
                        frequency: config.frequency,
                        unit: config.unit || null,
                        collection_method: config.collection_method,
                        validation_rules: config.validation_rules,
                        approval_required: config.approval_required,
                        assigned_topic_id: config.assigned_topic_id || null
                    }
                };

                console.log('[PopupsModule] Configuration payload:', payload);

                // Make API call to the correct endpoint
                const response = await fetch('/admin/configure_fields', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const result = await response.json();
                console.log('[PopupsModule] Configuration saved successfully:', result);

                // Update AppState configurations
                fieldIds.forEach(fieldId => {
                    window.AppState.setConfiguration(fieldId, config);
                });

                // Show success message
                this.showSuccess('Configuration applied successfully');

                // Close modal
                this.closeModal('configurationModal');

                // Reload assignment configurations to refresh UI with updated topic assignments
                if (typeof window.reloadAssignmentConfigurations === 'function') {
                    await window.reloadAssignmentConfigurations();
                    console.log('[PopupsModule] UI refreshed with updated configurations');

                    // Show detailed notification if topic was assigned
                    if (config.assigned_topic_id && window.PopupManager) {
                        const topicName = this.getTopicNameById(config.assigned_topic_id);
                        const fieldCount = fieldIds.length;
                        const fieldText = fieldCount === 1 ? 'data point' : 'data points';
                        window.PopupManager.showSuccess(
                            'Topic Assignment Updated',
                            `${fieldCount} ${fieldText} assigned to <strong>${topicName}</strong> topic`,
                            4000
                        );

                        // Highlight the moved items
                        this.highlightMovedDataPoints(fieldIds);
                    }
                }

                // Emit success event
                window.AppEvents.emit('configuration-saved', { config, fieldIds });

            } catch (error) {
                console.error('[PopupsModule] Error saving configuration:', error);
                this.showError(`Failed to save configuration: ${error.message}`);
            }
        },

        /**
         * BUG FIX #5: Get currently CHECKED data points from SelectedDataPointsPanel
         * This respects checkbox state, not just what's in AppState.selectedDataPoints
         */
        getCheckedDataPoints() {
            const checkedDataPoints = new Map();

            // Find all checked checkboxes in the selected data points panel
            const selectedPanel = document.getElementById('selectedDataPointsList') || document.getElementById('selectedPointsList');
            if (!selectedPanel) {
                console.warn('[PopupsModule] Selected data points panel not found');
                return checkedDataPoints;
            }

            const checkedBoxes = selectedPanel.querySelectorAll('.point-select:checked');
            console.log('[PopupsModule] Found checked boxes:', checkedBoxes.length);

            checkedBoxes.forEach(checkbox => {
                const fieldId = checkbox.closest('[data-field-id]')?.dataset.fieldId;
                if (fieldId) {
                    // Try to get from selectedDataPoints first
                    if (window.AppState.selectedDataPoints.has(fieldId)) {
                        checkedDataPoints.set(fieldId, window.AppState.selectedDataPoints.get(fieldId));
                    }
                    // Fallback: Try to get from dataPoints (all loaded fields)
                    else if (window.AppState.dataPoints && window.AppState.dataPoints.has(fieldId)) {
                        const field = window.AppState.dataPoints.get(fieldId);
                        checkedDataPoints.set(fieldId, field);
                        console.log('[PopupsModule] Field not in selectedDataPoints, using dataPoints:', fieldId);
                    }
                    // Last resort: Create minimal field object from DOM
                    else {
                        const fieldItem = checkbox.closest('[data-field-id]');
                        const fieldName = fieldItem?.querySelector('.point-name')?.textContent || 'Unknown Field';
                        console.warn('[PopupsModule] Field not found in AppState, creating minimal object:', fieldId);
                        checkedDataPoints.set(fieldId, {
                            field_id: fieldId,
                            id: fieldId,
                            field_name: fieldName,
                            name: fieldName
                        });
                    }
                }
            });

            return checkedDataPoints;
        },

        /**
         * BUG FIX #2: Handle Apply Entity Assignment button click
         */
        handleApplyEntityAssignment() {
            console.log('[PopupsModule] Apply Entity Assignment handler called');

            // Get selected entities from state
            const selectedEntityIds = Array.from(this.state.selectedEntities);

            if (selectedEntityIds.length === 0) {
                this.showError('Please select at least one entity');
                return;
            }

            console.log('[PopupsModule] Selected entities:', selectedEntityIds);

            // BUG FIX #5: Get ONLY checked data points (not all in AppState)
            // This matches old behavior where only checked items are processed
            const selectedDataPoints = this.getCheckedDataPoints();

            if (!selectedDataPoints || selectedDataPoints.size === 0) {
                this.showError('No data points selected');
                return;
            }

            console.log('[PopupsModule] Operating on checked data points:', selectedDataPoints.size);

            // Make API call to save entity assignments
            this.applyEntityAssignmentToServer(selectedEntityIds, selectedDataPoints);
        },

        /**
         * BUG FIX #2: Apply entity assignments to server
         */
        async applyEntityAssignmentToServer(entityIds, selectedDataPoints) {
            try {
                console.log('[PopupsModule] Sending entity assignments to server...');

                // Prepare field IDs
                const fieldIds = Array.from(selectedDataPoints.keys());

                // Build request payload in the format expected by /admin/assign_entities
                const payload = {
                    field_ids: fieldIds,
                    entity_ids: entityIds,
                    configuration: {}  // Empty configuration object for now
                };

                console.log('[PopupsModule] Entity assignment payload:', payload);

                // Make API call to the correct endpoint
                const response = await fetch('/admin/assign_entities', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const result = await response.json();
                console.log('[PopupsModule] Entity assignments saved successfully:', result);

                // Update AppState entity assignments
                fieldIds.forEach(fieldId => {
                    window.AppState.entityAssignments.set(fieldId, new Set(entityIds));
                });

                // Show success message
                this.showSuccess('Entity assignments applied successfully');

                // Close modal
                this.closeModal('entityModal');

                // Reload configurations to update badge counts with actual active assignments
                console.log('[PopupsModule] Reloading configurations after entity assignment');
                window.AppEvents.emit('reload-configurations');

                // Emit success event
                window.AppEvents.emit('entities-assigned', { entityIds, fieldIds });

            } catch (error) {
                console.error('[PopupsModule] Error saving entity assignments:', error);
                this.showError(`Failed to save entity assignments: ${error.message}`);
            }
        },

        /**
         * Get topic name by topic ID from loaded topics
         */
        getTopicNameById(topicId) {
            // Try to find topic name from the dropdown options
            const topicSelect = this.elements.modalTopicSelect;
            if (topicSelect) {
                const option = topicSelect.querySelector(`option[value="${topicId}"]`);
                if (option) {
                    return option.textContent;
                }
            }
            return 'Selected Topic';
        },

        /**
         * Highlight data points that were moved to a new topic group
         * @param {Array} fieldIds - Array of field IDs to highlight
         */
        highlightMovedDataPoints(fieldIds) {
            console.log('[PopupsModule] Highlighting moved data points:', fieldIds);

            // Wait a brief moment for UI to refresh
            setTimeout(() => {
                fieldIds.forEach(fieldId => {
                    // Find the data point item in the selected panel
                    const dataPointItem = document.querySelector(`[data-field-id="${fieldId}"]`);

                    if (dataPointItem) {
                        // Add highlight animation class
                        dataPointItem.classList.add('topic-change-highlight');

                        // Remove the highlight after animation completes
                        setTimeout(() => {
                            dataPointItem.classList.remove('topic-change-highlight');
                        }, 2000);
                    }
                });
            }, 500); // Wait for UI refresh to complete
        },

        /**
         * Handle single item configure button click
         * Ensures the checkbox is checked and opens configuration modal for that specific item
         */
        handleSingleConfigure(fieldId, itemData) {
            console.log('[PopupsModule] Single configure clicked for:', fieldId);

            // Ensure the checkbox is checked
            const checkbox = document.querySelector(`.point-select[data-field-id="${fieldId}"]`);
            if (checkbox && !checkbox.checked) {
                checkbox.checked = true;
                // Emit event to update state
                window.AppEvents.emit('selected-panel-item-checkbox-changed', {
                    fieldId: fieldId,
                    isChecked: true
                });
            }

            // Create a Map with just this single item
            const singleItemMap = new Map();
            singleItemMap.set(fieldId, itemData);

            // Open configuration modal with this single item
            this.showConfigurationModal(singleItemMap, 1);
        },

        /**
         * Handle single item assign entity button click
         * Ensures the checkbox is checked and opens entity assignment modal for that specific item
         */
        handleSingleAssign(fieldId, itemData) {
            console.log('[PopupsModule] Single assign clicked for:', fieldId);

            // Ensure the checkbox is checked
            const checkbox = document.querySelector(`.point-select[data-field-id="${fieldId}"]`);
            if (checkbox && !checkbox.checked) {
                checkbox.checked = true;
                // Emit event to update state
                window.AppEvents.emit('selected-panel-item-checkbox-changed', {
                    fieldId: fieldId,
                    isChecked: true
                });
            }

            // Create a Map with just this single item
            const singleItemMap = new Map();
            singleItemMap.set(fieldId, itemData);

            // Open entity assignment modal with this single item
            this.showEntityAssignmentModal(singleItemMap, 1);
        }

    };

    // Export to window
    window.PopupsModule = PopupsModule;

    console.log('[PopupsModule] Module loaded and ready to initialize');

})();