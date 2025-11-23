# Detailed Implementation Plan

**Feature:** Computed Field Dependency Auto-Management
**Version:** 1.0.0
**Last Updated:** 2025-11-10

## 🎯 Implementation Overview

This document provides the detailed technical implementation plan for the computed field dependency auto-management feature. Each component is broken down with specific code changes, file locations, and implementation notes.

---

## 📂 File Structure & Changes

```
app/
├── models/
│   └── framework.py [MODIFY]
├── routes/
│   └── admin_assignments_api.py [MODIFY]
├── services/
│   └── dependency_service.py [CREATE]
├── static/js/admin/assign_data_points/
│   ├── main.js [MODIFY]
│   ├── SelectDataPointsPanel.js [MODIFY]
│   ├── SelectedDataPointsPanel.js [MODIFY]
│   ├── PopupsModule.js [MODIFY]
│   ├── DependencyTreeView.js [CREATE]
│   └── DependencyManager.js [CREATE]
└── templates/admin/
    └── assign_data_points.html [MODIFY]
```

---

## 🔧 Phase 1: Backend Foundation

### 1.1 Model Enhancements
**File:** `app/models/framework.py`

```python
# Add to FrameworkDataField class (line ~286)

def get_all_dependencies(self, visited=None):
    """
    Get all raw field dependencies recursively.
    Returns flat list of all dependency field objects.
    """
    if not self.is_computed:
        return []

    if visited is None:
        visited = set()

    if self.field_id in visited:
        return []  # Circular dependency protection

    visited.add(self.field_id)
    dependencies = []

    for mapping in self.variable_mappings:
        raw_field = mapping.raw_field
        dependencies.append(raw_field)

        # Recursively get dependencies if raw field is also computed
        if raw_field.is_computed:
            dependencies.extend(raw_field.get_all_dependencies(visited))

    return dependencies

def get_dependency_tree(self):
    """
    Get hierarchical dependency structure.
    Returns nested dictionary representing dependency tree.
    """
    if not self.is_computed:
        return None

    tree = {
        'field_id': self.field_id,
        'field_name': self.field_name,
        'is_computed': True,
        'formula': self.formula_expression,
        'dependencies': []
    }

    for mapping in self.variable_mappings:
        dep_info = {
            'variable': mapping.variable_name,
            'coefficient': mapping.coefficient,
            'field_id': mapping.raw_field_id,
            'field_name': mapping.raw_field.field_name,
            'is_computed': mapping.raw_field.is_computed
        }

        if mapping.raw_field.is_computed:
            dep_info['dependencies'] = mapping.raw_field.get_dependency_tree()

        tree['dependencies'].append(dep_info)

    return tree

def validate_frequency_compatibility(self, proposed_frequency):
    """
    Check if proposed frequency is compatible with all dependencies.
    Returns (is_valid, incompatible_fields).
    """
    if not self.is_computed:
        return (True, [])

    freq_hierarchy = {
        'Annual': 1,
        'Quarterly': 2,
        'Monthly': 3
    }

    proposed_level = freq_hierarchy.get(proposed_frequency, 1)
    incompatible = []

    for dep in self.get_all_dependencies():
        # Check if dependency has existing assignment
        from ..models.data_assignment import DataPointAssignment
        assignments = DataPointAssignment.query.filter_by(
            field_id=dep.field_id,
            series_status='active'
        ).all()

        for assignment in assignments:
            dep_level = freq_hierarchy.get(assignment.frequency, 3)
            if dep_level < proposed_level:
                incompatible.append({
                    'field': dep.field_name,
                    'current_frequency': assignment.frequency,
                    'required_frequency': proposed_frequency
                })

    return (len(incompatible) == 0, incompatible)

def get_fields_depending_on_this(self):
    """
    Get all computed fields that depend on this field.
    Returns list of computed fields using this as dependency.
    """
    from . import FieldVariableMapping

    dependent_mappings = FieldVariableMapping.query.filter_by(
        raw_field_id=self.field_id
    ).all()

    dependent_fields = []
    for mapping in dependent_mappings:
        if mapping.computed_field and mapping.computed_field.is_computed:
            dependent_fields.append(mapping.computed_field)

    return dependent_fields

def can_be_removed(self):
    """
    Check if this field can be safely removed from assignments.
    Returns (can_remove, blocking_computed_fields).
    """
    dependents = self.get_fields_depending_on_this()

    # Check if any dependent computed fields are assigned
    from ..models.data_assignment import DataPointAssignment
    blocking_fields = []

    for computed_field in dependents:
        assignments = DataPointAssignment.query.filter_by(
            field_id=computed_field.field_id,
            series_status='active'
        ).count()

        if assignments > 0:
            blocking_fields.append({
                'field_id': computed_field.field_id,
                'field_name': computed_field.field_name,
                'assignment_count': assignments
            })

    return (len(blocking_fields) == 0, blocking_fields)
```

