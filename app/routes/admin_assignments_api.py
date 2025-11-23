"""
Assignment Management API Routes for Phase 3 Frontend Enhancement.

This module provides API endpoints for the enhanced assignment management interface
that integrates with the AssignmentVersioningService from Phase 2.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
import uuid

from ..decorators.auth import admin_or_super_admin_required, tenant_required
from ..models.data_assignment import DataPointAssignment
from ..models.framework import FrameworkDataField, Topic
from ..models.entity import Entity
from ..models.company import Company
from ..models.audit_log import AuditLog
from ..services.assignment_versioning import AssignmentVersioningService
from ..middleware.tenant import get_current_tenant
from ..extensions import db

def is_super_admin():
    """Check if the current user is a SUPER_ADMIN."""
    return current_user.is_authenticated and current_user.role == 'SUPER_ADMIN'

# Blueprint for assignment management API
assignment_api_bp = Blueprint('assignment_api', __name__, url_prefix='/admin/api/assignments')


# BUG FIX #4: Add /api/assignments/history endpoint (alias for /admin/assignment-history/api/timeline)
@assignment_api_bp.route('/history', methods=['GET'])
@login_required
@admin_or_super_admin_required
@tenant_required
def get_assignment_history_alias():
    """
    API endpoint to get assignment history timeline (alias for backward compatibility).
    This proxies to the actual implementation in admin_assignment_history blueprint.

    Query parameters:
    - page: Page number for pagination (default: 1)
    - per_page: Items per page (default: 20)
    - field_id: Filter by specific field
    - entity_id: Filter by specific entity
    - data_series_id: Filter by specific data series
    - date_from: Filter assignments from date (YYYY-MM-DD)
    - date_to: Filter assignments to date (YYYY-MM-DD)
    - search: Search in field names, entity names
    """
    try:
        from sqlalchemy import desc, and_, or_
        from sqlalchemy.orm import joinedload

        tenant = get_current_tenant()

        # Get query parameters
        field_id = request.args.get('field_id')
        entity_id = request.args.get('entity_id', type=int)
        data_series_id = request.args.get('data_series_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)

        # Base query with tenant scoping
        query = DataPointAssignment.query.filter_by(company_id=tenant.id).options(
            joinedload(DataPointAssignment.field).joinedload(FrameworkDataField.topic),
            joinedload(DataPointAssignment.entity),
            joinedload(DataPointAssignment.assigned_by_user),
            joinedload(DataPointAssignment.assigned_topic)
        )

        # Apply filters
        if field_id:
            query = query.filter(DataPointAssignment.field_id == field_id)
        if entity_id:
            query = query.filter(DataPointAssignment.entity_id == entity_id)
        if data_series_id:
            query = query.filter(DataPointAssignment.data_series_id == data_series_id)

        # Date range filtering
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(DataPointAssignment.assigned_date >= from_date)
            except ValueError:
                return jsonify({'error': 'Invalid date_from format. Use YYYY-MM-DD'}), 400

        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(DataPointAssignment.assigned_date <= to_date)
            except ValueError:
                return jsonify({'error': 'Invalid date_to format. Use YYYY-MM-DD'}), 400

        # Search filtering
        if search:
            from ..models.user import User
            search_filter = or_(
                DataPointAssignment.field.has(FrameworkDataField.field_name.ilike(f'%{search}%')),
                DataPointAssignment.entity.has(Entity.name.ilike(f'%{search}%')),
                DataPointAssignment.assigned_by_user.has(User.name.ilike(f'%{search}%'))
            )
            query = query.filter(search_filter)

        # Order by assigned date (newest first)
        query = query.order_by(
            desc(DataPointAssignment.assigned_date),
            desc(DataPointAssignment.series_version)
        )

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        assignments = pagination.items

        # Format response
        timeline_data = []
        for assignment in assignments:
            timeline_data.append({
                'id': assignment.id,
                'field_id': assignment.field_id,
                'field_name': assignment.field.field_name if assignment.field else 'Unknown Field',
                'entity_id': assignment.entity_id,
                'entity_name': assignment.entity.name if assignment.entity else 'Unknown Entity',
                'frequency': assignment.frequency,
                'unit': assignment.effective_unit,
                'series_id': assignment.data_series_id,
                'version': assignment.series_version,
                'status': assignment.series_status,
                'assigned_date': assignment.assigned_date.isoformat() if assignment.assigned_date else None,
                'assigned_by': assignment.assigned_by_user.name if assignment.assigned_by_user else 'Unknown',
                'is_active': assignment.series_status == 'active'
            })

        return jsonify({
            'timeline': timeline_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })

    except Exception as e:
        current_app.logger.error(f'Error fetching assignment history: {str(e)}')
        return jsonify({'error': 'Failed to fetch assignment history'}), 500


# Removed orphaned /create endpoint - was only used by legacy assign_data_points.js


# Removed orphaned /conflicts endpoint - was only used by legacy assign_data_points.js


def _is_frequency_compatible(requested_freq: str, dependency_freq: str) -> bool:
    """
    Check if a requested frequency is compatible with a dependency frequency.
    
    Rule: Computed field frequency must be equal to or lower frequency than dependencies
    (Annual < Quarterly < Monthly in terms of frequency)
    """
    freq_hierarchy = {
        'Annual': 1,
        'Quarterly': 2, 
        'Monthly': 3
    }
    
    req_level = freq_hierarchy.get(requested_freq, 1)
    dep_level = freq_hierarchy.get(dependency_freq, 1)
    
    return req_level <= dep_level


@assignment_api_bp.route('/<assignment_id>/deactivate', methods=['POST'])
@login_required
@admin_or_super_admin_required
def deactivate_assignment(assignment_id):
    """
    Soft delete (deactivate) an assignment with audit trail.

    This endpoint marks an assignment as inactive (series_status='inactive') instead of
    deleting it to preserve historical data integrity.

    Expected payload:
    {
        "reason": "User removed assignment" // optional deactivation reason
    }
    """
    try:
        # Get the assignment
        if is_super_admin():
            assignment = DataPointAssignment.query.get(assignment_id)
        else:
            # Check tenant access for non-SUPER_ADMIN users
            current_tenant = get_current_tenant()
            if not current_tenant:
                return jsonify({
                    'success': False,
                    'error': 'Tenant context required for non-SUPER_ADMIN users'
                }), 403

            assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
                id=assignment_id
            ).first()

        if not assignment:
            return jsonify({
                'success': False,
                'error': 'Assignment not found or access denied'
            }), 404

        # Check if assignment is already inactive
        if assignment.series_status != 'active':
            return jsonify({
                'success': False,
                'error': 'Assignment is already deactivated'
            }), 400

        # Get optional deactivation reason from payload
        data = request.get_json() or {}
        reason = data.get('reason', 'Assignment deactivated by admin')

        # Get count of associated ESG data entries for audit
        data_entry_count = assignment.get_data_entry_count()

        # Perform soft deletion
        assignment.series_status = 'inactive'  # Mark as inactive status

        # Log the deactivation in audit trail
        audit_payload = {
            'assignment_id': assignment.id,
            'field_id': assignment.field_id,
            'field_name': assignment.field.field_name if assignment.field else None,
            'entity_id': assignment.entity_id,
            'entity_name': assignment.entity.name if assignment.entity else None,
            'company_id': assignment.company_id,
            'frequency': assignment.frequency,
            'unit': assignment.unit,
            'data_series_id': assignment.data_series_id,
            'series_version': assignment.series_version,
            'data_entry_count': data_entry_count,
            'reason': reason
        }

        AuditLog.log_action(
            user_id=current_user.id,
            action='DEACTIVATE_ASSIGNMENT',
            entity_type='DataPointAssignment',
            entity_id=assignment_id,
            payload=audit_payload,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        # Commit changes
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Assignment deactivated successfully',
            'result': {
                'assignment_id': assignment.id,
                'field_name': assignment.field.field_name if assignment.field else None,
                'entity_name': assignment.entity.name if assignment.entity else None,
                'data_entry_count': data_entry_count,
                'preserved_data': True,
                'reason': reason
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Assignment deactivation error for ID {assignment_id}: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Assignment deactivation failed: {str(e)}'
        }), 500


@assignment_api_bp.route('/<assignment_id>/reactivate', methods=['POST'])
@login_required
@admin_or_super_admin_required
def reactivate_assignment(assignment_id):
    """
    Reactivate a previously deactivated assignment.

    This endpoint restores an assignment by setting series_status='active'.

    Expected payload:
    {
        "reason": "Assignment restored" // optional reactivation reason
    }
    """
    try:
        # Get the assignment
        if is_super_admin():
            assignment = DataPointAssignment.query.get(assignment_id)
        else:
            # Check tenant access for non-SUPER_ADMIN users
            current_tenant = get_current_tenant()
            if not current_tenant:
                return jsonify({
                    'success': False,
                    'error': 'Tenant context required for non-SUPER_ADMIN users'
                }), 403

            assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
                id=assignment_id
            ).first()

        if not assignment:
            return jsonify({
                'success': False,
                'error': 'Assignment not found or access denied'
            }), 404

        # Check if assignment is already active
        if assignment.series_status == 'active':
            return jsonify({
                'success': False,
                'error': 'Assignment is already active'
            }), 400

        # Check for conflicts with existing active assignments
        conflict_check = DataPointAssignment.query.filter_by(
            field_id=assignment.field_id,
            entity_id=assignment.entity_id,
            series_status='active'
        ).first()

        if conflict_check:
            return jsonify({
                'success': False,
                'error': f'Cannot reactivate: Active assignment already exists for this field+entity combination (Assignment ID: {conflict_check.id})'
            }), 409

        # Get optional reactivation reason from payload
        data = request.get_json() or {}
        reason = data.get('reason', 'Assignment reactivated by admin')

        # Get count of associated ESG data entries for audit
        data_entry_count = assignment.get_data_entry_count()

        # Reactivate assignment
        assignment.series_status = 'active'
        assignment.series_status = 'active'

        # Log the reactivation in audit trail
        audit_payload = {
            'assignment_id': assignment.id,
            'field_id': assignment.field_id,
            'field_name': assignment.field.field_name if assignment.field else None,
            'entity_id': assignment.entity_id,
            'entity_name': assignment.entity.name if assignment.entity else None,
            'company_id': assignment.company_id,
            'frequency': assignment.frequency,
            'unit': assignment.unit,
            'data_series_id': assignment.data_series_id,
            'series_version': assignment.series_version,
            'data_entry_count': data_entry_count,
            'reason': reason
        }

        AuditLog.log_action(
            user_id=current_user.id,
            action='REACTIVATE_ASSIGNMENT',
            entity_type='DataPointAssignment',
            entity_id=assignment_id,
            payload=audit_payload,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        # Commit changes
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Assignment reactivated successfully',
            'result': {
                'assignment_id': assignment.id,
                'field_name': assignment.field.field_name if assignment.field else None,
                'entity_name': assignment.entity.name if assignment.entity else None,
                'data_entry_count': data_entry_count,
                'reason': reason
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Assignment reactivation error for ID {assignment_id}: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Assignment reactivation failed: {str(e)}'
        }), 500


@assignment_api_bp.route('/by-field/<field_id>', methods=['GET'])
@login_required
@admin_or_super_admin_required
def get_assignments_by_field(field_id):
    """
    Get all assignments for a specific field_id.

    This endpoint is used by the UI to find assignments that need to be deactivated
    when a user wants to remove a field from the assignment interface.
    """
    try:
        # Check tenant access for non-SUPER_ADMIN users
        if not is_super_admin():
            current_tenant = get_current_tenant()
            if not current_tenant:
                return jsonify({
                    'success': False,
                    'error': 'Tenant context required for non-SUPER_ADMIN users'
                }), 403
            company_id = current_tenant.id
        else:
            current_tenant = get_current_tenant()
            company_id = current_tenant.id if current_tenant else None

        # Build the query using proper tenant scoping
        if is_super_admin() and company_id:
            # SUPER_ADMIN with specific company - manually filter
            query = DataPointAssignment.query.filter_by(field_id=field_id, company_id=company_id)
            assignments = query.all()
        else:
            # Regular users or SUPER_ADMIN without specific company - use tenant scoping
            query = DataPointAssignment.query_for_tenant(db.session).filter_by(field_id=field_id)
            assignments = query.all()

        # Convert to list of dictionaries
        assignment_list = []
        for assignment in assignments:
            assignment_list.append({
                'id': assignment.id,
                'field_id': assignment.field_id,
                'entity_id': assignment.entity_id,
                'entity_name': assignment.entity.name if assignment.entity else None,
                'company_id': assignment.company_id,
                'frequency': assignment.frequency,
                'unit': assignment.unit,
                'series_status': assignment.series_status,
                'assigned_date': assignment.assigned_date.isoformat() if assignment.assigned_date else None,
                'field_name': assignment.field.field_name if assignment.field else None
            })

        return jsonify({
            'success': True,
            'assignments': assignment_list,
            'count': len(assignment_list)
        })

    except Exception as e:
        current_app.logger.error(f'Error getting assignments for field {field_id}: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Failed to get assignments: {str(e)}'
        }), 500


@assignment_api_bp.route('/by-field/<field_id>/deactivate-all', methods=['POST'])
@login_required
@admin_or_super_admin_required
def deactivate_all_field_assignments(field_id):
    """
    BUG FIX: Cascade soft delete ALL assignment records for a field.

    When a field is soft deleted (removed from assignment interface), this endpoint
    marks ALL related DataPointAssignment records as inactive, including:
    - Active assignments
    - Superseded assignments
    - Legacy assignments
    - All version history

    This ensures data integrity and UI consistency when viewing assignment history.

    Expected payload:
    {
        "reason": "User removed field from assignment interface"  // optional
    }

    Returns:
    {
        "success": true,
        "message": "All assignments deactivated for field",
        "result": {
            "field_id": "...",
            "field_name": "...",
            "total_deactivated": 15,
            "breakdown": {
                "active": 3,
                "superseded": 10,
                "legacy": 2
            }
        }
    }
    """
    try:
        # Check tenant access for non-SUPER_ADMIN users
        if not is_super_admin():
            current_tenant = get_current_tenant()
            if not current_tenant:
                return jsonify({
                    'success': False,
                    'error': 'Tenant context required for non-SUPER_ADMIN users'
                }), 403
            company_id = current_tenant.id
        else:
            current_tenant = get_current_tenant()
            company_id = current_tenant.id if current_tenant else None

        # Get optional reason from payload
        data = request.get_json() or {}
        reason = data.get('reason', 'Field soft deleted - cascade deactivation')

        # Build query to get ALL assignments for this field (all statuses, all versions)
        if is_super_admin() and company_id:
            # SUPER_ADMIN with specific company - manually filter
            assignments = DataPointAssignment.query.filter_by(
                field_id=field_id,
                company_id=company_id
            ).all()
        else:
            # Regular users - use tenant scoping
            assignments = DataPointAssignment.query_for_tenant(db.session).filter_by(
                field_id=field_id
            ).all()

        if not assignments:
            return jsonify({
                'success': False,
                'error': f'No assignments found for field {field_id}'
            }), 404

        # Get field name for audit logging
        field_name = assignments[0].field.field_name if assignments[0].field else 'Unknown'

        # Track status breakdown BEFORE deactivation
        status_breakdown = {
            'active': 0,
            'superseded': 0,
            'legacy': 0,
            'already_inactive': 0
        }

        # Deactivate ALL assignments for this field
        deactivated_count = 0
        for assignment in assignments:
            if assignment.series_status == 'inactive':
                # Already inactive, skip
                status_breakdown['already_inactive'] += 1
                continue

            # Track old status
            old_status = assignment.series_status
            if old_status == 'active':
                status_breakdown['active'] += 1
            elif old_status == 'superseded':
                status_breakdown['superseded'] += 1
            elif old_status == 'legacy':
                status_breakdown['legacy'] += 1

            # CASCADE UPDATE: Mark as inactive
            assignment.series_status = 'inactive'
            db.session.add(assignment)
            deactivated_count += 1

        # Log the cascade deactivation in audit trail
        audit_payload = {
            'field_id': field_id,
            'field_name': field_name,
            'company_id': company_id,
            'total_assignments': len(assignments),
            'total_deactivated': deactivated_count,
            'status_breakdown': status_breakdown,
            'reason': reason,
            'cascade_operation': True
        }

        AuditLog.log_action(
            user_id=current_user.id,
            action='DEACTIVATE_FIELD_ALL_ASSIGNMENTS',
            entity_type='FrameworkDataField',
            entity_id=field_id,
            payload=audit_payload,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        # Commit all changes
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'All assignments deactivated for field "{field_name}"',
            'result': {
                'field_id': field_id,
                'field_name': field_name,
                'total_assignments': len(assignments),
                'total_deactivated': deactivated_count,
                'breakdown': {
                    'active_deactivated': status_breakdown['active'],
                    'superseded_deactivated': status_breakdown['superseded'],
                    'legacy_deactivated': status_breakdown['legacy'],
                    'already_inactive': status_breakdown['already_inactive']
                },
                'reason': reason
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deactivating all assignments for field {field_id}: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Failed to deactivate field assignments: {str(e)}'
        }), 500


@assignment_api_bp.route('/import', methods=['POST'])
@login_required
@admin_or_super_admin_required
def import_assignments():
    """
    Import bulk assignments from CSV data.

    This endpoint handles:
    - Creating assignments for existing fields only
    - Handling multiple entities per field (semicolon-separated)
    - Deduplication to prevent duplicate assignments
    - Proper versioning for existing assignments
    - Field configuration updates

    Expected payload:
    {
        "assignments": [
            {
                "field_id": "uuid",
                "field_name": "Field Name",
                "frequency": "Annual|Quarterly|Monthly",
                "unit": "unit_code",
                "assigned_entities": ["entity_name_1", "entity_name_2"],
                "topic": "Topic Name"
            }
        ]
    }
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'message': 'JSON request required'}), 400

        payload = request.get_json()
        assignments_data = payload.get('assignments', [])

        if not assignments_data:
            return jsonify({'success': False, 'message': 'No assignments provided'}), 400

        # Get current tenant
        current_tenant = get_current_tenant()
        if not current_tenant:
            return jsonify({'success': False, 'message': 'Tenant context required'}), 403

        company_id = current_tenant.id

        # Ensure clean session state before starting
        try:
            db.session.rollback()  # Clear any pending transactions
        except Exception:
            pass  # Ignore if no transaction to rollback

        # Get all entities for this company
        try:
            entities = {entity.name: entity.id for entity in Entity.query_for_tenant(db.session).all()}
        except Exception as e:
            current_app.logger.error(f'Error querying entities: {str(e)}')
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

        results = []
        total_created = 0
        total_updated = 0
        total_skipped = 0

        for assignment_data in assignments_data:
            field_id = assignment_data.get('field_id')
            field_name = assignment_data.get('field_name', 'Unknown')
            frequency = assignment_data.get('frequency')
            unit = assignment_data.get('unit')
            topic_name = assignment_data.get('topic')
            assigned_entities = assignment_data.get('assigned_entities', [])

            if not field_id:
                results.append({
                    'field_id': field_id,
                    'field_name': field_name,
                    'success': False,
                    'message': 'Missing field_id'
                })
                total_skipped += 1
                continue

            # Validate field exists
            field = FrameworkDataField.query.filter_by(field_id=field_id).first()
            if not field:
                results.append({
                    'field_id': field_id,
                    'field_name': field_name,
                    'success': False,
                    'message': f'Field not found in system'
                })
                total_skipped += 1
                continue

            # Handle topic assignment if provided
            topic_updated = False
            if topic_name and topic_name.strip():
                topic_name = topic_name.strip()
                # Find topic by name (case-insensitive search across framework topics and custom company topics)
                topic = Topic.query.filter(
                    db.func.lower(Topic.name) == topic_name.lower(),
                    db.or_(
                        Topic.framework_id == field.framework_id,  # Framework-specific topic
                        Topic.company_id == get_current_tenant().id   # Company-specific custom topic
                    )
                ).first()

                if topic:
                    # Update field's topic assignment if different
                    if field.topic_id != topic.topic_id:
                        field.topic_id = topic.topic_id
                        db.session.add(field)
                        topic_updated = True
                        current_app.logger.info(f'Updated topic assignment for field {field_id} to topic {topic_name}')
                else:
                    current_app.logger.warning(f'Topic "{topic_name}" not found for field {field_id}. Skipping topic assignment.')

            # IMPORT FIX: Deactivate existing assignments for this field that are NOT in the CSV
            # This ensures the CSV defines the complete assignment state for each field
            try:
                # Get entity IDs that should be assigned (from CSV)
                target_entity_ids = []
                for entity_name in assigned_entities:
                    entity_id = entities.get(entity_name.strip())
                    if entity_id:
                        target_entity_ids.append(entity_id)

                # Find existing assignments for this field that are NOT in the target entities
                existing_assignments_to_deactivate = DataPointAssignment.query_for_tenant(db.session).filter(
                    DataPointAssignment.field_id == field_id,
                    DataPointAssignment.series_status == 'active',
                    DataPointAssignment.series_status == 'active',
                    ~DataPointAssignment.entity_id.in_(target_entity_ids) if target_entity_ids else True
                ).all()

                # Deactivate assignments to entities not in the CSV
                for assignment in existing_assignments_to_deactivate:
                    assignment.series_status = 'inactive'
                    assignment.series_status = 'inactive'
                    db.session.add(assignment)
                    current_app.logger.info(f'Deactivated assignment for field {field_id} entity {assignment.entity_id} during import')

            except Exception as e:
                current_app.logger.error(f'Error deactivating existing assignments for field {field_id}: {str(e)}')

            # Process each entity
            field_results = []
            field_created = 0
            field_updated = 0
            field_skipped = 0

            for entity_name in assigned_entities:
                entity_name = entity_name.strip()
                entity_id = entities.get(entity_name)

                if not entity_id:
                    field_results.append({
                        'entity_name': entity_name,
                        'success': False,
                        'message': f'Entity "{entity_name}" not found in company'
                    })
                    field_skipped += 1
                    continue

                # Check for existing assignment
                existing_assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
                    field_id=field_id,
                    entity_id=entity_id,
                    series_status='active'
                ).first()

                if existing_assignment:
                    # Update existing assignment if configuration changed
                    config_changed = False
                    config_changes = {}

                    if frequency and existing_assignment.frequency != frequency:
                        config_changes['frequency'] = frequency
                        config_changed = True

                    if unit and existing_assignment.unit != unit:
                        config_changes['unit'] = unit
                        config_changed = True

                    if config_changed:
                        try:
                            # Directly update the existing assignment instead of using versioning service
                            # This avoids transaction conflicts during bulk import
                            if 'frequency' in config_changes:
                                existing_assignment.frequency = config_changes['frequency']
                            if 'unit' in config_changes:
                                existing_assignment.unit = config_changes['unit']

                            # Mark as modified for session tracking
                            db.session.add(existing_assignment)

                            field_results.append({
                                'entity_name': entity_name,
                                'success': True,
                                'message': f'Updated existing assignment configuration',
                                'action': 'updated'
                            })
                            field_updated += 1

                        except Exception as e:
                            field_results.append({
                                'entity_name': entity_name,
                                'success': False,
                                'message': f'Failed to update assignment: {str(e)}'
                            })
                            field_skipped += 1
                    else:
                        # No changes needed
                        field_results.append({
                            'entity_name': entity_name,
                            'success': True,
                            'message': 'Assignment already exists with same configuration',
                            'action': 'no_change'
                        })
                        # Don't count as skipped since it's correctly configured
                else:
                    # Create new assignment
                    try:
                        # BUG FIX: Query for latest series_version to avoid creating v1 for reactivated fields
                        # Check if there are any inactive assignments we should reactivate
                        latest_assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
                            field_id=field_id,
                            entity_id=entity_id
                        ).order_by(DataPointAssignment.series_version.desc()).first()

                        # Determine appropriate version and data_series_id
                        if latest_assignment:
                            # Reactivating existing series - use latest version and same data_series_id
                            series_version = latest_assignment.series_version
                            data_series_id = latest_assignment.data_series_id
                            current_app.logger.info(f'Import: Reactivating field {field_id} for entity {entity_id}: using v{series_version}')
                        else:
                            # First time assignment - start with v1 and new data_series_id
                            series_version = 1
                            data_series_id = str(uuid.uuid4())
                            current_app.logger.info(f'Import: New assignment for field {field_id}, entity {entity_id}: creating v1')

                        new_assignment = DataPointAssignment(
                            field_id=field_id,
                            entity_id=entity_id,
                            company_id=company_id,
                            frequency=frequency or 'Annual',
                            unit=unit,
                            data_series_id=data_series_id,
                            series_version=series_version,
                            assigned_by=1  # Use system admin user ID for imports
                        )

                        # Set additional properties after creation
                        new_assignment.series_status = 'active'
                        new_assignment.series_status = 'active'

                        db.session.add(new_assignment)

                        field_results.append({
                            'entity_name': entity_name,
                            'success': True,
                            'message': 'Created new assignment',
                            'action': 'created'
                        })
                        field_created += 1

                    except Exception as e:
                        # Rollback session on individual assignment error
                        try:
                            db.session.rollback()
                        except Exception:
                            pass  # Ignore rollback errors

                        # Add detailed logging for debugging
                        current_app.logger.error(f'Failed to create assignment for entity {entity_name} (ID: {entity_id}) and field {field_name} (ID: {field_id}): {str(e)}')
                        current_app.logger.error(f'Exception type: {type(e).__name__}')
                        current_app.logger.error(f'Assignment data: field_id={field_id}, entity_id={entity_id}, company_id={company_id}, frequency={frequency}, unit={unit}')

                        field_results.append({
                            'entity_name': entity_name,
                            'success': False,
                            'message': f'Failed to create assignment: {str(e)}'
                        })
                        field_skipped += 1

            # Build field summary
            total_field_entities = len(assigned_entities)
            field_success = field_created + field_updated

            results.append({
                'field_id': field_id,
                'field_name': field_name,
                'success': field_success > 0,
                'message': f'Processed {total_field_entities} entities: {field_created} created, {field_updated} updated, {field_skipped} skipped',
                'entities': field_results,
                'created': field_created,
                'updated': field_updated,
                'skipped': field_skipped
            })

            total_created += field_created
            total_updated += field_updated
            total_skipped += field_skipped

        # Commit all changes with better error handling
        try:
            db.session.commit()
        except Exception as commit_error:
            db.session.rollback()
            current_app.logger.error(f'Error committing import changes: {str(commit_error)}')
            return jsonify({
                'success': False,
                'error': f'Import failed during commit: {str(commit_error)}',
                'partial_results': results
            }), 500

        return jsonify({
            'success': True,
            'message': f'Import complete: {total_created} created, {total_updated} updated, {total_skipped} skipped',
            'summary': {
                'total_created': total_created,
                'total_updated': total_updated,
                'total_skipped': total_skipped,
                'total_processed': len(assignments_data)
            },
            'results': results
        })

    except Exception as e:
        # Ensure session is properly rolled back
        try:
            db.session.rollback()
        except Exception:
            pass  # Ignore rollback errors

        current_app.logger.error(f'Error importing assignments: {str(e)}')
        current_app.logger.error(f'Exception type: {type(e).__name__}')
        import traceback
        current_app.logger.error(f'Traceback: {traceback.format_exc()}')

        return jsonify({
            'success': False,
            'error': f'Import failed: {str(e)}'
        }), 500


