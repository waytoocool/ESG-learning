"""
File Upload Service

Handles file upload, validation, and parsing for bulk Excel uploads.
"""

import pandas as pd
from typing import Dict, List, Any
from werkzeug.datastructures import FileStorage
from datetime import datetime
from flask import current_app

# Try to import python-magic for MIME type validation (optional)
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False


class FileUploadService:
    """Service for handling Excel/CSV file uploads and parsing."""

    @staticmethod
    def validate_file(file: FileStorage) -> Dict[str, Any]:
        """
        Validate uploaded file before parsing.

        Args:
            file: Uploaded file object

        Returns:
            dict: {'valid': bool, 'errors': List[str]}
        """
        errors = []

        # Check filename exists
        if not file or not file.filename:
            errors.append("No file provided")
            return {'valid': False, 'errors': errors}

        # Check file extension
        filename = file.filename.lower()
        allowed_formats = current_app.config.get('BULK_UPLOAD_ALLOWED_FORMATS', {'.xlsx', '.xls', '.csv'})

        if not any(filename.endswith(ext) for ext in allowed_formats):
            errors.append(
                f"Invalid file format. Supported formats: {', '.join(allowed_formats)}"
            )

        # MIME type validation (if python-magic available)
        if MAGIC_AVAILABLE:
            try:
                # Read first 2KB for MIME detection
                file_content = file.read(2048)
                file.seek(0)  # Reset file pointer

                # Detect MIME type
                mime_type = magic.from_buffer(file_content, mime=True)

                # Allowed MIME types
                allowed_mime_types = {
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
                    'application/vnd.ms-excel',  # .xls
                    'text/csv',  # .csv
                    'application/csv',  # .csv (alternative)
                    'text/plain',  # .csv (some systems detect as plain text)
                    'application/zip',  # .xlsx (xlsx is a zip file)
                }

                if mime_type not in allowed_mime_types:
                    errors.append(
                        f"Invalid file type detected: '{mime_type}'. "
                        "Only Excel (.xlsx, .xls) and CSV files are supported. "
                        "File may be corrupted or renamed."
                    )
                    current_app.logger.warning(f"MIME type validation failed: {mime_type} for file {filename}")

            except Exception as e:
                # If MIME detection fails, log warning but continue with extension validation
                current_app.logger.warning(f"MIME type detection failed: {e}")
        else:
            # Log that MIME validation is skipped (library not installed)
            current_app.logger.info("python-magic not available, skipping MIME type validation")

        # Check file size (read file size)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        max_size = current_app.config.get('BULK_UPLOAD_MAX_FILE_SIZE', 5 * 1024 * 1024)
        if file_size > max_size:
            errors.append(
                f"File exceeds {max_size // (1024*1024)}MB limit (current: {file_size // (1024*1024)}MB)"
            )

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'file_size': file_size
        }

    @staticmethod
    def parse_file(file: FileStorage) -> Dict[str, Any]:
        """
        Parse Excel/CSV file and extract rows.

        Args:
            file: Uploaded file object

        Returns:
            dict: {
                'success': bool,
                'rows': List[dict],
                'total_rows': int,
                'errors': List[str]
            }
        """
        errors = []
        rows = []

        try:
            filename = file.filename.lower()

            # Parse based on file type
            if filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:  # .xlsx or .xls
                df = pd.read_excel(file, sheet_name='Data Entry')

            # Validate required columns exist
            required_cols = ['Field_ID', 'Entity_ID', 'Assignment_ID', 'Field_Name', 'Rep_Date']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                errors.append(
                    f"Template missing required columns: {', '.join(missing_cols)}. "
                    "Please download a fresh template."
                )
                return {
                    'success': False,
                    'rows': [],
                    'total_rows': 0,
                    'errors': errors
                }

            # Check max rows limit
            max_rows = current_app.config.get('BULK_UPLOAD_MAX_ROWS', 1000)
            if len(df) > max_rows:
                errors.append(f"Maximum {max_rows} rows allowed (found {len(df)} rows)")
                return {
                    'success': False,
                    'rows': [],
                    'total_rows': len(df),
                    'errors': errors
                }

            # Parse each row
            for idx, row in df.iterrows():
                try:
                    parsed_row = FileUploadService._parse_row(row, idx + 2)  # +2 for Excel row number
                    if parsed_row:
                        rows.append(parsed_row)
                except Exception as e:
                    errors.append(f"Row {idx + 2}: {str(e)}")

            # Check if any rows were parsed
            if not rows and not errors:
                errors.append("No data rows found in file")

            return {
                'success': len(errors) == 0,
                'rows': rows,
                'total_rows': len(rows),
                'errors': errors
            }

        except Exception as e:
            errors.append(f"Failed to parse file: {str(e)}")
            return {
                'success': False,
                'rows': [],
                'total_rows': 0,
                'errors': errors
            }

    @staticmethod
    def _parse_row(row, row_number: int) -> Dict:
        """
        Parse a single row from the DataFrame.

        Args:
            row: pandas Series (row)
            row_number: Excel row number (for error reporting)

        Returns:
            dict: Parsed row data
        """
        # Extract dimension columns
        dimensions = {}
        for col in row.index:
            if col.startswith('Dimension_'):
                dim_name = col.replace('Dimension_', '')
                dim_value = row[col]

                # Only include non-empty dimension values
                if pd.notna(dim_value) and str(dim_value).strip() != '':
                    dimensions[dim_name.lower()] = str(dim_value).strip()

        # Parse reporting date
        rep_date = row['Rep_Date']
        if pd.notna(rep_date) and str(rep_date).strip() not in ['', 'N/A', 'None']:
            try:
                if isinstance(rep_date, pd.Timestamp):
                    reporting_date = rep_date.date()
                elif isinstance(rep_date, datetime):
                    reporting_date = rep_date.date()
                else:
                    # Try parsing string
                    reporting_date = pd.to_datetime(str(rep_date)).date()
            except Exception as e:
                raise ValueError(f"Invalid reporting date format: {rep_date}. Expected YYYY-MM-DD")
        else:
            raise ValueError("Reporting date is missing or empty")

        # Build row dictionary
        parsed_row = {
            'row_number': row_number,
            'field_id': str(row['Field_ID']).strip() if pd.notna(row['Field_ID']) else None,
            'field_name': str(row['Field_Name']).strip() if pd.notna(row['Field_Name']) else '',
            'entity_id': int(row['Entity_ID']) if pd.notna(row['Entity_ID']) else None,
            'assignment_id': str(row['Assignment_ID']).strip() if pd.notna(row['Assignment_ID']) else None,
            'reporting_date': reporting_date,
            'value': row['Value'] if pd.notna(row['Value']) else None,
            'dimensions': dimensions if dimensions else None,
            'notes': str(row['Notes']).strip() if pd.notna(row.get('Notes')) and str(row.get('Notes')).strip() != '' else None
        }

        # Validate required fields
        if not parsed_row['field_id']:
            raise ValueError("Field_ID is missing")
        if not parsed_row['entity_id']:
            raise ValueError("Entity_ID is missing")
        if not parsed_row['assignment_id']:
            raise ValueError("Assignment_ID is missing")

        return parsed_row
