/**
 * Dimension Management Module for Assign Data Points
 * Phase 2: Dimension Configuration Integration
 * Integrates shared dimension component with assign data points workflow
 */

window.DimensionModule = (function() {
    'use strict';

    let initialized = false;

    /**
     * Initialize dimension management
     */
    function init() {
        if (initialized) {
            console.warn('[DimensionModule] Already initialized');
            return;
        }

        console.log('[DimensionModule] Initializing dimension management for Assign Data Points...');

        // Initialize shared dimension component
        if (typeof window.DimensionManagerShared !== 'undefined') {
            window.DimensionManagerShared.init({
                context: 'assign-data-points',
                containerId: 'dimensionManagementModal',

                // Callback when dimension is assigned to a field
                onDimensionAssigned: function(fieldId, dimensionData) {
                    console.log('[DimensionModule] Dimension assigned:', fieldId, dimensionData);

                    // Refresh dimension badges for this field
                    refreshFieldDimensions(fieldId);

                    // Emit event for other modules to react
                    if (window.AppEvents) {
                        window.AppEvents.emit('dimension-assigned', { fieldId, dimensionData });
                    }
                },

                // Callback when dimension is removed from a field
                onDimensionRemoved: function(fieldId, dimensionId) {
                    console.log('[DimensionModule] Dimension removed:', fieldId, dimensionId);

                    // Refresh dimension badges for this field
                    refreshFieldDimensions(fieldId);

                    // Emit event for other modules to react
                    if (window.AppEvents) {
                        window.AppEvents.emit('dimension-removed', { fieldId, dimensionId });
                    }
                },

                // Callback when new dimension is created
                onDimensionCreated: function(dimensionData) {
                    console.log('[DimensionModule] New dimension created:', dimensionData);

                    // Emit event for other modules to react
                    if (window.AppEvents) {
                        window.AppEvents.emit('dimension-created', dimensionData);
                    }
                },

                // Callback when validation error occurs
                onValidationError: function(errorData) {
                    console.error('[DimensionModule] Validation error:', errorData);

                    // Show error notification using existing popup system
                    if (window.PopupManager) {
                        window.PopupManager.show({
                            type: 'error',
                            title: errorData.title || 'Validation Error',
                            message: errorData.message || 'Cannot perform this operation'
                        });
                    }
                }
            });

            console.log('[DimensionModule] Shared component initialized successfully');
        } else {
            console.error('[DimensionModule] DimensionManagerShared not found - dimension management unavailable');
            return;
        }

        // Setup event listeners for "Manage Dimensions" buttons
        setupEventListeners();

        initialized = true;
        console.log('[DimensionModule] Initialization complete');
    }

    /**
     * Setup event listeners for dimension management buttons
     */
    function setupEventListeners() {
        // Use event delegation for dynamically added fields
        document.addEventListener('click', function(e) {
            // Check if clicked element is a "Manage Dimensions" button
            const btn = e.target.closest('.manage-dimensions-btn');
            if (!btn) return;

            e.preventDefault();
            e.stopPropagation();

            const fieldId = btn.dataset.fieldId;
            const fieldName = btn.dataset.fieldName;

            console.log('[DimensionModule] Opening dimension modal for field:', fieldId, fieldName);

            // Open dimension modal using shared component
            if (window.DimensionManagerShared) {
                window.DimensionManagerShared.openDimensionModal(
                    fieldId,
                    fieldName,
                    'assign-data-points'
                );
            }
        });

        console.log('[DimensionModule] Event listeners attached for dimension buttons');
    }

    /**
     * Refresh dimension badges for a field
     */
    async function refreshFieldDimensions(fieldId) {
        try {
            console.log('[DimensionModule] Refreshing dimensions for field:', fieldId);

            // Fetch field dimensions from server
            const response = await fetch(`/admin/fields/${fieldId}/dimensions`);
            const data = await response.json();

            if (data.success && data.dimensions) {
                // Render dimension badges
                renderDimensionBadges(fieldId, data.dimensions);
                console.log('[DimensionModule] Dimension badges refreshed for field:', fieldId);
            } else {
                console.warn('[DimensionModule] No dimensions found for field:', fieldId);
            }
        } catch (error) {
            console.error('[DimensionModule] Error refreshing field dimensions:', error);
        }
    }

    /**
     * Render dimension badges for a field
     */
    function renderDimensionBadges(fieldId, dimensions) {
        const containerId = `field-badges-${fieldId}`;
        const container = document.getElementById(containerId);

        if (!container) {
            console.warn('[DimensionModule] Badge container not found:', containerId);
            return;
        }

        // Use shared DimensionBadge component to render badges
        if (window.DimensionBadge) {
            window.DimensionBadge.render(dimensions, containerId);

            // Initialize tooltips using shared DimensionTooltip component
            if (window.DimensionTooltip && dimensions.length > 0) {
                window.DimensionTooltip.initAll(container, dimensions);
            }

            console.log('[DimensionModule] Rendered', dimensions.length, 'dimension badges for field:', fieldId);
        } else {
            console.error('[DimensionModule] DimensionBadge component not available');
        }

        // Update manage dimensions button styling
        updateManageDimensionsButton(fieldId, dimensions.length > 0);
    }

    /**
     * Update manage dimensions button to show green when dimensions are assigned
     */
    function updateManageDimensionsButton(fieldId, hasDimensions) {
        const button = document.querySelector(`.manage-dimensions-btn[data-field-id="${fieldId}"]`);

        if (!button) {
            console.warn('[DimensionModule] Manage dimensions button not found for field:', fieldId);
            return;
        }

        if (hasDimensions) {
            button.classList.add('status-dimensions-assigned');
            console.log('[DimensionModule] Added status-dimensions-assigned class to button for field:', fieldId);
        } else {
            button.classList.remove('status-dimensions-assigned');
            console.log('[DimensionModule] Removed status-dimensions-assigned class from button for field:', fieldId);
        }
    }

    /**
     * Load dimensions for all selected fields
     */
    async function loadDimensionsForFields(fieldIds) {
        console.log('[DimensionModule] Loading dimensions for', fieldIds.length, 'fields');

        for (const fieldId of fieldIds) {
            await refreshFieldDimensions(fieldId);
        }

        console.log('[DimensionModule] All field dimensions loaded');
    }

    /**
     * Check if module is initialized
     */
    function isInitialized() {
        return initialized;
    }

    // Public API
    return {
        init: init,
        refreshFieldDimensions: refreshFieldDimensions,
        renderDimensionBadges: renderDimensionBadges,
        loadDimensionsForFields: loadDimensionsForFields,
        isInitialized: isInitialized
    };
})();
