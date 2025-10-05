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