@assignment_api_bp.route('/export', methods=['GET'])
@login_required
@admin_or_super_admin_required
@tenant_required
def export_assignments():
    """
    Export all active assignments for the current tenant to CSV format.

    Query parameters:
    - framework_id: Filter by framework (optional)
    - entity_id: Filter by entity (optional)
    - include_inactive: Include inactive assignments (default: false)

    Returns JSON with assignments array suitable for CSV export.
    """
    try:
        from sqlalchemy.orm import joinedload

        tenant = get_current_tenant()
        if not tenant:
            return jsonify({'error': 'Tenant context required'}), 403

        # Get query parameters
        framework_id = request.args.get('framework_id')
        entity_id = request.args.get('entity_id', type=int)
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

        # Base query with tenant scoping and eager loading
        query = DataPointAssignment.query.filter_by(company_id=tenant.id).options(
            joinedload(DataPointAssignment.field).joinedload(FrameworkDataField.topic),
            joinedload(DataPointAssignment.entity),
            joinedload(DataPointAssignment.assigned_by_user),
            joinedload(DataPointAssignment.assigned_topic)
        )

        # Filter by status
        if not include_inactive:
            query = query.filter(DataPointAssignment.series_status == 'active')

        # Filter by framework
        if framework_id:
            query = query.join(FrameworkDataField).filter(
                FrameworkDataField.framework_id == framework_id
            )

        # Filter by entity
        if entity_id:
            query = query.filter(DataPointAssignment.entity_id == entity_id)

        # Order by field_id and entity_id for consistent export
        query = query.order_by(
            DataPointAssignment.field_id,
            DataPointAssignment.entity_id
        )

        # Execute query
        assignments = query.all()

        # ENHANCEMENT: Group assignments by field_id and combine entity names
        # This allows one CSV row to represent multiple entities for the same field
        from collections import defaultdict
        grouped_assignments = defaultdict(lambda: {
            'field_id': None,
            'field_name': None,
            'entity_names': [],
            'frequency': None,
            'unit': None,
            'topic_name': None,
            'has_conflicts': False
        })

        for assignment in assignments:
            field_id = assignment.field_id
            entity_name = assignment.entity.name if assignment.entity else 'Unknown'
            topic_name = assignment.assigned_topic.name if assignment.assigned_topic else ''

            # Initialize or update field data
            if grouped_assignments[field_id]['field_id'] is None:
                grouped_assignments[field_id]['field_id'] = field_id
                grouped_assignments[field_id]['field_name'] = assignment.field.field_name if assignment.field else 'Unknown'
                grouped_assignments[field_id]['frequency'] = assignment.frequency
                grouped_assignments[field_id]['unit'] = assignment.unit or ''
                grouped_assignments[field_id]['topic_name'] = topic_name

            # Add entity name to the list
            grouped_assignments[field_id]['entity_names'].append(entity_name)

            # Check for conflicts (different frequency or unit for same field)
            if (grouped_assignments[field_id]['frequency'] != assignment.frequency or
                grouped_assignments[field_id]['unit'] != (assignment.unit or '')):
                grouped_assignments[field_id]['has_conflicts'] = True

        # Convert grouped data to export format
        export_data = []
        for field_id, data in grouped_assignments.items():
            if data['has_conflicts']:
                # If conflicts exist, fall back to separate rows (one per entity)
                # This preserves different settings for different entities
                for assignment in assignments:
                    if assignment.field_id == field_id:
                        topic_name = assignment.assigned_topic.name if assignment.assigned_topic else ''
                        export_data.append({
                            'field_id': assignment.field_id,
                            'field_name': assignment.field.field_name if assignment.field else 'Unknown',
                            'entity_name': assignment.entity.name if assignment.entity else 'Unknown',
                            'frequency': assignment.frequency,
                            'unit': assignment.unit or '',
                            'topic_name': topic_name,
                            'notes': ''
                        })
            else:
                # No conflicts: combine entity names with comma separator
                export_data.append({
                    'field_id': data['field_id'],
                    'field_name': data['field_name'],
                    'entity_name': ', '.join(data['entity_names']),  # Comma-separated entities
                    'frequency': data['frequency'],
                    'unit': data['unit'],
                    'topic_name': data['topic_name'],
                    'notes': ''
                })

        return jsonify({
            'success': True,
            'assignments': export_data,
            'count': len(export_data),
            'filters': {
                'framework_id': framework_id,
                'entity_id': entity_id,
                'include_inactive': include_inactive
            }
        })

    except Exception as e:
        current_app.logger.error(f'Error exporting assignments: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Export failed: {str(e)}'
        }), 500


