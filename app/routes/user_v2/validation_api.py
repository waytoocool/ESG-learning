"""
Validation API Blueprint

Provides endpoints for automated data validation:
- /api/user/validate-submission - Validate data before submission

Author: Claude Code
Date: 2025-11-21
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ...services.validation_service import ValidationService
from ...models import ESGData, ESGDataAuditLog, Company
from ...extensions import db
from datetime import datetime, date

validation_api = Blueprint('validation_api', __name__)


@validation_api.route('/api/user/validate-submission', methods=['POST'])
@login_required
def validate_submission():
    """
    Validate ESG data submission before saving.

    Request Body:
        {
            "field_id": "abc-123",
            "entity_id": 1,
            "value": 1500,
            "reporting_date": "2024-12-31",
            "assignment_id": "def-456",  // optional
            "dimension_values": {"gender": "Male"},  // optional
            "has_attachments": true
        }

    Response:
        {
            "success": true,
            "validation": {
                "passed": false,
                "risk_score": 35,
                "flags": [
                    {
                        "type": "trend_variance",
                        "severity": "warning",
                        "message": "Value increased 25% vs Nov 2024",
                        "details": {...}
                    }
                ],
                "timestamp": "2024-12-31T10:30:00Z"
            }
        }

    Error Response:
        {
            "success": false,
            "error": "Error message"
        }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['field_id', 'entity_id', 'value', 'reporting_date']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return jsonify({
                'success': False,
                'error': f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Parse reporting_date
        try:
            if isinstance(data['reporting_date'], str):
                reporting_date = datetime.strptime(data['reporting_date'], '%Y-%m-%d').date()
            else:
                reporting_date = data['reporting_date']
        except (ValueError, TypeError) as e:
            return jsonify({
                'success': False,
                'error': f"Invalid reporting_date format. Expected YYYY-MM-DD: {str(e)}"
            }), 400

        # Parse value
        try:
            value = float(data['value'])
        except (ValueError, TypeError) as e:
            return jsonify({
                'success': False,
                'error': f"Invalid value format. Expected number: {str(e)}"
            }), 400

        # Get company_id from current user
        if not current_user.company_id:
            return jsonify({
                'success': False,
                'error': "User must be associated with a company"
            }), 403

        # Prepare attachments list
        attachments = []
        if data.get('has_attachments'):
            attachments = [{'exists': True}]  # Placeholder for validation

        # Run validation
        validation_result = ValidationService.validate_submission(
            field_id=data['field_id'],
            entity_id=int(data['entity_id']),
            value=value,
            reporting_date=reporting_date,
            company_id=current_user.company_id,
            assignment_id=data.get('assignment_id'),
            dimension_values=data.get('dimension_values'),
            attachments=attachments
        )

        # Log validation in audit trail (if warnings present)
        if not validation_result['passed']:
            try:
                # Create audit log entry for validation warning
                audit_log = ESGDataAuditLog(
                    data_id=data.get('data_id', 'pending'),  # If updating existing data
                    change_type='Validation_Warning',
                    changed_by=current_user.id,
                    old_value=None,
                    new_value=value,
                    change_metadata={
                        'field_id': data['field_id'],
                        'entity_id': data['entity_id'],
                        'reporting_date': reporting_date.isoformat(),
                        'validation_risk_score': validation_result['risk_score'],
                        'warning_count': len([f for f in validation_result['flags']
                                            if f.get('severity') == 'warning']),
                        'error_count': len([f for f in validation_result['flags']
                                          if f.get('severity') == 'error'])
                    }
                )
                db.session.add(audit_log)
                db.session.commit()
            except Exception as e:
                # Don't fail validation if audit logging fails
                print(f"[validation_api] Audit log failed: {str(e)}")
                db.session.rollback()

        return jsonify({
            'success': True,
            'validation': validation_result
        })

    except Exception as e:
        db.session.rollback()
        print(f"[validation_api] Validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Validation failed: {str(e)}"
        }), 500


@validation_api.route('/api/user/validation-stats', methods=['GET'])
@login_required
def get_validation_stats():
    """
    Get validation statistics for current user's company.

    Query Parameters:
        - days: Number of days to look back (default: 30)

    Response:
        {
            "success": true,
            "stats": {
                "total_validations": 150,
                "passed": 120,
                "warnings": 25,
                "errors": 5,
                "avg_risk_score": 12.5,
                "period_days": 30
            }
        }
    """
    try:
        days = int(request.args.get('days', 30))

        if not current_user.company_id:
            return jsonify({
                'success': False,
                'error': "User must be associated with a company"
            }), 403

        # Get validation audit logs for the period
        from datetime import datetime, timedelta, UTC

        start_date = datetime.now(UTC) - timedelta(days=days)

        validation_logs = ESGDataAuditLog.query.filter(
            ESGDataAuditLog.change_type.in_(['Validation_Warning', 'Validation_Passed']),
            ESGDataAuditLog.change_date >= start_date
        ).all()

        total_validations = len(validation_logs)
        warnings = len([log for log in validation_logs
                       if log.change_type == 'Validation_Warning'])
        passed = total_validations - warnings

        # Calculate average risk score
        risk_scores = []
        for log in validation_logs:
            if log.change_metadata and 'validation_risk_score' in log.change_metadata:
                risk_scores.append(log.change_metadata['validation_risk_score'])

        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0

        return jsonify({
            'success': True,
            'stats': {
                'total_validations': total_validations,
                'passed': passed,
                'warnings': warnings,
                'errors': 0,  # Not tracking errors separately yet
                'avg_risk_score': round(avg_risk_score, 2),
                'period_days': days
            }
        })

    except Exception as e:
        print(f"[validation_api] Stats error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Failed to get stats: {str(e)}"
        }), 500
