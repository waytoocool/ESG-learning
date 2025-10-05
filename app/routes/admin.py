from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from ..models.user import User
from ..models.entity import Entity
from ..models.framework import Framework, FrameworkDataField, FieldVariableMapping
from ..extensions import db
from ..services.email import send_registration_email
from ..services.token import generate_registration_token
from ..services.redis import check_rate_limit
from ..models.esg_data import ESGDataAuditLog, ESGData
from ..models.data_assignment import DataPointAssignment
from ..services.aggregation import aggregation_service
from ..middleware.tenant import get_current_tenant
from ..decorators.auth import admin_or_super_admin_required, tenant_required_for, require_admin
import json
import re
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError  # Local import to avoid cycles
from ..models import (Framework, FrameworkDataField, DataPointAssignment, Entity, 
                      ESGData, User, AuditLog, ESGDataAuditLog, Company, Topic,
                      FieldVariableMapping)
from ..utils.unit_conversions import UnitConverter, get_unit_options_for_field, validate_esg_data_unit
from ..utils.field_import_templates import FieldImportTemplate
from sqlalchemy.sql import func
from .admin_dimensions import register_dimension_routes

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Register dimension management routes
register_dimension_routes(admin_bp)

# Register new framework API routes
from .admin_frameworks_api import admin_frameworks_api_bp
admin_bp.register_blueprint(admin_frameworks_api_bp)

# Register additional assignment data points routes
from .admin_assignDataPoints_Additional import admin_assign_additional_bp
admin_bp.register_blueprint(admin_assign_additional_bp)

# Register modular assign data points routes (Phase 0 + 1)
from .admin_assign_data_points import admin_assign_data_points_bp
admin_bp.register_blueprint(admin_assign_data_points_bp)

# Note: Bulk operations functionality has been integrated into the main assignment interface

# Import models after blueprint creation to avoid circular imports
from ..models import (Framework, FrameworkDataField, DataPointAssignment, Entity, 
                      ESGData, User, AuditLog, ESGDataAuditLog, Company, Topic,
                      FieldVariableMapping, Dimension, DimensionValue, FieldDimension)

def is_super_admin():
    """Check if current user is a super admin (no company_id)"""
    return current_user.role == 'SUPER_ADMIN'

def require_tenant_for_admin():
    """Decorator to ensure admin users access via their company subdomain"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # First check: Only ADMIN or SUPER_ADMIN roles can access admin pages
            if current_user.role not in ['ADMIN', 'SUPER_ADMIN']:
                current_app.logger.warning(
                    f"Access denied: User {current_user.id} (role: {current_user.role}) "
                    f"attempted to access admin endpoint {f.__name__}"
                )
                flash('Access denied. Admin privileges required.', 'error')
                return redirect(url_for('auth.login'))

            # SUPER_ADMIN must use impersonation to access admin pages
            if is_super_admin():
                # Check if SUPER_ADMIN has tenant context (via impersonation)
                tenant = get_current_tenant()
                if not tenant:
                    # SUPER_ADMIN accessing without company context - redirect to users page for impersonation
                    flash('Please select a company to manage by using the impersonation feature.', 'info')
                    return redirect(url_for('superadmin.list_users'))

                # SUPER_ADMIN has tenant context - check if they're actually impersonating
                from flask import session
                if not session.get('impersonating') or not session.get('impersonated_user_id'):
                    # SUPER_ADMIN on tenant subdomain without impersonation - redirect to main domain users page
                    flash('Please use impersonation to access admin features for this company.', 'info')
                    return redirect('http://127-0-0-1.nip.io:8000/superadmin/users')

                # SUPER_ADMIN with tenant context and active impersonation - allow access
                return f(*args, **kwargs)
            
            # Admin users must have tenant context
            tenant = get_current_tenant()
            if not tenant:
                # Admin accessing from localhost - redirect to their company subdomain
                if current_user.company_id:
                    company = Company.query.get(current_user.company_id)
                    if company:
                        # Build redirect URL to company subdomain
                        from urllib.parse import urlunparse
                        import re
                        
                        host_parts = request.host.split(':')
                        hostname = host_parts[0]
                        port = host_parts[1] if len(host_parts) > 1 else None
                        
                        # Build tenant URL
                        if hostname in ("localhost", "127.0.0.1") or hostname.count('.') == 0:
                            tenant_host = f"{company.slug}.127-0-0-1.nip.io"
                        elif re.match(r"^\d+-\d+-\d+-\d+\.nip\.io$", hostname):
                            tenant_host = f"{company.slug}.{hostname}"
                        else:
                            parts = hostname.split('.', 1)
                            tenant_host = f"{company.slug}.{parts[1]}" if len(parts) > 1 else hostname
                        
                        if port:
                            tenant_host += f":{port}"
                        
                        scheme = request.scheme
                        redirect_url = urlunparse((scheme, tenant_host, request.path, '', '', ''))
                        
                        flash('Please access admin features via your company subdomain.', 'info')
                        return redirect(redirect_url)
                
                # No company or tenant - deny access
                flash('Access denied. Admin users must access via company subdomain.', 'error')
                return redirect(url_for('auth.login'))
            
            # Verify tenant matches admin's company
            if current_user.company_id != tenant.id:
                flash('Access denied. You can only access your own company data.', 'error')
                return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_admin_entities():
    """Get entities based on admin's access level"""
    if is_super_admin():
        # Super admin can see all entities
        return Entity.query.all()
    else:
        # Regular admin can only see their tenant's entities
        tenant = get_current_tenant()
        if tenant:
            return Entity.query_for_tenant(db.session).all()
        else:
            # No fallback - admin users must access via their company subdomain
            return []

def get_admin_data_points():
    """Get data points (assignments) based on admin's access level"""
    if is_super_admin():
        # Super admin can see all ACTIVE assignments
        return DataPointAssignment.query.filter_by(series_status='active').all()
    else:
        # Regular admin can only see their tenant's ACTIVE assignments
        tenant = get_current_tenant()
        if tenant:
            return DataPointAssignment.query_for_tenant(db.session).filter_by(series_status='active').all()
        else:
            # No fallback - admin users must access via their company subdomain
            return []

def get_admin_esg_data():
    """Get ESG data based on admin's access level"""
    if is_super_admin():
        # Super admin can see all ESG data
        return ESGData.query.all()
    else:
        # Regular admin can only see their tenant's ESG data
        tenant = get_current_tenant()
        if tenant:
            return ESGData.query_for_tenant(db.session).all()
        else:
            # No fallback - admin users must access via their company subdomain
            return []

def get_admin_assignments():
    """Get data point assignments based on admin's access level"""
    if is_super_admin():
        # Super admin can see all ACTIVE assignments
        return DataPointAssignment.query.filter_by(series_status='active').all()
    else:
        # Regular admin can only see their tenant's ACTIVE assignments
        tenant = get_current_tenant()
        if tenant:
            return DataPointAssignment.query_for_tenant(db.session).filter_by(series_status='active').all()
        else:
            return []

@admin_bp.route('/home')
@login_required
@admin_or_super_admin_required
def home():
    return render_template('admin/home.html')

@admin_bp.route('/company-settings', methods=['GET', 'POST'])
@login_required
@require_tenant_for_admin()
def company_settings():
    """
    Company fiscal year configuration interface.
    
    GET: Display the fiscal year configuration form
    POST: Handle fiscal year configuration updates with validation
    """
    company = current_user.company
    
    if request.method == 'POST':
        try:
            # Get form data
            fy_end_month = int(request.form.get('fy_end_month', 3))
            fy_end_day = int(request.form.get('fy_end_day', 31))
            
            # Update company settings
            company.fy_end_month = fy_end_month
            company.fy_end_day = fy_end_day
            
            # Validate the configuration
            is_valid, error_message = company.validate_fy_configuration()
            if not is_valid:
                flash(f'Invalid fiscal year configuration: {error_message}', 'error')
                return render_template('admin/company_settings.html', company=company)
            
            # Save changes
            db.session.commit()
            
            # Success message with example
            from datetime import datetime
            current_year = datetime.now().year
            example_fy = company.get_fy_display(current_year + 1)  # Next FY as example
            flash(f'Fiscal year configuration updated successfully! Example: {example_fy}', 'success')
            
            return redirect(url_for('admin.company_settings'))
            
        except (ValueError, TypeError) as e:
            flash(f'Invalid input: Please provide valid numbers for month and day.', 'error')
            return render_template('admin/company_settings.html', company=company)
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while updating settings: {str(e)}', 'error')
            return render_template('admin/company_settings.html', company=company)
    
    # GET request - display the form
    return render_template('admin/company_settings.html', company=company)

