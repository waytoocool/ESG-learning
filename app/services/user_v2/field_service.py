"""
Field Service
=============

Business logic for field details, metadata, and validation.
"""

from typing import Dict, Any, Optional, List
from datetime import date
from sqlalchemy.orm import Session

from ...models.framework import FrameworkDataField, FieldVariableMapping
from ...models.data_assignment import DataPointAssignment
from ...models.dimension import Dimension, FieldDimension, DimensionValue
from ...extensions import db


class FieldService:
    """Service for managing field details and metadata."""

    @staticmethod
    def get_field_details(field_id: str, entity_id: int, session: Optional[Session] = None) -> Dict[str, Any]:
        """
        Get comprehensive field details including dimensions and validation rules.

        Args:
            field_id: The framework data field ID
            entity_id: The entity ID (for assignment information)
            session: Optional database session

        Returns:
            Dict with complete field information
        """
        if session is None:
            session = db.session

        # Get the field
        field = FrameworkDataField.query.get(field_id)
        if not field:
            return {
                'success': False,
                'error': 'Field not found'
            }

        # Get assignment for this field and entity
        assignment = DataPointAssignment.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            series_status='active'
        ).first()

        # Get dimensions for this field
        dimensions = FieldService._get_field_dimensions(field_id)

        # Get validation rules
        validation_rules = FieldService._get_validation_rules(field, assignment)

        # Get dependencies if computed field
        dependencies = []
        if field.is_computed:
            dependencies = FieldService._get_field_dependencies(field_id)

        return {
            'success': True,
            'field_id': field.field_id,
            'field_name': field.field_name,
            'field_code': field.field_code,
            'field_type': 'computed' if field.is_computed else 'raw_input',
            'data_type': field.value_type.lower() if field.value_type else 'text',
            'unit_category': field.unit_category,
            'default_unit': field.default_unit,
            'description': field.description,
            'dimensions': dimensions,
            'validation_rules': validation_rules,
            'assignment': FieldService._format_assignment(assignment) if assignment else None,
            'dependencies': dependencies,
            'formula_expression': field.formula_expression if field.is_computed else None,
            'constant_multiplier': field.constant_multiplier if field.is_computed else None
        }

    @staticmethod
    def _get_field_dimensions(field_id: str) -> List[Dict[str, Any]]:
        """
        Get dimensions associated with a field.

        Args:
            field_id: The field ID

        Returns:
            List of dimension dictionaries
        """
        field_dimensions = FieldDimension.query.filter_by(field_id=field_id).all()

        dimensions = []
        for fd in field_dimensions:
            if not fd.dimension:
                continue

            dim = fd.dimension
            values = []

            for dv in dim.get_ordered_values():
                values.append({
                    'value_id': dv.value_id,
                    'value': dv.value,
                    'display_name': dv.display_name,
                    'effective_display_name': dv.effective_display_name
                })

            dimensions.append({
                'dimension_id': dim.dimension_id,
                'name': dim.name,
                'is_required': fd.is_required,
                'values': values
            })

        return dimensions

    @staticmethod
    def _get_validation_rules(field: FrameworkDataField, assignment: Optional[DataPointAssignment]) -> Dict[str, Any]:
        """
        Get validation rules for a field.

        Args:
            field: The field object
            assignment: The assignment object (optional)

        Returns:
            Dict with validation rules
        """
        rules = {
            'required': True if assignment else False,
            'data_type': field.value_type.lower() if field.value_type else 'text'
        }

        # Add numeric validation rules
        if field.value_type == 'NUMBER':
            rules['min_value'] = None  # Can be extended based on field metadata
            rules['max_value'] = None

        # Add frequency-based validation
        if assignment:
            rules['frequency'] = assignment.frequency
            rules['valid_reporting_dates'] = [
                d.isoformat() for d in assignment.get_valid_reporting_dates()
            ]

        return rules

    @staticmethod
    def _get_field_dependencies(computed_field_id: str) -> List[Dict[str, Any]]:
        """
        Get dependencies for a computed field.

        Args:
            computed_field_id: The computed field ID

        Returns:
            List of dependency dictionaries
        """
        mappings = FieldVariableMapping.query.filter_by(
            computed_field_id=computed_field_id
        ).all()

        dependencies = []
        for mapping in mappings:
            raw_field = FrameworkDataField.query.get(mapping.raw_field_id)
            if raw_field:
                dependencies.append({
                    'field_id': raw_field.field_id,
                    'field_name': raw_field.field_name,
                    'variable_name': mapping.variable_name,
                    'coefficient': mapping.coefficient,
                    'aggregation_type': mapping.aggregation_type,
                    'dimension_filter': mapping.dimension_filter
                })

        return dependencies

    @staticmethod
    def _format_assignment(assignment: DataPointAssignment) -> Dict[str, Any]:
        """
        Format assignment information for API response.

        Args:
            assignment: The assignment object

        Returns:
            Dict with formatted assignment data
        """
        return {
            'assignment_id': assignment.id,
            'frequency': assignment.frequency,
            'unit': assignment.effective_unit,
            'data_series_id': assignment.data_series_id,
            'series_version': assignment.series_version,
            'series_status': assignment.series_status,
            'assigned_date': assignment.assigned_date.isoformat() if assignment.assigned_date else None,
            'topic_name': assignment.effective_topic_name,
            'topic_path': assignment.effective_topic_path
        }

    @staticmethod
    def get_assigned_fields_for_entity(entity_id: int, include_computed: bool = True) -> List[Dict[str, Any]]:
        """
        Get all assigned fields for an entity.

        Args:
            entity_id: The entity ID
            include_computed: Whether to include computed fields

        Returns:
            List of field dictionaries with assignment info
        """
        from ...models.entity import Entity

        # Verify entity exists
        entity = Entity.query.get(entity_id)
        if not entity:
            return []

        # Get active assignments for THIS SPECIFIC ENTITY ONLY
        # Users should only see data points explicitly assigned to their entity
        assignments = DataPointAssignment.query.filter(
            DataPointAssignment.entity_id == entity_id,
            DataPointAssignment.series_status == 'active'
        ).all()

        fields = []
        for assignment in assignments:
            field = FrameworkDataField.query.get(assignment.field_id)
            if not field:
                continue

            # Skip computed fields if not requested
            if field.is_computed and not include_computed:
                continue

            fields.append({
                'field_id': field.field_id,
                'field_name': field.field_name,
                'field_code': field.field_code,
                'is_computed': field.is_computed,
                'value_type': field.value_type,
                'unit_category': field.unit_category,
                'default_unit': field.default_unit,
                'assignment_id': assignment.id,
                'frequency': assignment.frequency,
                'entity_id': assignment.entity_id,
                'topic_name': assignment.effective_topic_name
            })

        return fields

    @staticmethod
    def validate_field_value(field_id: str, value: Any, dimension_values: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Validate a field value against field rules.

        Args:
            field_id: The field ID
            value: The value to validate
            dimension_values: Optional dimension values

        Returns:
            Dict with validation result
        """
        field = FrameworkDataField.query.get(field_id)
        if not field:
            return {
                'valid': False,
                'error': 'Field not found'
            }

        # Type validation
        if field.value_type == 'NUMBER':
            try:
                float_value = float(value)
            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'error': f'Value must be a number'
                }

        # Dimension validation
        if dimension_values:
            field_dimensions = FieldDimension.query.filter_by(field_id=field_id).all()
            for fd in field_dimensions:
                if fd.is_required:
                    dim_name = fd.dimension.name.lower()
                    if dim_name not in dimension_values or not dimension_values[dim_name]:
                        return {
                            'valid': False,
                            'error': f'Required dimension "{fd.dimension.name}" is missing'
                        }

        return {
            'valid': True
        }
