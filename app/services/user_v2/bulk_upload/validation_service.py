"""
Bulk Validation Service

Handles validation of bulk uploads including overwrite detection.
"""

from typing import Dict, List, Any
from datetime import datetime


class BulkValidationService:
    """Service for validating bulk upload data."""

    @staticmethod
    def validate_and_check_overwrites(rows: List[Dict], current_user) -> Dict[str, Any]:
        """
        Validate all rows and detect overwrites.

        Args:
            rows: List of parsed row dictionaries
            current_user: Current user object

        Returns:
            dict: {
                'valid': bool,
                'total_rows': int,
                'valid_count': int,
                'invalid_count': int,
                'warning_count': int,
                'overwrite_count': int,
                'invalid_rows': List[dict],
                'warning_rows': List[dict],
                'overwrite_rows': List[dict],
                'valid_rows': List[dict]
            }
        """
        from ..data_validation_service import DataValidationService
        from ....models.esg_data import ESGData

        # First, run standard validation
        validation_result = DataValidationService.validate_bulk_upload(rows)

        if not validation_result['valid']:
            # Validation failed, return early
            return {
                **validation_result,
                'overwrite_count': 0,
                'overwrite_rows': []
            }

        # Check for overwrites (existing data)
        overwrite_rows = []
        for row in validation_result['valid_rows']:
            # Check if data already exists for this field + entity + date + dimensions
            existing = ESGData.query.filter_by(
                field_id=row['field_id'],
                entity_id=row['entity_id'],
                reporting_date=row['reporting_date'],
                is_draft=False
            ).first()

            if existing:
                # Check if dimensions match (if applicable)
                if row.get('dimensions'):
                    # For dimensional data, check if dimensions match
                    if existing.dimension_values != row['dimensions']:
                        # Different dimension combination, not an overwrite
                        continue

                # This is an overwrite
                overwrite_rows.append({
                    'row_number': row['row_number'],
                    'field_name': row['field_name'],
                    'old_value': existing.raw_value,
                    'new_value': str(row['parsed_value']),
                    'submitted_date': existing.created_at.isoformat(),
                    'has_notes': existing.has_notes(),
                    'has_attachments': len(existing.attachments) > 0,
                    'data_id': existing.data_id  # Store for later use
                })

                # Mark row as overwrite
                row['is_overwrite'] = True
                row['existing_data_id'] = existing.data_id

        return {
            **validation_result,
            'overwrite_count': len(overwrite_rows),
            'overwrite_rows': overwrite_rows
        }

    @staticmethod
    def check_dimension_version_changes(rows: List[Dict]) -> Dict[str, Any]:
        """
        Check if dimensions have changed since template download.

        Args:
            rows: List of parsed row dictionaries

        Returns:
            dict: {
                'valid': bool,
                'errors': List[str]
            }
        """
        from ....models.dimension import FieldDimension

        errors = []

        # Group rows by field_id
        fields_checked = set()

        for row in rows:
            field_id = row['field_id']

            if field_id in fields_checked:
                continue

            fields_checked.add(field_id)

            # Get current dimensions for field
            current_dimensions = FieldDimension.query.filter_by(
                field_id=field_id
            ).all()

            current_dim_names = {fd.dimension.name.lower() for fd in current_dimensions}

            # Get dimensions from row
            row_dimensions = row.get('dimensions', {})
            row_dim_names = {name.lower() for name in row_dimensions.keys()} if row_dimensions else set()

            # Check if dimension structure has changed
            if current_dim_names != row_dim_names:
                errors.append(
                    f"Row {row['row_number']}: Field dimensions have changed. "
                    f"Current dimensions: {', '.join(current_dim_names) or 'None'}. "
                    "Please download a new template."
                )

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