@admin_bp.route('/data_hierarchy', methods=['GET', 'POST'])
@login_required
@require_tenant_for_admin()
def data_hierarchy():
    def build_hierarchy(entity, visited, all_entities):
        if entity.id in visited:
            return None
        visited.add(entity.id)
        users = [{
            "name": user.name,
            "username": user.name,
            "email": user.email,
            "is_email_verified": user.is_email_verified,
            # Optionally expose verification date if you track it
        } for user in entity.users]
        children = [
            build_hierarchy(child, visited, all_entities)
            for child in all_entities if child.parent_id == entity.id
        ]
        children = [child for child in children if child is not None]
        return {
            'name': entity.name or "Unnamed Entity",
            'details': entity.entity_type or "Unknown Type",
            'users': users,
            'children': children
        }

    if request.method == 'POST':
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Invalid request method'}), 400
        
        try:
            name = request.form.get('name')
            entity_type = request.form.get('entity_type')
            parent_id = request.form.get('parent_id')

            # Validate required fields
            if not name:
                return jsonify({'success': False, 'message': 'Entity name is required.'}), 400
            if not entity_type:
                return jsonify({'success': False, 'message': 'Entity type is required.'}), 400
            if not parent_id:
                # Business rule: Only one root entity per company is allowed
                # This prevents multiple top-level entities and maintains hierarchy
                return jsonify({'success': False, 'message': 'Parent entity is required. Only one root entity per company is allowed.'}), 400

            # Validate parent entity exists and is accessible
            if is_super_admin():
                parent = Entity.query.get(parent_id)
            else:
                parent = Entity.get_for_tenant(db.session, parent_id)
            
            if not parent:
                return jsonify({'success': False, 'message': 'Invalid parent entity.'}), 400

            # Check hierarchy level
            max_hierarchy_level = 3
            if parent.get_hierarchy_level() >= max_hierarchy_level:
                return jsonify({
                    'success': False,
                    'message': f'Maximum hierarchy level of {max_hierarchy_level} reached.'
                }), 400

            # Check for duplicate names within tenant scope
            if is_super_admin():
                # For super-admin we scope the uniqueness check to the same company as the provided parent entity.
                parent_entity = Entity.query.get(parent_id)
                parent_company_id = parent_entity.company_id if parent_entity else None
                existing_entity = Entity.query.filter_by(name=name, company_id=parent_company_id).first()
            else:
                existing_entity = Entity.exists_for_tenant(db.session, name=name)
            
            if existing_entity:
                return jsonify({'success': False, 'message': 'An entity with this name already exists.'}), 400
            
            # Create new entity
            if is_super_admin():
                # Super admin creates entity without tenant restriction
                new_entity = Entity(
                    name=name,
                    entity_type=entity_type,
                    parent_id=parent_id,
                    company_id=parent.company_id  # Inherit parent's company_id
                )
            else:
                # Regular admin creates entity for their tenant
                new_entity = Entity.create_for_current_tenant(
                    db.session,
                    name=name,
                    entity_type=entity_type,
                    parent_id=parent_id
                )
            
            db.session.add(new_entity)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Entity created successfully!'
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating entity: {str(e)}')
            return jsonify({
                'success': False,
                'message': 'An error occurred while creating the entity'
            }), 500
   
    entities = get_admin_entities()
    hierarchy_data = [
        build_hierarchy(entity, set(), entities) 
        for entity in entities if entity.parent_id is None
    ]
    hierarchy_data = [item for item in hierarchy_data if item is not None]

    return render_template('admin/data_hierarchy.html', 
                         entities=entities, 
                         hierarchy_data=hierarchy_data)

@admin_bp.route('/frameworks/wizard')
@login_required
@admin_or_super_admin_required
def framework_wizard():
    """Framework creation wizard page"""
    edit_framework_id = request.args.get('edit')
    framework_data = None
    
    if edit_framework_id:
        # Load existing framework data for editing
        from ..services import frameworks_service
        framework_data = frameworks_service.get_framework_for_editing(edit_framework_id, current_user.company_id)
        
        if not framework_data:
            flash('Framework not found or access denied', 'error')
            return redirect(url_for('admin.frameworks'))
    
    return render_template('admin/framework_wizard.html', 
                         edit_mode=bool(edit_framework_id),
                         framework_data=framework_data)

@admin_bp.route('/frameworks', methods=['GET', 'POST'])
@login_required
@require_tenant_for_admin()
def frameworks():
    if request.method == 'POST':
        try:
            # Extract framework details
            framework_name = request.form.get('framework_name')
            framework_description = request.form.get('framework_description', '')

            # Validate framework name
            if not framework_name:
                flash('Framework name is required', 'error')
                return redirect(url_for('admin.frameworks'))

            # Create new framework with company_id
            new_framework = Framework(
                framework_name=framework_name, 
                description=framework_description,
                company_id=current_user.company_id
            )
            db.session.add(new_framework)
            db.session.flush()  # To get the framework_id

            # Get dependencies data
            try:
                dependencies = json.loads(request.form.get('dependencies', '{}'))
            except json.JSONDecodeError:
                flash('Invalid dependencies format', 'error')
                return redirect(url_for('admin.frameworks'))

            # Create default "Uncategorised" topic for this framework
            default_topic = Topic(
                name="Uncategorised",
                description="Default topic for uncategorised fields",
                framework_id=new_framework.framework_id,
                company_id=current_user.company_id
            )
            db.session.add(default_topic)
            db.session.flush()  # To get the topic_id

            # Process data fields
            data_point_names = request.form.getlist('data_point_name[]')
            data_point_descriptions = request.form.getlist('data_point_description[]')
            data_point_is_computed = request.form.getlist('data_point_is_computed[]')
            
            # Phase 1 new fields
            field_codes = request.form.getlist('field_code[]')
            unit_categories = request.form.getlist('unit_category[]')
            default_units = request.form.getlist('default_unit[]')
            value_types = request.form.getlist('value_type[]')
            
            # Phase 2 new fields
            topic_ids = request.form.getlist('topic_id[]')
            
            formula_expressions = request.form.getlist('formula_expression[]')

            for i, name in enumerate(data_point_names):
                if not name:  # Skip empty fields
                    continue

                is_computed = i < len(data_point_is_computed) and data_point_is_computed[i] == 'true'
                
                # Get Phase 1 field data
                field_code = field_codes[i] if i < len(field_codes) and field_codes[i] else None
                unit_category = unit_categories[i] if i < len(unit_categories) and unit_categories[i] else None
                default_unit = default_units[i] if i < len(default_units) and default_units[i] else None
                value_type = value_types[i] if i < len(value_types) and value_types[i] else 'NUMBER'
                
                # Get Phase 2 field data - assign to default topic if none specified
                topic_id = topic_ids[i] if i < len(topic_ids) and topic_ids[i] else default_topic.topic_id

                # Create data field
                new_field = FrameworkDataField(
                    framework_id=new_framework.framework_id,
                    company_id=current_user.company_id,
                    field_name=name,
                    field_code=field_code,  # Will auto-generate if not provided
                    description=data_point_descriptions[i] if i < len(data_point_descriptions) else None,
                    unit_category=unit_category,
                    default_unit=default_unit,
                    value_type=value_type,
                    topic_id=topic_id,
                    is_computed=is_computed,
                )

                # Handle computed fields
                if is_computed and name in dependencies:
                    dep_data = dependencies[name]
                    
                    # Store the basic formula expression (e.g., "A + B")
                    new_field.formula_expression = dep_data.get('formula', '')
                    
                    # Validate formula format
                    if not re.match(r'^[A-Z\+\-\*\/\(\)\s]*$', new_field.formula_expression):
                        raise ValueError(f"Invalid formula format for field {name}")

                    db.session.add(new_field)
                    db.session.flush()  # To get the field_id
                    
                    # Create variable mappings with coefficients
                    for mapping in dep_data.get('fieldMappings', []):
                        # Validate required fields
                        if not all(key in mapping for key in ['variable', 'field_id', 'coefficient']):
                            raise ValueError(f"Missing required mapping data for field {name}")
                        
                        # Create the mapping with coefficient
                        new_mapping = FieldVariableMapping(
                            computed_field_id=new_field.field_id,
                            raw_field_id=mapping['field_id'],
                            variable_name=mapping['variable'],
                            coefficient=float(mapping.get('coefficient', 1.0))
                        )
                        db.session.add(new_mapping)
                else:
                    # For non-computed fields, just add the field
                    db.session.add(new_field)

            db.session.commit()
            flash('Framework created successfully', 'success')

        except ValueError as ve:
            db.session.rollback()
            current_app.logger.error(f'Validation error creating framework: {str(ve)}')
            flash(str(ve), 'error')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating framework: {str(e)}')
            flash(f'Error creating framework: {str(e)}', 'error')

        return redirect(url_for('admin.frameworks'))

    # GET request: fetch frameworks for current user's company
    from ..services import frameworks_service
    
    company_id = current_user.company_id
    include_global = True  # Include global frameworks for regular admins
    
    # Use the frameworks service to get enhanced framework data
    frameworks_data = frameworks_service.list_frameworks(
        company_id=company_id,
        include_global=include_global,
        sort='name_asc'
    )
    
    return render_template('admin/frameworks.html', frameworks=frameworks_data)



