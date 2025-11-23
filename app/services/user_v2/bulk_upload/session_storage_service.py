"""
Session Storage Service for Bulk Upload

Provides file-based storage for bulk upload data to avoid session cookie size limits.
Stores validated rows and upload metadata in temporary JSON files instead of Flask session.

BUG FIX: BUG-ENH4-005 - Session cookie exceeds 4KB browser limit
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from flask import current_app


class SessionStorageService:
    """Manages temporary file storage for bulk upload sessions."""

    @staticmethod
    def _get_storage_dir() -> Path:
        """Get or create the temporary storage directory for bulk uploads."""
        storage_dir = Path(tempfile.gettempdir()) / 'esg_bulk_uploads'
        storage_dir.mkdir(exist_ok=True)
        return storage_dir

    @staticmethod
    def _get_file_path(upload_id: str) -> Path:
        """Get the file path for a given upload_id."""
        storage_dir = SessionStorageService._get_storage_dir()
        # Sanitize upload_id to prevent path traversal
        safe_id = upload_id.replace('/', '_').replace('\\', '_')
        return storage_dir / f"{safe_id}.json"

    @staticmethod
    def store(upload_id: str, data: Dict[str, Any]) -> bool:
        """
        Store upload data to a temporary file.

        Args:
            upload_id: Unique identifier for the upload session
            data: Dictionary containing upload data (rows, metadata, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = SessionStorageService._get_file_path(upload_id)

            # Add timestamp for expiration tracking
            data['_stored_at'] = datetime.now().isoformat()

            # Convert data to JSON-serializable format
            json_data = json.dumps(data, default=str)

            # Write to file
            file_path.write_text(json_data, encoding='utf-8')

            current_app.logger.info(f"Stored upload data for {upload_id} at {file_path}")
            return True

        except Exception as e:
            current_app.logger.error(f"Failed to store upload data for {upload_id}: {str(e)}")
            return False

    @staticmethod
    def retrieve(upload_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve upload data from temporary file.

        Args:
            upload_id: Unique identifier for the upload session

        Returns:
            Dictionary containing upload data, or None if not found/expired
        """
        try:
            file_path = SessionStorageService._get_file_path(upload_id)

            if not file_path.exists():
                current_app.logger.warning(f"Upload data not found for {upload_id}")
                return None

            # Read data
            json_data = file_path.read_text(encoding='utf-8')
            data = json.loads(json_data)

            # Check expiration (30 minutes default)
            if '_stored_at' in data:
                stored_at = datetime.fromisoformat(data['_stored_at'])
                timeout = current_app.config.get('BULK_UPLOAD_SESSION_TIMEOUT', 30 * 60)
                if (datetime.now() - stored_at).total_seconds() > timeout:
                    current_app.logger.warning(f"Upload session expired for {upload_id}")
                    SessionStorageService.delete(upload_id)
                    return None

            return data

        except Exception as e:
            current_app.logger.error(f"Failed to retrieve upload data for {upload_id}: {str(e)}")
            return None

    @staticmethod
    def delete(upload_id: str) -> bool:
        """
        Delete upload data file.

        Args:
            upload_id: Unique identifier for the upload session

        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = SessionStorageService._get_file_path(upload_id)

            if file_path.exists():
                file_path.unlink()
                current_app.logger.info(f"Deleted upload data for {upload_id}")

            return True

        except Exception as e:
            current_app.logger.error(f"Failed to delete upload data for {upload_id}: {str(e)}")
            return False

    @staticmethod
    def cleanup_expired() -> int:
        """
        Clean up expired upload session files.

        Returns:
            Number of files deleted
        """
        try:
            storage_dir = SessionStorageService._get_storage_dir()
            timeout = current_app.config.get('BULK_UPLOAD_SESSION_TIMEOUT', 30 * 60)
            deleted_count = 0

            for file_path in storage_dir.glob('*.json'):
                try:
                    # Check file modification time
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if (datetime.now() - mtime).total_seconds() > timeout:
                        file_path.unlink()
                        deleted_count += 1

                except Exception as e:
                    current_app.logger.warning(f"Failed to check/delete {file_path}: {str(e)}")
                    continue

            if deleted_count > 0:
                current_app.logger.info(f"Cleaned up {deleted_count} expired upload sessions")

            return deleted_count

        except Exception as e:
            current_app.logger.error(f"Failed to cleanup expired sessions: {str(e)}")
            return 0
