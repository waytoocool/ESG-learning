"""
Bulk Upload API Routes

Enhancement #4: Bulk Excel Upload for Overdue Data Submission
Provides API endpoints for template generation, file upload, validation, and submission.
"""

from flask import Blueprint, request, jsonify, send_file, session, current_app
from flask_login import login_required, current_user
from ...decorators.auth import tenant_required_for
from ...services.user_v2.bulk_upload import (
    TemplateGenerationService,
    FileUploadService,
    BulkValidationService,
    BulkSubmissionService,
    SessionStorageService
)
from datetime import datetime
from werkzeug.utils import secure_filename

bulk_upload_bp = Blueprint('user_v2_bulk_upload', __name__,
                           url_prefix='/api/user/v2/bulk-upload')


@bulk_upload_bp.route('/template', methods=['POST'])
@login_required
@tenant_required_for('USER')
def download_template():
    """
    Generate and download Excel template with assignments.

    Request Body:
        {
            "filter": "overdue" | "pending" | "overdue_and_pending"
        }

    Returns:
        Excel file download
    """
    try:
        data = request.get_json()
        filter_type = data.get('filter', 'pending')

        # Validate filter type
        valid_filters = ['overdue', 'pending', 'overdue_and_pending']
        if filter_type not in valid_filters:
            return jsonify({
                'success': False,
                'error': f"Invalid filter type. Must be one of: {', '.join(valid_filters)}"
            }), 400

        # Generate template
        excel_file = TemplateGenerationService.generate_template(
            user=current_user,
            filter_type=filter_type
        )

        # Create filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Template_{filter_type}_{timestamp}.xlsx"

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404

    except Exception as e:
        current_app.logger.error(f"Template generation failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate template'
        }), 500


