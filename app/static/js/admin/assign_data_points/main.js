/**
 * Main module for Assign Data Points - Global Event System & State Management
 * Phase 1: Foundation
 */

// Global Event System
window.AppEvents = {
    listeners: {},

    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    },

    off(event, callback) {
        if (!this.listeners[event]) return;
        this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    },

    emit(event, data) {
        console.log(`[AppEvents] ${event}:`, data);
        if (!this.listeners[event]) return;
        this.listeners[event].forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`[AppEvents] Error in ${event} listener:`, error);
            }
        });
    }
};

// Global State Management
window.AppState = {
    selectedDataPoints: new Map(),
    configurations: new Map(),
    entityAssignments: new Map(),
    topicAssignments: new Map(), // BUG FIX: Add missing topicAssignments Map for material topic tracking
    currentView: 'topic-tree', // Default view
    previousView: null,
    currentFramework: null,

    // State mutation methods
    addSelectedDataPoint(dataPoint) {
        // Defensive validation to catch incorrect usage
        if (typeof dataPoint === 'string') {
            console.error('[AppState] ERROR: addSelectedDataPoint() requires an object, not a string:', dataPoint);
            console.error('[AppState] Stack trace for debugging:');
            console.trace();
            return;
        }

        // BUG FIX #1: Support both 'id' and 'field_id' properties for flexibility
        // Accept field_id as primary key, id as alias for backward compatibility
        const fieldKey = dataPoint.field_id || dataPoint.id;

        if (!dataPoint || !fieldKey) {
            console.error('[AppState] ERROR: addSelectedDataPoint() requires object with either id or field_id property:', dataPoint);
            console.trace();
            return;
        }

        // Normalize data point to always have both properties
        const normalizedDataPoint = {
            ...dataPoint,
            id: fieldKey,
            field_id: fieldKey
        };

        this.selectedDataPoints.set(fieldKey, normalizedDataPoint);
        AppEvents.emit('state-dataPoint-added', normalizedDataPoint);
        AppEvents.emit('state-selectedDataPoints-changed', this.selectedDataPoints);
    },

    removeSelectedDataPoint(dataPointId) {
        const dataPoint = this.selectedDataPoints.get(dataPointId);
        this.selectedDataPoints.delete(dataPointId);
        AppEvents.emit('state-dataPoint-removed', dataPoint);
        AppEvents.emit('state-selectedDataPoints-changed', this.selectedDataPoints);
    },

    setConfiguration(dataPointId, config) {
        this.configurations.set(dataPointId, config);
        AppEvents.emit('state-configuration-changed', {dataPointId, config});
    },

    // BUG FIX #2: Add missing getConfiguration() method
    getConfiguration(dataPointId) {
        return this.configurations.get(dataPointId);
    },

    setView(viewType) {
        console.log(`[AppState] Setting view to: ${viewType}`);
        this.previousView = this.currentView;
        this.currentView = viewType;
        AppEvents.emit('state-view-changed', { viewType, previousView: this.previousView });
    },

    getCurrentView() {
        return this.currentView;
    },

    getPreviousView() {
        return this.previousView;
    },

    setFramework(frameworkId, frameworkName) {
        console.log(`[AppState] Setting framework to: ${frameworkId} (${frameworkName || 'Unknown'})`);
        this.currentFramework = {
            id: frameworkId,
            name: frameworkName
        };
        AppEvents.emit('state-framework-changed', {
            frameworkId,
            frameworkName
        });
    },

    getFramework() {
        return this.currentFramework;
    },

    getSelectedCount() {
        return this.selectedDataPoints.size;
    },

    isSelected(dataPointId) {
        return this.selectedDataPoints.has(dataPointId);
    }
};

// FIX BUG #2: Register event handlers IMMEDIATELY (not in DOMContentLoaded)
// This ensures handlers are ready before any module tries to emit events
console.log('[AppMain] Registering global event handlers...');

