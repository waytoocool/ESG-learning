"""
Data API
========

API endpoints for historical data retrieval and data submission.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, date

from ...decorators.auth import tenant_required_for
from ...services.user_v2.historical_data_service import HistoricalDataService
from ...models.esg_data import ESGData
from ...extensions import db

data_api_bp = Blueprint('user_v2_data_api', __name__, url_prefix='/api/user/v2')


@data_api_bp.route('/historical-data/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_historical_data(field_id):
    """
    Get historical data submissions for a field.

    Args:
        field_id: The framework data field ID

    Query Parameters:
        entity_id (optional): Entity ID (defaults to current user's entity)
        start_date (optional): Start date filter (YYYY-MM-DD)
        end_date (optional): End date filter (YYYY-MM-DD)
        limit (optional): Maximum number of records (default: 50)

    Response:
        {
            "success": true,
            "field_id": "abc-123",
            "field_name": "Employee Count",
            "entity_id": 1,
            "total_count": 12,
            "data": [
                {
                    "id": "data-1",
                    "reporting_date": "2024-01-31",
                    "raw_value": 500,
                    "dimension_values": {...},
                    "status": "submitted",
                    "created_at": "2024-02-01T10:00:00Z",
                    "attachments": [...]
                }
            ]
        }
    """
    try:
        # Get parameters
        entity_id = request.args.get('entity_id', type=int)
        if not entity_id:
            entity_id = current_user.entity_id

        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'No entity context available'
            }), 400

        # Parse date filters
        start_date = None
        end_date = None

        start_date_str = request.args.get('start_date')
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid start_date format. Use YYYY-MM-DD'
                }), 400

        end_date_str = request.args.get('end_date')
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid end_date format. Use YYYY-MM-DD'
                }), 400

        limit = request.args.get('limit', 50, type=int)

        # Get historical data
        result = HistoricalDataService.get_historical_data(
            field_id=field_id,
            entity_id=entity_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
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


@data_api_bp.route('/data-summary/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_data_summary(field_id):
    """
    Get summary statistics for a field's historical data.

    Args:
        field_id: The framework data field ID

    Query Parameters:
        entity_id (optional): Entity ID (defaults to current user's entity)

    Response:
        {
            "success": true,
            "field_id": "abc-123",
            "entity_id": 1,
            "total_submissions": 12,
            "date_range": {
                "earliest": "2023-01-31",
                "latest": "2024-12-31"
            },
            "statistics": {
                "min": 450,
                "max": 550,
                "average": 500,
                "count": 12
            }
        }
    """
    try:
        # Get entity ID
        entity_id = request.args.get('entity_id', type=int)
        if not entity_id:
            entity_id = current_user.entity_id

        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'No entity context available'
            }), 400

        # Get summary
        result = HistoricalDataService.get_data_summary(
            field_id=field_id,
            entity_id=entity_id
        )

        if not result.get('success'):
            return jsonify(result), 404

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_api_bp.route('/data-by-date-range', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_data_by_date_range():
    """
    Get all data for an entity within a date range.

    Query Parameters:
        entity_id (optional): Entity ID (defaults to current user's entity)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        field_ids (optional): Comma-separated list of field IDs to filter

    Response:
        {
            "success": true,
            "entity_id": 1,
            "date_range": {
                "start": "2024-01-01",
                "end": "2024-12-31"
            },
            "data_by_date": {
                "2024-01-31": {
                    "field-1": {...},
                    "field-2": {...}
                }
            }
        }
    """
    try:
        # Get entity ID
        entity_id = request.args.get('entity_id', type=int)
        if not entity_id:
            entity_id = current_user.entity_id

        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'No entity context available'
            }), 400

        # Parse required date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if not start_date_str or not end_date_str:
            return jsonify({
                'success': False,
                'error': 'start_date and end_date are required'
            }), 400

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }), 400

        # Parse optional field IDs
        field_ids = None
        field_ids_str = request.args.get('field_ids')
        if field_ids_str:
            field_ids = [fid.strip() for fid in field_ids_str.split(',')]

        # Get data
        result = HistoricalDataService.get_data_by_date_range(
            entity_id=entity_id,
            start_date=start_date,
            end_date=end_date,
            field_ids=field_ids
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_api_bp.route('/data-completeness', methods=['GET'])
@login_required
@tenant_required_for('USER')
def check_data_completeness():
    """
    Check data completeness for a specific date.

    Query Parameters:
        entity_id (optional): Entity ID (defaults to current user's entity)
        reporting_date: The reporting date to check (YYYY-MM-DD)

    Response:
        {
            "success": true,
            "entity_id": 1,
            "reporting_date": "2024-01-31",
            "total_fields": 25,
            "submitted_count": 20,
            "missing_count": 5,
            "completeness_percentage": 80.0,
            "missing_fields": [...]
        }
    """
    try:
        # Get entity ID
        entity_id = request.args.get('entity_id', type=int)
        if not entity_id:
            entity_id = current_user.entity_id

        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'No entity context available'
            }), 400

        # Parse reporting date
        reporting_date_str = request.args.get('reporting_date')
        if not reporting_date_str:
            return jsonify({
                'success': False,
                'error': 'reporting_date is required'
            }), 400

        try:
            reporting_date = datetime.strptime(reporting_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }), 400

        # Check completeness
        result = HistoricalDataService.check_data_completeness(
            entity_id=entity_id,
            reporting_date=reporting_date
        )

        if not result.get('success'):
            return jsonify(result), 404

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
