"""
Field API
=========

API endpoints for field details, metadata, and validation.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from ...decorators.auth import tenant_required_for
from ...services.user_v2.field_service import FieldService
from ...extensions import db

field_api_bp = Blueprint('user_v2_field_api', __name__, url_prefix='/api/user/v2')


@field_api_bp.route('/field-details/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_field_details(field_id):
    """
    Get comprehensive field details including dimensions and validation rules.

    Args:
        field_id: The framework data field ID

    Query Parameters:
        entity_id (optional): Entity ID for assignment info (defaults to current user's entity)

    Response:
        {
            "success": true,
            "field_id": "abc-123",
            "field_name": "Employee Count",
            "field_type": "raw_input",
            "data_type": "number",
            "unit": "employees",
            "description": "Total number of employees",
            "dimensions": [...],
            "validation_rules": {...},
            "assignment": {...}
        }
    """
    try:
        # Get entity ID from query params or use current user's entity
        entity_id = request.args.get('entity_id', type=int)
        if not entity_id:
            entity_id = current_user.entity_id

        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'No entity context available'
            }), 400

        # Get field details
        result = FieldService.get_field_details(
            field_id=field_id,
            entity_id=entity_id,
            session=db.session
        )

        if not result.get('success'):
            return jsonify(result), 404

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@field_api_bp.route('/assigned-fields', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_assigned_fields():
    """
    Get all fields assigned to the current entity.

    Query Parameters:
        include_computed (optional): Include computed fields (default: true)
        entity_id (optional): Entity ID (defaults to current user's entity)

    Response:
        {
            "success": true,
            "entity_id": 1,
            "fields": [
                {
                    "field_id": "abc-123",
                    "field_name": "Employee Count",
                    "is_computed": false,
                    "value_type": "NUMBER",
                    "frequency": "Monthly",
                    "assignment_id": "assign-1"
                }
            ],
            "total_count": 15
        }
    """
    try:
        # Get parameters
        include_computed = request.args.get('include_computed', 'true').lower() == 'true'
        entity_id = request.args.get('entity_id', type=int)

        if not entity_id:
            entity_id = current_user.entity_id

        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'No entity context available'
            }), 400

        # Get assigned fields
        fields = FieldService.get_assigned_fields_for_entity(
            entity_id=entity_id,
            include_computed=include_computed
        )

        return jsonify({
            'success': True,
            'entity_id': entity_id,
            'fields': fields,
            'total_count': len(fields)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@field_api_bp.route('/validate-value', methods=['POST'])
@login_required
@tenant_required_for('USER')
def validate_field_value():
    """
    Validate a field value against field rules.

    Request Body:
        {
            "field_id": "abc-123",
            "value": 500,
            "dimension_values": {"gender": "Male", "age": "<30"}
        }

    Response:
        {
            "valid": true
        }
        or
        {
            "valid": false,
            "error": "Value must be a number"
        }
    """
    try:
        data = request.get_json()

        field_id = data.get('field_id')
        value = data.get('value')
        dimension_values = data.get('dimension_values')

        if not field_id or value is None:
            return jsonify({
                'valid': False,
                'error': 'field_id and value are required'
            }), 400

        # Validate
        result = FieldService.validate_field_value(
            field_id=field_id,
            value=value,
            dimension_values=dimension_values
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 500


@field_api_bp.route('/field-dates/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_field_dates(field_id):
    """
    Get valid reporting dates for a field with completion status.

    Args:
        field_id: The framework data field ID

    Query Parameters:
        entity_id (optional): Entity ID (defaults to current user's entity)
        fy_year (optional): Fiscal year (defaults to current FY)

    Response:
        {
            "success": true,
            "field_id": "abc-123",
            "field_name": "Employee Count",
            "frequency": "Monthly",
            "fy_year": 2025,
            "fy_display": "Apr 2024 - Mar 2025",
            "valid_dates": [
                {
                    "date": "2024-04-30",
                    "status": "complete",
                    "has_dimensional_data": false
                },
                {
                    "date": "2024-05-31",
                    "status": "pending",
                    "has_dimensional_data": false
                }
            ]
        }
    """
    try:
        from ...models.data_assignment import DataPointAssignment
        from ...models.esg_data import ESGData
        from ...models.dimension import FieldDimension
        from ...services.fiscal_year_service import FiscalYearService
        import itertools

        # Get entity ID from query params or use current user's entity
        entity_id = request.args.get('entity_id', type=int)
        if not entity_id:
            entity_id = current_user.entity_id

        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'No entity context available'
            }), 400

        # Get FY year from query params or use current FY
        fy_year = request.args.get('fy_year', type=int)
        if not fy_year:
            fy_year = FiscalYearService.get_current_fy_year(current_user.company)

        # Get active assignment for this field and entity
        assignment = DataPointAssignment.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            series_status='active'
        ).first()

        if not assignment:
            return jsonify({
                'success': False,
                'error': 'No active assignment found for this field and entity'
            }), 404

        # Get valid reporting dates for the fiscal year
        valid_dates = assignment.get_valid_reporting_dates(fy_year)

        # Check if field has dimensions
        field_dimensions = FieldDimension.query.filter_by(field_id=field_id).all()
        has_dimensions = len(field_dimensions) > 0

        # Calculate required dimension combinations if applicable
        required_combinations_count = 1
        required_dim_combinations = []

        if has_dimensions:
            # Build list of all possible dimension combinations
            print(f"[DimensionDebug] Field has {len(field_dimensions)} field_dimensions")
            dimension_lists = []
            for fd in field_dimensions:
                print(f"[DimensionDebug] Field dimension: is_required={fd.is_required}, dimension={fd.dimension}, dimension_id={fd.dimension_id}")
                if fd.is_required and fd.dimension:
                    dim_values = [dv.value for dv in fd.dimension.dimension_values]
                    dimension_lists.append([(fd.dimension.name, val) for val in dim_values])
                    print(f"[DimensionDebug] {fd.dimension.name}: {len(dim_values)} values = {dim_values}")
                else:
                    print(f"[DimensionDebug] SKIPPED: is_required={fd.is_required}, has_dimension={fd.dimension is not None}")

            # Generate all combinations
            if dimension_lists:
                for combo in itertools.product(*dimension_lists):
                    required_dim_combinations.append(dict(combo))
                required_combinations_count = len(required_dim_combinations)
                print(f"[DimensionDebug] Built {required_combinations_count} required combinations")
                print(f"[DimensionDebug] Sample combo: {required_dim_combinations[0] if required_dim_combinations else 'NONE'}")

        # Build response with status for each date
        from datetime import date as date_class
        today = date_class.today()

        dates_with_status = []
        for report_date in valid_dates:
            # Calculate due date for this reporting period
            due_date = FiscalYearService.calculate_due_date(report_date, assignment.company)
            is_past_due = FiscalYearService.is_overdue(report_date, assignment.company, today)

            # Check completion status
            if has_dimensions:
                # For dimensional data, check if all required combinations have data
                # ESGData stores dimensions in a JSON field: dimension_values
                existing_data = ESGData.query.filter_by(
                    field_id=field_id,
                    entity_id=entity_id,
                    reporting_date=report_date
                ).all()

                # Check if using new format (version 2) or old format
                is_complete = False

                if len(existing_data) == 1 and existing_data[0].dimension_values:
                    # Might be new format (single row with all data)
                    dim_values = existing_data[0].dimension_values

                    # Check if it's version 2 format with metadata
                    if isinstance(dim_values, dict) and dim_values.get('version') == 2:
                        # New format: Check the metadata.is_complete flag
                        metadata = dim_values.get('metadata', {})
                        is_complete = metadata.get('is_complete', False)
                    else:
                        # Old format with single entry - check if it matches a required combo
                        # Use case-insensitive matching
                        dim_values_lower = {k.lower(): v for k, v in dim_values.items()}
                        for req_combo in required_dim_combinations:
                            req_combo_lower = {k.lower(): v for k, v in req_combo.items()}
                            if dim_values_lower == req_combo_lower:
                                is_complete = True
                                break
                else:
                    # Old format: Multiple rows, each with dimension_values
                    # Count how many required combinations have data
                    found_combinations = 0
                    for data_entry in existing_data:
                        if data_entry.dimension_values:
                            # Use case-insensitive matching for dimension keys
                            entry_dims_lower = {k.lower(): v for k, v in data_entry.dimension_values.items()}

                            # Check if this entry matches any required combination
                            for req_combo in required_dim_combinations:
                                req_combo_lower = {k.lower(): v for k, v in req_combo.items()}
                                if entry_dims_lower == req_combo_lower:
                                    found_combinations += 1
                                    break

                    # Debug logging
                    print(f"[DateStatus] {report_date}: found {found_combinations}/{required_combinations_count} combinations")
                    if found_combinations > 0 and found_combinations < required_combinations_count:
                        print(f"[DateStatus] Required: {required_dim_combinations}")
                        print(f"[DateStatus] Found entries: {[e.dimension_values for e in existing_data]}")

                    is_complete = found_combinations >= required_combinations_count
            else:
                # For non-dimensional data, check if ESGData exists with a value
                esg_data = ESGData.query.filter_by(
                    field_id=field_id,
                    entity_id=entity_id,
                    reporting_date=report_date
                ).first()

                is_complete = esg_data and (esg_data.raw_value is not None or esg_data.calculated_value is not None)

            # Determine status based on completion and overdue logic
            if is_complete:
                status = 'complete'
            elif is_past_due:
                status = 'overdue'
            else:
                status = 'pending'

            dates_with_status.append({
                'date': report_date.isoformat(),
                'due_date': due_date.isoformat(),
                'is_overdue': is_past_due,
                'status': status,
                'has_dimensional_data': has_dimensions
            })

        return jsonify({
            'success': True,
            'field_id': field_id,
            'field_name': assignment.field.field_name,
            'frequency': assignment.frequency,
            'fy_year': fy_year,
            'fy_display': assignment.company.get_fy_display(fy_year),
            'has_dimensions': has_dimensions,
            'required_combinations_count': required_combinations_count,
            'valid_dates': dates_with_status
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@field_api_bp.route('/field-metadata/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_field_metadata(field_id):
    """
    Get field metadata including formula, dependencies, and description.

    Args:
        field_id: The framework data field ID

    Query Parameters:
        entity_id (optional): Entity ID (defaults to current user's entity)

    Response:
        {
            "success": true,
            "field_id": "abc-123",
            "field_name": "Total Employee Count",
            "description": "Sum of all employees",
            "field_type": "computed",
            "unit": "employees",
            "formula": "A + B",
            "dependencies": [
                {
                    "field_id": "def-456",
                    "field_name": "Male Employees",
                    "variable": "A"
                },
                {
                    "field_id": "ghi-789",
                    "field_name": "Female Employees",
                    "variable": "B"
                }
            ]
        }
    """
    try:
        from ...models.framework import FrameworkDataField
        from ...models.data_assignment import DataPointAssignment

        # Get entity ID from query params or use current user's entity
        entity_id = request.args.get('entity_id', type=int)
        if not entity_id:
            entity_id = current_user.entity_id

        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'No entity context available'
            }), 400

        # Get field details
        field = FrameworkDataField.query.filter_by(field_id=field_id).first()
        if not field:
            return jsonify({
                'success': False,
                'error': 'Field not found'
            }), 404

        # Get assignment for context
        assignment = DataPointAssignment.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            series_status='active'
        ).first()

        # Build response
        response = {
            'success': True,
            'field_id': field.field_id,
            'field_name': field.field_name,
            'description': field.description or 'No description available',
            'field_type': 'computed' if field.is_computed else 'raw_input',
            'unit': field.default_unit,
            'data_type': field.value_type,
            'topic': field.topic.name if field.topic else None,
            'framework': field.framework.framework_name if field.framework else None
        }

        # Add formula and dependencies for computed fields
        if field.is_computed and field.formula_expression:
            response['formula'] = field.formula_expression
            response['dependencies'] = []

            # Get dependencies from variable mappings relationship
            if field.variable_mappings:
                for mapping in field.variable_mappings:
                    if mapping.raw_field:
                        response['dependencies'].append({
                            'field_id': mapping.raw_field.field_id,
                            'field_name': mapping.raw_field.field_name,
                            'variable': mapping.variable_name,
                            'unit': mapping.raw_field.default_unit
                        })

        # Add assignment info if available
        if assignment:
            response['frequency'] = assignment.frequency
            response['is_assigned'] = True
        else:
            response['is_assigned'] = False

        return jsonify(response)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@field_api_bp.route('/field-data/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_field_data(field_id):
    """
    Get existing data for a field including notes (Enhancement #2).

    Used to pre-populate the modal when editing existing data.

    Args:
        field_id: The framework data field ID

    Query Parameters:
        entity_id (required): Entity ID
        reporting_date (required): Reporting date (YYYY-MM-DD)

    Response:
        {
            "success": true,
            "field_id": "abc-123",
            "entity_id": 1,
            "reporting_date": "2025-01-31",
            "raw_value": "85",
            "calculated_value": null,
            "notes": "Includes 5 new hires from acquisition...",
            "has_notes": true,
            "unit": "employees",
            "dimension_values": {},
            "created_at": "2025-01-12T10:30:00",
            "updated_at": "2025-01-12T14:20:00"
        }
    """
    try:
        from ...models.esg_data import ESGData
        from datetime import datetime

        # Get parameters
        entity_id = request.args.get('entity_id', type=int)
        reporting_date_str = request.args.get('reporting_date')

        if not entity_id or not reporting_date_str:
            return jsonify({
                'success': False,
                'error': 'entity_id and reporting_date are required'
            }), 400

        # Parse date
        try:
            reporting_date = datetime.strptime(reporting_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }), 400

        # Find data entry
        esg_data = ESGData.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date,
            company_id=current_user.company_id,
            is_draft=False
        ).first()

        if not esg_data:
            return jsonify({
                'success': False,
                'error': 'No data found for this field and date'
            }), 404

        return jsonify({
            'success': True,
            'data_id': esg_data.data_id,  # Enhancement #3: For file attachment linking
            'field_id': esg_data.field_id,
            'entity_id': esg_data.entity_id,
            'reporting_date': esg_data.reporting_date.isoformat(),
            'raw_value': esg_data.raw_value,
            'calculated_value': esg_data.calculated_value,
            'notes': esg_data.notes,
            'has_notes': esg_data.has_notes(),
            'unit': esg_data.effective_unit,
            'dimension_values': esg_data.dimension_values,
            'created_at': esg_data.created_at.isoformat() if esg_data.created_at else None,
            'updated_at': esg_data.updated_at.isoformat() if esg_data.updated_at else None
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@field_api_bp.route('/field-history/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_field_history(field_id):
    """
    Get historical data entries for a field.

    Args:
        field_id: The framework data field ID

    Query Parameters:
        entity_id (optional): Entity ID (defaults to current user's entity)
        limit (optional): Number of entries to return (default: 10)

    Response:
        {
            "success": true,
            "field_id": "abc-123",
            "field_name": "Employee Count",
            "history": [
                {
                    "reporting_date": "2024-01-31",
                    "value": 150,
                    "unit": "employees",
                    "has_dimensions": false,
                    "created_at": "2024-02-05T10:30:00",
                    "updated_at": "2024-02-05T10:30:00"
                }
            ],
            "total_count": 5
        }
    """
    try:
        from ...models.esg_data import ESGData
        from ...models.framework import FrameworkDataField
        from ...models.data_assignment import DataPointAssignment
        from sqlalchemy import desc

        # Get entity ID from query params or use current user's entity
        entity_id = request.args.get('entity_id', type=int)
        if not entity_id:
            entity_id = current_user.entity_id

        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'No entity context available'
            }), 400

        # Get limit from query params
        limit = request.args.get('limit', 10, type=int)
        if limit > 50:
            limit = 50  # Cap at 50 entries

        # Get field details
        field = FrameworkDataField.query.filter_by(field_id=field_id).first()
        if not field:
            return jsonify({
                'success': False,
                'error': 'Field not found'
            }), 404

        # Check if field is assigned to this entity
        assignment = DataPointAssignment.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            series_status='active'
        ).first()

        if not assignment:
            return jsonify({
                'success': False,
                'error': 'Field not assigned to this entity'
            }), 404

        # Get offset from query params (for pagination)
        offset = request.args.get('offset', 0, type=int)

        # Get total count first (for pagination info)
        total_count = ESGData.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            is_draft=False
        ).count()

        # Get historical data (exclude drafts) with pagination
        historical_entries = ESGData.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            is_draft=False
        ).order_by(
            desc(ESGData.reporting_date)
        ).limit(limit).offset(offset).all()

        # Build history list
        history = []
        for entry in historical_entries:
            # Determine value to show
            if field.is_computed:
                value = entry.calculated_value
            else:
                value = entry.raw_value

            # Check if entry has dimensional data
            has_dimensions = entry.dimension_values is not None and len(entry.dimension_values) > 0 if entry.dimension_values else False

            history.append({
                'reporting_date': entry.reporting_date.isoformat(),
                'value': value,
                'unit': entry.unit or field.default_unit,
                'has_dimensions': has_dimensions,
                'dimension_values': entry.dimension_values if has_dimensions else None,
                'notes': entry.notes,  # Enhancement #2: Include notes
                'has_notes': entry.has_notes(),  # Enhancement #2: Notes flag
                'attachments': [  # Enhancement #3: Include attachments
                    {
                        'id': att.id,
                        'filename': att.filename,
                        'file_size': att.file_size,
                        'mime_type': att.mime_type,
                        'uploaded_at': att.uploaded_at.isoformat() if att.uploaded_at else None
                    }
                    for att in entry.attachments
                ],
                'created_at': entry.created_at.isoformat() if entry.created_at else None,
                'updated_at': entry.updated_at.isoformat() if entry.updated_at else None
            })

        # Calculate if there are more entries to load
        has_more = (offset + len(history)) < total_count

        return jsonify({
            'success': True,
            'field_id': field.field_id,
            'field_name': field.field_name,
            'field_type': 'computed' if field.is_computed else 'raw_input',
            'history': history,
            'loaded_count': len(history),
            'total_count': total_count,
            'offset': offset,
            'limit': limit,
            'has_more': has_more
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@field_api_bp.route('/computed-field-details/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_computed_field_details(field_id):
    """
    Get comprehensive details for a computed field including formula,
    dependencies, and calculation result.

    Enhancement #1: Computed Field Modal - Show calculation details instead of input form.

    Args:
        field_id: The computed field ID

    Query Parameters:
        entity_id (required): Entity ID
        reporting_date (required): Reporting date (YYYY-MM-DD)

    Response:
        {
            "success": true,
            "field_id": "abc-123",
            "field_name": "Total Employee Count",
            "result": {
                "value": 150,
                "unit": "employees",
                "status": "complete",
                "calculated_at": "2025-01-12T10:30:00"
            },
            "formula": "A + B",
            "variable_mapping": {
                "A": {"field_id": "def-456", "field_name": "Male Employees"},
                "B": {"field_id": "ghi-789", "field_name": "Female Employees"}
            },
            "dependencies": [
                {
                    "field_id": "def-456",
                    "field_name": "Male Employees",
                    "variable": "A",
                    "coefficient": 1.0,
                    "value": 85,
                    "unit": "employees",
                    "status": "available",
                    "reporting_date": "2025-01-31",
                    "notes": "Includes 5 new hires..."
                }
            ],
            "missing_dependencies": []
        }

    Status Values:
        - Result Status: complete, partial, no_data, failed
        - Dependency Status: available, missing, pending

    Errors:
        400: Missing required parameters or invalid date format
        404: Field not found or not assigned to entity
        400: Field is not a computed field
        500: Server error
    """
    try:
        from ...models.framework import FrameworkDataField
        from ...models.esg_data import ESGData
        from ...models.data_assignment import DataPointAssignment
        from datetime import datetime

        # Get parameters
        entity_id = request.args.get('entity_id', type=int)
        reporting_date_str = request.args.get('reporting_date')

        if not entity_id or not reporting_date_str:
            return jsonify({
                'success': False,
                'error': 'entity_id and reporting_date are required'
            }), 400

        # Parse reporting date
        try:
            reporting_date = datetime.strptime(reporting_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }), 400

        # Get field
        field = FrameworkDataField.query.filter_by(
            field_id=field_id,
            company_id=current_user.company_id
        ).first()

        if not field:
            return jsonify({
                'success': False,
                'error': 'Field not found'
            }), 404

        # Validate field is computed
        if not field.is_computed:
            return jsonify({
                'success': False,
                'error': 'Field is not a computed field'
            }), 400

        # Check active assignment for entity
        assignment = DataPointAssignment.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            series_status='active'
        ).first()

        if not assignment:
            return jsonify({
                'success': False,
                'error': 'Field not assigned to entity'
            }), 404

        # Get ESGData for computed result
        esg_data = ESGData.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date,
            company_id=current_user.company_id
        ).first()

        # Build result object
        result = {
            'value': None,
            'unit': field.default_unit,
            'status': 'no_data',
            'calculated_at': None
        }

        if esg_data and esg_data.calculated_value is not None:
            result['value'] = esg_data.calculated_value
            result['status'] = 'complete'
            result['calculated_at'] = esg_data.updated_at.isoformat() if esg_data.updated_at else None

        # Build variable mapping for display
        variable_mapping = {}
        for mapping in field.variable_mappings:
            variable_mapping[mapping.variable_name] = {
                'field_id': mapping.raw_field_id,
                'field_name': mapping.raw_field.field_name if mapping.raw_field else 'Unknown',
                'coefficient': float(mapping.coefficient) if mapping.coefficient else 1.0
            }

        # Get dependency values and status
        dependencies = []
        missing_dependencies = []

        for mapping in field.variable_mappings:
            dep_field = mapping.raw_field
            if not dep_field:
                continue

            # Fetch ESGData for this dependency at the same reporting date
            dep_data = ESGData.query.filter_by(
                field_id=dep_field.field_id,
                entity_id=entity_id,
                reporting_date=reporting_date,
                company_id=current_user.company_id
            ).first()

            # Determine dependency status
            dep_status = 'missing'
            dep_value = None
            dep_notes = None

            if dep_data:
                if dep_data.raw_value is not None:
                    dep_status = 'available'
                    dep_value = dep_data.raw_value
                    dep_notes = dep_data.notes
                elif dep_data.calculated_value is not None:
                    dep_status = 'available'
                    dep_value = dep_data.calculated_value
                    dep_notes = dep_data.notes
                else:
                    dep_status = 'pending'

            # Build dependency info object
            dependency_info = {
                'field_id': dep_field.field_id,
                'field_name': dep_field.field_name,
                'field_type': 'computed' if dep_field.is_computed else 'raw_input',
                'variable': mapping.variable_name,
                'coefficient': float(mapping.coefficient) if mapping.coefficient else 1.0,
                'value': dep_value,
                'unit': dep_field.default_unit,
                'status': dep_status,
                'reporting_date': reporting_date.isoformat(),
                'notes': dep_notes
            }

            dependencies.append(dependency_info)

            # Track missing dependencies
            if dep_status == 'missing' or dep_status == 'pending':
                missing_dependencies.append({
                    'field_id': dep_field.field_id,
                    'field_name': dep_field.field_name,
                    'variable': mapping.variable_name
                })

        # Update result status based on dependencies
        if missing_dependencies and result['status'] == 'no_data':
            result['status'] = 'no_data'
        elif missing_dependencies:
            result['status'] = 'partial'

        # BUGFIX: Calculate value on-the-fly if all dependencies are available
        # and no pre-saved calculated value exists
        if not missing_dependencies and result['value'] is None and dependencies:
            try:
                # Build variable values dict from dependencies
                var_values = {}
                for dep in dependencies:
                    if dep['value'] is not None and dep['status'] == 'available':
                        # Apply coefficient
                        var_values[dep['variable']] = float(dep['value']) * dep['coefficient']

                # Only calculate if we have all variables
                if len(var_values) == len(dependencies):
                    # Parse and evaluate formula
                    formula = field.formula_expression
                    if formula:
                        # Replace variables with their values
                        calc_expression = formula
                        for var_name, var_value in var_values.items():
                            calc_expression = calc_expression.replace(var_name, str(var_value))

                        # Safely evaluate the expression
                        try:
                            calculated_result = eval(calc_expression, {"__builtins__": {}}, {})

                            # Apply constant multiplier if present
                            if field.constant_multiplier:
                                calculated_result *= float(field.constant_multiplier)

                            # Update result with calculated value
                            result['value'] = calculated_result
                            result['status'] = 'complete'
                            result['calculated_at'] = None  # Not saved to DB, calculated on-the-fly

                            print(f"[ComputedField] Calculated on-the-fly: {formula} = {calculated_result}")
                        except Exception as eval_error:
                            print(f"[ComputedField] Error evaluating formula '{calc_expression}': {eval_error}")
                            result['status'] = 'failed'
            except Exception as calc_error:
                print(f"[ComputedField] Error calculating value: {calc_error}")
                import traceback
                traceback.print_exc()

        return jsonify({
            'success': True,
            'field_id': field.field_id,
            'field_name': field.field_name,
            'result': result,
            'formula': field.formula_expression,
            'constant_multiplier': float(field.constant_multiplier) if field.constant_multiplier else 1.0,
            'variable_mapping': variable_mapping,
            'dependencies': dependencies,
            'missing_dependencies': missing_dependencies
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