// Listen for data point add requests from SelectDataPointsPanel OR legacy code
AppEvents.on('data-point-add-requested', (data) => {
    const { fieldId, field } = data;
    console.log('[AppMain] Data point add requested:', fieldId);

    // Try new modular code first (SelectDataPointsPanel)
    if (window.SelectDataPointsPanel && window.SelectDataPointsPanel.flatListData) {
        // Try multiple ID formats: id, field_id, or exact string match
        const dataPointItem = window.SelectDataPointsPanel.flatListData.find(
            item => item.dataPoint.id === fieldId ||
                    item.dataPoint.field_id === fieldId ||
                    String(item.dataPoint.id) === String(fieldId) ||
                    String(item.dataPoint.field_id) === String(fieldId)
        );

        if (dataPointItem) {
            // Pass the complete field object with all properties
            // Ensure 'id' property exists for AppState Map key
            const fieldData = {
                id: dataPointItem.dataPoint.field_id || dataPointItem.dataPoint.id || fieldId,
                field_id: dataPointItem.dataPoint.field_id || dataPointItem.dataPoint.id || fieldId,
                name: dataPointItem.dataPoint.field_name || dataPointItem.dataPoint.name,
                topic: dataPointItem.topic,
                path: dataPointItem.path,
                ...dataPointItem.dataPoint  // Spread all other properties
            };

            window.AppState.addSelectedDataPoint(fieldData);
            console.log('[AppMain] Data point added to selection (modular):', fieldData);
            return;
        } else {
            console.warn('[AppMain] Data point not found in flatListData for fieldId:', fieldId);
        }
    }

    // Fallback to legacy dataPointsManager if modular code not available
    if (window.dataPointsManager && typeof window.dataPointsManager.addDataPoint === 'function') {
        // Check if field object was provided in event (from legacy flat list)
        if (field) {
            console.log('[AppMain] Using legacy dataPointsManager.addDataPoint with field from event:', fieldId);
            window.dataPointsManager.addDataPoint(field);
            console.log('[AppMain] Data point added via legacy method:', fieldId);
        } else {
            console.warn('[AppMain] No field object provided in event, cannot add data point:', fieldId);
        }
    } else {
        console.warn('[AppMain] dataPointsManager not available');
    }
});

// Handle data point remove requests
AppEvents.on('data-point-remove-requested', (data) => {
    const { fieldId } = data;
    console.log('[AppMain] Data point remove requested:', fieldId);
    window.AppState.removeSelectedDataPoint(fieldId);
});