### 1.2 Dependency Service
**File:** `app/services/dependency_service.py` [CREATE NEW]

```python
"""
Service for managing computed field dependencies.
Handles auto-cascade, validation, and conflict resolution.
"""

from flask import current_app
from sqlalchemy import and_, or_
from ..models.framework import FrameworkDataField, FieldVariableMapping
from ..models.data_assignment import DataPointAssignment
from ..models.entity import Entity
from ..extensions import db
from ..middleware.tenant import get_current_tenant
from typing import List, Dict, Set, Tuple, Optional


class DependencyService:
    """Service for managing field dependencies and cascading operations."""

    @staticmethod
    def get_dependencies_for_fields(field_ids: List[str]) -> Dict[str, List[str]]:
        """
        Get all dependencies for a list of fields.

        Args:
            field_ids: List of field IDs to get dependencies for

        Returns:
            Dictionary mapping field_id to list of dependency field_ids
        """
        dependency_map = {}

        for field_id in field_ids:
            field = FrameworkDataField.query.get(field_id)
            if field and field.is_computed:
                deps = field.get_all_dependencies()
                dependency_map[field_id] = [d.field_id for d in deps]
            else:
                dependency_map[field_id] = []

        return dependency_map

    @staticmethod
    def get_auto_include_fields(selected_fields: List[str],
                               existing_selections: Set[str] = None) -> Dict:
        """
        Determine which fields should be auto-included based on selections.

        Args:
            selected_fields: Fields explicitly selected by user
            existing_selections: Fields already in selection (optional)

        Returns:
            {
                'auto_include': [field_ids to auto-add],
                'already_selected': [dependency fields already selected],
                'notifications': [messages to show user]
            }
        """
        if existing_selections is None:
            existing_selections = set()

        auto_include = set()
        already_selected = set()
        notifications = []

        for field_id in selected_fields:
            field = FrameworkDataField.query.get(field_id)
            if not field or not field.is_computed:
                continue

            dependencies = field.get_all_dependencies()
            dep_count = len(dependencies)

            if dep_count > 0:
                newly_added = []
                already_present = []

                for dep in dependencies:
                    if dep.field_id in existing_selections:
                        already_selected.add(dep.field_id)
                        already_present.append(dep.field_name)
                    else:
                        auto_include.add(dep.field_id)
                        newly_added.append(dep.field_name)

                # Create notification message
                if newly_added:
                    notifications.append(
                        f"Added '{field.field_name}' and {len(newly_added)} "
                        f"dependencies: {', '.join(newly_added[:3])}"
                        f"{'...' if len(newly_added) > 3 else ''}"
                    )

                if already_present:
                    notifications.append(
                        f"'{field.field_name}' dependencies already selected: "
                        f"{', '.join(already_present[:2])}"
                        f"{'...' if len(already_present) > 2 else ''}"
                    )

        return {
            'auto_include': list(auto_include),
            'already_selected': list(already_selected),
            'notifications': notifications,
            'total_added': len(auto_include)
        }

    @staticmethod
    def validate_frequency_compatibility(assignments: List[Dict]) -> Dict:
        """
        Validate frequency compatibility for assignments.

        Args:
            assignments: List of assignment configurations
                [{field_id, frequency, entity_id}, ...]

        Returns:
            {
                'is_valid': bool,
                'conflicts': [conflict details],
                'warnings': [warning messages]
            }
        """
        freq_hierarchy = {
            'Annual': 1,
            'Quarterly': 2,
            'Monthly': 3
        }

        conflicts = []
        warnings = []
        field_freq_map = {}

        # Build frequency map
        for assignment in assignments:
            field_id = assignment['field_id']
            frequency = assignment['frequency']
            field_freq_map[field_id] = frequency

        # Check each computed field
        for assignment in assignments:
            field = FrameworkDataField.query.get(assignment['field_id'])
            if not field or not field.is_computed:
                continue

            computed_freq = assignment['frequency']
            computed_level = freq_hierarchy.get(computed_freq, 1)

            for dep in field.get_all_dependencies():
                dep_freq = field_freq_map.get(dep.field_id)
                if not dep_freq:
                    continue

                dep_level = freq_hierarchy.get(dep_freq, 3)

                if dep_level < computed_level:
                    conflicts.append({
                        'computed_field': field.field_name,
                        'computed_frequency': computed_freq,
                        'dependency_field': dep.field_name,
                        'dependency_frequency': dep_freq,
                        'message': f"'{dep.field_name}' has {dep_freq} frequency "
                                  f"but '{field.field_name}' needs {computed_freq} or lower"
                    })

        return {
            'is_valid': len(conflicts) == 0,
            'conflicts': conflicts,
            'warnings': warnings
        }

    @staticmethod
    def check_removal_impact(field_ids: List[str]) -> Dict:
        """
        Check impact of removing fields from assignments.

        Args:
            field_ids: Fields to be removed

        Returns:
            {
                'can_remove': bool,
                'blocking_fields': [fields that would break],
                'affected_computed_fields': [computed fields affected]
            }
        """
        tenant = get_current_tenant()
        if not tenant:
            return {'can_remove': False, 'error': 'No tenant context'}

        blocking_fields = []
        affected_computed = []

        for field_id in field_ids:
            field = FrameworkDataField.query.get(field_id)
            if not field:
                continue

            # Get computed fields depending on this
            dependents = field.get_fields_depending_on_this()

            for computed_field in dependents:
                # Check if computed field is assigned
                assignments = DataPointAssignment.query.filter_by(
                    field_id=computed_field.field_id,
                    company_id=tenant.id,
                    series_status='active'
                ).count()

                if assignments > 0:
                    blocking_fields.append({
                        'removed_field': field.field_name,
                        'blocked_by': computed_field.field_name,
                        'assignment_count': assignments
                    })

                    affected_computed.append({
                        'field_id': computed_field.field_id,
                        'field_name': computed_field.field_name
                    })

        return {
            'can_remove': len(blocking_fields) == 0,
            'blocking_fields': blocking_fields,
            'affected_computed_fields': affected_computed,
            'message': f"Cannot remove: Required by {len(affected_computed)} computed fields"
                      if blocking_fields else "Safe to remove"
        }

    @staticmethod
    def get_entity_assignment_cascade(computed_field_id: str,
                                     assigned_entities: List[int]) -> Dict:
        """
        Determine entity assignments for dependencies.

        Args:
            computed_field_id: The computed field being assigned
            assigned_entities: Entities assigned to computed field

        Returns:
            {
                'dependency_assignments': {dep_field_id: [entity_ids]},
                'existing_assignments': {dep_field_id: [existing_entity_ids]}
            }
        """
        tenant = get_current_tenant()
        if not tenant:
            return {'error': 'No tenant context'}

        field = FrameworkDataField.query.get(computed_field_id)
        if not field or not field.is_computed:
            return {'dependency_assignments': {}, 'existing_assignments': {}}

        dependency_assignments = {}
        existing_assignments = {}

        for dep in field.get_all_dependencies():
            # Start with computed field's entities
            dep_entities = set(assigned_entities)

            # Check existing assignments for this dependency
            existing = DataPointAssignment.query.filter_by(
                field_id=dep.field_id,
                company_id=tenant.id,
                series_status='active'
            ).all()

            existing_entity_ids = [a.entity_id for a in existing]

            if existing_entity_ids:
                existing_assignments[dep.field_id] = existing_entity_ids
                # Merge with existing entities (union)
                dep_entities.update(existing_entity_ids)

            dependency_assignments[dep.field_id] = list(dep_entities)

        return {
            'dependency_assignments': dependency_assignments,
            'existing_assignments': existing_assignments
        }

    @staticmethod
    def validate_complete_assignment_set(assignments: List[Dict]) -> Dict:
        """
        Validate that all computed fields have their dependencies.

        Args:
            assignments: Complete list of assignments to validate

        Returns:
            {
                'is_complete': bool,
                'missing_dependencies': {computed_field_id: [missing_dep_ids]},
                'orphaned_computed_fields': [computed fields without deps]
            }
        """
        field_ids_in_assignment = set(a['field_id'] for a in assignments)
        missing_dependencies = {}
        orphaned_computed_fields = []

        for assignment in assignments:
            field = FrameworkDataField.query.get(assignment['field_id'])
            if not field or not field.is_computed:
                continue

            required_deps = [d.field_id for d in field.get_all_dependencies()]
            missing = [dep_id for dep_id in required_deps
                      if dep_id not in field_ids_in_assignment]

            if missing:
                missing_dependencies[field.field_id] = missing
                orphaned_computed_fields.append({
                    'field_id': field.field_id,
                    'field_name': field.field_name,
                    'missing_count': len(missing)
                })

        return {
            'is_complete': len(missing_dependencies) == 0,
            'missing_dependencies': missing_dependencies,
            'orphaned_computed_fields': orphaned_computed_fields
        }


# Export service instance
dependency_service = DependencyService()
```

