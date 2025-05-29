from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from ..models.data_point import DataPoint
from ..models.esg_data import ESGData, ESGDataAuditLog, ESGDataAttachment
from ..extensions import db
from datetime import datetime, UTC, date, timedelta
import os
from werkzeug.utils import secure_filename
from flask import current_app
from ..models.framework import FrameworkDataField, FieldVariableMapping
from ..models.entity import Entity

user_bp = Blueprint('user', __name__, url_prefix='/user')

def user_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'User':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@user_bp.route('/dashboard', methods=['GET','POST'])
@user_required
def dashboard():
    if not current_user.entity_id:
        flash('No entity assigned to user', 'error')
        return redirect(url_for('auth.login'))
    
    # Get selected date (default to current month)
    selected_date = request.args.get('date')
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m').date() if selected_date else date.today().replace(day=1)
    except ValueError:
        selected_date = date.today().replace(day=1)
    
    # Get the user's entity and its parent entities
    user_entity = Entity.query.get(current_user.entity_id)
    parent_entities = []
    current_entity = user_entity
    while current_entity.parent_id:
        parent_entities.append(current_entity.parent_id)
        current_entity = current_entity.parent

    # First, get all raw input fields and their relationships
    raw_fields = {}  # Dictionary to store raw fields and the computed fields that depend on them
    computed_fields = set()  # Set to store all computed field IDs
    
    # Get all variable mappings to build dependency relationships
    variable_mappings = (FieldVariableMapping.query
        .join(FrameworkDataField, FrameworkDataField.field_id == FieldVariableMapping.raw_field_id)
        .all())
    
    for mapping in variable_mappings:
        computed_fields.add(mapping.computed_field_id)
        if mapping.raw_field_id not in raw_fields:
            raw_fields[mapping.raw_field_id] = {
                'computed_fields': set(),
                'variable_names': {}
            }
        raw_fields[mapping.raw_field_id]['computed_fields'].add(mapping.computed_field_id)
        raw_fields[mapping.raw_field_id]['variable_names'][mapping.computed_field_id] = mapping.variable_name

    # Get all data points with proper filtering
    all_data_points = (DataPoint.query
        .join(DataPoint.framework)
        .join(
            FrameworkDataField,
            FrameworkDataField.field_id == DataPoint.id
        )
        .join(
            Entity,
            DataPoint.entities
        )
        .filter(
            Entity.id.in_([current_user.entity_id] + parent_entities)
        )
        .add_columns(
            FrameworkDataField.description,
            FrameworkDataField.is_computed,
            FrameworkDataField.formula_expression,
            Entity.id.label('assigned_entity_id'),
            Entity.name.label('assigned_entity_name')
        )
        .distinct()
        .all())

    # Organize data points into categories
    raw_input_points = []
    computed_points = []
    raw_dependencies = {}  # Store raw dependencies and their computed fields

    for dp, desc, is_computed, formula, assigned_entity_id, assigned_entity_name in all_data_points:
        point_data = {
            'id': dp.id,
            'name': dp.name,
            'value_type': dp.value_type,
            'unit': dp.unit,
            'description': desc,
            'is_computed': is_computed,
            'formula': formula,
            'status': get_data_point_status(dp.id, current_user.entity_id, selected_date),
            'assigned_entity': assigned_entity_name,
            'dependencies': []
        }

        if dp.id in raw_fields:  # This is a raw dependency
            raw_dependencies[dp.id] = {
                'data': point_data,
                'computed_fields': raw_fields[dp.id]['computed_fields'],
                'variable_names': raw_fields[dp.id]['variable_names']
            }
        elif dp.id in computed_fields:  # This is a computed field
            # Get dependencies for this computed field
            deps = (FieldVariableMapping.query
                   .filter_by(computed_field_id=dp.id)
                   .all())
            
            point_data['dependencies'] = [
                {
                    'field_id': dep.raw_field_id,
                    'field_name': FrameworkDataField.query.get(dep.raw_field_id).field_name,
                    'variable_name': dep.variable_name,
                    'coefficient': dep.coefficient
                } for dep in deps
            ]
            computed_points.append(point_data)
        else:  # This is a regular raw input field
            raw_input_points.append(point_data)

    # Get ESG data entries
    esg_data_entries = ESGData.query.filter_by(
        entity_id=current_user.entity_id,
        reporting_date=selected_date
    ).all()

    # Create a properly structured dictionary for entity data entries
    entity_data_entries = {}
    for entry in esg_data_entries:
        entity_data_entries[entry.data_point_id] = {
            'raw_value': entry.raw_value,
            'calculated_value': entry.calculated_value,
            'entity_id': entry.entity_id,
            'data_id': entry.data_id
        }

    return render_template('user/dashboard.html',
                         raw_input_points=raw_input_points,
                         computed_points=computed_points,
                         raw_dependencies=raw_dependencies,
                         entity_data_entries=entity_data_entries,
                         selected_date=selected_date)