@assignment_api_bp.route('/validate-import', methods=['POST'])
@admin_or_super_admin_required
def validate_import():
    """
    Validate CSV import file and return preview of what will be imported.
    This endpoint performs validation without actually importing anything.
    """
    try:
        data = request.get_json()
        if not data or 'assignments' not in data:
            return jsonify({'success': False, 'error': 'No assignment data provided'}), 400

        assignments_data = data['assignments']

        # Get available entities for the current tenant
        entities = Entity.query_for_tenant(db.session).all()
        entity_lookup = {entity.name.strip(): entity.id for entity in entities if entity.name}

        # Get all framework data fields to validate field IDs
        all_fields = FrameworkDataField.query.all()
        field_lookup = {field.field_id: field for field in all_fields}

        validation_results = []
        import_preview = []
        valid_count = 0
        error_count = 0
        warning_count = 0

        for assignment in assignments_data:
            field_id = (assignment.get('field_id') or '').strip()
            field_name = (assignment.get('field_name') or 'Unknown Field').strip()
            assigned_entities = assignment.get('assigned_entities', [])
            frequency = (assignment.get('frequency') or '').strip()
            unit = (assignment.get('unit') or '').strip()

            # Validation checks
            validation_issues = []
            validation_status = 'valid'

            # Check if field exists
            if not field_id:
                validation_issues.append('Missing Field ID')
                validation_status = 'error'
            elif field_id not in field_lookup:
                validation_issues.append('Field ID not found in system')
                validation_status = 'error'

            # Check entities
            valid_entities = []
            invalid_entities = []

            if assigned_entities:
                for entity_name in assigned_entities:
                    if entity_name is None or entity_name == '':
                        continue
                    # Ensure entity_name is a string before calling strip()
                    if not isinstance(entity_name, str):
                        entity_name = str(entity_name)
                    entity_name = entity_name.strip()
                    # Skip empty strings after stripping
                    if not entity_name:
                        continue
                    if entity_name in entity_lookup:
                        valid_entities.append({
                            'name': entity_name,
                            'id': entity_lookup[entity_name]
                        })
                    else:
                        invalid_entities.append(entity_name)
                        validation_issues.append(f'Entity "{entity_name}" not found')
                        if validation_status == 'valid':
                            validation_status = 'warning'
            else:
                validation_issues.append('No entities assigned')
                if validation_status == 'valid':
                    validation_status = 'warning'

            # Check frequency validation
            valid_frequencies = ['Monthly', 'Quarterly', 'Annual']
            if frequency and frequency not in valid_frequencies:
                validation_issues.append(f'Invalid frequency "{frequency}". Must be one of: {", ".join(valid_frequencies)}')
                validation_status = 'error'
            elif not frequency:
                validation_issues.append('Missing frequency')
                validation_status = 'error'

            # Check for existing assignments
            existing_assignments = []
            assignments_to_deactivate = []

            if field_id in field_lookup and valid_entities:
                valid_entity_ids = [e['id'] for e in valid_entities]

                # Check existing active assignments for this field
                existing = DataPointAssignment.query_for_tenant(db.session).filter(
                    DataPointAssignment.field_id == field_id,
                    DataPointAssignment.series_status == 'active',
                    DataPointAssignment.series_status == 'active'
                ).all()

                for existing_assignment in existing:
                    entity = next((e for e in entities if e.id == existing_assignment.entity_id), None)
                    entity_name = entity.name if entity and entity.name else f"Entity {existing_assignment.entity_id}"

                    if existing_assignment.entity_id in valid_entity_ids:
                        existing_assignments.append({
                            'entity_name': entity_name,
                            'entity_id': existing_assignment.entity_id,
                            'status': 'will_update'
                        })
                    else:
                        assignments_to_deactivate.append({
                            'entity_name': entity_name,
                            'entity_id': existing_assignment.entity_id,
                            'status': 'will_deactivate'
                        })

            # Create validation result
            if validation_status == 'valid':
                valid_count += 1
            elif validation_status == 'error':
                error_count += 1
            else:
                warning_count += 1

            validation_result = {
                'field_id': field_id,
                'field_name': field_name,
                'status': validation_status,
                'issues': validation_issues,
                'valid_entities': valid_entities,
                'invalid_entities': invalid_entities,
                'existing_assignments': existing_assignments,
                'assignments_to_deactivate': assignments_to_deactivate,
                'frequency': frequency,
                'unit': unit
            }

            validation_results.append(validation_result)

            # Add to import preview if valid
            if validation_status in ['valid', 'warning'] and valid_entities:
                import_preview.append({
                    'field_name': field_name,
                    'field_id': field_id,
                    'entities': [e['name'] for e in valid_entities],
                    'frequency': frequency,
                    'unit': unit,
                    'action': 'update' if existing_assignments else 'create',
                    'deactivations': len(assignments_to_deactivate)
                })

        return jsonify({
            'success': True,
            'validation': {
                'total_records': len(assignments_data),
                'valid_count': valid_count,
                'warning_count': warning_count,
                'error_count': error_count,
                'can_proceed': error_count == 0
            },
            'results': validation_results,
            'preview': import_preview,
            'entities_available': [{'id': e.id, 'name': e.name} for e in entities]
        })

    except Exception as e:
        current_app.logger.error(f'Error validating import: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Validation failed: {str(e)}'
        }), 500