### 1.3 API Endpoints
**File:** `app/routes/admin_assignments_api.py` (Add at line ~1665)

```python
# ============================================================================
# DEPENDENCY MANAGEMENT API ENDPOINTS
# ============================================================================

@assignment_api_bp.route('/validate-dependencies', methods=['POST'])
@login_required
@admin_or_super_admin_required
@tenant_required
def validate_dependencies():
    """
    Validate that all computed fields have required dependencies.

    Expected payload:
    {
        "assignments": [
            {"field_id": "xxx", "frequency": "Monthly", "entity_id": 1}
        ]
    }

    Returns:
    {
        "is_valid": true/false,
        "missing_dependencies": {},
        "frequency_conflicts": [],
        "warnings": []
    }
    """
    try:
        from ..services.dependency_service import dependency_service

        data = request.get_json()
        assignments = data.get('assignments', [])

        # Validate completeness
        completeness = dependency_service.validate_complete_assignment_set(assignments)

        # Validate frequency compatibility
        frequency_check = dependency_service.validate_frequency_compatibility(assignments)

        return jsonify({
            'is_valid': completeness['is_complete'] and frequency_check['is_valid'],
            'missing_dependencies': completeness['missing_dependencies'],
            'orphaned_computed_fields': completeness['orphaned_computed_fields'],
            'frequency_conflicts': frequency_check['conflicts'],
            'warnings': frequency_check['warnings']
        })

    except Exception as e:
        current_app.logger.error(f'Error validating dependencies: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Validation failed: {str(e)}'
        }), 500


@assignment_api_bp.route('/get-dependencies/<field_id>', methods=['GET'])
@login_required
@admin_or_super_admin_required
def get_field_dependencies(field_id):
    """
    Get all dependencies for a specific field.

    Returns:
    {
        "field_id": "xxx",
        "is_computed": true,
        "dependencies": [field objects],
        "dependency_tree": {nested structure}
    }
    """
    try:
        field = FrameworkDataField.query.get(field_id)
        if not field:
            return jsonify({'error': 'Field not found'}), 404

        if not field.is_computed:
            return jsonify({
                'field_id': field_id,
                'is_computed': False,
                'dependencies': [],
                'dependency_tree': None
            })

        dependencies = field.get_all_dependencies()
        dependency_tree = field.get_dependency_tree()

        return jsonify({
            'field_id': field_id,
            'field_name': field.field_name,
            'is_computed': True,
            'formula': field.formula_expression,
            'dependencies': [
                {
                    'field_id': dep.field_id,
                    'field_name': dep.field_name,
                    'is_computed': dep.is_computed
                } for dep in dependencies
            ],
            'dependency_tree': dependency_tree
        })

    except Exception as e:
        current_app.logger.error(f'Error getting dependencies for field {field_id}: {str(e)}')
        return jsonify({'error': f'Failed to get dependencies: {str(e)}'}), 500


@assignment_api_bp.route('/check-removal-impact', methods=['POST'])
@login_required
@admin_or_super_admin_required
@tenant_required
def check_removal_impact():
    """
    Check impact of removing fields from assignments.

    Expected payload:
    {
        "field_ids": ["field_id1", "field_id2"]
    }

    Returns:
    {
        "can_remove": true/false,
        "blocking_fields": [],
        "affected_computed_fields": []
    }
    """
    try:
        from ..services.dependency_service import dependency_service

        data = request.get_json()
        field_ids = data.get('field_ids', [])

        if not field_ids:
            return jsonify({'error': 'No field IDs provided'}), 400

        impact = dependency_service.check_removal_impact(field_ids)

        return jsonify(impact)

    except Exception as e:
        current_app.logger.error(f'Error checking removal impact: {str(e)}')
        return jsonify({'error': f'Failed to check impact: {str(e)}'}), 500


@assignment_api_bp.route('/auto-include-dependencies', methods=['POST'])
@login_required
@admin_or_super_admin_required
def auto_include_dependencies():
    """
    Get fields that should be auto-included based on selections.

    Expected payload:
    {
        "selected_fields": ["field_id1", "field_id2"],
        "existing_selections": ["field_id3", "field_id4"]
    }

    Returns:
    {
        "auto_include": [field_ids],
        "notifications": [messages],
        "total_added": count
    }
    """
    try:
        from ..services.dependency_service import dependency_service

        data = request.get_json()
        selected_fields = data.get('selected_fields', [])
        existing_selections = set(data.get('existing_selections', []))

        result = dependency_service.get_auto_include_fields(
            selected_fields, existing_selections
        )

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f'Error getting auto-include fields: {str(e)}')
        return jsonify({'error': f'Failed to get dependencies: {str(e)}'}), 500


@assignment_api_bp.route('/dependency-tree', methods=['GET'])
@login_required
@admin_or_super_admin_required
def get_dependency_tree():
    """
    Get complete dependency tree for all computed fields.

    Query params:
    - framework_id: Filter by framework (optional)

    Returns hierarchical structure of all dependencies.
    """
    try:
        framework_id = request.args.get('framework_id')

        query = FrameworkDataField.query.filter_by(is_computed=True)
        if framework_id:
            query = query.filter_by(framework_id=framework_id)

        computed_fields = query.all()

        tree = []
        for field in computed_fields:
            tree.append(field.get_dependency_tree())

        return jsonify({
            'success': True,
            'dependency_tree': tree,
            'total_computed_fields': len(tree)
        })

    except Exception as e:
        current_app.logger.error(f'Error getting dependency tree: {str(e)}')
        return jsonify({'error': f'Failed to get tree: {str(e)}'}), 500
```

