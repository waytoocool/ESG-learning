"""
Entity Service
==============

Business logic for entity management and switching in the user dashboard.
"""

from typing import List, Dict, Any, Optional
from flask_login import current_user
from sqlalchemy.orm import Session

from ...models.entity import Entity
from ...models.user import User
from ...models.data_assignment import DataPointAssignment
from ...extensions import db


class EntityService:
    """Service for managing entities in the user dashboard."""

    @staticmethod
    def get_user_entities(user_id: int, session: Optional[Session] = None) -> List[Entity]:
        """
        Get all entities accessible by the user.

        Args:
            user_id: The user ID
            session: Optional database session (defaults to db.session)

        Returns:
            List of Entity objects accessible by the user
        """
        if session is None:
            session = db.session

        user = User.query.get(user_id)
        if not user:
            return []

        if user.role == 'ADMIN':
            # Admins see all entities in their company
            return Entity.query.filter_by(company_id=user.company_id).all()
        elif user.role == 'USER':
            # Regular users see only their assigned entity
            if user.entity_id:
                entity = Entity.query.get(user.entity_id)
                return [entity] if entity else []
            return []

        return []

    @staticmethod
    def get_current_entity(user_id: int) -> Optional[Entity]:
        """
        Get the current entity for the user.

        Args:
            user_id: The user ID

        Returns:
            Current Entity object or None
        """
        user = User.query.get(user_id)
        if not user or not user.entity_id:
            return None

        return Entity.query.get(user.entity_id)

    @staticmethod
    def switch_entity(user_id: int, entity_id: int, session: Optional[Session] = None) -> Dict[str, Any]:
        """
        Switch the user's current entity.

        This updates the user's entity_id and returns the new entity context.
        Only allowed for ADMIN users.

        Args:
            user_id: The user ID
            entity_id: The new entity ID to switch to
            session: Optional database session

        Returns:
            Dict with success status, message, and new entity data
        """
        if session is None:
            session = db.session

        user = User.query.get(user_id)
        if not user:
            return {
                'success': False,
                'error': 'User not found'
            }

        # Only admins can switch entities
        if user.role != 'ADMIN':
            return {
                'success': False,
                'error': 'Only administrators can switch entities'
            }

        # Verify entity exists and belongs to user's company
        entity = Entity.query.filter_by(
            id=entity_id,
            company_id=user.company_id
        ).first()

        if not entity:
            return {
                'success': False,
                'error': 'Entity not found or not accessible'
            }

        # Update user's entity
        user.entity_id = entity_id
        session.commit()

        return {
            'success': True,
            'message': f'Switched to entity: {entity.name}',
            'entity': {
                'id': entity.id,
                'name': entity.name,
                'type': entity.entity_type,
                'parent_id': entity.parent_id
            }
        }

    @staticmethod
    def get_entity_hierarchy(entity_id: int) -> Dict[str, Any]:
        """
        Get the hierarchical path for an entity.

        Args:
            entity_id: The entity ID

        Returns:
            Dict with hierarchy information
        """
        entity = Entity.query.get(entity_id)
        if not entity:
            return {
                'entity_id': entity_id,
                'path': [],
                'level': 0
            }

        # Build path from root to current entity
        path = []
        current = entity
        while current:
            path.insert(0, {
                'id': current.id,
                'name': current.name,
                'type': current.entity_type
            })
            current = current.parent if current.parent_id else None

        return {
            'entity_id': entity_id,
            'path': path,
            'level': entity.get_hierarchy_level()
        }

    @staticmethod
    def get_entity_assignment_count(entity_id: int) -> Dict[str, int]:
        """
        Get counts of assigned data points for an entity.

        Args:
            entity_id: The entity ID

        Returns:
            Dict with counts of total, raw, and computed assignments
        """
        from ...models.framework import FrameworkDataField

        # Get active assignments for this entity
        assignments = DataPointAssignment.query.filter_by(
            entity_id=entity_id,
            series_status='active'
        ).all()

        total_count = len(assignments)
        raw_count = 0
        computed_count = 0

        for assignment in assignments:
            field = FrameworkDataField.query.get(assignment.field_id)
            if field:
                if field.is_computed:
                    computed_count += 1
                else:
                    raw_count += 1

        return {
            'total': total_count,
            'raw': raw_count,
            'computed': computed_count
        }