# ============================================================================
# VERSIONING API ENDPOINTS (Frontend Compatibility)
# Added to assignment_api_bp with prefix /admin/api/assignments
# ============================================================================

@assignment_api_bp.route('/version/create', methods=['POST'])
@login_required
@admin_or_super_admin_required
@tenant_required
def create_assignment_version():
    """
    Create a new assignment with versioning support.

    This endpoint is called by the frontend VersioningModule when creating
    new assignments through the import process or manual creation.

    Expected payload:
    {
        "field_id": "uuid",
        "entity_id": 123,
        "frequency": "Annual|Quarterly|Monthly",
        "unit": "unit_code",
        "assigned_topic_id": "topic_uuid",  // optional
        "existing_assignment_id": "assignment_uuid"  // optional, for updating
    }

    Returns:
    {
        "success": true,
        "assignment": {
            "id": "new_assignment_uuid",
            "series_id": "data_series_uuid",
            "version": 1,
            "status": "active"
        }
    }
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'JSON request required'}), 400

        data = request.get_json()
        field_id = data.get('field_id')
        entity_id = data.get('entity_id')
        frequency = data.get('frequency')
        unit = data.get('unit')
        assigned_topic_id = data.get('assigned_topic_id')
        existing_assignment_id = data.get('existing_assignment_id')

        # Validate required fields
        if not field_id or not entity_id or not frequency:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: field_id, entity_id, frequency'
            }), 400

        # Get current tenant
        current_tenant = get_current_tenant()
        if not current_tenant:
            return jsonify({'success': False, 'error': 'Tenant context required'}), 403

        company_id = current_tenant.id

        # If updating existing assignment, use versioning service
        if existing_assignment_id:
            changes = {}
            if frequency:
                changes['frequency'] = frequency
            if unit:
                changes['unit'] = unit
            if assigned_topic_id:
                changes['assigned_topic_id'] = assigned_topic_id

            # Use the versioning service to create a new version
            version_result = AssignmentVersioningService.create_assignment_version(
                assignment_id=existing_assignment_id,
                changes=changes,
                reason='Updated via assignment interface',
                created_by=current_user.id
            )

            db.session.commit()

            return jsonify({
                'success': True,
                'assignment': version_result['new_assignment']
            })

        # Creating new assignment
        # Check for existing active assignment
        existing = DataPointAssignment.query_for_tenant(db.session).filter_by(
            field_id=field_id,
            entity_id=entity_id,
            series_status='active'
        ).first()

        if existing:
            # Update existing assignment instead of creating duplicate
            changes = {}
            if frequency != existing.frequency:
                changes['frequency'] = frequency
            if unit != existing.unit:
                changes['unit'] = unit
            if assigned_topic_id and assigned_topic_id != existing.assigned_topic_id:
                changes['assigned_topic_id'] = assigned_topic_id

            if changes:
                version_result = AssignmentVersioningService.create_assignment_version(
                    assignment_id=existing.id,
                    changes=changes,
                    reason='Updated via assignment interface',
                    created_by=current_user.id
                )
                db.session.commit()

                return jsonify({
                    'success': True,
                    'assignment': version_result['new_assignment']
                })
            else:
                # No changes needed
                return jsonify({
                    'success': True,
                    'assignment': {
                        'id': existing.id,
                        'series_id': existing.data_series_id,
                        'version': existing.series_version,
                        'status': existing.series_status
                    }
                })

        # Create new assignment (first version)
        new_assignment = DataPointAssignment(
            field_id=field_id,
            entity_id=entity_id,
            company_id=company_id,
            frequency=frequency,
            unit=unit,
            assigned_topic_id=assigned_topic_id,
            assigned_by=current_user.id,
            data_series_id=str(uuid.uuid4()),
            series_version=1
        )
        new_assignment.series_status = 'active'

        db.session.add(new_assignment)
        db.session.commit()

        return jsonify({
            'success': True,
            'assignment': {
                'id': new_assignment.id,
                'series_id': new_assignment.data_series_id,
                'version': new_assignment.series_version,
                'status': new_assignment.series_status
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating assignment version: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Failed to create assignment: {str(e)}'
        }), 500


@assignment_api_bp.route('/version/<assignment_id>', methods=['GET'])
@login_required
@admin_or_super_admin_required
@tenant_required
def get_assignment_version(assignment_id):
    """
    Get details for a specific assignment version.

    Returns:
    {
        "success": true,
        "assignment": {
            "id": "assignment_uuid",
            "field_id": "field_uuid",
            "entity_id": 123,
            "frequency": "Annual",
            "unit": "kg",
            "series_id": "data_series_uuid",
            "version": 1,
            "status": "active",
            "assigned_date": "2025-01-01",
            "assigned_by": "User Name"
        }
    }
    """
    try:
        # Get current tenant for security
        current_tenant = get_current_tenant()
        if not current_tenant:
            return jsonify({'success': False, 'error': 'Tenant context required'}), 403

        # Query assignment with tenant scoping
        assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
            id=assignment_id
        ).first()

        if not assignment:
            return jsonify({
                'success': False,
                'error': 'Assignment not found'
            }), 404

        # Build response
        assignment_data = {
            'id': assignment.id,
            'field_id': assignment.field_id,
            'field_name': assignment.field.field_name if assignment.field else None,
            'entity_id': assignment.entity_id,
            'entity_name': assignment.entity.name if assignment.entity else None,
            'frequency': assignment.frequency,
            'unit': assignment.unit,
            'series_id': assignment.data_series_id,
            'version': assignment.series_version,
            'status': assignment.series_status,
            'assigned_date': assignment.assigned_date.isoformat() if assignment.assigned_date else None,
            'assigned_by': assignment.assigned_by_user.name if assignment.assigned_by_user else None,
            'assigned_topic_id': assignment.assigned_topic_id,
            'topic_name': assignment.assigned_topic.name if assignment.assigned_topic else None
        }

        return jsonify({
            'success': True,
            'assignment': assignment_data
        })

    except Exception as e:
        current_app.logger.error(f'Error getting assignment version {assignment_id}: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Failed to get assignment: {str(e)}'
        }), 500


@assignment_api_bp.route('/version/<assignment_id>/supersede', methods=['PUT', 'POST'])
@login_required
@admin_or_super_admin_required
@tenant_required
def supersede_assignment_version(assignment_id):
    """
    Supersede (deactivate) an assignment version.

    This marks the assignment as inactive without creating a new version.

    Expected payload (optional):
    {
        "reason": "Reason for superseding"
    }

    Returns:
    {
        "success": true,
        "message": "Assignment superseded successfully"
    }
    """
    try:
        # Use silent=True to handle empty request bodies without error
        data = request.get_json(silent=True) or {}
        reason = data.get('reason', 'Superseded via assignment interface')

        # Use the versioning service (service method does NOT commit)
        result = AssignmentVersioningService.supersede_assignment(
            assignment_id=assignment_id,
            reason=reason
        )

        # Commit the transaction
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Assignment superseded successfully',
            'result': result
        })

    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error superseding assignment {assignment_id}: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Failed to supersede assignment: {str(e)}'
        }), 500


@assignment_api_bp.route('/version/<assignment_id>/status', methods=['PUT', 'POST'])
@login_required
@admin_or_super_admin_required
@tenant_required
def update_assignment_status(assignment_id):
    """
    Update the status of an assignment version.

    Expected payload:
    {
        "status": "active|inactive|superseded|legacy"
    }

    Returns:
    {
        "success": true,
        "message": "Assignment status updated successfully"
    }
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'JSON request required'}), 400

        data = request.get_json()
        new_status = data.get('status')

        if not new_status:
            return jsonify({'success': False, 'error': 'Missing status field'}), 400

        if new_status not in ['active', 'inactive', 'superseded', 'legacy']:
            return jsonify({'success': False, 'error': 'Invalid status value'}), 400

        # Get current tenant
        current_tenant = get_current_tenant()
        if not current_tenant:
            return jsonify({'success': False, 'error': 'Tenant context required'}), 403

        # Query assignment with tenant scoping
        assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
            id=assignment_id
        ).first()

        if not assignment:
            return jsonify({
                'success': False,
                'error': 'Assignment not found'
            }), 404

        # Update status
        old_status = assignment.series_status
        assignment.series_status = new_status

        # Log the status change
        AuditLog.log_action(
            user_id=current_user.id,
            action='UPDATE_ASSIGNMENT_STATUS',
            entity_type='DataPointAssignment',
            entity_id=assignment_id,
            payload={
                'old_status': old_status,
                'new_status': new_status,
                'assignment_id': assignment_id,
                'field_id': assignment.field_id,
                'entity_id': assignment.entity_id
            },
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Assignment status updated from {old_status} to {new_status}'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating assignment status {assignment_id}: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Failed to update status: {str(e)}'
        }), 500