def get_data_point_status(data_point_id, entity_id, reporting_date):
    """Determine the status of a data point."""
    entry = ESGData.query.filter_by(
        data_point_id=data_point_id,
        entity_id=entity_id,
        reporting_date=reporting_date
    ).first()
    
    if not entry:
        return 'pending'
    elif entry.raw_value is None:
        return 'error'
    else:
        return 'complete'

@user_bp.route('/submit_data', methods=['POST'])
@user_required
def submit_data():
    try:
        reporting_date = request.form.get('reporting_date')
        if not reporting_date:
            return jsonify({
                'success': False,
                'error': 'Reporting date is required'
            }), 400
        
        reporting_date = datetime.strptime(reporting_date, '%Y-%m-%d').date()
        
        form_data = request.form
        print("Form data received:", form_data)
        
        affected_computed_fields = set()
        
        # First, create/update all ESG data entries
        for key, value in form_data.items():
            if key.startswith('data_point_'):
                field_id = key.replace('data_point_', '')
                print(f"\nProcessing field {field_id} with value {value}")
                
                # Skip empty values
                if not value or not value.strip():
                    continue
                
                # Get the data point and its framework field
                data_point = DataPoint.query.get(field_id)
                framework_field = FrameworkDataField.query.filter_by(field_id=field_id).first()
                
                if not data_point or not framework_field:
                    print(f"Data point or framework field not found for {field_id}")
                    continue

                # Skip if this is a computed field
                if framework_field.is_computed:
                    print(f"Skipping computed field {field_id}")
                    continue

                # Check if this data point is assigned to the user's entity
                if current_user.entity_id not in [entity.id for entity in data_point.entities]:
                    print(f"Data point {field_id} not assigned to user's entity")
                    continue

                # Find or create ESGData entry
                esg_data = ESGData.query.filter_by(
                    data_point_id=field_id,
                    entity_id=current_user.entity_id,
                    reporting_date=reporting_date
                ).first()
                
                try:
                    # Convert value based on data point type
                    if data_point.value_type == 'numeric':
                        processed_value = float(value)
                    else:
                        processed_value = str(value)
                except ValueError:
                    print(f"Error converting value '{value}' for field {field_id}")
                    continue

                old_value = None
                if esg_data:
                    old_value = esg_data.raw_value
                    esg_data.raw_value = processed_value
                else:
                    esg_data = ESGData(
                        entity_id=current_user.entity_id,
                        field_id=field_id,
                        data_point_id=field_id,
                        raw_value=processed_value,
                        reporting_date=reporting_date
                    )
                    db.session.add(esg_data)
                
                # Commit to ensure the ESG data record exists
                db.session.commit()
                
                # Create audit log entry if value changed
                if old_value != processed_value:
                    audit_log = ESGDataAuditLog(
                        data_id=esg_data.data_id,
                        change_type='Update',
                        changed_by=current_user.id,
                        old_value=float(old_value) if old_value and isinstance(old_value, (int, float)) else old_value,
                        new_value=float(processed_value) if isinstance(processed_value, (int, float)) else processed_value
                    )
                    db.session.add(audit_log)
                    db.session.commit()
                
                # Find computed fields that depend on this raw field
                dependent_computed_fields = (FieldVariableMapping.query
                    .filter_by(raw_field_id=field_id)
                    .all())
                
                for dep in dependent_computed_fields:
                    affected_computed_fields.add(dep.computed_field_id)
        
        # Now process all affected computed fields
        print(f"\nProcessing {len(affected_computed_fields)} affected computed fields")
        for computed_field_id in affected_computed_fields:
            # Find or create the computed field's ESG data entry
            computed_data = ESGData.query.filter_by(
                data_point_id=computed_field_id,
                entity_id=current_user.entity_id,
                reporting_date=reporting_date
            ).first()
            
            old_computed_value = computed_data.calculated_value if computed_data else None
            new_computed_value = compute_field_value(computed_field_id, current_user.entity_id, reporting_date)
            
            if new_computed_value is not None:
                if not computed_data:
                    computed_data = ESGData(
                        entity_id=current_user.entity_id,
                        field_id=computed_field_id,
                        data_point_id=computed_field_id,
                        raw_value=None,
                        calculated_value=new_computed_value,
                        reporting_date=reporting_date
                    )
                    db.session.add(computed_data)
                else:
                    computed_data.calculated_value = new_computed_value
                
                db.session.commit()  # Commit to ensure we have the data_id
                
                # Only create audit log if value changed
                if old_computed_value != new_computed_value:
                    audit_log = ESGDataAuditLog(
                        data_id=computed_data.data_id,
                        change_type='Update',
                        changed_by=current_user.id,
                        old_value=old_computed_value,
                        new_value=new_computed_value
                    )
                    db.session.add(audit_log)
                    db.session.commit()
        
        print("All computations completed and committed successfully")
        
        return jsonify({
            'success': True,
            'message': f'Data successfully saved for {reporting_date.strftime("%B %Y")}. Computed values have been updated.',
            'redirect': url_for('user.dashboard', date=reporting_date.strftime('%Y-%m'))
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error saving data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def compute_field_value(computed_field_id, entity_id, reporting_date):
    """Compute the value for a computed field based on its formula and dependencies."""
    try:
        # Get the computed field
        computed_field = FrameworkDataField.query.get(computed_field_id)
        if not computed_field or not computed_field.is_computed:
            return None
        
        print(f"\nComputing value for field: {computed_field.field_name}")
        
        # Get all variable mappings
        mappings = computed_field.variable_mappings
        
        # Get values for all dependencies
        values = {}
        for mapping in mappings:
            raw_data = ESGData.query.filter_by(
                data_point_id=mapping.raw_field_id,
                entity_id=entity_id,
                reporting_date=reporting_date
            ).first()
            
            if not raw_data or raw_data.raw_value is None:
                print(f"Missing raw value for {mapping.variable_name}")
                return None
            
            # Apply coefficient to the raw value
            try:
                raw_value = float(raw_data.raw_value)
                value = raw_value * mapping.coefficient
                values[mapping.variable_name] = value
                print(f"Variable {mapping.variable_name}: {raw_value} * {mapping.coefficient} = {value}")
            except (ValueError, TypeError):
                print(f"Error converting raw value '{raw_data.raw_value}' to float")
                return None
        
        # Get the formula and substitute values
        formula = computed_field.formula_expression
        print(f"Original formula: {formula}")
        
        # Create a copy of formula for substitution
        computed_formula = formula
        for var_name, value in values.items():
            computed_formula = computed_formula.replace(var_name, str(value))
        
        print(f"Formula with values: {computed_formula}")
        
        # Evaluate the formula
        try:
            result = eval(computed_formula)
            if computed_field.constant_multiplier:
                result *= computed_field.constant_multiplier
            print(f"Result: {result} (after multiplier: {computed_field.constant_multiplier})")
            return result
            
        except Exception as e:
            print(f"Error evaluating formula {computed_formula}: {str(e)}")
            return None
        
    except Exception as e:
        print(f"Error computing field {computed_field_id}: {str(e)}")
        return None

@user_bp.route('/api/historical-data')
@user_required
def get_historical_data():
    try:
        print("Received request for historical data")
        print("Args:", request.args)
        
        data_point_id = request.args.get('dataPoint')
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        
        # Convert string dates to datetime objects
        if start_date:
            start_date = datetime.strptime(start_date + '-01', '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date + '-01', '%Y-%m-%d').date()
            # Set to last day of the month
            end_date = (end_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        print(f"Parsed dates: start={start_date}, end={end_date}")
        
        # Build the query with proper joins
        query = (ESGData.query
                .join(DataPoint, ESGData.data_point_id == DataPoint.id)
                .filter(ESGData.entity_id == current_user.entity_id))
        
        if data_point_id:
            query = query.filter(ESGData.data_point_id == data_point_id)
        if start_date:
            query = query.filter(ESGData.reporting_date >= start_date)
        if end_date:
            query = query.filter(ESGData.reporting_date <= end_date)
        
        # Get the data with DataPoint information
        historical_entries = query.order_by(ESGData.reporting_date).all()
        print(f"Found {len(historical_entries)} entries")
        
        # Format the data for the frontend
        data = [{
            'data_point_id': entry.data_point_id,
            'data_point_name': entry.data_point.name,
            'raw_value': entry.raw_value,
            'calculated_value': entry.calculated_value,
            'reporting_date': entry.reporting_date.strftime('%Y-%m-%d'),
            'updated_at': entry.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        } for entry in historical_entries]
        
        return jsonify({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        print("Error in historical data:", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@user_bp.route('/upload_attachment', methods=['POST'])
@user_required
def upload_attachment():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
            
        file = request.files['file']
        data_id = request.form.get('data_id')
        
        if not file or not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed'}), 400
            
        if not data_id:
            return jsonify({'success': False, 'error': 'No data ID provided'}), 400

        # Check file size - use the file's content length
        file_size = file.content_length if hasattr(file, 'content_length') else 0
        if file_size > current_app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'success': False, 'error': 'File too large'}), 400

        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.entity_id))
        os.makedirs(upload_dir, exist_ok=True)

        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_dir, f"{data_id}_{filename}")
        file.save(file_path)

        # Get actual file size after saving
        file_size = os.path.getsize(file_path)

        # Create attachment record
        attachment = ESGDataAttachment(
            data_id=data_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type or 'application/octet-stream',
            uploaded_by=current_user.id
        )
        
        db.session.add(attachment)
        db.session.commit()

        return jsonify({
            'success': True,
            'attachment': {
                'id': attachment.id,
                'filename': attachment.filename,
                'size': attachment.file_size,
                'uploaded_at': attachment.uploaded_at.isoformat()
            }
        })

    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@user_bp.route('/attachments/<data_id>', methods=['GET'])
@user_required
def get_attachments(data_id):
    try:
        attachments = ESGDataAttachment.query.filter_by(data_id=data_id).all()
        return jsonify({
            'success': True,
            'attachments': [{
                'id': att.id,
                'filename': att.filename,
                'size': att.file_size,
                'uploaded_at': att.uploaded_at.isoformat()
            } for att in attachments]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
        