@admin_bp.route('/get_frameworks')
@login_required
@admin_or_super_admin_required
def get_frameworks():
    """Get frameworks for dropdown selection (tenant-scoped + global)."""
    try:
        from ..services import frameworks_service  # Local import to avoid circular deps

        if is_super_admin():
            # Super admins can view all frameworks across tenants
            frameworks = Framework.query.all()
        else:
            # Include both company-specific and global frameworks for the current tenant
            frameworks_by_type = frameworks_service.separate_frameworks_by_type(current_user.company_id)
            frameworks = frameworks_by_type['company'] + frameworks_by_type['global']

        return jsonify([{  # unchanged response shape
            'framework_id': fw.framework_id,
            'framework_name': fw.framework_name
        } for fw in frameworks])
    except Exception as e:
        current_app.logger.error(f'Error fetching frameworks: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/get_framework_fields/<framework_id>')
@login_required
@admin_or_super_admin_required
def get_framework_fields(framework_id):
    """Get all fields for a specific framework with complete metadata (tenant-scoped)."""
    try:
        from ..services import frameworks_service  # Local import to avoid circular deps

        # Filter by company_id for tenant isolation, except for global frameworks
        if is_super_admin():
            fields = FrameworkDataField.query.filter_by(framework_id=framework_id).all()
        else:
            # Check if this is a global framework
            if frameworks_service.is_global_framework(framework_id, current_user.company_id):
                # For global frameworks, don't filter by company_id - all companies can access
                fields = FrameworkDataField.query.filter_by(framework_id=framework_id).all()
            else:
                # For company-specific frameworks, filter by company_id
                fields = FrameworkDataField.query.filter_by(
                    framework_id=framework_id,
                    company_id=current_user.company_id
                ).all()
        
        return jsonify([{
            'field_id': field.field_id,
            'field_name': field.field_name,
            'field_code': field.field_code,
            'unit_category': field.unit_category,
            'default_unit': field.default_unit,
            'value_type': field.value_type,
            'is_computed': field.is_computed,
            'description': field.description,
            'topic_id': field.topic_id,
            'topic_name': field.topic.name if field.topic else None,
            'topic_full_path': field.topic.get_full_path() if field.topic else None
        } for field in fields])
    except Exception as e:
        current_app.logger.error(f'Error fetching framework fields: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/frameworks/<framework_id>', methods=['PUT'])
@login_required
@require_tenant_for_admin()
def update_framework(framework_id):
    """Update an existing framework - only company-owned frameworks can be edited"""
    try:
        from ..services import frameworks_service
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Framework name is required'}), 400
        
        # Update framework using service layer
        framework = frameworks_service.update_framework(
            framework_id=framework_id,
            company_id=current_user.company_id,
            name=data['name'],
            description=data.get('description', ''),
            data_points=data.get('data_points', []),
            topics=data.get('topics', [])
        )
        
        if not framework:
            return jsonify({'success': False, 'error': 'Framework not found or access denied'}), 404
        
        return jsonify({
            'success': True,
            'framework_id': framework.framework_id,
            'message': 'Framework updated successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating framework: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/validate_formula', methods=['POST'])
@login_required
@admin_or_super_admin_required
def validate_formula():
    """Validate a formula and its dependencies for circular references."""
    try:
        data = request.get_json()
        formula = data.get('formula')
        dependencies = data.get('dependencies', [])
        
        # Strip any whitespace
        formula = formula.replace(' ', '')
        
        # Basic formula validation - only allow variables and basic operators
        # Note: We don't check for numbers here as coefficients are stored separately
        if not re.match(r'^[A-Z\+\-\*\/\(\)]*$', formula):
            return jsonify({
                'valid': False,
                'message': 'Formula can only contain variables (A-Z), operators (+,-,*,/), and parentheses. Coefficients should be specified in the field mappings.'
            })
        
        # Check for balanced parentheses
        if formula.count('(') != formula.count(')'):
            return jsonify({
                'valid': False,
                'message': 'Formula has unbalanced parentheses'
            })
        
        # Check that all variables in formula have mappings
        variables_in_formula = set(re.findall(r'[A-Z]', formula))
        mapped_variables = {dep['variable'] for dep in dependencies}
        unmapped = variables_in_formula - mapped_variables
        
        if unmapped:
            return jsonify({
                'valid': False,
                'message': f'Variables not mapped: {", ".join(sorted(unmapped))}'
            })
        
        return jsonify({'valid': True})
        
    except Exception as e:
        current_app.logger.error(f'Error validating formula: {str(e)}')
        return jsonify({
            'valid': False,
            'message': f'Error validating formula: {str(e)}'
        }), 500


# BACKUP ROUTE - Commented out for production deployment
# Uncomment if critical issues found with new modular page
# @admin_bp.route('/assign_data_points_redesigned_backup', methods=['GET'])
# @login_required
# @require_tenant_for_admin()
# def assign_data_points_redesigned_backup():
#     """BACKUP: Original legacy page preserved for emergency rollback"""
#     from ..services import frameworks_service  # Local import to avoid circular deps
#
#     if is_super_admin():
#         frameworks = Framework.query.all()
#     else:
#         frameworks_by_type = frameworks_service.separate_frameworks_by_type(current_user.company_id)
#         frameworks = frameworks_by_type['company'] + frameworks_by_type['global']
#
#     entities = get_admin_entities()
#     data_points = get_admin_data_points()
#
#     return render_template('admin/assign_data_points_redesigned.html',
#                          frameworks=frameworks,
#                          entities=entities,
#                          data_points=data_points)

# Note: Bulk operations functionality integrated into main assignment interface

def _is_frequency_combination_valid(dependency_field, computed_field, computed_frequency):
    """
    Check if a frequency combination is valid for computed fields.
    
    Valid combinations:
    - Monthly dependency can support Quarterly or Annual computed fields
    - Quarterly dependency can support Annual computed fields  
    - Same frequencies are always valid
    
    Invalid combinations:
    - Annual dependency cannot support Monthly or Quarterly computed fields
    - Quarterly dependency cannot support Monthly computed fields
    """
    # Get the dependency frequency from existing assignments or use a default
    dependency_frequency = _get_dependency_frequency(dependency_field)
    
    # Define frequency hierarchy (higher number = higher frequency)
    frequency_hierarchy = {
        'Annual': 1,
        'Quarterly': 2, 
        'Monthly': 3
    }
    
    dep_level = frequency_hierarchy.get(dependency_frequency, 1)
    comp_level = frequency_hierarchy.get(computed_frequency, 1)
    
    # Computed field frequency must be equal or lower than dependency frequency
    return comp_level <= dep_level

def _get_dependency_frequency(dependency_field):
    """Get the most common frequency for a dependency field from existing assignments."""
    # Look for existing assignments for this field to determine its frequency
    assignments = DataPointAssignment.query.filter_by(
        field_id=dependency_field.field_id,
        is_active=True
    ).all()
    
    if assignments:
        # Use the most common frequency
        frequencies = [a.frequency for a in assignments if a.frequency]
        if frequencies:
            return max(set(frequencies), key=frequencies.count)
    
    # Default frequency based on field type (this is a fallback)
    return 'Annual'  # Default to most restrictive

@admin_bp.route('/get_entities')
@login_required
@admin_or_super_admin_required
def get_entities():
    entities = get_admin_entities()
    return jsonify([{'id': e.id, 'name': e.name, 'entity_type': e.entity_type, 'parent_id': e.parent_id} for e in entities])

@admin_bp.route('/create_user', methods=['POST'])
@login_required
@admin_or_super_admin_required
def create_user():
    """Endpoint used from the Data-Hierarchy ➜ "Add User" side-drawer.

    Expects a regular HTML form submission executed via Fetch/AJAX on the
    front-end (see app/static/js/admin/forms.js).  Instead of redirecting or
    rendering a template we always return a JSON payload so the calling
    JavaScript can decide whether to show a success or an error popup.
    """

    name = request.form.get('username')  # Note: form field is still 'username' for now  
    email = request.form.get('email', '').lower().strip() if request.form.get('email') else ''
    entity_id = request.form.get('entity_id')

    try:
        # Fetch entity to derive tenant (company) information.
        entity = Entity.query.get(entity_id)
        if not entity:
            return jsonify({
                'success': False,
                'message': 'Selected entity does not exist.'
            })

        new_user = User(
            name=name,
            email=email,
            entity_id=entity_id,
            company_id=entity.company_id,  # ⬅️ tie the user to the tenant
            role="USER",  # keep enum value consistent with model definition
            is_email_verified=False
        )

        db.session.add(new_user)
        db.session.commit()

        # Send registration email with token so that the new user can set a
        # password and verify their email address.
        token = generate_registration_token(new_user.id)
        email_ok, email_msg = send_registration_email(email, token)

        if not email_ok:
            # Email failed but user has been created — inform admin.
            return jsonify({
                'success': False,
                'message': f'User created, but email could not be sent: {email_msg}. '
                           'Please contact support or resend later.'
            })

        # Build user data for sidebar
        user_data = {
            "id": new_user.id,
            "name": new_user.name,
            "username": new_user.name,  # Keep for backward compatibility in JS
            "email": new_user.email,
            "role": new_user.role,
            "is_email_verified": new_user.is_email_verified,
            "verification_date": new_user.verification_date if hasattr(new_user, 'verification_date') else None
        }

        return jsonify({
            'success': True,
            'message': 'User created successfully. A verification email has been sent.',
            'user_data': user_data
        })

    except IntegrityError as ie:
        # Roll back the session so the error does not pollute future
        # transactions.
        db.session.rollback()

        # Check if the failure is due to duplicate e-mail – SQLite and most
        # other SQL dialects include the column name in the error string.
        if 'user.email' in str(ie.orig) or 'UNIQUE constraint failed' in str(ie.orig):
            return jsonify({
                'success': False,
                'message': 'A user with this e-mail address already exists.'
            })

        # Fallback for other integrity errors (e.g. FK constraints).
        current_app.logger.error(f'IntegrityError while creating user: {ie}')
        return jsonify({
            'success': False,
            'message': 'Unable to create user due to a database integrity error.'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Unexpected error while creating user: {e}')
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred while creating the user.'
        })

@admin_bp.route('/resend_verification', methods=['POST'])
@login_required
@admin_or_super_admin_required
def resend_verification():
    """
    Admin route to resend verification email for a user.

    Request Body:
        email (str): Email address of the user to resend verification.

    Returns:
        JSON response with success or failure status.
    """
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip() if data.get('email') else ''

        if not email:
            return jsonify({'success': False, 'message': 'Email is required'})

        # Check if user exists and needs verification
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'})

        if user.is_email_verified:
            return jsonify({'success': False, 'message': 'User is already verified'})

        # Use the rate limit helper function
        can_send, limit_message = check_rate_limit(email)
        if not can_send:
            return jsonify({'success': False, 'message': limit_message})

        # Generate and send new token
        token = generate_registration_token(user.id)
        send_registration_email(email, token)

        return jsonify({
            'success': True,
            'message': 'Verification email has been sent successfully.'
        })

    except Exception as e:
        current_app.logger.error(f'Error in resend_verification: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your request.'
        })

