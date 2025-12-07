"""
Attachment API for User Dashboard V2
Handles file upload, download, and deletion for ESGData attachments.

Adapted from legacy upload implementation with improvements:
- Multi-tenant file structure: uploads/{company_id}/{entity_id}/
- UUID-based filenames for uniqueness
- Immediate upload on file selection
- Requires ESGData to exist before upload
"""

from flask import jsonify, request, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid
import logging

from . import user_v2_bp
from app.decorators.auth import tenant_required_for
from app.models.esg_data import ESGData, ESGDataAttachment
from app.extensions import db

logger = logging.getLogger(__name__)


def allowed_file(filename):
    """Check if file extension is allowed (from config)."""
    if not filename or '.' not in filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower()
    return extension in current_app.config.get('ALLOWED_EXTENSIONS', set())


@user_v2_bp.route('/api/upload-attachment', methods=['POST'])
@login_required
@tenant_required_for('USER')
def upload_attachment():
    """
    Upload file attachment for ESG data.

    Form Data:
        file: File to upload (required)
        data_id: ESGData data_id (required)

    Returns:
        {
            "success": true,
            "attachment_id": "uuid",
            "filename": "original_name.pdf",
            "file_size": 12345,
            "mime_type": "application/pdf"
        }

    Errors:
        400: No file provided, invalid file type, file too large, no data_id
        404: ESGData not found
        500: Server error
    """
    try:
        # Validate file in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Validate file extension
        if not allowed_file(file.filename):
            allowed = current_app.config.get('ALLOWED_EXTENSIONS', set())
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Allowed types: {", ".join(sorted(allowed))}'
            }), 400

        # Get data_id from form
        data_id = request.form.get('data_id')
        if not data_id:
            return jsonify({
                'success': False,
                'error': 'data_id is required'
            }), 400

        # Verify ESGData exists and belongs to current tenant
        esg_data = ESGData.query.filter_by(
            data_id=data_id,
            company_id=current_user.company_id
        ).first()

        if not esg_data:
            return jsonify({
                'success': False,
                'error': 'Data entry not found. Please save data before uploading attachments.'
            }), 404

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 20 * 1024 * 1024)
        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            return jsonify({
                'success': False,
                'error': f'File size exceeds maximum of {max_mb}MB'
            }), 400

        # Generate secure filename with UUID
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}_{original_filename}"

        # Create multi-tenant directory structure (as S3 key)
        # uploads/{company_id}/{entity_id}/
        # Keep consistent structure for S3 logical paths
        company_dir_key = f"{current_user.company_id}/{esg_data.entity_id}"
        
        # Save file using S3 Service
        from app.services.s3_service import get_s3_service
        s3_service = get_s3_service()
        
        # Prepare object key
        file_key = f"{company_dir_key}/{unique_filename}"
        
        # Upload
        s3_service.upload_file(file, file_key, content_type=file.content_type)
        
        # Create attachment record
        # Note: file_path now stores the S3 key (or relative local path)
        attachment = ESGDataAttachment(
            data_id=data_id,
            filename=original_filename,
            file_path=file_key,  # Store the key
            file_size=file_size,
            mime_type=file.content_type or 'application/octet-stream',
            uploaded_by=current_user.id
        )

        db.session.add(attachment)
        db.session.commit()

        logger.info(f"[Upload] File uploaded: {original_filename} ({file_size} bytes) "
                   f"for data_id={data_id} by user={current_user.id}")

        return jsonify({
            'success': True,
            'attachment_id': attachment.id,
            'filename': attachment.filename,
            'file_size': attachment.file_size,
            'mime_type': attachment.mime_type
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"[Upload] Error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_v2_bp.route('/api/attachments/<data_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_attachments(data_id):
    """
    Get all attachments for an ESGData entry.

    Args:
        data_id: ESGData data_id

    Returns:
        {
            "success": true,
            "attachments": [
                {
                    "id": "uuid",
                    "filename": "report.pdf",
                    "file_size": 12345,
                    "mime_type": "application/pdf",
                    "uploaded_at": "2025-01-12T10:30:00",
                    "uploaded_by": 1
                }
            ]
        }
    """
    try:
        # Verify ESGData exists and belongs to current tenant
        esg_data = ESGData.query.filter_by(
            data_id=data_id,
            company_id=current_user.company_id
        ).first()

        if not esg_data:
            return jsonify({
                'success': False,
                'error': 'Data entry not found'
            }), 404

        # Get attachments
        attachments = ESGDataAttachment.query.filter_by(data_id=data_id).all()

        return jsonify({
            'success': True,
            'attachments': [
                {
                    'id': att.id,
                    'filename': att.filename,
                    'file_size': att.file_size,
                    'mime_type': att.mime_type,
                    'uploaded_at': att.uploaded_at.isoformat() if att.uploaded_at else None,
                    'uploaded_by': att.uploaded_by
                }
                for att in attachments
            ]
        })

    except Exception as e:
        logger.error(f"[Get Attachments] Error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_v2_bp.route('/api/attachment/<attachment_id>', methods=['DELETE'])
@login_required
@tenant_required_for('USER')
def delete_attachment(attachment_id):
    """
    Delete an attachment.

    Permissions: Anyone with access to the ESGData can delete attachments.

    Args:
        attachment_id: Attachment ID to delete

    Returns:
        {
            "success": true,
            "message": "File deleted successfully"
        }
    """
    try:
        # Find attachment
        attachment = ESGDataAttachment.query.filter_by(id=attachment_id).first()

        if not attachment:
            return jsonify({
                'success': False,
                'error': 'Attachment not found'
            }), 404

        # Verify ESGData belongs to current tenant
        esg_data = ESGData.query.filter_by(
            data_id=attachment.data_id,
            company_id=current_user.company_id
        ).first()

        if not esg_data:
            return jsonify({
                'success': False,
                'error': 'Permission denied'
            }), 403

        # Delete file from storage (S3 or local)
        from app.services.s3_service import get_s3_service
        s3_service = get_s3_service()
        
        # Try to delete using the stored path as key
        s3_service.delete_file(attachment.file_path)
        logger.info(f"[Delete] File storage cleanup requested for: {attachment.file_path}")

        # Delete database record
        db.session.delete(attachment)
        db.session.commit()

        logger.info(f"[Delete] Attachment deleted: {attachment.filename} "
                   f"(id={attachment_id}) by user={current_user.id}")

        return jsonify({
            'success': True,
            'message': 'File deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"[Delete] Error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_v2_bp.route('/api/download-attachment/<attachment_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def download_attachment(attachment_id):
    """
    Download an attachment file.

    Args:
        attachment_id: Attachment ID to download

    Returns:
        File download response
    """
    try:
        # Find attachment
        attachment = ESGDataAttachment.query.filter_by(id=attachment_id).first()

        if not attachment:
            return jsonify({
                'success': False,
                'error': 'Attachment not found'
            }), 404

        # Verify ESGData belongs to current tenant
        esg_data = ESGData.query.filter_by(
            data_id=attachment.data_id,
            company_id=current_user.company_id
        ).first()

        if not esg_data:
            return jsonify({
                'success': False,
                'error': 'Permission denied'
            }), 403

        # Get file from S3 service
        from app.services.s3_service import get_s3_service
        s3_service = get_s3_service()
        
        try:
            file_body = s3_service.download_file(attachment.file_path)
            
            return send_file(
                file_body,
                as_attachment=True,
                download_name=attachment.filename,
                mimetype=attachment.mime_type
            )
        except Exception as e:
             logger.error(f"[Download] Storage Error: {str(e)}")
             return jsonify({
                 'success': False,
                 'error': 'File not found / Retrieval failed'
             }), 404

    except Exception as e:
        logger.error(f"[Download] Error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
