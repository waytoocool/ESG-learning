/**
 * SelectedDataPointsPanel Module for Assign Data Points - Right Panel Functionality
 * Phase 5: Right panel functionality extracted from legacy code
 *
 * Handles selected data points display, organization, status indicators, and management
 */

window.SelectedDataPointsPanel = {
    // State tracking
    selectedItems: new Map(),
    groupingMethod: 'topic', // 'topic', 'framework', 'none'
    isVisible: false,
    showInactive: false,
    isInitialized: false,

    // DOM element references
    elements: {
        panelContainer: null,
        selectedDataPointsList: null,
        selectedPointsList: null,
        countDisplay: null,
        selectAllButton: null,
        deselectAllButton: null,
        toggleInactiveButton: null,
        emptyState: null
    },

    // Cached data for performance
    topicGroups: new Map(),
    configurationStatus: new Map(),
    entityAssignments: new Map(),

    // Initialization
    init() {
        console.log('[SelectedDataPointsPanel] Initializing SelectedDataPointsPanel module...');
        this.cacheElements();
        this.bindEvents();
        this.setupEventListeners();
        this.updateDisplay();
        this.isInitialized = true;
        AppEvents.emit('selected-data-points-panel-initialized');
        console.log('[SelectedDataPointsPanel] SelectedDataPointsPanel module initialized successfully');
    },

    // Element caching for performance
    cacheElements() {
        console.log('[SelectedDataPointsPanel] Caching DOM elements...');

        // Main panel containers
        this.elements.panelContainer = document.querySelector('.selected-panel');
        this.elements.selectedDataPointsList = document.getElementById('selectedDataPointsList');
        this.elements.selectedPointsList = document.getElementById('selectedPointsList');

        // Control buttons
        this.elements.selectAllButton = document.getElementById('selectAllDataPoints');
        this.elements.deselectAllButton = document.getElementById('deselectAllDataPoints');
        this.elements.toggleInactiveButton = document.getElementById('toggleInactiveAssignments');

        // Count display
        this.elements.countDisplay = document.querySelector('.selected-count-display');

        // Empty state
        this.elements.emptyState = document.querySelector('.selected-panel-empty-state');

        // Validate critical elements
        const missingElements = [];
        if (!this.elements.panelContainer) missingElements.push('.selected-panel');
        if (!this.elements.selectedDataPointsList) missingElements.push('#selectedDataPointsList');
        if (!this.elements.selectAllButton) missingElements.push('#selectAllDataPoints');
        if (!this.elements.deselectAllButton) missingElements.push('#deselectAllDataPoints');
        if (!this.elements.toggleInactiveButton) missingElements.push('#toggleInactiveAssignments');

        if (missingElements.length > 0) {
            console.warn('[SelectedDataPointsPanel] Missing critical DOM elements:', missingElements);
        }

        console.log('[SelectedDataPointsPanel] DOM elements cached:', {
            panelContainer: !!this.elements.panelContainer,
            selectedDataPointsList: !!this.elements.selectedDataPointsList,
            selectedPointsList: !!this.elements.selectedPointsList,
            selectAllButton: !!this.elements.selectAllButton,
            deselectAllButton: !!this.elements.deselectAllButton,
            toggleInactiveButton: !!this.elements.toggleInactiveButton
        });
    },

    // Event binding
    bindEvents() {
        console.log('[SelectedDataPointsPanel] Binding events...');

        // Select All button
        if (this.elements.selectAllButton) {
            this.elements.selectAllButton.addEventListener('click', () => {
                this.handleSelectAll();
            });
        }

        // Deselect All button
        if (this.elements.deselectAllButton) {
            this.elements.deselectAllButton.addEventListener('click', () => {
                this.handleDeselectAll();
            });
        }

        // Toggle Inactive button
        if (this.elements.toggleInactiveButton) {
            this.elements.toggleInactiveButton.addEventListener('click', () => {
                this.handleToggleInactive();
            });
        }

        // Delegate event handling for dynamically created elements
        if (this.elements.selectedDataPointsList) {
            this.elements.selectedDataPointsList.addEventListener('click', (e) => {
                this.handlePanelClick(e);
            });
        }

        if (this.elements.selectedPointsList) {
            this.elements.selectedPointsList.addEventListener('click', (e) => {
                this.handlePanelClick(e);
            });
        }

        console.log('[SelectedDataPointsPanel] Events bound successfully');
    },

    // AppEvents listeners
    setupEventListeners() {
        console.log('[SelectedDataPointsPanel] Setting up AppEvents listeners...');

        // Listen for data point selections from left panel
        AppEvents.on('data-point-selected', (data) => {
            this.handleDataPointSelected(data.fieldId, data);
        });

        AppEvents.on('data-point-deselected', (data) => {
            this.handleDataPointDeselected(data.fieldId);
        });

        // Listen for AppState changes
        // FIX BUG #2: data is the complete dataPoint object, not {fieldId, itemData}
        AppEvents.on('state-dataPoint-added', (dataPoint) => {
            console.log('[SelectedDataPointsPanel] Adding item:', dataPoint);
            this.addItem(dataPoint.id || dataPoint.field_id, dataPoint);
        });

        AppEvents.on('state-dataPoint-removed', (dataPoint) => {
            const fieldId = dataPoint ? (dataPoint.id || dataPoint.field_id) : null;
            if (fieldId) {
                this.removeItem(fieldId);
            }
        });

        AppEvents.on('state-selectedDataPoints-changed', (selectedDataPointsMap) => {
            // FIX BUG #2: selectedDataPointsMap is the Map itself, not {selectedDataPoints: Map}
            this.syncSelectionState(selectedDataPointsMap);
        });

        AppEvents.on('state-configuration-changed', (data) => {
            this.updateConfigurationStatus(data.fieldId, data.status);
        });

        // Listen for configuration and assignment updates
        AppEvents.on('configuration-updated', (data) => {
            this.updateItemStatus(data.fieldId, 'configuration', data.status);
        });

        AppEvents.on('entity-assignment-updated', (data) => {
            this.updateItemStatus(data.fieldId, 'assignment', data.status);
        });

        // Listen for data reload completion
        AppEvents.on('data-points-reload-complete', (data) => {
            this.handleDataReloadComplete(data);
        });

        // Listen for panel refresh requests
        AppEvents.on('panel-refresh-requested', () => {
            this.refreshDisplay();
        });

        // Listen for CoreUI toolbar actions (Phase 3 integration)
        AppEvents.on('toolbar-configure-clicked', (data) => {
            console.log('[SelectedDataPointsPanel] Configure clicked for', data.selectedCount, 'items');
        });

        AppEvents.on('toolbar-assign-clicked', (data) => {
            console.log('[SelectedDataPointsPanel] Assign clicked for', data.selectedCount, 'items');
        });

        console.log('[SelectedDataPointsPanel] AppEvents listeners setup complete');
    },

    // Data point selection handlers
    handleDataPointSelected(fieldId, data) {
        console.log('[SelectedDataPointsPanel] Data point selected:', fieldId);

        if (!fieldId) return;

        // FIX BUG #2 (P0): ALWAYS get complete data from AppState, not from event data
        // Event data may only contain {fieldId, isSelected} without field name/unit/etc
        const itemData = window.AppState ? AppState.selectedDataPoints.get(fieldId) : null;

        if (itemData) {
            this.addItem(fieldId, itemData);
        } else {
            console.warn('[SelectedDataPointsPanel] No item data available for:', fieldId);
        }
    },

    handleDataPointDeselected(fieldId) {
        console.log('[SelectedDataPointsPanel] Data point deselected:', fieldId);
        this.removeItem(fieldId);
    },

    // Item management
    addItem(fieldId, itemData) {
        // Enrich item data with dependency information if it's a computed field
        let enrichedItemData = { ...itemData };

        if (window.DependencyManager && window.DependencyManager.isReady()) {
            // Check if this is a computed field
            const isComputed = itemData.is_computed || false;

            if (isComputed) {
                // Get dependencies from DependencyManager
                const dependencies = window.DependencyManager.getDependencies(fieldId);

                if (dependencies && dependencies.length > 0) {
                    // Enrich with dependency metadata
                    enrichedItemData.dependencies = dependencies.map(depId => {
                        const depMetadata = window.DependencyManager.getFieldMetadata(depId);
                        return {
                            fieldId: depId,
                            field_id: depId,
                            name: depMetadata ? depMetadata.field_name : depId,
                            field_name: depMetadata ? depMetadata.field_name : depId
                        };
                    });

                    console.log(`[SelectedDataPointsPanel] ✓ Enriched computed field with ${dependencies.length} dependencies`);
                } else {
                    console.warn('[SelectedDataPointsPanel] ✗ No dependencies found for computed field:', fieldId);
                }
            }
        } else {
            console.warn('[SelectedDataPointsPanel] DependencyManager not available or not ready');
        }

        // Store item data with is_active flag (default to true for new items)
        this.selectedItems.set(fieldId, {
            ...enrichedItemData,
            fieldId: fieldId,
            addedAt: Date.now(),
            is_active: itemData.is_active !== undefined ? itemData.is_active : true
        });

        // Update display
        this.updateDisplay();
        this.updateVisibility();

        const activeCount = this.getActiveCount();

        // Emit events
        AppEvents.emit('selected-panel-item-added', {
            fieldId: fieldId,
            count: activeCount
        });

        AppEvents.emit('selected-panel-count-changed', {
            count: activeCount
        });
    },

    async removeItem(fieldId) {
        console.log('[SelectedDataPointsPanel] Soft deleting item (marking as inactive):', fieldId);

        if (!this.selectedItems.has(fieldId)) {
            console.log('[SelectedDataPointsPanel] Item not found for removal:', fieldId);
            return;
        }

        // SOFT DELETE: Mark item as inactive instead of removing from Map
        const item = this.selectedItems.get(fieldId);
        item.is_active = false;
        item.deleted_at = new Date().toISOString();

        // Keep item in Map but marked as inactive
        this.selectedItems.set(fieldId, item);

        // CASCADE DELETE: Call backend to deactivate all related assignment records
        try {
            const response = await fetch(`/admin/api/assignments/by-field/${fieldId}/deactivate-all`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    reason: 'Field soft deleted by user'
                })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('[SelectedDataPointsPanel] Backend cascade delete successful:', result);

                // Show success message if available
                if (result.message) {
                    console.log('[SelectedDataPointsPanel] ' + result.message);
                }
            } else {
                const error = await response.json();
                console.error('[SelectedDataPointsPanel] Backend cascade delete failed:', error);
            }
        } catch (error) {
            console.error('[SelectedDataPointsPanel] Error calling cascade delete endpoint:', error);
        }

        // Update display (will filter based on showInactive state)
        this.updateDisplay();
        this.updateVisibility();

        // Get active and total counts
        const activeCount = this.getActiveCount();
        const totalCount = this.selectedItems.size;

        // Emit events
        AppEvents.emit('selected-panel-item-deactivated', {
            fieldId: fieldId,
            activeCount: activeCount,
            totalCount: totalCount
        });

        AppEvents.emit('datapoint-deactivated', { // Updated event name
            fieldId: fieldId
        });

        AppEvents.emit('selected-panel-count-changed', {
            count: activeCount // Use active count for consistency
        });

        console.log('[SelectedDataPointsPanel] Item marked as inactive:', {
            fieldId,
            activeCount,
            totalCount,
            inactiveCount: totalCount - activeCount
        });
    },

    // Display management
    updateDisplay() {
        console.log('[SelectedDataPointsPanel] Updating display...');

        const container = this.elements.selectedDataPointsList || this.elements.selectedPointsList;
        if (!container) {
            console.warn('[SelectedDataPointsPanel] No container element found for display update');
            return;
        }

        // Update count display
        this.updateSelectedCount();

        if (this.selectedItems.size === 0) {
            this.showEmptyState();
            return;
        }

        this.hideEmptyState();

        // ALWAYS use dependency grouping when DependencyManager is available
        // This ensures computed fields show with their visual indicators
        let html = '';
        if (window.DependencyManager && window.DependencyManager.isReady()) {
            console.log('[SelectedDataPointsPanel] ✓ Using dependency grouping (DependencyManager active)');
            html = this.generateFlatHTMLWithDependencyGrouping();
        } else {
            // Fallback to legacy grouping methods when DependencyManager not available
            console.log('[SelectedDataPointsPanel] Using legacy grouping:', this.groupingMethod);
            switch (this.groupingMethod) {
                case 'topic':
                    html = this.generateTopicGroupsHTML();
                    break;
                case 'framework':
                    html = this.generateFrameworkGroupsHTML();
                    break;
                default:
                    html = this.generateFlatHTML();
            }
        }

        container.innerHTML = html;

        // Update button states
        this.updateBulkSelectionButtons();

        // Setup dependency toggle listeners (for collapsible groups)
        this.setupDependencyToggleListeners();

        // Emit display updated event
        AppEvents.emit('selected-panel-updated', {
            itemCount: this.selectedItems.size,
            groupingMethod: this.groupingMethod
        });
    },

    updateSelectedCount() {
        const activeCount = this.getActiveCount();
        const totalCount = this.selectedItems.size;
        const inactiveCount = totalCount - activeCount;

        // Display format: "X selected" or "X selected (Y inactive)" if there are inactive items
        let displayText = `${activeCount} selected`;
        if (inactiveCount > 0 && this.showInactive) {
            displayText = `${activeCount} active, ${inactiveCount} inactive`;
        }

        if (this.elements.countDisplay) {
            this.elements.countDisplay.textContent = displayText;
        }

        // Update any count badges in the UI
        const countBadges = document.querySelectorAll('.selected-count-badge');
        countBadges.forEach(badge => {
            badge.textContent = activeCount;
        });

        console.log('[SelectedDataPointsPanel] Count updated:', {
            activeCount,
            inactiveCount,
            totalCount,
            displayText
        });
    },

    // HTML generation methods
    generateTopicGroupsHTML() {
        console.log('[SelectedDataPointsPanel] Generating topic groups HTML...');

        // Group items by topic
        const topicGroups = this.groupItemsByTopic();
        let html = '<div class="selected-points-grouped">';

        // Sort topic groups alphabetically
        const sortedTopics = Array.from(topicGroups.entries()).sort((a, b) => {
            return a[0].localeCompare(b[0]);
        });

        sortedTopics.forEach(([topicName, items]) => {
            const filteredItems = this.showInactive ? items : items.filter(item => !this.isInactiveItem(item));

            if (filteredItems.length === 0) return;

            html += `
                <div class="topic-group">
                    <div class="topic-group-header">
                        <div class="topic-group-name">
                            ${topicName}
                        </div>
                        <div class="topic-group-count">${filteredItems.length}</div>
                    </div>
                    <div class="topic-group-items">
            `;

            // Sort items alphabetically within each topic
            filteredItems.sort((a, b) => {
                const nameA = (a.name || a.field_name || '').toLowerCase();
                const nameB = (b.name || b.field_name || '').toLowerCase();
                return nameA.localeCompare(nameB);
            });

            filteredItems.forEach(item => {
                html += this.generateItemHTML(item);
            });

            html += `
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    },

    generateFrameworkGroupsHTML() {
        console.log('[SelectedDataPointsPanel] Generating framework groups HTML...');

        // Group items by framework
        const frameworkGroups = this.groupItemsByFramework();
        let html = '<div class="selected-items-grouped">';

        frameworkGroups.forEach((items, frameworkName) => {
            const filteredItems = this.showInactive ? items : items.filter(item => !this.isInactiveItem(item));

            if (filteredItems.length === 0) return;

            html += `
                <div class="framework-group" data-framework="${frameworkName}">
                    <div class="framework-group-header">
                        <h4 class="framework-name">${frameworkName}</h4>
                        <span class="framework-count">(${filteredItems.length})</span>
                    </div>
                    <div class="framework-items">
            `;

            filteredItems.forEach(item => {
                html += this.generateItemHTML(item);
            });

            html += `
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    },

    generateFlatHTML() {
        console.log('[SelectedDataPointsPanel] Generating flat HTML...');

        // Use dependency grouping if DependencyManager is available and ready
        const depMgrAvailable = !!window.DependencyManager;
        const depMgrReady = window.DependencyManager?.isReady() || false;
        console.log('[SelectedDataPointsPanel] DependencyManager available:', depMgrAvailable, 'ready:', depMgrReady);

        if (window.DependencyManager && window.DependencyManager.isReady()) {
            console.log('[SelectedDataPointsPanel] ✓ Using dependency grouping layout');
            return this.generateFlatHTMLWithDependencyGrouping();
        }

        // Fallback to original flat layout
        console.log('[SelectedDataPointsPanel] ✗ Using fallback flat layout (no dependency grouping)');
        let html = '<div class="selected-items-flat">';

        const items = Array.from(this.selectedItems.values());
        const filteredItems = this.showInactive ? items : items.filter(item => !this.isInactiveItem(item));

        filteredItems.forEach(item => {
            html += this.generateItemHTML(item);
        });

        html += '</div>';
        return html;
    },

    generateItemHTML(item) {
        const fieldId = item.fieldId || item.field_id;
        const configStatus = this.getConfigurationStatus(fieldId);
        const assignmentStatus = this.getAssignmentStatus(fieldId);
        const isInactive = this.isInactiveItem(item);

        // Determine item type
        const isComputed = item.is_computed || false;
        const hasDependencies = item.dependencies && item.dependencies.length > 0;
        const isDependency = item.isDependency || false;
        const depCount = hasDependencies ? item.dependencies.length : 0;
        const isCollapsed = hasDependencies ? this.isGroupCollapsed(fieldId) : false;

        // Build CSS classes
        let itemClasses = 'topic-group-item selected-point-item';
        if (isInactive) itemClasses += ' inactive';
        if (isComputed) itemClasses += ' is-computed';
        if (isDependency) itemClasses += ' is-dependency';

        return `
            <div class="${itemClasses}" data-field-id="${fieldId}"${isDependency && item.parentId ? ` data-parent-id="${item.parentId}"` : ''}>
                ${hasDependencies ? `
                <button class="dependency-toggle-btn" data-field-id="${fieldId}" aria-label="${isCollapsed ? 'Expand' : 'Collapse'} dependencies">
                    <i class="fas fa-chevron-${isCollapsed ? 'right' : 'down'}"></i>
                </button>
                ` : ''}
                ${isDependency ? `
                <div class="dependency-indicator" title="Dependency">
                    <i class="fas fa-arrow-turn-down-right"></i>
                </div>
                ` : ''}
                <div class="point-checkbox">
                    <input type="checkbox" class="form-check-input point-select" id="selected_${fieldId}" data-field-id="${fieldId}">
                </div>
                <div class="point-content">
                    <div class="point-header">
                        <h6 class="point-title">
                            ${isComputed ? `
                            <span class="computed-badge" data-field-id="${fieldId}" title="Computed Field">
                                <i class="fas fa-calculator"></i>
                            </span>
                            ` : ''}
                            ${item.name || item.field_name || 'Unnamed Field'}
                            ${hasDependencies ? `<span class="dependency-count-badge" title="${depCount} dependencies">${depCount}</span>` : ''}
                        </h6>
                        ${isInactive ? '<span class="inactive-badge"><i class="fas fa-pause-circle"></i> Inactive</span>' : ''}
                    </div>
                    <!-- Phase 9.5: Dimension badges container -->
                    <div class="dimension-badges-container" id="field-badges-${fieldId}" data-field-id="${fieldId}">
                        <!-- Dimension badges will be rendered here by DimensionBadge.js -->
                    </div>
                    <div class="point-details">
                        <div class="detail-item">
                            <strong>Field Code:</strong> ${item.field_code || 'N/A'}
                        </div>
                        <div class="detail-item">
                            <strong>Configuration:</strong>
                            ${configStatus.text !== 'Not configured' ?
                                `<span class="text-success">${configStatus.text}</span>` :
                                '<span class="text-warning">Not configured</span>'
                            }
                        </div>
                        <div class="detail-item">
                            <strong>Entities:</strong>
                            ${assignmentStatus.text !== 'No entities assigned' ?
                                `<span class="text-success">${assignmentStatus.text}</span>` :
                                '<span class="text-warning">No entities assigned</span>'
                            }
                        </div>
                    </div>
                </div>
                <div class="point-actions">
                    <button type="button" class="action-btn info field-info-single" data-field-id="${fieldId}" title="View field information">
                        <i class="fas fa-info-circle"></i>
                    </button>
                    <button type="button" class="action-btn configure-single ${configStatus.class === 'configured' ? 'status-configured' : 'status-not-configured'}" data-field-id="${fieldId}" title="${configStatus.class === 'configured' ? '✓ Material topic assigned' : 'Configure material topic'}">
                        <i class="fas fa-cog"></i>
                    </button>
                    <button type="button" class="action-btn secondary assign-single ${assignmentStatus.class === 'assigned' ? 'status-assigned' : 'status-not-assigned'}" data-field-id="${fieldId}" title="${assignmentStatus.class === 'assigned' ? `✓ ${assignmentStatus.count || 0} entities assigned` : 'Assign entities to this data point'}" ${assignmentStatus.class === 'assigned' && assignmentStatus.count ? `data-entity-count="${assignmentStatus.count}"` : ''}>
                        <i class="fas fa-building"></i>
                    </button>
                    <!-- Phase 9.5: Manage Dimensions button -->
                    <button type="button" class="action-btn manage-dimensions-btn" data-field-id="${fieldId}" data-field-name="${item.name || item.field_name || 'Unnamed Field'}" title="Manage field dimensions">
                        <i class="fas fa-layer-group"></i>
                    </button>
                    <button type="button" class="remove-point" data-field-id="${fieldId}" title="Remove from selection">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    },

    generateDependenciesHTML(item) {
        if (!item.dependencies || item.dependencies.length === 0) return '';

        return `
            <div class="dependencies-section">
                <div class="dependencies-header">
                    <div class="dependencies-toggle">
                        <i class="fas fa-chevron-right toggle-icon"></i>
                        <span class="dependencies-title">Dependencies (${item.dependencies.length})</span>
                    </div>
                    <div class="dependencies-info">
                        <i class="fas fa-info-circle" title="Auto-added dependencies inherit configuration"></i>
                    </div>
                </div>
                <div class="dependencies-list" style="display: none;">
                    ${item.dependencies.map(dep => `
                        <div class="dependency-item" data-field-id="${dep.fieldId}">
                            <span class="dependency-name">${dep.name}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    },

    // Grouping methods
    groupItemsByTopic() {
        const groups = new Map();

        this.selectedItems.forEach((item, fieldId) => {
            // BUG FIX: Group by company material topics (assigned_topic_id) instead of framework topics (topic_name)
            // Check if this data point has a material topic assigned
            const assignedTopicId = window.AppState?.topicAssignments?.get(fieldId);

            let topicName = 'Unassigned'; // Default category for data points without material topic

            if (assignedTopicId) {
                // Get the topic name from the current assignment data, not the cached item
                // This ensures we use the latest topic assignment after updates
                const currentAssignment = item.current_assignment;
                if (currentAssignment && currentAssignment.assigned_topic_name) {
                    topicName = currentAssignment.assigned_topic_name;
                } else if (item.assigned_topic_name) {
                    // Fallback to item's assigned_topic_name if current_assignment doesn't have it
                    topicName = item.assigned_topic_name;
                }
            }

            if (!groups.has(topicName)) {
                groups.set(topicName, []);
            }

            groups.get(topicName).push(item);
        });

        return groups;
    },

    groupItemsByFramework() {
        const groups = new Map();

        this.selectedItems.forEach((item, fieldId) => {
            const frameworkName = item.framework_name || 'Other';

            if (!groups.has(frameworkName)) {
                groups.set(frameworkName, []);
            }

            groups.get(frameworkName).push(item);
        });

        return groups;
    },

    // Event handlers for panel interactions
    handlePanelClick(e) {
        const target = e.target;

        // Handle remove button clicks (.remove-point or .remove-selected-btn)
        if (target.closest('.remove-point') || target.closest('.remove-selected-btn')) {
            const btn = target.closest('.remove-point') || target.closest('.remove-selected-btn');
            const fieldId = btn.dataset.fieldId;
            this.handleRemoveClick(fieldId);
            return;
        }

        // Handle configure button clicks
        if (target.closest('.configure-single')) {
            const fieldId = target.closest('.configure-single').dataset.fieldId;
            this.handleConfigureClick(fieldId);
            return;
        }

        // Handle assign entities button clicks
        if (target.closest('.assign-single')) {
            const fieldId = target.closest('.assign-single').dataset.fieldId;
            this.handleAssignClick(fieldId);
            return;
        }

        // Handle field info button clicks
        if (target.closest('.field-info-single')) {
            const fieldId = target.closest('.field-info-single').dataset.fieldId;
            this.handleFieldInfoClick(fieldId);
            return;
        }

        // Handle checkbox changes
        if (target.classList.contains('point-select')) {
            const fieldId = target.dataset.fieldId;
            const isChecked = target.checked;
            this.handleItemCheckboxChange(fieldId, isChecked);
            return;
        }

        // Handle dependencies toggle
        if (target.closest('.dependencies-toggle')) {
            this.handleDependenciesToggle(target.closest('.dependencies-section'));
            return;
        }

        // Handle item click for details
        if (target.closest('.selected-point-item')) {
            const fieldId = target.closest('.selected-point-item').dataset.fieldId;
            this.handleItemClick(fieldId);
        }
    },

    async handleRemoveClick(fieldId) {
        console.log('[SelectedDataPointsPanel] Remove clicked for:', fieldId);

        // Check if DependencyManager is available and this field is a dependency
        if (window.DependencyManager && window.DependencyManager.isReady()) {
            const dependentFields = window.DependencyManager.getDependentFields(fieldId);

            if (dependentFields && dependentFields.length > 0) {
                // Check if any dependent computed fields are selected
                const selectedDependents = dependentFields.filter(depFieldId =>
                    window.AppState && AppState.isSelected(depFieldId)
                );

                if (selectedDependents.length > 0) {
                    // Get field names for warning message
                    const dependentNames = selectedDependents.map(depId => {
                        const metadata = window.DependencyManager.getFieldMetadata(depId);
                        return metadata ? metadata.field_name : depId;
                    });

                    // Emit event for DependencyManager to show warning
                    AppEvents.emit('data-point-remove-requested', {fieldId});

                    // Show warning and get confirmation
                    const fieldMetadata = window.DependencyManager.getFieldMetadata(fieldId);
                    const fieldName = fieldMetadata ? fieldMetadata.field_name : fieldId;

                    const confirmed = await window.DependencyManager.showRemovalWarning(
                        fieldName,
                        dependentNames
                    );

                    if (!confirmed) {
                        console.log('[SelectedDataPointsPanel] Removal cancelled by user');
                        return; // Don't remove if user cancels
                    }

                    // If confirmed, also remove dependent computed fields
                    console.log('[SelectedDataPointsPanel] Removing field and its dependents:', selectedDependents);
                    selectedDependents.forEach(depId => {
                        this.removeItem(depId);
                    });
                }
            }
        }

        this.removeItem(fieldId);
    },

    handleConfigureClick(fieldId) {
        console.log('[SelectedDataPointsPanel] Configure clicked for:', fieldId);
        AppEvents.emit('configure-single-clicked', {
            fieldId: fieldId,
            itemData: this.selectedItems.get(fieldId)
        });
    },

    handleAssignClick(fieldId) {
        console.log('[SelectedDataPointsPanel] Assign clicked for:', fieldId);
        AppEvents.emit('assign-single-clicked', {
            fieldId: fieldId,
            itemData: this.selectedItems.get(fieldId)
        });
    },

    handleFieldInfoClick(fieldId) {
        console.log('[SelectedDataPointsPanel] Field info clicked for:', fieldId);
        AppEvents.emit('show-field-info', {
            fieldId: fieldId,
            itemData: this.selectedItems.get(fieldId)
        });
    },

    handleItemCheckboxChange(fieldId, isChecked) {
        console.log('[SelectedDataPointsPanel] Item checkbox changed:', fieldId, isChecked);

        // Note: Checkbox state is managed by this panel, but we emit events
        // for other modules to respond to
        AppEvents.emit('selected-panel-item-checkbox-changed', {
            fieldId: fieldId,
            isChecked: isChecked
        });
    },

    handleItemClick(fieldId) {
        console.log('[SelectedDataPointsPanel] Item clicked:', fieldId);

        AppEvents.emit('selected-panel-item-clicked', {
            fieldId: fieldId,
            itemData: this.selectedItems.get(fieldId)
        });
    },

    handleDependenciesToggle(section) {
        const list = section.querySelector('.dependencies-list');
        const icon = section.querySelector('.toggle-icon');

        if (list.style.display === 'none') {
            list.style.display = 'block';
            icon.className = 'fas fa-chevron-down toggle-icon';
        } else {
            list.style.display = 'none';
            icon.className = 'fas fa-chevron-right toggle-icon';
        }
    },

    handleDataReloadComplete(data) {
        console.log('[SelectedDataPointsPanel] Data reload complete:', data);

        // Update display with new data
        this.updateDisplay();

        // Re-enable and update the toggle button
        if (this.elements.toggleInactiveButton) {
            this.elements.toggleInactiveButton.disabled = false;

            if (this.showInactive) {
                // Showing inactive - button should say "Hide Inactive" with eye icon
                this.elements.toggleInactiveButton.innerHTML = '<i class="fas fa-eye" aria-hidden="true"></i> Hide Inactive';
                this.elements.toggleInactiveButton.title = 'Hide inactive assignments';
            } else {
                // Hiding inactive - button should say "Show Inactive" with eye-slash icon
                this.elements.toggleInactiveButton.innerHTML = '<i class="fas fa-eye-slash" aria-hidden="true"></i> Show Inactive';
                this.elements.toggleInactiveButton.title = 'Show inactive assignments';
            }
        }

        // Emit event to notify reload complete
        AppEvents.emit('inactive-toggle-changed', {
            showInactive: this.showInactive,
            visibleItemCount: this.getVisibleItemCount()
        });
    },

    // Bulk operations
    handleSelectAll() {
        console.log('[SelectedDataPointsPanel] Select All clicked');

        // Check all checkboxes in the right panel
        const checkboxes = document.querySelectorAll('.selected-point-item .point-select');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
        });

        // Update bulk selection button states
        this.updateBulkSelectionButtons();

        // Emit event
        AppEvents.emit('bulk-selection-changed', {
            action: 'select-all',
            affectedItems: Array.from(this.selectedItems.keys())
        });
    },

    handleDeselectAll() {
        console.log('[SelectedDataPointsPanel] Deselect All clicked');

        // Deselect All should only UNCHECK boxes, not remove items from the panel
        // This matches the old implementation behavior where items stay visible but unchecked

        // Uncheck all checkboxes in the right panel
        const checkboxes = document.querySelectorAll('.selected-point-item .point-select');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });

        // Update bulk selection button states (should disable configure/assign buttons)
        this.updateBulkSelectionButtons();

        // Emit event to update toolbar buttons (no items are "selected" for actions)
        AppEvents.emit('bulk-selection-changed', {
            action: 'deselect-all',
            affectedItems: [] // No items removed, just unchecked
        });

        // Update toolbar to reflect that no items are checked (for configure/assign actions)
        AppEvents.emit('toolbar-buttons-updated', {
            hasSelection: false,
            selectedCount: 0
        });

        console.log('[SelectedDataPointsPanel] Deselect All completed. Items remain visible but unchecked.');
    },

    async handleToggleInactive() {
        console.log('[SelectedDataPointsPanel] Toggle Inactive clicked');

        this.showInactive = !this.showInactive;

        // Update button state, text, and icon
        if (this.elements.toggleInactiveButton) {
            this.elements.toggleInactiveButton.classList.toggle('active', this.showInactive);
            this.elements.toggleInactiveButton.disabled = true; // Disable during reload

            // Update button text and icon
            if (this.showInactive) {
                // Showing inactive - button should say "Hide Inactive" with eye icon
                this.elements.toggleInactiveButton.innerHTML = '<i class="fas fa-spinner fa-spin" aria-hidden="true"></i> Loading...';
                this.elements.toggleInactiveButton.title = 'Loading inactive assignments...';
            } else {
                // Hiding inactive - button should say "Show Inactive" with eye-slash icon
                this.elements.toggleInactiveButton.innerHTML = '<i class="fas fa-spinner fa-spin" aria-hidden="true"></i> Loading...';
                this.elements.toggleInactiveButton.title = 'Loading active assignments...';
            }
        }

        // Emit event to request data reload with include_inactive parameter
        AppEvents.emit('reload-data-points-requested', {
            includeInactive: this.showInactive
        });

        // Note: The display will be updated after the data reload completes
        // The button will be re-enabled in the afterReloadComplete handler
    },

    updateBulkSelectionButtons() {
        const checkboxes = document.querySelectorAll('.selected-point-item .point-select');
        const checkedCount = document.querySelectorAll('.selected-point-item .point-select:checked').length;

        if (this.elements.selectAllButton) {
            this.elements.selectAllButton.disabled = (checkedCount === checkboxes.length);
        }

        if (this.elements.deselectAllButton) {
            this.elements.deselectAllButton.disabled = (checkedCount === 0);
        }
    },

    // Status management
    updateItemStatus(fieldId, statusType, statusValue) {
        console.log('[SelectedDataPointsPanel] Updating item status:', fieldId, statusType, statusValue);

        if (statusType === 'configuration') {
            this.configurationStatus.set(fieldId, statusValue);
        } else if (statusType === 'assignment') {
            this.entityAssignments.set(fieldId, statusValue);
        }

        // Update visual indicators
        const itemElements = document.querySelectorAll(`[data-field-id="${fieldId}"]`);
        itemElements.forEach(element => {
            const statusElement = element.querySelector(`.${statusType}-status`);
            if (statusElement) {
                const statusInfo = this.getStatusInfo(statusType, statusValue);
                statusElement.className = `status-icon ${statusType}-status ${statusInfo.class}`;

                const statusValueElement = element.querySelector(`.${statusType}-value`);
                if (statusValueElement) {
                    statusValueElement.textContent = statusInfo.text;
                }
            }
        });
    },

    updateConfigurationStatus(fieldId, status) {
        this.updateItemStatus(fieldId, 'configuration', status);
    },

    getConfigurationStatus(fieldId) {
        // Check AppState for material topic assignment
        const hasTopic = window.AppState?.topicAssignments?.get(fieldId);
        const status = hasTopic ? 'configured' : 'not_configured';
        return this.getStatusInfo('configuration', status);
    },

    getAssignmentStatus(fieldId) {
        // Check AppState for entity assignments
        const entities = window.AppState?.entityAssignments?.get(fieldId);
        const entityCount = entities ? entities.size : 0;

        // Determine status based on entity count
        const status = entityCount > 0 ? 'assigned' : 'not_assigned';
        const statusInfo = this.getStatusInfo('assignment', status);

        // Add entity count to status info
        return {
            ...statusInfo,
            count: entityCount
        };
    },

    getStatusInfo(type, status) {
        const statusMap = {
            configuration: {
                configured: { class: 'configured', text: 'Configured' },
                partially_configured: { class: 'partial', text: 'Partial' },
                not_configured: { class: 'not-configured', text: 'Not configured' }
            },
            assignment: {
                assigned: { class: 'assigned', text: 'Assigned' },
                partially_assigned: { class: 'partial', text: 'Partial' },
                not_assigned: { class: 'not-assigned', text: 'No entities assigned' }
            }
        };

        return statusMap[type]?.[status] || { class: 'unknown', text: 'Unknown' };
    },

    // Visibility management
    updateVisibility() {
        const shouldShow = this.selectedItems.size > 0;

        if (shouldShow !== this.isVisible) {
            this.isVisible = shouldShow;

            if (this.elements.panelContainer) {
                this.elements.panelContainer.style.display = shouldShow ? 'block' : 'none';
            }

            AppEvents.emit('selected-panel-visibility-changed', {
                isVisible: shouldShow,
                itemCount: this.selectedItems.size
            });
        }
    },

    showEmptyState() {
        const container = this.elements.selectedDataPointsList || this.elements.selectedPointsList;
        if (container) {
            container.innerHTML = `
                <div class="selected-panel-empty-state">
                    <div class="empty-state-icon">
                        <i class="fas fa-list"></i>
                    </div>
                    <div class="empty-state-message">
                        <h3>No data points selected</h3>
                        <p>Select data points from the left panel to see them here</p>
                    </div>
                </div>
            `;
        }
    },

    hideEmptyState() {
        // Empty state is replaced by actual content in updateDisplay()
    },

    // Utility methods
    syncSelectionState(selectedDataPointsMap) {
        console.log('[SelectedDataPointsPanel] Syncing selection state:', selectedDataPointsMap);

        // FIX BUG #2: Handle Map object from AppState, not array
        if (!selectedDataPointsMap || !(selectedDataPointsMap instanceof Map)) {
            console.warn('[SelectedDataPointsPanel] Invalid selectedDataPointsMap, expected Map:', selectedDataPointsMap);
            return;
        }

        // Clear current items that aren't in the new selection
        const newSelectionKeys = new Set(selectedDataPointsMap.keys());

        Array.from(this.selectedItems.keys()).forEach(fieldId => {
            if (!newSelectionKeys.has(fieldId)) {
                this.selectedItems.delete(fieldId);
            }
        });

        // Add new items from the Map (each entry is [fieldId, dataPoint])
        selectedDataPointsMap.forEach((dataPoint, fieldId) => {
            if (!this.selectedItems.has(fieldId)) {
                this.selectedItems.set(fieldId, {
                    ...dataPoint,
                    fieldId: fieldId,
                    addedAt: Date.now()
                });
            }
        });

        this.updateDisplay();
        this.updateVisibility();
    },

    isInactiveItem(item) {
        // Logic to determine if an item is inactive based on assignment status
        // Check both is_active flag (soft delete) and legacy is_inactive flag
        return item.is_active === false || item.is_inactive === true;
    },

    getActiveCount() {
        // Count only active items (not soft-deleted)
        return Array.from(this.selectedItems.values())
            .filter(item => item.is_active !== false).length;
    },

    getVisibleItemCount() {
        if (this.showInactive) {
            return this.selectedItems.size;
        }

        return Array.from(this.selectedItems.values()).filter(item =>
            !this.isInactiveItem(item)
        ).length;
    },

    refreshDisplay() {
        console.log('[SelectedDataPointsPanel] Refreshing display...');
        this.updateDisplay();
        this.updateVisibility();
    },

    // Grouping method management
    setGroupingMethod(method) {
        if (['topic', 'framework', 'none'].includes(method)) {
            this.groupingMethod = method;
            this.updateDisplay();

            AppEvents.emit('selected-panel-grouping-changed', {
                groupingMethod: method
            });
        }
    },

    // Public API methods
    getSelectedItems() {
        return Array.from(this.selectedItems.keys());
    },

    getSelectedCount() {
        return this.selectedItems.size;
    },

    getVisibleCount() {
        return this.getVisibleItemCount();
    },

    hasItem(fieldId) {
        return this.selectedItems.has(fieldId);
    },

    getItem(fieldId) {
        return this.selectedItems.get(fieldId);
    },

    clearAll() {
        console.log('[SelectedDataPointsPanel] Clearing all items');

        const clearedItems = Array.from(this.selectedItems.keys());
        this.selectedItems.clear();

        this.updateDisplay();
        this.updateVisibility();

        AppEvents.emit('selected-panel-cleared', {
            clearedItems: clearedItems
        });
    },

    // ============================================================================
    // COLLAPSIBLE DEPENDENCY GROUPING FEATURE
    // ============================================================================

    /**
     * Generates HTML with collapsible dependency grouping
     * Groups dependencies under their computed fields with expand/collapse functionality
     */
    generateFlatHTMLWithDependencyGrouping() {
        console.log('[SelectedDataPointsPanel] Generating flat HTML with dependency grouping...');

        const items = Array.from(this.selectedItems.values());

        // Build dependency map from ALL items first (before filtering)
        // This ensures we know the relationships even for inactive items
        const fullDependencyMap = this.buildDependencyMap(items);

        // When hiding inactive, we need to handle orphaned active dependencies
        let filteredItems = items;
        let orphanedActiveDependencies = [];

        if (!this.showInactive) {
            // Separate inactive computed fields and collect their active dependencies
            items.forEach(item => {
                const fieldId = item.fieldId || item.field_id;
                const isInactive = this.isInactiveItem(item);

                // If this is an inactive computed field
                if (isInactive && fullDependencyMap.has(fieldId)) {
                    const depInfo = fullDependencyMap.get(fieldId);
                    const dependencies = depInfo ? depInfo.dependencies : [];

                    // Check each dependency - if it's active, it should be shown as standalone
                    dependencies.forEach(dep => {
                        if (dep && !this.isInactiveItem(dep)) {
                            orphanedActiveDependencies.push(dep);
                        }
                    });
                }
            });

            // Filter out inactive items
            filteredItems = items.filter(item => !this.isInactiveItem(item));

            // Add orphaned active dependencies back to filteredItems if not already present
            orphanedActiveDependencies.forEach(dep => {
                const depId = dep.fieldId || dep.field_id;
                const alreadyInFiltered = filteredItems.some(item =>
                    (item.fieldId || item.field_id) === depId
                );
                if (!alreadyInFiltered) {
                    filteredItems.push(dep);
                }
            });
        }

        // Get dependency relationships for active items
        const dependencyMap = this.buildDependencyMap(filteredItems);

        // Separate computed fields and standalone fields
        const { computedFields, standaloneFields } = this.categorizeFields(filteredItems, dependencyMap);

        let html = '<div class="selected-items-flat with-dependency-grouping">';

        // Render computed fields with their dependencies
        computedFields.forEach(computedField => {
            html += this.generateComputedFieldGroupHTML(computedField, dependencyMap);
        });

        // Render standalone fields (not computed, not dependencies)
        standaloneFields.forEach(field => {
            html += this.generateItemHTML(field);
        });

        html += '</div>';
        return html;
    },

    /**
     * Build dependency map from DependencyManager's API
     */
    buildDependencyMap(items) {
        const dependencyMap = new Map();

        if (!window.DependencyManager || !window.DependencyManager.isReady()) {
            console.warn('[SelectedDataPointsPanel] DependencyManager not ready');
            return dependencyMap;
        }

        // Get dependency data from DependencyManager's public API
        const depMap = window.DependencyManager.getDependencyMap();

        items.forEach(item => {
            const fieldId = item.fieldId || item.field_id;

            // Check if this field has dependencies in DependencyManager
            const depIds = depMap.get(fieldId);

            // Also check if the item itself has dependencies attached (from addItem enrichment)
            const itemDependencies = item.dependencies;

            if ((depIds && depIds.length > 0) || (itemDependencies && itemDependencies.length > 0)) {
                // Prefer item dependencies if available (already enriched), otherwise use DependencyManager
                let dependencies = [];

                if (itemDependencies && itemDependencies.length > 0) {
                    // Use enriched dependencies from item
                    dependencies = itemDependencies;
                } else if (depIds && depIds.length > 0) {
                    // Build dependencies from DependencyManager
                    dependencies = depIds.map(depId => {
                        // First try to find in items
                        let depField = items.find(i => (i.fieldId || i.field_id) === depId);

                        // If not found in items, get from DependencyManager metadata
                        if (!depField) {
                            const depMetadata = window.DependencyManager.getFieldMetadata(depId);
                            if (depMetadata) {
                                depField = {
                                    fieldId: depId,
                                    field_id: depId,
                                    name: depMetadata.field_name,
                                    field_name: depMetadata.field_name,
                                    is_computed: depMetadata.is_computed
                                };
                            }
                        }

                        return depField;
                    }).filter(Boolean); // Remove undefined items
                }

                if (dependencies.length > 0) {
                    dependencyMap.set(fieldId, {
                        field: item,
                        dependencies: dependencies
                    });
                }
            }
        });

        return dependencyMap;
    },

    /**
     * Categorize fields into computed and standalone
     */
    categorizeFields(items, dependencyMap) {
        const computedFields = [];
        const dependencyFieldIds = new Set();
        const standaloneFields = [];

        // Collect all dependency field IDs
        dependencyMap.forEach(({ dependencies }) => {
            dependencies.forEach(dep => {
                const depId = dep.fieldId || dep.field_id;
                dependencyFieldIds.add(depId);
            });
        });

        items.forEach(item => {
            const fieldId = item.fieldId || item.field_id;

            if (dependencyMap.has(fieldId)) {
                // This is a computed field
                computedFields.push(item);
            } else if (!dependencyFieldIds.has(fieldId)) {
                // This is a standalone field (not computed, not a dependency)
                standaloneFields.push(item);
            }
            // Dependencies are not added to standalone - they'll be rendered under their computed field
        });

        return { computedFields, standaloneFields };
    },

    /**
     * Generate HTML for a computed field with collapsible dependencies
     */
    generateComputedFieldGroupHTML(computedField, dependencyMap) {
        const fieldId = computedField.fieldId || computedField.field_id;
        const depInfo = dependencyMap.get(fieldId);
        const dependencies = depInfo ? depInfo.dependencies : [];
        const isCollapsed = this.isGroupCollapsed(fieldId); // Check collapse state

        let html = `
            <div class="computed-field-group" data-field-id="${fieldId}">
                <!-- Computed Field (Parent) -->
                <div class="computed-field-parent">
                    ${this.generateItemHTML(computedField)}
                </div>

                <!-- Dependencies (Children) - Collapsible -->
                <div class="computed-field-dependencies ${isCollapsed ? 'collapsed' : 'expanded'}" data-parent-id="${fieldId}">
        `;

        dependencies.forEach(dependency => {
            if (dependency) {
                // Mark as dependency and add parent reference
                const depItem = {
                    ...dependency,
                    isDependency: true,
                    parentId: fieldId
                };
                html += this.generateItemHTML(depItem);
            }
        });

        html += `
                </div>
            </div>
        `;

        return html;
    },

    /**
     * Generate HTML for a computed field item with toggle button
     */
    generateComputedFieldHTML(item, depCount, isCollapsed) {
        const fieldId = item.fieldId || item.field_id;
        const configStatus = this.getConfigurationStatus(fieldId);
        const assignmentStatus = this.getAssignmentStatus(fieldId);
        const isInactive = this.isInactiveItem(item);

        return `
            <div class="topic-group-item selected-point-item is-computed${isInactive ? ' inactive' : ''}" data-field-id="${fieldId}">
                <button class="dependency-toggle-btn" data-field-id="${fieldId}" aria-label="${isCollapsed ? 'Expand' : 'Collapse'} dependencies">
                    <i class="fas fa-chevron-${isCollapsed ? 'right' : 'down'}"></i>
                </button>
                <div class="point-checkbox">
                    <input type="checkbox" class="form-check-input point-select" id="selected_${fieldId}" data-field-id="${fieldId}">
                </div>
                <div class="point-content">
                    <div class="point-header">
                        <h6 class="point-title">
                            <span class="computed-indicator" title="Computed Field">
                                <i class="fas fa-calculator"></i>
                            </span>
                            ${item.name || item.field_name || 'Unnamed Field'}
                            <span class="dependency-count-badge" title="${depCount} dependencies">${depCount}</span>
                        </h6>
                        ${isInactive ? '<span class="inactive-badge"><i class="fas fa-pause-circle"></i> Inactive</span>' : ''}
                    </div>
                    <div class="point-details">
                        <div class="detail-item">
                            <strong>Field Code:</strong> ${item.field_code || 'N/A'}
                        </div>
                        <div class="detail-item">
                            <strong>Configuration:</strong>
                            ${configStatus.text !== 'Not configured' ?
                                `<span class="text-success">${configStatus.text}</span>` :
                                '<span class="text-warning">Not configured</span>'
                            }
                        </div>
                        <div class="detail-item">
                            <strong>Entities:</strong>
                            ${assignmentStatus.text !== 'No entities assigned' ?
                                `<span class="text-success">${assignmentStatus.text}</span>` :
                                '<span class="text-muted">No entities assigned</span>'
                            }
                        </div>
                    </div>
                </div>
                <button class="remove-point-btn" data-field-id="${fieldId}" title="Remove field">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
    },

    /**
     * Generate HTML for a dependency item (child)
     */
    generateDependencyHTML(item, parentId) {
        const fieldId = item.fieldId || item.field_id;
        const configStatus = this.getConfigurationStatus(fieldId);
        const assignmentStatus = this.getAssignmentStatus(fieldId);
        const isInactive = this.isInactiveItem(item);

        return `
            <div class="topic-group-item selected-point-item is-dependency${isInactive ? ' inactive' : ''}"
                 data-field-id="${fieldId}"
                 data-parent-id="${parentId}">
                <div class="dependency-indicator" title="Dependency">
                    <i class="fas fa-arrow-turn-down-right"></i>
                </div>
                <div class="point-checkbox">
                    <input type="checkbox" class="form-check-input point-select" id="selected_${fieldId}" data-field-id="${fieldId}">
                </div>
                <div class="point-content">
                    <div class="point-header">
                        <h6 class="point-title">
                            ${item.name || item.field_name || 'Unnamed Field'}
                        </h6>
                        ${isInactive ? '<span class="inactive-badge"><i class="fas fa-pause-circle"></i> Inactive</span>' : ''}
                    </div>
                    <div class="point-details">
                        <div class="detail-item">
                            <strong>Field Code:</strong> ${item.field_code || 'N/A'}
                        </div>
                        <div class="detail-item">
                            <strong>Configuration:</strong>
                            ${configStatus.text !== 'Not configured' ?
                                `<span class="text-success">${configStatus.text}</span>` :
                                '<span class="text-warning">Not configured</span>'
                            }
                        </div>
                        <div class="detail-item">
                            <strong>Entities:</strong>
                            ${assignmentStatus.text !== 'No entities assigned' ?
                                `<span class="text-success">${assignmentStatus.text}</span>` :
                                '<span class="text-muted">No entities assigned</span>'
                            }
                        </div>
                    </div>
                </div>
                <button class="remove-point-btn" data-field-id="${fieldId}" title="Remove dependency">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
    },

    /**
     * Check if a group is collapsed (stored in sessionStorage)
     */
    isGroupCollapsed(fieldId) {
        const collapseState = sessionStorage.getItem(`dependency-group-${fieldId}`);
        return collapseState === 'collapsed';
    },

    /**
     * Toggle collapse state for a computed field group
     */
    toggleDependencyGroup(fieldId) {
        const group = document.querySelector(`.computed-field-dependencies[data-parent-id="${fieldId}"]`);
        const toggleBtn = document.querySelector(`.dependency-toggle-btn[data-field-id="${fieldId}"]`);

        if (!group || !toggleBtn) return;

        const isCurrentlyCollapsed = group.classList.contains('collapsed');

        if (isCurrentlyCollapsed) {
            // Expand
            group.classList.remove('collapsed');
            group.classList.add('expanded');
            toggleBtn.querySelector('i').className = 'fas fa-chevron-down';
            toggleBtn.setAttribute('aria-label', 'Collapse dependencies');
            sessionStorage.setItem(`dependency-group-${fieldId}`, 'expanded');
        } else {
            // Collapse
            group.classList.add('collapsed');
            group.classList.remove('expanded');
            toggleBtn.querySelector('i').className = 'fas fa-chevron-right';
            toggleBtn.setAttribute('aria-label', 'Expand dependencies');
            sessionStorage.setItem(`dependency-group-${fieldId}`, 'collapsed');
        }
    },

    /**
     * Setup event delegation for toggle buttons
     */
    setupDependencyToggleListeners() {
        const container = this.elements.selectedDataPointsList || this.elements.selectedPointsList;
        if (!container) return;

        // Remove existing listener if any
        if (this._toggleListener) {
            container.removeEventListener('click', this._toggleListener);
        }

        // Add new listener
        this._toggleListener = (e) => {
            const toggleBtn = e.target.closest('.dependency-toggle-btn');
            if (toggleBtn) {
                e.preventDefault();
                e.stopPropagation();
                const fieldId = toggleBtn.dataset.fieldId;
                this.toggleDependencyGroup(fieldId);
            }
        };

        container.addEventListener('click', this._toggleListener);
    },


    // Module health check
    isHealthy() {
        return this.isInitialized &&
               (this.elements.selectedDataPointsList || this.elements.selectedPointsList) !== null &&
               typeof AppEvents !== 'undefined';
    },

    isReady() {
        return this.isInitialized;
    }
};