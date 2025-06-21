from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from ..models.user import User
from ..models.entity import Entity
from ..models.framework import Framework, FrameworkDataField, FieldVariableMapping
from ..models.data_point import DataPoint
from ..extensions import db
from ..services.email import send_registration_email
from ..services.token import generate_registration_token
from ..services.redis import check_rate_limit
from ..models.esg_data import ESGDataAuditLog, ESGData
from ..models.data_assignment import DataPointAssignment
from ..services.aggregation import aggregation_service
from ..middleware.tenant import get_current_tenant
from ..decorators.auth import admin_or_super_admin_required, tenant_required_for
import json
import re
from datetime import datetime, date

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def is_super_admin():
    """Check if current user is a super admin (no company_id)"""
    return current_user.role == 'SUPER_ADMIN'

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
            return []

def get_admin_data_points():
    """Get data points based on admin's access level"""
    if is_super_admin():
        # Super admin can see all data points
        return DataPoint.query.all()
    else:
        # Regular admin can only see their tenant's data points
        tenant = get_current_tenant()
        if tenant:
            return DataPoint.query_for_tenant(db.session).all()
        else:
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
            return []

def get_admin_assignments():
    """Get data point assignments based on admin's access level"""
    if is_super_admin():
        # Super admin can see all assignments
        return DataPointAssignment.query.all()
    else:
        # Regular admin can only see their tenant's assignments
        tenant = get_current_tenant()
        if tenant:
            return DataPointAssignment.query_for_tenant(db.session).all()
        else:
            return []

@admin_bp.route('/home')
@login_required
@admin_or_super_admin_required
def home():
    return render_template('admin/home.html')

@admin_bp.route('/data_hierarchy', methods=['GET', 'POST'])
@login_required
@admin_or_super_admin_required
def data_hierarchy():
    def build_hierarchy(entity, visited, all_entities):
        if entity.id in visited:
            return None
        visited.add(entity.id)
        users = [{"name": user.username, "email": user.email} for user in entity.users]
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
                return jsonify({'success': False, 'message': 'Parent entity is required.'}), 400

            # Check for duplicate names within tenant scope
            if is_super_admin():
                existing_entity = Entity.query.filter_by(name=name).first()
            else:
                existing_entity = Entity.exists_for_tenant(db.session, name=name)
            
            if existing_entity:
                return jsonify({'success': False, 'message': 'An entity with this name already exists.'}), 400
            
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

