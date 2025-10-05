// Redesigned Assign Data Points JavaScript
// Single-page implementation maintaining all existing functionality

console.log('DEBUG: Starting to load assign_data_points_redesigned.js');

class DataPointsManager {
    constructor() {
        // MODULAR REFACTOR: These state properties moved to window.AppState in main.js lines 41-48
        this.selectedDataPoints = new Map(); // field_id -> data point object
        this.configurations = new Map(); // field_id -> configuration object
        this.entityAssignments = new Map(); // field_id -> Set of entity IDs
        this.topicAssignments = new Map(); // field_id -> topic_id for material topic assignments
        this.availableEntities = [];
        this.companyTopics = []; // Available company topics for assignment
        this.currentSelectedPoints = new Set(); // Currently checked points in right panel
        this.showingInactiveAssignments = false; // Track whether inactive assignments are shown

        this.init();
    }

    // MODULAR REFACTOR: This utility method moved to window.AppUtils in main.js lines 90-99
    getEntityTypeIcon(entityType) {
        const iconMap = {
            'Office': 'fas fa-building',
            'Manufacturing': 'fas fa-industry',
            'Warehouse': 'fas fa-warehouse',
            'Campus': 'fas fa-university',
            'Company': 'fas fa-building-flag',
            'Team': 'fas fa-users'
        };
        return iconMap[entityType] || 'fas fa-building';
    }

    // MODULAR REFACTOR: This initialization method moved to initializeApp() in main.js lines 236-285
    async init() {
        try {
            console.log('Starting DataPointsManager initialization...');
            
            // Initialize PopupManager
            if (window.PopupManager) {
                PopupManager.init();
                console.log('PopupManager initialized');
            } else {
                console.warn('PopupManager not available, using fallback messaging');
            }

            // Load initial data
            console.log('Loading entities...');
            await this.loadEntities();
            
            console.log('Loading company topics...');
            await this.loadCompanyTopics();
            
            console.log('Loading existing data points...');
            await this.loadExistingDataPoints();

            // Setup event listeners
            console.log('Setting up event listeners...');
            this.setupEventListeners();
            
            // Update UI
            console.log('Updating UI...');
            this.updateUIComponents();
            
            // Setup new UI components (topic tree, view toggle, etc.)
            this.setupNewUIComponents();
            
            // Setup unit override save button - removed dead code (no HTML element exists)
            
            console.log('DataPointsManager initialized successfully');
        } catch (error) {
            console.error('Error initializing DataPointsManager:', error);
            console.error('Error stack:', error.stack);
            this.showMessage('Error initializing the interface: ' + error.message, 'error');
        }
    }

    setupEventListeners() {
        try {
            // Framework selection
            const frameworkSelect = document.getElementById('framework_select');
            if (frameworkSelect) {
                frameworkSelect.addEventListener('change', (e) => this.handleFrameworkChange(e));
            } else {
                console.warn('Framework select element not found');
            }

            // Search functionality
            const searchInput = document.getElementById('dataPointSearch');
            if (searchInput) {
                searchInput.addEventListener('input', (e) => this.handleSearch(e));
            } else {
                console.warn('Search input element not found');
            }

            // Toggle inactive assignments
            const toggleInactiveBtn = document.getElementById('toggleInactiveAssignments');
            if (toggleInactiveBtn) {
                toggleInactiveBtn.addEventListener('click', (e) => this.toggleInactiveAssignments(e));
            }

            // Configuration mode toggle
            const modeButtons = document.querySelectorAll('.mode-btn');
            if (modeButtons.length > 0) {
                modeButtons.forEach(btn => {
                    btn.addEventListener('click', (e) => this.handleModeChange(e));
                });
            } else {
                console.warn('Mode buttons not found');
            }

            // Setup modal listeners for FY preview
            this.setupModalListeners();

            // Action buttons
            const actionButtons = [
                { id: 'configureSelected', handler: () => this.openConfigurationModal() },
                { id: 'assignEntities', handler: () => this.openEntityModal() },
                { id: 'saveAllConfiguration', handler: () => this.saveAllConfiguration() },
                { id: 'exportAssignments', handler: () => this.exportAssignments() },
                { id: 'importAssignments', handler: () => this.importAssignments() },
                { id: 'clearAllSelection', handler: () => this.clearAllSelection() },
                { id: 'selectAllVisible', handler: () => this.selectAllVisible() },
                { id: 'selectAllDataPoints', handler: () => this.selectAllDataPoints() },
                { id: 'deselectAllDataPoints', handler: () => this.deselectAllDataPoints() }
            ];

            actionButtons.forEach(({ id, handler }) => {
                const element = document.getElementById(id);
                if (element) {
                    element.addEventListener('click', handler);
                } else {
                    console.warn(`Action button ${id} not found`);
                }
            });

            // Modal action buttons
            const modalButtons = [
                { id: 'applyConfiguration', handler: () => this.applyConfiguration() },
                { id: 'applyEntityAssignment', handler: () => this.applyEntityAssignment() }
            ];

            modalButtons.forEach(({ id, handler }) => {
                const element = document.getElementById(id);
                if (element) {
                    element.addEventListener('click', handler);
                } else {
                    console.warn(`Modal button ${id} not found`);
                }
            });
            
            // Setup topic assignment event listeners
            this.setupTopicEventListeners();
            
            console.log('Event listeners setup completed');
        } catch (error) {
            console.error('Error setting up event listeners:', error);
        }
    }

    setupModalListeners() {
        // Unit Override Toggle
        const unitOverrideToggle = document.getElementById('unitOverrideToggle');
        if (unitOverrideToggle) {
            unitOverrideToggle.addEventListener('change', (e) => {
                const unitSelectContainer = document.getElementById('modalUnitOverrideSelect').closest('.config-form-group');
                if (unitSelectContainer) {
                    if (e.target.checked) {
                        // Show the form group with smooth animation
                        unitSelectContainer.style.display = 'block';
                        unitSelectContainer.style.opacity = '0';
                        unitSelectContainer.style.transform = 'translateY(-10px)';

                        // Animate in
                        setTimeout(() => {
                            unitSelectContainer.style.transition = 'all 0.3s ease';
                            unitSelectContainer.style.opacity = '1';
                            unitSelectContainer.style.transform = 'translateY(0)';
                        }, 10);
                    } else {
                        // Hide with animation
                        unitSelectContainer.style.transition = 'all 0.3s ease';
                        unitSelectContainer.style.opacity = '0';
                        unitSelectContainer.style.transform = 'translateY(-10px)';

                        setTimeout(() => {
                            unitSelectContainer.style.display = 'none';
                            document.getElementById('modalUnitOverrideSelect').value = '';
                        }, 300);
                    }
                }
            });
        }

        // Material Topic Toggle
        const materialTopicToggle = document.getElementById('materialTopicToggle');
        if (materialTopicToggle) {
            materialTopicToggle.addEventListener('change', (e) => {
                const topicSelectContainer = document.getElementById('modalTopicSelect').closest('.config-form-group');
                if (topicSelectContainer) {
                    if (e.target.checked) {
                        // Show the form group with smooth animation
                        topicSelectContainer.style.display = 'block';
                        topicSelectContainer.style.opacity = '0';
                        topicSelectContainer.style.transform = 'translateY(-10px)';

                        // Animate in
                        setTimeout(() => {
                            topicSelectContainer.style.transition = 'all 0.3s ease';
                            topicSelectContainer.style.opacity = '1';
                            topicSelectContainer.style.transform = 'translateY(0)';
                        }, 10);
                    } else {
                        // Hide with animation
                        topicSelectContainer.style.transition = 'all 0.3s ease';
                        topicSelectContainer.style.opacity = '0';
                        topicSelectContainer.style.transform = 'translateY(-10px)';

                        setTimeout(() => {
                            topicSelectContainer.style.display = 'none';
                            document.getElementById('modalTopicSelect').value = '';
                        }, 300);
                    }
                }
            });
        }

        // Clear Topic Assignment Button
        const clearTopicBtn = document.getElementById('clearTopicAssignment');
        if (clearTopicBtn) {
            clearTopicBtn.addEventListener('click', () => {
                document.getElementById('modalTopicSelect').value = '';
            });
        }

        console.log('Modal listeners set up');
    }


    async loadEntities() {
        try {
            console.log('Fetching entities from /admin/get_entities');
            const response = await fetch('/admin/get_entities');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.availableEntities = await response.json();
            console.log('Loaded entities:', this.availableEntities.length);
        } catch (error) {
            console.error('Error loading entities:', error);
            this.showMessage('Error loading entities: ' + error.message, 'error');
        }
    }

    async loadCompanyTopics() {
        try {
            console.log('Fetching company topics from /admin/topics/company_dropdown');
            const response = await fetch('/admin/topics/company_dropdown');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            if (data.success) {
                this.companyTopics = data.topics || [];
                console.log('Loaded company topics:', this.companyTopics.length);
                this.populateTopicDropdown();
            } else {
                throw new Error(data.error || 'Failed to load topics');
            }
        } catch (error) {
            console.error('Error loading company topics:', error);
            this.showMessage('Error loading topics: ' + error.message, 'error');
        }
    }

    async loadExistingDataPoints() {
        try {
            console.log('Fetching existing data points and assignments...');

            // Include inactive assignments if the toggle is on
            const includeInactiveParam = this.showingInactiveAssignments ? '?include_inactive=true' : '';

            const [dataPointsResponse, assignmentsResponse] = await Promise.all([
                fetch(`/admin/get_existing_data_points${includeInactiveParam}`),
                fetch('/admin/get_data_point_assignments')
            ]);
            
            if (!dataPointsResponse.ok) {
                throw new Error(`Failed to fetch existing data points: HTTP ${dataPointsResponse.status}`);
            }
            if (!assignmentsResponse.ok) {
                throw new Error(`Failed to fetch assignments: HTTP ${assignmentsResponse.status}`);
            }

            const existingPoints = await dataPointsResponse.json();
            const assignments = await assignmentsResponse.json();
            
            console.log('Loaded existing points:', existingPoints.length);
            console.log('Loaded assignments:', assignments.length);
            
            // Load existing data points into selectedDataPoints
            existingPoints.forEach(point => {
                this.selectedDataPoints.set(point.field_id.toString(), point);
            });

            // Load assignments and configurations
            this.loadAssignments(assignments);
            
            // Update UI
            this.updateSelectedDataPointsList();
            this.updateSelectedCount();
            
        } catch (error) {
            console.error('Error loading existing data points:', error);
            this.showMessage('Error loading existing data points: ' + error.message, 'error');
        }
    }

    loadAssignments(assignments) {
        // Group assignments by field_id
        const assignmentMap = {};
        assignments.forEach(assign => {
            const fieldId = assign.field_id.toString();
            if (!assignmentMap[fieldId]) {
                assignmentMap[fieldId] = [];
            }
            assignmentMap[fieldId].push(assign.entity_id.toString());
        });

        // Load configurations
        assignments.forEach(assign => {
            const fieldId = assign.field_id.toString();
            if (!this.configurations.has(fieldId)) {
                this.configurations.set(fieldId, {
                    fy_start_month: assign.fy_start_month || 4,
                    fy_start_year: assign.fy_start_year || new Date().getFullYear(),
                    fy_end_year: assign.fy_end_year || (new Date().getFullYear() + 1),
                    frequency: assign.frequency || 'Annual',
                    unit: assign.unit || '',
                    entities: assignmentMap[fieldId] || []
                });
            }

            // Load topic assignments
            if (assign.assigned_topic_id) {
                this.topicAssignments.set(fieldId, assign.assigned_topic_id);
            }
        });

        // Load entity assignments into entityAssignments Map for button state tracking
        Object.keys(assignmentMap).forEach(fieldId => {
            this.entityAssignments.set(fieldId, new Set(assignmentMap[fieldId]));
        });
    }

    async handleFrameworkChange(event) {
        const frameworkId = event.target.value;
        const availableFields = document.getElementById('availableFields');
        
        // Also reload topic tree when framework changes
        this.loadTopicTree();
        
        // Reload table view if it's currently visible
        const tableView = document.getElementById('tableView');
        if (tableView && tableView.style.display !== 'none') {
            this.loadTableView();
        }
        
        if (!frameworkId) {
            availableFields.innerHTML = '<div class="empty-state"><i class="fas fa-info-circle"></i><p>Select a framework to view available data points</p></div>';
            return;
        }

        try {
            availableFields.innerHTML = '<div class="loading-state"><i class="fas fa-spinner fa-spin"></i><p>Loading data points...</p></div>';
            
            const response = await fetch(`/admin/get_framework_fields/${frameworkId}`);
            if (!response.ok) throw new Error('Failed to fetch framework fields');
            
            const fields = await response.json();

            // Store all available fields for use in export and other operations
            this.availableFields = fields;

            if (fields.length === 0) {
                availableFields.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>No data points available for this framework</p></div>';
                return;
            }

            // Filter out already selected fields
            const availableFields_filtered = fields.filter(field => 
                !this.selectedDataPoints.has(field.field_id.toString())
            );

            this.renderAvailableDataPoints(availableFields_filtered);
            this.showMessage(`Loaded ${fields.length} data points for selected framework`, 'success');
            
        } catch (error) {
            console.error('Error loading framework fields:', error);
            availableFields.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Error loading data points</p></div>';
            this.showMessage('Error loading framework fields', 'error');
        }
    }