@bulk_upload_bp.route('/upload', methods=['POST'])
@login_required
@tenant_required_for('USER')
def upload_file():
    """
    Accept Excel file upload and parse.

    Request: multipart/form-data with 'file' field

    Returns:
        {
            "success": true,
            "upload_id": "temp-abc-123",
            "total_rows": 23,
            "parsed_rows": [...],
            "filename": "uploaded_file.xlsx",
            "file_size": 245760
        }
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        # Validate file
        validation = FileUploadService.validate_file(file)
        if not validation['valid']:
            return jsonify({
                'success': False,
                'errors': validation['errors']
            }), 400

        # Parse file
        parse_result = FileUploadService.parse_file(file)

        if not parse_result['success']:
            return jsonify({
                'success': False,
                'errors': parse_result['errors']
            }), 400

        # Generate temporary upload ID for session
        upload_id = f"upload-{datetime.now().strftime('%Y%m%d%H%M%S')}-{current_user.id}"

        # Store ALL data in file storage only - DO NOT use session (FIX: BUG-ENH4-006 - session cookie size limit)
        # The base session (user auth, dashboard state) is already ~4KB, adding ANY bulk upload data causes overflow
        storage_data = {
            'rows': parse_result['rows'],
            'filename': secure_filename(file.filename),
            'uploaded_at': datetime.now().isoformat(),
            'user_id': current_user.id  # Store user_id for validation
        }
        SessionStorageService.store(upload_id, storage_data)

        return jsonify({
            'success': True,
            'upload_id': upload_id,
            'total_rows': parse_result['total_rows'],
            'filename': file.filename,
            'file_size': validation['file_size']
        })

    except Exception as e:
        current_app.logger.error(f"File upload failed: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'File upload failed: {str(e)}'
        }), 500


@bulk_upload_bp.route('/validate', methods=['POST'])
@login_required
@tenant_required_for('USER')
def validate_upload():
    """
    Validate parsed rows from upload.

    Request Body:
        {
            "upload_id": "temp-abc-123"
        }

    Returns:
        {
            "success": true/false,
            "valid": true/false,
            "total_rows": 23,
            "valid_count": 20,
            "invalid_count": 3,
            "warning_count": 5,
            "overwrite_count": 2,
            "invalid_rows": [...],
            "warning_rows": [...],
            "overwrite_rows": [...]
        }
    """
    try:
        data = request.get_json()
        upload_id = data.get('upload_id')

        if not upload_id:
            return jsonify({
                'success': False,
                'error': 'upload_id is required'
            }), 400

        # Retrieve parsed rows ONLY from file storage (FIX: BUG-ENH4-006 - no session storage)
        upload_data = SessionStorageService.retrieve(upload_id)
        if not upload_data:
            return jsonify({
                'success': False,
                'error': 'Upload session expired or invalid'
            }), 404

        # Validate user_id matches (security check)
        if upload_data.get('user_id') != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Upload session does not belong to current user'
            }), 403

        rows = upload_data.get('rows', [])

        # Reconvert date strings back to date objects (Flask session may serialize in various formats)
        from datetime import datetime
        import dateutil.parser

        for row in rows:
            if 'reporting_date' in row:
                # Handle various date formats from session serialization
                if isinstance(row['reporting_date'], str):
                    try:
                        # Try ISO format first (most common)
                        row['reporting_date'] = datetime.fromisoformat(row['reporting_date']).date()
                    except (ValueError, AttributeError):
                        try:
                            # Fall back to flexible parser for formats like 'Tue, 31 Mar 2026 00:00:00 GMT'
                            row['reporting_date'] = dateutil.parser.parse(row['reporting_date']).date()
                        except Exception as e:
                            current_app.logger.warning(
                                f"Could not parse date '{row['reporting_date']}' in row {row.get('row_number', '?')}: {str(e)}"
                            )
                            # Keep as string and let validation handle the error
                elif isinstance(row['reporting_date'], datetime):
                    # Already a datetime object
                    row['reporting_date'] = row['reporting_date'].date()
                # If it's already a date object, leave it as-is

        # Check for dimension version changes
        dim_check = BulkValidationService.check_dimension_version_changes(rows)
        if not dim_check['valid']:
            return jsonify({
                'success': False,
                'valid': False,
                'errors': dim_check['errors']
            }), 400

        # Validate and check for overwrites
        validation_result = BulkValidationService.validate_and_check_overwrites(
            rows, current_user
        )

        # Store validated rows in file storage ONLY (FIX: BUG-ENH4-006 - no session storage)
        if validation_result['valid']:
            # Convert dates to ISO format strings for JSON serialization
            for row in validation_result['valid_rows']:
                if 'reporting_date' in row and hasattr(row['reporting_date'], 'isoformat'):
                    row['reporting_date'] = row['reporting_date'].isoformat()

            # Update file storage with validation results (overwrite existing data)
            storage_data = {
                'validated_rows': validation_result['valid_rows'],
                'overwrite_rows': validation_result['overwrite_rows'],
                'filename': upload_data.get('filename'),
                'uploaded_at': upload_data.get('uploaded_at'),
                'user_id': current_user.id
            }
            SessionStorageService.store(upload_id, storage_data)

        return jsonify({
            'success': True,
            **validation_result
        })

    except Exception as e:
        current_app.logger.error(f"Validation failed: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Validation failed: {str(e)}'
        }), 500


@bulk_upload_bp.route('/submit', methods=['POST'])
@login_required
@tenant_required_for('USER')
def submit_upload():
    """
    Submit validated data and create ESGData entries.

    Request Body:
        {
            "upload_id": "temp-abc-123",
            "attachments": {
                "row_5": <file_data>,
                "row_10": <file_data>
            }
        }

    Returns:
        {
            "success": true,
            "batch_id": "batch-abc-123",
            "new_entries": 20,
            "updated_entries": 3,
            "total": 23,
            "attachments_uploaded": 2
        }
    """
    try:
        # Get upload_id from form data (multipart form for attachments)
        upload_id = request.form.get('upload_id')

        if not upload_id:
            return jsonify({
                'success': False,
                'error': 'upload_id is required'
            }), 400

        # Retrieve validated rows ONLY from file storage (FIX: BUG-ENH4-006 - no session storage)
        upload_data = SessionStorageService.retrieve(upload_id)
        if not upload_data:
            return jsonify({
                'success': False,
                'error': 'Upload session expired or invalid'
            }), 404

        # Validate user_id matches (security check)
        if upload_data.get('user_id') != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Upload session does not belong to current user'
            }), 403

        validated_rows = upload_data.get('validated_rows')
        filename = upload_data.get('filename')

        if not validated_rows:
            return jsonify({
                'success': False,
                'error': 'No validated rows found. Please validate first.'
            }), 400

        # Convert ISO format date strings back to date objects for database insertion
        from datetime import datetime, date
        for row in validated_rows:
            if 'reporting_date' in row and isinstance(row['reporting_date'], str):
                # Parse ISO format string to date object
                row['reporting_date'] = datetime.fromisoformat(row['reporting_date']).date()

        # Extract attachments from request files
        attachments = {}
        for key in request.files:
            if key.startswith('row_'):
                attachments[key] = request.files[key]

        # Submit data
        result = BulkSubmissionService.submit_bulk_data(
            validated_rows=validated_rows,
            filename=filename,
            current_user=current_user,
            attachments=attachments
        )

        # Clear file storage on success (FIX: BUG-ENH4-006 - no session storage)
        if result['success']:
            SessionStorageService.delete(upload_id)

        return jsonify(result), 200 if result['success'] else 500

    except Exception as e:
        current_app.logger.error(f"Submission failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Submission failed'
        }), 500


@bulk_upload_bp.route('/cancel', methods=['POST'])
@login_required
@tenant_required_for('USER')
def cancel_upload():
    """
    Cancel an in-progress upload and clear file storage.

    Request Body:
        {"upload_id": "temp-abc-123"}

    Returns:
        {"success": true}
    """
    try:
        data = request.get_json()
        upload_id = data.get('upload_id')

        if upload_id:
            # Delete file storage (FIX: BUG-ENH4-006 - no session storage)
            SessionStorageService.delete(upload_id)

        return jsonify({'success': True})

    except Exception as e:
        current_app.logger.error(f"Cancel failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to cancel upload'
        }), 500