@admin_bp.route('/get_existing_data_points')
@login_required
@admin_or_super_admin_required
def get_existing_data_points():
    """Get data points (assignments) with their framework field information"""
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

    if include_inactive:
        # Get both active and inactive assignments
        if is_super_admin():
            assignments = DataPointAssignment.query.all()
        else:
            tenant = get_current_tenant()
            if tenant:
                assignments = DataPointAssignment.query_for_tenant(db.session).all()
            else:
                assignments = []
    else:
        # Get only active assignments (current behavior)
        assignments = get_admin_data_points()
    
    result = []
    for assignment in assignments:
        # Get the framework field information
        framework_field = FrameworkDataField.query.get(assignment.field_id)
        if framework_field:
            # Fetch assigned material topic name if available
            assigned_topic_name = None
            if assignment.assigned_topic_id:
                from ..models.framework import Topic
                assigned_topic = Topic.query.get(assignment.assigned_topic_id)
                if assigned_topic:
                    assigned_topic_name = assigned_topic.name

            result.append({
                'id': assignment.id,
                'field_id': assignment.field_id,
                'field_name': framework_field.field_name,
                'name': framework_field.field_name,  # Keep for backward compatibility
                'description': framework_field.description,
                'is_computed': framework_field.is_computed,
                # Include Phase 1 metadata from FrameworkDataField
                'field_code': framework_field.field_code,
                'unit_category': framework_field.unit_category,
                'default_unit': framework_field.default_unit,
                'value_type': framework_field.value_type,  # Use field's value_type instead of assignment's
                'unit': assignment.effective_unit,
                'framework_id': framework_field.framework_id,
                'entity_id': assignment.entity_id,
                'entity_name': assignment.entity.name if assignment.entity else None,
                'frequency': assignment.frequency,
                'is_active': assignment.series_status == 'active',  # Compatibility
                'series_status': assignment.series_status,
                'framework_name': framework_field.framework.framework_name if framework_field.framework else None,
                # Include topic information for frontend assignment logic
                'topic_name': framework_field.topic.name if framework_field.topic else None,
                'topic_id': framework_field.topic_id,
                # Include assigned_topic_id from assignment for material topic configuration tracking
                'assigned_topic_id': assignment.assigned_topic_id,
                'assigned_topic_name': assigned_topic_name  # Company material topic name
            })
    
    return jsonify(result)