console.log('[AppMain] Event handlers registered:', {
    'data-point-add-requested': AppEvents.listeners['data-point-add-requested']?.length || 0,
    'data-point-remove-requested': AppEvents.listeners['data-point-remove-requested']?.length || 0
});

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[AppMain] Event system and state management initialized');

    // Initialize modules in sequence
    // NOTE: ServicesModule self-initializes via its own DOMContentLoaded listener
    // and does not expose an init() method, so we skip it here

    if (window.CoreUI && typeof window.CoreUI.init === 'function') {
        window.CoreUI.init();
        console.log('[AppMain] CoreUI initialized');
    } else {
        console.warn('[AppMain] CoreUI not available or missing init method');
    }

    if (window.SelectDataPointsPanel && typeof window.SelectDataPointsPanel.init === 'function') {
        window.SelectDataPointsPanel.init();
        console.log('[AppMain] SelectDataPointsPanel initialized');
    } else {
        console.warn('[AppMain] SelectDataPointsPanel not available or missing init method');
    }

    if (window.SelectedDataPointsPanel && typeof window.SelectedDataPointsPanel.init === 'function') {
        window.SelectedDataPointsPanel.init();
        console.log('[AppMain] SelectedDataPointsPanel initialized');
    } else {
        console.warn('[AppMain] SelectedDataPointsPanel not available or missing init method');
    }

    // Phase 6: Initialize PopupsModule
    if (window.PopupsModule && typeof window.PopupsModule.init === 'function') {
        window.PopupsModule.init();
        console.log('[AppMain] PopupsModule initialized');
    } else {
        console.warn('[AppMain] PopupsModule not loaded or missing init method');
    }

    // Phase 7: Initialize VersioningModule
    if (window.VersioningModule && typeof window.VersioningModule.init === 'function') {
        window.VersioningModule.init();
        console.log('[AppMain] VersioningModule initialized');
    } else {
        console.warn('[AppMain] VersioningModule not loaded or missing init method');
    }

    // Phase 8: Initialize DependencyManager for computed field auto-cascade
    if (window.DependencyManager && typeof window.DependencyManager.init === 'function') {
        window.DependencyManager.init().then(() => {
            console.log('[AppMain] DependencyManager initialized');

            // Phase 8.5: Initialize TooltipManager after DependencyManager is ready
            if (window.TooltipManager && typeof window.TooltipManager.init === 'function') {
                window.TooltipManager.init();
                console.log('[AppMain] TooltipManager initialized');
            } else {
                console.warn('[AppMain] TooltipManager not loaded or missing init method');
            }
        }).catch(error => {
            console.error('[AppMain] Failed to initialize DependencyManager:', error);
        });
    } else {
        console.warn('[AppMain] DependencyManager not loaded or missing init method');
    }

    // Phase 8: Initialize ImportExportModule
    if (window.ImportExportModule && typeof window.ImportExportModule.init === 'function') {
        window.ImportExportModule.init();
        console.log('[AppMain] ImportExportModule initialized');
    } else {
        console.warn('[AppMain] ImportExportModule not loaded or missing init method');
    }

    // Phase 8: Initialize HistoryModule
    if (window.HistoryModule && typeof window.HistoryModule.init === 'function') {
        window.HistoryModule.init();
        console.log('[AppMain] HistoryModule initialized');

        // Wire up History Tab activation event
        const historyTab = document.getElementById('assignment-history-tab');
        if (historyTab) {
            historyTab.addEventListener('shown.bs.tab', function(event) {
                console.log('[AppMain] History tab activated, loading assignment history');
                if (window.HistoryModule && typeof window.HistoryModule.loadAssignmentHistory === 'function') {
                    window.HistoryModule.loadAssignmentHistory();
                } else {
                    console.error('[AppMain] HistoryModule.loadAssignmentHistory not available');
                }
            });
            console.log('[AppMain] History tab event listener attached');
        } else {
            console.warn('[AppMain] History tab button not found in DOM');
        }
    } else {
        console.warn('[AppMain] HistoryModule not loaded or missing init method');
    }

    // Phase 9.5: Initialize DimensionModule for dimension configuration
    if (window.DimensionModule && typeof window.DimensionModule.init === 'function') {
        window.DimensionModule.init();
        console.log('[AppMain] DimensionModule initialized');
    } else {
        console.warn('[AppMain] DimensionModule not loaded or missing init method');
    }

    // FIX BUG #1 (P0 CRITICAL): Auto-load existing assignments on page initialization
    // This matches the legacy behavior where OLD page shows 17 existing assignments immediately
    // NEW page was showing empty state, making users think all data was lost
    console.log('[AppMain] Loading existing assignments on initialization...');
    loadExistingAssignments();

    // Listen for reload-configurations event (triggered after entity assignments)
    AppEvents.on('reload-configurations', () => {
        console.log('[AppMain] Reload configurations event received');
        reloadAssignmentConfigurations();
    });

    // Listen for reload-data-points event (triggered by Show Inactive toggle)
    AppEvents.on('reload-data-points-requested', (data) => {
        console.log('[AppMain] Reload data points event received:', data);
        reloadDataPoints(data.includeInactive);
    });

    AppEvents.emit('app-initialized');
    console.log('[AppMain] All modules initialized successfully');
});

/**
 * FIX BUG #1: Load existing assignments on page initialization
 * This function loads existing data point assignments from the server
 * and populates the selected data points panel, matching legacy behavior
 */