    renderAvailableDataPoints(fields) {
        const container = document.getElementById('availableFields');
        
        if (fields.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-check-circle"></i><p>All data points from this framework are already selected</p></div>';
            return;
        }

        container.innerHTML = fields.map(field => this.createDataPointCardHTML(field)).join('');
        
        // Add event listeners to cards
        container.querySelectorAll('.data-point-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.add-point')) {
                    card.querySelector('.add-point')?.click();
                }
            });
            
            const addBtn = card.querySelector('.add-point');
            addBtn?.addEventListener('click', (e) => {
                e.stopPropagation();
                this.addDataPoint(field);
            });
        });
    }

    createDataPointCardHTML(field) {
        const fieldId = field.field_id || field.id;
        const isComputed = field.is_computed ? 'block' : 'none';
        
        return `
            <div class="data-point-card" data-field-id="${fieldId}">
                <div class="card-content">
                    <div class="point-info">
                        <h5 class="point-name">${field.field_name || field.name}</h5>
                        <div class="point-meta">
                        </div>
                        <div class="point-details">
                            <small class="field-code">Code: ${field.field_code || 'Not set'}</small>
                            <small class="unit-category">Category: ${field.unit_category || 'Not set'}</small>
                        </div>
                    </div>
                    <div class="card-actions">
                        <button class="btn btn-sm btn-primary add-point">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    addDataPoint(field) {
        const fieldId = field.field_id.toString();
        
        if (this.selectedDataPoints.has(fieldId)) {
            this.showMessage('Data point already selected', 'warning');
            return;
        }

        this.selectedDataPoints.set(fieldId, field);
        this.updateSelectedDataPointsList();
        this.updateSelectedCount();
        
        // Remove from available list
        const availableCard = document.querySelector(`#availableFields .data-point-card[data-field-id="${fieldId}"]`);
        availableCard?.remove();
        
        this.showMessage('Data point added to selection', 'success');
    }

    updateSelectedDataPointsList() {
        const container = document.getElementById('selectedDataPointsList');
        
        if (this.selectedDataPoints.size === 0) {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-clipboard-list"></i><p>No data points selected yet</p><small>Add data points from the left panel to configure them</small></div>';
            this.updateToolbarButtons();
            return;
        }

        // Group data points by topic for organized display
        const topicGroups = this.groupDataPointsByTopic();
        
        if (topicGroups.size === 0) {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-clipboard-list"></i><p>No data points selected yet</p><small>Add data points from the left panel to configure them</small></div>';
            this.updateToolbarButtons();
            return;
        }

        container.innerHTML = this.createTopicGroupsHTML(topicGroups);

        // Add event listeners
        container.querySelectorAll('.selected-point-item').forEach(item => {
            const fieldId = item.dataset.fieldId;

            // Checkbox selection
            const checkbox = item.querySelector('.point-select');
            checkbox?.addEventListener('change', () => this.updateSelectionState());

            // Remove button
            const removeBtn = item.querySelector('.remove-point');
            removeBtn?.addEventListener('click', () => this.removeDataPoint(fieldId));

            // Individual configure button
            const configBtn = item.querySelector('.configure-single');
            configBtn?.addEventListener('click', () => this.configureSingleDataPoint(fieldId));

                    // Individual assign entities button
        const assignBtn = item.querySelector('.assign-single');
        assignBtn?.addEventListener('click', () => this.assignEntitiesToSingle(fieldId));

        // Individual field info button
        const infoBtn = item.querySelector('.field-info-single');
        infoBtn?.addEventListener('click', () => this.showFieldInfo(fieldId));

        // Update button status for this data point
        this.updateButtonStatus(fieldId);
        
        // Dependency card collapsible headers
        const dependencyHeaders = item.querySelectorAll('.dependencies-section .dependency-header');
        dependencyHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const section = header.closest('.dependencies-section');
                const items = section.querySelector('.dependency-items');
                const toggleIcon = header.querySelector('i');
                
                if (items.style.display === 'none') {
                    items.style.display = 'block';
                    toggleIcon.classList.remove('fa-chevron-right');
                    toggleIcon.classList.add('fa-chevron-down');
                } else {
                    items.style.display = 'none';
                    toggleIcon.classList.remove('fa-chevron-down');
                    toggleIcon.classList.add('fa-chevron-right');
                }
            });
        });
        
        // Dependency info buttons
        const dependencyInfoBtns = item.querySelectorAll('.dependency-info-btn');
        dependencyInfoBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const dependencyFieldId = btn.dataset.fieldId;
                this.openFieldInfoModal(dependencyFieldId);
            });
        });
        });

        this.updateToolbarButtons();
        this.updateDenseMode();
    }

    updateDenseMode() {
        const container = document.getElementById('selectedDataPointsList');
        if (!container) return;

        // Enable dense mode when there are more than 10 data points
        if (this.selectedDataPoints.size > 10) {
            container.classList.add('dense-mode');
        } else {
            container.classList.remove('dense-mode');
        }
    }

    createSelectedPointHTML(point) {
        const fieldId = point.field_id.toString();
        const config = this.configurations.get(fieldId);
        const entities = this.entityAssignments.get(fieldId) || new Set();

        const isConfigured = config !== undefined;
        const hasEntities = entities.size > 0;
        const isInactive = this.isInactiveAssignment(point);

        // Build CSS classes
        let itemClass = isConfigured ? 'configured' : '';
        if (isInactive) {
            itemClass += ' inactive';
        }

        const configStatusClass = isConfigured ? 'configured' : '';
        const configValue = isConfigured ? 'Configured' : 'Not configured';
        
        const entityStatusClass = hasEntities ? 'assigned' : '';
        const entityValue = hasEntities ? `${entities.size} entities assigned` : 'No entities assigned';

        return `
            <div class="selected-point-item ${itemClass}" data-field-id="${fieldId}">
                <div class="point-checkbox">
                    <input type="checkbox" class="point-select">
                </div>
                <div class="point-content">
                    <div class="point-main-info">
                        <div class="point-header">
                            <h5 class="point-name">${point.field_name || point.name}</h5>
                            ${isInactive ? '<span class="inactive-badge"><i class="fas fa-pause-circle"></i> Inactive</span>' : ''}
                        </div>
                    </div>
                    <div class="point-status-indicators">
                        <div class="status-item">
                            <div class="status-icon config-status ${configStatusClass}">
                                <i class="fas fa-cog"></i>
                            </div>
                            <div class="status-text">
                                <span class="status-label">Config:</span>
                                <span class="status-value ${configStatusClass}">${configValue}</span>
                            </div>
                        </div>
                        <div class="status-item">
                            <div class="status-icon entity-status ${entityStatusClass}">
                                <i class="fas fa-building"></i>
                            </div>
                            <div class="status-text">
                                <span class="status-label">Entities:</span>
                                <span class="status-value ${entityStatusClass}">${entityValue}</span>
                            </div>
                        </div>
                    </div>
                    ${this.createDependenciesHTML(point, fieldId)}
                    <div class="point-actions">
                        <button type="button" class="action-btn info field-info-single" data-field-id="${fieldId}" title="View field information">
                            <i class="fas fa-info-circle"></i> Info
                        </button>
                        <button type="button" class="action-btn configure-single" data-field-id="${fieldId}" title="Configure this data point">
                            <i class="fas fa-cog"></i> Config
                        </button>
                        <button type="button" class="action-btn secondary assign-single" data-field-id="${fieldId}" title="Assign entities to this data point">
                            <i class="fas fa-building"></i> Entities
                        </button>
                        <button type="button" class="remove-point" data-field-id="${fieldId}" title="Remove from selection">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    createDependenciesHTML(point, fieldId) {
        // Only show dependencies for computed fields
        if (!point.is_computed || !point.dependencies || point.dependencies.length === 0) {
            return '';
        }

        const dependenciesHTML = point.dependencies.map(dep => {
            const isAutoAdded = this.selectedDataPoints.has(dep.field_id);
            const config = this.configurations.get(dep.field_id);
            const isInherited = config?.isAutoAssigned;
            const hasConflicts = config?.hasConflicts;

            const statusClass = isInherited ? 'auto-added' : 'existing';
            const statusText = isInherited ? 'Auto-added' : 'Existing';

            return `
                <div class="dependency-item" data-field-id="${dep.field_id}">
                    <div class="dependency-content">
                        <div class="dependency-indicator">
                            <i class="fas fa-link dependency-icon"></i>
                        </div>
                        <div class="dependency-info">
                            <span class="dependency-name">${dep.field_name}</span>
                            <div class="dependency-meta">
                                <span class="dependency-status ${statusClass}">${statusText}</span>
                                ${hasConflicts ? '<span class="dependency-conflict"><i class="fas fa-exclamation-triangle"></i> Conflict</span>' : ''}
                            </div>
                        </div>
                        <div class="dependency-actions">
                            <button class="dependency-info-btn btn btn-sm btn-outline-secondary" data-field-id="${dep.field_id}" title="View dependency info">
                                <i class="fas fa-info"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        return `
            <div class="dependencies-section" data-parent-id="${fieldId}">
                <div class="dependencies-header">
                    <div class="dependencies-toggle">
                        <i class="fas fa-chevron-right toggle-icon"></i>
                        <span class="dependencies-title">Dependencies (<span class="dep-count">${point.dependencies.length}</span>)</span>
                    </div>
                    <div class="dependencies-info">
                        <i class="fas fa-info-circle" title="Auto-added dependencies inherit configuration"></i>
                    </div>
                </div>
                <div class="dependencies-list" style="display: none;">
                    ${dependenciesHTML}
                </div>
            </div>
        `;
    }

    async removeDataPoint(fieldId) {
        const fieldData = this.selectedDataPoints.get(fieldId);
        if (!fieldData) {
            this.showMessage('Error: Field data not found', 'error');
            return;
        }

        // Show confirmation dialog
        const confirmMessage = `Are you sure you want to remove "${fieldData.field_name}" from assignments?\n\n` +
                             `This will deactivate all assignments for this field, preventing users from submitting data.\n` +
                             `All existing data will be preserved and can be reactivated later if needed.`;

        if (!confirm(confirmMessage)) {
            return;
        }

        try {
            // Show loading state
            this.showMessage('Removing field assignments...', 'info');

            // First, get all assignments for this field
            const assignmentsResponse = await fetch(`/admin/api/assignments/by-field/${fieldId}`);
            const assignmentsData = await assignmentsResponse.json();

            if (!assignmentsData.success) {
                this.showMessage(`Error: Unable to find assignments for field "${fieldData.field_name}"`, 'error');
                return;
            }

            const assignments = assignmentsData.assignments || [];
            const activeAssignments = assignments.filter(a => a.is_active);

            if (activeAssignments.length === 0) {
                // No active assignments, just remove from local UI
                this.selectedDataPoints.delete(fieldId);
                this.configurations.delete(fieldId);
                this.entityAssignments.delete(fieldId);
                this.currentSelectedPoints.delete(fieldId);

                this.updateSelectedDataPointsList();
                this.updateSelectedCount();

                this.showMessage(`No active assignments found for "${fieldData.field_name}". Removed from selection.`, 'success');
                return;
            }

            // Deactivate all active assignments
            let deactivatedCount = 0;
            let errors = [];

            for (const assignment of activeAssignments) {
                try {
                    const deactivateResponse = await fetch(`/admin/api/assignments/${assignment.id}/deactivate`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            reason: `Field removed from assignment interface - Field: ${fieldData.field_name} (Entity: ${assignment.entity_name})`
                        })
                    });

                    const deactivateData = await deactivateResponse.json();
                    if (deactivateData.success) {
                        deactivatedCount++;
                    } else {
                        errors.push(`${assignment.entity_name}: ${deactivateData.error || 'Unknown error'}`);
                    }
                } catch (error) {
                    errors.push(`${assignment.entity_name}: ${error.message}`);
                }
            }

            // Remove from local UI state
            this.selectedDataPoints.delete(fieldId);
            this.configurations.delete(fieldId);
            this.entityAssignments.delete(fieldId);
            this.currentSelectedPoints.delete(fieldId);

            this.updateSelectedDataPointsList();
            this.updateSelectedCount();

            // Show results
            if (deactivatedCount > 0) {
                const message = `Successfully deactivated ${deactivatedCount} assignment(s) for "${fieldData.field_name}".\n` +
                              `Users can no longer submit data for this field. All existing data is preserved.\n` +
                              `Assignments can be reactivated later if needed.`;
                this.showMessage(message, 'success');
            }

            if (errors.length > 0) {
                console.error('Assignment deactivation errors:', errors);
                this.showMessage(`Some assignments could not be deactivated: ${errors.join(', ')}`, 'warning');
            }

        } catch (error) {
            console.error('Error removing data point assignments:', error);
            this.showMessage(`Error removing field assignments: ${error.message}`, 'error');
        }
    }

    configureSingleDataPoint(fieldId) {
        // Clear current selection checkboxes
        document.querySelectorAll('.point-select').forEach(checkbox => {
            checkbox.checked = false;
        });

        // Check only this data point's checkbox
        const targetItem = document.querySelector(`[data-field-id="${fieldId}"]`);
        const targetCheckbox = targetItem?.querySelector('.point-select');
        if (targetCheckbox) {
            targetCheckbox.checked = true;
        }

        // Clear and update currentSelectedPoints directly
        this.currentSelectedPoints.clear();
        this.currentSelectedPoints.add(fieldId);

        // Update toolbar buttons state
        this.updateToolbarButtons();

        // Open configuration modal
        this.openConfigurationModal();
    }

    assignEntitiesToSingle(fieldId) {
        // Clear current selection checkboxes
        document.querySelectorAll('.point-select').forEach(checkbox => {
            checkbox.checked = false;
        });

        // Check only this data point's checkbox
        const targetItem = document.querySelector(`[data-field-id="${fieldId}"]`);
        const targetCheckbox = targetItem?.querySelector('.point-select');
        if (targetCheckbox) {
            targetCheckbox.checked = true;
        }

        // Clear and update currentSelectedPoints directly
        this.currentSelectedPoints.clear();
        this.currentSelectedPoints.add(fieldId);

        // Update toolbar buttons state
        this.updateToolbarButtons();

        // Open entity assignment modal
        this.openEntityModal();
    }

    openFieldInfoModal(fieldId) {
        const field = this.selectedDataPoints.get(fieldId);
        if (!field) {
            this.showMessage('Field not found', 'error');
            return;
        }

        // Populate field information
        document.getElementById('fieldInfoName').textContent = field.field_name || field.name || '-';
        document.getElementById('fieldInfoType').textContent = field.value_type || 'NUMBER';
        document.getElementById('fieldInfoTopic').textContent = field.topic || 'General';
        document.getElementById('fieldInfoFramework').textContent = field.framework_name || '-';
        document.getElementById('fieldInfoUnitCategory').textContent = field.unit_category || '-';
        document.getElementById('fieldInfoDefaultUnit').textContent = field.default_unit || field.unit || '-';

        // Show computed field indicator
        const computedIndicator = document.getElementById('fieldInfoComputedIndicator');
        if (field.is_computed) {
            computedIndicator.style.display = 'block';
            computedIndicator.innerHTML = '<i class="fas fa-calculator text-warning"></i> <strong>Computed Field</strong>';
        } else {
            computedIndicator.style.display = 'none';
        }

        // Show description if available
        const descriptionSection = document.getElementById('fieldInfoDescription');
        const descriptionText = document.getElementById('fieldInfoDescriptionText');
        if (field.description) {
            descriptionText.textContent = field.description;
            descriptionSection.style.display = 'block';
        } else {
            descriptionSection.style.display = 'none';
        }

        // Enhanced computed field information
        const computedDetailsSection = document.getElementById('fieldInfoComputedDetails');
        if (field.is_computed && field.dependencies && field.dependencies.length > 0) {
            computedDetailsSection.style.display = 'block';
            
            // Show calculation formula if available
            const formulaElement = document.getElementById('fieldInfoFormula');
            if (field.calculation_formula) {
                formulaElement.textContent = field.calculation_formula;
                formulaElement.parentElement.style.display = 'block';
            } else {
                formulaElement.parentElement.style.display = 'none';
            }
            
            // Show dependencies
            const dependenciesList = document.getElementById('fieldInfoDependencies');
            dependenciesList.innerHTML = field.dependencies.map(dep => `
                <div class="dependency-item">
                    <i class="fas fa-arrow-right text-muted"></i>
                    <span class="dependency-name">${dep.field_name || dep.name}</span>
                    <span class="dependency-meta text-muted">(${dep.framework_name || 'Unknown Framework'})</span>
                    ${dep.is_computed ? '<i class="fas fa-calculator text-warning ms-2" title="Also computed"></i>' : ''}
                </div>
            `).join('');
            
            // Show dependency tree depth
            const treeInfo = document.getElementById('fieldInfoTreeInfo');
            const maxDepth = this.calculateDependencyDepth(field);
            treeInfo.textContent = `Dependency depth: ${maxDepth} level${maxDepth !== 1 ? 's' : ''}`;
            
        } else if (field.is_computed) {
            computedDetailsSection.style.display = 'block';
            document.getElementById('fieldInfoDependencies').innerHTML = '<div class="text-muted">No dependencies defined</div>';
            document.getElementById('fieldInfoTreeInfo').textContent = 'Simple computed field';
        } else {
            computedDetailsSection.style.display = 'none';
        }

        // Show conflict warnings for computed fields
        const conflictSection = document.getElementById('fieldInfoConflicts');
        if (field.is_computed && this.hasConfigurationConflicts(fieldId)) {
            conflictSection.style.display = 'block';
            const conflicts = this.getConfigurationConflicts(fieldId);
            const conflictList = document.getElementById('fieldInfoConflictList');
            conflictList.innerHTML = conflicts.map(conflict => `
                <div class="alert alert-warning py-2">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>${conflict.type}:</strong> ${conflict.message}
                    ${conflict.suggestion ? `<br><small class="text-muted">${conflict.suggestion}</small>` : ''}
                </div>
            `).join('');
        } else {
            conflictSection.style.display = 'none';
        }

        // Setup unit override
        this.setupUnitOverride(field);

        // Store current field ID for saving
        this.currentFieldInfoId = fieldId;

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('fieldInfoModal'));
        modal.show();
    }

    async setupUnitOverride(field) {
        const currentUnitDisplay = document.getElementById('currentUnitDisplay');
        const unitOverrideSelect = document.getElementById('unitOverrideSelect');

        // Check if unit override elements exist (they may not exist in all modal contexts)
        if (!currentUnitDisplay || !unitOverrideSelect) {
            console.log('Unit override elements not found, skipping setupUnitOverride');
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
                console.error('Error loading unit options:', error);
            }
        }
    }

    async getFieldAssignment(fieldId) {
        try {
            const response = await fetch('/admin/get_existing_data_points');
            const assignments = await response.json();
            return assignments.find(a => a.field_id.toString() === fieldId.toString());
        } catch (error) {
            console.error('Error getting field assignment:', error);
            return null;
        }
    }

    setupNewUIComponents() {
        try {
            // Setup view toggle between topic tree and flat list
            this.setupViewToggle();
            
            // Setup topic tree functionality
            this.setupTopicTree();
            
            // Setup clear filters functionality
            this.setupClearFilters();
            
            // Setup search functionality
            this.setupSmartSearch();
            
            console.log('New UI components setup completed');
        } catch (error) {
            console.error('Error setting up new UI components:', error);
        }
    }

    setupViewToggle() {
        const topicTreeViewBtn = document.getElementById('topicTreeViewBtn');
        const flatListViewBtn = document.getElementById('flatListViewBtn');
        const topicTreeView = document.getElementById('topicTreeView');
        const flatListView = document.getElementById('flatListView');

        if (!topicTreeViewBtn || !flatListViewBtn || !topicTreeView || !flatListView) {
            console.warn('View toggle elements not found, skipping setup');
            console.warn('Missing elements:', {
                topicTreeViewBtn: !!topicTreeViewBtn,
                flatListViewBtn: !!flatListViewBtn,
                topicTreeView: !!topicTreeView,
                flatListView: !!flatListView
            });
            return;
        }

        // Function to hide all views
        const hideAllViews = () => {
            topicTreeView.style.display = 'none';
            flatListView.style.display = 'none';
        };

        // Function to remove active class from all buttons and update ARIA attributes
        const removeActiveFromAll = () => {
            [topicTreeViewBtn, flatListViewBtn].forEach(btn => {
                if (btn) {
                    btn.classList.remove('active');
                    btn.setAttribute('aria-selected', 'false');
                }
            });
        };

        topicTreeViewBtn.addEventListener('click', () => {
            // Switch to topic tree view
            removeActiveFromAll();
            hideAllViews();
            topicTreeViewBtn.classList.add('active');
            topicTreeViewBtn.setAttribute('aria-selected', 'true');
            topicTreeView.style.display = 'block';

            // Load topic tree if not already loaded
            this.loadTopicTree();
        });

        flatListViewBtn.addEventListener('click', () => {
            // Switch to flat list view
            removeActiveFromAll();
            hideAllViews();
            flatListViewBtn.classList.add('active');
            flatListViewBtn.setAttribute('aria-selected', 'true');
            flatListView.style.display = 'block';

            // Load data points if not already loaded
            this.loadDataPoints();
        });

        // Default to topic tree view and load it
        this.loadTopicTree();
    }

    setupTopicTree() {
        const expandAllBtn = document.getElementById('expandAllTopics');
        const collapseAllBtn = document.getElementById('collapseAllTopics');

        if (expandAllBtn) {
            expandAllBtn.addEventListener('click', () => this.expandAllTopics());
        }

        if (collapseAllBtn) {
            collapseAllBtn.addEventListener('click', () => this.collapseAllTopics());
        }
    }

    setupTableView() {
        const selectAllTableRows = document.getElementById('selectAllTableRows');
        const selectAllVisibleTable = document.getElementById('selectAllVisibleTable');
        const addSelectedFromTable = document.getElementById('addSelectedFromTable');

        if (selectAllTableRows) {
            selectAllTableRows.addEventListener('change', (e) => {
                // Toggle all visible table row checkboxes
                const checkboxes = document.querySelectorAll('#dataPointsTableBody .table-checkbox');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = e.target.checked;
                    // Update row selection visual
                    const row = checkbox.closest('tr');
                    if (checkbox.checked) {
                        row.classList.add('selected');
                    } else {
                        row.classList.remove('selected');
                    }
                });
                this.updateTableSelectionButtons();
            });
        }

        if (selectAllVisibleTable) {
            selectAllVisibleTable.addEventListener('click', () => {
                if (selectAllTableRows) {
                    selectAllTableRows.checked = true;
                    selectAllTableRows.dispatchEvent(new Event('change'));
                }
            });
        }

        if (addSelectedFromTable) {
            addSelectedFromTable.addEventListener('click', () => {
                this.addSelectedFromTable();
            });
        }
    }

    async loadTableView() {
        try {
            console.log('Loading table view data...');
            const tableBody = document.getElementById('dataPointsTableBody');
            
            if (!tableBody) {
                console.warn('Table body not found');
                return;
            }

            // Show loading state
            tableBody.innerHTML = `
                <tr class="loading-row">
                    <td colspan="4" class="text-center">
                        <i class="fas fa-spinner fa-spin"></i>
                        Loading data points...
                    </td>
                </tr>
            `;

            // Get framework filter
            const frameworkSelect = document.getElementById('framework_select');
            const selectedFramework = frameworkSelect ? frameworkSelect.value : '';

            // Fetch data points from API
            let apiUrl = '/admin/frameworks/all_data_points';
            if (selectedFramework && selectedFramework.trim() !== '') {
                apiUrl += `?framework_id=${encodeURIComponent(selectedFramework)}`;
            }

            const response = await fetch(apiUrl);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const dataPoints = await response.json();
            
            if (dataPoints.length === 0) {
                tableBody.innerHTML = `
                    <tr class="empty-table-state">
                        <td colspan="4">
                            <div class="empty-table-state">
                                <i class="fas fa-database"></i>
                                <p>No data points available</p>
                                <small>Try selecting a different framework or clearing filters</small>
                            </div>
                        </td>
                    </tr>
                `;
                return;
            }

            // Populate table with data points
            tableBody.innerHTML = dataPoints.map(point => {
                const isSelected = this.selectedDataPoints.has(point.field_id.toString());
                return `
                    <tr ${isSelected ? 'class="selected"' : ''}>
                        <td>
                            <input type="checkbox" 
                                   class="table-checkbox" 
                                   data-field-id="${point.field_id}"
                                   ${isSelected ? 'checked' : ''}>
                        </td>
                        <td>
                            <a href="#" class="table-field-name" data-field-id="${point.field_id}">
                                ${point.field_name || 'Unnamed Field'}
                            </a>
                        </td>
                        <td>
                            <span class="table-framework">${point.framework_name || 'Unknown Framework'}</span>
                        </td>
                        <td>
                            <button class="table-action-btn add-from-table" 
                                    data-field-id="${point.field_id}"
                                    ${isSelected ? 'disabled' : ''}>
                                ${isSelected ? 'Added' : 'Add'}
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');

            // Setup event listeners for table rows
            this.setupTableRowListeners();
            this.updateTableSelectionButtons();

            console.log(`Table view loaded with ${dataPoints.length} data points`);
        } catch (error) {
            console.error('Error loading table view:', error);
            const tableBody = document.getElementById('dataPointsTableBody');
            if (tableBody) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center text-danger">
                            <i class="fas fa-exclamation-triangle"></i>
                            Error loading data: ${error.message}
                        </td>
                    </tr>
                `;
            }
        }
    }

    setupTableRowListeners() {
        // Individual checkbox change handlers
        const checkboxes = document.querySelectorAll('#dataPointsTableBody .table-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const row = checkbox.closest('tr');
                const fieldId = checkbox.dataset.fieldId;
                
                if (checkbox.checked) {
                    row.classList.add('selected');
                } else {
                    row.classList.remove('selected');
                }
                
                this.updateTableSelectionButtons();
                
                // Update select all checkbox state
                const selectAllCheckbox = document.getElementById('selectAllTableRows');
                if (selectAllCheckbox) {
                    const allCheckboxes = document.querySelectorAll('#dataPointsTableBody .table-checkbox');
                    const checkedCheckboxes = document.querySelectorAll('#dataPointsTableBody .table-checkbox:checked');
                    selectAllCheckbox.checked = allCheckboxes.length > 0 && allCheckboxes.length === checkedCheckboxes.length;
                }
            });
        });

        // Field name click handlers (show info)
        const fieldLinks = document.querySelectorAll('.table-field-name');
        fieldLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const fieldId = link.dataset.fieldId;
                this.showFieldInfo(fieldId);
            });
        });

        // Add button handlers
        const addButtons = document.querySelectorAll('.add-from-table');
        addButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const fieldId = button.dataset.fieldId;
                this.addSingleDataPointFromTable(fieldId);
            });
        });
    }

    updateTableSelectionButtons() {
        const selectedCheckboxes = document.querySelectorAll('#dataPointsTableBody .table-checkbox:checked');
        const addSelectedBtn = document.getElementById('addSelectedFromTable');
        
        if (addSelectedBtn) {
            addSelectedBtn.disabled = selectedCheckboxes.length === 0;
            addSelectedBtn.innerHTML = selectedCheckboxes.length > 0 
                ? `<i class="fas fa-plus"></i> Add Selected (${selectedCheckboxes.length})`
                : '<i class="fas fa-plus"></i> Add Selected';
        }
    }

    async addSelectedFromTable() {
        const selectedCheckboxes = document.querySelectorAll('#dataPointsTableBody .table-checkbox:checked');
        
        if (selectedCheckboxes.length === 0) {
            this.showMessage('No data points selected', 'warning');
            return;
        }

        const fieldIds = Array.from(selectedCheckboxes).map(cb => cb.dataset.fieldId);
        console.log('Adding selected fields from table:', fieldIds);

        try {
            // Add each selected field
            for (const fieldId of fieldIds) {
                await this.addSingleDataPointFromTable(fieldId);
            }

            // Clear selections and refresh table
            selectedCheckboxes.forEach(cb => {
                cb.checked = false;
                cb.closest('tr').classList.remove('selected');
            });
            
            const selectAllCheckbox = document.getElementById('selectAllTableRows');
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = false;
            }

            this.updateTableSelectionButtons();
            this.showMessage(`Added ${fieldIds.length} data points`, 'success');
        } catch (error) {
            console.error('Error adding selected from table:', error);
            this.showMessage('Error adding selected data points: ' + error.message, 'error');
        }
    }

    async addSingleDataPointFromTable(fieldId) {
        try {
            // Get field data from the API 
            const response = await fetch(`/admin/frameworks/get_field_data/${fieldId}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch field data: HTTP ${response.status}`);
            }

            const fieldData = await response.json();
            
            // Add to selected data points
            this.selectedDataPoints.set(fieldId.toString(), fieldData);
            
            // Update UI
            this.updateSelectedDataPointsList();
            this.updateUIComponents();

            // Update table button for this field
            const addButton = document.querySelector(`button[data-field-id="${fieldId}"].add-from-table`);
            if (addButton) {
                addButton.disabled = true;
                addButton.textContent = 'Added';
            }
            
            // Update table row visual
            const checkbox = document.querySelector(`input[data-field-id="${fieldId}"].table-checkbox`);
            if (checkbox) {
                checkbox.checked = false;
                checkbox.closest('tr').classList.remove('selected');
            }

            console.log('Added field from table:', fieldData.field_name);
        } catch (error) {
            console.error('Error adding single field from table:', error);
            throw error;
        }
    }

    setupClearFilters() {
        const clearFiltersBtn = document.getElementById('clearFilters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                // Clear search input
                const searchInput = document.getElementById('dataPointSearch');
                if (searchInput) {
                    searchInput.value = '';
                }
                
                // Reset framework filter
                const frameworkSelect = document.getElementById('framework_select');
                if (frameworkSelect) {
                    frameworkSelect.value = '';
                }
                
                // Reload current view
                if (document.getElementById('topicTreeView').style.display !== 'none') {
                    this.loadTopicTree();
                } else if (document.getElementById('tableView').style.display !== 'none') {
                    this.loadTableView();
                } else {
                    this.loadDataPoints();
                }
            });
        }
    }

    setupSmartSearch() {
        const searchInput = document.getElementById('dataPointSearch');
        const clearSearchBtn = document.getElementById('clearSearch');
        
        if (!searchInput) {
            console.warn('Search input not found, skipping search setup');
            return;
        }

        let searchTimeout;
        
        // Setup search input with debouncing
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.trim();
            
            // Clear previous timeout
            clearTimeout(searchTimeout);
            
            // Debounce search - wait 300ms after user stops typing
            searchTimeout = setTimeout(() => {
                if (searchTerm.length >= 2) {
                    this.performSearch(searchTerm);
                } else if (searchTerm.length === 0) {
                    this.clearSearch();
                } else {
                    // Show hint for minimum characters
                    this.showSearchHint();
                }
            }, 300);
        });

        // Setup clear search button
        if (clearSearchBtn) {
            clearSearchBtn.addEventListener('click', () => {
                searchInput.value = '';
                this.clearSearch();
                searchInput.focus();
            });
        }

        // Setup framework filter interaction with search
        const frameworkSelect = document.getElementById('framework_select');
        if (frameworkSelect) {
            frameworkSelect.addEventListener('change', () => {
                const searchTerm = searchInput.value.trim();
                if (searchTerm.length >= 2) {
                    this.performSearch(searchTerm);
                }
            });
        }
    }

    async performSearch(searchTerm) {
        try {
            console.log('Performing search:', searchTerm);
            
            // Show search results view
            this.showSearchResults();
            
            // Update search results title
            const searchTitle = document.getElementById('searchResultsTitle');
            if (searchTitle) {
                searchTitle.textContent = `Search Results for "${searchTerm}"`;
            }
            
            // Show loading state
            const searchResults = document.getElementById('searchResults');
            if (searchResults) {
                searchResults.innerHTML = `
                    <div class="loading-state">
                        <i class="fas fa-spinner fa-spin"></i>
                        <p>Searching...</p>
                    </div>
                `;
            }

            // Get framework filter
            const frameworkSelect = document.getElementById('framework_select');
            const frameworkFilter = frameworkSelect ? frameworkSelect.value : '';

            // Build search URL with parameters
            const searchParams = new URLSearchParams({
                search: searchTerm
            });
            
            if (frameworkFilter) {
                searchParams.append('framework_id', frameworkFilter);
            }

            // Perform search API call
            const response = await fetch(`/admin/frameworks/all_data_points?${searchParams}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success && data.data_points) {
                this.renderSearchResults(data.data_points, searchTerm);
            } else {
                this.showNoSearchResults(searchTerm);
            }

        } catch (error) {
            console.error('Error performing search:', error);
            const searchResults = document.getElementById('searchResults');
            if (searchResults) {
                searchResults.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Search Error</p>
                        <small>${error.message}</small>
                    </div>
                `;
            }
        }
    }

    showSearchResults() {
        const searchResultsView = document.getElementById('searchResultsView');
        const topicTreeView = document.getElementById('topicTreeView');
        const flatListView = document.getElementById('flatListView');

        if (searchResultsView) searchResultsView.style.display = 'block';
        if (topicTreeView) topicTreeView.style.display = 'none';
        if (flatListView) flatListView.style.display = 'none';

        // Update view toggle buttons to show search state
        const topicTreeBtn = document.getElementById('topicTreeViewBtn');
        const flatListBtn = document.getElementById('flatListViewBtn');
        if (topicTreeBtn) topicTreeBtn.classList.remove('active');
        if (flatListBtn) flatListBtn.classList.remove('active');
    }

    clearSearch() {
        const searchResultsView = document.getElementById('searchResultsView');
        const topicTreeView = document.getElementById('topicTreeView');
        
        if (searchResultsView) searchResultsView.style.display = 'none';
        if (topicTreeView) topicTreeView.style.display = 'block';

        // Restore topic tree button as active
        const topicTreeBtn = document.getElementById('topicTreeViewBtn');
        if (topicTreeBtn) topicTreeBtn.classList.add('active');
    }

    showSearchHint() {
        const searchResults = document.getElementById('searchResults');
        if (searchResults) {
            searchResults.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <p>Type at least 2 characters to search</p>
                    <small>Search across field names, codes, and descriptions</small>
                </div>
            `;
        }
        this.showSearchResults();
    }

    renderSearchResults(dataPoints, searchTerm) {
        const searchResults = document.getElementById('searchResults');
        if (!searchResults) return;

        if (dataPoints.length === 0) {
            this.showNoSearchResults(searchTerm);
            return;
        }

        // Clear container
        searchResults.innerHTML = '';

        // Group results by framework for better organization
        const groupedResults = this.groupResultsByFramework(dataPoints);

        // Render grouped results
        Object.entries(groupedResults).forEach(([frameworkName, fields]) => {
            // Add framework group header
            const groupHeader = document.createElement('div');
            groupHeader.className = 'search-group-header';
            groupHeader.innerHTML = `
                <h6><i class="fas fa-layer-group"></i> ${frameworkName} (${fields.length})</h6>
            `;
            searchResults.appendChild(groupHeader);

            // Add fields in this group
            fields.forEach(field => {
                const resultElement = this.createSearchResultItem(field, searchTerm);
                searchResults.appendChild(resultElement);
            });
        });
    }

    groupResultsByFramework(dataPoints) {
        const grouped = {};
        
        dataPoints.forEach(field => {
            const frameworkName = field.framework_name || 'Uncategorized';
            if (!grouped[frameworkName]) {
                grouped[frameworkName] = [];
            }
            grouped[frameworkName].push(field);
        });

        // Sort each group by field name
        Object.values(grouped).forEach(fields => {
            fields.sort((a, b) => a.field_name.localeCompare(b.field_name));
        });

        return grouped;
    }

    createSearchResultItem(field, searchTerm) {
        const template = document.getElementById('searchResultItemTemplate');
        const element = template.content.cloneNode(true);
        
        const resultItem = element.querySelector('.search-result-item');
        resultItem.dataset.fieldId = field.field_id;
        
        // Set field name with highlighting
        const fieldNameEl = element.querySelector('.search-field-name');
        fieldNameEl.innerHTML = this.highlightSearchTerm(field.field_name, searchTerm);
        
        // Badges removed per user request
        
        // Set breadcrumb path
        const breadcrumbEl = element.querySelector('.breadcrumb-path');
        const breadcrumbPath = this.buildBreadcrumbPath(field);
        breadcrumbEl.textContent = breadcrumbPath;
        
        // Set description if available
        if (field.description && field.description.trim()) {
            const descriptionEl = element.querySelector('.field-description');
            const descriptionText = element.querySelector('.description-text');
            descriptionText.innerHTML = this.highlightSearchTerm(field.description, searchTerm);
            descriptionEl.style.display = 'block';
        }
        
        // Setup add button
        const addBtn = element.querySelector('.add-search-result');
        addBtn.addEventListener('click', () => {
            this.addDataPointFromSearch(field);
        });
        
        return element;
    }

    buildBreadcrumbPath(field) {
        const parts = [];
        
        if (field.framework_name) {
            parts.push(field.framework_name);
        }
        
        if (field.topic_path && field.topic_path !== 'Uncategorized') {
            parts.push(field.topic_path);
        }
        
        return parts.length > 0 ? parts.join(' > ') : 'Uncategorized';
    }

    highlightSearchTerm(text, searchTerm) {
        if (!text || !searchTerm) return text;
        
        const regex = new RegExp(`(${searchTerm})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    addDataPointFromSearch(field) {
        this.addDataPoint(field);
    }

    showNoSearchResults(searchTerm) {
        const searchResults = document.getElementById('searchResults');
        if (searchResults) {
            searchResults.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <p>No results found for "${searchTerm}"</p>
                    <small>Try different keywords or check your framework filter</small>
                </div>
            `;
        }
    }

    async loadDataPoints() {
        try {
            console.log('Loading flat list data points...');
            const flatListContainer = document.getElementById('flatListView');
            
            if (!flatListContainer) {
                console.warn('Flat list container not found');
                return;
            }

            // Show loading state
            flatListContainer.innerHTML = `
                <div class="loading-state">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Loading data points...</p>
                </div>
            `;

            // Get framework filter
            const frameworkSelect = document.getElementById('framework_select');
            const selectedFramework = frameworkSelect ? frameworkSelect.value : '';

            // Fetch data points from API
            let apiUrl = '/admin/frameworks/all_data_points';
            if (selectedFramework && selectedFramework.trim() !== '') {
                apiUrl += `?framework_id=${encodeURIComponent(selectedFramework)}`;
            }

            console.log('Fetching data points from API:', apiUrl);
            const response = await fetch(apiUrl);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('API response for data points:', data);

            if (data.success && data.data_points) {
                this.renderFlatDataPointsList(data.data_points, flatListContainer);
            } else {
                flatListContainer.innerHTML = `
                    <div class="no-data-message">
                        <i class="fas fa-info-circle"></i>
                        <p>No data points found</p>
                        <small>Try adjusting your framework filter</small>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading data points:', error);
            const flatListContainer = document.getElementById('flatListView');
            if (flatListContainer) {
                flatListContainer.innerHTML = `
                    <div class="error-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Error loading data points</p>
                        <small>${error.message}</small>
                    </div>
                `;
            }
        }
    }

    renderFlatDataPointsList(dataPoints, container) {
        if (!container) return;

        if (!dataPoints || dataPoints.length === 0) {
            container.innerHTML = `
                <div class="no-data-message">
                    <i class="fas fa-info-circle"></i>
                    <p>No data points available</p>
                    <small>Try different search criteria or framework selection</small>
                </div>
            `;
            return;
        }

        // Group data points by framework for better organization
        const groupedByFramework = dataPoints.reduce((acc, field) => {
            const frameworkName = field.framework_name || 'Unknown Framework';
            if (!acc[frameworkName]) {
                acc[frameworkName] = [];
            }
            acc[frameworkName].push(field);
            return acc;
        }, {});

        let html = '<div class="flat-data-points-list topic-tree-style">';

        // Render each framework group in topic-hierarchy style
        Object.entries(groupedByFramework).forEach(([frameworkName, fields]) => {
            html += `
                <div class="framework-node topic-node" data-framework="${frameworkName}">
                    <div class="framework-header topic-header" role="button" aria-expanded="true">
                        <div class="topic-toggle">
                            <i class="fas fa-chevron-down toggle-icon"></i>
                        </div>
                        <div class="topic-info">
                            <span class="framework-name topic-name">${frameworkName}</span>
                            <span class="field-count">(${fields.length} fields)</span>
                        </div>
                        <div class="topic-actions">
                            <button class="add-all-framework btn btn-sm btn-outline-primary"
                                    data-framework="${frameworkName}"
                                    title="Add all fields in this framework">
                                <i class="fas fa-plus-circle"></i> Add All
                            </button>
                        </div>
                    </div>
                    <div class="framework-fields topic-children">
            `;

            fields.forEach(field => {
                const isSelected = this.selectedDataPoints.has(field.field_id);
                const truncatedDescription = field.description && field.description.length > 60
                    ? field.description.substring(0, 60) + '...'
                    : (field.description || '');

                html += `
                    <div class="field-item topic-data-point"
                         data-field-id="${field.field_id}">
                        <div class="field-info">
                            <div class="field-details">
                                <div class="field-display">
                                    <div class="field-first-line">
                                        <span class="field-code">${field.field_code || ''}</span>
                                        <span class="field-name">${field.field_name}</span>
                                    </div>
                                    ${truncatedDescription ? `<div class="field-second-line">
                                        <span class="field-description" title="${field.description || ''}">${truncatedDescription}</span>
                                    </div>` : ''}
                                </div>
                            </div>
                        </div>
                        <div class="field-actions">
                            <button class="add-field-btn btn btn-sm btn-primary ${isSelected ? 'selected' : ''}"
                                    data-field-id="${field.field_id}"
                                    title="${isSelected ? 'Already selected' : 'Add this field'}">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;

        // Add event listeners for toggle functionality
        container.querySelectorAll('.framework-header').forEach(header => {
            header.addEventListener('click', (e) => {
                if (e.target.closest('.topic-actions')) return; // Don't toggle when clicking actions

                const frameworkNode = header.closest('.framework-node');
                const toggleIcon = header.querySelector('.toggle-icon');
                const children = frameworkNode.querySelector('.framework-fields');

                if (children.style.display === 'none') {
                    children.style.display = 'block';
                    toggleIcon.classList.remove('fa-chevron-right');
                    toggleIcon.classList.add('fa-chevron-down');
                    header.setAttribute('aria-expanded', 'true');
                } else {
                    children.style.display = 'none';
                    toggleIcon.classList.remove('fa-chevron-down');
                    toggleIcon.classList.add('fa-chevron-right');
                    header.setAttribute('aria-expanded', 'false');
                }
            });
        });

        // Add event listeners for individual field add buttons
        container.querySelectorAll('.add-field-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const fieldId = e.target.closest('.add-field-btn').dataset.fieldId;
                const field = dataPoints.find(f => f.field_id === fieldId);

                if (!button.classList.contains('selected') && field) {
                    this.addDataPoint(field);
                    button.classList.add('selected');
                    button.title = 'Already selected';
                }
            });
        });

        // Add event listeners for "Add All" framework buttons
        container.querySelectorAll('.add-all-framework').forEach(button => {
            button.addEventListener('click', (e) => {
                const frameworkName = e.target.closest('.add-all-framework').dataset.framework;
                const frameworkFields = groupedByFramework[frameworkName] || [];

                frameworkFields.forEach(field => {
                    if (!this.selectedDataPoints.has(field.field_id)) {
                        this.addDataPoint(field);
                    }
                });

                // Update button states
                const frameworkNode = e.target.closest('.framework-node');
                frameworkNode.querySelectorAll('.add-field-btn').forEach(fieldBtn => {
                    fieldBtn.classList.add('selected');
                    fieldBtn.title = 'Already selected';
                });
            });
        });
    }

    async loadTopicTree() {
        const topicTree = document.getElementById('topicTree');
        console.log('loadTopicTree called, topicTree element:', topicTree);
        if (!topicTree) {
            console.log('topicTree element not found, returning');
            return;
        }

        try {
            console.log('Loading topic tree...');
            // Show loading state
            topicTree.innerHTML = `
                <div class="loading-state">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Loading topic hierarchy...</p>
                </div>
            `;

            // Get selected framework for filtering
            const frameworkSelect = document.getElementById('framework_select');
            const selectedFramework = frameworkSelect ? frameworkSelect.value : '';
            
            // Build API URL with framework filter if selected
            let apiUrl = '/admin/frameworks/all_topics_tree';
            if (selectedFramework && selectedFramework.trim() !== '') {
                apiUrl += `?framework_id=${encodeURIComponent(selectedFramework)}`;
            }

            console.log('Fetching topics from API:', apiUrl);
            const response = await fetch(apiUrl);
            console.log('API response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const topics = await response.json();
            console.log('API response topics:', topics);
            this.renderTopicTree(topics, topicTree);

        } catch (error) {
            console.error('Error loading topic tree:', error);
            topicTree.innerHTML = `
                <div class="loading-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error loading topics</p>
                    <small>${error.message}</small>
                </div>
            `;
        }
    }

    renderTopicTree(topics, container) {
        console.log('renderTopicTree called with:', {
            topics: topics,
            topicsLength: topics ? topics.length : 'undefined',
            container: container,
            containerElement: container ? container.tagName : 'undefined'
        });

        if (!topics || topics.length === 0) {
            console.log('No topics available, showing empty state');
            container.innerHTML = `
                <div class="loading-state">
                    <i class="fas fa-info-circle"></i>
                    <p>No topics available</p>
                    <small>Create frameworks with topics to see them here</small>
                </div>
            `;
            return;
        }

        console.log('Clearing container and starting to render topics');
        container.innerHTML = '';
        
        topics.forEach((topic, index) => {
            console.log(`Creating topic node ${index + 1}/${topics.length}:`, topic);
            try {
                const topicElement = this.createTopicNode(topic, 0); // Start with level 0 for root topics
                console.log('Topic element created successfully:', topicElement);
                
                if (!topicElement) {
                    console.error('createTopicNode returned null/undefined for topic:', topic);
                    return; // Use return instead of continue in forEach
                }
                
                container.appendChild(topicElement);
                console.log('Topic element appended to container successfully');
            } catch (error) {
                console.error('Error creating/appending topic node:', error, topic);
                console.error('Error stack:', error.stack);
            }
        });
        
        console.log('renderTopicTree completed. Container children count:', container.children.length);
    }

    createTopicNode(topic, level = null) {
        console.log('createTopicNode called with:', {
            topic: topic,
            topicName: topic?.name,
            topicId: topic?.topic_id,
            level: level
        });
        
        const template = document.getElementById('topicNodeTemplate');
        console.log('Template found:', template);
        if (!template) {
            console.error('topicNodeTemplate not found!');
            return null;
        }
        
        const node = template.content.cloneNode(true);
        console.log('Node cloned:', node);
        
        const topicNodeDiv = node.querySelector('.topic-node');
        topicNodeDiv.dataset.topicId = topic.topic_id;
        const currentLevel = level !== null ? level : topic.level || 0;
        topicNodeDiv.dataset.level = currentLevel;
        
        // Apply hierarchical indentation
        const indentationLevel = Math.max(0, currentLevel);
        topicNodeDiv.style.marginLeft = `${indentationLevel * 20}px`;
        topicNodeDiv.classList.add('folder-item');
        
        // Set topic name and framework info with folder icon
        const topicName = node.querySelector('.topic-name');
        topicName.innerHTML = topic.name;
        
        const frameworkBadge = node.querySelector('.framework-badge');
        frameworkBadge.style.display = 'none'; // Hide framework name from topic display
        
        // Handle expand/collapse toggle
        const topicHeader = node.querySelector('.topic-header');
        const toggleIcon = node.querySelector('.toggle-icon');
        const childrenContainer = node.querySelector('.topic-children');
        
        if (topic.has_children || (topic.children && topic.children.length > 0) || (topic.field_count && topic.field_count > 0)) {
            topicHeader.addEventListener('click', (e) => {
                console.log('Topic header clicked:', topic.name, 'Event target:', e.target);
                if (e.target.closest('.topic-actions')) {
                    console.log('Clicked on topic actions, ignoring');
                    return; // Don't toggle when clicking actions
                }
                
                const isExpanded = topicNodeDiv.classList.contains('expanded');
                console.log('Current expanded state:', isExpanded);
                
                if (isExpanded) {
                    console.log('Collapsing topic:', topic.name);
                    topicNodeDiv.classList.remove('expanded');
                    childrenContainer.style.display = 'none';
                } else {
                    console.log('Expanding topic:', topic.name);
                    topicNodeDiv.classList.add('expanded');
                    childrenContainer.style.display = 'block';
                    
                    // Load children if not already loaded
                    if (childrenContainer.children.length === 0) {
                        console.log('Loading children for topic:', topic.name);
                        this.loadTopicChildren(topic, childrenContainer);
                    } else {
                        console.log('Children already loaded for topic:', topic.name);
                    }
                }
            });
        } else {
            // No children, hide toggle icon
            toggleIcon.style.opacity = '0.3';
        }

        // Handle "Select All" button
        const selectAllBtn = node.querySelector('.select-all-topic');
        selectAllBtn.addEventListener('click', () => {
            this.selectAllInTopic(topic.topic_id);
        });

        console.log('createTopicNode returning:', node, 'topicNodeDiv:', topicNodeDiv);
        return node;
    }

    async loadTopicChildren(topic, container) {
        try {
            console.log('Loading topic children for:', topic.name, 'Topic ID:', topic.topic_id);
            // Show loading for children
            container.innerHTML = '<div class="loading-state" style="padding: 1rem;"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';

            // Load data points for this topic
            const response = await fetch(`/admin/frameworks/all_data_points?topic_id=${topic.topic_id}`);
            console.log('API response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('API response data:', data);
            container.innerHTML = '';

            // Create hierarchical structure container
            const hierarchicalContainer = document.createElement('div');
            hierarchicalContainer.className = 'topic-hierarchy-container';

            // Add child topics first (folders)
            if (topic.children && topic.children.length > 0) {
                topic.children.forEach(childTopic => {
                    const childElement = this.createTopicNode(childTopic, topic.level + 1);
                    hierarchicalContainer.appendChild(childElement);
                });
            }

            // Add data points for this specific topic (files)
            if (data.success && data.data_points) {
                data.data_points.forEach(dataPoint => {
                    const pointElement = this.createTopicDataPoint(dataPoint, topic.level + 1);
                    hierarchicalContainer.appendChild(pointElement);
                });
            }

            container.appendChild(hierarchicalContainer);

            // Show empty state if no children or data points
            if ((!topic.children || topic.children.length === 0) && 
                (!data.success || !data.data_points || data.data_points.length === 0)) {
                const emptyState = document.createElement('div');
                emptyState.className = 'empty-topic-state';
                emptyState.innerHTML = `
                    <div style="padding: 1rem; color: #6c757d; font-style: italic;">
                        <i class="fas fa-folder-open"></i> Empty topic
                    </div>
                `;
                container.appendChild(emptyState);
            }

        } catch (error) {
            console.error('Error loading topic children:', error);
            container.innerHTML = `<div class="loading-state" style="padding: 1rem;"><i class="fas fa-exclamation-triangle"></i> Error loading data</div>`;
        }
    }

    createTopicDataPoint(dataPoint, level = 0) {
        const template = document.getElementById('topicDataPointTemplate');
        const node = template.content.cloneNode(true);
        
        const pointDiv = node.querySelector('.topic-data-point');
        pointDiv.dataset.fieldId = dataPoint.field_id;
        pointDiv.dataset.level = level;
        
        // Apply hierarchical indentation (data points are nested under topics)
        const indentationLevel = Math.max(0, level);
        pointDiv.style.marginLeft = `${indentationLevel * 20}px`;
        pointDiv.classList.add('file-item');
        
        // Set field name with file icon
        const fieldName = node.querySelector('.field-name');
        // Icons removed per user request
        fieldName.innerHTML = dataPoint.field_name;

        // Field type icons removed per user request
        
        // Badges removed per user request
        
        // Handle add button
        const addBtn = node.querySelector('.add-field-btn');
        addBtn.addEventListener('click', () => {
            this.addDataPointFromTree(dataPoint);
        });
        
        return node;
    }

    addDataPointFromTree(dataPoint) {
        // Use existing addDataPoint logic
        this.addDataPoint(dataPoint);
    }

    async selectAllInTopic(topicId) {
        try {
            console.log('Selecting all data points in topic:', topicId);
            
            // Load all data points for this topic (including descendants)
            const response = await fetch(`/admin/frameworks/all_data_points?topic_id=${topicId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (!data.success || !data.data_points) {
                throw new Error('No data points found for this topic');
            }

            let addedCount = 0;
            const errors = [];

            // Add each data point that isn't already selected
            for (const dataPoint of data.data_points) {
                if (!this.selectedDataPoints.has(dataPoint.field_id)) {
                    try {
                        await this.addDataPoint(dataPoint);
                        addedCount++;
                        
                        // For computed fields, auto-assign dependencies immediately
                        if (dataPoint.is_computed) {
                            await this.autoAssignDependencies(dataPoint);
                        }
                    } catch (error) {
                        console.error(`Error adding data point ${dataPoint.field_name}:`, error);
                        errors.push(`${dataPoint.field_name}: ${error.message}`);
                    }
                }
            }

            // Show success/error message
            if (addedCount > 0) {
                const message = `Added ${addedCount} data points from topic`;
                this.showNotification(message, 'success');
                
                if (errors.length > 0) {
                    console.warn('Some data points could not be added:', errors);
                    this.showNotification(`${errors.length} data points had issues`, 'warning');
                }
            } else if (data.data_points.length > 0) {
                this.showNotification('All data points in this topic are already selected', 'info');
            } else {
                this.showNotification('No data points found in this topic', 'info');
            }

        } catch (error) {
            console.error('Error selecting all in topic:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
        }
    }

    async autoAssignDependencies(computedField) {
        console.log('Auto-assigning dependencies for computed field:', computedField.field_name);
        
        if (!computedField.dependencies || computedField.dependencies.length === 0) {
            console.log('No dependencies found for computed field');
            return { success: true, addedCount: 0, conflicts: [] };
        }

        let addedCount = 0;
        let conflicts = [];
        const addedDependencies = [];

        try {
            // Process each dependency
            for (const dependency of computedField.dependencies) {
                if (!this.selectedDataPoints.has(dependency.field_id)) {
                    // Check for conflicts before adding
                    const conflictCheck = await this.checkDependencyConflicts(dependency, computedField);
                    
                    if (conflictCheck.hasConflicts) {
                        conflicts.push({
                            field: dependency,
                            conflicts: conflictCheck.conflicts
                        });
                        console.warn(`Conflict detected for dependency ${dependency.field_name}:`, conflictCheck.conflicts);
                    } else {
                        // No conflicts - add the dependency
                        try {
                            // Fetch full field data for the dependency
                            const fullDependencyData = await this.fetchFieldData(dependency.field_id);
                            
                            if (fullDependencyData) {
                                // Add dependency with inherited configuration
                                await this.addDataPointWithInheritedConfig(fullDependencyData, computedField);
                                addedDependencies.push(fullDependencyData);
                                addedCount++;
                                console.log(`Auto-added dependency: ${dependency.field_name}`);

                                // If this dependency is also computed, recursively add its dependencies
                                if (fullDependencyData.is_computed) {
                                    const subResult = await this.autoAssignDependencies(fullDependencyData);
                                    addedCount += subResult.addedCount;
                                    conflicts.push(...subResult.conflicts);
                                }
                            }
                        } catch (error) {
                            console.error(`Error adding dependency ${dependency.field_name}:`, error);
                            conflicts.push({
                                field: dependency,
                                conflicts: [`Error adding field: ${error.message}`]
                            });
                        }
                    }
                } else {
                    console.log(`Dependency ${dependency.field_name} already selected`);
                }
            }

            // Show notification about auto-assignment
            if (addedCount > 0 || conflicts.length > 0) {
                this.showDependencyAssignmentResults(computedField, addedCount, conflicts);
            }

            return { success: true, addedCount, conflicts, addedDependencies };

        } catch (error) {
            console.error('Error in auto-assignment:', error);
            return { success: false, error: error.message, addedCount, conflicts };
        }
    }

    async fetchFieldData(fieldId) {
        try {
            const response = await fetch(`/admin/frameworks/all_data_points?field_id=${fieldId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.success && data.data_points && data.data_points.length > 0) {
                return data.data_points[0];
            }
            return null;
        } catch (error) {
            console.error(`Error fetching field data for ${fieldId}:`, error);
            return null;
        }
    }

    async addDataPointWithInheritedConfig(field, parentComputedField) {
        // Add the field to selected data points
        await this.addDataPoint(field);
        
        // Inherit configuration from parent computed field
        const parentConfig = this.configurations.get(parentComputedField.field_id);
        if (parentConfig) {
            const inheritedConfig = {
                ...parentConfig,
                // Dependencies inherit same financial year and frequency or higher
                frequency: this.getCompatibleFrequency(parentConfig.frequency, field.suggested_frequency || 'Annual'),
                isAutoAssigned: true,
                inheritedFrom: parentComputedField.field_id
            };
            
            this.configurations.set(field.field_id, inheritedConfig);
            console.log(`Inherited configuration for ${field.field_name} from ${parentComputedField.field_name}`);
        }

        // Inherit entity assignments
        const parentEntities = this.entityAssignments.get(parentComputedField.field_id);
        if (parentEntities && parentEntities.size > 0) {
            this.entityAssignments.set(field.field_id, new Set(parentEntities));
            console.log(`Inherited entity assignments for ${field.field_name}`);
        }
    }

    getCompatibleFrequency(parentFrequency, suggestedFrequency) {
        const frequencyHierarchy = {
            'Monthly': 3,
            'Quarterly': 2,
            'Annual': 1
        };

        const parentLevel = frequencyHierarchy[parentFrequency] || 1;
        const suggestedLevel = frequencyHierarchy[suggestedFrequency] || 1;

        // Use the higher frequency (higher number in hierarchy)
        return parentLevel >= suggestedLevel ? parentFrequency : suggestedFrequency;
    }

    async checkDependencyConflicts(dependency, computedField) {
        const conflicts = [];
        let hasConflicts = false;

        try {
            // Check if dependency already exists with conflicting configuration
            const parentConfig = this.configurations.get(computedField.field_id);
            if (parentConfig) {
                // Check existing configuration of dependency if already configured
                const dependencyConfig = this.configurations.get(dependency.field_id);
                if (dependencyConfig) {
                    // Check FY period conflicts
                    if (dependencyConfig.fy_start_year !== parentConfig.fy_start_year ||
                        dependencyConfig.fy_start_month !== parentConfig.fy_start_month) {
                        conflicts.push(`Different FY period: dependency has ${dependencyConfig.fy_start_month}/${dependencyConfig.fy_start_year}, required ${parentConfig.fy_start_month}/${parentConfig.fy_start_year}`);
                        hasConflicts = true;
                    }

                    // Check frequency conflicts (dependency must be same or higher frequency)
                    if (!this.isFrequencyCompatible(dependencyConfig.frequency, parentConfig.frequency)) {
                        conflicts.push(`Frequency too low: dependency has ${dependencyConfig.frequency}, required ${parentConfig.frequency} or higher`);
                        hasConflicts = true;
                    }

                    // Check entity assignment conflicts
                    const parentEntities = this.entityAssignments.get(computedField.field_id);
                    const dependencyEntities = this.entityAssignments.get(dependency.field_id);
                    
                    if (parentEntities && dependencyEntities) {
                        const parentEntitiesArray = Array.from(parentEntities);
                        const dependencyEntitiesArray = Array.from(dependencyEntities);
                        
                        // Check if dependency entities include all parent entities
                        const missingEntities = parentEntitiesArray.filter(entity => !dependencyEntities.has(entity));
                        if (missingEntities.length > 0) {
                            conflicts.push(`Missing entity assignments: dependency needs entities ${missingEntities.join(', ')}`);
                            hasConflicts = true;
                        }
                    }
                }
            }

        } catch (error) {
            console.error('Error checking dependency conflicts:', error);
            conflicts.push(`Error checking conflicts: ${error.message}`);
            hasConflicts = true;
        }

        return { hasConflicts, conflicts };
    }

    isFrequencyCompatible(dependencyFreq, requiredFreq) {
        const frequencyLevels = {
            'Monthly': 3,
            'Quarterly': 2,
            'Annual': 1
        };

        const depLevel = frequencyLevels[dependencyFreq] || 1;
        const reqLevel = frequencyLevels[requiredFreq] || 1;

        // Dependency frequency must be same or higher (higher number)
        return depLevel >= reqLevel;
    }

    showDependencyAssignmentResults(computedField, addedCount, conflicts) {
        let message = '';
        let type = 'info';

        if (addedCount > 0 && conflicts.length === 0) {
            message = `✓ Auto-added ${addedCount} dependencies for ${computedField.field_name}`;
            type = 'success';
        } else if (addedCount > 0 && conflicts.length > 0) {
            message = `⚠ Added ${addedCount} dependencies for ${computedField.field_name}, but ${conflicts.length} had conflicts`;
            type = 'warning';
        } else if (conflicts.length > 0) {
            message = `✗ Cannot auto-assign dependencies for ${computedField.field_name} due to conflicts`;
            type = 'error';
        }

        if (message) {
            this.showNotification(message, type);
            
            // Log detailed conflict information
            if (conflicts.length > 0) {
                console.group('Dependency Conflicts:');
                conflicts.forEach(conflict => {
                    console.warn(`${conflict.field.field_name}:`, conflict.conflicts);
                });
                console.groupEnd();
            }
        }
    }

    showNotification(message, type = 'info') {
        // Use PopupManager if available, otherwise fallback to browser alert
        if (window.PopupManager && PopupManager.showMessage) {
            const alertType = type === 'error' ? 'danger' : type;
            PopupManager.showMessage(message, alertType);
        } else {
            // Fallback to console and browser alert for critical errors
            console.log(`${type.toUpperCase()}: ${message}`);
            if (type === 'error') {
                alert(`Error: ${message}`);
            }
        }
    }

    expandAllTopics() {
        const allNodes = document.querySelectorAll('.topic-node');
        allNodes.forEach(node => {
            const childrenContainer = node.querySelector('.topic-children');
            if (childrenContainer && childrenContainer.children.length > 0) {
                node.classList.add('expanded');
                childrenContainer.style.display = 'block';
            }
        });
    }

    collapseAllTopics() {
        const allNodes = document.querySelectorAll('.topic-node');
        allNodes.forEach(node => {
            node.classList.remove('expanded');
            const childrenContainer = node.querySelector('.topic-children');
            if (childrenContainer) {
                childrenContainer.style.display = 'none';
            }
        });
    }

    // saveUnitOverride method removed - dead code (no HTML elements exist for this functionality)

    updateSelectedCount() {
        // Count the visible data point items in the DOM
        // This ensures the counter matches what the user can actually see
        const selectedPointsContainer = document.getElementById('selectedDataPointsList');

        if (!selectedPointsContainer) {
            console.warn('selectedDataPointsList container not found');
            return;
        }

        // First try to count .data-point-card elements
        let dataPointCards = selectedPointsContainer.querySelectorAll('.data-point-card');

        // If no data-point-card elements, try other selectors based on the actual DOM structure
        if (dataPointCards.length === 0) {
            // Try counting data point items based on the actual DOM structure we see
            dataPointCards = selectedPointsContainer.querySelectorAll('.data-point-item, .point-item, [data-field-id]');
        }

        // Filter out any hidden elements
        const visibleCards = Array.from(dataPointCards).filter(card => {
            const style = window.getComputedStyle(card);
            return style.display !== 'none' && style.visibility !== 'hidden';
        });

        const count = visibleCards.length;

        console.log(`updateSelectedCount: container found, total cards: ${dataPointCards.length}, visible cards: ${count}`);

        const countElement = document.getElementById('selectedCount');
        if (countElement) {
            countElement.textContent = count;
        }
    }

    updateSelectionState() {
        const checkedBoxes = document.querySelectorAll('.point-select:checked');
        this.currentSelectedPoints.clear();
        
        checkedBoxes.forEach(checkbox => {
            const fieldId = checkbox.closest('.selected-point-item').dataset.fieldId;
            this.currentSelectedPoints.add(fieldId);
        });
        
        this.updateToolbarButtons();
    }

    updateToolbarButtons() {
        const hasDataPoints = this.selectedDataPoints.size > 0;
        const hasSelection = this.currentSelectedPoints.size > 0;
        
        // Enable/disable buttons based on state
        const configureBtn = document.getElementById('configureSelected');
        const assignBtn = document.getElementById('assignEntities');
        const saveBtn = document.getElementById('saveAllConfiguration');
        
        if (configureBtn) configureBtn.disabled = !hasSelection;
        if (assignBtn) assignBtn.disabled = !hasSelection;
        if (saveBtn) saveBtn.disabled = !hasDataPoints;
    }

    selectAllDataPoints() {
        document.querySelectorAll('.point-select').forEach(checkbox => {
            checkbox.checked = true;
        });
        this.updateSelectionState();
    }

    deselectAllDataPoints() {
        document.querySelectorAll('.point-select').forEach(checkbox => {
            checkbox.checked = false;
        });
        this.updateSelectionState();
    }

    // Modal functionality
    openConfigurationModal() {
        if (this.currentSelectedPoints.size === 0) {
            this.showMessage('Please select data points to configure', 'warning');
            return;
        }

        // Update modal count
        const countElement = document.getElementById('configPointCount');
        if (countElement) {
            countElement.textContent = this.currentSelectedPoints.size;
        }

        // Analyze current configurations and populate modal intelligently
        this.analyzeCurrentConfigurations();

        // Initialize toggle states
        this.initializeModalToggles();

        // Show modal using Bootstrap
        const modal = new bootstrap.Modal(document.getElementById('configurationModal'));
        modal.show();
    }

    analyzeCurrentConfigurations() {
        // Analyze current configurations of selected data points
        const frequencies = new Set();
        const units = new Set();
        const topics = new Set();
        let hasAssignments = false;

        for (const fieldId of this.currentSelectedPoints) {
            const field = this.selectedDataPoints.get(fieldId);
            if (field && field.current_assignment && field.current_assignment.has_assignments) {
                hasAssignments = true;

                // Use enhanced mixed state detection from API
                if (field.current_assignment.all_frequencies) {
                    // Use all frequencies for mixed state detection
                    field.current_assignment.all_frequencies.forEach(freq => frequencies.add(freq));
                } else if (field.current_assignment.frequency) {
                    // Fallback to single frequency for backward compatibility
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
        this.originalConfigurationState = {
            frequencies: Array.from(frequencies),
            units: Array.from(units),
            topics: Array.from(topics),
            hasAssignments: hasAssignments
        };

        // Update modal to show current state
        this.populateModalWithCurrentConfig();

        // Show change summary if there are existing configurations
        const changeSummary = document.getElementById('configChangeSummary');
        if (changeSummary && hasAssignments) {
            changeSummary.style.display = 'block';
        }
    }

    populateModalWithCurrentConfig() {
        const state = this.originalConfigurationState;

        // Set frequency dropdown
        const frequencySelect = document.getElementById('modalFrequency');
        if (state.frequencies.length === 1) {
            // All have same frequency - pre-select it
            frequencySelect.value = state.frequencies[0];
        } else if (state.frequencies.length > 1) {
            // Mixed frequencies - add mixed indicator option
            if (!frequencySelect.querySelector('option[value="__MIXED__"]')) {
                const mixedOption = document.createElement('option');
                mixedOption.value = '__MIXED__';
                mixedOption.textContent = `Mixed (${state.frequencies.join(', ')})`;
                mixedOption.style.fontStyle = 'italic';
                mixedOption.style.color = '#666';
                frequencySelect.insertBefore(mixedOption, frequencySelect.firstChild);
            }
            frequencySelect.value = '__MIXED__';
        }

        // Set unit dropdown
        const unitSelect = document.getElementById('modalUnitOverrideSelect');
        if (state.units.length === 1) {
            unitSelect.value = state.units[0];
        } else if (state.units.length > 1) {
            // Mixed units - show placeholder
            if (!unitSelect.querySelector('option[value="__MIXED__"]')) {
                const mixedOption = document.createElement('option');
                mixedOption.value = '__MIXED__';
                mixedOption.textContent = `Mixed units (${state.units.join(', ')})`;
                mixedOption.style.fontStyle = 'italic';
                mixedOption.style.color = '#666';
                unitSelect.insertBefore(mixedOption, unitSelect.firstChild);
            }
            unitSelect.value = '__MIXED__';
        }

        // Set topic dropdown
        const topicSelect = document.getElementById('modalTopicSelect');
        if (state.topics.length === 1) {
            topicSelect.value = state.topics[0];
        } else if (state.topics.length > 1) {
            // Mixed topics - show placeholder
            if (!topicSelect.querySelector('option[value="__MIXED__"]')) {
                const mixedOption = document.createElement('option');
                mixedOption.value = '__MIXED__';
                mixedOption.textContent = 'Mixed topics';
                mixedOption.style.fontStyle = 'italic';
                mixedOption.style.color = '#666';
                topicSelect.insertBefore(mixedOption, topicSelect.firstChild);
            }
            topicSelect.value = '__MIXED__';
        }
    }

    initializeModalToggles() {
        // Initialize Unit Override Toggle - off by default (hidden)
        const unitOverrideToggle = document.getElementById('unitOverrideToggle');
        const unitSelectContainer = document.getElementById('modalUnitOverrideSelect').closest('.config-form-group');

        if (unitOverrideToggle && unitSelectContainer) {
            unitOverrideToggle.checked = false;
            unitSelectContainer.style.display = 'none';
            document.getElementById('modalUnitOverrideSelect').value = '';
        }

        // Initialize Material Topic Toggle - on by default as shown in the design (visible)
        const materialTopicToggle = document.getElementById('materialTopicToggle');
        const topicSelectContainer = document.getElementById('modalTopicSelect').closest('.config-form-group');

        if (materialTopicToggle && topicSelectContainer) {
            materialTopicToggle.checked = true;
            topicSelectContainer.style.display = 'block';
            topicSelectContainer.style.opacity = '1';
            topicSelectContainer.style.transform = 'translateY(0)';
        }
    }

    openEntityModal() {
        if (this.currentSelectedPoints.size === 0) {
            this.showMessage('Please select data points to assign entities', 'warning');
            return;
        }

        // Update modal count
        const countElement = document.getElementById('entityPointCount');
        if (countElement) {
            countElement.textContent = this.currentSelectedPoints.size;
        }

        // Populate entity modal
        this.populateEntityModal();

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('entityModal'));
        modal.show();
    }

    populateEntityModal() {
        const availableContainer = document.getElementById('modalAvailableEntities');
        const selectedContainer = document.getElementById('modalSelectedEntities');
        const hierarchyContainer = document.getElementById('entityHierarchyContainer');

        if (!availableContainer || !selectedContainer) return;

        // Get currently assigned entities for selected points
        const currentlyAssigned = new Set();
        this.currentSelectedPoints.forEach(fieldId => {
            const entities = this.entityAssignments.get(fieldId) || new Set();
            entities.forEach(entityId => currentlyAssigned.add(entityId));
        });

        // Render available entities list (flat list for easy selection)
        availableContainer.innerHTML = this.availableEntities
            .map(entity => this.createEntityItemHTML(entity, currentlyAssigned.has(entity.id.toString())))
            .join('');

        // Render entity hierarchy (structured view)
        if (hierarchyContainer) {
            this.populateEntityHierarchy(hierarchyContainer, currentlyAssigned);
        }

        // Render selected entities as badges
        this.updateSelectedEntityBadges(currentlyAssigned);

        // Update count
        const countElement = document.getElementById('modalSelectedEntitiesCount');
        if (countElement) {
            countElement.textContent = currentlyAssigned.size;
        }

        // Add event listeners
        this.setupModalEntityListeners();
    }

    createEntityItemHTML(entity, isSelected) {
        const iconText = entity.name.split(' ').map(word => word[0]).join('').substring(0, 2).toUpperCase();
        const selectedClass = isSelected ? 'selected' : '';

        return `
            <div class="entity-item ${selectedClass}" data-entity-id="${entity.id}">
                <div class="entity-icon">${iconText}</div>
                <div class="entity-name">${entity.name}</div>
            </div>
        `;
    }

    populateEntityHierarchy(container, currentlyAssigned) {
        // For now, show a simple hierarchical list based on entity types and parent_id
        // Build hierarchy from availableEntities
        const hierarchyHTML = this.buildEntityHierarchyHTML(this.availableEntities, currentlyAssigned);
        container.innerHTML = hierarchyHTML || '<div class="hierarchy-empty">No entities available</div>';
    }

    buildEntityHierarchyHTML(entities, currentlyAssigned) {
        if (!entities || entities.length === 0) {
            return '<div class="hierarchy-empty">No entities available</div>';
        }

        // Use the same hierarchy building logic as the data_hierarchy page
        // Group entities by parent_id to build hierarchy
        const entitiesByParent = {};
        const rootEntities = [];

        entities.forEach(entity => {
            // Convert parent_id to proper type for comparison
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

        // Build HTML for root entities and their children recursively
        let html = '';
        rootEntities.forEach(entity => {
            html += this.renderEntityHierarchyNode(entity, entitiesByParent, currentlyAssigned, 0);
        });

        return html || '<div class="hierarchy-empty">No hierarchy structure found</div>';
    }

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
    }

    updateSelectedEntityBadges(currentlyAssigned) {
        const selectedContainer = document.getElementById('modalSelectedEntities');
        if (!selectedContainer) return;

        if (currentlyAssigned.size === 0) {
            selectedContainer.innerHTML = ''; // Will show "No entities selected" via CSS
            return;
        }

        const selectedEntities = this.availableEntities.filter(entity =>
            currentlyAssigned.has(entity.id.toString())
        );

        selectedContainer.innerHTML = selectedEntities.map(entity => `
            <div class="selected-entity-badge" data-entity-id="${entity.id}">
                <span>${entity.name}</span>
                <i class="fas fa-times remove-entity" data-entity-id="${entity.id}"></i>
            </div>
        `).join('');
    }

    setupModalEntityListeners() {
        const availableContainer = document.getElementById('modalAvailableEntities');
        const selectedContainer = document.getElementById('modalSelectedEntities');
        const hierarchyContainer = document.getElementById('entityHierarchyContainer');

        // Add click listeners to move entities between containers (flat list)
        if (availableContainer) {
            availableContainer.querySelectorAll('.entity-item').forEach(item => {
                item.addEventListener('click', () => this.moveEntityToSelected(item));
            });
        }

        if (selectedContainer) {
            selectedContainer.querySelectorAll('.entity-item').forEach(item => {
                item.addEventListener('click', () => this.moveEntityToAvailable(item));
            });
        }

        // Add hierarchy toggle and selection listeners
        if (hierarchyContainer) {
            // Toggle hierarchy expand/collapse
            hierarchyContainer.querySelectorAll('.toggle-icon').forEach(toggleBtn => {
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

            // Handle entity selection in hierarchy
            hierarchyContainer.querySelectorAll('.entity-selectable').forEach(entityNode => {
                entityNode.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const entityId = entityNode.dataset.entityId;
                    const entity = this.availableEntities.find(e => e.id.toString() === entityId);

                    if (entity) {
                        this.toggleEntitySelection(entity);
                    }
                });
            });

            // Handle remove entity badges
            selectedContainer.querySelectorAll('.remove-entity').forEach(removeBtn => {
                removeBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const entityId = removeBtn.dataset.entityId;
                    const entity = this.availableEntities.find(e => e.id.toString() === entityId);

                    if (entity) {
                        this.toggleEntitySelection(entity);
                    }
                });
            });
        }
    }

    toggleEntitySelection(entity) {
        // Get current field selection
        const selectedFieldIds = Array.from(this.currentSelectedPoints);
        if (selectedFieldIds.length === 0) {
            console.warn('No field selected for entity assignment');
            return;
        }

        // Get currently assigned entities for selected fields
        const currentlyAssigned = new Set();
        selectedFieldIds.forEach(fieldId => {
            const assignedEntityIds = this.entityAssignments.get(fieldId) || new Set();
            assignedEntityIds.forEach(entityId => currentlyAssigned.add(entityId));
        });

        // Toggle entity selection
        const entityId = entity.id.toString();
        const isCurrentlySelected = currentlyAssigned.has(entityId);

        selectedFieldIds.forEach(fieldId => {
            let assignedEntities = this.entityAssignments.get(fieldId) || new Set();

            if (isCurrentlySelected) {
                assignedEntities.delete(entityId);
            } else {
                assignedEntities.add(entityId);
            }

            this.entityAssignments.set(fieldId, assignedEntities);
        });

        // Refresh the entity modal display
        this.refreshEntityModalDisplay();
    }

    refreshEntityModalDisplay() {
        // Get current field selection
        const selectedFieldIds = Array.from(this.currentSelectedPoints);
        if (selectedFieldIds.length === 0) {
            return;
        }

        // Get currently assigned entities for selected fields
        const currentlyAssigned = new Set();
        selectedFieldIds.forEach(fieldId => {
            const assignedEntityIds = this.entityAssignments.get(fieldId) || new Set();
            assignedEntityIds.forEach(entityId => currentlyAssigned.add(entityId));
        });

        // Repopulate hierarchy with updated selections
        const hierarchyContainer = document.getElementById('entityHierarchyContainer');
        if (hierarchyContainer) {
            this.populateEntityHierarchy(hierarchyContainer, currentlyAssigned);
        }

        // Update selected entity badges
        this.updateSelectedEntityBadges(currentlyAssigned);

        // Update count
        const countElement = document.getElementById('modalSelectedEntitiesCount');
        if (countElement) {
            countElement.textContent = currentlyAssigned.size;
        }

        // Re-setup event listeners
        this.setupModalEntityListeners();
    }

    moveEntityToSelected(entityItem) {
        const selectedContainer = document.getElementById('modalSelectedEntities');
        entityItem.classList.add('selected');
        selectedContainer.appendChild(entityItem);
        entityItem.removeEventListener('click', () => this.moveEntityToSelected(entityItem));
        entityItem.addEventListener('click', () => this.moveEntityToAvailable(entityItem));
        this.updateModalEntityCount();
    }

    moveEntityToAvailable(entityItem) {
        const availableContainer = document.getElementById('modalAvailableEntities');
        entityItem.classList.remove('selected');
        availableContainer.appendChild(entityItem);
        entityItem.removeEventListener('click', () => this.moveEntityToAvailable(entityItem));
        entityItem.addEventListener('click', () => this.moveEntityToSelected(entityItem));
        this.updateModalEntityCount();
    }

    updateModalEntityCount() {
        const selectedContainer = document.getElementById('modalSelectedEntities');
        const count = selectedContainer.children.length;
        const countElement = document.getElementById('modalSelectedEntitiesCount');
        if (countElement) {
            countElement.textContent = count;
        }
    }

    async applyConfiguration() {
        const config = this.getModalConfiguration();
        
        if (!this.validateConfiguration(config)) {
            return;
        }

        // Check for conflicts before applying
        const conflicts = this.checkConfigurationConflicts(config);
        if (conflicts.length > 0) {
            this.showConfigurationConflictModal(conflicts, config);
            return;
        }

        await this.executeConfigurationApplication(config);
    }

    checkConfigurationConflicts(config) {
        const conflicts = [];
        
        for (const fieldId of this.currentSelectedPoints) {
            const field = this.selectedDataPoints.get(fieldId);
            if (!field || !field.is_computed) continue;
            
            // Check dependency conflicts
            if (field.dependencies) {
                for (const dep of field.dependencies) {
                    const depFieldId = dep.field_id?.toString();
                    const depConfig = this.configurations.get(depFieldId);
                    
                    if (depConfig) {
                        // FY conflicts removed - now handled at company level

                        // Frequency conflicts
                        if (config.frequency !== depConfig.frequency) {
                            conflicts.push({
                                type: 'frequency_mismatch',
                                fieldId: fieldId,
                                fieldName: field.field_name,
                                dependencyId: depFieldId,
                                dependencyName: dep.field_name,
                                issue: `Frequency mismatch: ${config.frequency} vs ${depConfig.frequency}`,
                                severity: 'medium',
                                autoResolvable: true
                            });
                        }
                    }
                }
            }
        }
        
        return conflicts;
    }

    showConfigurationConflictModal(conflicts, config) {
        const modal = document.getElementById('conflictResolutionModal');
        if (!modal) {
            this.createConflictResolutionModal();
        }
        
        this.populateConflictModal(conflicts, config);
        
        const conflictModal = new bootstrap.Modal(document.getElementById('conflictResolutionModal'));
        conflictModal.show();
    }

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
        
        // Add event listeners
        document.getElementById('autoResolveConflicts')?.addEventListener('click', () => {
            this.autoResolveConflicts();
        });
        
        document.getElementById('forceApplyConfiguration')?.addEventListener('click', () => {
            this.forceApplyConfiguration();
        });
    }

    populateConflictModal(conflicts, config) {
        const conflictsList = document.getElementById('conflictsList');
        if (!conflictsList) return;
        
        conflictsList.innerHTML = conflicts.map(conflict => `
            <div class="conflict-item card mb-3">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div class="conflict-title">
                        <i class="fas fa-exclamation-circle text-${this.getConflictSeverityColor(conflict.severity)}"></i>
                        <strong>${conflict.fieldName}</strong> → ${conflict.dependencyName}
                    </div>
                    <span>${conflict.severity.toUpperCase()}</span>
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
        
        this.currentConflicts = conflicts;
        this.currentConflictConfig = config;
    }

    getConflictSeverityColor(severity) {
        switch (severity) {
            case 'high': return 'danger';
            case 'medium': return 'warning';
            case 'low': return 'info';
            default: return 'secondary';
        }
    }

    async autoResolveConflicts() {
        if (!this.currentConflicts || !this.currentConflictConfig) return;
        
        try {
            for (const conflict of this.currentConflicts) {
                if (conflict.autoResolvable) {
                    // Auto-resolve by updating dependency configuration
                    await this.saveConfiguration(conflict.dependencyId, this.currentConflictConfig);
                    this.configurations.set(conflict.dependencyId, this.currentConflictConfig);
                }
            }
            
            // Apply original configuration
            await this.executeConfigurationApplication(this.currentConflictConfig);
            
            // Close conflict modal
            const conflictModal = bootstrap.Modal.getInstance(document.getElementById('conflictResolutionModal'));
            conflictModal?.hide();
            
            this.showMessage('Conflicts auto-resolved and configuration applied successfully', 'success');
            
        } catch (error) {
            console.error('Error auto-resolving conflicts:', error);
            this.showMessage('Error resolving conflicts', 'error');
        }
    }

    async forceApplyConfiguration() {
        if (!this.currentConflictConfig) return;
        
        if (!confirm('Force applying this configuration may cause calculation errors. Are you sure you want to continue?')) {
            return;
        }
        
        await this.executeConfigurationApplication(this.currentConflictConfig);
        
        // Close conflict modal
        const conflictModal = bootstrap.Modal.getInstance(document.getElementById('conflictResolutionModal'));
        conflictModal?.hide();
        
        this.showMessage('Configuration force applied (conflicts remain unresolved)', 'warning');
    }

    async executeConfigurationApplication(config) {
        try {
            for (const fieldId of this.currentSelectedPoints) {
                // Get current field data to preserve existing configuration
                const field = this.selectedDataPoints.get(fieldId);
                const currentConfig = this.configurations.get(fieldId) || {};

                // Build configuration that preserves existing values for unchanged fields
                const fieldConfig = {
                    // Preserve existing values by default
                    frequency: currentConfig.frequency || (field?.current_assignment?.frequency) || 'Annual',
                    unit: currentConfig.unit || (field?.current_assignment?.unit) || null,
                    assigned_topic_id: currentConfig.assigned_topic_id || (field?.current_assignment?.assigned_topic_id) || null,
                    collection_method: currentConfig.collection_method || 'Manual Entry',
                    validation_rules: currentConfig.validation_rules || 'Required',
                    approval_required: currentConfig.approval_required || false
                };

                // Override only the fields that were explicitly changed
                if (config.changedFields?.frequency && config.frequency !== null) {
                    fieldConfig.frequency = config.frequency;
                }
                if (config.changedFields?.unit) {
                    fieldConfig.unit = config.unit;
                }
                if (config.changedFields?.assigned_topic_id) {
                    fieldConfig.assigned_topic_id = config.assigned_topic_id;
                }

                // Always apply these non-user-facing fields if present in config
                if (config.collection_method) fieldConfig.collection_method = config.collection_method;
                if (config.validation_rules) fieldConfig.validation_rules = config.validation_rules;
                if (config.approval_required !== undefined) fieldConfig.approval_required = config.approval_required;

                await this.saveConfiguration(fieldId, fieldConfig);
                this.configurations.set(fieldId, fieldConfig);

                // Apply topic assignment tracking
                if (fieldConfig.assigned_topic_id) {
                    this.topicAssignments.set(fieldId, fieldConfig.assigned_topic_id);
                } else {
                    this.topicAssignments.delete(fieldId);
                }
            }
            
            this.updateSelectedDataPointsList();

            // Check if any fields have no entity assignments
            const fieldsWithoutEntities = Array.from(this.currentSelectedPoints).filter(fieldId => {
                const entities = this.entityAssignments.get(fieldId) || new Set();
                return entities.size === 0;
            });

            if (fieldsWithoutEntities.length > 0 && config.assigned_topic_id) {
                const topicMsg = config.assigned_topic_id ? ' and topic assignment' : '';
                this.showMessage(`Configuration${topicMsg} applied to ${this.currentSelectedPoints.size} data points. Note: ${fieldsWithoutEntities.length} field(s) need entity assignments to persist topic configuration.`, 'warning');
            } else {
                const topicMsg = config.assigned_topic_id ? ' and topic assignment' : '';
                this.showMessage(`Configuration${topicMsg} applied to ${this.currentSelectedPoints.size} data points`, 'success');
            }

            // Update button statuses after configuration changes
            this.updateAllButtonStatuses();
            
            // Close configuration modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('configurationModal'));
            modal?.hide();
            
        } catch (error) {
            console.error('Error applying configuration:', error);
            this.showMessage('Error applying configuration', 'error');
        }
    }

    async applyEntityAssignment() {
        const selectedContainer = document.getElementById('modalSelectedEntities');
        const selectedEntityIds = Array.from(selectedContainer.children).map(item => item.dataset.entityId);

        try {
            for (const fieldId of this.currentSelectedPoints) {
                this.entityAssignments.set(fieldId, new Set(selectedEntityIds));

                // Save entity assignments to backend
                const config = this.configurations.get(fieldId) || this.getDefaultConfiguration();
                // Include any existing topic assignment
                const assignedTopicId = this.topicAssignments.get(fieldId);
                if (assignedTopicId) {
                    config.assigned_topic_id = assignedTopicId;
                }

                // Convert entity IDs to integers
                const entityIdsAsInts = selectedEntityIds.map(id => parseInt(id));
                await this.saveEntityAssignments(fieldId, entityIdsAsInts, config);
            }
            
            this.updateSelectedDataPointsList();
            this.showMessage(`Entities assigned to ${this.currentSelectedPoints.size} data points`, 'success');

            // Update button statuses after entity assignment changes
            this.updateAllButtonStatuses();
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('entityModal'));
            modal.hide();
            
        } catch (error) {
            console.error('Error applying entity assignment:', error);
            this.showMessage('Error assigning entities', 'error');
        }
    }

    getModalConfiguration() {
        const frequencyValue = document.getElementById('modalFrequency').value;
        const unitValue = document.getElementById('modalUnitOverrideSelect').value;
        const topicValue = document.getElementById('modalTopicSelect').value;

        const config = {
            frequency: frequencyValue && frequencyValue !== '__MIXED__' ? frequencyValue : null,
            unit: unitValue && unitValue !== '__MIXED__' ? (unitValue || null) : null,
            collection_method: document.getElementById('modalCollectionMethod').value,
            validation_rules: document.getElementById('modalValidationRules').value,
            approval_required: document.getElementById('modalApprovalRequired').value === 'Yes',
            assigned_topic_id: topicValue && topicValue !== '__MIXED__' ? (topicValue || null) : null
        };

        // Track which fields were actually changed from original values
        const state = this.originalConfigurationState || {};
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
            // Explicitly clearing unit
            config.changedFields.unit = true;
        }

        // Check topic changes
        if (topicValue && topicValue !== '__MIXED__') {
            if (state.topics.length === 0 || !state.topics.includes(topicValue)) {
                config.changedFields.assigned_topic_id = true;
            }
        } else if (topicValue === '') {
            // Explicitly clearing topic
            config.changedFields.assigned_topic_id = true;
        }

        return config;
    }

    getDefaultConfiguration() {
        return {
            fy_start_month: 4,
            fy_start_year: new Date().getFullYear(),
            fy_end_year: new Date().getFullYear() + 1,
            frequency: 'Annual',
            collection_method: 'Manual Entry',
            validation_rules: 'Required',
            approval_required: false,
            entities: [],
            assigned_topic_id: null // NEW: Default no topic assignment
        };
    }

    // === Status Detection Functions ===

    /**
     * Get configuration status for a data point
     * @param {string} fieldId - The field ID to check
     * @returns {string} 'configured' or 'not-configured'
     */
    getConfigurationStatus(fieldId) {
        // Check if material topic is assigned
        const hasTopicAssigned = this.topicAssignments.get(fieldId);
        return hasTopicAssigned ? 'configured' : 'not-configured';
    }

    /**
     * Get entity assignment status for a data point
     * @param {string} fieldId - The field ID to check
     * @returns {object} { status: 'assigned'|'not-assigned', count: number }
     */
    getEntityAssignmentStatus(fieldId) {
        const entities = this.entityAssignments.get(fieldId) || new Set();
        return {
            status: entities.size > 0 ? 'assigned' : 'not-assigned',
            count: entities.size
        };
    }

    /**
     * Update button status classes and attributes for a specific data point
     * @param {string} fieldId - The field ID to update
     */
    updateButtonStatus(fieldId) {
        const dataPointItem = document.querySelector(`[data-field-id="${fieldId}"]`);
        if (!dataPointItem) return;

        const configBtn = dataPointItem.querySelector('.configure-single');
        const entityBtn = dataPointItem.querySelector('.assign-single');

        if (configBtn) {
            // Get configuration status
            const configStatus = this.getConfigurationStatus(fieldId);

            // Remove existing status classes
            configBtn.classList.remove('status-configured', 'status-not-configured');

            // Add appropriate status class
            configBtn.classList.add(`status-${configStatus}`);

            // Update tooltip
            const tooltip = configStatus === 'configured'
                ? '✓ Material topic assigned'
                : 'Configure material topic';
            configBtn.setAttribute('title', tooltip);
        }

        if (entityBtn) {
            // Get entity assignment status
            const entityStatus = this.getEntityAssignmentStatus(fieldId);

            // Remove existing status classes
            entityBtn.classList.remove('status-assigned', 'status-not-assigned');

            // Add appropriate status class
            entityBtn.classList.add(`status-${entityStatus.status}`);

            // Handle entity count badge
            if (entityStatus.status === 'assigned') {
                entityBtn.setAttribute('data-entity-count', entityStatus.count);
            } else {
                entityBtn.removeAttribute('data-entity-count');
            }

            // Update tooltip
            const tooltip = entityStatus.status === 'assigned'
                ? `✓ ${entityStatus.count} entities assigned`
                : 'Assign entities to this data point';
            entityBtn.setAttribute('title', tooltip);
        }
    }

    /**
     * Update button status for all selected data points
     */
    updateAllButtonStatuses() {
        for (const fieldId of this.selectedDataPoints.keys()) {
            this.updateButtonStatus(fieldId);
        }
    }

    // Removed updateSelectedFieldsChips as we don't use the chips display anymore

    // Old individual configuration methods removed - now using modal popups

    // Old entity rendering methods removed - now using modal popups

    // Old bulk selection methods removed - replaced with updateSelectionState

    // Old bulk configuration methods removed - replaced with modal functionality

    validateConfiguration(config) {
        // FY validation removed - now handled at company level

        // Basic validation for assignment-level configuration
        if (!config.frequency) {
            this.showMessage('Please select a data collection frequency', 'error');
            return false;
        }

        return true;
    }

    async saveConfiguration(fieldId, config) {
        const response = await fetch('/admin/configure_fields', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                field_ids: [fieldId],
                configuration: {
                    frequency: config.frequency,
                    unit: config.unit || null,
                    assigned_topic_id: config.assigned_topic_id || null,
                    collection_method: config.collection_method || null,
                    validation_rules: config.validation_rules || null,
                    approval_required: config.approval_required || false
                }
            })
        });

        const result = await response.json();
        if (!result.success) {
            throw new Error(result.message || 'Failed to save configuration');
        }

        // Update local state after successful save
        this.configurations.set(fieldId, config);

        // Update topic assignments state to ensure button color changes
        if (config.assigned_topic_id) {
            this.topicAssignments.set(fieldId, config.assigned_topic_id);
        } else {
            this.topicAssignments.delete(fieldId);
        }

        // Update button status to reflect the change (make button green if configured)
        this.updateButtonStatus(fieldId);

        return result;
    }

    async saveEntityAssignments(fieldId, entityIds, config = {}) {
        const response = await fetch('/admin/assign_entities', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                field_ids: [fieldId],
                entity_ids: entityIds,
                configuration: {
                    frequency: config.frequency || 'Annual',
                    unit: config.unit || null,
                    assigned_topic_id: config.assigned_topic_id || null
                }
            })
        });

        const result = await response.json();
        if (!result.success) {
            throw new Error(result.message || 'Failed to save entity assignments');
        }

        return result;
    }

    async saveAllConfiguration() {
        if (this.selectedDataPoints.size === 0) {
            this.showMessage('No data points selected to save', 'warning');
            return;
        }

        const unconfiguredPoints = Array.from(this.selectedDataPoints.keys()).filter(fieldId => 
            !this.configurations.has(fieldId)
        );

        if (unconfiguredPoints.length > 0) {
            this.showMessage(`${unconfiguredPoints.length} data points are not configured yet`, 'warning');
            return;
        }

        try {
            // All points are already configured through individual saves
            this.showMessage(`Configuration saved successfully for ${this.selectedDataPoints.size} data points`, 'success');
        } catch (error) {
            console.error('Error saving all configurations:', error);
            this.showMessage('Error saving configurations', 'error');
        }
    }

    clearAllSelection() {
        this.selectedDataPoints.clear();
        this.configurations.clear();
        this.entityAssignments.clear();
        this.currentSelectedPoints.clear();
        
        this.updateSelectedDataPointsList();
        this.updateSelectedCount();
        
        // Clear framework selection
        const frameworkSelect = document.getElementById('framework_select');
        if (frameworkSelect) {
            frameworkSelect.value = '';
        }
        
        const availableFields = document.getElementById('availableFields');
        if (availableFields) {
            availableFields.innerHTML = '<div class="empty-state"><i class="fas fa-info-circle"></i><p>Select a framework to view available data points</p></div>';
        }
        
        this.showMessage('All selections cleared', 'success');
    }

    selectAllVisible() {
        const availableCards = document.querySelectorAll('#availableFields .data-point-card');
        
        if (availableCards.length === 0) {
            this.showMessage('No data points available to select', 'warning');
            return;
        }

        availableCards.forEach(card => {
            const addBtn = card.querySelector('.add-point');
            addBtn?.click();
        });
    }

    saveAsTemplate() {
        const globalConfig = this.getGlobalConfiguration();
        
        // For now, just show a success message
        // In a real implementation, you'd save to backend
        this.showMessage('Configuration template saved successfully', 'success');
    }

    updateGlobalPreview() {
        const preview = document.getElementById('globalFyPreview');
        const month = parseInt(document.getElementById('globalFyStartMonth').value);
        const startYear = parseInt(document.getElementById('globalFyStartYear').value);
        const endYear = parseInt(document.getElementById('globalFyEndYear').value);
        
        preview.textContent = this.generateFYPreview(month, startYear, endYear);
    }

    generateFYPreview(month, startYear, endYear) {
        const monthName = this.getMonthName(month);
        return `Current FY: ${monthName} ${startYear} - ${monthName} ${endYear}`;
    }

    getMonthName(monthNumber) {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return months[monthNumber - 1] || 'Jan';
    }

    handleSearch(event) {
        const searchTerm = event.target.value.toLowerCase();
        const cards = document.querySelectorAll('#availableFields .data-point-card');
        
        cards.forEach(card => {
            const pointName = card.querySelector('.point-name').textContent.toLowerCase();
            const fieldCode = card.querySelector('.field-code').textContent.toLowerCase();
            
            const matches = pointName.includes(searchTerm) || fieldCode.includes(searchTerm);
            card.style.display = matches ? 'block' : 'none';
        });
    }

    showIndividualEmptyState() {
        const emptyState = document.querySelector('#individualConfigSection .individual-info');
        const form = document.getElementById('individualConfigForm');
        
        emptyState.style.display = 'block';
        form.style.display = 'none';
    }

    updateUIComponents() {
        // Update entity counts
        this.updateSelectedCount();
        
        // Update configuration preview
        this.updateConfigurationPreview();
    }

    updateConfigurationPreview() {
        const preview = document.getElementById('configurationSummary');
        if (!preview) return;

        if (this.selectedDataPoints.size === 0) {
            preview.innerHTML = '<div class="preview-empty"><i class="fas fa-info-circle"></i><p>Configuration preview will appear here</p></div>';
            return;
        }

        const globalConfig = this.getGlobalConfiguration();
        const configuredCount = Array.from(this.selectedDataPoints.keys()).filter(fieldId => 
            this.configurations.has(fieldId)
        ).length;

        preview.innerHTML = `
            <div class="preview-summary">
                <h5>Configuration Summary</h5>
                <div class="summary-stats">
                    <div class="stat-item">
                        <label>Total Selected:</label>
                        <span>${this.selectedDataPoints.size}</span>
                    </div>
                    <div class="stat-item">
                        <label>Configured:</label>
                        <span>${configuredCount}</span>
                    </div>
                    <div class="stat-item">
                        <label>Pending:</label>
                        <span>${this.selectedDataPoints.size - configuredCount}</span>
                    </div>
                </div>
                <div class="global-config-preview">
                    <h6>Global Settings</h6>
                    <p><strong>FY:</strong> ${this.generateFYPreview(globalConfig.fy_start_month, globalConfig.fy_start_year, globalConfig.fy_end_year)}</p>
                    <p><strong>Frequency:</strong> ${globalConfig.frequency}</p>
                    <p><strong>Entities:</strong> ${this.selectedEntities.size} selected</p>
                </div>
            </div>
        `;
    }

    // Helper methods for enhanced modal functionality
    calculateDependencyDepth(field, visited = new Set()) {
        if (!field.is_computed || !field.dependencies || field.dependencies.length === 0) {
            return 0;
        }
        
        if (visited.has(field.field_id)) {
            return 0; // Avoid circular dependencies
        }
        
        visited.add(field.field_id);
        let maxDepth = 0;
        
        for (const dep of field.dependencies) {
            const depField = this.selectedDataPoints.get(dep.field_id?.toString()) || 
                            this.findFieldInAvailable(dep.field_id);
            if (depField && depField.is_computed) {
                const depDepth = this.calculateDependencyDepth(depField, new Set(visited));
                maxDepth = Math.max(maxDepth, depDepth);
            }
        }
        
        visited.delete(field.field_id);
        return maxDepth + 1;
    }
    
    findFieldInAvailable(fieldId) {
        // This would need to search in the available fields cache
        // For now, return null as this requires API call
        return null;
    }
    
    hasConfigurationConflicts(fieldId) {
        const field = this.selectedDataPoints.get(fieldId);
        if (!field || !field.is_computed) return false;
        
        const config = this.configurations.get(fieldId);
        if (!config) return false;
        
        // Check for dependency configuration mismatches
        if (field.dependencies) {
            for (const dep of field.dependencies) {
                const depFieldId = dep.field_id?.toString();
                const depConfig = this.configurations.get(depFieldId);
                
                if (depConfig) {
                    // Check for FY mismatches
                    if (config.fy_start_year !== depConfig.fy_start_year || 
                        config.fy_end_year !== depConfig.fy_end_year) {
                        return true;
                    }
                    
                    // Check for frequency mismatches
                    if (config.frequency !== depConfig.frequency) {
                        return true;
                    }
                    
                    // Check for entity assignment mismatches
                    const mainEntities = this.entityAssignments.get(fieldId) || new Set();
                    const depEntities = this.entityAssignments.get(depFieldId) || new Set();
                    
                    // Dependencies should be assigned to at least the same entities
                    for (const entity of mainEntities) {
                        if (!depEntities.has(entity)) {
                            return true;
                        }
                    }
                }
            }
        }
        
        return false;
    }
    
    getConfigurationConflicts(fieldId) {
        const conflicts = [];
        const field = this.selectedDataPoints.get(fieldId);
        if (!field || !field.is_computed) return conflicts;
        
        const config = this.configurations.get(fieldId);
        if (!config) return conflicts;
        
        // Check dependency conflicts
        if (field.dependencies) {
            for (const dep of field.dependencies) {
                const depFieldId = dep.field_id?.toString();
                const depConfig = this.configurations.get(depFieldId);
                
                if (depConfig) {
                    // FY conflicts
                    if (config.fy_start_year !== depConfig.fy_start_year || 
                        config.fy_end_year !== depConfig.fy_end_year) {
                        conflicts.push({
                            type: 'Financial Year Mismatch',
                            message: `Dependency "${dep.field_name}" has different FY (${depConfig.fy_start_year}-${depConfig.fy_end_year}) than this field (${config.fy_start_year}-${config.fy_end_year})`,
                            suggestion: 'Consider updating configurations to match for accurate calculations'
                        });
                    }
                    
                    // Frequency conflicts
                    if (config.frequency !== depConfig.frequency) {
                        conflicts.push({
                            type: 'Reporting Frequency Mismatch',
                            message: `Dependency "${dep.field_name}" has ${depConfig.frequency} frequency while this field has ${config.frequency}`,
                            suggestion: 'Ensure reporting frequencies are compatible for meaningful calculations'
                        });
                    }
                }
                
                // Entity assignment conflicts
                const mainEntities = this.entityAssignments.get(fieldId) || new Set();
                const depEntities = this.entityAssignments.get(depFieldId) || new Set();
                
                const missingEntities = [];
                for (const entity of mainEntities) {
                    if (!depEntities.has(entity)) {
                        missingEntities.push(entity);
                    }
                }
                
                if (missingEntities.length > 0) {
                    conflicts.push({
                        type: 'Entity Assignment Gap',
                        message: `Dependency "${dep.field_name}" is not assigned to all entities that this field is assigned to`,
                        suggestion: 'Auto-assign dependencies to matching entities or review entity assignments'
                    });
                }
            }
        }
        
        return conflicts;
    }

    showMessage(message, type = 'info') {
        if (window.PopupManager && typeof PopupManager.showInfo === 'function') {
            switch (type) {
                case 'success':
                    PopupManager.showSuccess('Success', message);
                    break;
                case 'error':
                    PopupManager.showError('Error', message);
                    break;
                case 'warning':
                    PopupManager.showWarning('Warning', message);
                    break;
                case 'info':
                default:
                    PopupManager.showInfo('Info', message);
            }
        } else {
            // Fallback to console log and alert for critical errors
            console.log(`${type.toUpperCase()}: ${message}`);
            if (type === 'error') {
                alert(`Error: ${message}`);
            }
        }
    }

    // ===== MATERIAL TOPIC ASSIGNMENT METHODS =====

    populateTopicDropdown() {
        const topicSelect = document.getElementById('modalTopicSelect');
        if (!topicSelect) return;

        // Clear existing options except the first one
        while (topicSelect.children.length > 2) {
            topicSelect.removeChild(topicSelect.lastChild);
        }

        // Add company topics
        if (this.companyTopics.length > 0) {
            this.companyTopics.forEach(topic => {
                const option = document.createElement('option');
                option.value = topic.topic_id;
                option.textContent = topic.display_name;
                option.title = topic.full_path;
                topicSelect.appendChild(option);
            });
        } else {
            const noTopicsOption = document.createElement('option');
            noTopicsOption.value = '';
            noTopicsOption.textContent = 'No company topics available';
            noTopicsOption.disabled = true;
            topicSelect.appendChild(noTopicsOption);
        }
    }

    setupTopicEventListeners() {
        // Topic selection change handler
        const topicSelect = document.getElementById('modalTopicSelect');
        if (topicSelect) {
            topicSelect.addEventListener('change', (e) => this.handleTopicSelection(e));
        }

        // Clear topic assignment button
        const clearTopicBtn = document.getElementById('clearTopicAssignment');
        if (clearTopicBtn) {
            clearTopicBtn.addEventListener('click', () => this.clearTopicSelection());
        }
    }

    handleTopicSelection(event) {
        const topicId = event.target.value;
        const preview = document.getElementById('selectedTopicPreview');
        
        if (topicId) {
            const topic = this.companyTopics ? this.companyTopics.find(t => t.topic_id === topicId) : null;
            if (topic) {
                this.showTopicPreview(topic);
                this.updateTopicAssignmentSummary(topic);
            }
        } else {
            this.hideTopicPreview();
            this.updateTopicAssignmentSummary(null);
        }
    }

    showTopicPreview(topic) {
        const preview = document.getElementById('selectedTopicPreview');
        const nameEl = document.getElementById('previewTopicName');
        const pathEl = document.getElementById('previewTopicPath');
        const descEl = document.getElementById('previewTopicDescription');
        const descTextEl = document.getElementById('previewTopicDescriptionText');

        if (preview && nameEl && pathEl) {
            nameEl.textContent = topic.name;
            pathEl.textContent = topic.full_path;
            
            if (topic.description && descEl && descTextEl) {
                descTextEl.textContent = topic.description;
                descEl.style.display = 'block';
            } else if (descEl) {
                descEl.style.display = 'none';
            }
            
            preview.style.display = 'block';
        }
    }

    hideTopicPreview() {
        const preview = document.getElementById('selectedTopicPreview');
        if (preview) {
            preview.style.display = 'none';
        }
    }

    clearTopicSelection() {
        const topicSelect = document.getElementById('modalTopicSelect');
        if (topicSelect) {
            topicSelect.value = '';
            this.hideTopicPreview();
            this.updateTopicAssignmentSummary(null);
        }
    }

    updateTopicAssignmentSummary(topic) {
        const summary = document.getElementById('topicAssignmentSummary');
        if (summary) {
            if (topic) {
                const selectedCount = this.currentSelectedPoints.size;
                summary.textContent = `Will assign "${topic.name}" to ${selectedCount} selected data point(s)`;
            } else {
                summary.textContent = 'Ready to assign material topics to selected data points';
            }
        }
    }

    applyTopicToSelectedPoints(topicId) {
        // Apply topic assignment to all currently selected data points
        this.currentSelectedPoints.forEach(fieldId => {
            if (topicId) {
                this.topicAssignments.set(fieldId, topicId);
            } else {
                this.topicAssignments.delete(fieldId);
            }
        });

        // Update UI to reflect topic assignments
        this.updateSelectedPointsDisplay();
        this.showMessage(`Topic assignment updated for ${this.currentSelectedPoints.size} data point(s)`, 'success');
    }

    getDataPointEffectiveTopic(dataPoint) {
        // Get assigned material topic or fall back to framework topic
        const fieldId = dataPoint.field_id;
        const assignedTopicId = this.topicAssignments.get(fieldId);
        
        if (assignedTopicId) {
            return this.companyTopics ? this.companyTopics.find(t => t.topic_id === assignedTopicId) : null;
        } else if (dataPoint.topic_name) {
            // Framework topic fallback
            return {
                topic_id: 'framework_' + dataPoint.field_id,
                name: dataPoint.topic_name,
                display_name: dataPoint.topic_name + ' (Framework)',
                full_path: dataPoint.topic_name,
                is_framework_topic: true
            };
        } else {
            return null;
        }
    }

    groupDataPointsByTopic() {
        const groups = new Map();

        this.selectedDataPoints.forEach((dataPoint, fieldId) => {
            // Skip inactive assignments if not showing them
            if (!this.showingInactiveAssignments && this.isInactiveAssignment(dataPoint)) {
                return;
            }

            const effectiveTopic = this.getDataPointEffectiveTopic(dataPoint);
            const groupKey = effectiveTopic ? effectiveTopic.topic_id : 'unassigned';
            const groupName = effectiveTopic ? effectiveTopic.name : 'Unassigned';

            if (!groups.has(groupKey)) {
                groups.set(groupKey, {
                    topic: effectiveTopic,
                    name: groupName,
                    dataPoints: []
                });
            }

            groups.get(groupKey).dataPoints.push(dataPoint);
        });

        return groups;
    }

    createTopicGroupsHTML(topicGroups) {
        // Sort topics alphabetically - "Unassigned" first, then alphabetically by name
        const sortedGroups = Array.from(topicGroups.entries()).sort(([keyA, groupA], [keyB, groupB]) => {
            // Always put "Unassigned" first
            if (keyA === 'unassigned') return -1;
            if (keyB === 'unassigned') return 1;

            // Sort other topics alphabetically by name
            const nameA = groupA.name.toLowerCase();
            const nameB = groupB.name.toLowerCase();
            return nameA.localeCompare(nameB);
        });

        const groupsHTML = sortedGroups.map(([groupKey, group]) => {
            const topic = group.topic;
            const dataPoints = group.dataPoints;
            const count = dataPoints.length;
            
            // Determine group class and icon
            let groupClass = 'topic-group';
            if (!topic || groupKey === 'unassigned') {
                groupClass += ' unassigned';
            } else if (topic.is_framework_topic) {
                groupClass += ' framework-topic';
            } else {
                // Try to categorize by topic name for styling
                const lowerName = topic.name.toLowerCase();
                if (lowerName.includes('environment') || lowerName.includes('energy') || lowerName.includes('water')) {
                    groupClass += ' environmental';
                } else if (lowerName.includes('social') || lowerName.includes('employee') || lowerName.includes('community')) {
                    groupClass += ' social';
                } else if (lowerName.includes('governance') || lowerName.includes('board') || lowerName.includes('ethics')) {
                    groupClass += ' governance';
                }
            }
            
            const topicDisplayName = topic ? topic.display_name || topic.name : 'Unassigned';
            const topicPath = topic ? topic.full_path : '';
            
            return `
                <div class="${groupClass}">
                    <div class="topic-group-header">
                        <div class="topic-group-name" title="${topicPath}">
                            ${topicDisplayName}
                        </div>
                        <div class="topic-group-count">${count}</div>
                    </div>
                    <div class="topic-group-items">
                        ${dataPoints.sort((a, b) => a.field_name.localeCompare(b.field_name)).map(point => {
                            const isInactive = this.isInactiveAssignment(point);
                            const itemClass = `topic-group-item selected-point-item${isInactive ? ' inactive' : ''}`;
                            return `
                            <div class="${itemClass}" data-field-id="${point.field_id}">
                                <div class="point-checkbox">
                                    <input type="checkbox" class="form-check-input point-select" id="selected_${point.field_id}">
                                </div>
                                <div class="point-content">
                                    ${this.createSelectedPointContent(point)}
                                    ${isInactive ? '<span class="inactive-badge"><i class="fas fa-pause-circle"></i> Inactive</span>' : ''}
                                </div>
                                <div class="point-actions">
                                    <button type="button" class="btn btn-sm btn-outline-primary configure-single" title="Configure">
                                        <i class="fas fa-cog"></i>
                                    </button>
                                    <button type="button" class="btn btn-sm btn-outline-success assign-single" title="Assign Entities">
                                        <i class="fas fa-building"></i>
                                    </button>
                                    <button type="button" class="btn btn-sm btn-outline-info field-info-single" title="Field Info">
                                        <i class="fas fa-info"></i>
                                    </button>
                                    <button type="button" class="btn btn-sm btn-outline-danger remove-point" title="Remove">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>`;
                        }).join('')}
                    </div>
                </div>
            `;
        }).join('');
        
        return `<div class="selected-points-grouped">${groupsHTML}</div>`;
    }

    createSelectedPointContent(point) {
        // Extract the main content from the existing createSelectedPointHTML method
        const config = this.configurations.get(point.field_id);
        const entities = this.entityAssignments.get(point.field_id);
        const assignedTopic = this.topicAssignments.get(point.field_id);
        
        // Badges removed per user request

        return `
            <div class="point-header">
                <h6 class="point-title">${point.field_name}</h6>
                <div class="point-badges">
                </div>
            </div>
            <div class="point-details">
                <div class="detail-item">
                    <strong>Field Code:</strong> ${point.field_code || 'N/A'}
                </div>
                <div class="detail-item">
                    <strong>Configuration:</strong> 
                    ${config ? 
                        `<span class="text-success">${config.frequency} - FY ${config.fy_start_year}/${config.fy_end_year}</span>` : 
                        '<span class="text-warning">Not configured</span>'
                    }
                </div>
                <div class="detail-item">
                    <strong>Entities:</strong> 
                    ${entities && entities.size > 0 ? 
                        `<span class="text-success">${entities.size} assigned</span>` : 
                        '<span class="text-warning">No entities assigned</span>'
                    }
                </div>
            </div>
        `;
    }

    // Helper function to ensure field metadata is available for export
    async ensureFieldMetadata() {
        // If we already have field metadata, no need to fetch
        if (this.availableFields && this.availableFields.length > 0) {
            return;
        }

        try {
            console.log('Fetching field metadata for export...');
            const response = await fetch('/admin/frameworks/all_data_points');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const responseData = await response.json();

            // Handle the API response structure
            if (responseData.success && responseData.data_points) {
                // Store the field metadata for use in export
                this.availableFields = responseData.data_points;
                console.log(`Loaded ${responseData.data_points.length} field metadata entries for export`);
            } else {
                console.warn('API response did not contain expected data structure:', responseData);
                this.availableFields = [];
            }
        } catch (error) {
            console.warn('Could not fetch field metadata for export:', error);
            // Export will continue with whatever field data is available
            this.availableFields = [];
        }
    }

    // Import/Export functionality
    async exportAssignments() {
        try {
            console.log('Exporting assignments...');
            
            // Check if we have assignments to export
            if (this.selectedDataPoints.size === 0) {
                PopupManager.showInfo('Export Assignments', 'No assignments to export. Please configure some data points first.');
                return;
            }

            // Ensure we have field metadata for all configurations
            await this.ensureFieldMetadata();

            // Prepare export data
            const exportData = [];
            const headers = [
                'Field ID',
                'Field Name',
                'Frequency',
                'Unit',
                'Assigned Entities',
                'Topic'
            ];
            
            // Add headers
            exportData.push(headers);
            
            // Add data rows - fetch field data if not available
            for (const [fieldId, config] of this.configurations) {
                let field = this.availableFields ? this.availableFields.find(f => f.field_id === fieldId) : null;

                // If field data is not available, try to fetch it from selected data points
                if (!field && this.selectedDataPoints.has(fieldId)) {
                    field = this.selectedDataPoints.get(fieldId);
                }

                const entities = this.entityAssignments.get(fieldId) || new Set();
                const entityNames = Array.from(entities).map(id => {
                    const entity = this.availableEntities ? this.availableEntities.find(e => e.id == id) : null;
                    return entity ? entity.name : `Entity ${id}`;
                }).join('; ');

                exportData.push([
                    fieldId,
                    field?.field_name || 'Unknown Field',
                    config.frequency || 'Annual',
                    config.unit || field?.default_unit || field?.unit || 'N/A',
                    entityNames || 'None',
                    config.assigned_topic_id || field?.topic_path || 'No Topic'
                ]);
            }
            
            // Convert to CSV
            const csvContent = exportData.map(row => 
                row.map(cell => {
                    // Escape quotes and wrap in quotes if contains comma, quote, or newline
                    const cellStr = String(cell || '');
                    if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
                        return '"' + cellStr.replace(/"/g, '""') + '"';
                    }
                    return cellStr;
                }).join(',')
            ).join('\n');
            
            // Create and download file
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `esg_assignments_${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            PopupManager.showSuccess('Export Complete', `Successfully exported ${exportData.length - 1} assignments to CSV file.`);
            console.log('Export completed successfully');
            
        } catch (error) {
            console.error('Error exporting assignments:', error);
            PopupManager.showError('Export Failed', 'Failed to export assignments. Please try again.');
        }
    }
    
    async importAssignments() {
        // Use the separate import module
        if (!this.importer) {
            this.importer = new AssignmentImporter(this);
        }
        return this.importer.importAssignments();
    }    
    // Note: Import-related methods have been moved to assign_data_points_import.js module

    async toggleInactiveAssignments(e) {
        e.preventDefault();

        const button = e.target.closest('button');
        const icon = button.querySelector('.fas');

        try {
            // Toggle the state
            this.showingInactiveAssignments = !this.showingInactiveAssignments;

            // Update button appearance
            if (this.showingInactiveAssignments) {
                button.classList.add('showing-inactive');
                icon.className = 'fas fa-eye';
                button.innerHTML = '<i class="fas fa-eye" aria-hidden="true"></i> Hide Inactive';
                button.title = 'Hide previously deleted assignments';
            } else {
                button.classList.remove('showing-inactive');
                icon.className = 'fas fa-eye-slash';
                button.innerHTML = '<i class="fas fa-eye-slash" aria-hidden="true"></i> Show Inactive';
                button.title = 'Show previously deleted assignments';
            }

            // Reload data with new filter
            await this.loadExistingDataPoints();
            this.updateSelectedDataPointsList();
            this.updateSelectedCount();

            this.showMessage(
                this.showingInactiveAssignments ?
                'Showing active and inactive assignments' :
                'Showing only active assignments',
                'info'
            );

        } catch (error) {
            console.error('Error toggling inactive assignments:', error);
            this.showMessage('Error toggling inactive assignments: ' + error.message, 'error');
        }
    }

    // Helper method to determine if an assignment should be shown as inactive
    isInactiveAssignment(dataPoint) {
        // MODULAR REFACTOR: This utility logic moved to AppUtils.isInactiveDataPoint() in main.js lines 104-106
        return dataPoint.is_active === false || dataPoint.series_status === 'legacy';
    }

    // Method to reactivate an assignment when configuration is updated
    async reactivateAssignment(fieldId) {
        try {
            // Find assignments for this field and reactivate them
            const response = await fetch(`/admin/api/assignments/by-field/${fieldId}`);

            if (response.ok) {
                const assignments = await response.json();
                const inactiveAssignments = assignments.filter(a => !a.is_active);

                // Reactivate each inactive assignment
                for (const assignment of inactiveAssignments) {
                    const reactivateResponse = await fetch(`/admin/api/assignments/${assignment.id}/reactivate`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            reason: 'Assignment reactivated through configuration update'
                        })
                    });

                    if (!reactivateResponse.ok) {
                        console.warn(`Failed to reactivate assignment ${assignment.id}`);
                    }
                }

                // Refresh the data
                await this.loadExistingDataPoints();
                this.updateSelectedDataPointsList();
                this.updateSelectedCount();

                if (inactiveAssignments.length > 0) {
                    this.showMessage(`Reactivated ${inactiveAssignments.length} assignment(s)`, 'success');
                }
            }

        } catch (error) {
            console.error('Error reactivating assignment:', error);
            this.showMessage('Error reactivating assignment: ' + error.message, 'error');
        }
    }

    async showFieldInfo(fieldId) {
        try {
            console.log('Opening field info modal for field:', fieldId);

            // Get field data from our existing data points or fetch it
            let fieldData = null;

            // First try to get from existing loaded data points
            if (this.selectedDataPoints.has(fieldId)) {
                fieldData = this.selectedDataPoints.get(fieldId);
            } else {
                // Fetch field data from API
                fieldData = await this.fetchFieldData(fieldId);
                if (!fieldData) {
                    this.showMessage('Field data not found', 'error');
                    return;
                }
            }

            // Get the modal
            const modal = document.getElementById('fieldInfoModal');
            if (!modal) {
                this.showMessage('Field Information modal not found', 'error');
                return;
            }

            // Populate field details
            this.populateFieldDetails(fieldData);

            // Set up assignment history
            this.setupAssignmentHistoryTab(fieldId, fieldData.field_name);

            // Load assignment history immediately to populate frequency in Field Details
            await this.loadAssignmentHistory(fieldId);

            // Show the modal
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();

            // Force Field Details tab to be active every time modal opens using Bootstrap's Tab API
            const fieldDetailsTab = document.getElementById('field-details-tab');
            if (fieldDetailsTab) {
                // Use Bootstrap's Tab class to properly activate the Field Details tab
                const tab = new bootstrap.Tab(fieldDetailsTab);
                tab.show();
            }

            // Set up event listeners for the modal
            this.setupFieldInfoModalListeners(fieldId);

        } catch (error) {
            console.error('Error showing field info:', error);
            this.showMessage('Error opening field information: ' + error.message, 'error');
        }
    }

    populateFieldDetails(fieldData) {
        // Populate field information in the Field Details tab
        document.getElementById('fieldInfoName').textContent = fieldData.field_name || '-';

        // Fix data type mapping - API returns 'value_type', not 'data_type'
        document.getElementById('fieldInfoType').textContent = fieldData.value_type || fieldData.data_type || '-';

        document.getElementById('fieldInfoTopic').textContent = fieldData.topic_name || '-';
        document.getElementById('fieldInfoFramework').textContent = fieldData.framework_name || '-';

        // Set unit category if elements exist
        const unitCategoryElement = document.getElementById('fieldInfoUnitCategory');
        if (unitCategoryElement) {
            unitCategoryElement.textContent = fieldData.unit_category || '-';
        }

        // Fix default unit mapping - API returns 'default_unit'
        const defaultUnitElement = document.getElementById('fieldInfoDefaultUnit');
        if (defaultUnitElement) {
            defaultUnitElement.textContent = fieldData.default_unit || fieldData.unit || '-';
        }

        // Set description if elements exist and show the section if description is available
        const descriptionElement = document.getElementById('fieldInfoDescription');
        const descriptionTextElement = document.getElementById('fieldInfoDescriptionText');
        if (descriptionElement && descriptionTextElement) {
            if (fieldData.description && fieldData.description.trim() !== '') {
                descriptionTextElement.textContent = fieldData.description;
                descriptionElement.style.display = 'block';
            } else {
                descriptionElement.style.display = 'none';
            }
        }

        // Set field code if elements exist
        const fieldCodeElement = document.getElementById('fieldInfoCode');
        if (fieldCodeElement) {
            fieldCodeElement.textContent = fieldData.field_code || '-';
        }

        // Add additional field information that's available from API
        this.populateAdditionalFieldInfo(fieldData);
    }

    populateAdditionalFieldInfo(fieldData) {
        // Handle computed field indicator
        const computedIndicatorElement = document.getElementById('fieldInfoComputedIndicator');
        if (computedIndicatorElement) {
            if (fieldData.is_computed) {
                computedIndicatorElement.style.display = 'block';
                computedIndicatorElement.innerHTML = '<i class="fas fa-calculator"></i> This is a computed field';
            } else {
                computedIndicatorElement.style.display = 'none';
            }
        }

        // Frequency will be populated from assignment history data
        // Field metadata frequency is not reliable for current assignments
        const frequencyElement = document.getElementById('fieldInfoFrequency');
        if (frequencyElement) {
            frequencyElement.textContent = '-'; // Will be updated when assignment history loads
        }

        // Add series status if available
        const statusElement = document.getElementById('fieldInfoStatus');
        if (statusElement && fieldData.series_status) {
            statusElement.textContent = fieldData.series_status;
            statusElement.className = `status-badge status-${fieldData.series_status.toLowerCase()}`;
        }

        // Add field ID for debugging/reference
        const fieldIdElement = document.getElementById('fieldInfoFieldId');
        if (fieldIdElement && fieldData.field_id) {
            fieldIdElement.textContent = fieldData.field_id;
        }
    }

    setupAssignmentHistoryTab(fieldId, fieldName) {
        // Set field name in history header
        const historyFieldNameElement = document.getElementById('historyFieldName');
        if (historyFieldNameElement) {
            historyFieldNameElement.textContent = fieldName || 'Unknown Field';
        }

        // Initially show loading state
        this.showHistoryLoading();

        // Load assignment history when tab is clicked
        const historyTab = document.getElementById('assignment-history-tab');
        if (historyTab) {
            // Remove any existing listeners to avoid duplicates
            historyTab.removeEventListener('click', this._handleHistoryTabClick);

            // Create a bound function reference we can remove later
            this._handleHistoryTabClick = () => {
                console.log('Assignment history tab clicked, loading data for field:', fieldId);
                this.loadAssignmentHistory(fieldId);
            };

            // Add click listener
            historyTab.addEventListener('click', this._handleHistoryTabClick);

            // Also listen for Bootstrap tab shown event as backup
            historyTab.addEventListener('shown.bs.tab', this._handleHistoryTabClick);
        }
    }

    setupFieldInfoModalListeners(fieldId) {
        // Set up refresh history button
        const refreshBtn = document.getElementById('refreshHistory');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadAssignmentHistory(fieldId);
            });
        }
    }

    async loadAssignmentHistory(fieldId) {
        try {
            console.log('Loading assignment history for field:', fieldId);
            this.showHistoryLoading();

            // Fetch assignment history from API
            const response = await fetch(`/admin/assignment-history/api/timeline?field_id=${fieldId}&per_page=50`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            console.log('Assignment history loaded:', data);

            // Display the history
            this.displayAssignmentHistory(data);

        } catch (error) {
            console.error('Error loading assignment history:', error);
            this.showHistoryError('Failed to load assignment history: ' + error.message);
        }
    }

    showHistoryLoading() {
        const loadingElement = document.getElementById('historyLoading');
        const contentElement = document.getElementById('historyContent');
        const emptyElement = document.getElementById('historyEmpty');

        if (loadingElement) loadingElement.style.display = 'block';
        if (contentElement) contentElement.style.display = 'none';
        if (emptyElement) emptyElement.style.display = 'none';
    }

    showHistoryError(message) {
        const loadingElement = document.getElementById('historyLoading');
        const contentElement = document.getElementById('historyContent');
        const emptyElement = document.getElementById('historyEmpty');

        if (loadingElement) loadingElement.style.display = 'none';
        if (contentElement) contentElement.style.display = 'none';
        if (emptyElement) {
            emptyElement.style.display = 'block';
            emptyElement.innerHTML = `
                <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                <p class="text-danger">${message}</p>
                <button class="btn btn-outline-primary btn-sm" onclick="window.dataPointsManager.loadAssignmentHistory('${fieldId}')">
                    <i class="fas fa-refresh"></i> Retry
                </button>
            `;
        }
    }

    displayAssignmentHistory(data) {
        const loadingElement = document.getElementById('historyLoading');
        const contentElement = document.getElementById('historyContent');
        const emptyElement = document.getElementById('historyEmpty');
        const timelineElement = document.getElementById('historyTimeline');

        // Hide loading
        if (loadingElement) loadingElement.style.display = 'none';

        // Check if we have any timeline data
        if (!data.timeline || data.timeline.length === 0) {
            if (contentElement) contentElement.style.display = 'none';
            if (emptyElement) emptyElement.style.display = 'block';
            return;
        }

        // Show content
        if (contentElement) contentElement.style.display = 'block';
        if (emptyElement) emptyElement.style.display = 'none';

        // Update summary statistics
        this.updateHistorySummary(data.timeline);

        // Update frequency in Field Details tab from current active assignment
        this.updateFieldDetailsFromAssignmentHistory(data.timeline);

        // Populate timeline
        if (timelineElement) {
            timelineElement.innerHTML = this.generateTimelineHTML(data.timeline);
        }
    }

    updateHistorySummary(timeline) {
        // Calculate statistics
        const totalCount = timeline.length;
        const activeCount = timeline.filter(item => item.is_active).length;
        const supersededCount = timeline.filter(item => !item.is_active || item.series_status === 'superseded').length;
        const entitiesCount = new Set(timeline.map(item => item.entity_name)).size;

        // Update summary cards
        const totalElement = document.getElementById('historyTotalCount');
        const activeElement = document.getElementById('historyActiveCount');
        const supersededElement = document.getElementById('historySupersededCount');
        const entitiesElement = document.getElementById('historyEntitiesCount');

        if (totalElement) totalElement.textContent = totalCount;
        if (activeElement) activeElement.textContent = activeCount;
        if (supersededElement) supersededElement.textContent = supersededCount;
        if (entitiesElement) entitiesElement.textContent = entitiesCount;
    }

    updateFieldDetailsFromAssignmentHistory(timeline) {
        console.log('updateFieldDetailsFromAssignmentHistory called with timeline:', timeline);

        // Find the current active assignment to get the current frequency and topic
        // First try: both is_active=true AND series_status='active'
        let activeAssignment = timeline.find(item => item.is_active && item.series_status === 'active');

        // Fallback: if series_status is undefined/null, just use is_active=true
        if (!activeAssignment) {
            activeAssignment = timeline.find(item => item.is_active);
        }

        console.log('Active assignment found:', activeAssignment);

        if (activeAssignment) {
            // Enhanced debugging: log all properties of active assignment
            console.log('=== ENHANCED DEBUGGING: Active Assignment Properties ===');
            console.log('All keys in activeAssignment:', Object.keys(activeAssignment));

            // Check all topic-related properties
            const topicProps = {};
            for (const key in activeAssignment) {
                if (key.toLowerCase().includes('topic') || key.toLowerCase().includes('material')) {
                    topicProps[key] = activeAssignment[key];
                }
            }
            console.log('Topic-related properties found:', topicProps);

            // Update frequency in Field Details tab
            const frequencyElement = document.getElementById('fieldInfoFrequency');
            console.log('Frequency element found:', frequencyElement);
            if (frequencyElement) {
                const frequency = activeAssignment.frequency || '-';
                console.log('Setting frequency to:', frequency);
                frequencyElement.textContent = frequency;
            }

            // Update topic in Field Details tab
            const topicElement = document.getElementById('fieldInfoTopic');
            console.log('Topic element found:', topicElement);
            if (topicElement) {
                // Enhanced topic logic: try multiple possible property names
                console.log('=== TOPIC RESOLUTION DEBUG ===');
                console.log('effective_topic_name:', activeAssignment.effective_topic_name);
                console.log('assigned_topic_name:', activeAssignment.assigned_topic_name);
                console.log('topic_name:', activeAssignment.topic_name);
                console.log('field_topic_name:', activeAssignment.field_topic_name);
                console.log('material_topic_name:', activeAssignment.material_topic_name);

                const topicName = activeAssignment.effective_topic_name ||
                                 activeAssignment.assigned_topic_name ||
                                 activeAssignment.field_topic_name ||
                                 activeAssignment.topic_name ||
                                 activeAssignment.material_topic_name ||
                                 '-';
                console.log('Final resolved topic name:', topicName);
                topicElement.textContent = topicName;
            }

            // Update status in Field Details tab
            const statusElement = document.getElementById('fieldInfoStatus');
            console.log('Status element found:', statusElement);
            if (statusElement) {
                const status = activeAssignment.series_status || 'active';
                console.log('Setting status to:', status);
                statusElement.textContent = status;
                // Add appropriate CSS class for status styling
                statusElement.className = 'field-info-value field-status';
                statusElement.setAttribute('data-status', status);
            }
        } else {
            console.log('No active assignment found in timeline');
        }
    }

    generateTimelineHTML(timeline) {
        if (!timeline || timeline.length === 0) {
            return '<p class="text-muted text-center">No assignment history available.</p>';
        }

        return timeline.map(item => {
            const statusIcon = item.is_active ? 'fas fa-check-circle' : 'fas fa-pause-circle';

            return `
                <div class="timeline-item">
                    <div class="timeline-marker ${item.is_active ? 'active' : 'inactive'}">
                        <i class="${statusIcon}"></i>
                    </div>
                    <div class="timeline-content">
                        <div class="timeline-header">
                            <h6 class="mb-1">${item.entity_name}</h6>
                            <small class="text-muted">${this.formatDate(item.assigned_date)} by ${item.assigned_by}</small>
                        </div>
                        <div class="timeline-body">
                            <div class="assignment-details">
                                <span class="badge badge-outline-primary">${item.frequency}</span>
                                ${item.unit ? `<span class="badge badge-outline-secondary">${item.unit}</span>` : ''}
                                <span class="badge ${item.is_active ? 'badge-success' : 'badge-secondary'}">
                                    v${item.version} ${item.status_display}
                                </span>
                            </div>
                            ${item.changes_summary ? `<p class="mb-1 text-muted small">${item.changes_summary}</p>` : ''}
                            ${item.data_entry_count > 0 ? `<small class="text-info">${item.data_entry_count} data entries</small>` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    formatDate(dateString) {
        if (!dateString) return 'Unknown date';

        try {
            const date = new Date(dateString);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        } catch (error) {
            return dateString;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, starting DataPointsManager...');
    
    // Check if essential elements exist
    const essentialElements = [
        'framework_select',
        'availableFields', 
        'selectedDataPointsList',
        'configureSelected',
        'assignEntities',
        'saveAllConfiguration'
    ];
    
    const missingElements = essentialElements.filter(id => !document.getElementById(id));
    
    if (missingElements.length > 0) {
        console.error('Missing essential elements:', missingElements);
        alert(`Interface error: Missing elements - ${missingElements.join(', ')}. Please check the HTML template.`);
        return;
    }
    
    // Add enhanced interaction features for the redesigned interface
    // MODULAR REFACTOR: This entire function moved to main.js lines 149-230
    function enhanceInteractiveFeatures() {
        // Enhanced topic hierarchy collapsible functionality
        document.addEventListener('click', function(e) {
            const topicToggle = e.target.closest('.topic-toggle');
            if (topicToggle) {
                e.preventDefault();
                e.stopPropagation();

                const topicNode = topicToggle.closest('.topic-node');
                const topicChildren = topicNode?.querySelector('.topic-children');
                const toggleIcon = topicToggle.querySelector('.toggle-icon');

                if (topicChildren && toggleIcon) {
                    const isExpanded = topicChildren.classList.contains('expanded');

                    if (isExpanded) {
                        topicChildren.classList.remove('expanded');
                        toggleIcon.classList.remove('expanded');
                        topicChildren.style.display = 'none';
                    } else {
                        topicChildren.classList.add('expanded');
                        toggleIcon.classList.add('expanded');
                        topicChildren.style.display = 'block';
                        // Add slide down animation
                        topicChildren.classList.add('slide-down');
                        setTimeout(() => topicChildren.classList.remove('slide-down'), 300);
                    }
                }
            }
        });

        // Enhanced hover effects for data point items
        document.addEventListener('mouseenter', function(e) {
            // Defensive check: ensure e.target is an Element before calling closest()
            if (e.target && e.target instanceof Element) {
                const targetElement = e.target.closest('.selected-point-item, .topic-data-point, .data-point-card');
                if (targetElement) {
                    targetElement.classList.add('fade-in');
                }
            }
        }, true);

        // Enhanced button hover animations
        document.addEventListener('mouseenter', function(e) {
            // Defensive check: ensure e.target is an Element before calling matches()
            if (e.target && e.target instanceof Element && e.target.matches('.btn, .action-btn')) {
                e.target.style.transform = 'translateY(-1px)';
            }
        }, true);

        document.addEventListener('mouseleave', function(e) {
            // Defensive check: ensure e.target is an Element before calling matches()
            if (e.target && e.target instanceof Element && e.target.matches('.btn, .action-btn')) {
                if (!e.target.disabled) {
                    e.target.style.transform = 'translateY(0)';
                }
            }
        }, true);

        // Expand All / Collapse All functionality
        const expandAllBtn = document.getElementById('expandAllTopics');
        const collapseAllBtn = document.getElementById('collapseAllTopics');

        if (expandAllBtn) {
            expandAllBtn.addEventListener('click', function() {
                document.querySelectorAll('.topic-children').forEach(children => {
                    children.classList.add('expanded');
                    children.style.display = 'block';
                });
                document.querySelectorAll('.topic-toggle .toggle-icon').forEach(icon => {
                    icon.classList.add('expanded');
                });
            });
        }

        if (collapseAllBtn) {
            collapseAllBtn.addEventListener('click', function() {
                document.querySelectorAll('.topic-children').forEach(children => {
                    children.classList.remove('expanded');
                    children.style.display = 'none';
                });
                document.querySelectorAll('.topic-toggle .toggle-icon').forEach(icon => {
                    icon.classList.remove('expanded');
                });
            });
        }

        // Enhanced search input focus animation
        const searchInput = document.getElementById('dataPointSearch');
        if (searchInput) {
            searchInput.addEventListener('focus', function() {
                this.parentElement.style.transform = 'scale(1.02)';
            });

            searchInput.addEventListener('blur', function() {
                this.parentElement.style.transform = 'scale(1)';
            });
        }

        // Add icons to topic headers based on topic type
        document.querySelectorAll('.topic-header').forEach(header => {
            const topicName = header.querySelector('.topic-name')?.textContent?.toLowerCase();
            if (topicName) {
                if (topicName.includes('energy')) {
                    header.setAttribute('data-topic', 'energy');
                } else if (topicName.includes('water')) {
                    header.setAttribute('data-topic', 'water');
                } else if (topicName.includes('waste')) {
                    header.setAttribute('data-topic', 'waste');
                } else if (topicName.includes('social')) {
                    header.setAttribute('data-topic', 'social');
                } else if (topicName.includes('emission')) {
                    header.setAttribute('data-topic', 'emissions');
                }
            }
        });
    }

    // Initialize enhanced features and then main application
    enhanceInteractiveFeatures();

    try {
        window.dataPointsManager = new DataPointsManager();
    } catch (error) {
        console.error('Failed to initialize DataPointsManager:', error);
        alert(`Failed to initialize interface: ${error.message}`);
    }
});