# ============================================================================
# DEPENDENCY MANAGEMENT API ENDPOINTS
# ============================================================================

@assignment_api_bp.route('/validate-dependencies', methods=['POST'])
@login_required
@admin_or_super_admin_required
@tenant_required
def validate_dependencies():
    """
    Validate that all computed fields have required dependencies.

    Expected payload:
    {
        "assignments": [
            {"field_id": "xxx", "frequency": "Monthly", "entity_id": 1}
        ]
    }

    Returns:
    {
        "is_valid": true/false,
        "missing_dependencies": {},
        "frequency_conflicts": [],
        "warnings": []
    }
    """
    try:
        from ..services.dependency_service import dependency_service

        data = request.get_json()
        assignments = data.get('assignments', [])

        # Validate completeness
        completeness = dependency_service.validate_complete_assignment_set(assignments)

        # Validate frequency compatibility
        frequency_check = dependency_service.validate_frequency_compatibility(assignments)

        return jsonify({
            'is_valid': completeness['is_complete'] and frequency_check['is_valid'],
            'missing_dependencies': completeness['missing_dependencies'],
            'orphaned_computed_fields': completeness['orphaned_computed_fields'],
            'frequency_conflicts': frequency_check['conflicts'],
            'warnings': frequency_check['warnings']
        })

    except Exception as e:
        current_app.logger.error(f'Error validating dependencies: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Validation failed: {str(e)}'
        }), 500


