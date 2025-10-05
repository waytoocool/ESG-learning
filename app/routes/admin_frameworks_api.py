from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_
from ..decorators.auth import admin_or_super_admin_required, tenant_required

# Local helper to check super admin without causing circular import
from flask_login import current_user as _cu

def _is_super_admin():
    return getattr(_cu, 'role', None) == 'SUPER_ADMIN'

from ..services import frameworks_service
from ..models.framework import Topic  # Needed for hierarchical topics tree

admin_frameworks_api_bp = Blueprint('admin_frameworks_api', __name__, url_prefix='/admin/frameworks')

# BUG FIX #3: Add /admin/frameworks endpoint (alias for /admin/frameworks/list)
@admin_frameworks_api_bp.route('/', methods=['GET'])
@admin_frameworks_api_bp.route('', methods=['GET'])
@login_required
@admin_or_super_admin_required
@tenant_required
def get_frameworks():
    """
    API endpoint to get all frameworks (company-specific + global).
    This is an alias for /admin/frameworks/list for backward compatibility.
    """
    try:
        company_id = current_user.company_id
        frameworks = frameworks_service.list_frameworks(company_id, include_global=True)
        return jsonify(frameworks)
    except Exception as e:
        current_app.logger.error(f"Error listing frameworks: {str(e)}")
        return jsonify({'error': 'Failed to list frameworks'}), 500