---

## 🎨 Phase 2: Frontend Auto-Selection

### 2.1 Dependency Manager Module
**File:** `app/static/js/admin/assign_data_points/DependencyManager.js` [CREATE NEW]

```javascript
/**
 * DependencyManager - Handles dependency tracking and cascade selection
 * Phase 2: Frontend dependency management
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
            data.dependency_tree.forEach(computedField => {
                processDependencyTree(computedField);
            });

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
         * Fetch field data for dependency fields
         */
        async fetchFieldData(fieldIds) {
            // This would normally fetch from API
            // For now, return mock data
            return fieldIds.map(id => ({
                field_id: id,
                id: id,
                field_name: state.fieldMetadata.get(id)?.field_name || 'Unknown Field',
                is_computed: false
            }));
        },

        /**
         * Show auto-add notification
         */
        showAutoAddNotification(fieldName, addedCount, alreadySelectedCount) {
            const message = `✅ Added '${fieldName}' and ${addedCount} dependencies`;

            if (window.PopupManager) {
                PopupManager.showNotification(message, 'success', 4000);
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
            const message = `ℹ️ '${fieldName}' dependencies (${count}) already selected`;

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
                    <h4>⚠️ Cannot Remove Dependency</h4>
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
        }
    };
})();
```

### 2.2 Update Main.js
**File:** `app/static/js/admin/assign_data_points/main.js` (Modify line ~186)

