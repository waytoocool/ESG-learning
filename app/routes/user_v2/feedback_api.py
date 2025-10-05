from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, UTC
from ...extensions import db
from ...models.user_feedback import UserFeedback
from ...decorators.auth import tenant_required_for
from . import user_v2_bp

@user_v2_bp.route('/api/feedback', methods=['POST'])
@login_required
@tenant_required_for('USER')
def submit_feedback():
    """
    Submit user feedback about the interface.

    POST /user/v2/api/feedback
    Body: {
        "interfaceVersion": "legacy" or "modal",
        "feedbackType": "bug", "suggestion", "praise", "other",
        "message": "Feedback text"
    }

    Returns:
        JSON with success status
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing request body'
            }), 400

        # Validate required fields
        interface_version = data.get('interfaceVersion')
        feedback_type = data.get('feedbackType')
        message = data.get('message')

        if not interface_version:
            return jsonify({
                'success': False,
                'error': 'interfaceVersion is required'
            }), 400

        if not message or not message.strip():
            return jsonify({
                'success': False,
                'error': 'message is required and cannot be empty'
            }), 400

        # Validate interface version
        valid_versions = ['legacy', 'modal']
        if interface_version not in valid_versions:
            return jsonify({
                'success': False,
                'error': f'interfaceVersion must be one of {valid_versions}'
            }), 400

        # Validate feedback type (optional, but validate if provided)
        valid_types = ['bug', 'suggestion', 'praise', 'other']
        if feedback_type and feedback_type not in valid_types:
            return jsonify({
                'success': False,
                'error': f'feedbackType must be one of {valid_types}'
            }), 400

        # Create feedback record
        feedback = UserFeedback(
            user_id=current_user.id,
            interface_version=interface_version,
            feedback_type=feedback_type or 'other',
            message=message.strip()
        )

        db.session.add(feedback)
        db.session.commit()

        current_app.logger.info(
            f'Feedback submitted by user {current_user.id} for {interface_version} interface'
        )

        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback!',
            'feedbackId': feedback.id
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error submitting feedback: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Failed to submit feedback: {str(e)}'
        }), 500


@user_v2_bp.route('/api/feedback', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_user_feedback():
    """
    Get current user's feedback history.

    GET /user/v2/api/feedback

    Returns:
        JSON with list of user's feedback
    """
    try:
        feedback_list = UserFeedback.query.filter_by(
            user_id=current_user.id
        ).order_by(UserFeedback.created_at.desc()).all()

        return jsonify({
            'success': True,
            'feedback': [f.to_dict() for f in feedback_list],
            'count': len(feedback_list)
        })

    except Exception as e:
        current_app.logger.error(f'Error fetching feedback: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Failed to fetch feedback: {str(e)}'
        }), 500