async function loadExistingAssignments() {
    try {
        console.log('[AppMain] Fetching existing data points and assignments...');

        // Use ServicesModule to load existing data points and assignments
        if (!window.ServicesModule || typeof window.ServicesModule.loadExistingDataPointsWithInactive !== 'function') {
            console.error('[AppMain] ServicesModule not available, cannot load existing assignments');
            return;
        }

        const { dataPoints, assignments } = await window.ServicesModule.loadExistingDataPointsWithInactive(false);

        console.log('[AppMain] Loaded existing data points:', dataPoints.length);
        console.log('[AppMain] Loaded assignments:', assignments.length);

        // Process each existing data point and add to AppState
        dataPoints.forEach(point => {
            // Ensure the data point has an 'id' property for AppState Map key
            const fieldData = {
                id: point.field_id || point.id,
                field_id: point.field_id || point.id,
                name: point.field_name || point.name,
                field_name: point.field_name || point.name,
                ...point  // Spread all other properties
            };

            // Add to global state (this will trigger SelectedDataPointsPanel update)
            window.AppState.addSelectedDataPoint(fieldData);
        });

        // Process assignments and configurations
        if (assignments && assignments.length > 0) {
            loadAssignmentConfigurations(assignments);
        }

        console.log('[AppMain] Existing assignments loaded successfully:', dataPoints.length, 'data points');

        // Phase 9.5: Load dimension badges for all loaded fields
        if (window.DimensionModule && typeof window.DimensionModule.loadDimensionsForFields === 'function') {
            const fieldIds = dataPoints.map(point => point.field_id || point.id);
            console.log('[AppMain] Loading dimensions for', fieldIds.length, 'fields');
            window.DimensionModule.loadDimensionsForFields(fieldIds);
        } else {
            console.warn('[AppMain] DimensionModule not available for loading dimension badges');
        }

    } catch (error) {
        console.error('[AppMain] Error loading existing assignments:', error);
        // Don't show error to user - page should still be usable even if loading fails
    }
}

/**
 * Reload assignment configurations from the server
 * This function is called after entity assignments are modified to refresh badge counts
 */
async function reloadAssignmentConfigurations() {
    try {
        console.log('[AppMain] Reloading assignment configurations...');

        // Fetch fresh assignments from server
        if (!window.ServicesModule || typeof window.ServicesModule.loadDataPointAssignments !== 'function') {
            console.error('[AppMain] ServicesModule not available, cannot reload configurations');
            return;
        }

        const assignments = await window.ServicesModule.loadDataPointAssignments();
        console.log('[AppMain] Reloaded assignments:', assignments.length);

        // Clear existing configurations and entity assignments
        window.AppState.entityAssignments.clear();
        window.AppState.configurations.clear();
        window.AppState.topicAssignments.clear();

        // Reload configurations into AppState
        if (assignments && assignments.length > 0) {
            loadAssignmentConfigurations(assignments);
        }

        // Trigger UI refresh
        window.AppEvents.emit('panel-refresh-requested');
        console.log('[AppMain] Assignment configurations reloaded successfully');

    } catch (error) {
        console.error('[AppMain] Error reloading assignment configurations:', error);
    }
}

/**
 * Reload data points from the server with optional inactive items
 * This function is called when the "Show Inactive" toggle is clicked
 * @param {boolean} includeInactive - Whether to include inactive assignments
 */
async function reloadDataPoints(includeInactive = false) {
    try {
        console.log(`[AppMain] Reloading data points (includeInactive: ${includeInactive})...`);

        // Use ServicesModule to load existing data points and assignments with include_inactive parameter
        if (!window.ServicesModule || typeof window.ServicesModule.loadExistingDataPointsWithInactive !== 'function') {
            console.error('[AppMain] ServicesModule not available, cannot reload data points');
            return;
        }

        const { dataPoints, assignments } = await window.ServicesModule.loadExistingDataPointsWithInactive(includeInactive);

        console.log('[AppMain] Reloaded data points:', dataPoints.length);
        console.log('[AppMain] Reloaded assignments:', assignments.length);

        // Clear existing state
        window.AppState.selectedDataPoints.clear();
        window.AppState.entityAssignments.clear();
        window.AppState.configurations.clear();
        window.AppState.topicAssignments.clear();

        // Process each data point and add to AppState
        dataPoints.forEach(point => {
            // Ensure the data point has an 'id' property for AppState Map key
            const fieldData = {
                id: point.field_id || point.id,
                field_id: point.field_id || point.id,
                name: point.field_name || point.name,
                field_name: point.field_name || point.name,
                is_active: point.is_active !== undefined ? point.is_active : true, // Mark inactive status
                ...point  // Spread all other properties
            };

            // Add to global state (this will trigger SelectedDataPointsPanel update)
            window.AppState.addSelectedDataPoint(fieldData);
        });

        // Process assignments and configurations
        if (assignments && assignments.length > 0) {
            loadAssignmentConfigurations(assignments);
        }

        // Emit reload complete event
        window.AppEvents.emit('data-points-reload-complete', {
            includeInactive,
            dataPointCount: dataPoints.length,
            assignmentCount: assignments.length
        });

        console.log('[AppMain] Data points reloaded successfully:', dataPoints.length, 'data points');

        // Phase 9.5: Load dimension badges for all reloaded fields
        if (window.DimensionModule && typeof window.DimensionModule.loadDimensionsForFields === 'function') {
            const fieldIds = dataPoints.map(point => point.field_id || point.id);
            console.log('[AppMain] Loading dimensions for', fieldIds.length, 'reloaded fields');
            window.DimensionModule.loadDimensionsForFields(fieldIds);
        } else {
            console.warn('[AppMain] DimensionModule not available for loading dimension badges');
        }

    } catch (error) {
        console.error('[AppMain] Error reloading data points:', error);
        // Emit error event so UI can handle it
        window.AppEvents.emit('data-points-reload-error', { error: error.message });
    }
}

