"""
Assignment History Blueprint for ESG DataVault.

This module implements Phase 5 of the Main Assignment System Implementation:
Admin Interface Enhancements - Assignment History View.

Features:
- Timeline of assignment evolution
- Change tracking with reasons
- Link to affected ESGData entries  
- Visual representation of data series
- Interactive filtering and search
"""

from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from datetime import date, datetime
from sqlalchemy import desc, and_, or_, func
from sqlalchemy.orm import joinedload

from ..models.data_assignment import DataPointAssignment
from ..models.framework import FrameworkDataField
from ..models.entity import Entity
from ..models.esg_data import ESGData
from ..models.user import User
from ..extensions import db
from ..middleware.tenant import get_current_tenant
from ..services.assignment_versioning import AssignmentVersioningService

assignment_history_bp = Blueprint('assignment_history', __name__, url_prefix='/admin/assignment-history')


def require_tenant_for_admin():
    """Decorator to ensure admin users access via their company subdomain"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # SUPER_ADMIN must use impersonation to access admin pages
            if current_user.role == 'SUPER_ADMIN':
                tenant = get_current_tenant()
                if not tenant:
                    flash('Please select a company to manage by using the impersonation feature.', 'info')
                    return redirect(url_for('superadmin.dashboard'))
                return f(*args, **kwargs)
            
            # Admin users must have tenant context
            tenant = get_current_tenant()
            if not tenant:
                if current_user.company_id:
                    # Logic to redirect to company subdomain would go here
                    flash('Please access admin features via your company subdomain.', 'info')
                    return redirect(url_for('auth.login'))
                flash('Access denied. Admin users must access via company subdomain.', 'error')
                return redirect(url_for('auth.login'))
            
            # Verify tenant matches admin's company
            if current_user.company_id != tenant.id:
                flash('Access denied. Tenant mismatch.', 'error')
                return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@assignment_history_bp.route('/')
@login_required
@require_tenant_for_admin()
def assignment_history():
    """
    Display the assignment history timeline interface.
    
    Shows chronological view of all assignment changes in the current company
    with filtering and search capabilities.
    """
    tenant = get_current_tenant()
    
    # Get summary statistics for the overview
    stats = get_assignment_history_stats(tenant.id)
    
    return render_template(
        'admin/assignment_history.html',
        stats=stats,
        current_tenant=tenant
    )


@assignment_history_bp.route('/api/timeline')
@login_required
@require_tenant_for_admin()
def assignment_timeline_api():
    """
    API endpoint to fetch assignment timeline data with filtering support.
    
    Query parameters:
    - field_id: Filter by specific field
    - entity_id: Filter by specific entity
    - data_series_id: Filter by specific data series
    - date_from: Filter assignments from date (YYYY-MM-DD)
    - date_to: Filter assignments to date (YYYY-MM-DD)
    - search: Search in field names, entity names, or reasons
    - page: Page number for pagination (default: 1)
    - per_page: Items per page (default: 20)
    """
    tenant = get_current_tenant()
    
    # Get query parameters
    field_id = request.args.get('field_id')
    entity_id = request.args.get('entity_id', type=int)
    data_series_id = request.args.get('data_series_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)  # Cap at 100
    
    try:
        # Base query with tenant scoping and eager loading
        from ..models.framework import Topic
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
            search_filter = or_(
                DataPointAssignment.field.has(FrameworkDataField.field_name.ilike(f'%{search}%')),
                DataPointAssignment.entity.has(Entity.name.ilike(f'%{search}%')),
                DataPointAssignment.assigned_by_user.has(User.name.ilike(f'%{search}%'))
            )
            query = query.filter(search_filter)
        
        # Order by assigned date (newest first) and version
        query = query.order_by(
            desc(DataPointAssignment.assigned_date),
            desc(DataPointAssignment.series_version)
        )
        
        # Paginate results
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        assignments = pagination.items
        
        # Format timeline data
        timeline_data = []
        for assignment in assignments:
            # Get data entry count for this assignment
            data_count = assignment.get_data_entry_count()
            
            # Get changes from previous version if exists
            changes_summary = get_assignment_changes_summary(assignment)
            
            timeline_item = {
                'id': assignment.id,
                'field_name': assignment.field.field_name if assignment.field else 'Unknown Field',
                'entity_name': assignment.entity.name if assignment.entity else 'Unknown Entity',
                'frequency': assignment.frequency,
                'unit': assignment.effective_unit,
                'series_id': assignment.data_series_id,
                'version': assignment.series_version,
                'status': assignment.series_status,
                'assigned_date': assignment.assigned_date.isoformat() if assignment.assigned_date else None,
                'assigned_by': assignment.assigned_by_user.name if assignment.assigned_by_user else 'Unknown',
                'data_entry_count': data_count,
                'changes_summary': changes_summary,
                'version_display': assignment.version_display,
                'status_display': assignment.status_display,
                'is_active': assignment.series_status == 'active',
                # Add topic-related properties for field information modal
                'effective_topic_name': assignment.effective_topic_name,
                'assigned_topic_name': assignment.assigned_topic.name if assignment.assigned_topic else None,
                'field_topic_name': assignment.field.topic.name if assignment.field and assignment.field.topic else None,
                'effective_topic_path': assignment.effective_topic_path
            }
            
            timeline_data.append(timeline_item)
        
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
        current_app.logger.error(f'Error fetching assignment timeline: {str(e)}')
        return jsonify({'error': 'Failed to fetch assignment timeline'}), 500


@assignment_history_bp.route('/api/series/<series_id>')
@login_required
@require_tenant_for_admin()
def data_series_details_api(series_id):
    """
    API endpoint to get detailed information about a specific data series.
    
    Returns all versions in the series with change tracking and data impact analysis.
    """
    tenant = get_current_tenant()
    
    try:
        # Get all assignments in this data series
        assignments = DataPointAssignment.query.filter(
            and_(
                DataPointAssignment.data_series_id == series_id,
                DataPointAssignment.company_id == tenant.id
            )
        ).options(
            joinedload(DataPointAssignment.field),
            joinedload(DataPointAssignment.entity),
            joinedload(DataPointAssignment.assigned_by_user)
        ).order_by(DataPointAssignment.series_version).all()
        
        if not assignments:
            return jsonify({'error': 'Data series not found'}), 404
        
        # Build version history with changes
        version_history = []
        previous_assignment = None
        
        for assignment in assignments:
            version_data = {
                'id': assignment.id,
                'version': assignment.series_version,
                'status': assignment.series_status,
                'assigned_date': assignment.assigned_date.isoformat() if assignment.assigned_date else None,
                'assigned_by': assignment.assigned_by_user.name if assignment.assigned_by_user else 'Unknown',
                'frequency': assignment.frequency,
                'unit': assignment.effective_unit,
                'data_entry_count': assignment.get_data_entry_count(),
                'is_active': assignment.series_status == 'active'
            }
            
            # Calculate changes from previous version
            if previous_assignment:
                changes = []
                if previous_assignment.frequency != assignment.frequency:
                    changes.append({
                        'field': 'frequency',
                        'old_value': previous_assignment.frequency,
                        'new_value': assignment.frequency
                    })
                
                if previous_assignment.effective_unit != assignment.effective_unit:
                    changes.append({
                        'field': 'unit',
                        'old_value': previous_assignment.effective_unit,
                        'new_value': assignment.effective_unit
                    })
                
                version_data['changes'] = changes
            else:
                version_data['changes'] = []
            
            version_history.append(version_data)
            previous_assignment = assignment
        
        # Get series summary
        current_assignment = next((a for a in assignments if a.series_status == 'active'), assignments[-1])
        series_summary = {
            'series_id': series_id,
            'field_name': current_assignment.field.field_name if current_assignment.field else 'Unknown Field',
            'entity_name': current_assignment.entity.name if current_assignment.entity else 'Unknown Entity',
            'total_versions': len(assignments),
            'current_version': current_assignment.series_version,
            'first_assigned': assignments[0].assigned_date.isoformat() if assignments[0].assigned_date else None,
            'last_updated': assignments[-1].assigned_date.isoformat() if assignments[-1].assigned_date else None
        }
        
        return jsonify({
            'series_summary': series_summary,
            'version_history': version_history
        })
        
    except Exception as e:
        current_app.logger.error(f'Error fetching data series details: {str(e)}')
        return jsonify({'error': 'Failed to fetch data series details'}), 500


@assignment_history_bp.route('/api/data-entries/<assignment_id>')
@login_required
@require_tenant_for_admin()
def assignment_data_entries_api(assignment_id):
    """
    API endpoint to get ESG data entries affected by a specific assignment.
    
    Returns list of data entries with dates, values, and entry details.
    """
    tenant = get_current_tenant()
    
    try:
        # Verify assignment belongs to current tenant
        assignment = DataPointAssignment.query.filter(
            and_(
                DataPointAssignment.id == assignment_id,
                DataPointAssignment.company_id == tenant.id
            )
        ).first()
        
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        # Get data entries linked to this assignment (direct links)
        direct_entries = ESGData.query.filter_by(assignment_id=assignment_id).options(
            joinedload(ESGData.created_by_user)
        ).order_by(desc(ESGData.reporting_date)).limit(100).all()  # Limit for performance
        
        # Get data entries linked by field+entity (legacy pattern)
        legacy_entries = ESGData.query.filter(
            and_(
                ESGData.field_id == assignment.field_id,
                ESGData.entity_id == assignment.entity_id,
                ESGData.assignment_id.is_(None)  # Only unlinked entries
            )
        ).options(
            joinedload(ESGData.created_by_user)
        ).order_by(desc(ESGData.reporting_date)).limit(50).all()  # Fewer legacy entries
        
        # Format data entries
        data_entries = []
        
        # Process direct entries
        for entry in direct_entries:
            data_entries.append({
                'id': entry.id,
                'reporting_date': entry.reporting_date.isoformat() if entry.reporting_date else None,
                'raw_value': entry.raw_value,
                'unit': entry.unit,
                'link_type': 'direct',
                'created_at': entry.created_at.isoformat() if entry.created_at else None,
                'created_by': entry.created_by_user.username if entry.created_by_user else 'Unknown',
                'has_file': bool(entry.file_path)
            })
        
        # Process legacy entries
        for entry in legacy_entries:
            data_entries.append({
                'id': entry.id,
                'reporting_date': entry.reporting_date.isoformat() if entry.reporting_date else None,
                'raw_value': entry.raw_value,
                'unit': entry.unit,
                'link_type': 'legacy',
                'created_at': entry.created_at.isoformat() if entry.created_at else None,
                'created_by': entry.created_by_user.username if entry.created_by_user else 'Unknown',
                'has_file': bool(entry.file_path)
            })
        
        # Sort all entries by reporting date (newest first)
        data_entries.sort(key=lambda x: x['reporting_date'] or '', reverse=True)
        
        return jsonify({
            'assignment_info': {
                'id': assignment.id,
                'field_name': assignment.field.field_name if assignment.field else 'Unknown Field',
                'entity_name': assignment.entity.name if assignment.entity else 'Unknown Entity',
                'version': assignment.series_version,
                'frequency': assignment.frequency
            },
            'data_entries': data_entries,
            'summary': {
                'total_entries': len(data_entries),
                'direct_entries': len(direct_entries),
                'legacy_entries': len(legacy_entries)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Error fetching assignment data entries: {str(e)}')
        return jsonify({'error': 'Failed to fetch data entries'}), 500


@assignment_history_bp.route('/api/filters')
@login_required
@require_tenant_for_admin()
def assignment_filters_api():
    """
    API endpoint to get filter options for the assignment history interface.
    
    Returns available fields, entities, and date ranges for filtering.
    """
    tenant = get_current_tenant()
    
    try:
        # Get unique fields used in assignments
        field_query = db.session.query(
            FrameworkDataField.field_id,
            FrameworkDataField.field_name
        ).join(
            DataPointAssignment, DataPointAssignment.field_id == FrameworkDataField.field_id
        ).filter(
            DataPointAssignment.company_id == tenant.id
        ).distinct().order_by(FrameworkDataField.field_name).all()
        
        fields = [{'id': f.field_id, 'name': f.field_name} for f in field_query]
        
        # Get unique entities used in assignments
        entity_query = db.session.query(
            Entity.id,
            Entity.name
        ).join(
            DataPointAssignment, DataPointAssignment.entity_id == Entity.id
        ).filter(
            DataPointAssignment.company_id == tenant.id
        ).distinct().order_by(Entity.name).all()
        
        entities = [{'id': e.id, 'name': e.name} for e in entity_query]
        
        # Get date range
        date_range = db.session.query(
            func.min(DataPointAssignment.assigned_date).label('min_date'),
            func.max(DataPointAssignment.assigned_date).label('max_date')
        ).filter(
            DataPointAssignment.company_id == tenant.id
        ).first()
        
        date_range_info = {
            'min_date': date_range.min_date.isoformat() if date_range.min_date else None,
            'max_date': date_range.max_date.isoformat() if date_range.max_date else None
        }
        
        return jsonify({
            'fields': fields,
            'entities': entities,
            'date_range': date_range_info
        })
        
    except Exception as e:
        current_app.logger.error(f'Error fetching filter options: {str(e)}')
        return jsonify({'error': 'Failed to fetch filter options'}), 500


def get_assignment_history_stats(company_id):
    """Get summary statistics for assignment history overview."""
    try:
        # Total assignments
        total_assignments = DataPointAssignment.query.filter_by(company_id=company_id).count()
        
        # Active assignments (must have both series_status='active' AND is_active=True)
        active_assignments = DataPointAssignment.query.filter(
            and_(
                DataPointAssignment.company_id == company_id,
                DataPointAssignment.series_status == 'active',
                DataPointAssignment.series_status == 'active'
            )
        ).count()
        
        # Total data series
        total_series = db.session.query(DataPointAssignment.data_series_id).filter(
            DataPointAssignment.company_id == company_id
        ).distinct().count()
        
        # Assignments with versions > 1 (i.e., have been modified)
        versioned_assignments = DataPointAssignment.query.filter(
            and_(
                DataPointAssignment.company_id == company_id,
                DataPointAssignment.series_version > 1
            )
        ).count()
        
        return {
            'total_assignments': total_assignments,
            'active_assignments': active_assignments,
            'total_series': total_series,
            'versioned_assignments': versioned_assignments
        }
        
    except Exception as e:
        current_app.logger.error(f'Error calculating assignment history stats: {str(e)}')
        return {
            'total_assignments': 0,
            'active_assignments': 0,
            'total_series': 0,
            'versioned_assignments': 0
        }


def get_assignment_changes_summary(assignment):
    """Get a summary of changes made in this assignment version."""
    try:
        if assignment.series_version <= 1:
            return 'Initial assignment'
        
        # Get the previous version in the same series
        previous_version = DataPointAssignment.query.filter(
            and_(
                DataPointAssignment.data_series_id == assignment.data_series_id,
                DataPointAssignment.series_version == assignment.series_version - 1
            )
        ).first()
        
        if not previous_version:
            return 'Version history unavailable'
        
        changes = []
        
        # Check for frequency changes
        if previous_version.frequency != assignment.frequency:
            changes.append(f'Frequency: {previous_version.frequency} → {assignment.frequency}')
        
        # Check for unit changes
        if previous_version.effective_unit != assignment.effective_unit:
            changes.append(f'Unit: {previous_version.effective_unit or "None"} → {assignment.effective_unit or "None"}')
        
        # Check for topic changes
        if previous_version.assigned_topic_id != assignment.assigned_topic_id:
            changes.append('Material topic assignment changed')
        
        if not changes:
            return 'Minor updates'
        
        return '; '.join(changes)
        
    except Exception as e:
        current_app.logger.error(f'Error generating changes summary: {str(e)}')
        return 'Changes unavailable'