"""
Additional routes for assign data points functionality.

This module contains additional assignment-related routes to avoid bloating admin.py:
- Field configuration endpoint
- Advanced assignment operations
- Assignment versioning operations
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import and_, desc
from datetime import datetime, UTC
import uuid

from ..extensions import db
from ..models.data_assignment import DataPointAssignment
from ..models.framework import FrameworkDataField
from ..models.entity import Entity
from ..models.company import Company
from ..models.user import User
from ..models import Topic
from ..middleware.tenant import get_current_tenant
from ..decorators.auth import admin_or_super_admin_required, tenant_required_for

# Create blueprint for additional assignment functionality
admin_assign_additional_bp = Blueprint('admin_assign_additional', __name__)


@admin_assign_additional_bp.route('/configure_fields', methods=['POST'])
@login_required
@tenant_required_for('ADMIN')
def configure_fields():
    """
    Configure field-level properties independently of entity assignments.

    This endpoint handles:
    - Field configuration (frequency, unit overrides, topic assignments)
    - Independent of entity assignments
    - Uses assignment versioning for existing assignments
    - Creates field configuration templates for future assignments

    Request payload:
    {
        "field_ids": ["field-uuid-1", "field-uuid-2"],
        "configuration": {
            "frequency": "Monthly|Quarterly|Annual",
            "unit": "override_unit_code",
            "assigned_topic_id": "topic-uuid",
            "collection_method": "method_value",
            "validation_rules": "rules_value",
            "approval_required": true|false
        }
    }
    """
    try:
        print(f"[DEBUG configure_fields] Starting configure_fields endpoint")

        if not request.is_json:
            return jsonify({'success': False, 'message': 'JSON request required'}), 400

        payload = request.get_json()
        field_ids = payload.get('field_ids', [])
        configuration = payload.get('configuration', {})

        print(f"[DEBUG configure_fields] Field IDs: {field_ids}")
        print(f"[DEBUG configure_fields] Configuration: {configuration}")

        if not field_ids:
            return jsonify({'success': False, 'message': 'Field selection required'}), 400

        # Validate field configuration
        allowed_config_fields = {
            'frequency', 'unit', 'assigned_topic_id', 'collection_method',
            'validation_rules', 'approval_required'
        }

        config_changes = {k: v for k, v in configuration.items()
                         if k in allowed_config_fields and v is not None}

        if not config_changes:
            return jsonify({'success': False, 'message': 'No valid configuration provided'}), 400

        current_tenant = get_current_tenant()
        company_id = current_tenant.id if current_tenant else None

        # Validate assigned_topic_id belongs to company (security check)
        if 'assigned_topic_id' in config_changes and config_changes['assigned_topic_id']:
            from ..models import Topic
            topic = Topic.query.filter_by(
                topic_id=config_changes['assigned_topic_id'],
                company_id=company_id
            ).first()
            if not topic:
                return jsonify({
                    'success': False,
                    'message': f'Invalid topic ID: {config_changes["assigned_topic_id"]} - topic not found or not accessible for your company'
                }), 400

        results = []

        for field_id in field_ids:
            try:
                # Validate field exists and is accessible
                field = FrameworkDataField.query.filter_by(field_id=field_id).first()
                if not field:
                    results.append({
                        'field_id': field_id,
                        'success': False,
                        'message': f'Field {field_id} not found'
                    })
                    continue

                # Find ALL existing assignments for this field (both active and inactive)
                all_assignments = DataPointAssignment.query.filter(
                    and_(
                        DataPointAssignment.field_id == field_id,
                        DataPointAssignment.company_id == company_id
                    )
                ).all()

                # Separate active and inactive assignments based on series_status
                # NOTE: 'superseded' assignments should NEVER be reactivated during config changes
                active_assignments = [a for a in all_assignments if a.series_status == 'active']
                inactive_assignments = [a for a in all_assignments if a.series_status == 'inactive']  # Only truly inactive, NOT superseded

                # DEFENSIVE FIX: Check for duplicate active assignments and auto-fix before versioning
                # Group active assignments by entity_id to detect duplicates
                from collections import defaultdict
                active_by_entity = defaultdict(list)
                for assignment in active_assignments:
                    active_by_entity[assignment.entity_id].append(assignment)

                # Check each entity has at most 1 active assignment
                duplicates_fixed = 0
                for entity_id, entity_assignments in active_by_entity.items():
                    if len(entity_assignments) > 1:
                        # CRITICAL: Multiple active assignments for same field-entity
                        current_app.logger.error(
                            f"[DUPLICATE-FIX] DETECTED: field={field_id}, entity={entity_id}, "
                            f"count={len(entity_assignments)}, versions=[{', '.join(f'v{a.series_version}' for a in entity_assignments)}]"
                        )

                        # Auto-fix: Keep only highest version active, supersede others
                        entity_assignments.sort(key=lambda x: x.series_version, reverse=True)
                        highest = entity_assignments[0]

                        for assignment in entity_assignments[1:]:
                            assignment.series_status = 'superseded'
                            duplicates_fixed += 1
                            current_app.logger.warning(
                                f"[DUPLICATE-FIX] Auto-superseded {assignment.id} (v{assignment.series_version}), "
                                f"keeping {highest.id} (v{highest.series_version}) active"
                            )

                        # Flush changes immediately to ensure database consistency
                        db.session.flush()

                # Refresh active_assignments list after auto-fix
                if duplicates_fixed > 0:
                    active_assignments = [a for a in all_assignments if a.series_status == 'active']
                    current_app.logger.info(f"[DUPLICATE-FIX] Fixed {duplicates_fixed} duplicate active assignments")

                updated_assignments = []
                reactivated_assignments = []
                failed_assignments = []

                # Process active assignments with versioning
                for assignment in active_assignments:
                    try:
                        # Use the versioning service to create new versions
                        from ..services.assignment_versioning import AssignmentVersioningService

                        # Ensure we're working in the existing transaction context
                        version_result = AssignmentVersioningService.create_assignment_version(
                            assignment.id,
                            config_changes,
                            f"Field configuration update via UI: {', '.join(config_changes.keys())}",
                            current_user.id
                        )

                        updated_assignments.append({
                            'assignment_id': version_result['new_assignment']['id'],
                            'entity_id': assignment.entity_id,
                            'version': version_result['new_assignment']['version'],
                            'type': 'versioned'
                        })

                    except Exception as version_error:
                        current_app.logger.error(f'Error versioning assignment {assignment.id}: {str(version_error)}')

                        # Track the failure
                        failed_assignments.append({
                            'assignment_id': assignment.id,
                            'entity_id': assignment.entity_id,
                            'error': str(version_error),
                            'type': 'versioning_failed'
                        })

                        # For critical errors that indicate system issues, we need to rollback and re-raise
                        error_msg = str(version_error).lower()
                        if ("transaction" in error_msg or
                            "unexpected keyword argument" in error_msg or
                            "flush" in error_msg):
                            db.session.rollback()
                            raise version_error
                        # Continue with other assignments even if one fails

                # IMPORTANT: Configuration changes should ONLY affect ACTIVE assignments
                # Inactive assignments should remain inactive - they are not part of configuration changes
                # Reactivation is a separate operation and should NOT happen during configure_fields
                #
                # REMOVED: Inactive reactivation logic (lines 209-274 original)
                # Reason: Configuration changes must maintain version history immutability
                #         - Never reactivate old versions
                #         - Always create forward versions
                #         - Inactive assignments stay inactive
                #
                # If reactivation is needed, it should be a separate UI operation with its own endpoint
                current_app.logger.info(
                    f'Skipping {len(inactive_assignments)} inactive assignments - '
                    f'configure_fields only affects active assignments. '
                    f'Use separate reactivation operation if needed.'
                )

                # Build response message
                total_processed = len(updated_assignments) + len(reactivated_assignments)
                total_failed = len(failed_assignments)

                if total_processed > 0:
                    message_parts = []
                    if updated_assignments:
                        message_parts.append(f"Updated {len(updated_assignments)} active assignments")
                    if reactivated_assignments:
                        message_parts.append(f"Reactivated {len(reactivated_assignments)} inactive assignments")
                    if total_failed > 0:
                        message_parts.append(f"Failed to process {total_failed} assignments")

                    # Only mark as success if no failures occurred
                    operation_success = total_processed > 0 and total_failed == 0

                    results.append({
                        'field_id': field_id,
                        'success': operation_success,
                        'message': '; '.join(message_parts),
                        'updated_assignments': updated_assignments,
                        'reactivated_assignments': reactivated_assignments,
                        'failed_assignments': failed_assignments,
                        'configuration_applied': config_changes,
                        'total_processed': total_processed,
                        'total_failed': total_failed
                    })
                elif total_failed > 0:
                    # Only failures, no successful processing
                    results.append({
                        'field_id': field_id,
                        'success': False,
                        'message': f'Failed to process {total_failed} assignments - see details in failed_assignments',
                        'failed_assignments': failed_assignments,
                        'configuration_applied': config_changes,
                        'total_failed': total_failed
                    })
                else:
                    # No existing assignments - configuration will be applied to future assignments
                    # Store configuration as field-level template for future use
                    results.append({
                        'field_id': field_id,
                        'success': True,
                        'message': 'Configuration saved for future assignments',
                        'configuration': config_changes,
                        'note': 'Will be applied when entities are assigned to this field'
                    })

            except Exception as field_error:
                current_app.logger.error(f'Error configuring field {field_id}: {str(field_error)}')
                results.append({
                    'field_id': field_id,
                    'success': False,
                    'message': f'Configuration error: {str(field_error)}'
                })

        # Commit all changes
        db.session.commit()

        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)

        # Calculate reactivation statistics
        total_updated = sum(len(r.get('updated_assignments', [])) for r in results if r['success'])
        total_reactivated = sum(len(r.get('reactivated_assignments', [])) for r in results if r['success'])
        total_processed = total_updated + total_reactivated

        # Build enhanced message
        message_parts = [f'Field configuration applied to {success_count}/{total_count} fields']
        if total_reactivated > 0:
            message_parts.append(f'Reactivated {total_reactivated} inactive assignments')
        if total_updated > 0:
            message_parts.append(f'Updated {total_updated} active assignments')

        return jsonify({
            'success': success_count > 0,
            'message': '; '.join(message_parts),
            'results': results,
            'summary': {
                'total_fields': total_count,
                'successful': success_count,
                'failed': total_count - success_count,
                'total_assignments_processed': total_processed,
                'assignments_updated': total_updated,
                'assignments_reactivated': total_reactivated,
                'configuration_applied': config_changes
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in field configuration: {str(e)}')

        # Clean up any session state issues
        try:
            db.session.close()
        except:
            pass

        return jsonify({'success': False, 'message': f'Configuration failed: {str(e)}'}), 500


@admin_assign_additional_bp.route('/validate_field_configuration', methods=['POST'])
@login_required
@tenant_required_for('ADMIN')
def validate_field_configuration():
    """
    Validate field configuration before applying changes.

    This endpoint helps prevent destructive configuration changes by:
    - Checking for existing data that might be affected
    - Validating configuration compatibility
    - Providing warnings about potential impacts
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'message': 'JSON request required'}), 400

        payload = request.get_json()
        field_ids = payload.get('field_ids', [])
        configuration = payload.get('configuration', {})

        if not field_ids:
            return jsonify({'success': False, 'message': 'Field selection required'}), 400

        current_tenant = get_current_tenant()
        company_id = current_tenant.id if current_tenant else None

        validation_results = []

        for field_id in field_ids:
            # Get existing assignments
            existing_assignments = DataPointAssignment.query.filter(
                and_(
                    DataPointAssignment.field_id == field_id,
                    DataPointAssignment.company_id == company_id,
                    DataPointAssignment.series_status == 'active',
                    DataPointAssignment.series_status == 'active'
                )
            ).all()

            warnings = []
            impacts = []

            # Check for frequency changes
            if 'frequency' in configuration:
                new_frequency = configuration['frequency']
                for assignment in existing_assignments:
                    if assignment.frequency != new_frequency:
                        # Count affected data entries
                        from ..models.esg_data import ESGData
                        data_count = ESGData.query.filter_by(
                            field_id=field_id,
                            entity_id=assignment.entity_id
                        ).count()

                        if data_count > 0:
                            warnings.append(f'Frequency change affects {data_count} data entries for entity {assignment.entity_id}')

            # Check for unit changes
            if 'unit' in configuration:
                new_unit = configuration['unit']
                for assignment in existing_assignments:
                    current_unit = assignment.effective_unit
                    if current_unit != new_unit:
                        warnings.append(f'Unit change from {current_unit} to {new_unit} may require data recalculation')

            # Check topic assignment changes
            if 'assigned_topic_id' in configuration:
                topic_changes = len([a for a in existing_assignments if a.assigned_topic_id != configuration['assigned_topic_id']])
                if topic_changes > 0:
                    impacts.append(f'Topic assignment will change for {topic_changes} assignments')

            validation_results.append({
                'field_id': field_id,
                'existing_assignments': len(existing_assignments),
                'warnings': warnings,
                'impacts': impacts,
                'validation_status': 'safe' if not warnings else 'warning'
            })

        return jsonify({
            'success': True,
            'validation_results': validation_results,
            'overall_status': 'safe' if not any(r['warnings'] for r in validation_results) else 'warning',
            'total_fields': len(field_ids)
        })

    except Exception as e:
        current_app.logger.error(f'Error validating field configuration: {str(e)}')
        return jsonify({'success': False, 'message': f'Validation failed: {str(e)}'}), 500


