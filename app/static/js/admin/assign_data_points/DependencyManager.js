/**
 * DependencyManager - Handles dependency tracking and cascade selection
 * Phase 2: Frontend dependency management for computed fields
 *
 * Features:
 * - Auto-cascade selection when computed fields are selected
 * - Deletion protection for dependency fields
 * - Dependency tree visualization
 * - Frequency compatibility validation
 */

window.DependencyManager = (function() {
    'use strict';

    // Private state
    const state = {
        dependencyMap: new Map(),        // computed_field_id -> [dependency_ids]
        reverseDependencyMap: new Map(), // raw_field_id -> [computed_field_ids]
        fieldMetadata: new Map(),        // field_id -> {is_computed, formula, etc}
        isInitialized: false
    };

    // Private methods
    async function loadDependencyData() {
        try {
            console.log('[DependencyManager] Loading dependency data...');

            // Load all computed fields and their dependencies
            const response = await fetch('/admin/api/assignments/dependency-tree');
            if (!response.ok) throw new Error('Failed to load dependency tree');

            const data = await response.json();

            // Build dependency maps
            if (data.dependency_tree && Array.isArray(data.dependency_tree)) {
                data.dependency_tree.forEach(computedField => {
                    processDependencyTree(computedField);
                });
            }

            console.log('[DependencyManager] Loaded dependencies for',
                       state.dependencyMap.size, 'computed fields');

            state.isInitialized = true;
            AppEvents.emit('dependencies-loaded', {
                computedFieldCount: state.dependencyMap.size
            });

        } catch (error) {
            console.error('[DependencyManager] Failed to load dependencies:', error);
            AppEvents.emit('dependencies-load-failed', {error: error.message});
        }
    }

    function processDependencyTree(node, parentId = null) {
        if (!node) return;

        const fieldId = node.field_id;

        // Store metadata
        state.fieldMetadata.set(fieldId, {
            field_name: node.field_name,
            is_computed: node.is_computed,
            formula: node.formula
        });

        if (node.is_computed && node.dependencies) {
            const depIds = [];

            node.dependencies.forEach(dep => {
                depIds.push(dep.field_id);

                // Build reverse map
                if (!state.reverseDependencyMap.has(dep.field_id)) {
                    state.reverseDependencyMap.set(dep.field_id, new Set());
                }
                state.reverseDependencyMap.get(dep.field_id).add(fieldId);

                // Store dependency metadata
                state.fieldMetadata.set(dep.field_id, {
                    field_name: dep.field_name,
                    is_computed: dep.is_computed,
                    formula: null
                });

                // Process nested dependencies
                if (dep.dependencies) {
                    processDependencyTree(dep, fieldId);
                }
            });

            state.dependencyMap.set(fieldId, depIds);
        }
    }

    async function checkRemovalImpact(fieldIds) {
        try {
            const response = await fetch('/admin/api/assignments/check-removal-impact', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({field_ids: fieldIds})
            });

            if (!response.ok) throw new Error('Failed to check removal impact');

            return await response.json();

        } catch (error) {
            console.error('[DependencyManager] Failed to check removal impact:', error);
            return {can_remove: false, error: error.message};
        }
    }

    // Public API
    return {
        /**
         * Initialize the dependency manager
         */
        async init() {
            console.log('[DependencyManager] Initializing...');

            // Load dependency data
            await loadDependencyData();

            // Set up event listeners
            this.bindEvents();

            console.log('[DependencyManager] Initialized successfully');
            AppEvents.emit('dependency-manager-initialized');
        },

        /**
         * Bind event listeners
         */
        bindEvents() {
            // Listen for field selection requests
            AppEvents.on('data-point-add-requested', (data) => {
                this.handleFieldSelection(data);
            });

            // Listen for field removal requests
            AppEvents.on('data-point-remove-requested', (data) => {
                this.handleFieldRemoval(data);
            });

            // Listen for framework changes
            AppEvents.on('state-framework-changed', () => {
                // Reload dependencies for new framework
                loadDependencyData();
            });
        },

        /**
         * Handle field selection with auto-cascade
         */
        async handleFieldSelection(data) {
            const {fieldId, field} = data;

            // Check if computed field
            const metadata = state.fieldMetadata.get(fieldId);
            if (!metadata || !metadata.is_computed) {
                return; // Not computed, no cascade needed
            }

            // Get dependencies
            const dependencies = state.dependencyMap.get(fieldId) || [];
            if (dependencies.length === 0) {
                return; // No dependencies
            }

            console.log(`[DependencyManager] Auto-adding ${dependencies.length} dependencies for ${fieldId}`);

            // Check which dependencies are already selected
            const existingSelections = new Set(
                Array.from(AppState.selectedDataPoints.keys())
            );

            const toAdd = [];
            const alreadySelected = [];

            dependencies.forEach(depId => {
                if (existingSelections.has(depId)) {
                    alreadySelected.push(depId);
                } else {
                    toAdd.push(depId);
                }
            });

            // Auto-add dependencies
            if (toAdd.length > 0) {
                // Get field data for dependencies
                const depFields = await this.fetchFieldData(toAdd);

                depFields.forEach(depField => {
                    // Add to selection without triggering cascade
                    AppState.addSelectedDataPoint(depField);
                });

                // Show notification
                this.showAutoAddNotification(metadata.field_name, toAdd.length, alreadySelected.length);
            } else if (alreadySelected.length > 0) {
                // All dependencies already selected
                this.showAlreadySelectedNotification(metadata.field_name, alreadySelected.length);
            }
        },

        /**
         * Handle field removal with protection
         */
        async handleFieldRemoval(data) {
            const {fieldId} = data;

            // Check if this field is a dependency
            const dependentFields = state.reverseDependencyMap.get(fieldId);
            if (!dependentFields || dependentFields.size === 0) {
                return; // Safe to remove
            }

            // Check if any dependent fields are selected
            const selectedDependents = [];
            dependentFields.forEach(depFieldId => {
                if (AppState.isSelected(depFieldId)) {
                    const metadata = state.fieldMetadata.get(depFieldId);
                    selectedDependents.push(metadata.field_name);
                }
            });

            if (selectedDependents.length > 0) {
                // Show warning modal
                const confirmed = await this.showRemovalWarning(
                    state.fieldMetadata.get(fieldId).field_name,
                    selectedDependents
                );

                if (!confirmed) {
                    // Cancel removal
                    AppEvents.emit('field-removal-cancelled', {fieldId});
                    return false;
                }
            }

            return true;
        },

        /**
         * Fetch field data for dependency fields from current framework
         */
        async fetchFieldData(fieldIds) {
            const dependencyFields = [];

            fieldIds.forEach(fieldId => {
                // Try multiple data sources in priority order
                let field = null;

                // 1. Try SelectDataPointsPanel.findDataPointById() - most comprehensive
                if (window.SelectDataPointsPanel && typeof window.SelectDataPointsPanel.findDataPointById === 'function') {
                    field = window.SelectDataPointsPanel.findDataPointById(fieldId);
                    if (field) {
                        // Normalize the field data
                        dependencyFields.push({
                            id: field.field_id || field.id || fieldId,
                            field_id: field.field_id || field.id || fieldId,
                            field_name: field.field_name || field.name,
                            name: field.field_name || field.name,
                            unit: field.unit || field.default_unit,
                            is_computed: field.is_computed || false,
                            topic: field.topic,
                            path: field.path,
                            ...field
                        });
                        return; // Found, continue to next fieldId
                    }
                }

                // 2. Fallback to fieldMetadata from dependency tree
                const metadata = state.fieldMetadata.get(fieldId);
                if (metadata) {
                    dependencyFields.push({
                        field_id: fieldId,
                        id: fieldId,
                        field_name: metadata.field_name,
                        name: metadata.field_name,
                        is_computed: metadata.is_computed || false
                    });
                } else {
                    console.warn('[DependencyManager] Could not find field data for dependency:', fieldId);
                }
            });

            return dependencyFields;
        },

        /**
         * Show auto-add notification
         */
        showAutoAddNotification(fieldName, addedCount, alreadySelectedCount) {
            const message = `Added '${fieldName}' and ${addedCount} dependencies`;

            if (window.PopupManager && window.PopupManager.showPopup) {
                PopupManager.showPopup('Dependencies Auto-Added', message, 'success', 4000);
            } else {
                console.log('[DependencyManager]', message);
            }

            AppEvents.emit('dependencies-auto-added', {
                computed_field: fieldName,
                added_count: addedCount,
                already_selected: alreadySelectedCount
            });
        },

        /**
         * Show already selected notification
         */
        showAlreadySelectedNotification(fieldName, count) {
            const message = `'${fieldName}' dependencies (${count}) already selected`;

            if (window.PopupManager) {
                PopupManager.showNotification(message, 'info', 3000);
            }
        },

        /**
         * Show removal warning modal
         */
        async showRemovalWarning(fieldName, dependentFields) {
            const message = `
                <div class="removal-warning">
                    <h4>Cannot Remove Dependency</h4>
                    <p>'${fieldName}' is required by these computed fields:</p>
                    <ul>
                        ${dependentFields.map(f => `<li>${f}</li>`).join('')}
                    </ul>
                    <p>Remove anyway? (Computed fields will be removed too)</p>
                </div>
            `;

            // Use PopupManager if available
            if (window.PopupManager && window.PopupManager.showConfirmDialog) {
                return await PopupManager.showConfirmDialog(message);
            }

            // Fallback to confirm
            return confirm(`'${fieldName}' is required by ${dependentFields.length} computed fields. Remove anyway?`);
        },

        /**
         * Check if field is computed
         */
        isComputedField(fieldId) {
            const metadata = state.fieldMetadata.get(fieldId);
            return metadata && metadata.is_computed;
        },

        /**
         * Get dependencies for a field
         */
        getDependencies(fieldId) {
            return state.dependencyMap.get(fieldId) || [];
        },

        /**
         * Get fields that depend on this field
         */
        getDependentFields(fieldId) {
            return Array.from(state.reverseDependencyMap.get(fieldId) || []);
        },

        /**
         * Validate frequency compatibility
         */
        async validateFrequencyCompatibility(assignments) {
            try {
                const response = await fetch('/admin/api/assignments/validate-dependencies', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({assignments})
                });

                if (!response.ok) throw new Error('Validation failed');

                return await response.json();

            } catch (error) {
                console.error('[DependencyManager] Validation error:', error);
                return {is_valid: false, error: error.message};
            }
        },

        /**
         * Get dependency tree for visualization
         */
        getDependencyTree() {
            const tree = [];

            state.dependencyMap.forEach((deps, fieldId) => {
                const metadata = state.fieldMetadata.get(fieldId);
                if (metadata && metadata.is_computed) {
                    tree.push({
                        field_id: fieldId,
                        field_name: metadata.field_name,
                        formula: metadata.formula,
                        dependencies: deps.map(depId => ({
                            field_id: depId,
                            field_name: state.fieldMetadata.get(depId)?.field_name || 'Unknown'
                        }))
                    });
                }
            });

            return tree;
        },

        /**
         * Get field metadata
         */
        getFieldMetadata(fieldId) {
            return state.fieldMetadata.get(fieldId);
        },

        /**
         * Check if initialized
         */
        isReady() {
            return state.isInitialized;
        },

        /**
         * Get dependency map (for SelectedDataPointsPanel integration)
         * Returns: Map<computedFieldId, [dependencyFieldIds]>
         */
        getDependencyMap() {
            return new Map(state.dependencyMap);
        },

        /**
         * Get reverse dependency map (for SelectedDataPointsPanel integration)
         * Returns: Map<rawFieldId, [computedFieldIds that depend on it]>
         */
        getReverseDependencyMap() {
            return new Map(state.reverseDependencyMap);
        },

        /**
         * Get all field metadata (for SelectedDataPointsPanel integration)
         * Returns: Map<fieldId, {is_computed, formula, field_name, etc}>
         */
        getAllFieldMetadata() {
            return new Map(state.fieldMetadata);
        }
    };
})();
