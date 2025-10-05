"""
Draft Service for User V2
==========================

Handles auto-save draft functionality for data entry forms.

Features:
- Save draft data every 30 seconds during editing
- Retrieve drafts for specific fields/entities/dates
- Clean up old drafts (> 7 days)
- Handle concurrent edits gracefully

Phase 4: Uses ESGData model with is_draft flag and draft_metadata JSON column
"""

import json
from datetime import datetime, timedelta, date as date_type
from typing import Optional, Dict, Any, List
from sqlalchemy import and_, desc
from app.extensions import db
from app.models import ESGData, User, Entity, DataPointAssignment, FrameworkDataField
import logging

logger = logging.getLogger(__name__)


class DraftService:
    """Service for managing draft data entries"""

    @staticmethod
    def save_draft(
        user_id: int,
        field_id: str,
        entity_id: int,
        reporting_date: str,
        form_data: Dict[str, Any],
        company_id: int
    ) -> Dict[str, Any]:
        """
        Save a draft entry for later retrieval.

        Drafts are stored as special ESGData records with is_draft=True flag.
        If a draft already exists for this combination, it's updated.

        Args:
            user_id: ID of user creating the draft
            field_id: ID of the field being edited (UUID string)
            entity_id: ID of the entity
            reporting_date: Reporting date (YYYY-MM-DD format string)
            form_data: Dictionary containing form state
            company_id: Company ID for tenant isolation

        Returns:
            Dictionary with:
                - success: bool
                - draft_id: str (ESGData data_id)
                - timestamp: str (ISO format)
                - message: str

        Example form_data:
            {
                'raw_value': '1234.56',
                'calculated_value': 1234.56,
                'unit': 'kWh',
                'dimension_values': {'gender': 'Male', 'age': '<30'},
                'assignment_id': 'uuid-string'
            }
        """
        try:
            # Validate inputs
            if not all([user_id, field_id, entity_id, reporting_date, company_id]):
                return {
                    'success': False,
                    'message': 'Missing required parameters',
                    'timestamp': datetime.now().isoformat()
                }

            # Parse reporting_date string to date object
            if isinstance(reporting_date, str):
                reporting_date = datetime.strptime(reporting_date, '%Y-%m-%d').date()

            # Check if draft already exists
            existing_draft = ESGData.query.filter(
                and_(
                    ESGData.field_id == field_id,
                    ESGData.entity_id == entity_id,
                    ESGData.reporting_date == reporting_date,
                    ESGData.company_id == company_id,
                    ESGData.is_draft == True
                )
            ).first()

            # Prepare draft metadata
            draft_metadata = {
                'saved_by_user_id': user_id,
                'draft_timestamp': datetime.now().isoformat(),
                'form_data': form_data
            }

            if existing_draft:
                # Update existing draft
                existing_draft.raw_value = form_data.get('raw_value', '')
                existing_draft.calculated_value = form_data.get('calculated_value')
                existing_draft.unit = form_data.get('unit')
                existing_draft.dimension_values = form_data.get('dimension_values', {})
                existing_draft.draft_metadata = draft_metadata
                existing_draft.updated_at = datetime.now()

                db.session.commit()

                return {
                    'success': True,
                    'draft_id': existing_draft.data_id,
                    'timestamp': existing_draft.updated_at.isoformat(),
                    'message': 'Draft updated successfully'
                }
            else:
                # Create new draft
                new_draft = ESGData(
                    entity_id=entity_id,
                    field_id=field_id,
                    raw_value=form_data.get('raw_value', ''),
                    reporting_date=reporting_date,
                    company_id=company_id,
                    calculated_value=form_data.get('calculated_value'),
                    unit=form_data.get('unit'),
                    dimension_values=form_data.get('dimension_values', {}),
                    assignment_id=form_data.get('assignment_id')
                )

                # Set draft-specific fields
                new_draft.is_draft = True
                new_draft.draft_metadata = draft_metadata

                db.session.add(new_draft)
                db.session.commit()

                return {
                    'success': True,
                    'draft_id': new_draft.data_id,
                    'timestamp': new_draft.created_at.isoformat(),
                    'message': 'Draft saved successfully'
                }

        except Exception as e:
            logger.error(f"Error saving draft: {str(e)}", exc_info=True)
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error saving draft: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }

    @staticmethod
    def get_draft(
        user_id: int,
        field_id: str,
        entity_id: int,
        reporting_date: str,
        company_id: int
    ) -> Dict[str, Any]:
        """
        Retrieve draft data for a specific field/entity/date combination.

        Args:
            user_id: ID of user
            field_id: ID of the field (UUID string)
            entity_id: ID of the entity
            reporting_date: Reporting date (YYYY-MM-DD format string)
            company_id: Company ID for tenant isolation

        Returns:
            Dictionary with:
                - has_draft: bool
                - draft_data: dict (if exists)
                - timestamp: str (ISO format)
                - draft_id: str (if exists)
        """
        try:
            # Parse reporting_date string to date object
            if isinstance(reporting_date, str):
                reporting_date = datetime.strptime(reporting_date, '%Y-%m-%d').date()

            draft = ESGData.query.filter(
                and_(
                    ESGData.field_id == field_id,
                    ESGData.entity_id == entity_id,
                    ESGData.reporting_date == reporting_date,
                    ESGData.company_id == company_id,
                    ESGData.is_draft == True
                )
            ).first()

            if draft:
                # Parse draft metadata
                draft_metadata = draft.draft_metadata or {}
                form_data = draft_metadata.get('form_data', {}) if isinstance(draft_metadata, dict) else {}

                return {
                    'has_draft': True,
                    'draft_id': draft.data_id,
                    'draft_data': {
                        'raw_value': draft.raw_value,
                        'calculated_value': draft.calculated_value,
                        'unit': draft.unit,
                        'dimension_values': draft.dimension_values or {},
                        'assignment_id': draft.assignment_id,
                        **form_data  # Include any additional form data
                    },
                    'timestamp': draft.updated_at.isoformat(),
                    'age_minutes': (datetime.now() - draft.updated_at.replace(tzinfo=None)).total_seconds() / 60
                }
            else:
                return {
                    'has_draft': False,
                    'draft_data': None,
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error retrieving draft: {str(e)}", exc_info=True)
            return {
                'has_draft': False,
                'draft_data': None,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

    @staticmethod
    def discard_draft(draft_id: str, user_id: int, company_id: int) -> Dict[str, Any]:
        """
        Discard a draft by ID.

        Args:
            draft_id: ID of the draft to discard (data_id UUID string)
            user_id: ID of user (for authorization)
            company_id: Company ID for tenant isolation

        Returns:
            Dictionary with success status and message
        """
        try:
            draft = ESGData.query.filter(
                and_(
                    ESGData.data_id == draft_id,
                    ESGData.company_id == company_id,
                    ESGData.is_draft == True
                )
            ).first()

            if not draft:
                return {
                    'success': False,
                    'message': 'Draft not found or not authorized'
                }

            # Verify user authorization through metadata
            draft_metadata = draft.draft_metadata or {}
            if isinstance(draft_metadata, dict):
                saved_by = draft_metadata.get('saved_by_user_id')
                if saved_by and saved_by != user_id:
                    return {
                        'success': False,
                        'message': 'Not authorized to discard this draft'
                    }

            db.session.delete(draft)
            db.session.commit()

            return {
                'success': True,
                'message': 'Draft discarded successfully'
            }

        except Exception as e:
            logger.error(f"Error discarding draft: {str(e)}", exc_info=True)
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error discarding draft: {str(e)}'
            }

    @staticmethod
    def list_drafts(
        user_id: int,
        company_id: int,
        entity_id: Optional[int] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List all drafts for a user, optionally filtered by entity.

        Args:
            user_id: ID of user
            company_id: Company ID for tenant isolation
            entity_id: Optional entity ID filter
            limit: Maximum number of drafts to return

        Returns:
            Dictionary with:
                - drafts: list of draft summaries
                - count: total count
        """
        try:
            query = ESGData.query.filter(
                and_(
                    ESGData.company_id == company_id,
                    ESGData.is_draft == True
                )
            )

            if entity_id:
                query = query.filter(ESGData.entity_id == entity_id)

            # Filter by user through metadata (since we don't have created_by column)
            # For now, return all company drafts and filter in Python
            all_drafts = query.order_by(desc(ESGData.updated_at)).limit(limit * 2).all()

            # Filter by user_id from metadata
            user_drafts = []
            for draft in all_drafts:
                draft_metadata = draft.draft_metadata or {}
                if isinstance(draft_metadata, dict):
                    saved_by = draft_metadata.get('saved_by_user_id')
                    if saved_by == user_id:
                        user_drafts.append(draft)
                        if len(user_drafts) >= limit:
                            break

            draft_list = []
            for draft in user_drafts:
                # Get field and entity details
                field = FrameworkDataField.query.filter_by(field_id=draft.field_id).first()
                entity = Entity.query.get(draft.entity_id)

                draft_list.append({
                    'draft_id': draft.data_id,
                    'field_id': draft.field_id,
                    'field_name': field.field_name if field else 'Unknown',
                    'entity_id': draft.entity_id,
                    'entity_name': entity.name if entity else 'Unknown',
                    'reporting_date': draft.reporting_date.isoformat() if isinstance(draft.reporting_date, date_type) else str(draft.reporting_date),
                    'updated_at': draft.updated_at.isoformat(),
                    'age_minutes': (datetime.now() - draft.updated_at.replace(tzinfo=None)).total_seconds() / 60,
                    'has_value': bool(draft.raw_value)
                })

            return {
                'success': True,
                'drafts': draft_list,
                'count': len(draft_list)
            }

        except Exception as e:
            logger.error(f"Error listing drafts: {str(e)}", exc_info=True)
            return {
                'success': False,
                'drafts': [],
                'count': 0,
                'error': str(e)
            }

    @staticmethod
    def cleanup_old_drafts(days: int = 7) -> Dict[str, Any]:
        """
        Clean up drafts older than specified days.

        This should be run periodically (e.g., daily cron job).

        Args:
            days: Delete drafts older than this many days (default: 7)

        Returns:
            Dictionary with count of deleted drafts
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            old_drafts = ESGData.query.filter(
                and_(
                    ESGData.is_draft == True,
                    ESGData.updated_at < cutoff_date
                )
            ).all()

            count = len(old_drafts)

            for draft in old_drafts:
                db.session.delete(draft)

            db.session.commit()

            logger.info(f"Cleaned up {count} old drafts (older than {days} days)")

            return {
                'success': True,
                'deleted_count': count,
                'cutoff_date': cutoff_date.isoformat()
            }

        except Exception as e:
            logger.error(f"Error cleaning up drafts: {str(e)}", exc_info=True)
            db.session.rollback()
            return {
                'success': False,
                'deleted_count': 0,
                'error': str(e)
            }

    @staticmethod
    def promote_draft_to_data(
        draft_id: str,
        user_id: int,
        company_id: int
    ) -> Dict[str, Any]:
        """
        Convert a draft to actual data entry (remove is_draft flag).

        This is called when user submits the form.

        Args:
            draft_id: ID of the draft (data_id UUID string)
            user_id: ID of user (for authorization)
            company_id: Company ID for tenant isolation

        Returns:
            Dictionary with success status and data_id
        """
        try:
            draft = ESGData.query.filter(
                and_(
                    ESGData.data_id == draft_id,
                    ESGData.company_id == company_id,
                    ESGData.is_draft == True
                )
            ).first()

            if not draft:
                return {
                    'success': False,
                    'message': 'Draft not found or not authorized'
                }

            # Verify user authorization through metadata
            draft_metadata = draft.draft_metadata or {}
            if isinstance(draft_metadata, dict):
                saved_by = draft_metadata.get('saved_by_user_id')
                if saved_by and saved_by != user_id:
                    return {
                        'success': False,
                        'message': 'Not authorized to promote this draft'
                    }

            # Simply remove the draft flag
            draft.is_draft = False
            draft.updated_at = datetime.now()

            # Clear draft metadata since it's now real data
            draft.draft_metadata = None

            db.session.commit()

            return {
                'success': True,
                'data_id': draft.data_id,
                'message': 'Draft promoted to data successfully'
            }

        except Exception as e:
            logger.error(f"Error promoting draft: {str(e)}", exc_info=True)
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error promoting draft: {str(e)}'
            }
