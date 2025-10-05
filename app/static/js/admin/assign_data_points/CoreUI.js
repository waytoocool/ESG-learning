/**
 * CoreUI Module for Assign Data Points - Toolbar & Global Actions
 * Phase 3: Toolbar functionality extracted from legacy code
 */

window.CoreUI = {
    // State tracking
    selectedCount: 0,
    isInitialized: false,

    // DOM element references
    elements: {
        selectedCountDisplay: null,
        configureButton: null,
        assignButton: null,
        saveButton: null,
        exportButton: null,
        importButton: null,
        selectAllButton: null,
        deselectAllButton: null
    },

    // Initialization
    init() {
        console.log('[CoreUI] Initializing CoreUI module...');
        this.cacheElements();
        this.bindEvents();
        this.setupEventListeners();
        this.updateButtonStates();
        this.isInitialized = true;
        AppEvents.emit('core-ui-initialized');
        console.log('[CoreUI] CoreUI module initialized successfully');
    },

    // Element caching for performance
    cacheElements() {
        console.log('[CoreUI] Caching DOM elements...');
        this.elements.selectedCountDisplay = document.getElementById('selectedCount');
        this.elements.configureButton = document.getElementById('configureSelected');
        this.elements.assignButton = document.getElementById('assignEntities');
        this.elements.saveButton = document.getElementById('saveAllConfiguration');
        this.elements.exportButton = document.getElementById('exportAssignments');
        this.elements.importButton = document.getElementById('importAssignments');
        this.elements.selectAllButton = document.getElementById('selectAllVisible');
        this.elements.deselectAllButton = document.getElementById('deselectAllDataPoints');

        // Log which elements were found
        Object.entries(this.elements).forEach(([key, element]) => {
            if (element) {
                console.log(`[CoreUI] Found element: ${key}`);
            } else {
                console.warn(`[CoreUI] Element not found: ${key}`);
            }
        });
    },

    // Event binding
    bindEvents() {
        console.log('[CoreUI] Binding toolbar events...');

        // Configure Selected button
        if (this.elements.configureButton) {
            this.elements.configureButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleConfigureSelected();
            });
        }

        // Assign Entities button
        if (this.elements.assignButton) {
            this.elements.assignButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleAssignEntities();
            });
        }

        // Save All Configuration button
        if (this.elements.saveButton) {
            this.elements.saveButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleSaveAll();
            });
        }

        // Export Assignments button
        if (this.elements.exportButton) {
            this.elements.exportButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleExport();
            });
        }

        // Import Assignments button
        if (this.elements.importButton) {
            this.elements.importButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleImport();
            });
        }

        // Select All button
        if (this.elements.selectAllButton) {
            this.elements.selectAllButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleSelectAll();
            });
        }

        // Deselect All button
        if (this.elements.deselectAllButton) {
            this.elements.deselectAllButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleDeselectAll();
            });
        }

        console.log('[CoreUI] Toolbar events bound successfully');
    },

    // AppEvents listeners
    setupEventListeners() {
        console.log('[CoreUI] Setting up AppEvents listeners...');

        // Listen for state changes from AppState
        AppEvents.on('state-selectedDataPoints-changed', (selectedDataPoints) => {
            this.updateSelectedCount(selectedDataPoints.size);
        });

        AppEvents.on('state-dataPoint-added', (dataPoint) => {
            this.updateSelectedCount(AppState.getSelectedCount());
        });

        AppEvents.on('state-dataPoint-removed', (dataPoint) => {
            this.updateSelectedCount(AppState.getSelectedCount());
        });

        // Listen for configuration and assignment completion
        AppEvents.on('configuration-saved', (data) => {
            console.log('[CoreUI] Configuration saved:', data);
            this.showMessage('Configuration saved successfully', 'success');
        });

        AppEvents.on('entities-assigned', (data) => {
            console.log('[CoreUI] Entities assigned:', data);
            this.showMessage('Entities assigned successfully', 'success');
        });

        console.log('[CoreUI] AppEvents listeners set up');
    },

    // Button state management
    updateButtonStates() {
        const hasSelection = this.selectedCount > 0;

        // Enable/disable buttons based on selection
        if (this.elements.configureButton) {
            this.elements.configureButton.disabled = !hasSelection;
        }
        if (this.elements.assignButton) {
            this.elements.assignButton.disabled = !hasSelection;
        }
        if (this.elements.saveButton) {
            this.elements.saveButton.disabled = !hasSelection;
        }

        // Export is always enabled (can export all)
        // Import is always enabled

        AppEvents.emit('toolbar-buttons-updated', { hasSelection, selectedCount: this.selectedCount });
    },

    // Count display updates
    updateSelectedCount(count) {
        this.selectedCount = count;

        if (this.elements.selectedCountDisplay) {
            this.elements.selectedCountDisplay.textContent = count;
        }

        this.updateButtonStates();
        AppEvents.emit('toolbar-count-updated', count);

        console.log(`[CoreUI] Selected count updated to: ${count}`);
    },

    // Toolbar action handlers
    handleConfigureSelected() {
        console.log('[CoreUI] Configure Selected clicked');

        // Get only the CHECKED items from the right panel
        const checkedItems = this.getCheckedItems();

        if (checkedItems.length === 0) {
            this.showMessage('Please select data points to configure', 'warning');
            return;
        }

        // Emit event for other modules to handle
        AppEvents.emit('toolbar-configure-clicked', {
            selectedCount: checkedItems.length,
            selectedPoints: checkedItems
        });
    },

    handleAssignEntities() {
        console.log('[CoreUI] Assign Entities clicked');

        // Get only the CHECKED items from the right panel
        const checkedItems = this.getCheckedItems();

        if (checkedItems.length === 0) {
            this.showMessage('Please select data points to assign', 'warning');
            return;
        }

        // Emit event for other modules to handle
        AppEvents.emit('toolbar-assign-clicked', {
            selectedCount: checkedItems.length,
            selectedPoints: checkedItems
        });
    },

    handleSaveAll() {
        console.log('[CoreUI] Save All Configuration clicked');

        if (this.selectedCount === 0) {
            this.showMessage('No data points selected to save', 'warning');
            return;
        }

        // Validate configurations before saving
        const selectedPoints = Array.from(AppState.selectedDataPoints.values());
        const configurationsToSave = [];

        for (const point of selectedPoints) {
            const config = AppState.configurations.get(point.field_id);
            if (config && Object.keys(config).length > 0) {
                configurationsToSave.push({ fieldId: point.field_id, config });
            }
        }

        if (configurationsToSave.length === 0) {
            this.showMessage('No configurations to save. Please configure the selected data points first.', 'warning');
            return;
        }

        AppEvents.emit('toolbar-save-clicked', {
            selectedCount: this.selectedCount,
            configurationsToSave
        });
    },

    async handleExport() {
        console.log('[CoreUI] Export Assignments clicked');

        try {
            // Emit event for ImportExportModule to handle
            AppEvents.emit('toolbar-export-clicked', {
                selectedCount: this.selectedCount
            });

            // ImportExportModule listens for this event and handles the export
            // No need to call legacy functions directly
        } catch (error) {
            console.error('[CoreUI] Export error:', error);
            this.showMessage('Error during export: ' + error.message, 'error');
        }
    },

    handleImport() {
        console.log('[CoreUI] Import Assignments clicked');

        try {
            // Emit event for ImportExportModule to handle
            AppEvents.emit('toolbar-import-clicked');

            // ImportExportModule listens for this event and handles the import
            // No need to call legacy functions directly
        } catch (error) {
            console.error('[CoreUI] Import error:', error);
            this.showMessage('Error during import: ' + error.message, 'error');
        }
    },

    handleSelectAll() {
        console.log('[CoreUI] Select All clicked');

        AppEvents.emit('toolbar-select-all-clicked');

        // For now, delegate to the legacy select all function if available
        if (window.dataPointsManager && window.dataPointsManager.selectAllVisible) {
            window.dataPointsManager.selectAllVisible();
        } else {
            console.warn('[CoreUI] Select All function not available in legacy manager');
        }
    },

    handleDeselectAll() {
        console.log('[CoreUI] Deselect All clicked');

        AppEvents.emit('toolbar-deselect-all-clicked');

        // For now, delegate to the legacy deselect function if available
        if (window.dataPointsManager && window.dataPointsManager.clearAllSelection) {
            window.dataPointsManager.clearAllSelection();
        } else {
            console.warn('[CoreUI] Deselect All function not available in legacy manager');
        }
    },

    // Utility methods
    getCheckedItems() {
        // Get only the checked checkboxes from the right panel
        const checkedCheckboxes = document.querySelectorAll('.selected-point-item .point-select:checked');
        const checkedItems = [];

        checkedCheckboxes.forEach(checkbox => {
            const fieldId = checkbox.dataset.fieldId;
            if (fieldId && window.AppState) {
                const item = AppState.selectedDataPoints.get(fieldId);
                if (item) {
                    checkedItems.push(item);
                }
            }
        });

        console.log(`[CoreUI] Found ${checkedItems.length} checked items out of ${AppState.selectedDataPoints.size} total items in panel`);
        return checkedItems;
    },

    showMessage(message, type = 'info') {
        console.log(`[CoreUI] ${type.toUpperCase()}: ${message}`);

        // Use ServicesModule if available, otherwise fallback
        if (window.ServicesModule && window.ServicesModule.showMessage) {
            ServicesModule.showMessage(message, type);
        } else {
            // Fallback message display
            AppEvents.emit('message-shown', { message, type });
        }
    },

    // Public API for external access
    getSelectedCount() {
        return this.selectedCount;
    },

    isReady() {
        return this.isInitialized;
    },

    // Manual trigger for updating count (for compatibility)
    triggerCountUpdate() {
        if (window.AppState) {
            this.updateSelectedCount(AppState.getSelectedCount());
        }
    }
};

// Initialize on DOM ready if AppEvents is available
document.addEventListener('DOMContentLoaded', function() {
    // Wait for AppEvents to be available before initializing
    if (typeof AppEvents !== 'undefined') {
        console.log('[CoreUI] DOM ready, AppEvents available, ready for manual initialization');
        AppEvents.emit('core-ui-ready');
    } else {
        console.warn('[CoreUI] DOM ready but AppEvents not available, will need manual initialization');
    }
});

// Export for global access
window.CoreUIModule = CoreUI;