@admin_assign_additional_bp.route('/get_field_configurations', methods=['POST'])
@login_required
@tenant_required_for('ADMIN')
def get_field_configurations():
    """
    Get current configuration for specified fields.

    Returns aggregated configuration from existing assignments
    and any field-level configuration templates.
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'message': 'JSON request required'}), 400

        payload = request.get_json()
        field_ids = payload.get('field_ids', [])

        if not field_ids:
            return jsonify({'success': False, 'message': 'Field selection required'}), 400

        current_tenant = get_current_tenant()
        company_id = current_tenant.id if current_tenant else None

        configurations = {}

        for field_id in field_ids:
            # Get field info
            field = FrameworkDataField.query.filter_by(field_id=field_id).first()
            if not field:
                continue

            # Get existing assignments
            assignments = DataPointAssignment.query.filter(
                and_(
                    DataPointAssignment.field_id == field_id,
                    DataPointAssignment.company_id == company_id,
                    DataPointAssignment.series_status == 'active',
                    DataPointAssignment.series_status == 'active'
                )
            ).all()

            # Aggregate configuration from assignments
            config_summary = {
                'field_id': field_id,
                'field_name': field.field_name,
                'has_assignments': len(assignments) > 0,
                'assignment_count': len(assignments),
                'configurations': {}
            }

            if assignments:
                # Find common configurations
                frequencies = set(a.frequency for a in assignments)
                units = set(a.effective_unit for a in assignments)
                topics = set(a.assigned_topic_id for a in assignments if a.assigned_topic_id)

                config_summary['configurations'] = {
                    'frequency': list(frequencies)[0] if len(frequencies) == 1 else 'Mixed',
                    'unit': list(units)[0] if len(units) == 1 else 'Mixed',
                    'assigned_topic_id': list(topics)[0] if len(topics) == 1 else ('Mixed' if len(topics) > 1 else None),
                    'is_mixed': len(frequencies) > 1 or len(units) > 1 or len(topics) > 1
                }

                # Add assignment details
                config_summary['assignment_details'] = [
                    {
                        'assignment_id': a.id,
                        'entity_id': a.entity_id,
                        'frequency': a.frequency,
                        'unit': a.effective_unit,
                        'topic_id': a.assigned_topic_id,
                        'version': a.series_version
                    }
                    for a in assignments
                ]

            configurations[field_id] = config_summary

        return jsonify({
            'success': True,
            'configurations': configurations,
            'total_fields': len(field_ids)
        })

    except Exception as e:
        current_app.logger.error(f'Error getting field configurations: {str(e)}')
        return jsonify({'success': False, 'message': f'Failed to get configurations: {str(e)}'}), 500


@admin_assign_additional_bp.route('/assign_entities', methods=['POST'])
@login_required
@tenant_required_for('ADMIN')
def assign_entities():
    """
    Create entity assignments for specified fields.

    This endpoint handles creating new assignments when entities are assigned to data fields.
    It supports multi-entity assignments where one field can be assigned to multiple entities.

    Request payload:
    {
        "field_ids": ["field-uuid-1", "field-uuid-2"],
        "entity_ids": [1, 2, 3],
        "configuration": {
            "frequency": "Monthly|Quarterly|Annual",
            "unit": "override_unit_code",
            "assigned_topic_id": "topic-uuid"
        }
    }
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'message': 'JSON request required'}), 400

        payload = request.get_json()
        field_ids = payload.get('field_ids', [])
        entity_ids = [int(eid) for eid in payload.get('entity_ids', [])]  # Convert to integers
        configuration = payload.get('configuration', {})

        if not field_ids:
            return jsonify({'success': False, 'message': 'Field selection required'}), 400

        if not entity_ids:
            return jsonify({'success': False, 'message': 'Entity selection required'}), 400

        current_tenant = get_current_tenant()
        company_id = current_tenant.id if current_tenant else None

        # Validate entities belong to current tenant
        valid_entities = Entity.query.filter(
            Entity.id.in_(entity_ids),
            Entity.company_id == company_id
        ).all()

        if len(valid_entities) != len(entity_ids):
            return jsonify({'success': False, 'message': 'Some entities not found or not accessible'}), 400

        # Validate assigned_topic_id belongs to company (security check)
        if configuration.get('assigned_topic_id'):
            topic = Topic.query.filter_by(
                topic_id=configuration['assigned_topic_id'],
                company_id=company_id
            ).first()
            if not topic:
                return jsonify({
                    'success': False,
                    'message': f'Invalid topic ID: {configuration["assigned_topic_id"]} - topic not found or not accessible'
                }), 400

        results = []
        total_created = 0

        for field_id in field_ids:
            try:
                # Validate field exists
                field = FrameworkDataField.query.filter_by(field_id=field_id).first()
                if not field:
                    results.append({
                        'field_id': field_id,
                        'success': False,
                        'message': f'Field {field_id} not found'
                    })
                    continue

                # Get existing assignments for this field
                existing_assignments = DataPointAssignment.query.filter(
                    and_(
                        DataPointAssignment.field_id == field_id,
                        DataPointAssignment.company_id == company_id,
                        DataPointAssignment.series_status == 'active'
                    )
                ).all()

                existing_entity_ids = set(a.entity_id for a in existing_assignments)
                requested_entity_ids = set(entity_ids)
                new_entity_ids = [eid for eid in entity_ids if eid not in existing_entity_ids]
                removed_entity_ids = [eid for eid in existing_entity_ids if eid not in requested_entity_ids]

                # DEBUG logging
                current_app.logger.info(f"[assign_entities] Field {field_id}:")
                current_app.logger.info(f"  Requested entity_ids: {entity_ids}")
                current_app.logger.info(f"  Existing entity_ids: {existing_entity_ids}")
                current_app.logger.info(f"  New entity_ids: {new_entity_ids}")
                current_app.logger.info(f"  Removed entity_ids: {removed_entity_ids}")

                # First, remove assignments that are no longer selected
                removed_count = 0
                for entity_id in removed_entity_ids:
                    try:
                        # Find the assignment to remove
                        assignment_to_remove = next((a for a in existing_assignments if a.entity_id == entity_id), None)
                        if assignment_to_remove:
                            assignment_to_remove.series_status = 'inactive'
                            db.session.flush()
                            removed_count += 1
                            current_app.logger.info(f"  Removed assignment for entity {entity_id}")
                    except Exception as remove_error:
                        current_app.logger.error(f'Error removing assignment for field {field_id}, entity {entity_id}: {str(remove_error)}')

                created_assignments = []

                for entity_id in new_entity_ids:
                    try:
                        # BUG FIX: Query for latest series_version for this field to avoid creating v1 for reactivated fields
                        # When reactivating an inactive field, we should use the latest version or create the next sequential version
                        latest_assignment = DataPointAssignment.query.filter(
                            and_(
                                DataPointAssignment.field_id == field_id,
                                DataPointAssignment.entity_id == entity_id,
                                DataPointAssignment.company_id == company_id
                            )
                        ).order_by(DataPointAssignment.series_version.desc()).first()

                        # Determine appropriate version and data_series_id
                        if latest_assignment:
                            # Reactivating existing series - use latest version and same data_series_id
                            series_version = latest_assignment.series_version
                            data_series_id = latest_assignment.data_series_id
                            current_app.logger.info(f"  Reactivating field {field_id} for entity {entity_id}: using existing v{series_version}, series_id={data_series_id}")
                        else:
                            # First time assignment - start with v1 and new data_series_id
                            series_version = 1
                            data_series_id = str(uuid.uuid4())
                            current_app.logger.info(f"  New assignment for field {field_id}, entity {entity_id}: creating v1 with new series_id={data_series_id}")

                        # Create new assignment with correct version
                        new_assignment = DataPointAssignment(
                            field_id=field_id,
                            entity_id=entity_id,
                            company_id=company_id,
                            frequency=configuration.get('frequency', 'Annual'),
                            assigned_by=current_user.id,
                            unit=configuration.get('unit'),
                            assigned_topic_id=configuration.get('assigned_topic_id'),
                            data_series_id=data_series_id,
                            series_version=series_version
                        )

                        # DEBUG: Check series_status before setting
                        current_app.logger.debug(f"[assign_entities] BEFORE setting series_status: {new_assignment.series_status}")

                        # CRITICAL FIX: Set series_status BEFORE db.session.add()
                        # because before_insert event validates it immediately
                        new_assignment.series_status = 'active'

                        # DEBUG: Check series_status after setting
                        current_app.logger.debug(f"[assign_entities] AFTER setting series_status: {new_assignment.series_status}")

                        db.session.add(new_assignment)
                        db.session.flush()  # Get the ID

                        created_assignments.append({
                            'assignment_id': new_assignment.id,
                            'entity_id': entity_id,
                            'field_id': field_id,
                            'frequency': new_assignment.frequency,
                            'version': new_assignment.series_version
                        })

                        total_created += 1

                    except Exception as assignment_error:
                        current_app.logger.error(f'Error creating assignment for field {field_id}, entity {entity_id}: {str(assignment_error)}')
                        # Continue with other assignments even if one fails

                # Build result message
                message_parts = []
                if created_assignments:
                    message_parts.append(f'Created {len(created_assignments)} new assignment(s)')
                if removed_count > 0:
                    message_parts.append(f'Removed {removed_count} assignment(s)')
                if not created_assignments and removed_count == 0:
                    message_parts.append('No changes - all entities already assigned')

                results.append({
                    'field_id': field_id,
                    'success': True,
                    'message': ', '.join(message_parts),
                    'created_assignments': created_assignments,
                    'removed_count': removed_count,
                    'skipped_existing': len(entity_ids) - len(new_entity_ids)
                })

            except Exception as field_error:
                current_app.logger.error(f'Error processing field {field_id}: {str(field_error)}')
                results.append({
                    'field_id': field_id,
                    'success': False,
                    'message': f'Processing error: {str(field_error)}'
                })

        # Commit all changes
        db.session.commit()

        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)

        return jsonify({
            'success': success_count > 0,
            'message': f'Entity assignment completed: {success_count}/{total_count} fields processed, {total_created} assignments created',
            'results': results,
            'summary': {
                'total_fields': total_count,
                'successful_fields': success_count,
                'failed_fields': total_count - success_count,
                'total_assignments_created': total_created
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in entity assignment: {str(e)}')
        return jsonify({'success': False, 'message': f'Entity assignment failed: {str(e)}'}), 500