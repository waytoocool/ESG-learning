from flask import request, jsonify, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime, UTC
from ...extensions import db
from ...decorators.auth import tenant_required_for
from . import user_v2_bp

@user_v2_bp.route('/api/toggle-interface', methods=['POST'])
@login_required
@tenant_required_for('USER')
def toggle_interface():
    """
    Toggle between old and new data entry interface.

    POST /user/v2/api/toggle-interface
    Body: {"useNewInterface": true/false}

    Returns:
        JSON with success status and redirect URL
    """
    try:
        data = request.get_json()
        if not data or 'useNewInterface' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing useNewInterface parameter'
            }), 400

        new_preference = data.get('useNewInterface')

        # Validate boolean value
        if not isinstance(new_preference, bool):
            return jsonify({
                'success': False,
                'error': 'useNewInterface must be a boolean'
            }), 400

        # Update user preference
        current_user.use_new_data_entry = new_preference
        db.session.commit()

        current_app.logger.info(
            f'User {current_user.id} toggled interface to {"new" if new_preference else "old"}'
        )

        # Always redirect to V2 dashboard (legacy dashboard removed)
        redirect_url = url_for('user_v2.dashboard')

        return jsonify({
            'success': True,
            'useNewInterface': new_preference,
            'redirect': redirect_url,
            'message': f'Switched to {"new" if new_preference else "old"} interface'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error toggling interface: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Failed to toggle interface: {str(e)}'
        }), 500


@user_v2_bp.route('/api/preferences', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_preferences():
    """
    Get user's current interface preferences.

    GET /user/v2/api/preferences

    Returns:
        JSON with user's current preferences
    """
    try:
        return jsonify({
            'success': True,
            'preferences': {
                'useNewInterface': current_user.use_new_data_entry,
                'userId': current_user.id,
                'userName': current_user.name,
                'userEmail': current_user.email
            }
        })
    except Exception as e:
        current_app.logger.error(f'Error fetching preferences: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Failed to fetch preferences: {str(e)}'
        }), 500