@admin_bp.route('/save_assignments', methods=['POST'])
@login_required
@admin_or_super_admin_required
def save_assignments():
    """Save/update data point assignments with value_type and unit"""
    from ..services.assignment_versioning import AssignmentVersioningService
    from ..models.esg_data import ESGData

    try:
        assignments_data = request.get_json()

        if not assignments_data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # Process assignment updates
        updated_count = 0
        versioned_count = 0
        reactivated_count = 0

        for assignment_data in assignments_data:
            assignment_id = assignment_data.get('assignment_id')
            value_type = assignment_data.get('value_type', 'text')
            unit = assignment_data.get('unit')
            frequency = assignment_data.get('frequency')
            assigned_topic_id = assignment_data.get('assigned_topic_id')

            # Get assignment with proper access control
            if is_super_admin():
                assignment = DataPointAssignment.query.get(assignment_id)
            else:
                assignment = DataPointAssignment.query_for_tenant(db.session).get(assignment_id)

            if not assignment:
                continue

            # Check if assignment has collected ESG data
            has_data = ESGData.query.filter_by(assignment_id=assignment_id).count() > 0

            # Build changes dictionary
            changes = {}
            if assignment.value_type != value_type:
                changes['value_type'] = value_type
            if frequency and assignment.frequency != frequency:
                changes['frequency'] = frequency
            if assigned_topic_id != assignment.assigned_topic_id:
                changes['assigned_topic_id'] = assigned_topic_id

            # Handle inactive assignment reactivation
            was_inactive = assignment.series_status != 'active'
            if was_inactive and changes:
                # Reactivating inactive assignment with configuration changes
                assignment.series_status = 'active'
                assignment.series_status = 'active'
                reactivated_count += 1

            # Determine if versioning is needed
            if has_data and changes and assignment.series_status == 'active':
                # Data exists and configuration is changing - create new version
                try:
                    reason = f"Configuration update via save_assignments: {', '.join(changes.keys())}"
                    version_result = AssignmentVersioningService.create_assignment_version(
                        assignment_id,
                        changes,
                        reason,
                        current_user.id
                    )

                    if version_result.get('success'):
                        versioned_count += 1
                    else:
                        current_app.logger.warning(f"Versioning failed for assignment {assignment_id}: {version_result}")
                        # Fall back to direct update if versioning fails
                        assignment.value_type = value_type
                        if frequency:
                            assignment.frequency = frequency
                        if assigned_topic_id is not None:
                            assignment.assigned_topic_id = assigned_topic_id
                        updated_count += 1

                except Exception as version_error:
                    current_app.logger.error(f"Versioning error for assignment {assignment_id}: {version_error}")
                    # Fall back to direct update if versioning fails
                    assignment.value_type = value_type
                    if frequency:
                        assignment.frequency = frequency
                    if assigned_topic_id is not None:
                        assignment.assigned_topic_id = assigned_topic_id
                    updated_count += 1

            elif changes:
                # No data exists or not active - direct update
                assignment.value_type = value_type
                if frequency:
                    assignment.frequency = frequency

                # Handle material topic assignment
                if assigned_topic_id is not None:  # Allow None to unassign topics
                    # Validate topic belongs to same company if provided
                    if assigned_topic_id:
                        topic = Topic.query.filter_by(
                            topic_id=assigned_topic_id,
                            company_id=current_user.company_id
                        ).first()
                        if not topic:
                            return jsonify({'success': False, 'error': f'Invalid topic ID: {assigned_topic_id}'}), 400
                    assignment.assigned_topic_id = assigned_topic_id

                updated_count += 1

        db.session.commit()

        # Build response message
        message_parts = []
        if updated_count > 0:
            message_parts.append(f"Updated {updated_count} assignment(s)")
        if versioned_count > 0:
            message_parts.append(f"Created {versioned_count} new version(s)")
        if reactivated_count > 0:
            message_parts.append(f"Reactivated {reactivated_count} assignment(s)")

        return jsonify({
            'success': True,
            'message': '; '.join(message_parts) if message_parts else 'No changes detected',
            'summary': {
                'updated': updated_count,
                'versioned': versioned_count,
                'reactivated': reactivated_count
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in save_assignments: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/get_data_point_assignments')
@login_required
@admin_or_super_admin_required
def get_data_point_assignments():
    assignments = get_admin_assignments()
    return jsonify([{
        'id': a.id,
        'field_id': a.field_id,
        'entity_id': a.entity_id,
        'value_type': a.field.value_type if a.field else None,
        'unit': a.unit,
        'frequency': a.frequency,
        'is_active': a.series_status == 'active',  # Compatibility
        'data_series_id': a.data_series_id,
        'series_version': a.series_version,
        'series_status': a.series_status,
        'assigned_topic_id': a.assigned_topic_id
    } for a in assignments])


@admin_bp.route('/get_valid_dates/<field_id>/<int:entity_id>')
@login_required
@admin_or_super_admin_required
def get_valid_dates(field_id, entity_id):
    # Find assignment (with proper access control)
    if is_super_admin():
        assignment = DataPointAssignment.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            is_active=True
        ).first()
    else:
        assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
            field_id=field_id,
            entity_id=entity_id,
            is_active=True
        ).first()
    
    if not assignment:
        return jsonify({'error': 'Assignment not found'}), 404
    
    valid_dates = assignment.get_valid_reporting_dates()
    return jsonify({
        'valid_dates': [date.isoformat() for date in valid_dates],
        'frequency': assignment.frequency,
        'fy_display': assignment.get_fy_display()
    })

@admin_bp.route('/data_review', methods=['GET', 'POST'])
@login_required
@admin_or_super_admin_required
def data_review():
    if request.method == 'POST':
        try:
            data_id = request.form.get('data_id')
            action = request.form.get('action')
            admin_notes = request.form.get('admin_notes', '')
            
            # Get ESG data with proper access control
            if is_super_admin():
                esg_data = ESGData.query.get(data_id)
            else:
                esg_data = ESGData.get_for_tenant(db.session, data_id)
            
            if not esg_data:
                flash('Data not found or access denied', 'error')
                return redirect(url_for('admin.data_review'))
            
            # Handle different actions
            if action == 'approve':
                esg_data.status = 'approved'
                flash('Data approved successfully', 'success')
            elif action == 'reject':
                esg_data.status = 'rejected'
                flash('Data rejected', 'info')
            elif action == 'request_revision':
                esg_data.status = 'revision_requested'
                flash('Revision requested', 'info')
            
            # Add admin notes if provided
            if admin_notes:
                esg_data.admin_notes = admin_notes
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error in data review: {str(e)}')
            flash('An error occurred while processing the request', 'error')
        
        return redirect(url_for('admin.data_review'))
    
    # Get all ESG data entries for review
    esg_entries = get_admin_esg_data()
    
    # Get associated entities for filtering
    entities = get_admin_entities()
    
    return render_template('admin/data_review.html', 
                         esg_entries=esg_entries,
                         entities=entities)

@admin_bp.route('/audit_log')
@login_required
@admin_or_super_admin_required
def audit_log():
    # Get all audit logs with related data
    audit_logs = ESGDataAuditLog.query\
        .join(ESGDataAuditLog.user)\
        .join(ESGDataAuditLog.esg_data)\
        .order_by(ESGDataAuditLog.change_date.desc())\
        .all()
    
    return render_template('admin/audit_log.html', audit_logs=audit_logs)

@admin_bp.route('/data_status_matrix', methods=['GET'])
@login_required
@admin_or_super_admin_required
def data_status_matrix():
    # Get entities and assignments (which are now our data points)
    entities = get_admin_entities()
    assignments = get_admin_assignments()
    
    # Build matrix data
    matrix_data = []
    for entity in entities:
        entity_assignments = [a for a in assignments if a.entity_id == entity.id and a.series_status == 'active']
        
        for assignment in entity_assignments:
            # Get framework field information
            framework_field = FrameworkDataField.query.get(assignment.field_id)
            if not framework_field:
                continue
            
            # Get ESG data for this assignment
            if is_super_admin():
                esg_data = ESGData.query.filter_by(
                    field_id=assignment.field_id,
                    entity_id=entity.id
                ).order_by(ESGData.reporting_date.desc()).all()
            else:
                esg_data = ESGData.query_for_tenant(db.session).filter_by(
                    field_id=assignment.field_id,
                    entity_id=entity.id
                ).order_by(ESGData.reporting_date.desc()).all()
            
            # Calculate status
            status = 'no_data'
            latest_value = None
            latest_date = None
            
            if esg_data:
                latest_entry = esg_data[0]
                latest_date = latest_entry.reporting_date
                
                if framework_field.is_computed:
                    latest_value = latest_entry.calculated_value
                    status = 'computed' if latest_value is not None else 'pending_computation'
                else:
                    latest_value = latest_entry.raw_value
                    status = 'complete' if latest_value is not None else 'incomplete'
            
            matrix_data.append({
                'entity_id': entity.id,
                'entity_name': entity.name,
                'field_id': assignment.field_id,
                'assignment_id': assignment.id,
                'field_name': framework_field.field_name,
                'frequency': assignment.frequency,
                'value_type': assignment.value_type,
                'unit': assignment.effective_unit,
                'status': status,
                'latest_value': latest_value,
                'latest_date': latest_date.isoformat() if latest_date else None,
                'is_computed': framework_field.is_computed
            })
    
    return jsonify(matrix_data)

@admin_bp.route('/esg_data_details/<data_id>')
@login_required
@admin_or_super_admin_required
def get_esg_data_details(data_id):
    # Get ESG data with proper access control
    if is_super_admin():
        esg_data = ESGData.query.get(data_id)
    else:
        esg_data = ESGData.get_for_tenant(db.session, data_id)
    
    if not esg_data:
        return jsonify({'error': 'Data not found or access denied'}), 404
    
    # Get related framework field
    framework_field = FrameworkDataField.query.get(esg_data.field_id)
    
    # Get audit logs for this data
    audit_logs = ESGDataAuditLog.query.filter_by(data_id=data_id)\
                    .order_by(ESGDataAuditLog.change_date.desc()).all()
    
    return jsonify({
        'data_id': esg_data.data_id,
        'entity_name': esg_data.entity.name,
        'field_name': framework_field.field_name if framework_field else 'Unknown',
        'raw_value': esg_data.raw_value,
        'calculated_value': esg_data.calculated_value,
        'reporting_date': esg_data.reporting_date.isoformat(),
        'created_at': esg_data.created_at.isoformat(),
        'updated_at': esg_data.updated_at.isoformat(),
        'is_computed': framework_field.is_computed if framework_field else False,
        'audit_logs': [{
            'change_type': log.change_type,
            'old_value': log.old_value,
            'new_value': log.new_value,
            'changed_by': log.user.name,
            'changed_by_name': log.user.name,  # Ensure frontend compatibility
            'change_date': log.change_date.isoformat()
        } for log in audit_logs]
    })

def recompute_field_value_admin(computed_field_id, entity_id, reporting_date):
    """
    Admin utility function to recompute a field value.
    Uses the same aggregation service as user routes for consistency.
    """
    try:
        return aggregation_service.compute_field_value(
            computed_field_id, 
            entity_id, 
            reporting_date
        )
    except Exception as e:
        current_app.logger.error(f'Admin: Error computing field value: {str(e)}')
        return None

def recompute_multiple_fields_admin(field_entity_date_tuples):
    """
    Admin utility function to recompute multiple fields efficiently.
    Uses bulk operations for better performance.
    """
    try:
        return aggregation_service.compute_multiple_fields(field_entity_date_tuples)
    except Exception as e:
        current_app.logger.error(f'Admin: Error in bulk field computation: {str(e)}')
        return {}

def get_field_aggregation_summary_admin(computed_field_id, entity_id, reporting_date):
    """
    Admin utility function to get detailed aggregation summary.
    Useful for transparency and debugging in admin interface.
    """
    try:
        return aggregation_service.get_aggregation_summary(
            computed_field_id,
            entity_id,
            reporting_date
        )
    except Exception as e:
        current_app.logger.error(f'Admin: Error getting aggregation summary: {str(e)}')
        return {}

@admin_bp.route('/api/aggregation-summary/<computed_field_id>/<int:entity_id>')
@login_required
@admin_or_super_admin_required
def get_aggregation_summary(computed_field_id, entity_id):
    """
    API endpoint to get detailed aggregation summary for a computed field.
    Provides transparency on how computed values are calculated.
    """
    try:
        date_str = request.args.get('reporting_date')
        if not date_str:
            return jsonify({'error': 'Reporting date is required'}), 400
        
        reporting_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        summary = get_field_aggregation_summary_admin(
            computed_field_id,
            entity_id,
            reporting_date
        )
        
        if not summary:
            return jsonify({'error': 'No aggregation summary available'}), 404
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        current_app.logger.error(f'Error getting aggregation summary: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/recompute-field', methods=['POST'])
@login_required
@admin_or_super_admin_required
def recompute_field():
    try:
        data = request.get_json()
        computed_field_id = data.get('computed_field_id')
        entity_id = data.get('entity_id')
        reporting_date_str = data.get('reporting_date')
        
        if not all([computed_field_id, entity_id, reporting_date_str]):
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400
        
        # Validate access to the data through assignments
        if not is_super_admin():
            # Regular admin can only recompute their tenant's data
            assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
                field_id=computed_field_id,
                entity_id=entity_id,
                is_active=True
            ).first()
            if not assignment:
                return jsonify({
                    'success': False,
                    'error': 'Access denied to the specified data'
                }), 403
        
        reporting_date = datetime.strptime(reporting_date_str, '%Y-%m-%d').date()
        
        # Perform recomputation
        computed_value = recompute_field_value_admin(computed_field_id, entity_id, reporting_date)
        
        if computed_value is not None:
            return jsonify({
                'success': True,
                'computed_value': computed_value,
                'message': 'Field recomputed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to compute field value'
            })
            
    except Exception as e:
        current_app.logger.error(f'Error in field recomputation: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/api/bulk-recompute', methods=['POST'])
