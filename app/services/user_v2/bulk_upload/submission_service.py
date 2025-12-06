"""
Bulk Submission Service

Handles transactional submission of validated bulk upload data.
"""

from typing import Dict, List, Any
from datetime import datetime, UTC
from uuid import uuid4
import hashlib
from flask import current_app


class BulkSubmissionService:
    """Service for submitting validated bulk upload data."""

    @staticmethod
    def submit_bulk_data(
        validated_rows: List[Dict],
        filename: str,
        current_user,
        attachments: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Submit validated data in a transaction.

        Args:
            validated_rows: List of validated row dictionaries
            filename: Original filename
            current_user: Current user object
            attachments: Optional dict of {data_id: file_data}

        Returns:
            dict: {
                'success': bool,
                'batch_id': str,
                'new_entries': int,
                'updated_entries': int,
                'total': int,
                'attachments_uploaded': int,
                'error': str (if failed)
            }
        """
        from ....extensions import db
        from ....models.esg_data import ESGData, ESGDataAuditLog, ESGDataAttachment

        # Generate batch ID for grouping
        batch_id = str(uuid4())
        new_count = 0
        update_count = 0
        attachments_count = 0
        attachments = attachments or {}

        try:
            # Process each row
            for row in validated_rows:
                is_overwrite = row.get('is_overwrite', False)

                if is_overwrite:
                    # UPDATE existing entry
                    existing = ESGData.query.get(row['existing_data_id'])

                    # Create audit log for update
                    audit_log = ESGDataAuditLog(
                        data_id=existing.data_id,
                        change_type='Excel Upload Update',
                        old_value=float(existing.raw_value) if existing.raw_value else None,
                        new_value=float(row['parsed_value']) if row['parsed_value'] is not None else None,
                        changed_by=current_user.id,
                        change_metadata={
                            'source': 'bulk_upload',
                            'filename': filename,
                            'row_number': row['row_number'],
                            'batch_id': batch_id,
                            'previous_submission_date': existing.created_at.isoformat(),
                            'has_notes': bool(row.get('notes'))
                        }
                    )
                    db.session.add(audit_log)

                    # Update existing entry
                    existing.raw_value = str(row['parsed_value'])
                    existing.dimension_values = row.get('dimensions')
                    existing.notes = row.get('notes')
                    existing.updated_at = datetime.now(UTC)

                    update_count += 1

                else:
                    # CREATE new entry
                    new_entry = ESGData(
                        entity_id=row['entity_id'],
                        field_id=row['field_id'],
                        raw_value=str(row['parsed_value']),
                        reporting_date=row['reporting_date'],
                        company_id=current_user.company_id,
                        assignment_id=row['assignment_id'],
                        dimension_values=row.get('dimensions'),
                        notes=row.get('notes')
                        # is_draft defaults to False in model
                    )
                    db.session.add(new_entry)
                    db.session.flush()  # Get data_id

                    # Create audit log for new entry
                    audit_log = ESGDataAuditLog(
                        data_id=new_entry.data_id,
                        change_type='Excel Upload',
                        old_value=None,
                        new_value=float(row['parsed_value']) if row['parsed_value'] is not None else None,
                        changed_by=current_user.id,
                        change_metadata={
                            'source': 'bulk_upload',
                            'filename': filename,
                            'row_number': row['row_number'],
                            'batch_id': batch_id,
                            'has_notes': bool(row.get('notes'))
                        }
                    )
                    db.session.add(audit_log)

                    new_count += 1

                    # Handle attachment if provided
                    row_key = f"row_{row['row_number']}"
                    if row_key in attachments:
                        attachment_data = attachments[row_key]
                        attachment_count = BulkSubmissionService._save_attachment(
                            new_entry.data_id,
                            attachment_data,
                            current_user.id
                        )
                        attachments_count += attachment_count

            # Commit transaction
            db.session.commit()

            return {
                'success': True,
                'batch_id': batch_id,
                'new_entries': new_count,
                'updated_entries': update_count,
                'total': new_count + update_count,
                'attachments_uploaded': attachments_count
            }

        except Exception as e:
            # Rollback on error
            db.session.rollback()
            current_app.logger.error(f"Bulk upload submission failed: {str(e)}")

            return {
                'success': False,
                'error': str(e),
                'batch_id': batch_id,
                'new_entries': 0,
                'updated_entries': 0,
                'total': 0,
                'attachments_uploaded': 0
            }

    @staticmethod
    def _save_attachment(data_id: str, file_data, uploaded_by: int) -> int:
        """
        Save attachment file with deduplication.

        Args:
            data_id: ESGData ID
            file_data: FileStorage object or dict with file info
            uploaded_by: User ID

        Returns:
            int: 1 if saved, 0 if error
        """
        from ....extensions import db
        from ....models.esg_data import ESGDataAttachment
        import os

        try:
            # Calculate file hash for deduplication
            file_content = file_data.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            file_data.seek(0)

            # Check for existing file with same hash
            existing_attachment = ESGDataAttachment.query.filter_by(
                file_hash=file_hash,
                uploaded_by=uploaded_by
            ).first()

            if existing_attachment:
                # Reuse existing file path
                file_path = existing_attachment.file_path
            else:
                # Save new file
                upload_folder = current_app.config['UPLOAD_FOLDER']
                try:
                    os.makedirs(upload_folder, exist_ok=True)
                except OSError as e:
                    # Handle read-only filesystem (e.g., serverless environments)
                    current_app.logger.error(f"Cannot create upload directory (read-only filesystem): {str(e)}")
                    raise

                # Generate unique filename
                timestamp = datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{file_hash[:8]}_{file_data.filename}"
                file_path = os.path.join(upload_folder, unique_filename)

                # Save file
                file_data.save(file_path)

            # Create attachment record (always create new, even if file reused)
            attachment = ESGDataAttachment(
                data_id=data_id,
                filename=file_data.filename,
                file_path=file_path,
                file_size=len(file_content),
                mime_type=file_data.content_type or 'application/octet-stream',
                uploaded_by=uploaded_by,
                file_hash=file_hash
            )
            db.session.add(attachment)

            return 1

        except Exception as e:
            current_app.logger.error(f"Failed to save attachment: {str(e)}")
            return 0