```javascript
// Add after line 186, before the existing data-point-add-requested handler
// Initialize DependencyManager if available
if (window.DependencyManager) {
    window.DependencyManager.init().then(() => {
        console.log('[AppMain] DependencyManager initialized');
    }).catch(error => {
        console.error('[AppMain] Failed to initialize DependencyManager:', error);
    });
}

// MODIFY existing handler at line 138 - wrap existing logic
const originalHandler = AppEvents.listeners['data-point-add-requested'][0];
AppEvents.off('data-point-add-requested', originalHandler);

AppEvents.on('data-point-add-requested', async (data) => {
    const { fieldId, field } = data;
    console.log('[AppMain] Data point add requested:', fieldId);

    // Let DependencyManager handle cascade first
    if (window.DependencyManager) {
        await window.DependencyManager.handleFieldSelection(data);
    }

    // Then continue with original logic
    originalHandler(data);
});
```

---

## 🎨 Phase 3: Visual Indicators

### 3.1 Update SelectDataPointsPanel.js
**File:** `app/static/js/admin/assign_data_points/SelectDataPointsPanel.js`

Add computed field indicators to the rendering (around line 800):

```javascript
// In renderFieldItem function, add badge for computed fields
function renderFieldItem(field, isInactive = false) {
    const isComputed = field.is_computed || false;
    const dependencyCount = field.dependency_count || 0;

    const computedBadge = isComputed ?
        `<span class="computed-badge" title="Computed field with ${dependencyCount} dependencies">
            🧮 <small>(${dependencyCount})</small>
        </span>` : '';

    return `
        <div class="field-item ${isInactive ? 'inactive' : ''}"
             data-field-id="${field.field_id || field.id}">
            <span class="field-name">
                ${field.field_name || field.name}
                ${computedBadge}
            </span>
            <button class="add-btn" data-field-id="${field.field_id || field.id}">
                <i class="fas fa-plus"></i>
            </button>
        </div>
    `;
}
```