@login_required
@admin_or_super_admin_required
def bulk_recompute_fields():
    try:
        data = request.get_json()
        field_entity_date_tuples = []
        
        for item in data.get('computations', []):
            computed_field_id = item.get('computed_field_id')
            entity_id = item.get('entity_id')
            reporting_date_str = item.get('reporting_date')
            
            if not all([computed_field_id, entity_id, reporting_date_str]):
                continue
            
            # Validate access for regular admins through assignments
            if not is_super_admin():
                assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
                    field_id=computed_field_id,
                    entity_id=entity_id,
                    is_active=True
                ).first()
                if not assignment:
                    continue  # Skip inaccessible data
            
            reporting_date = datetime.strptime(reporting_date_str, '%Y-%m-%d').date()
            field_entity_date_tuples.append((computed_field_id, entity_id, reporting_date))
        
        if not field_entity_date_tuples:
            return jsonify({
                'success': False,
                'error': 'No valid computations to process'
            }), 400
        
        # Perform bulk recomputation
        results = recompute_multiple_fields_admin(field_entity_date_tuples)
        
        successful_computations = sum(1 for v in results.values() if v is not None)
        
        return jsonify({
            'success': True,
            'total_requested': len(field_entity_date_tuples),
            'successful_computations': successful_computations,
            'results': {f'{k[0]}_{k[1]}_{k[2]}': v for k, v in results.items()},
            'message': f'Bulk recomputation completed: {successful_computations}/{len(field_entity_date_tuples)} successful'
        })
        
    except Exception as e:
        current_app.logger.error(f'Error in bulk recomputation: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/topics', methods=['POST'])