@admin_bp.route('/frameworks', methods=['GET', 'POST'])
@login_required
@admin_or_super_admin_required
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

            # Create new framework
            new_framework = Framework(
                framework_name=framework_name, 
                description=framework_description
            )
            db.session.add(new_framework)
            db.session.flush()  # To get the framework_id

            # Get dependencies data
            try:
                dependencies = json.loads(request.form.get('dependencies', '{}'))
            except json.JSONDecodeError:
                flash('Invalid dependencies format', 'error')
                return redirect(url_for('admin.frameworks'))

            # Process data fields
            data_point_names = request.form.getlist('data_point_name[]')
            data_point_descriptions = request.form.getlist('data_point_description[]')
            data_point_is_computed = request.form.getlist('data_point_is_computed[]')
            formula_expressions = request.form.getlist('formula_expression[]')

            for i, name in enumerate(data_point_names):
                if not name:  # Skip empty fields
                    continue

                is_computed = i < len(data_point_is_computed) and data_point_is_computed[i] == 'true'

                # Create data field
                new_field = FrameworkDataField(
                    framework_id=new_framework.framework_id,
                    field_name=name,
                    description=data_point_descriptions[i] if i < len(data_point_descriptions) else None,
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

    # GET request: fetch all frameworks
    frameworks = Framework.query.order_by(Framework.created_at.desc()).all()
    return render_template('admin/frameworks.html', frameworks=frameworks)

@admin_bp.route('/frameworks/<framework_id>', methods=['GET'])
@login_required
@admin_or_super_admin_required
def get_framework_details(framework_id):
    try:
        framework = Framework.query.get_or_404(framework_id)
        
        framework_details = {
            'framework_id': framework.framework_id,
            'framework_name': framework.framework_name,
            'description': framework.description,
            'created_at': framework.created_at.isoformat(),
            'data_fields': []
        }
        
        for field in framework.data_fields:
            field_info = {
                'field_name': field.field_name,
                'description': field.description,
                'is_computed': field.is_computed,
                'formula': field.formula_expression,
                'dependencies': []
            }
            
            # Add dependency information for computed fields
            if field.is_computed:
                for mapping in field.variable_mappings:
                    field_info['dependencies'].append({
                        'variable': mapping.variable_name,
                        'coefficient': mapping.coefficient,
                        'raw_field_name': mapping.raw_field.field_name,
                        'raw_framework_name': mapping.raw_field.framework.framework_name
                    })
            
            framework_details['data_fields'].append(field_info)
        
        return jsonify(framework_details)
    except Exception as e:
        current_app.logger.error(f'Error fetching framework details: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/get_frameworks')
@login_required
@admin_or_super_admin_required
def get_frameworks():
    """Get all frameworks for dropdown selection."""
    try:
        frameworks = Framework.query.all()
        return jsonify([{
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
    """Get all fields for a specific framework."""
    try:
        # Remove the is_computed filter to get all fields
        fields = FrameworkDataField.query.filter_by(
            framework_id=framework_id
        ).all()
        
        return jsonify([{
            'field_id': field.field_id,
            'field_name': field.field_name
        } for field in fields])
    except Exception as e:
        current_app.logger.error(f'Error fetching framework fields: {str(e)}')
        return jsonify({'error': str(e)}), 500

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

@admin_bp.route('/assign_data_points', methods=['GET', 'POST'])
@login_required
@admin_or_super_admin_required
def assign_data_points():
    if request.method == 'POST':
        try:
            # Get form data
            data_point_ids = request.form.getlist('data_point_ids')
            entity_ids = request.form.getlist('entity_ids')
            fy_start_month = int(request.form.get('fy_start_month'))
            fy_start_year = int(request.form.get('fy_start_year'))
            fy_end_year = int(request.form.get('fy_end_year'))
            frequency = request.form.get('frequency')

            if not data_point_ids or not entity_ids:
                flash('Please select at least one data point and one entity', 'error')
                return redirect(url_for('admin.assign_data_points'))

            # Validate selected entities and data points are accessible to admin
            if is_super_admin():
                # Super admin can assign any data points to any entities
                valid_entities = Entity.query.filter(Entity.id.in_(entity_ids)).all()
                valid_data_points = DataPoint.query.filter(DataPoint.id.in_(data_point_ids)).all()
            else:
                # Regular admin can only assign their tenant's data points to their tenant's entities
                valid_entities = Entity.query_for_tenant(db.session).filter(Entity.id.in_(entity_ids)).all()
                valid_data_points = DataPoint.query_for_tenant(db.session).filter(DataPoint.id.in_(data_point_ids)).all()

            # Create assignments
            assignment_count = 0
            for entity in valid_entities:
                for data_point in valid_data_points:
                    # Check if assignment already exists
                    existing_assignment = None
                    if is_super_admin():
                        existing_assignment = DataPointAssignment.query.filter_by(
                            data_point_id=data_point.id,
                            entity_id=entity.id
                        ).first()
                    else:
                        existing_assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
                            data_point_id=data_point.id,
                            entity_id=entity.id
                        ).first()
                    
                    if existing_assignment:
                        existing_assignment.is_active = True
                        existing_assignment.fy_start_month = fy_start_month
                        existing_assignment.fy_start_year = fy_start_year
                        existing_assignment.fy_end_year = fy_end_year
                        existing_assignment.frequency = frequency
                        existing_assignment.assigned_by = current_user.id
                    else:
                        # Create new assignment
                        if is_super_admin():
                            assignment = DataPointAssignment(
                                data_point_id=data_point.id,
                                entity_id=entity.id,
                                company_id=entity.company_id,  # Set company_id from entity
                                fy_start_month=fy_start_month,
                                fy_start_year=fy_start_year,
                                fy_end_year=fy_end_year,
                                frequency=frequency,
                                assigned_by=current_user.id
                            )
                        else:
                            assignment = DataPointAssignment.create_for_current_tenant(
                                db.session,
                                data_point_id=data_point.id,
                                entity_id=entity.id,
                                fy_start_month=fy_start_month,
                                fy_start_year=fy_start_year,
                                fy_end_year=fy_end_year,
                                frequency=frequency,
                                assigned_by=current_user.id
                            )
                        
                        db.session.add(assignment)
                    assignment_count += 1

            db.session.commit()
            flash(f'Successfully created/updated {assignment_count} data point assignments!', 'success')
            return redirect(url_for('admin.assign_data_points'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating assignments: {str(e)}')
            flash('An error occurred while creating assignments', 'error')
            return redirect(url_for('admin.assign_data_points'))

    # Get data for GET request
    frameworks = Framework.query.all()  # Frameworks are shared across tenants
    entities = get_admin_entities()
    data_points = get_admin_data_points()

    return render_template('admin/assign_data_points.html',
                         frameworks=frameworks,
                         entities=entities,
                         data_points=data_points)

@admin_bp.route('/get_entities')
@login_required
@admin_or_super_admin_required
def get_entities():
    entities = get_admin_entities()
    return jsonify([{'id': e.id, 'name': e.name, 'type': e.entity_type} for e in entities])

@admin_bp.route('/create_user', methods=['POST'])
@login_required
@admin_or_super_admin_required
def create_user():
    username = request.form.get('username')
    email = request.form['email']
    entity_id = request.form['entity_id']
    
    new_user = User(
        username=username, 
        email=email, 
        entity_id=entity_id, 
        role="User", 
        is_email_verified=False
    )
    db.session.add(new_user)
    db.session.commit()

    token = generate_registration_token(new_user.id)
    send_registration_email(email, token)

    return jsonify({
        'success': True, 
        'message': 'User created successfully. An email has been sent for registration.'
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
        email = data.get('email')

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
    data_points = get_admin_data_points()
    return jsonify([{
        'id': dp.id,
        'name': dp.name,
        'value_type': dp.value_type,
        'unit': dp.unit,
        'framework_id': dp.framework_id
    } for dp in data_points])

@admin_bp.route('/save_data_points', methods=['POST'])
@login_required
@admin_or_super_admin_required
def save_data_points():
    try:
        data_points_data = request.get_json()
        
        if not data_points_data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Get current data points for comparison
        current_data_points = get_admin_data_points()
        existing_data_point_ids = {dp.id for dp in current_data_points}
        
        # Process updates and additions
        new_data_point_ids = set()
        for dp_data in data_points_data:
            field_id = dp_data.get('field_id')
            new_data_point_ids.add(field_id)
            
            # Check if this is an update or new data point
            if field_id in existing_data_point_ids:
                # Update existing data point (if admin has access)
                if is_super_admin():
                    dp = DataPoint.query.get(field_id)
                else:
                    dp = DataPoint.get_for_tenant(db.session, field_id)
                
                if dp:
                    dp.name = dp_data.get('name', dp.name)
                    dp.value_type = dp_data.get('value_type', dp.value_type)
                    dp.unit = dp_data.get('unit', dp.unit)
            else:
                # Create new data point
                field = FrameworkDataField.query.get(field_id)
                if field:
                    if is_super_admin():
                        # Super admin can create data points for any tenant
                        # For now, create without tenant restriction
                        dp = DataPoint(
                            name=dp_data.get('name'),
                            value_type=dp_data.get('value_type'),
                            framework_id=field.framework_id,
                            unit=dp_data.get('unit')
                        )
                    else:
                        # Regular admin creates for their tenant
                        dp = DataPoint.create_for_current_tenant(
                            db.session,
                            name=dp_data.get('name'),
                            value_type=dp_data.get('value_type'),
                            framework_id=field.framework_id,
                            unit=dp_data.get('unit')
                        )
                    db.session.add(dp)
        
        # Remove data points that are no longer in the list (if admin has access)
        ids_to_remove = existing_data_point_ids - new_data_point_ids
        if ids_to_remove:
            if is_super_admin():
                DataPoint.query.filter(DataPoint.id.in_(ids_to_remove)).delete(synchronize_session=False)
            else:
                # For regular admins, only delete their tenant's data points
                tenant_data_points = DataPoint.query_for_tenant(db.session).filter(DataPoint.id.in_(ids_to_remove)).all()
                for dp in tenant_data_points:
                    db.session.delete(dp)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Data points saved successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/get_data_point_assignments')
@login_required
@admin_or_super_admin_required
def get_data_point_assignments():
    assignments = get_admin_assignments()
    return jsonify([{
        'id': a.id,
        'data_point_id': a.data_point_id,
        'entity_id': a.entity_id,
        'frequency': a.frequency,
        'is_active': a.is_active,
        'fy_start_month': a.fy_start_month,
        'fy_start_year': a.fy_start_year,
        'fy_end_year': a.fy_end_year
    } for a in assignments])

@admin_bp.route('/get_assignment_configurations')
@login_required
@admin_or_super_admin_required
def get_assignment_configurations():
    assignments = get_admin_assignments()
    active_assignments = [a for a in assignments if a.is_active]
    
    return jsonify([{
        'id': assignment.id,
        'data_point_id': assignment.data_point_id,
        'data_point_name': assignment.data_point.name,
        'entity_id': assignment.entity_id,
        'entity_name': assignment.entity.name,
        'frequency': assignment.frequency,
        'fy_display': assignment.get_fy_display(),
        'fy_start_month': assignment.fy_start_month,
        'fy_start_year': assignment.fy_start_year,
        'fy_end_year': assignment.fy_end_year,
        'valid_dates': [date.isoformat() for date in assignment.get_valid_reporting_dates()]
    } for assignment in active_assignments])

@admin_bp.route('/get_valid_dates/<data_point_id>/<int:entity_id>')
@login_required
@admin_or_super_admin_required
def get_valid_dates(data_point_id, entity_id):
    # Find assignment (with proper access control)
    if is_super_admin():
        assignment = DataPointAssignment.query.filter_by(
            data_point_id=data_point_id,
            entity_id=entity_id,
            is_active=True
        ).first()
    else:
        assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
            data_point_id=data_point_id,
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
    # Get entities and data points based on admin access
    entities = get_admin_entities()
    data_points = get_admin_data_points()
    
    # Get assignments based on admin access
    assignments = get_admin_assignments()
    
    # Build matrix data
    matrix_data = []
    for entity in entities:
        entity_assignments = [a for a in assignments if a.entity_id == entity.id and a.is_active]
        
        for assignment in entity_assignments:
            data_point = next((dp for dp in data_points if dp.id == assignment.data_point_id), None)
            if not data_point:
                continue
            
            framework_field = FrameworkDataField.query.filter_by(field_id=data_point.id).first()
            if not framework_field:
                continue
            
            # Get ESG data for this assignment
            if is_super_admin():
                esg_data = ESGData.query.filter_by(
                    data_point_id=data_point.id,
                    entity_id=entity.id
                ).order_by(ESGData.reporting_date.desc()).all()
            else:
                esg_data = ESGData.query_for_tenant(db.session).filter_by(
                    data_point_id=data_point.id,
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
                'data_point_id': data_point.id,
                'data_point_name': data_point.name,
                'frequency': assignment.frequency,
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
    framework_field = FrameworkDataField.query.get(esg_data.data_point_id)
    
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
            'changed_by': log.user.username,
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
        
        # Validate access to the data
        if not is_super_admin():
            # Regular admin can only recompute their tenant's data
            computed_field = DataPoint.get_for_tenant(db.session, computed_field_id)
            entity = Entity.get_for_tenant(db.session, entity_id)
            if not computed_field or not entity:
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
            
            # Validate access for regular admins
            if not is_super_admin():
                computed_field = DataPoint.get_for_tenant(db.session, computed_field_id)
                entity = Entity.get_for_tenant(db.session, entity_id)
                if not computed_field or not entity:
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