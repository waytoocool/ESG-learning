"""
Draft API for User V2
=====================

REST API endpoints for draft management.

Endpoints:
- POST /api/user/v2/save-draft - Save draft data
- GET /api/user/v2/get-draft/<field_id> - Retrieve draft
- DELETE /api/user/v2/discard-draft/<draft_id> - Discard draft
- GET /api/user/v2/list-drafts - List user's drafts
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.services.user_v2.draft_service import DraftService
from app.decorators.auth import tenant_required
import logging

logger = logging.getLogger(__name__)

# Create blueprint
draft_api_bp = Blueprint('draft_api', __name__, url_prefix='/api/user/v2')


@draft_api_bp.route('/save-draft', methods=['POST'])
@login_required
@tenant_required
def save_draft():
    """
    Save draft data for a field entry.

    Request Body:
        {
            "field_id": 123,
            "entity_id": 456,
            "reporting_date": "2025-01-15",
            "form_data": {
                "value": "1234.56",
                "notes": "Draft notes",
                "confidence": "MEDIUM",
                "dimensional_data": {...},
                "context_data": {...}
            }
        }

    Response:
        {
            "success": true,
            "draft_id": 789,
            "timestamp": "2025-01-15T10:30:00",
            "message": "Draft saved successfully"
        }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['field_id', 'entity_id', 'reporting_date', 'form_data']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'Missing required fields: field_id, entity_id, reporting_date, form_data'
            }), 400

        # Extract parameters
        field_id = data['field_id']
        entity_id = data['entity_id']
        reporting_date = data['reporting_date']
        form_data = data['form_data']

        # Call service
        result = DraftService.save_draft(
            user_id=current_user.id,
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date,
            form_data=form_data,
            company_id=current_user.company_id
        )

        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error in save_draft endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500


@draft_api_bp.route('/get-draft/<field_id>', methods=['GET'])
@login_required
@tenant_required
def get_draft(field_id):
    """
    Retrieve draft for a specific field/entity/date combination.

    Path Parameters:
        - field_id: str (UUID string, required)

    Query Parameters:
        - entity_id: int (required)
        - reporting_date: str (required, YYYY-MM-DD format)

    Response:
        {
            "has_draft": true,
            "draft_id": "uuid-string",
            "draft_data": {
                "raw_value": "1234.56",
                "calculated_value": 1234.56,
                "unit": "kWh",
                "dimension_values": {...}
            },
            "timestamp": "2025-01-15T10:30:00",
            "age_minutes": 5.2
        }
    """
    try:
        # Get query parameters
        entity_id = request.args.get('entity_id', type=int)
        reporting_date = request.args.get('reporting_date')

        if not entity_id or not reporting_date:
            return jsonify({
                'has_draft': False,
                'message': 'Missing required parameters: entity_id, reporting_date'
            }), 400

        # Call service
        result = DraftService.get_draft(
            user_id=current_user.id,
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date,
            company_id=current_user.company_id
        )

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error in get_draft endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'has_draft': False,
            'message': f'Internal server error: {str(e)}'
        }), 500


@draft_api_bp.route('/discard-draft/<draft_id>', methods=['DELETE'])
@login_required
@tenant_required
def discard_draft(draft_id):
    """
    Discard a draft by ID.

    Path Parameters:
        - draft_id: str (UUID string, required)

    Response:
        {
            "success": true,
            "message": "Draft discarded successfully"
        }
    """
    try:
        # Call service
        result = DraftService.discard_draft(
            draft_id=draft_id,
            user_id=current_user.id,
            company_id=current_user.company_id
        )

        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error in discard_draft endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500


@draft_api_bp.route('/list-drafts', methods=['GET'])
@login_required
@tenant_required
def list_drafts():
    """
    List all drafts for the current user.

    Query Parameters:
        - entity_id: int (optional, filter by entity)
        - limit: int (optional, default 50)

    Response:
        {
            "success": true,
            "drafts": [
                {
                    "draft_id": 789,
                    "field_id": 123,
                    "field_name": "Total Energy Consumption",
                    "entity_id": 456,
                    "entity_name": "Main Office",
                    "reporting_date": "2025-01-15",
                    "updated_at": "2025-01-15T10:30:00",
                    "age_minutes": 5.2,
                    "has_value": true
                }
            ],
            "count": 1
        }
    """
    try:
        # Get query parameters
        entity_id = request.args.get('entity_id', type=int)
        limit = request.args.get('limit', default=50, type=int)

        # Call service
        result = DraftService.list_drafts(
            user_id=current_user.id,
            company_id=current_user.company_id,
            entity_id=entity_id,
            limit=limit
        )

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error in list_drafts endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'drafts': [],
            'count': 0,
            'message': f'Internal server error: {str(e)}'
        }), 500


@draft_api_bp.route('/promote-draft/<draft_id>', methods=['POST'])
@login_required
@tenant_required
def promote_draft(draft_id):
    """
    Promote a draft to actual data (when form is submitted).

    Path Parameters:
        - draft_id: str (UUID string, required)

    Response:
        {
            "success": true,
            "data_id": "uuid-string",
            "message": "Draft promoted to data successfully"
        }
    """
    try:
        # Call service
        result = DraftService.promote_draft_to_data(
            draft_id=draft_id,
            user_id=current_user.id,
            company_id=current_user.company_id
        )

        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error in promote_draft endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500


# Export blueprint
__all__ = ['draft_api_bp']
