"""
Dimensional Data Service for User Dashboard V2
Handles dimensional data operations for ESG data collection.
"""

from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from app.models.dimension import Dimension, DimensionValue, FieldDimension
from app.models.framework import FrameworkDataField
from app.models.esg_data import ESGData
from app.extensions import db
from flask_login import current_user
import itertools


class DimensionalDataService:
    """Service for handling dimensional data operations."""

    @staticmethod
    def prepare_dimension_matrix(field_id: str, entity_id: int, reporting_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate dimension matrix structure for a field.

        Args:
            field_id: The framework field ID
            entity_id: The entity ID for which to prepare the matrix
            reporting_date: Optional reporting date to load existing data

        Returns:
            Dictionary containing dimension matrix structure and existing data
        """
        # Get the field
        field = FrameworkDataField.query.get(field_id)
        if not field:
            return {
                'success': False,
                'error': 'Field not found'
            }

        # Get field dimensions
        field_dimensions = FieldDimension.query.filter_by(
            field_id=field_id,
            company_id=current_user.company_id
        ).all()

        if not field_dimensions:
            # No dimensions - simple field
            return {
                'success': True,
                'field_id': field_id,
                'field_name': field.field_name,
                'dimensions': [],
                'dimension_values': {},
                'combinations': [],
                'total_combinations': 0,
                'has_dimensions': False
            }

        # Get dimension values
        dimension_data = {}
        dimension_metadata = {}

        for fd in field_dimensions:
            dimension = fd.dimension
            values = dimension.get_ordered_values()

            dimension_data[dimension.name] = [
                {
                    'value': v.value,
                    'display_name': v.display_name or v.value,
                    'order': v.display_order,
                    'value_id': v.value_id
                }
                for v in values if v.is_active
            ]

            dimension_metadata[dimension.name] = {
                'dimension_id': dimension.dimension_id,
                'description': dimension.description,
                'is_required': fd.is_required
            }

        # Generate all combinations
        combinations = DimensionalDataService.generate_dimension_combinations(dimension_data)

        # Load existing data if reporting_date provided
        existing_data = None
        if reporting_date:
            esg_data = ESGData.query.filter_by(
                field_id=field_id,
                entity_id=entity_id,
                reporting_date=reporting_date,
                company_id=current_user.company_id
            ).first()

            if esg_data and esg_data.dimension_values:
                existing_data = esg_data.dimension_values

        return {
            'success': True,
            'field_id': field_id,
            'field_name': field.field_name,
            'field_unit': field.default_unit,
            'dimensions': list(dimension_data.keys()),
            'dimension_values': dimension_data,
            'dimension_metadata': dimension_metadata,
            'combinations': combinations,
            'total_combinations': len(combinations),
            'has_dimensions': True,
            'existing_data': existing_data
        }

    @staticmethod
    def generate_dimension_combinations(dimension_data: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Generate all possible combinations of dimension values.

        Args:
            dimension_data: Dictionary of dimension names to their values

        Returns:
            List of all dimension combinations
        """
        if not dimension_data:
            return []

        # Extract dimension names and values
        dimension_names = list(dimension_data.keys())
        dimension_value_lists = [dimension_data[dim] for dim in dimension_names]

        # Generate all combinations using Cartesian product
        combinations = []
        for combo in itertools.product(*dimension_value_lists):
            combination = {}
            for i, dim_name in enumerate(dimension_names):
                combination[dim_name] = combo[i]['value']
            combinations.append(combination)

        return combinations

    @staticmethod
    def calculate_totals(dimensional_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate totals across all dimensions.

        Args:
            dimensional_data: Dictionary containing breakdowns and dimensions

        Returns:
            Dictionary with overall and per-dimension totals
        """
        breakdowns = dimensional_data.get('breakdowns', [])
        dimensions = dimensional_data.get('dimensions', [])

        # Calculate overall total
        overall_total = 0
        for breakdown in breakdowns:
            if breakdown.get('raw_value') is not None:
                try:
                    overall_total += float(breakdown.get('raw_value', 0))
                except (ValueError, TypeError):
                    pass

        # Calculate per-dimension totals
        by_dimension = {}
        for dim_name in dimensions:
            dim_totals = {}
            for breakdown in breakdowns:
                dim_value = breakdown.get('dimensions', {}).get(dim_name)
                if dim_value and breakdown.get('raw_value') is not None:
                    try:
                        current = dim_totals.get(dim_value, 0)
                        dim_totals[dim_value] = current + float(breakdown.get('raw_value', 0))
                    except (ValueError, TypeError):
                        continue
            by_dimension[dim_name] = dim_totals

        return {
            'overall': overall_total,
            'by_dimension': by_dimension
        }

    @staticmethod
    def validate_dimensional_data(field_id: str, dimensional_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate dimensional data completeness and correctness.

        Args:
            field_id: The framework field ID
            dimensional_data: The dimensional data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Get field dimensions
        field_dimensions = FieldDimension.query.filter_by(
            field_id=field_id,
            company_id=current_user.company_id
        ).all()

        if not field_dimensions:
            # No dimensions required
            return True, None

        # Check all required dimensions are present
        required_dims = {fd.dimension.name for fd in field_dimensions if fd.is_required}
        provided_dims = set(dimensional_data.get('dimensions', []))

        if not required_dims.issubset(provided_dims):
            missing = required_dims - provided_dims
            return False, f"Missing required dimensions: {', '.join(missing)}"

        # Validate all breakdowns
        breakdowns = dimensional_data.get('breakdowns', [])

        if not breakdowns:
            return False, "No dimensional breakdowns provided"

        # Build valid dimension values lookup
        valid_values = {}
        for fd in field_dimensions:
            dimension = fd.dimension
            valid_values[dimension.name] = {
                v.value for v in dimension.dimension_values if v.is_active
            }

        # Validate each breakdown
        for i, breakdown in enumerate(breakdowns):
            dims = breakdown.get('dimensions', {})

            # Check all required dimensions are present in breakdown
            for req_dim in required_dims:
                if req_dim not in dims:
                    return False, f"Breakdown {i+1} missing required dimension: {req_dim}"

            # Check each dimension value is valid
            for dim_name, dim_value in dims.items():
                if dim_name not in valid_values:
                    return False, f"Unknown dimension: {dim_name}"

                if dim_value not in valid_values[dim_name]:
                    return False, f"Invalid value '{dim_value}' for dimension '{dim_name}'"

            # Validate raw_value if present
            raw_value = breakdown.get('raw_value')
            if raw_value is not None:
                try:
                    float(raw_value)
                except (ValueError, TypeError):
                    return False, f"Invalid numeric value in breakdown {i+1}: {raw_value}"

        return True, None

    @staticmethod
    def build_dimension_values_json(dimensional_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the complete dimension_values JSON structure for storage.

        Args:
            dimensional_data: Input dimensional data from API

        Returns:
            Complete JSON structure for ESGData.dimension_values column
        """
        # Calculate totals
        totals = DimensionalDataService.calculate_totals(dimensional_data)

        # Count completed combinations
        breakdowns = dimensional_data.get('breakdowns', [])
        completed_count = sum(1 for b in breakdowns if b.get('raw_value') is not None)
        total_count = len(breakdowns)

        # Build complete structure
        dimension_values = {
            'version': 2,
            'dimensions': dimensional_data.get('dimensions', []),
            'breakdowns': breakdowns,
            'totals': totals,
            'metadata': {
                'last_updated': datetime.utcnow().isoformat() + 'Z',
                'completed_combinations': completed_count,
                'total_combinations': total_count,
                'is_complete': completed_count == total_count and total_count > 0
            }
        }

        return dimension_values

    @staticmethod
    def extract_breakdowns_for_display(dimension_values: Dict[str, Any]) -> List[Dict]:
        """
        Extract and format dimensional breakdowns for display.

        Args:
            dimension_values: The stored dimension_values JSON

        Returns:
            List of formatted breakdowns for UI display
        """
        if not dimension_values or dimension_values.get('version') != 2:
            return []

        breakdowns = dimension_values.get('breakdowns', [])
        formatted = []

        for breakdown in breakdowns:
            formatted.append({
                'dimensions': breakdown.get('dimensions', {}),
                'raw_value': breakdown.get('raw_value'),
                'notes': breakdown.get('notes'),
                'display_label': DimensionalDataService._create_display_label(
                    breakdown.get('dimensions', {})
                )
            })

        return formatted

    @staticmethod
    def _create_display_label(dimensions: Dict[str, str]) -> str:
        """
        Create a human-readable display label for dimension combination.

        Args:
            dimensions: Dictionary of dimension name to value

        Returns:
            Formatted display string
        """
        if not dimensions:
            return "No dimensions"

        parts = [f"{k}: {v}" for k, v in dimensions.items()]
        return " | ".join(parts)

    @staticmethod
    def get_dimension_summary(field_id: str, entity_id: int, reporting_date: str) -> Dict[str, Any]:
        """
        Get summary of dimensional data for a specific entry.

        Args:
            field_id: Framework field ID
            entity_id: Entity ID
            reporting_date: Reporting date

        Returns:
            Summary of dimensional data including completeness
        """
        esg_data = ESGData.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date,
            company_id=current_user.company_id
        ).first()

        if not esg_data or not esg_data.dimension_values:
            return {
                'has_data': False,
                'is_complete': False,
                'total_value': None,
                'completed_combinations': 0,
                'total_combinations': 0
            }

        dim_values = esg_data.dimension_values
        metadata = dim_values.get('metadata', {})
        totals = dim_values.get('totals', {})

        return {
            'has_data': True,
            'is_complete': metadata.get('is_complete', False),
            'total_value': totals.get('overall'),
            'completed_combinations': metadata.get('completed_combinations', 0),
            'total_combinations': metadata.get('total_combinations', 0),
            'by_dimension': totals.get('by_dimension', {}),
            'last_updated': metadata.get('last_updated')
        }
