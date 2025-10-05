"""
Historical Data Service
=======================

Business logic for querying and retrieving historical ESG data submissions.
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...models.esg_data import ESGData, ESGDataAttachment
from ...models.framework import FrameworkDataField
from ...models.data_assignment import DataPointAssignment
from ...extensions import db


class HistoricalDataService:
    """Service for managing historical data queries."""

    @staticmethod
    def get_historical_data(
        field_id: str,
        entity_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50,
        session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Get historical data submissions for a field and entity.

        Args:
            field_id: The field ID
            entity_id: The entity ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of records to return
            session: Optional database session

        Returns:
            Dict with historical data and metadata
        """
        if session is None:
            session = db.session

        # Verify field and assignment exist
        field = FrameworkDataField.query.get(field_id)
        if not field:
            return {
                'success': False,
                'error': 'Field not found'
            }

        assignment = DataPointAssignment.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            series_status='active'
        ).first()

        if not assignment:
            return {
                'success': False,
                'error': 'No active assignment found for this field and entity'
            }

        # Build query
        query = ESGData.query.filter_by(
            field_id=field_id,
            entity_id=entity_id
        ).filter(
            ESGData.raw_value.isnot(None) | ESGData.calculated_value.isnot(None)
        )

        # Apply date filters
        if start_date:
            query = query.filter(ESGData.reporting_date >= start_date)
        if end_date:
            query = query.filter(ESGData.reporting_date <= end_date)

        # Order by date descending and limit
        query = query.order_by(ESGData.reporting_date.desc()).limit(limit)

        # Execute query
        entries = query.all()

        # Format data
        data = []
        for entry in entries:
            # Get attachments for this entry
            attachments = ESGDataAttachment.query.filter_by(data_id=entry.data_id).all()

            data.append({
                'id': entry.data_id,
                'reporting_date': entry.reporting_date.isoformat(),
                'raw_value': entry.raw_value,
                'calculated_value': entry.calculated_value,
                'unit': entry.effective_unit,
                'dimension_values': entry.dimension_values or {},
                'status': 'submitted',  # Can be extended with actual status tracking
                'created_at': entry.created_at.isoformat() if entry.created_at else None,
                'updated_at': entry.updated_at.isoformat() if entry.updated_at else None,
                'attachments': [
                    {
                        'id': att.id,
                        'filename': att.filename,
                        'file_size': att.file_size,
                        'mime_type': att.mime_type,
                        'uploaded_at': att.uploaded_at.isoformat()
                    } for att in attachments
                ]
            })

        return {
            'success': True,
            'field_id': field_id,
            'field_name': field.field_name,
            'entity_id': entity_id,
            'total_count': len(data),
            'data': data,
            'is_computed': field.is_computed
        }

    @staticmethod
    def get_data_summary(field_id: str, entity_id: int) -> Dict[str, Any]:
        """
        Get summary statistics for historical data.

        Args:
            field_id: The field ID
            entity_id: The entity ID

        Returns:
            Dict with summary statistics
        """
        # Get field
        field = FrameworkDataField.query.get(field_id)
        if not field:
            return {
                'success': False,
                'error': 'Field not found'
            }

        # Query data
        entries = ESGData.query.filter_by(
            field_id=field_id,
            entity_id=entity_id
        ).filter(
            ESGData.raw_value.isnot(None) | ESGData.calculated_value.isnot(None)
        ).all()

        if not entries:
            return {
                'success': True,
                'field_id': field_id,
                'entity_id': entity_id,
                'total_submissions': 0,
                'date_range': None,
                'statistics': None
            }

        # Calculate statistics
        total_submissions = len(entries)
        dates = [e.reporting_date for e in entries]

        summary = {
            'success': True,
            'field_id': field_id,
            'entity_id': entity_id,
            'total_submissions': total_submissions,
            'date_range': {
                'earliest': min(dates).isoformat() if dates else None,
                'latest': max(dates).isoformat() if dates else None
            }
        }

        # Add numeric statistics if applicable
        if field.value_type == 'NUMBER' and not field.is_computed:
            values = []
            for entry in entries:
                if entry.raw_value is not None:
                    try:
                        values.append(float(entry.raw_value))
                    except (ValueError, TypeError):
                        continue

            if values:
                summary['statistics'] = {
                    'min': min(values),
                    'max': max(values),
                    'average': sum(values) / len(values),
                    'count': len(values)
                }

        return summary

    @staticmethod
    def get_data_by_date_range(
        entity_id: int,
        start_date: date,
        end_date: date,
        field_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get all data for an entity within a date range.

        Args:
            entity_id: The entity ID
            start_date: Start date
            end_date: End date
            field_ids: Optional list of field IDs to filter

        Returns:
            Dict with data organized by date and field
        """
        query = ESGData.query.filter(
            ESGData.entity_id == entity_id,
            ESGData.reporting_date >= start_date,
            ESGData.reporting_date <= end_date
        ).filter(
            ESGData.raw_value.isnot(None) | ESGData.calculated_value.isnot(None)
        )

        # Filter by field IDs if provided
        if field_ids:
            query = query.filter(ESGData.field_id.in_(field_ids))

        entries = query.order_by(ESGData.reporting_date.desc()).all()

        # Organize by date then field
        data_by_date = {}
        for entry in entries:
            date_key = entry.reporting_date.isoformat()
            if date_key not in data_by_date:
                data_by_date[date_key] = {}

            # Get field info
            field = FrameworkDataField.query.get(entry.field_id)

            data_by_date[date_key][entry.field_id] = {
                'field_name': field.field_name if field else 'Unknown',
                'raw_value': entry.raw_value,
                'calculated_value': entry.calculated_value,
                'unit': entry.effective_unit,
                'dimension_values': entry.dimension_values or {},
                'is_computed': field.is_computed if field else False
            }

        return {
            'success': True,
            'entity_id': entity_id,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'data_by_date': data_by_date
        }

    @staticmethod
    def check_data_completeness(entity_id: int, reporting_date: date) -> Dict[str, Any]:
        """
        Check data completeness for a specific date.

        Args:
            entity_id: The entity ID
            reporting_date: The reporting date to check

        Returns:
            Dict with completeness information
        """
        from ...models.entity import Entity

        # Get entity and its parent entities
        entity = Entity.query.get(entity_id)
        if not entity:
            return {
                'success': False,
                'error': 'Entity not found'
            }

        entity_ids = [entity_id]
        current_entity = entity
        while current_entity and current_entity.parent_id:
            entity_ids.append(current_entity.parent_id)
            current_entity = current_entity.parent

        # Get all active assignments for these entities
        assignments = DataPointAssignment.query.filter(
            DataPointAssignment.entity_id.in_(entity_ids),
            DataPointAssignment.series_status == 'active'
        ).all()

        # Filter assignments valid for this date
        valid_assignments = []
        for assignment in assignments:
            if assignment.is_valid_reporting_date(reporting_date):
                valid_assignments.append(assignment)

        total_fields = len(valid_assignments)

        # Count submitted data
        submitted_count = 0
        missing_fields = []

        for assignment in valid_assignments:
            data = ESGData.query.filter_by(
                field_id=assignment.field_id,
                entity_id=entity_id,
                reporting_date=reporting_date
            ).filter(
                ESGData.raw_value.isnot(None) | ESGData.calculated_value.isnot(None)
            ).first()

            if data:
                submitted_count += 1
            else:
                field = FrameworkDataField.query.get(assignment.field_id)
                if field:
                    missing_fields.append({
                        'field_id': field.field_id,
                        'field_name': field.field_name,
                        'is_computed': field.is_computed
                    })

        completeness_percentage = (submitted_count / total_fields * 100) if total_fields > 0 else 0

        return {
            'success': True,
            'entity_id': entity_id,
            'reporting_date': reporting_date.isoformat(),
            'total_fields': total_fields,
            'submitted_count': submitted_count,
            'missing_count': len(missing_fields),
            'completeness_percentage': round(completeness_percentage, 2),
            'missing_fields': missing_fields[:10]  # Limit to first 10
        }