/**
 * Load assignment configurations from assignments data
 * This populates entity assignments and configurations
 */
function loadAssignmentConfigurations(assignments) {
    // Group assignments by field_id
    const assignmentMap = {};
    assignments.forEach(assign => {
        const fieldId = assign.field_id.toString();
        if (!assignmentMap[fieldId]) {
            assignmentMap[fieldId] = [];
        }
        assignmentMap[fieldId].push(assign.entity_id.toString());
    });

    // Load configurations into AppState
    assignments.forEach(assign => {
        const fieldId = assign.field_id.toString();
        if (!window.AppState.configurations.has(fieldId)) {
            window.AppState.configurations.set(fieldId, {
                fy_start_month: assign.fy_start_month || 4,
                fy_start_year: assign.fy_start_year || new Date().getFullYear(),
                fy_end_year: assign.fy_end_year || (new Date().getFullYear() + 1),
                frequency: assign.frequency || 'Annual',
                unit: assign.unit || '',
                entities: assignmentMap[fieldId] || []
            });
        }
    });

    // Load entity assignments into AppState
    Object.keys(assignmentMap).forEach(fieldId => {
        if (!window.AppState.entityAssignments.has(fieldId)) {
            window.AppState.entityAssignments.set(fieldId, new Set(assignmentMap[fieldId]));
        }
    });

    // Load topic assignments into AppState
    // BUG FIX: Store both topic ID and name, pick first NON-NULL topic for each field
    const topicMap = {}; // { fieldId: { topicId, topicName } }
    assignments.forEach(assign => {
        const fieldId = assign.field_id.toString();

        // If this field doesn't have a topic yet, and this assignment has one, use it
        if (assign.assigned_topic_id && !topicMap[fieldId]) {
            topicMap[fieldId] = {
                topicId: assign.assigned_topic_id.toString(),
                topicName: assign.assigned_topic_name
            };
        }
    });

    // Store in AppState
    Object.keys(topicMap).forEach(fieldId => {
        window.AppState.topicAssignments.set(fieldId, topicMap[fieldId].topicId);

        // Also update the data point in selectedDataPoints to include assigned_topic_name
        if (window.AppState.selectedDataPoints.has(fieldId)) {
            const dataPoint = window.AppState.selectedDataPoints.get(fieldId);
            dataPoint.assigned_topic_name = topicMap[fieldId].topicName;
            dataPoint.assigned_topic_id = topicMap[fieldId].topicId;
        }
    });

    console.log('[AppMain] Configurations loaded for', assignments.length, 'assignments');
    console.log('[AppMain] Entity assignments:', window.AppState.entityAssignments.size, 'fields');
    console.log('[AppMain] Topic assignments:', window.AppState.topicAssignments.size, 'fields');

    // Trigger a refresh of the SelectedDataPointsPanel to update button states
    if (window.SelectedDataPointsPanel && window.SelectedDataPointsPanel.isInitialized) {
        console.log('[AppMain] Refreshing SelectedDataPointsPanel to update button states');
        window.SelectedDataPointsPanel.updateDisplay();
    }
}