"""
Data Validation Service for Enhancement #4: Bulk Excel Upload

Unified validation logic for both modal and bulk upload workflows.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import re


class DataValidationService:
    """Service for validating ESG data entries."""

    @staticmethod
    def validate_data_entry(
        field_id: str,
        entity_id: int,
        reporting_date: date,
        value: Any,
        assignment=None,
        dimensions: Optional[Dict] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a single data entry.

        Args:
            field_id: Framework data field ID
            entity_id: Entity ID
            reporting_date: Reporting date
            value: Raw value to validate
            assignment: DataPointAssignment object (optional, will be resolved if not provided)
            dimensions: Dimension values dict (optional)
            notes: User notes (optional)

        Returns:
            dict: {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str],
                'parsed_value': Any  # Cleaned/parsed value
            }
        """
        from ...models.data_assignment import DataPointAssignment
        from ...models.framework import FrameworkDataField

        errors = []
        warnings = []
        parsed_value = None

        # 1. Validate assignment exists and is active
        if not assignment:
            assignment = DataPointAssignment.query.filter_by(
                field_id=field_id,
                entity_id=entity_id,
                series_status='active'
            ).first()

        if not assignment:
            errors.append(f"No active assignment found for field {field_id} and entity {entity_id}")
            return {
                'valid': False,
                'errors': errors,
                'warnings': warnings,
                'parsed_value': None
            }

        # 2. Validate reporting date
        date_validation = DataValidationService._validate_reporting_date(reporting_date, assignment)
        if not date_validation['valid']:
            errors.extend(date_validation['errors'])

        # 3. Get field for data type validation
        field = FrameworkDataField.query.get(field_id)
        if not field:
            errors.append(f"Field {field_id} not found")
            return {
                'valid': False,
                'errors': errors,
                'warnings': warnings,
                'parsed_value': None
            }

        # 4. Validate data type
        type_validation = DataValidationService._validate_data_type(value, field.value_type)
        if not type_validation['valid']:
            errors.extend(type_validation['errors'])
        else:
            parsed_value = type_validation['parsed_value']

        # 5. Validate dimensions if present
        if dimensions:
            dim_validation = DataValidationService._validate_dimensions(dimensions, field_id)
            if not dim_validation['valid']:
                errors.extend(dim_validation['errors'])
            warnings.extend(dim_validation.get('warnings', []))

        # 6. Validate notes length
        if notes and len(notes) > 1000:
            errors.append(f"Notes exceed maximum length of 1000 characters (current: {len(notes)})")

        # 7. Business rules validation (warnings only)
        if parsed_value is not None:
            business_warnings = DataValidationService._validate_business_rules(
                parsed_value, field, assignment
            )
            warnings.extend(business_warnings)

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'parsed_value': parsed_value
        }

    @staticmethod
    def validate_bulk_upload(rows: List[Dict]) -> Dict[str, Any]:
        """
        Validate multiple rows from bulk upload.

        Args:
            rows: List of row dictionaries with keys:
                  field_id, entity_id, reporting_date, value, dimensions, notes, row_number

        Returns:
            dict: {
                'valid': bool,  # All rows valid?
                'total_rows': int,
                'valid_count': int,
                'invalid_count': int,
                'warning_count': int,
                'invalid_rows': List[dict],
                'warning_rows': List[dict],
                'valid_rows': List[dict]  # Includes parsed_value
            }
        """
        from ...models.data_assignment import DataPointAssignment

        invalid_rows = []
        warning_rows = []
        valid_rows = []

        # Pre-fetch all assignments for efficiency
        assignments_cache = {}

        for row in rows:
            row_number = row.get('row_number', '?')
            field_id = row.get('field_id')
            entity_id = row.get('entity_id')

            # Get or cache assignment
            cache_key = f"{field_id}_{entity_id}"
            if cache_key not in assignments_cache:
                assignment = DataPointAssignment.query.filter_by(
                    field_id=field_id,
                    entity_id=entity_id,
                    series_status='active'
                ).first()
                assignments_cache[cache_key] = assignment
            else:
                assignment = assignments_cache[cache_key]

            # Validate row
            validation = DataValidationService.validate_data_entry(
                field_id=field_id,
                entity_id=entity_id,
                reporting_date=row.get('reporting_date'),
                value=row.get('value'),
                assignment=assignment,
                dimensions=row.get('dimensions'),
                notes=row.get('notes')
            )

            # Categorize result
            if not validation['valid']:
                invalid_rows.append({
                    'row_number': row_number,
                    'field_name': row.get('field_name', field_id),
                    'errors': validation['errors']
                })
            else:
                # Store parsed value in row
                row['parsed_value'] = validation['parsed_value']
                row['assignment_id'] = assignment.id if assignment else None
                valid_rows.append(row)

                # Check for warnings
                if validation['warnings']:
                    warning_rows.append({
                        'row_number': row_number,
                        'field_name': row.get('field_name', field_id),
                        'warnings': validation['warnings']
                    })

        return {
            'valid': len(invalid_rows) == 0,
            'total_rows': len(rows),
            'valid_count': len(valid_rows),
            'invalid_count': len(invalid_rows),
            'warning_count': len(warning_rows),
            'invalid_rows': invalid_rows,
            'warning_rows': warning_rows,
            'valid_rows': valid_rows
        }

    @staticmethod
    def _validate_reporting_date(reporting_date: date, assignment) -> Dict:
        """Validate reporting date is valid for assignment."""
        errors = []

        try:
            valid_dates = assignment.get_valid_reporting_dates()
            if reporting_date not in valid_dates:
                valid_dates_str = ', '.join([d.strftime('%Y-%m-%d') for d in valid_dates[:5]])
                errors.append(
                    f"Invalid reporting date {reporting_date.strftime('%Y-%m-%d')}. "
                    f"Valid dates: {valid_dates_str}"
                )
        except Exception as e:
            errors.append(f"Could not validate reporting date: {str(e)}")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    @staticmethod
    def _validate_data_type(value: Any, value_type: str) -> Dict:
        """
        Validate and parse value according to data type.

        Supported types: INTEGER, DECIMAL, NUMBER, PERCENTAGE, CURRENCY, BOOLEAN, DATE, TEXT
        """
        errors = []
        parsed_value = None

        # Handle empty/None values
        if value is None or (isinstance(value, str) and value.strip() == ''):
            errors.append("Value is required")
            return {'valid': False, 'errors': errors, 'parsed_value': None}

        try:
            if value_type == 'INTEGER':
                # Must be whole number
                parsed_value = int(float(value))
                if float(value) != parsed_value:
                    errors.append(f"Invalid INTEGER format: '{value}' (decimals not allowed)")

            elif value_type in ['DECIMAL', 'NUMBER']:
                # Allow decimals, remove commas
                clean_value = str(value).replace(',', '')
                parsed_value = float(Decimal(clean_value))

            elif value_type == 'PERCENTAGE':
                # Accept both 15 and 0.15, normalize to decimal
                clean_value = str(value).replace('%', '').replace(',', '').strip()
                num = float(Decimal(clean_value))
                # If > 1, assume it's like "15" meaning 15%, convert to 0.15
                parsed_value = num / 100 if num > 1 else num

            elif value_type == 'CURRENCY':
                # Strip $, commas
                clean_value = str(value).replace('$', '').replace(',', '').strip()
                parsed_value = float(Decimal(clean_value))

            elif value_type == 'BOOLEAN':
                # Accept TRUE/FALSE, YES/NO, 1/0
                str_value = str(value).strip().upper()
                if str_value in ['TRUE', 'YES', '1', 'T', 'Y']:
                    parsed_value = True
                elif str_value in ['FALSE', 'NO', '0', 'F', 'N']:
                    parsed_value = False
                else:
                    errors.append(f"Invalid BOOLEAN format: '{value}' (use TRUE/FALSE, YES/NO, or 1/0)")

            elif value_type == 'DATE':
                # Parse YYYY-MM-DD format
                if isinstance(value, date):
                    parsed_value = value
                elif isinstance(value, datetime):
                    parsed_value = value.date()
                else:
                    # Try parsing string
                    parsed_value = datetime.strptime(str(value), '%Y-%m-%d').date()

            elif value_type == 'TEXT':
                # Accept as-is
                parsed_value = str(value)

            else:
                # Unknown type, accept as string
                parsed_value = str(value)

        except (ValueError, InvalidOperation, TypeError) as e:
            errors.append(f"Invalid {value_type} format: '{value}'")
            parsed_value = None

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'parsed_value': parsed_value
        }

    @staticmethod
    def _validate_dimensions(dimensions: Dict, field_id: str) -> Dict:
        """Validate dimension values against field's defined dimensions."""
        from ...models.dimension import FieldDimension, DimensionValue

        errors = []
        warnings = []

        # Get field dimensions
        field_dimensions = FieldDimension.query.filter_by(field_id=field_id).all()

        if not field_dimensions and dimensions:
            warnings.append("Field has no dimensions configured, dimension values will be ignored")
            return {'valid': True, 'errors': [], 'warnings': warnings}

        # Create lookup of dimension names to allowed values
        dim_config = {}
        for fd in field_dimensions:
            dim_values = DimensionValue.query.filter_by(
                dimension_id=fd.dimension_id
            ).all()
            dim_config[fd.dimension.name.lower()] = {
                'required': fd.is_required,
                'allowed_values': [dv.value for dv in dim_values]
            }

        # Validate each provided dimension
        for dim_name, dim_value in dimensions.items():
            dim_name_lower = dim_name.lower()

            if dim_name_lower not in dim_config:
                warnings.append(f"Unknown dimension '{dim_name}' will be ignored")
                continue

            config = dim_config[dim_name_lower]

            # Check if value is in allowed values
            if dim_value not in config['allowed_values']:
                allowed_str = ', '.join(config['allowed_values'])
                errors.append(
                    f"Invalid value '{dim_value}' for dimension '{dim_name}'. "
                    f"Valid values: {allowed_str}"
                )

        # Check for missing required dimensions
        for dim_name, config in dim_config.items():
            if config['required']:
                if dim_name not in [k.lower() for k in dimensions.keys()]:
                    errors.append(f"Required dimension '{dim_name}' is missing")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    @staticmethod
    def _validate_business_rules(parsed_value: Any, field, assignment) -> List[str]:
        """
        Apply business rule validations (warnings only).

        Returns:
            List of warning messages
        """
        warnings = []

        # Numeric value warnings
        if isinstance(parsed_value, (int, float)):
            # Warn on negative values (except for variance fields)
            if parsed_value < 0:
                if 'variance' not in field.field_name.lower() and 'change' not in field.field_name.lower():
                    warnings.append(f"Negative value ({parsed_value}) detected - please verify")

            # Warn on very large values
            if abs(parsed_value) > 1_000_000_000:  # 1 billion
                warnings.append(f"Very large value ({parsed_value:,.0f}) - please verify")

        return warnings
