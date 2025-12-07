"""
Support and Issue Reporting API Endpoints.

This module provides RESTful API endpoints for the bug reporting and support system.
Users can submit issue reports, view their reports, and track issue status.

All endpoints require authentication and respect multi-tenant isolation.

Endpoints:
- POST /api/support/report - Submit a new issue report
- GET /api/support/reports - List user's issue reports
- GET /api/support/report/<ticket_number> - Get specific report details
- POST /api/support/upload-screenshot - Upload a screenshot file
"""

import os
import base64
import uuid
from datetime import datetime, UTC
from flask import Blueprint, request, jsonify, current_app, g
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models.issue_report import IssueReport, IssueComment
from ..services.github_service import get_github_service
from ..services.email import send_issue_confirmation_email

# Create blueprint
support_bp = Blueprint('support', __name__, url_prefix='/api/support')

# File upload configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_SCREENSHOT_SIZE_MB = int(os.getenv('MAX_SCREENSHOT_SIZE_MB', '10'))
MAX_SCREENSHOT_SIZE_BYTES = MAX_SCREENSHOT_SIZE_MB * 1024 * 1024


def allowed_file(filename):
    """
    Check if file extension is allowed for screenshot uploads.

    Args:
        filename (str): Name of the file to check

    Returns:
        bool: True if extension is allowed
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_screenshot(base64_data, ticket_number):
    """
    Save base64-encoded screenshot to S3.

    Args:
        base64_data (str): Base64 encoded image data (with or without data URI prefix)
        ticket_number (str): Ticket number for filename

    Returns:
        str: Storage key/path

    Raises:
        ValueError: If base64 data is invalid or file size exceeds limit
    """
    try:
        from io import BytesIO
        from app.services.s3_service import get_s3_service
        
        # Remove data URI prefix if present
        if ',' in base64_data:
            base64_data = base64_data.split(',', 1)[1]

        # Decode base64 data
        image_data = base64.b64decode(base64_data)

        # Check file size
        if len(image_data) > MAX_SCREENSHOT_SIZE_BYTES:
            raise ValueError(
                f"Screenshot size ({len(image_data) / 1024 / 1024:.2f}MB) "
                f"exceeds maximum allowed size ({MAX_SCREENSHOT_SIZE_MB}MB)"
            )
            
        file_io = BytesIO(image_data)

        # Generate unique filename/key
        file_id = str(uuid.uuid4())[:8]
        filename = f"{ticket_number}_{file_id}.png"
        
        # S3 key format: screenshots/BUG-YYYY-XXXX_abcdef.png
        key = f"screenshots/{filename}"

        # Upload using service
        s3 = get_s3_service()
        s3.upload_file(file_io, key, content_type='image/png')

        # Return key (matches what we stored essentially)
        return key

    except Exception as e:
        current_app.logger.error(f"Failed to save screenshot: {str(e)}")
        raise ValueError(f"Failed to save screenshot: {str(e)}")


@support_bp.route('/report', methods=['POST'])
@login_required
def submit_report():
    """
    Submit a new issue report.

    Request Body (JSON):
        {
            "category": "bug|feature_request|help|other",
            "severity": "critical|high|medium|low",
            "title": "string (required)",
            "description": "string (required)",
            "steps_to_reproduce": "string (optional)",
            "expected_behavior": "string (optional)",
            "actual_behavior": "string (optional)",
            "browser_info": {...},
            "page_url": "string",
            "page_title": "string",
            "viewport_size": "1920x1080",
            "screen_resolution": "2560x1440",
            "console_errors": [...],
            "api_history": [...],
            "user_actions": [...],
            "local_storage_data": {...},
            "session_storage_data": {...},
            "screenshot_data": "base64_string",
            "screenshot_annotations": [...]
        }

    Returns:
        JSON: {
            "success": true,
            "ticket_number": "BUG-2025-0001",
            "message": "Your issue has been reported successfully"
        }

    Status Codes:
        200: Issue created successfully
        400: Invalid request data
        500: Server error
    """
    try:
        # Get request data
        data = request.get_json()

        # Validate required fields
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        if not data.get('title'):
            return jsonify({
                'success': False,
                'error': 'Title is required'
            }), 400

        if not data.get('description'):
            return jsonify({
                'success': False,
                'error': 'Description is required'
            }), 400

        # Validate category
        valid_categories = ['bug', 'feature_request', 'help', 'other']
        category = data.get('category', 'bug')
        if category not in valid_categories:
            return jsonify({
                'success': False,
                'error': f'Invalid category. Must be one of: {", ".join(valid_categories)}'
            }), 400

        # Validate severity
        valid_severities = ['critical', 'high', 'medium', 'low']
        severity = data.get('severity', 'medium')
        if severity not in valid_severities:
            return jsonify({
                'success': False,
                'error': f'Invalid severity. Must be one of: {", ".join(valid_severities)}'
            }), 400

        # Generate unique ticket number
        ticket_number = IssueReport.generate_ticket_number()

        # Create issue report
        issue = IssueReport(
            ticket_number=ticket_number,
            category=category,
            severity=severity,
            title=data.get('title'),
            description=data.get('description'),
            steps_to_reproduce=data.get('steps_to_reproduce'),
            expected_behavior=data.get('expected_behavior'),
            actual_behavior=data.get('actual_behavior'),
            user_id=current_user.id,
            company_id=current_user.company_id,
            browser_info=data.get('browser_info'),
            page_url=data.get('page_url'),
            page_title=data.get('page_title'),
            viewport_size=data.get('viewport_size'),
            screen_resolution=data.get('screen_resolution'),
            console_errors=data.get('console_errors'),
            api_history=data.get('api_history'),
            user_actions=data.get('user_actions'),
            local_storage_data=data.get('local_storage_data'),
            session_storage_data=data.get('session_storage_data'),
            screenshot_annotations=data.get('screenshot_annotations'),
            status='new',
            github_sync_status='pending'
        )

        # Save screenshot if provided
        if data.get('screenshot_data'):
            try:
                screenshot_path = save_screenshot(data['screenshot_data'], ticket_number)
                issue.screenshot_path = screenshot_path
            except ValueError as e:
                current_app.logger.warning(f"Failed to save screenshot for {ticket_number}: {str(e)}")
                # Continue without screenshot - don't fail the entire request

        # Save to database
        db.session.add(issue)
        db.session.commit()

        current_app.logger.info(
            f"Issue report {ticket_number} created by user {current_user.id} "
            f"(company: {current_user.company_id})"
        )

        # Sync to GitHub (best effort - don't fail if GitHub sync fails)
        try:
            github_service = get_github_service()
            github_result = github_service.create_issue(issue)
            if github_result['success']:
                current_app.logger.info(
                    f"Successfully synced {ticket_number} to GitHub issue "
                    f"#{github_result['issue_number']}"
                )
        except Exception as e:
            current_app.logger.error(
                f"Failed to sync {ticket_number} to GitHub: {str(e)}. "
                f"Issue saved to database but GitHub sync failed."
            )

        # Send confirmation email (best effort - don't fail if email fails)
        try:
            send_issue_confirmation_email(issue)
            current_app.logger.info(f"Confirmation email sent for {ticket_number}")
        except Exception as e:
            current_app.logger.error(
                f"Failed to send confirmation email for {ticket_number}: {str(e)}"
            )

        return jsonify({
            'success': True,
            'ticket_number': ticket_number,
            'message': 'Your issue has been reported successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating issue report: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while submitting your report'
        }), 500


@support_bp.route('/reports', methods=['GET'])
@login_required
def list_reports():
    """
    List user's issue reports with pagination and filtering.

    Query Parameters:
        - page: int (default: 1) - Page number
        - per_page: int (default: 20, max: 100) - Items per page
        - status: string (optional) - Filter by status

    Returns:
        JSON: {
            "success": true,
            "reports": [...],
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total": 50,
                "pages": 3
            }
        }

    Status Codes:
        200: Success
        400: Invalid parameters
        500: Server error
    """
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')

        # Validate pagination parameters
        if page < 1:
            return jsonify({
                'success': False,
                'error': 'Page must be >= 1'
            }), 400

        if per_page < 1 or per_page > 100:
            return jsonify({
                'success': False,
                'error': 'per_page must be between 1 and 100'
            }), 400

        # Build query - only show user's own reports (tenant-scoped)
        query = IssueReport.query.filter_by(
            user_id=current_user.id,
            company_id=current_user.company_id
        )

        # Apply status filter if provided
        if status_filter:
            valid_statuses = ['new', 'in_review', 'assigned', 'in_progress', 'resolved', 'closed']
            if status_filter not in valid_statuses:
                return jsonify({
                    'success': False,
                    'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
                }), 400
            query = query.filter_by(status=status_filter)

        # Order by created_at descending (newest first)
        query = query.order_by(IssueReport.created_at.desc())

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # Format reports
        reports = [{
            'id': report.id,
            'ticket_number': report.ticket_number,
            'category': report.category,
            'severity': report.severity,
            'status': report.status,
            'title': report.title,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'updated_at': report.updated_at.isoformat() if report.updated_at else None,
            'github_issue_url': report.github_issue_url
        } for report in pagination.items]

        return jsonify({
            'success': True,
            'reports': reports,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error listing issue reports: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while fetching reports'
        }), 500


@support_bp.route('/report/<ticket_number>', methods=['GET'])
@login_required
def get_report(ticket_number):
    """
    Get details of a specific issue report.

    Args:
        ticket_number (str): The ticket number (e.g., BUG-2025-0001)

    Returns:
        JSON: {
            "success": true,
            "report": {...}
        }

    Status Codes:
        200: Success
        403: User doesn't have access to this report
        404: Report not found
        500: Server error
    """
    try:
        # Find report by ticket number
        report = IssueReport.query.filter_by(ticket_number=ticket_number).first()

        if not report:
            return jsonify({
                'success': False,
                'error': 'Report not found'
            }), 404

        # Verify user has access (must be their own report and same company)
        if report.user_id != current_user.id or report.company_id != current_user.company_id:
            current_app.logger.warning(
                f"User {current_user.id} attempted to access report {ticket_number} "
                f"belonging to user {report.user_id}"
            )
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403

        # Return full report details
        return jsonify({
            'success': True,
            'report': report.to_dict()
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error fetching issue report {ticket_number}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while fetching the report'
        }), 500


@support_bp.route('/upload-screenshot', methods=['POST'])
@login_required
def upload_screenshot():
    """
    Upload a screenshot file.

    Request:
        - Multipart form data
        - File field: 'screenshot'
        - Allowed extensions: png, jpg, jpeg, gif, webp
        - Max size: 10MB (configurable)

    Returns:
        JSON: {
            "success": true,
            "filename": "uuid.png",
            "path": "screenshots/uuid.png"
        }

    Status Codes:
        200: Success
        400: Invalid file or missing file
        413: File too large
        500: Server error
    """
    try:
        # Check if file is present
        if 'screenshot' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['screenshot']

        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_SCREENSHOT_SIZE_BYTES:
            return jsonify({
                'success': False,
                'error': f'File size ({file_size / 1024 / 1024:.2f}MB) exceeds maximum '
                        f'allowed size ({MAX_SCREENSHOT_SIZE_MB}MB)'
            }), 413

        # Generate unique filename
        file_id = str(uuid.uuid4())[:8]
        extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"temp_{file_id}.{extension}"
        
        # S3 key
        key = f"screenshots/{filename}"

        # Upload using service
        from app.services.s3_service import get_s3_service
        s3 = get_s3_service()
        s3.upload_file(file, key, content_type=file.content_type)

        current_app.logger.info(
            f"Screenshot uploaded by user {current_user.id}: {filename} "
            f"({file_size / 1024:.2f}KB)"
        )

        # Return path (key)
        relative_path = key

        return jsonify({
            'success': True,
            'filename': filename,
            'path': relative_path
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error uploading screenshot: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while uploading the screenshot'
        }), 500