@login_required
@admin_or_super_admin_required
def create_topic():
    """Create a new topic for organizing fields."""
    try:
        data = request.get_json()
        
        name = data.get('name')
        description = data.get('description', '')
        parent_id = data.get('parent_id')
        framework_id = data.get('framework_id')
        company_id = data.get('company_id')  # For custom company topics
        
        if not name:
            return jsonify({'error': 'Topic name is required'}), 400
        
        # Create new topic
        topic = Topic(
            name=name,
            description=description,
            parent_id=parent_id,
            framework_id=framework_id,
            company_id=company_id
        )
        
        db.session.add(topic)
        db.session.commit()
        
        return jsonify({
            'topic_id': topic.topic_id,
            'name': topic.name,
            'description': topic.description,
            'parent_id': topic.parent_id,
            'framework_id': topic.framework_id,
            'company_id': topic.company_id,
            'level': topic.level,
            'full_path': topic.get_full_path()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating topic: {str(e)}')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/topics/custom')
@login_required
@admin_or_super_admin_required
def get_custom_topics():
    """Get custom topics for the current company."""
    try:
        # Get company_id from current user
        company_id = current_user.company_id
        if not company_id:
            return jsonify({'error': 'Company context required'}), 400
        
        # Get custom topics for this company
        topics = Topic.query.filter_by(company_id=company_id).all()
        
        # Build hierarchical structure with enhanced data
        def build_topic_tree(parent_id=None):
            children = []
            for topic in topics:
                if topic.parent_id == parent_id:
                    # Count fields using this topic
                    field_count = FrameworkDataField.query.filter_by(topic_id=topic.topic_id).count()
                    
                    # Count frameworks using this topic
                    framework_ids = set()
                    for field in FrameworkDataField.query.filter_by(topic_id=topic.topic_id).all():
                        if field.framework_id:
                            framework_ids.add(field.framework_id)
                    framework_count = len(framework_ids)
                    
                    topic_data = {
                        'topic_id': topic.topic_id,
                        'name': topic.name,
                        'description': topic.description,
                        'parent_id': topic.parent_id,
                        'level': topic.level,
                        'full_path': topic.get_full_path(),
                        'field_count': field_count,
                        'framework_count': framework_count,
                        'is_custom': True,
                        'children': build_topic_tree(topic.topic_id)
                    }
                    children.append(topic_data)
            return children
        
        topic_tree = build_topic_tree()
        
        return jsonify(topic_tree)
        
    except Exception as e:
        current_app.logger.error(f'Error fetching custom topics: {str(e)}')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/topics/<topic_id>', methods=['PUT'])
@login_required
@admin_or_super_admin_required
def update_topic(topic_id):
    """Update an existing topic."""
    try:
        topic = Topic.query.get_or_404(topic_id)
        data = request.get_json()
        
        topic.name = data.get('name', topic.name)
        topic.description = data.get('description', topic.description)
        
        # Prevent circular dependencies in parent-child relationships
        new_parent_id = data.get('parent_id')
        if new_parent_id and new_parent_id != topic.parent_id:
            # Check if new parent would create a circular dependency
            potential_parent = Topic.query.get(new_parent_id)
            if potential_parent:
                # Check if topic is an ancestor of the potential parent
                current = potential_parent.parent
                while current:
                    if current.topic_id == topic.topic_id:
                        return jsonify({'error': 'Cannot set parent - would create circular dependency'}), 400
                    current = current.parent
                topic.parent_id = new_parent_id
        
        db.session.commit()
        
        return jsonify({
            'topic_id': topic.topic_id,
            'name': topic.name,
            'description': topic.description,
            'parent_id': topic.parent_id,
            'level': topic.level,
            'full_path': topic.get_full_path()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating topic: {str(e)}')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/topics/<topic_id>', methods=['DELETE'])
@login_required
@admin_or_super_admin_required
def delete_topic(topic_id):
    """Delete a topic and optionally reassign its fields."""
    try:
        topic = Topic.query.get_or_404(topic_id)
        
        # Check if topic has children
        if topic.children:
            return jsonify({'error': 'Cannot delete topic with child topics. Delete children first.'}), 400
        
        # Check if topic has fields assigned
        if topic.data_fields:
            return jsonify({
                'error': f'Topic has {len(topic.data_fields)} fields assigned. Reassign fields before deletion.',
                'field_count': len(topic.data_fields),
                'fields': [{'field_id': f.field_id, 'field_name': f.field_name} for f in topic.data_fields]
            }), 400
        
        db.session.delete(topic)
        db.session.commit()
        
        return jsonify({'message': 'Topic deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting topic: {str(e)}')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/topics-management')
@login_required
@admin_or_super_admin_required
def topics_management():
    """Standalone topic management page."""
    return render_template('admin/topics.html')


@admin_bp.route('/topics/<topic_id>/usage')
@login_required
@admin_or_super_admin_required
def get_topic_usage(topic_id):
    """Get detailed usage information for a specific topic."""
    try:
        topic = Topic.query.get_or_404(topic_id)
        
        # Get all fields using this topic
        fields = FrameworkDataField.query.filter_by(topic_id=topic_id).all()
        
        # Group fields by framework
        frameworks_usage = {}
        for field in fields:
            framework_id = field.framework_id
            if framework_id not in frameworks_usage:
                framework = Framework.query.get(framework_id)
                frameworks_usage[framework_id] = {
                    'framework_id': framework_id,
                    'framework_name': framework.framework_name if framework else 'Unknown',
                    'description': framework.description if framework else '',
                    'fields': [],
                    'field_count': 0
                }
            
            frameworks_usage[framework_id]['fields'].append({
                'field_id': field.field_id,
                'field_name': field.field_name,
                'field_code': field.field_code,
                'value_type': field.value_type,
                'is_computed': field.is_computed
            })
            frameworks_usage[framework_id]['field_count'] += 1
        
        usage_data = {
            'topic_id': topic.topic_id,
            'topic_name': topic.name,
            'total_fields': len(fields),
            'frameworks': list(frameworks_usage.values())
        }
        
        return jsonify(usage_data)
        
    except Exception as e:
        current_app.logger.error(f'Error getting topic usage: {str(e)}')
        return jsonify({'error': str(e)}), 500


# Phase 3: Enhanced dependency tracking endpoints

@admin_bp.route('/fields/<field_id>/dependants')
@login_required
@admin_or_super_admin_required
def get_field_dependants(field_id):
    """Get all computed fields that depend on this field (Phase 3)."""
    try:
        field = FrameworkDataField.query.get_or_404(field_id)
        dependants = field.get_dependants()
        
        result = []
        for dependant in dependants:
            result.append({
                'field_id': dependant.field_id,
                'field_name': dependant.field_name,
                'field_code': dependant.field_code,
                'framework_name': dependant.framework.framework_name,
                'formula_expression': dependant.formula_expression,
                'topic_name': dependant.topic.name if dependant.topic else None
            })
        
        return jsonify({
            'field_id': field_id,
            'field_name': field.field_name,
            'dependant_count': len(dependants),
            'dependants': result
        })
        
    except Exception as e:
        current_app.logger.error(f'Error fetching field dependants: {str(e)}')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/fields/<field_id>/can_delete')
@login_required 
@admin_or_super_admin_required
def check_field_deletion(field_id):
    """Check if a field can be safely deleted (Phase 3)."""
    try:
        field = FrameworkDataField.query.get_or_404(field_id)
        
        can_delete = not field.has_dependants()
        dependants = field.get_dependants() if not can_delete else []
        
        return jsonify({
            'can_delete': can_delete,
            'dependant_count': len(dependants),
            'blocking_fields': [
                {
                    'field_id': dep.field_id,
                    'field_name': dep.field_name,
                    'framework_name': dep.framework.framework_name
                } for dep in dependants
            ] if dependants else []
        })
        
    except Exception as e:
        current_app.logger.error(f'Error checking field deletion: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Phase 4: Unit-aware input functionality

@admin_bp.route('/fields/<field_id>/unit_options')
@login_required
@admin_or_super_admin_required
def get_field_unit_options(field_id):
    """Get unit options for a specific field based on its unit category (Phase 4)."""
    try:
        field = FrameworkDataField.query.get_or_404(field_id)
        unit_options = get_unit_options_for_field(field)
        
        return jsonify({
            'field_id': field_id,
            'field_name': field.field_name,
            'unit_category': field.unit_category,
            'default_unit': field.default_unit,
            'unit_options': unit_options
        })
        
    except Exception as e:
        current_app.logger.error(f'Error fetching unit options for field {field_id}: {str(e)}')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/convert_unit', methods=['POST'])
@login_required
@admin_or_super_admin_required
def convert_unit():
    """Convert a value from one unit to another (Phase 4)."""
    try:
        data = request.get_json()
        value = float(data.get('value', 0))
        from_unit = data.get('from_unit')
        to_unit = data.get('to_unit')
        
        if not from_unit or not to_unit:
            return jsonify({'error': 'Both from_unit and to_unit are required'}), 400
        
        converted_value, success, error = UnitConverter.convert_value(value, from_unit, to_unit)
        
        if success:
            return jsonify({
                'success': True,
                'original_value': value,
                'original_unit': from_unit,
                'converted_value': converted_value,
                'target_unit': to_unit,
                'conversion_factor': converted_value / value if value != 0 else 1
            })
        else:
            return jsonify({
                'success': False,
                'error': error,
                'original_value': value,
                'original_unit': from_unit,
                'target_unit': to_unit
            }), 400
            
    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        current_app.logger.error(f'Error converting units: {str(e)}')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/validate_unit', methods=['POST'])
@login_required
@admin_or_super_admin_required
def validate_unit():
    """Validate if a unit is appropriate for a field (Phase 4)."""
    try:
        data = request.get_json()
        unit = data.get('unit')
        field_id = data.get('field_id')
        
        if not field_id:
            return jsonify({'error': 'field_id is required'}), 400
        
        field = FrameworkDataField.query.get_or_404(field_id)
        is_valid, error_message = validate_esg_data_unit(unit, field)
        
        return jsonify({
            'is_valid': is_valid,
            'unit': unit,
            'field_id': field_id,
            'field_unit_category': field.unit_category,
            'field_default_unit': field.default_unit,
            'error_message': error_message
        })
        
    except Exception as e:
        current_app.logger.error(f'Error validating unit: {str(e)}')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/unit_categories')
@login_required
@admin_or_super_admin_required
def get_unit_categories():
    """Get all available unit categories and their units (Phase 4)."""
    try:
        categories = {}
        for category in UnitConverter.CONVERSION_FACTORS.keys():
            categories[category] = {
                'name': category.title(),
                'base_unit': UnitConverter.CONVERSION_FACTORS[category]['base'],
                'units': UnitConverter.get_unit_dropdown_options(category)
            }
        
        return jsonify(categories)
        
    except Exception as e:
        current_app.logger.error(f'Error fetching unit categories: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Phase 4.2: Field Import Template System

@admin_bp.route('/import_templates')
@login_required
@admin_or_super_admin_required
def get_import_templates():
    """Get available framework import templates (Phase 4.2)."""
    try:
        templates = FieldImportTemplate.get_available_templates()
        return jsonify({
            'available_templates': templates,
            'success': True
        })
        
    except Exception as e:
        current_app.logger.error(f'Error fetching import templates: {str(e)}')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/import_templates/<template_key>/preview')
@login_required
@admin_or_super_admin_required
def preview_template_import(template_key):
    """Preview what would be imported from a template (Phase 4.2)."""
    try:
        # Get existing field codes to detect duplicates
        existing_fields = FrameworkDataField.query.all()
        existing_field_codes = [field.field_code for field in existing_fields]
        
        preview = FieldImportTemplate.preview_template_diff(template_key, existing_field_codes)
        
        return jsonify({
            'success': True,
            'preview': preview
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f'Error previewing template {template_key}: {str(e)}')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/import_templates/<template_key>/import', methods=['POST'])
@login_required
@admin_or_super_admin_required
def import_template_framework(template_key):
    """Import a framework from a template (Phase 4.2)."""
    try:
        data = request.get_json()
        selected_field_codes = data.get('selected_field_codes')  # Optional: import only selected fields
        framework_name_override = data.get('framework_name')  # Optional: override template name
        
        # Get template data
        template = FieldImportTemplate.get_template(template_key)
        
        # Create framework
        framework_name = framework_name_override or template["framework_name"]
        new_framework = Framework(
            framework_name=framework_name,
            description=template["description"],
            company_id=current_user.company_id
        )
        db.session.add(new_framework)
        db.session.flush()  # To get framework_id
        
        # Track created topics and fields
        topic_mapping = {}  # temp_id -> actual_topic_id
        imported_fields = []
        
        # Create topics and fields recursively
        def create_topics_and_fields(topics_list, parent_topic_id=None):
            for topic_data in topics_list:
                # Create topic
                topic = Topic(
                    name=topic_data["name"],
                    description=topic_data.get("description", ""),
                    framework_id=new_framework.framework_id,
                    parent_id=parent_topic_id,
                    company_id=current_user.company_id
                )
                db.session.add(topic)
                db.session.flush()  # To get topic_id
                
                # Create fields for this topic
                if "fields" in topic_data:
                    for field_data in topic_data["fields"]:
                        field_code = field_data["field_code"]
                        
                        # Skip if we have selected fields and this isn't one of them
                        if selected_field_codes and field_code not in selected_field_codes:
                            continue
                        
                        # Check for duplicate field codes within company
                        existing_field = FrameworkDataField.query.filter_by(
                            field_code=field_code,
                            company_id=current_user.company_id
                        ).first()
                        if existing_field:
                            current_app.logger.warning(f'Skipping duplicate field code: {field_code}')
                            continue
                        
                        # Create field
                        field = FrameworkDataField(
                            framework_id=new_framework.framework_id,
                            company_id=current_user.company_id,
                            field_name=field_data["field_name"],
                            field_code=field_code,
                            description=field_data.get("description", ""),
                            unit_category=field_data.get("unit_category"),
                            default_unit=field_data.get("default_unit"),
                            value_type=field_data.get("value_type", "NUMBER"),
                            topic_id=topic.topic_id,
                            is_computed=field_data.get("is_computed", False),
                            formula_expression=field_data.get("formula_expression")
                        )
                        db.session.add(field)
                        imported_fields.append({
                            'field_name': field.field_name,
                            'field_code': field.field_code,
                            'topic_name': topic.name
                        })
                
                # Process child topics recursively
                if "children" in topic_data:
                    create_topics_and_fields(topic_data["children"], topic.topic_id)
        
        # Create all topics and fields
        create_topics_and_fields(template.get("topics", []))
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'framework_id': new_framework.framework_id,
            'framework_name': new_framework.framework_name,
            'imported_field_count': len(imported_fields),
            'imported_fields': imported_fields,
            'message': f'Successfully imported {len(imported_fields)} fields from {template["framework_name"]} template'
        })
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error importing template {template_key}: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Legacy coverage route removed - now handled by admin_frameworks_api.py

@admin_bp.route('/frameworks/draft', methods=['POST'])
@login_required
@admin_or_super_admin_required
def save_framework_draft():
    """Save framework draft for later completion"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # For now, store draft in session (could be moved to database)
        from flask import session
        draft_id = f"draft_{current_user.id}_{datetime.now().timestamp()}"
        session[f'framework_draft_{draft_id}'] = data
        
        return jsonify({
            'success': True,
            'draft_id': draft_id,
            'message': 'Draft saved successfully'
        })

    except Exception as e:
        current_app.logger.error(f"Error saving framework draft: {str(e)}")
        return jsonify({'error': 'Failed to save draft'}), 500

@admin_bp.route('/recent_activity')
@login_required
@admin_or_super_admin_required
def get_recent_activity():
    """Get recent activity related to frameworks and data points."""
    try:
        activities = []

        # Fetch recent framework creations
        recent_frameworks = (Framework.query.filter_by(company_id=current_user.company_id)
                            .order_by(Framework.created_at.desc()).limit(5).all())
        for fw in recent_frameworks:
            activities.append({
                'type': 'Framework Created',
                'name': fw.framework_name,
                'date': fw.created_at.isoformat()
            })

        # Fetch recent data point assignments
        recent_assignments = (DataPointAssignment.query.filter_by(
                                 company_id=current_user.company_id,
                                 is_active=True)
                             .order_by(DataPointAssignment.assigned_date.desc()).limit(5).all())
        for assign in recent_assignments:
            field_name = assign.field.field_name if assign.field else 'Unknown Field'
            entity_name = assign.entity.name if assign.entity else 'Unknown Entity'
            activities.append({
                'type': 'Data Point Assigned',
                'name': f'{field_name} to {entity_name}',
                'date': assign.assigned_date.isoformat()
            })

        # Sort activities by date in descending order
        activities.sort(key=lambda x: x['date'], reverse=True)

        return jsonify({
            'success': True,
            'activities': activities[:10] # Limit to top 10 recent activities
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching recent activity: {str(e)}")
        return jsonify({'error': 'Failed to fetch recent activity'}), 500

# Removed duplicate route - now handled by admin_frameworks_api.py

# Removed duplicate route - now handled by admin_frameworks_api.py

@admin_bp.route('/frameworks/draft/<draft_id>')
@login_required
@admin_or_super_admin_required
def load_framework_draft(draft_id):
    """Load framework draft"""
    try:
        from flask import session
        draft_key = f'framework_draft_{draft_id}'
        
        if draft_key not in session:
            return jsonify({'success': False, 'error': 'Draft not found'}), 404
        
        draft_data = session[draft_key]
        
        return jsonify({
            'success': True,
            'draft': draft_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error loading framework draft: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to load draft'}), 500

@admin_bp.route('/import_template', methods=['POST'])
@login_required
@admin_or_super_admin_required
def import_template():
    """Import template data points for wizard"""
    try:
        data = request.get_json()
        template_key = data.get('template_key')
        
        if not template_key:
            return jsonify({'success': False, 'error': 'Template key required'}), 400
        
        # Get template data using existing import functionality
        template = FieldImportTemplate.get_template(template_key)
        if not template:
            return jsonify({'success': False, 'error': 'Template not found'}), 404
        
        # Convert template fields to wizard format
        data_points = []
        for field_data in template.get('fields', []):
            data_points.append({
                'name': field_data.get('name', ''),
                'field_code': field_data.get('field_code', ''),
                'value_type': field_data.get('value_type', 'Numeric'),
                'unit_category': field_data.get('unit_category', ''),
                'default_unit': field_data.get('default_unit', ''),
                'description': field_data.get('description', ''),
                'is_computed': field_data.get('is_computed', False),
                'formula': field_data.get('formula', ''),
                'topic_id': None  # Will be assigned later if topics are created
            })
        
        return jsonify({
            'success': True,
            'data_points': data_points,
            'template_name': template.get('name', template_key)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error importing template: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to import template'}), 500

@admin_bp.route('/frameworks/<framework_id>/details', methods=['GET'])
@login_required
@admin_or_super_admin_required
def get_framework_coverage_details(framework_id):
    """Get detailed framework information including field data status"""
    try:
        # Use service layer for framework details with data status
        from ..services import frameworks_service
        
        details = frameworks_service.get_framework_details_with_data_status(framework_id, current_user.company_id)
        if not details:
            return jsonify({'error': 'Framework not found'}), 404
        
        return jsonify(details)
        
    except Exception as e:
        current_app.logger.error(f"Error getting framework details: {str(e)}")
        return jsonify({'error': 'Failed to get framework details'}), 500

# Duplicate route moved to admin_frameworks_api.py; keeping function for internal reuse but not registered
# def get_framework_topics(framework_id): (route disabled)
# The following original implementation is retained without Flask decorators for reference
def _deprecated_get_framework_topics(framework_id):
    """Get topic tree for a specific framework."""
    try:
        # Get all topics for this framework (including root topics)
        topics = Topic.query.filter_by(framework_id=framework_id).all()
        
        # Build hierarchical structure
        def build_topic_tree(parent_id=None):
            children = []
            for topic in topics:
                if topic.parent_id == parent_id:
                    topic_data = {
                        'topic_id': topic.topic_id,
                        'name': topic.name,
                        'description': topic.description,
                        'level': topic.level,
                        'full_path': topic.get_full_path(),
                        'field_count': len(topic.data_fields),
                        'children': build_topic_tree(topic.topic_id)
                    }
                    children.append(topic_data)
            return children
        
        topic_tree = build_topic_tree()
        
        return jsonify(topic_tree)
        
    except Exception as e:
        current_app.logger.error(f'Error fetching framework topics: {str(e)}')
        return jsonify({'error': str(e)}), 500


# Material Topics Assignment Endpoints

@admin_bp.route('/topics/company_dropdown')
@login_required
@admin_or_super_admin_required
def get_company_topics_for_dropdown():
    """Get company topics optimized for dropdown selection in assignment interface."""
    try:
        company_id = current_user.company_id
        if not company_id:
            return jsonify({'error': 'Company context required'}), 400
        
        # Get all company-specific topics
        topics = Topic.query.filter_by(company_id=company_id).order_by(Topic.name).all()
        
        # Build flattened list with hierarchical display names
        dropdown_options = []
        
        def add_topic_and_children(topic, level=0):
            # Create display name with indentation for hierarchy
            indent = "  " * level  # 2 spaces per level
            display_name = f"{indent}{topic.name}" if level > 0 else topic.name
            
            dropdown_options.append({
                'topic_id': topic.topic_id,
                'name': topic.name,
                'display_name': display_name,
                'full_path': topic.get_full_path(),
                'level': level,
                'description': topic.description
            })
            
            # Add children recursively
            children = [t for t in topics if t.parent_id == topic.topic_id]
            for child in sorted(children, key=lambda x: x.name):
                add_topic_and_children(child, level + 1)
        
        # Add root topics and their children
        root_topics = [t for t in topics if t.parent_id is None]
        for topic in sorted(root_topics, key=lambda x: x.name):
            add_topic_and_children(topic)
        
        return jsonify({
            'success': True,
            'topics': dropdown_options,
            'count': len(dropdown_options)
        })
        
    except Exception as e:
        current_app.logger.error(f'Error fetching company topics for dropdown: {str(e)}')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/assignments/bulk_update_topics', methods=['POST'])
@login_required
@admin_or_super_admin_required
def bulk_update_assignment_topics():
    """Bulk update topic assignments for multiple data point assignments."""
    try:
        data = request.get_json()
        assignment_ids = data.get('assignment_ids', [])
        topic_id = data.get('topic_id')  # Can be None to unassign topics
        
        if not assignment_ids:
            return jsonify({'success': False, 'error': 'No assignments specified'}), 400
        
        # Validate topic exists and belongs to company
        if topic_id:
            topic = Topic.query.filter_by(
                topic_id=topic_id, 
                company_id=current_user.company_id
            ).first()
            if not topic:
                return jsonify({'success': False, 'error': 'Topic not found or access denied'}), 404
        
        # Update assignments
        updated_count = 0
        for assignment_id in assignment_ids:
            assignment = DataPointAssignment.query.get(assignment_id)
            if assignment and assignment.company_id == current_user.company_id:
                assignment.assigned_topic_id = topic_id
                updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'updated_count': updated_count,
            'message': f'Updated {updated_count} assignment(s)'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in bulk topic update: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500