### 3.2 Add CSS Styles
**File:** `app/static/css/admin/assign_data_points.css`

```css
/* Computed Field Indicators */
.computed-badge {
    display: inline-block;
    margin-left: 8px;
    padding: 2px 6px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 12px;
    font-size: 0.75em;
    font-weight: 600;
    vertical-align: middle;
}

.computed-badge small {
    opacity: 0.9;
}

/* Dependency indicators in selected panel */
.selected-item.is-dependency {
    background: #f0f9ff;
    border-left: 3px solid #3b82f6;
}

.selected-item.is-dependency::before {
    content: "↳";
    position: absolute;
    left: 10px;
    color: #3b82f6;
}

.selected-item.is-computed {
    background: linear-gradient(to right, #faf5ff, #ffffff);
    border-left: 3px solid #8b5cf6;
}

/* Dependency tree view */
.dependency-tree {
    padding: 20px;
    background: #f9fafb;
    border-radius: 8px;
}

.dependency-tree-node {
    margin: 10px 0;
    padding: 10px;
    background: white;
    border-radius: 6px;
    border: 1px solid #e5e7eb;
}

.dependency-tree-node.computed {
    background: linear-gradient(to right, #faf5ff, #ffffff);
    border-color: #8b5cf6;
}

.dependency-tree-children {
    margin-left: 30px;
    margin-top: 10px;
    padding-left: 20px;
    border-left: 2px dashed #d1d5db;
}

/* Frequency conflict warnings */
.frequency-conflict {
    background: #fef2f2;
    border: 1px solid #ef4444;
    color: #991b1b;
    padding: 8px 12px;
    border-radius: 6px;
    margin: 10px 0;
}

.frequency-conflict i {
    color: #ef4444;
    margin-right: 8px;
}

/* Removal protection modal */
.removal-warning {
    padding: 20px;
}

.removal-warning h4 {
    color: #dc2626;
    margin-bottom: 15px;
}

.removal-warning ul {
    background: #fef2f2;
    padding: 15px 15px 15px 35px;
    border-radius: 6px;
    margin: 15px 0;
}

.removal-warning li {
    margin: 5px 0;
    color: #7f1d1d;
}
```

---

## 🧪 Phase 4: Test Implementation

Test implementation will be created in the next file...