@assignment_api_bp.route('/get-dependencies/<field_id>', methods=['GET'])
@login_required
@admin_or_super_admin_required
def get_field_dependencies(field_id):
    """
    Get all dependencies for a specific field.

    Returns:
    {
        "field_id": "xxx",
        "is_computed": true,
        "dependencies": [field objects],
        "dependency_tree": {nested structure}
    }
    """
    try:
        field = FrameworkDataField.query.get(field_id)
        if not field:
            return jsonify({'error': 'Field not found'}), 404

        if not field.is_computed:
            return jsonify({
                'field_id': field_id,
                'is_computed': False,
                'dependencies': [],
                'dependency_tree': None
            })

        dependencies = field.get_all_dependencies()
        dependency_tree = field.get_dependency_tree()

        return jsonify({
            'field_id': field_id,
            'field_name': field.field_name,
            'is_computed': True,
            'formula': field.formula_expression,
            'dependencies': [
                {
                    'field_id': dep.field_id,
                    'field_name': dep.field_name,
                    'is_computed': dep.is_computed
                } for dep in dependencies
            ],
            'dependency_tree': dependency_tree
        })

    except Exception as e:
        current_app.logger.error(f'Error getting dependencies for field {field_id}: {str(e)}')
        return jsonify({'error': f'Failed to get dependencies: {str(e)}'}), 500


