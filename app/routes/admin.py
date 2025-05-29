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
import json
import re
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'Admin':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/home')
@admin_required
def home():
    return render_template('admin/home.html')

@admin_bp.route('/data_hierarchy', methods=['GET', 'POST'])
@admin_required
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

            # Check for duplicate names
            if Entity.query.filter_by(name=name).first():
                return jsonify({'success': False, 'message': 'An entity with this name already exists.'}), 400
            
            # Validate parent entity exists
            parent = Entity.query.get(parent_id)
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
            new_entity = Entity(
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
   
    entities = Entity.query.all()
    hierarchy_data = [
        build_hierarchy(entity, set(), entities) 
        for entity in entities if entity.parent_id is None
    ]
    hierarchy_data = [item for item in hierarchy_data if item is not None]

    return render_template('admin/data_hierarchy.html', 
                         entities=entities, 
                         hierarchy_data=hierarchy_data)

@admin_bp.route('/frameworks', methods=['GET', 'POST'])
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
def assign_data_points():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            data_point_id = data.get('data_point_id')
            entity_ids = data.get('entity_ids', [])
            
            try:
                # Get the data point
                data_point = DataPoint.query.get(data_point_id)
                if data_point:
                    # Get the entities
                    entities = Entity.query.filter(Entity.id.in_(entity_ids)).all()
                    # Assign entities to the data point
                    data_point.entities = entities
                    db.session.commit()
                    return jsonify({'success': True})
                
                return jsonify({'success': False, 'message': 'Data point not found'}), 404
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': str(e)}), 500
    
    # For GET request
    frameworks = Framework.query.all()
    entities = Entity.query.all()
    data_points = DataPoint.query.all()

    return render_template('admin/assign_data_points.html', 
                         frameworks=frameworks,
                         entities=entities, 
                         data_points=data_points)

@admin_bp.route('/get_entities')
@admin_required
def get_entities():
    entities = Entity.query.all()
    return jsonify([{
        'id': entity.id,
        'name': entity.name
    } for entity in entities])

@admin_bp.route('/create_user', methods=['POST'])
@admin_required
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
@admin_required  # Restrict access to Admins
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
@admin_required
def get_existing_data_points():
    try:
        data_points = DataPoint.query.all()
        return jsonify([{
            'field_id': dp.id,
            'field_name': dp.name
        } for dp in data_points])
    except Exception as e:
        current_app.logger.error(f'Error fetching data points: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/save_data_points', methods=['POST'])
@admin_required
def save_data_points():
    try:
        data = request.get_json()
        field_ids = data.get('field_ids', [])

        # Get existing data point IDs
        existing_data_point_ids = {dp.id for dp in DataPoint.query.all()}
        
        # Determine which points to remove
        ids_to_remove = existing_data_point_ids - set(field_ids)
        if ids_to_remove:
            DataPoint.query.filter(DataPoint.id.in_(ids_to_remove)).delete(synchronize_session=False)

        # Add new data points
        for field_id in field_ids:
            # Check if data point already exists
            if field_id not in existing_data_point_ids:
                # Get the framework field details
                field = FrameworkDataField.query.get(field_id)
                if field:
                    new_data_point = DataPoint(
                        name=field.field_name,
                        value_type='numeric',  # Set appropriate default
                        framework_id=field.framework_id
                    )
                    # Explicitly set the UUID from the field_id
                    new_data_point.id = field_id
                    db.session.add(new_data_point)

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error saving data points: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/get_data_point_assignments')
@admin_required
def get_data_point_assignments():
    try:
        # Get all data points and their assigned entities
        data_points = DataPoint.query.all()
        assignments = {}
        
        for dp in data_points:
            # Get all entity IDs assigned to this data point
            assigned_entity_ids = [entity.id for entity in dp.entities]
            assignments[dp.id] = assigned_entity_ids
            
        return jsonify(assignments)
    except Exception as e:
        current_app.logger.error(f'Error fetching data point assignments: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/data_review', methods=['GET', 'POST'])
@admin_required
def data_review():
    """Admin route to view and edit ESG data submitted by subsidiaries."""
    if request.method == 'POST':
        try:
            data = request.get_json()
            data_id = data.get('data_id')
            new_value = data.get('new_value')
            edit_reason = data.get('edit_reason', '')
            
            # Get the ESG data record
            esg_data = ESGData.query.get(data_id)
            if not esg_data:
                return jsonify({'success': False, 'message': 'Data record not found'}), 404
            
            # Store old value for audit
            old_value = esg_data.raw_value or esg_data.calculated_value
            
            # Update the data
            if esg_data.field.is_computed:
                esg_data.calculated_value = float(new_value) if new_value else None
            else:
                esg_data.raw_value = new_value
            
            # Create audit log entry
            audit_log = ESGDataAuditLog(
                data_id=data_id,
                change_type='Update',
                changed_by=current_user.id,
                old_value=float(old_value) if old_value else None,
                new_value=float(new_value) if new_value else None
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Data updated successfully'})
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating ESG data: {str(e)}')
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # GET request: display the data review page
    # Get all entities for filtering
    entities = Entity.query.all()
    
    # Get filter parameters
    entity_id = request.args.get('entity_id')
    framework_id = request.args.get('framework_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    view_type = request.args.get('view_type', 'individual')  # 'individual' or 'consolidated'
    
    # Build query - Use simple query since relationships are already configured with lazy='joined'
    query = ESGData.query
    
    if entity_id:
        if view_type == 'consolidated':
            # For consolidated view, include entity and all its children
            entity = Entity.query.get(entity_id)
            if entity:
                child_ids = [child.id for child in entity.children]
                child_ids.append(entity.id)
                query = query.filter(ESGData.entity_id.in_(child_ids))
        else:
            # Individual view - specific entity only
            query = query.filter(ESGData.entity_id == entity_id)
    
    if framework_id:
        query = query.filter(ESGData.field.has(framework_id=framework_id))
    
    if date_from:
        query = query.filter(ESGData.reporting_date >= date_from)
    
    if date_to:
        query = query.filter(ESGData.reporting_date <= date_to)
    
    # Order by reporting date and entity
    esg_data_records = query.order_by(ESGData.reporting_date.desc(), ESGData.entity_id).all()
    
    # Get frameworks for filter dropdown
    frameworks = Framework.query.all()
    
    return render_template('admin/data_review.html', 
                         esg_data_records=esg_data_records,
                         entities=entities,
                         frameworks=frameworks,
                         selected_entity_id=entity_id,
                         selected_framework_id=framework_id,
                         date_from=date_from,
                         date_to=date_to,
                         view_type=view_type)

@admin_bp.route('/audit_log')
@admin_required
def audit_log():
    # Get all audit logs with related data
    audit_logs = ESGDataAuditLog.query\
        .join(ESGDataAuditLog.user)\
        .join(ESGDataAuditLog.esg_data)\
        .order_by(ESGDataAuditLog.change_date.desc())\
        .all()
    
    return render_template('admin/audit_log.html', audit_logs=audit_logs)

@admin_bp.route('/data_status_matrix', methods=['GET'])
@admin_required
def data_status_matrix():
    """Admin route to view data collection status in matrix format."""
    
    # Get filter parameters
    selected_date = request.args.get('reporting_date')
    if not selected_date:
        selected_date = datetime.now().strftime('%Y-%m-%d')
    
    # Convert to date object for querying
    try:
        reporting_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        reporting_date = datetime.now().date()
        selected_date = reporting_date.strftime('%Y-%m-%d')
    
    # Get all assigned data points (data points that have entities assigned to them)
    assigned_data_points = DataPoint.query.filter(DataPoint.entities.any()).all()
    
    # Get all entities that have data points assigned
    entities_with_data_points = Entity.query.filter(Entity.data_points.any()).all()
    
    # Create matrix data structure
    matrix_data = {}
    
    for data_point in assigned_data_points:
        # Get the framework field to determine if it's computed
        framework_field = FrameworkDataField.query.filter_by(field_id=data_point.id).first()
        is_computed = framework_field.is_computed if framework_field else False
        
        matrix_data[data_point.id] = {
            'data_point': data_point,
            'is_computed': is_computed,
            'entities': {}
        }
        
        # Get entities assigned to this data point
        assigned_entities = data_point.entities
        
        for entity in assigned_entities:
            # Check if data exists for this data point and entity on the selected date
            esg_data = ESGData.query.filter_by(
                data_point_id=data_point.id,
                entity_id=entity.id,
                reporting_date=reporting_date
            ).first()
            
            status = 'pending'
            value = None
            last_updated = None
            
            if esg_data:
                if esg_data.raw_value is not None or esg_data.calculated_value is not None:
                    status = 'completed'
                    value = esg_data.calculated_value if esg_data.field.is_computed else esg_data.raw_value
                    last_updated = esg_data.updated_at
                else:
                    status = 'incomplete'
            
            matrix_data[data_point.id]['entities'][entity.id] = {
                'entity': entity,
                'status': status,
                'value': value,
                'last_updated': last_updated,
                'esg_data': esg_data
            }
    
    # Calculate summary statistics
    total_assignments = sum(len(dp_data['entities']) for dp_data in matrix_data.values())
    completed_assignments = sum(
        1 for dp_data in matrix_data.values() 
        for entity_data in dp_data['entities'].values() 
        if entity_data['status'] == 'completed'
    )
    completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
    
    return render_template('admin/data_status_matrix.html',
                         matrix_data=matrix_data,
                         entities_with_data_points=entities_with_data_points,
                         assigned_data_points=assigned_data_points,
                         selected_date=selected_date,
                         total_assignments=total_assignments,
                         completed_assignments=completed_assignments,
                         completion_rate=completion_rate)

@admin_bp.route('/esg_data_details/<data_id>')
@admin_required
def get_esg_data_details(data_id):
    """API endpoint to get detailed information about an ESG data record."""
    try:
        esg_data = ESGData.query.get(data_id)
        if not esg_data:
            return jsonify({'success': False, 'message': 'Data record not found'}), 404
        
        # Get framework field to check if computed
        framework_field = FrameworkDataField.query.get(esg_data.data_point_id)
        is_computed = framework_field.is_computed if framework_field else False
        
        # Get current value
        current_value = esg_data.calculated_value if is_computed else esg_data.raw_value
        
        # Get audit trail
        audit_logs = ESGDataAuditLog.query.filter_by(data_id=data_id)\
            .order_by(ESGDataAuditLog.change_date.desc())\
            .limit(10).all()
        
        # Get evidence files (if you have this model)
        evidence_files = []  # Placeholder - add actual evidence file logic if available
        
        # Determine status
        status = 'pending'
        if esg_data.raw_value is not None or esg_data.calculated_value is not None:
            status = 'completed'
        elif esg_data.raw_value == '' or esg_data.calculated_value == '':
            status = 'incomplete'
        
        data_details = {
            'data_point_name': esg_data.data_point.name if esg_data.data_point else 'N/A',
            'entity_name': esg_data.entity.name if esg_data.entity else 'N/A',
            'framework_name': framework_field.framework.framework_name if framework_field and framework_field.framework else 'N/A',
            'reporting_date': esg_data.reporting_date.isoformat() if esg_data.reporting_date else None,
            'is_computed': is_computed,
            'current_value': current_value,
            'unit': getattr(esg_data.data_point, 'unit', None) if esg_data.data_point else None,
            'updated_at': esg_data.updated_at.isoformat() if esg_data.updated_at else None,
            'status': status,
            'evidence_files': evidence_files,
            'audit_trail': [{
                'change_type': log.change_type,
                'change_date': log.change_date.isoformat() if log.change_date else None,
                'changed_by_username': log.user.username if log.user else 'System',
                'old_value': log.old_value,
                'new_value': log.new_value
            } for log in audit_logs]
        }
        
        return jsonify({'success': True, 'data': data_details})
        
    except Exception as e:
        current_app.logger.error(f'Error fetching ESG data details: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500