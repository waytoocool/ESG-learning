"""
Service for managing computed field dependencies.
Handles auto-cascade, validation, and conflict resolution.

This service provides methods for:
- Identifying dependencies for computed fields
- Auto-including dependencies when computed fields are selected
- Validating frequency compatibility
- Checking removal impact
- Managing entity assignment cascades
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

    # ========================================================================
    # VALIDATION ENGINE METHODS
    # ========================================================================

    @staticmethod
    def get_dependent_computed_fields(field_id: str) -> List[FrameworkDataField]:
        """
        Get all computed fields that depend on the given field.

        This method is used by ValidationService to check if changing a field
        will impact any computed fields.

        Args:
            field_id: The field ID to check dependencies for

        Returns:
            List of FrameworkDataField objects that are computed and depend on this field
        """
        field = FrameworkDataField.query.get(field_id)
        if not field:
            return []

        # Use the existing method from FrameworkDataField model
        return field.get_fields_depending_on_this()

    @staticmethod
    def get_dependencies(computed_field_id: str) -> List[str]:
        """
        Get all dependency field IDs for a computed field.

        Args:
            computed_field_id: The computed field ID

        Returns:
            List of field_ids that this computed field depends on
        """
        computed_field = FrameworkDataField.query.get(computed_field_id)
        if not computed_field or not computed_field.is_computed:
            return []

        dependencies = computed_field.get_all_dependencies()
        return [dep.field_id for dep in dependencies]

    @staticmethod
    def calculate_computed_value(computed_field: FrameworkDataField,
                                dependency_values: Dict[str, float]) -> float:
        """
        Calculate computed field value from dependency values.

        This method evaluates the computed field's formula with the provided
        dependency values.

        Args:
            computed_field: The computed field object
            dependency_values: Dictionary mapping field_id to value
                              {field_id: value, ...}

        Returns:
            Calculated value (float)

        Raises:
            ValueError: If formula evaluation fails or dependencies missing
        """
        if not computed_field.is_computed or not computed_field.formula:
            raise ValueError(f"Field {computed_field.field_id} is not a computed field")

        # Get variable mappings for this computed field
        variable_mappings = FieldVariableMapping.query.filter_by(
            field_id=computed_field.field_id
        ).all()

        # Build evaluation context with variable names
        eval_context = {}
        for mapping in variable_mappings:
            variable_name = mapping.variable_name
            dependency_field_id = mapping.dependency_field_id

            if dependency_field_id not in dependency_values:
                raise ValueError(
                    f"Missing value for dependency {dependency_field_id} "
                    f"(variable: {variable_name})"
                )

            eval_context[variable_name] = dependency_values[dependency_field_id]

        # Evaluate formula
        try:
            # Use eval with restricted globals for safety
            # Only allow basic math operations
            safe_globals = {
                '__builtins__': {},
                'abs': abs,
                'min': min,
                'max': max,
                'round': round,
                'sum': sum
            }

            result = eval(computed_field.formula, safe_globals, eval_context)

            # Ensure result is numeric
            return float(result)

        except Exception as e:
            raise ValueError(
                f"Failed to evaluate formula '{computed_field.formula}': {str(e)}"
            )


# Export service instance
dependency_service = DependencyService()