@assignment_api_bp.route('/check-removal-impact', methods=['POST'])
@login_required
@admin_or_super_admin_required
@tenant_required
def check_removal_impact():
    """
    Check impact of removing fields from assignments.

    Expected payload:
    {
        "field_ids": ["field_id1", "field_id2"]
    }

    Returns:
    {
        "can_remove": true/false,
        "blocking_fields": [],
        "affected_computed_fields": []
    }
    """
    try:
        from ..services.dependency_service import dependency_service

        data = request.get_json()
        field_ids = data.get('field_ids', [])

        if not field_ids:
            return jsonify({'error': 'No field IDs provided'}), 400

        impact = dependency_service.check_removal_impact(field_ids)

        return jsonify(impact)

    except Exception as e:
        current_app.logger.error(f'Error checking removal impact: {str(e)}')
        return jsonify({'error': f'Failed to check impact: {str(e)}'}), 500


@assignment_api_bp.route('/auto-include-dependencies', methods=['POST'])
@login_required
@admin_or_super_admin_required
def auto_include_dependencies():
    """
    Get fields that should be auto-included based on selections.

    Expected payload:
    {
        "selected_fields": ["field_id1", "field_id2"],
        "existing_selections": ["field_id3", "field_id4"]
    }

    Returns:
    {
        "auto_include": [field_ids],
        "notifications": [messages],
        "total_added": count
    }
    """
    try:
        from ..services.dependency_service import dependency_service

        data = request.get_json()
        selected_fields = data.get('selected_fields', [])
        existing_selections = set(data.get('existing_selections', []))

        result = dependency_service.get_auto_include_fields(
            selected_fields, existing_selections
        )

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f'Error getting auto-include fields: {str(e)}')
        return jsonify({'error': f'Failed to get dependencies: {str(e)}'}), 500


@assignment_api_bp.route('/dependency-tree', methods=['GET'])
@login_required
@admin_or_super_admin_required
def get_dependency_tree():
    """
    Get complete dependency tree for all computed fields.

    Query params:
    - framework_id: Filter by framework (optional)

    Returns hierarchical structure of all dependencies.
    """
    try:
        framework_id = request.args.get('framework_id')

        query = FrameworkDataField.query.filter_by(is_computed=True)
        if framework_id:
            query = query.filter_by(framework_id=framework_id)

        computed_fields = query.all()

        tree = []
        for field in computed_fields:
            tree.append(field.get_dependency_tree())

        return jsonify({
            'success': True,
            'dependency_tree': tree,
            'total_computed_fields': len(tree)
        })

    except Exception as e:
        current_app.logger.error(f'Error getting dependency tree: {str(e)}')
        return jsonify({'error': f'Failed to get tree: {str(e)}'}), 500