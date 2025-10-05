"""
Entity API
==========

API endpoints for entity management and switching in the user dashboard.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from ...decorators.auth import tenant_required_for
from ...services.user_v2.entity_service import EntityService
from ...extensions import db

entity_api_bp = Blueprint('user_v2_entity_api', __name__, url_prefix='/api/user/v2')


@entity_api_bp.route('/entities', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_entities():
    """
    Get all entities accessible by the current user.

    Response:
        {
            "success": true,
            "entities": [
                {
                    "id": 1,
                    "name": "Facility Alpha-1",
                    "type": "facility",
                    "is_current": true,
                    "parent_id": null,
                    "assignment_count": 15
                }
            ],
            "current_entity_id": 1
        }
    """
    try:
        # Get user's accessible entities
        entities = EntityService.get_user_entities(current_user.id)

        # Format response
        entity_list = []
        for entity in entities:
            # Get assignment count for this entity
            counts = EntityService.get_entity_assignment_count(entity.id)

            entity_list.append({
                'id': entity.id,
                'name': entity.name,
                'type': entity.entity_type,
                'is_current': entity.id == current_user.entity_id,
                'parent_id': entity.parent_id,
                'assignment_count': counts['total']
            })

        return jsonify({
            'success': True,
            'entities': entity_list,
            'current_entity_id': current_user.entity_id
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@entity_api_bp.route('/switch-entity', methods=['POST'])
@login_required
@tenant_required_for('ADMIN')  # Only admins can switch entities
def switch_entity():
    """
    Switch the current user's entity context.

    Request Body:
        {
            "entity_id": 2
        }

    Response:
        {
            "success": true,
            "message": "Switched to entity: Facility Alpha-2",
            "entity": {
                "id": 2,
                "name": "Facility Alpha-2",
                "type": "facility",
                "parent_id": null
            }
        }
    """
    try:
        data = request.get_json()
        entity_id = data.get('entity_id')

        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'entity_id is required'
            }), 400

        # Attempt to switch entity
        result = EntityService.switch_entity(
            user_id=current_user.id,
            entity_id=entity_id,
            session=db.session
        )

        if not result['success']:
            return jsonify(result), 403

        return jsonify(result)

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@entity_api_bp.route('/entity-hierarchy/<int:entity_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_entity_hierarchy(entity_id):
    """
    Get the hierarchical path for an entity.

    Args:
        entity_id: The entity ID

    Response:
        {
            "success": true,
            "entity_id": 3,
            "path": [
                {"id": 1, "name": "Company", "type": "company"},
                {"id": 2, "name": "Region A", "type": "region"},
                {"id": 3, "name": "Facility A1", "type": "facility"}
            ],
            "level": 3
        }
    """
    try:
        # Verify user has access to this entity
        user_entities = EntityService.get_user_entities(current_user.id)
        entity_ids = [e.id for e in user_entities]

        if entity_id not in entity_ids:
            return jsonify({
                'success': False,
                'error': 'Entity not accessible'
            }), 403

        hierarchy = EntityService.get_entity_hierarchy(entity_id)

        return jsonify({
            'success': True,
            **hierarchy
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@entity_api_bp.route('/entity-stats/<int:entity_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_entity_stats(entity_id):
    """
    Get statistics for an entity's data assignments.

    Args:
        entity_id: The entity ID

    Response:
        {
            "success": true,
            "entity_id": 1,
            "assignments": {
                "total": 25,
                "raw": 20,
                "computed": 5
            }
        }
    """
    try:
        # Verify user has access to this entity
        user_entities = EntityService.get_user_entities(current_user.id)
        entity_ids = [e.id for e in user_entities]

        if entity_id not in entity_ids:
            return jsonify({
                'success': False,
                'error': 'Entity not accessible'
            }), 403

        counts = EntityService.get_entity_assignment_count(entity_id)

        return jsonify({
            'success': True,
            'entity_id': entity_id,
            'assignments': counts
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