@admin_frameworks_api_bp.route('/create_initial', methods=['POST'])
@login_required
@admin_or_super_admin_required
@tenant_required
def create_initial_framework_api():
    """API endpoint to create an initial framework with just name and description."""
    try:
        company_id = current_user.company_id
        data = request.get_json()
        name = data.get('framework_name')
        description = data.get('description')

        if not name or not description:
            return jsonify({'success': False, 'error': 'Framework name and description are required'}), 400

        framework_id = frameworks_service.create_initial_framework(company_id, name, description)
        return jsonify({'success': True, 'framework_id': framework_id}), 201
    except Exception as e:
        current_app.logger.error(f"Error creating initial framework: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create initial framework'}), 500

@admin_frameworks_api_bp.route('/add_topics/<framework_id>', methods=['POST'])
@login_required
@admin_or_super_admin_required
@tenant_required
def add_topics_to_framework_api(framework_id):
    """API endpoint to add topics to an existing framework."""
    try:
        company_id = current_user.company_id
        topics_data = request.get_json()

        if not isinstance(topics_data, list):
            return jsonify({'success': False, 'error': 'Topics data must be a list'}), 400

        frameworks_service.add_topics_to_framework(framework_id, company_id, topics_data)
        return jsonify({'success': True, 'message': 'Topics added successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error adding topics to framework {framework_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to add topics'}), 500

@admin_frameworks_api_bp.route('/add_data_points/<framework_id>', methods=['POST'])
@login_required
@admin_or_super_admin_required
@tenant_required
def add_data_points_to_framework_api(framework_id):
    """API endpoint to add data points to an existing framework."""
    try:
        company_id = current_user.company_id
        data_points_data = request.get_json()

        if not isinstance(data_points_data, list):
            return jsonify({'success': False, 'error': 'Data points data must be a list'}), 400

        frameworks_service.add_data_points_to_framework(framework_id, company_id, data_points_data)
        return jsonify({'success': True, 'message': 'Data points added successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error adding data points to framework {framework_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to add data points'}), 500

@admin_frameworks_api_bp.route('/<framework_id>/topics')
@login_required
@admin_or_super_admin_required
@tenant_required
def get_framework_topics(framework_id):
    """API endpoint to return a hierarchical topic tree (with field counts) for a framework."""
    try:
        # Fetch all topics linked to this framework (company-specific filtering not required here
        # because framework_id is globally unique and already tied to a single company).
        topics = Topic.query.filter_by(framework_id=framework_id).all()

        # Build nested structure identical to legacy admin.py implementation
        def build_topic_tree(parent_id=None):
            children = []
            for topic in topics:
                if topic.parent_id == parent_id:
                    children.append({
                        'topic_id': topic.topic_id,
                        'name': topic.name,
                        'description': topic.description,
                        'level': topic.level,
                        'full_path': topic.get_full_path(),
                        'field_count': len(topic.data_fields),
                        'children': build_topic_tree(topic.topic_id)
                    })
            return children

        topic_tree = build_topic_tree()
        return jsonify(topic_tree)
    except Exception as e:
        current_app.logger.error(f"Error getting topics for framework {framework_id}: {str(e)}")
        return jsonify({'error': 'Failed to get topics'}), 500

@admin_frameworks_api_bp.route('/<framework_id>/data_points')
@login_required
@admin_or_super_admin_required
@tenant_required
def get_framework_data_points(framework_id):
    """API endpoint to get all data points for a given framework."""
    try:
        company_id = current_user.company_id
        data_points = frameworks_service.get_data_points_for_framework(framework_id, company_id)
        return jsonify({'success': True, 'data_points': data_points})
    except Exception as e:
        current_app.logger.error(f"Error getting data points for framework {framework_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get data points'}), 500

@admin_frameworks_api_bp.route('/<framework_id>/topics/<topic_id>', methods=['DELETE'])
@login_required
@admin_or_super_admin_required
@tenant_required
def delete_framework_topic(framework_id, topic_id):
    """API endpoint to delete a topic from a specific framework."""
    try:
        company_id = current_user.company_id
        frameworks_service.delete_topic_from_framework(framework_id, topic_id, company_id)
        return jsonify({'success': True, 'message': 'Topic deleted successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting topic {topic_id} from framework {framework_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete topic'}), 500

@admin_frameworks_api_bp.route('/<framework_id>/data_points/<field_id>', methods=['DELETE'])
@login_required
@admin_or_super_admin_required
@tenant_required
def delete_framework_data_point(framework_id, field_id):
    """API endpoint to delete a data point from a specific framework."""
    try:
        company_id = current_user.company_id
        frameworks_service.delete_data_point_from_framework(framework_id, field_id, company_id)
        return jsonify({'success': True, 'message': 'Data point deleted successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting data point {field_id} from framework {framework_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete data point'}), 500

@admin_frameworks_api_bp.route('/<framework_id>/data_points/<field_id>', methods=['PUT'])
@login_required
@admin_or_super_admin_required
@tenant_required
def update_framework_data_point(framework_id, field_id):
    """API endpoint to update a data point in a specific framework."""
    try:
        company_id = current_user.company_id
        data_point_data = request.get_json()

        if not data_point_data:
            return jsonify({'success': False, 'error': 'Request data is required'}), 400

        updated_field = frameworks_service.update_data_point(framework_id, field_id, company_id, data_point_data)
        
        if not updated_field:
            return jsonify({'success': False, 'error': 'Data point not found or access denied'}), 404
            
        return jsonify({'success': True, 'message': 'Data point updated successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error updating data point {field_id} in framework {framework_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update data point'}), 500

@admin_frameworks_api_bp.route('/stats')
@login_required
@admin_or_super_admin_required
@tenant_required
def get_framework_stats():
    """API endpoint to get high-level statistics for frameworks dashboard."""
    try:
        company_id = current_user.company_id
        stats = frameworks_service.get_framework_kpis(company_id)
        return jsonify({'success': True, **stats})
    except Exception as e:
        current_app.logger.error(f"Error getting framework stats: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get framework stats'}), 500

@admin_frameworks_api_bp.route('/chart_data')
@login_required
@admin_or_super_admin_required
@tenant_required
def get_framework_chart_data():
    """API endpoint to get data for framework charts (top 5 coverage, global vs company-specific)."""
    try:
        company_id = current_user.company_id
        chart_data = frameworks_service.get_chart_data(company_id)
        return jsonify({'success': True, **chart_data})
    except Exception as e:
        current_app.logger.error(f"Error getting framework chart data: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get framework chart data'}), 500

@admin_frameworks_api_bp.route('/list')
@login_required
@admin_or_super_admin_required
@tenant_required
def list_frameworks():
    """API endpoint to list frameworks with search and sort options. Includes global and company-specific frameworks."""
    try:
        company_id = current_user.company_id
        search_term = request.args.get('search')
        sort_by = request.args.get('sort')
        include_global = request.args.get('include_global', 'true').lower() == 'true'
        
        frameworks = frameworks_service.list_frameworks(company_id, search=search_term, sort=sort_by, include_global=include_global)
        return jsonify({'success': True, 'frameworks': frameworks})
    except Exception as e:
        current_app.logger.error(f"Error listing frameworks: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to list frameworks'}), 500

@admin_frameworks_api_bp.route('/coverage/<framework_id>')
@login_required
@admin_or_super_admin_required
@tenant_required
def get_framework_coverage(framework_id):
    """API endpoint to get coverage statistics for a single framework."""
    try:
        company_id = current_user.company_id
        coverage_data = frameworks_service.get_framework_coverage(framework_id, company_id)
        if not coverage_data:
            return jsonify({'success': False, 'error': 'Framework not found or access denied'}), 404
        return jsonify({'success': True, **coverage_data})
    except Exception as e:
        current_app.logger.error(f"Error getting framework coverage for {framework_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get framework coverage'}), 500

@admin_frameworks_api_bp.route('/recent_activity')
@login_required
@admin_or_super_admin_required
@tenant_required
def get_recent_activity():
    """API endpoint to get recent activity related to frameworks and data points."""
    try:
        company_id = current_user.company_id
        activities = frameworks_service.get_recent_activity(company_id)
        return jsonify({'success': True, 'activities': activities})
    except Exception as e:
        current_app.logger.error(f"Error fetching recent activity: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch recent activity'}), 500

@admin_frameworks_api_bp.route('/<framework_id>/details')
@login_required
@admin_or_super_admin_required
@tenant_required
def get_framework_details(framework_id):
    """API endpoint to get detailed information for a single framework."""
    try:
        company_id = current_user.company_id
        framework_details = frameworks_service.get_single_framework_details(framework_id, company_id)
        if not framework_details:
            return jsonify({'success': False, 'error': 'Framework not found or access denied'}), 404
        return jsonify({'success': True, **framework_details})
    except Exception as e:
        current_app.logger.error(f"Error getting framework details for {framework_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get framework details'}), 500

@admin_frameworks_api_bp.route('/<framework_id>/type')
@login_required
@admin_or_super_admin_required
@tenant_required
def get_framework_type(framework_id):
    """API endpoint to get framework type information (global vs company-specific)."""
    try:
        company_id = current_user.company_id
        type_info = frameworks_service.get_framework_type_info(framework_id, company_id)
        if not type_info['framework_exists']:
            return jsonify({'success': False, 'error': 'Framework not found'}), 404
        return jsonify({'success': True, **type_info})
    except Exception as e:
        current_app.logger.error(f"Error getting framework type for {framework_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get framework type'}), 500

@admin_frameworks_api_bp.route('/all_topics_tree')
@login_required
@admin_or_super_admin_required
@tenant_required
def get_all_topics_hierarchical():
    """API endpoint for redesigned assign data points page: returns hierarchical topic tree. Can be filtered by framework."""
    try:
        company_id = current_user.company_id
        framework_id = request.args.get('framework_id')  # Optional framework filter
        
        # Import here to avoid circular imports
        from ..models.framework import Framework, FrameworkDataField
        
        # Get frameworks for this company (filtered or all) - includes global frameworks only
        from ..models.company import Company
        global_provider = Company.get_global_provider()
        global_provider_id = global_provider.id if global_provider else None

        if framework_id:
            # Check if specific framework exists and is accessible (company-specific or global only)
            framework = Framework.query.filter_by(framework_id=framework_id).first()
            if framework and (framework.company_id == company_id or
                            (global_provider_id and framework.company_id == global_provider_id)):
                frameworks = [framework]
                framework_ids = [framework_id]
            else:
                frameworks = []
                framework_ids = []
        else:
            # Get frameworks for this company + global frameworks only
            if global_provider_id:
                frameworks = Framework.query.filter(
                    (Framework.company_id == company_id) |
                    (Framework.company_id == global_provider_id)
                ).all()
            else:
                # Fallback if no global provider exists
                frameworks = Framework.query.filter_by(company_id=company_id).all()
            framework_ids = [f.framework_id for f in frameworks]
        
        if not framework_ids:
            return jsonify([])  # No frameworks, return empty tree
            
        # Get topics for the selected framework(s)
        topics = Topic.query.filter(Topic.framework_id.in_(framework_ids)).all()
        
        # Build unified hierarchical structure across all frameworks
        def build_unified_topic_tree(parent_id=None):
            children = []
            for topic in topics:
                if topic.parent_id == parent_id:
                    # Calculate field count for this topic (include global provider fields)
                    if global_provider_id and global_provider_id != company_id:
                        field_count = FrameworkDataField.query.filter_by(
                            topic_id=topic.topic_id
                        ).filter(
                            or_(
                                FrameworkDataField.company_id == company_id,
                                FrameworkDataField.company_id == global_provider_id
                            )
                        ).count()
                    else:
                        field_count = FrameworkDataField.query.filter_by(
                            topic_id=topic.topic_id,
                            company_id=company_id
                        ).count()
                    
                    # Get all descendants to calculate total field count
                    def get_descendant_field_count(topic_obj):
                        if global_provider_id and global_provider_id != company_id:
                            count = FrameworkDataField.query.filter_by(
                                topic_id=topic_obj.topic_id
                            ).filter(
                                or_(
                                    FrameworkDataField.company_id == company_id,
                                    FrameworkDataField.company_id == global_provider_id
                                )
                            ).count()
                        else:
                            count = FrameworkDataField.query.filter_by(
                                topic_id=topic_obj.topic_id,
                                company_id=company_id
                            ).count()
                        for child in topic_obj.children:
                            count += get_descendant_field_count(child)
                        return count
                    
                    total_field_count = get_descendant_field_count(topic)
                    
                    topic_data = {
                        'topic_id': topic.topic_id,
                        'name': topic.name,
                        'description': topic.description,
                        'level': topic.level,
                        'full_path': topic.get_full_path(),
                        'framework_id': topic.framework_id,
                        'framework_name': next((f.framework_name for f in frameworks if f.framework_id == topic.framework_id), 'Unknown'),
                        'field_count': field_count,
                        'total_field_count': total_field_count,  # Including children
                        'has_children': len([t for t in topics if t.parent_id == topic.topic_id]) > 0,
                        'children': build_unified_topic_tree(topic.topic_id)
                    }
                    children.append(topic_data)
            
            # Sort children by framework name, then by name for consistent display
            children.sort(key=lambda x: (x['framework_name'], x['name']))
            return children

        topic_tree = build_unified_topic_tree()
        return jsonify(topic_tree)
        
    except Exception as e:
        current_app.logger.error(f"Error getting unified topics tree: {str(e)}")
        return jsonify({'error': 'Failed to get topics tree'}), 500

@admin_frameworks_api_bp.route('/all_data_points')
@login_required
@admin_or_super_admin_required
@tenant_required
def get_all_data_points():
    """API endpoint for redesigned assign data points page: returns all data points across ALL frameworks with search support."""
    try:
        company_id = current_user.company_id
        search_term = request.args.get('search', '').strip()
        framework_id = request.args.get('framework_id', '').strip()
        topic_id = request.args.get('topic_id', '').strip()
        field_id = request.args.get('field_id', '').strip()
        
        # Import here to avoid circular imports
        from ..models.framework import Framework, FrameworkDataField
        from ..models.company import Company

        # Base query: all data points for this company + global provider frameworks
        global_provider = Company.get_global_provider()
        global_provider_id = global_provider.id if global_provider else None

        if global_provider_id and global_provider_id != company_id:
            # Include both company-specific and global provider data points
            query = FrameworkDataField.query.filter(
                or_(
                    FrameworkDataField.company_id == company_id,
                    FrameworkDataField.company_id == global_provider_id
                )
            )
        else:
            # Fallback: just current company data points
            query = FrameworkDataField.query.filter_by(company_id=company_id)
        
        # Specific field filter (for dependency lookup)
        if field_id:
            query = query.filter_by(field_id=field_id)
        
        # Framework filter
        elif framework_id:
            query = query.filter_by(framework_id=framework_id)
        
        # Topic filter
        elif topic_id:
            # Include this topic and all its descendants
            topic = Topic.query.filter_by(topic_id=topic_id).first()
            if topic:
                descendant_topics = topic.get_all_descendants()
                topic_ids = [topic.topic_id] + [t.topic_id for t in descendant_topics]
                query = query.filter(FrameworkDataField.topic_id.in_(topic_ids))
        
        # Search filter
        elif search_term:
            query = query.filter(
                or_(
                    FrameworkDataField.field_name.ilike(f'%{search_term}%'),
                    FrameworkDataField.field_code.ilike(f'%{search_term}%'),
                    FrameworkDataField.description.ilike(f'%{search_term}%')
                )
            )
        
        # Execute query with joins
        data_points = query.join(Framework).join(Topic, isouter=True).all()
        
        # Build response data
        result = []
        for field in data_points:
            framework = field.framework
            topic = field.topic

            field_data = {
                'field_id': field.field_id,
                'framework_id': field.framework_id,
                'framework_name': framework.framework_name if framework else 'Unknown',
                'field_name': field.field_name,
                'field_code': field.field_code,
                'description': field.description,
                'unit_category': field.unit_category,
                'default_unit': field.default_unit,
                'value_type': field.value_type,
                'is_computed': field.is_computed,
                'topic_id': field.topic_id,
                'topic_name': topic.name if topic else 'Uncategorized',
                'topic_path': topic.get_full_path() if topic else 'Uncategorized',
                'created_at': field.created_at.isoformat() if field.created_at else None,
                'updated_at': field.updated_at.isoformat() if field.updated_at else None
            }

            # Add current assignment information if available
            from ..models.data_assignment import DataPointAssignment
            current_assignments = DataPointAssignment.query.filter_by(
                field_id=field.field_id,
                company_id=company_id,
                series_status='active'
            ).all()

            if current_assignments:
                # Analyze all assignments to detect mixed configurations
                frequencies = list(set([a.frequency for a in current_assignments if a.frequency]))
                units = list(set([a.unit for a in current_assignments if a.unit]))
                topic_ids = list(set([a.assigned_topic_id for a in current_assignments if a.assigned_topic_id]))

                # For backward compatibility, use first assignment values as primary
                first_assignment = current_assignments[0]

                field_data['current_assignment'] = {
                    'frequency': first_assignment.frequency,
                    'unit': first_assignment.unit,
                    'assigned_topic_id': first_assignment.assigned_topic_id,
                    'entity_count': len(current_assignments),
                    'has_assignments': True,
                    # Add mixed state detection
                    'all_frequencies': frequencies,
                    'all_units': units,
                    'all_topic_ids': topic_ids,
                    'has_mixed_frequencies': len(frequencies) > 1,
                    'has_mixed_units': len(units) > 1,
                    'has_mixed_topics': len(topic_ids) > 1
                }
            else:
                field_data['current_assignment'] = {
                    'frequency': None,
                    'unit': None,
                    'assigned_topic_id': None,
                    'entity_count': 0,
                    'has_assignments': False
                }
            
            # Add dependency information for computed fields
            if field.is_computed:
                dependencies = []
                for mapping in field.variable_mappings:
                    dep_field = mapping.raw_field
                    dependencies.append({
                        'field_id': dep_field.field_id,
                        'field_name': dep_field.field_name,
                        'field_code': dep_field.field_code,
                        'variable_name': mapping.variable_name,
                        'coefficient': mapping.coefficient
                    })
                field_data['dependencies'] = dependencies
                field_data['formula_expression'] = field.formula_expression
                field_data['constant_multiplier'] = field.constant_multiplier
            
            result.append(field_data)
        
        # Sort results by framework name, then topic path, then field name
        result.sort(key=lambda x: (x['framework_name'], x['topic_path'], x['field_name']))
        
        return jsonify({
            'success': True,
            'data_points': result,
            'total_count': len(result),
            'filters_applied': {
                'search_term': search_term,
                'framework_id': framework_id,
                'topic_id': topic_id,
                'field_id': field_id
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting all data points: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get data points'}), 500

@admin_frameworks_api_bp.route('/<framework_id>', methods=['DELETE'])
@login_required
@admin_or_super_admin_required
@tenant_required
def delete_framework(framework_id):
    """Delete a framework and all associated data."""
    try:
        company_id = None if _is_super_admin() else current_user.company_id
        success = frameworks_service.delete_framework(framework_id, company_id)
        if not success:
            return jsonify({'success': False, 'error': 'Framework not found or access denied'}), 404
        return jsonify({'success': True, 'message': 'Framework deleted successfully'})
    except Exception as e:
        current_app.logger.error(f"Error deleting framework {framework_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete framework'}), 500
