from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from ..models.esg_data import ESGData, ESGDataAuditLog, ESGDataAttachment
from ..models.data_assignment import DataPointAssignment
from ..extensions import db
from datetime import datetime, UTC, date, timedelta
import os
from werkzeug.utils import secure_filename
from flask import current_app
from ..models.framework import FrameworkDataField, FieldVariableMapping
from ..models.entity import Entity
from ..services.aggregation import aggregation_service
from ..middleware.tenant import require_tenant
from ..decorators.auth import tenant_required_for
from ..utils.unit_conversions import get_unit_options_for_field
import json

user_bp = Blueprint('user', __name__, url_prefix='/user')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@user_bp.route('/dashboard', methods=['GET','POST'])
@login_required
@tenant_required_for('USER')
def dashboard():
    # Note: require_tenant() is now handled by @tenant_required_for decorator

    # Phase 0: Check if user has opted into new interface
    if current_app.config.get('FEATURE_NEW_DATA_ENTRY_ENABLED', False) and current_user.use_new_data_entry:
        current_app.logger.info(f'User {current_user.id} redirected to new v2 dashboard')
        return redirect(url_for('user_v2.dashboard'))

    if not current_user.entity_id:
        flash('No entity assigned to user', 'error')
        return redirect(url_for('auth.login'))
    
    # Get selected date (default to current month)
    selected_date = request.args.get('date')
    try:
        if selected_date:
            # Try to parse as full date first (YYYY-MM-DD)
            if len(selected_date) == 10:  # Full date format
                selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            else:  # Month format (YYYY-MM)
                selected_date = datetime.strptime(selected_date, '%Y-%m').date()
        else:
            # If no date provided, try to find a reasonable default
            # First, check if user has any ESG data entries
            latest_entry = (ESGData.query
                          .filter_by(entity_id=current_user.entity_id)
                          .order_by(ESGData.reporting_date.desc())
                          .first())
            
            if latest_entry:
                # Use the date of the most recent data entry
                selected_date = latest_entry.reporting_date
                current_app.logger.info(f'Using latest data entry date as default: {selected_date}')
            else:
                # Fall back to current month
                selected_date = date.today().replace(day=1)
                current_app.logger.info(f'No data found, using current month: {selected_date}')
    except ValueError:
        selected_date = date.today().replace(day=1)
    
    # Get the user's entity and its parent entities
    user_entity = Entity.get_for_tenant(db.session, current_user.entity_id)
    parent_entities = []
    current_entity = user_entity
    while current_entity and current_entity.parent_id:
        parent_entities.append(current_entity.parent_id)
        current_entity = Entity.get_for_tenant(db.session, current_entity.parent_id)

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

    # ------------------------------------------------------------------
    # Get all data points that have ACTIVE assignments for the user's
    # entity (or its ancestors).  We join through DataPointAssignment
    # instead of the entity_data_point association table because the
    # admin ➜ "Assign Data Points" UI writes to DataPointAssignment.
    # ------------------------------------------------------------------

    # Now use DataPointAssignment as the primary data source
    all_data_points = (DataPointAssignment.query_for_tenant(db.session)
        .filter(
            DataPointAssignment.series_status == 'active',
            DataPointAssignment.entity_id.in_([current_user.entity_id] + parent_entities)
        )
        # Join with FrameworkDataField to get framework metadata
        .join(FrameworkDataField, FrameworkDataField.field_id == DataPointAssignment.field_id)
        .join(Entity, Entity.id == DataPointAssignment.entity_id)
        .add_columns(
            FrameworkDataField.field_name,
            FrameworkDataField.description,
            FrameworkDataField.is_computed,
            FrameworkDataField.formula_expression
        )
        .distinct()
        .all())

    # Organize data points into categories
    raw_input_points = []
    computed_points = []
    raw_dependencies = {}  # Store raw dependencies and their computed fields

    current_app.logger.info(f'Processing {len(all_data_points)} data points for entity {current_user.entity_id}')

    for assignment, field_name, desc, is_computed, formula in all_data_points:
        current_app.logger.info(f'Processing assignment: {field_name} (Assignment ID: {assignment.id}, Field ID: {assignment.field_id}, is_computed: {is_computed})')
        
        # NEW: Gather dimension metadata for this field
        dimensions = []
        for fd in assignment.field.field_dimensions:
            dim = fd.dimension
            if not dim:
                continue
            dimensions.append({
                'dimension_id': dim.dimension_id,
                'name': dim.name,
                'is_required': fd.is_required,
                'values': [
                    {
                        'value_id': dv.value_id,
                        'value': dv.value,
                        'display_name': dv.display_name,
                        'effective_display_name': dv.effective_display_name
                    } for dv in dim.get_ordered_values()
                ]
            })
        
        point_data = {
            'id': assignment.field_id,  # Use field_id as the data point ID
            'assignment_id': assignment.id,  # Keep assignment ID for reference
            'name': field_name,
            'value_type': 'numeric' if assignment.field.value_type == 'NUMBER' else assignment.field.value_type.lower(),
            'unit_category': assignment.field.unit_category,
            'default_unit': assignment.field.default_unit,
            'unit_options': get_unit_options_for_field(assignment.field) if assignment.field.unit_category else [],
            'unit': assignment.effective_unit,
            'description': desc,
            'is_computed': is_computed,
            'formula': formula,
            'status': get_data_point_status(assignment.field_id, current_user.entity_id, selected_date),
            'dependencies': [],
            'dimensions': dimensions  # <--- include dimensions metadata
        }

        if assignment.field_id in raw_fields:  # This is a raw dependency
            current_app.logger.info(f'  -> Added as raw dependency: {field_name}')
            raw_dependencies[assignment.field_id] = {
                'data': point_data,
                'computed_fields': raw_fields[assignment.field_id]['computed_fields'],
                'variable_names': raw_fields[assignment.field_id]['variable_names']
            }
        elif is_computed:  # This is a computed field - use is_computed flag directly
            current_app.logger.info(f'  -> Added as computed field: {field_name}')
            # Use the field_id directly for dependencies
            deps = (FieldVariableMapping.query
                   .filter_by(computed_field_id=assignment.field_id)
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
            current_app.logger.info(f'  -> Added as raw input: {field_name}')
            raw_input_points.append(point_data)

    current_app.logger.info(f'Final counts: {len(raw_input_points)} raw, {len(computed_points)} computed, {len(raw_dependencies)} dependencies')

    # Get ESG data entries - LOAD ALL DATES, not just selected date
    # This ensures frontend has data for all dates when switching
    all_esg_data_entries = ESGData.query.filter_by(
        entity_id=current_user.entity_id
    ).all()

    # Add debug logging to understand data loading
    current_app.logger.info(f'Dashboard loading for user {current_user.id} (entity {current_user.entity_id})')
    current_app.logger.info(f'Selected date: {selected_date}')
    current_app.logger.info(f'Found {len(all_esg_data_entries)} total ESG data entries for this entity')
    
    # Group ESG data by date for efficient lookup
    esg_data_by_date = {}
    for entry in all_esg_data_entries:
        date_key = entry.reporting_date.strftime('%Y-%m-%d')
        if date_key not in esg_data_by_date:
            esg_data_by_date[date_key] = {}
        
        esg_data_by_date[date_key][entry.field_id] = {
            'raw_value': entry.raw_value,
            'calculated_value': entry.calculated_value,
            'entity_id': entry.entity_id,
            'data_id': entry.data_id
        }
    
    # For backward compatibility, also create entity_data_entries for the selected date
    entity_data_entries = esg_data_by_date.get(selected_date.strftime('%Y-%m-%d'), {})
    
    current_app.logger.info(f'ESG data organized by dates: {list(esg_data_by_date.keys())}')
    current_app.logger.info(f'Entity data entries for {selected_date}: {len(entity_data_entries)} entries')
    for dp_id, data in entity_data_entries.items():
        current_app.logger.info(f'  - {dp_id}: raw={data["raw_value"]}, calc={data["calculated_value"]}')

    # Convert sets to lists for JSON serialization
    serializable_raw_dependencies = {}
    for field_id, dep_data in raw_dependencies.items():
        serializable_raw_dependencies[field_id] = {
            'data': dep_data['data'],
            'computed_fields': list(dep_data['computed_fields']),  # Convert set to list
            'variable_names': dep_data['variable_names']
        }

    # Return user context for the frontend
    user_context = {
        'username': current_user.name,
    }

    return render_template('user/dashboard.html',
                         raw_input_points=raw_input_points,
                         computed_points=computed_points,
                         raw_dependencies=serializable_raw_dependencies,
                         entity_data_entries=entity_data_entries,
                         esg_data_by_date=esg_data_by_date,
                         selected_date=selected_date,
                         user_context=user_context)

def get_data_point_status(field_id, entity_id, reporting_date):
    """Determine the status of a data point (field)."""
    entry = ESGData.query.filter_by(
        field_id=field_id,
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
@login_required
@tenant_required_for('USER')
def submit_data():
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    try:
        reporting_date = request.form.get('reporting_date')
        if not reporting_date:
            return jsonify({
                'success': False,
                'error': 'Reporting date is required'
            }), 400
        
        reporting_date = datetime.strptime(reporting_date, '%Y-%m-%d').date()
        
        # Get all field IDs being submitted for validation
        field_ids = []
        for key, value in request.form.items():
            if key.startswith('field_') and value and value.strip():
                field_id = key.replace('field_', '')
                field_ids.append(field_id)
        
        # Validate reporting date against assignment configurations
        invalid_assignments = []
        for field_id in field_ids:
            assignment = DataPointAssignment.query.filter_by(
                field_id=field_id,
                entity_id=current_user.entity_id,
                is_active=True
            ).first()
            
            if assignment and not assignment.is_valid_reporting_date(reporting_date):
                framework_field = FrameworkDataField.query.get(field_id)
                invalid_assignments.append({
                    'name': framework_field.field_name if framework_field else 'Unknown',
                    'frequency': assignment.frequency,
                    'fy_display': assignment.get_fy_display()
                })
        
        if invalid_assignments:
            error_msg = f"Selected date {reporting_date.strftime('%Y-%m-%d')} is not valid for the following data points: "
            error_msg += ", ".join([f"{ia['name']} ({ia['frequency']} - {ia['fy_display']})" for ia in invalid_assignments])
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        form_data = request.form
        
        affected_computed_fields = set()
        
        # First, create/update all ESG data entries
        for key, value in form_data.items():
            if key.startswith('field_'):
                field_id = key.replace('field_', '')
                
                # Skip empty values
                if not value or not value.strip():
                    continue
                
                # Get assignment to validate permissions and get field info
                assignment = DataPointAssignment.query.filter_by(
                    field_id=field_id,
                    entity_id=current_user.entity_id,
                    is_active=True
                ).first()
                
                if not assignment:
                    continue

                # Get the framework field
                framework_field = FrameworkDataField.query.get(field_id)
                if not framework_field:
                    continue

                # Skip if this is a computed field
                if framework_field.is_computed:
                    continue

                # Get unit information from form
                unit_key = f'unit_{field_id}'
                selected_unit = form_data.get(unit_key, '').strip()
                
                # NEW: Get dimension information from form
                dimension_key = f'field_{field_id}_dimensions'
                dimension_data_json = form_data.get(dimension_key, '').strip()
                dimension_values = {}
                
                if dimension_data_json:
                    try:
                        dimension_values = json.loads(dimension_data_json)
                        current_app.logger.info(f'Form Submit - Parsed dimensions for field {field_id}: {dimension_values}')
                    except (json.JSONDecodeError, TypeError) as e:
                        current_app.logger.warning(f'Form Submit - Invalid dimension JSON for field {field_id}: {e}')
                        dimension_values = {}
                
                # Validate required dimensions
                field_dimensions = framework_field.field_dimensions
                for fd in field_dimensions:
                    if fd.is_required:
                        dim_name = fd.dimension.name.lower()
                        if dim_name not in dimension_values or not dimension_values[dim_name]:
                            return jsonify({
                                'success': False,
                                'error': f'Required dimension "{fd.dimension.name}" is missing for field "{framework_field.field_name}"'
                            }), 400
                
                # Find or create ESGData entry
                esg_data = ESGData.query.filter_by(
                    field_id=field_id,
                    entity_id=current_user.entity_id,
                    reporting_date=reporting_date
                ).first()
                
                try:
                    # Convert value based on field value type
                    if framework_field.value_type == 'NUMBER':
                        processed_value = float(value)
                    else:
                        processed_value = str(value)
                except ValueError:
                    continue

                old_value = None
                if esg_data:
                    old_value = esg_data.raw_value
                    esg_data.raw_value = processed_value
                    # Store unit information if provided (Phase 4.1)
                    if selected_unit:
                        esg_data.unit = selected_unit
                    # NEW: Store dimension values
                    if dimension_values:
                        esg_data.dimension_values = dimension_values
                    current_app.logger.info(f'Form Submit - Updated existing ESGData {esg_data.data_id}: {old_value} -> {processed_value} (unit: {selected_unit})')
                else:
                    esg_data = ESGData(
                        entity_id=current_user.entity_id,
                        field_id=field_id,
                        raw_value=processed_value,
                        reporting_date=reporting_date,
                        unit=selected_unit if selected_unit else None,
                        dimension_values=dimension_values if dimension_values else None
                    )
                    db.session.add(esg_data)
                    current_app.logger.info(f'Form Submit - Created new ESGData for field {field_id}: {processed_value} (unit: {selected_unit})')
                
                db.session.commit()
                current_app.logger.info(f'Form Submit - Database commit successful for field {field_id}')
                
                # Create audit log entry
                if old_value != processed_value:
                    audit_log = ESGDataAuditLog(
                        data_id=esg_data.data_id,
                        change_type='Update',
                        changed_by=current_user.id,
                        old_value=old_value,
                        new_value=processed_value
                    )
                    db.session.add(audit_log)
                    db.session.commit()
                    current_app.logger.info(f'Form Submit - Audit log created for field {field_id}')
                
                # Find computed fields that depend on this raw field
                dependent_computed_fields = (FieldVariableMapping.query
                    .filter_by(raw_field_id=field_id)
                    .all())
                
                for dep in dependent_computed_fields:
                    affected_computed_fields.add(dep.computed_field_id)
        
        # Now process all affected computed fields using aggregation service
        if affected_computed_fields:
            successful_computations = 0
            skipped_computations = 0
            computation_messages = []
            
            for computed_field_id in affected_computed_fields:
                try:
                    # Use aggregation service to compute the value
                    computed_value, status_message = aggregation_service.compute_field_value_if_ready(
                        computed_field_id,
                        current_user.entity_id,
                        reporting_date,
                        force_compute=False,
                        minimum_data_threshold=0.8  # Allow computation with 80% of expected data
                    )
                    
                    if computed_value is not None:
                        # Save the computed value
                        computed_data = ESGData.query.filter_by(
                            field_id=computed_field_id,
                            entity_id=current_user.entity_id,
                            reporting_date=reporting_date
                        ).first()
                        
                        if not computed_data:
                            computed_data = ESGData(
                                entity_id=current_user.entity_id,
                                field_id=computed_field_id,
                                raw_value=None,
                                calculated_value=computed_value,
                                reporting_date=reporting_date
                            )
                            db.session.add(computed_data)
                        else:
                            computed_data.calculated_value = computed_value
                        
                        successful_computations += 1
                        
                        # Get field name for logging
                        framework_field = FrameworkDataField.query.get(computed_field_id)
                        field_name = framework_field.field_name if framework_field else computed_field_id
                        current_app.logger.info(f'  ✅ Computed {field_name}: {computed_value}')
                    else:
                        skipped_computations += 1
                        # Get field name for logging
                        framework_field = FrameworkDataField.query.get(computed_field_id)
                        field_name = framework_field.field_name if framework_field else computed_field_id
                        computation_messages.append(f"Skipped {field_name}: {status_message}")
                        current_app.logger.info(f'  ⚠️ Skipped {field_name}: {status_message}')
                        
                except Exception as e:
                    skipped_computations += 1
                    # Get field name for logging
                    framework_field = FrameworkDataField.query.get(computed_field_id)
                    field_name = framework_field.field_name if framework_field else computed_field_id
                    computation_messages.append(f"Error computing {field_name}: {str(e)}")
                    current_app.logger.error(f'Error computing {field_name}: {e}')
            
            # Commit all computed field changes
            db.session.commit()
            
            # Prepare response message
            response_message = f'Data successfully saved for {reporting_date.strftime("%B %Y")}.'
            
            if successful_computations > 0:
                response_message += f' {successful_computations} computed field(s) updated.'
            
            if skipped_computations > 0:
                response_message += f' {skipped_computations} computed field(s) skipped (insufficient data).'
        else:
            # No computed fields affected, just basic success message
            response_message = f'Data successfully saved for {reporting_date.strftime("%B %Y")}.'
        
        return jsonify({
            'success': True,
            'message': response_message,
            'redirect': url_for('user.dashboard', date=reporting_date.strftime('%Y-%m-%d'))
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def compute_field_value(computed_field_id, entity_id, reporting_date):
    """
    Compute the value for a computed field based on its formula and dependencies.
    Now uses the intelligent aggregation service to handle different frequencies.
    """
    try:
        return aggregation_service.compute_field_value(
            computed_field_id, 
            entity_id, 
            reporting_date
        )
    except Exception as e:
        current_app.logger.error(f'Error computing field value: {str(e)}')
        return None

def compute_multiple_fields_bulk(field_entity_date_tuples):
    """
    Compute multiple computed fields efficiently using bulk operations.
    
    Args:
        field_entity_date_tuples: List of (field_id, entity_id, reporting_date) tuples
        
    Returns:
        Dict mapping (field_id, entity_id, reporting_date) to computed value
    """
    try:
        return aggregation_service.compute_multiple_fields(field_entity_date_tuples)
    except Exception as e:
        current_app.logger.error(f'Error in bulk field computation: {str(e)}')
        return {}

@user_bp.route('/api/historical-data')
@login_required
@tenant_required_for('USER')
def get_historical_data():
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    field_id = request.args.get('field_id')
    if not field_id:
        return jsonify({'error': 'Field ID is required'}), 400
    
    # Verify field exists and assignment exists for user's entity
    assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
        field_id=field_id,
        entity_id=current_user.entity_id,
        is_active=True
    ).first()
    
    if not assignment:
        return jsonify({'error': 'Field not found or not accessible'}), 404
    
    # Get historical entries for this field and entity
    historical_entries = ESGData.query_for_tenant(db.session).filter(
        ESGData.field_id == field_id,
        ESGData.entity_id == current_user.entity_id,
        ESGData.raw_value.isnot(None)
    ).order_by(ESGData.reporting_date.desc()).all()

    # Organize data by reporting date
    data_by_date = {}
    for entry in historical_entries:
        date_key = entry.reporting_date.strftime('%Y-%m')
        if date_key not in data_by_date:
            data_by_date[date_key] = {}
        
        # Use calculated_value if available (for computed fields), otherwise raw_value
        value = entry.calculated_value if entry.calculated_value is not None else entry.raw_value
        
        # Get field name from framework data field
        field = FrameworkDataField.query.get(entry.field_id)
        field_name = field.field_name if field else 'Unknown'
        
        data_by_date[date_key][entry.field_id] = {
            'value': value,
            'field_name': field_name
        }
    
    return jsonify({
        'success': True,
        'data': data_by_date
    })

@user_bp.route('/upload_attachment', methods=['POST'])
@login_required
@tenant_required_for('USER')
def upload_attachment():
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    data_id = request.form.get('data_id')
    status = request.form.get('status', 'no_data')
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not data_id:
        return jsonify({'success': False, 'error': 'No data ID provided'}), 400
    
    # Check if we have a data_id (ESGData entry) or just a data_point_id
    if status == 'no_data':
        # This means we only have a data_point_id, not an ESGData entry
        return jsonify({
            'success': False, 
            'error': 'Please save data for this data point first before uploading attachments. You need to enter a value and save the form.'
        }), 400
    
    # For existing ESGData entries, we need to find the actual data_id
    # The data_id passed might be the data_point_id, so let's check
    esg_data = ESGData.get_for_tenant(db.session, data_id)
    
    if not esg_data:
        return jsonify({
            'success': False, 
            'error': 'No data found for this data point. Please save data first before uploading attachments.'
        }), 400
    
    actual_data_id = esg_data.data_id
    
    if file and allowed_file(file.filename):
        # Check file size - use the file's content length
        file_size = file.content_length if hasattr(file, 'content_length') else 0
        if file_size > current_app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'success': False, 'error': 'File too large'}), 400

        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.entity_id))
        os.makedirs(upload_dir, exist_ok=True)

        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_dir, f"{actual_data_id}_{filename}")
        file.save(file_path)

        # Get actual file size after saving
        file_size = os.path.getsize(file_path)

        # Create attachment record
        attachment = ESGDataAttachment(
            data_id=actual_data_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type or 'application/octet-stream',
            uploaded_by=current_user.id
        )
        
        db.session.add(attachment)
        db.session.commit()

        return jsonify({'success': True, 'message': 'File uploaded successfully'})
    else:
        return jsonify({'success': False, 'error': 'File type not allowed'}), 400

@user_bp.route('/attachments/<data_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_attachments(data_id):
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    # Verify ESG data belongs to current tenant
    esg_data = ESGData.get_for_tenant(db.session, data_id)
    if not esg_data:
        return jsonify({'error': 'ESG data not found or not accessible'}), 404
    
    attachments = ESGDataAttachment.query.filter_by(data_id=data_id).all()
    return jsonify({
        'attachments': [{
            'id': att.id,
            'filename': att.filename,
            'file_size': att.file_size,
            'uploaded_at': att.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
        } for att in attachments]
    })

@user_bp.route('/api/valid-dates/<field_id>')
@login_required
@tenant_required_for('USER')
def get_valid_dates_for_user(field_id):
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    # Get assignment for this field and entity
    assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
        field_id=field_id,
        entity_id=current_user.entity_id,
        is_active=True
    ).first()
    
    if not assignment:
        return jsonify({'error': 'No assignment found'}), 404
    
    # Get the user's entity and validate tenant access
    user_entity = Entity.get_for_tenant(db.session, current_user.entity_id)
    if not user_entity:
        return jsonify({'error': 'Entity not found or not accessible'}), 404

    valid_dates = assignment.get_valid_reporting_dates()
    
    return jsonify({
        'valid_dates': [date.isoformat() for date in valid_dates],
        'frequency': assignment.frequency,
        'fy_display': assignment.get_fy_display(),
        'fy_start_month': assignment.fy_start_month,
        'fy_start_year': assignment.fy_start_year,
        'fy_end_year': assignment.fy_end_year
    })

@user_bp.route('/api/validate-date', methods=['POST'])
@login_required
@tenant_required_for('USER')
def validate_reporting_date():
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    data = request.get_json()
    field_id = data.get('field_id')
    reporting_date_str = data.get('reporting_date')
    
    if not field_id or not reporting_date_str:
        return jsonify({'valid': False, 'error': 'Missing required parameters'}), 400
    
    try:
        reporting_date = datetime.strptime(reporting_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'valid': False, 'error': 'Invalid date format'}), 400
    
    # Get assignment for this field and entity
    assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
        field_id=field_id,
        entity_id=current_user.entity_id,
        is_active=True
    ).first()
    
    if not assignment:
        return jsonify({'valid': False, 'error': 'No assignment found'}), 404
    
    # Get the user's entity and validate tenant access
    user_entity = Entity.get_for_tenant(db.session, current_user.entity_id)
    if not user_entity:
        return jsonify({'error': 'Entity not found or not accessible'}), 404

    if assignment and not assignment.is_valid_reporting_date(reporting_date):
        return jsonify({
            'valid': False,
            'message': 'Selected date is not valid for this data point',
            'valid_dates': [d.isoformat() for d in assignment.get_valid_reporting_dates()]
        })
    
    return jsonify({'valid': True})

@user_bp.route('/api/assignment-configurations')
@login_required
@tenant_required_for('USER')
def get_user_assignment_configurations():
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    # Get the user's entity and validate tenant access
    user_entity = Entity.get_for_tenant(db.session, current_user.entity_id)
    if not user_entity:
        return jsonify({'error': 'Entity not found or not accessible'}), 404

    # Get active assignments for user's entity
    assignments = DataPointAssignment.query_for_tenant(db.session).filter(
        DataPointAssignment.entity_id == current_user.entity_id,
        DataPointAssignment.series_status == 'active'
    ).all()
    
    if not assignments:
        return jsonify({
            'configurations': {},
            'all_valid_dates': [],
            'date_to_data_points': {}
        })
    
    # Build response data
    configurations = {}
    all_valid_dates = set()
    date_to_data_points = {}
    
    for assignment in assignments:
        field = assignment.field  # Use the field relationship instead of data_point
        valid_dates = assignment.get_valid_reporting_dates()
        
        configurations[str(assignment.field_id)] = {
            'field_id': assignment.field_id,
            'data_point_name': field.field_name,  # Use field_name instead of name
            'frequency': assignment.frequency,
            'fy_display': assignment.get_fy_display(),
            'fy_start_month': assignment.fy_start_month,
            'fy_start_year': assignment.fy_start_year,
            'fy_end_year': assignment.fy_end_year,
            'valid_dates': [date.isoformat() for date in valid_dates]
        }
        
        # Add to all valid dates
        for date in valid_dates:
            date_str = date.isoformat()
            all_valid_dates.add(date_str)
            
            if date_str not in date_to_data_points:
                date_to_data_points[date_str] = []
            
            date_to_data_points[date_str].append({
                'id': assignment.field_id,
                'name': field.field_name,  # Use field_name instead of name
                'frequency': assignment.frequency,
                'fy_display': assignment.get_fy_display()
            })
    
    return jsonify({
        'configurations': configurations,
        'all_valid_dates': sorted(list(all_valid_dates)),
        'date_to_data_points': date_to_data_points
    })

@user_bp.route('/upload-csv', methods=['POST'])
@login_required
@tenant_required_for('USER')
def upload_csv():
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    if 'csv_file' not in request.files:
        return jsonify({'success': False, 'error': 'No CSV file provided'}), 400
    
    file = request.files['csv_file']
    reporting_date_str = request.form.get('reporting_date')
    
    if not file or not file.filename:
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not reporting_date_str:
        return jsonify({'success': False, 'error': 'Reporting date is required'}), 400
    
    # Validate file type
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'success': False, 'error': 'File must be a CSV file'}), 400
    
    reporting_date = datetime.strptime(reporting_date_str, '%Y-%m-%d').date()
    
    # Read and parse CSV
    import csv
    import io
    
    # Read file content
    file_content = file.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(file_content))
    
    # Validate CSV headers - frequency is now optional
    required_headers = ['Reporting Date', 'Data Point Name', 'Value']
    optional_headers = ['Frequency']
    
    if not all(header in csv_reader.fieldnames for header in required_headers):
        return jsonify({
            'success': False, 
            'error': f'CSV must have columns: {", ".join(required_headers)}. Optional: {", ".join(optional_headers)}. Found: {", ".join(csv_reader.fieldnames or [])}'
        }), 400
    
    # Check if frequency column is present
    has_frequency_column = 'Frequency' in (csv_reader.fieldnames or [])
    
    # Process CSV rows
    processed_count = 0
    errors = []
    warnings = []
    processed_dates = set()
    
    # Add debugging
    current_app.logger.info(f'Starting CSV processing for user {current_user.id} (entity {current_user.entity_id})')
    current_app.logger.info(f'CSV has frequency column: {has_frequency_column}')
    
    for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header
        reporting_date_str = row.get('Reporting Date', '').strip()
        data_point_name = row.get('Data Point Name', '').strip()
        value = row.get('Value', '').strip()
        frequency = row.get('Frequency', '').strip() if has_frequency_column else ''
        
        # Clean up the reporting date string (remove quotes and leading apostrophe if present)
        if reporting_date_str.startswith('"') and reporting_date_str.endswith('"'):
            reporting_date_str = reporting_date_str[1:-1]
        elif reporting_date_str.startswith("'"):
            reporting_date_str = reporting_date_str[1:]
        
        # Clean up data point name (remove quotes if present)
        if data_point_name.startswith('"') and data_point_name.endswith('"'):
            data_point_name = data_point_name[1:-1]
        
        if not reporting_date_str or not data_point_name or not value:
            if reporting_date_str or data_point_name or value:  # Only warn if partially filled
                errors.append(f'Row {row_num}: Missing required data (Date: "{reporting_date_str}", Name: "{data_point_name}", Value: "{value}")')
            continue
        
        try:
            # Parse reporting date with improved handling
            row_reporting_date = datetime.strptime(reporting_date_str, '%Y-%m-%d').date()
            processed_dates.add(row_reporting_date)
        except ValueError:
            # Try alternative date formats
            try:
                # Try MM/DD/YYYY format (common Excel format)
                row_reporting_date = datetime.strptime(reporting_date_str, '%m/%d/%Y').date()
                processed_dates.add(row_reporting_date)
            except ValueError:
                try:
                    # Try DD/MM/YYYY format
                    row_reporting_date = datetime.strptime(reporting_date_str, '%d/%m/%Y').date()
                    processed_dates.add(row_reporting_date)
                except ValueError:
                    errors.append(f'Row {row_num}: Invalid date format "{reporting_date_str}". Use YYYY-MM-DD format or ensure date is properly formatted.')
                    continue
        
        # Get data points that are due for this specific date
        # First, try a simpler approach - get all data points assigned to this entity
        # and check if they're valid for this date
        user_entity = Entity.get_for_tenant(db.session, current_user.entity_id)
        available_data_points = []
        
        # Get all data points assigned to user's entity (including parent entities)
        entity_ids = [current_user.entity_id]
        current_entity = user_entity
        while current_entity and current_entity.parent_id:
            entity_ids.append(current_entity.parent_id)
            current_entity = Entity.get_for_tenant(db.session, current_entity.parent_id)
        
        # Get all assignments for these entities 
        all_assignments = (DataPointAssignment.query_for_tenant(db.session)
                         .filter(DataPointAssignment.entity_id.in_(entity_ids))
                         .filter(DataPointAssignment.series_status == 'active')
                         .all())
        
        # Build a mapping of field names to assignments (with frequency validation if provided)
        valid_assignments = {}
        for assignment in all_assignments:
            # Check if assignment is valid for this date
            if assignment.is_valid_reporting_date(row_reporting_date):
                # If frequency is provided in CSV, validate it matches (case-insensitive)
                if has_frequency_column and frequency:
                    assignment_frequency = assignment.frequency.lower().strip()
                    csv_frequency = frequency.lower().strip()
                    
                    if assignment_frequency != csv_frequency:
                        warnings.append(f'Row {row_num}: Frequency mismatch for "{data_point_name}" - Expected: {assignment.frequency}, Found: {frequency}. Processing anyway.')
                
                # Get field name from FrameworkDataField
                framework_field = FrameworkDataField.query.get(assignment.field_id)
                if framework_field:
                    field_name = framework_field.field_name
                    
                    # Use multiple variations of the name for matching
                    name_variations = [
                        field_name.lower().strip(),
                        field_name.strip(),  # Original case
                        field_name.replace(' ', '').lower(),  # No spaces
                        field_name.replace('_', ' ').lower().strip(),  # Underscores to spaces
                        field_name.replace('-', ' ').lower().strip(),  # Hyphens to spaces
                    ]
                    for name_var in name_variations:
                        valid_assignments[name_var] = assignment
        
        # Find matching assignment (try multiple variations)
        search_variations = [
            data_point_name.lower().strip(),
            data_point_name.strip(),  # Original case
            data_point_name.replace(' ', '').lower(),  # No spaces
            data_point_name.replace('_', ' ').lower().strip(),  # Underscores to spaces
            data_point_name.replace('-', ' ').lower().strip(),  # Hyphens to spaces
        ]
        
        assignment = None
        for search_var in search_variations:
            assignment = valid_assignments.get(search_var)
            if assignment:
                break
        
        if not assignment:
            # Provide more detailed error message
            available_names = []
            for assign in valid_assignments.values():
                framework_field = FrameworkDataField.query.get(assign.field_id)
                if framework_field:
                    available_names.append(framework_field.field_name)
            available_names = list(set(available_names))
            errors.append(f'Row {row_num}: Field "{data_point_name}" not found. Available fields for {reporting_date_str}: {", ".join(available_names[:5])}{"..." if len(available_names) > 5 else ""}')
            current_app.logger.warning(f'CSV Upload - Field not found: "{data_point_name}" for user {current_user.id}')
            continue
        
        # Add debug log for successful match
        current_app.logger.info(f'CSV Upload - Found field: "{data_point_name}" -> {assignment.field_id} for date {row_reporting_date}')
        
        try:
            # Convert value based on assignment value type
            if assignment.value_type == 'numeric':
                processed_value = float(value)
            else:
                processed_value = str(value)
            
            # Find or create ESGData entry
            esg_data = ESGData.query_for_tenant(db.session).filter_by(
                field_id=assignment.field_id,
                entity_id=current_user.entity_id,
                reporting_date=row_reporting_date
            ).first()
            
            old_value = None
            if esg_data:
                old_value = esg_data.raw_value
                esg_data.raw_value = processed_value
                current_app.logger.info(f'CSV Upload - Updated existing ESGData {esg_data.data_id}: {old_value} -> {processed_value}')
            else:
                esg_data = ESGData(
                    entity_id=current_user.entity_id,
                    field_id=assignment.field_id,
                    raw_value=processed_value,
                    reporting_date=row_reporting_date
                )
                db.session.add(esg_data)
                current_app.logger.info(f'CSV Upload - Created new ESGData for field {assignment.field_id}: {processed_value}')
            
            db.session.commit()
            current_app.logger.info(f'CSV Upload - Database commit successful for field {assignment.field_id}')
            
            # Create audit log entry
            if old_value != processed_value:
                audit_log = ESGDataAuditLog(
                    data_id=esg_data.data_id,
                    change_type='CSV Upload',
                    changed_by=current_user.id,
                    old_value=old_value,
                    new_value=processed_value
                )
                db.session.add(audit_log)
                db.session.commit()
                current_app.logger.info(f'CSV Upload - Audit log created for field {assignment.field_id}')
            
            processed_count += 1
            
        except ValueError as e:
            errors.append(f'Row {row_num}: Invalid value "{value}" for {data_point_name} ({assignment.value_type})')
        except Exception as e:
            errors.append(f'Row {row_num}: Error processing {data_point_name}: {str(e)}')
    
    # Process computed fields for all affected dates using bulk computation
    all_affected_computations = []
    
    for processed_date in processed_dates:
        affected_computed_fields = set()
        
        # Get all data points that were updated for this date
        updated_data_points = ESGData.query_for_tenant(db.session).filter_by(
            entity_id=current_user.entity_id,
            reporting_date=processed_date
        ).all()
        
        for esg_data in updated_data_points:
            dependent_computed_fields = (FieldVariableMapping.query
                .filter_by(raw_field_id=esg_data.field_id)
                .all())
            
            for dep in dependent_computed_fields:
                affected_computed_fields.add(dep.computed_field_id)
        
        # Add all affected computations to the bulk list
        for computed_field_id in affected_computed_fields:
            all_affected_computations.append((computed_field_id, current_user.entity_id, processed_date))
    
    # Perform bulk computation for all affected computed fields across all dates
    if all_affected_computations:
        computed_results = compute_multiple_fields_bulk(all_affected_computations)
        
        # Update computed fields with results
        for (computed_field_id, entity_id, processed_date), computed_value in computed_results.items():
            if computed_value is not None:
                computed_data = ESGData.query_for_tenant(db.session).filter_by(
                    field_id=computed_field_id,
                    entity_id=current_user.entity_id,
                    reporting_date=processed_date
                ).first()
                
                if not computed_data:
                    computed_data = ESGData(
                        entity_id=current_user.entity_id,
                        field_id=computed_field_id,
                        raw_value=None,
                        calculated_value=computed_value,
                        reporting_date=processed_date
                    )
                    db.session.add(computed_data)
                else:
                    computed_data.calculated_value = computed_value
                
                db.session.commit()
    
    # Prepare response
    response_data = {
        'success': True,
        'processed_count': processed_count,
        'message': f'Successfully processed {processed_count} data points across {len(processed_dates)} date(s)'
    }
    
    all_issues = errors + warnings
    if all_issues:
        response_data['warnings'] = all_issues[:15]  # Limit to first 15 issues
        if len(all_issues) > 15:
            response_data['warnings'].append(f'... and {len(all_issues) - 15} more issues')
        response_data['message'] += f' with {len(errors)} errors and {len(warnings)} warnings'
    
    # Add final debug log
    current_app.logger.info(f'CSV Upload completed - Processed: {processed_count}, Errors: {len(errors)}, Warnings: {len(warnings)}, Dates: {len(processed_dates)}')
    current_app.logger.info(f'CSV Upload response: {response_data}')
    
    return jsonify(response_data)

@user_bp.route('/debug/esg-data')
@login_required
@tenant_required_for('USER')
def debug_esg_data():
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    all_entries = ESGData.query_for_tenant(db.session).filter_by(entity_id=current_user.entity_id).all()
    
    entries_data = []
    for entry in all_entries:
        # Get field name from FrameworkDataField
        field = FrameworkDataField.query.get(entry.field_id)
        field_name = field.field_name if field else 'Unknown'
        
        entries_data.append({
            'data_id': entry.data_id,
            'field_id': entry.field_id,
            'field_name': field_name,
            'raw_value': entry.raw_value,
            'calculated_value': entry.calculated_value,
            'reporting_date': entry.reporting_date.strftime('%Y-%m-%d'),
            'created_at': entry.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': entry.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({
        'entity_id': current_user.entity_id,
        'total_entries': len(entries_data),
        'entries': entries_data
    })

@user_bp.route('/api/field-attachments/<field_id>')
@login_required
@tenant_required_for('USER')
def get_field_attachments(field_id):
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    # Verify field assignment exists for current user's entity
    assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
        field_id=field_id,
        entity_id=current_user.entity_id,
        is_active=True
    ).first()
    
    if not assignment:
        return jsonify({'error': 'Field not found or not accessible'}), 404
    
    # Get ESG data for this field and entity
    esg_data = ESGData.query_for_tenant(db.session).filter_by(
        field_id=field_id,
        entity_id=current_user.entity_id
    ).first()
    
    if not esg_data:
        return jsonify({'attachments': []})
    
    # Get attachments for this ESGData entry
    attachments = ESGDataAttachment.query.filter_by(data_id=esg_data.data_id).all()
    
    return jsonify({
        'attachments': [{
            'id': att.id,
            'filename': att.filename,
            'file_size': att.file_size,
            'mime_type': att.mime_type,
            'uploaded_at': att.uploaded_at.isoformat()
        } for att in attachments]
    })

@user_bp.route('/download-attachment/<attachment_id>')
@login_required
@tenant_required_for('USER')
def download_attachment(attachment_id):
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    attachment = ESGDataAttachment.query.get(attachment_id)
    if not attachment:
        flash('Attachment not found', 'error')
        return redirect(url_for('user.dashboard'))
    
    # Verify attachment belongs to tenant's ESG data
    esg_data = ESGData.get_for_tenant(db.session, attachment.data_id)
    if not esg_data:
        flash('Attachment not accessible', 'error')
        return redirect(url_for('user.dashboard'))

    return send_file(
        attachment.file_path,
        as_attachment=True,
        download_name=attachment.filename,
        mimetype=attachment.mime_type
    )

@user_bp.route('/delete-attachment/<attachment_id>', methods=['DELETE'])
@login_required
@tenant_required_for('USER')
def delete_attachment(attachment_id):
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    attachment = ESGDataAttachment.query.get(attachment_id)
    if not attachment:
        return jsonify({'success': False, 'error': 'Attachment not found'}), 404
    
    # Verify attachment belongs to tenant's ESG data
    esg_data = ESGData.get_for_tenant(db.session, attachment.data_id)
    if not esg_data:
        return jsonify({'success': False, 'error': 'Attachment not accessible'}), 403

    # Delete the physical file
    try:
        if os.path.exists(attachment.file_path):
            os.remove(attachment.file_path)
    except Exception as e:
        current_app.logger.warning(f'Could not delete physical file {attachment.file_path}: {str(e)}')
    
    # Delete the database record
    db.session.delete(attachment)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Attachment deleted successfully'})

@user_bp.route('/api/field-aggregation-details/<computed_field_id>')
@login_required
@tenant_required_for('USER')
def get_field_aggregation_details(computed_field_id):
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    # Verify computed field assignment exists for current user's entity
    assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
        field_id=computed_field_id,
        entity_id=current_user.entity_id,
        is_active=True
    ).first()
    
    if not assignment:
        return jsonify({'error': 'Computed field not found or not accessible'}), 404
    
    reporting_date_str = request.args.get('reporting_date')
    if not reporting_date_str:
        return jsonify({'error': 'Reporting date is required'}), 400
    
    try:
        reporting_date = datetime.strptime(reporting_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Get computed data for this field, entity, and date
    computed_data = ESGData.query_for_tenant(db.session).filter_by(
        field_id=computed_field_id,
        entity_id=current_user.entity_id,
        reporting_date=reporting_date
    ).first()

    if not computed_data:
        return jsonify({'error': 'No computed data found for this field'}), 404

    # Get aggregation summary using the service
    summary = aggregation_service.get_aggregation_summary(
        computed_field_id,
        current_user.entity_id,
        reporting_date
    )

    if not summary:
        return jsonify({'error': 'No aggregation information available for this field'}), 404

    # Add the computed value
    current_value = computed_data.calculated_value if computed_data else None

    return jsonify({
        'success': True,
        'field_id': computed_field_id,
        'entity_id': current_user.entity_id,
        'current_value': current_value,
        'aggregation_details': summary
    })

@user_bp.route('/api/compute-field-on-demand', methods=['POST'])
@login_required
@tenant_required_for('USER')
def compute_field_on_demand():
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    data = request.get_json()
    computed_field_id = data.get('computed_field_id')
    reporting_date_str = data.get('reporting_date')
    force_compute = data.get('force_compute', False)
    
    if not computed_field_id or not reporting_date_str:
        return jsonify({
            'success': False,
            'error': 'computed_field_id and reporting_date are required'
        }), 400
    
    reporting_date = datetime.strptime(reporting_date_str, '%Y-%m-%d').date()
    
    # Verify computed field assignment exists for current user's entity
    assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
        field_id=computed_field_id,
        entity_id=current_user.entity_id,
        is_active=True
    ).first()
    
    if not assignment:
        return jsonify({'success': False, 'error': 'Computed field not found or not accessible'}), 404

    # Check if value already exists
    existing_data = ESGData.query_for_tenant(db.session).filter_by(
        field_id=computed_field_id,
        entity_id=current_user.entity_id,
        reporting_date=reporting_date
    ).first()
    
    if existing_data and existing_data.calculated_value is not None and not force_compute:
        return jsonify({
            'success': True,
            'value': existing_data.calculated_value,
            'status': 'existing_value',
            'message': 'Using existing computed value'
        })
    
    # Attempt smart computation
    computed_value, status_message = aggregation_service.compute_field_value_if_ready(
        computed_field_id,
        current_user.entity_id,
        reporting_date,
        force_compute=force_compute
    )
    
    if computed_value is not None:
        # Save the computed value
        if existing_data:
            old_value = existing_data.calculated_value
            existing_data.calculated_value = computed_value
        else:
            existing_data = ESGData(
                entity_id=current_user.entity_id,
                field_id=computed_field_id,
                raw_value=None,
                calculated_value=computed_value,
                reporting_date=reporting_date
            )
            db.session.add(existing_data)
            old_value = None
        
        db.session.commit()
        
        # Create audit log
        audit_log = ESGDataAuditLog(
            data_id=existing_data.data_id,
            change_type='On-demand Computation',
            changed_by=current_user.id,
            old_value=old_value,
            new_value=computed_value
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'value': computed_value,
            'status': 'computed',
            'message': status_message
        })
    else:
        return jsonify({
            'success': False,
            'value': None,
            'status': 'insufficient_data',
            'message': status_message
        })

@user_bp.route('/api/check-computation-eligibility', methods=['POST'])
@login_required
@tenant_required_for('USER')
def check_computation_eligibility():
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    data = request.get_json()
    computed_field_id = data.get('computed_field_id')
    reporting_date_str = data.get('reporting_date')
    
    if not computed_field_id or not reporting_date_str:
        return jsonify({
            'success': False,
            'error': 'computed_field_id and reporting_date are required'
        }), 400
    
    reporting_date = datetime.strptime(reporting_date_str, '%Y-%m-%d').date()
    
    # Verify computed field assignment exists for current user's entity
    assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
        field_id=computed_field_id,
        entity_id=current_user.entity_id,
        is_active=True
    ).first()
    
    if not assignment:
        return jsonify({'eligible': False, 'reason': 'Computed field not found or not accessible'})

    should_compute, reason = aggregation_service.should_compute_field(
        computed_field_id,
        current_user.entity_id,
        reporting_date
    )
    
    return jsonify({
        'success': True,
        'eligible': should_compute,
        'reason': reason,
        'computed_field_id': computed_field_id,
        'reporting_date': reporting_date_str
    })

@user_bp.route('/debug/dashboard-data')
@login_required
@tenant_required_for('USER')
def debug_dashboard_data():
    # Note: require_tenant() is now handled by @tenant_required_for decorator
    
    # Get selected date (default to today)
    selected_date = datetime.now().date()
    
    # Get computed fields for this entity
    computed_fields_query = (db.session.query(
        FrameworkDataField,
        FrameworkDataField.description,
        FrameworkDataField.is_computed,
        FrameworkDataField.formula_expression
    )
    .join(DataPointAssignment, FrameworkDataField.field_id == DataPointAssignment.field_id)
    .join(Entity, DataPointAssignment.entity_id == Entity.id)
    .filter(
        DataPointAssignment.entity_id == current_user.entity_id,
        DataPointAssignment.series_status == 'active',
        FrameworkDataField.is_computed == True
    )
    .distinct()
    .all())
    
    computed_points = []
    for dp, desc, is_computed, formula in computed_fields_query:
        point_data = {
            'id': dp.field_id,
            'name': dp.field_name,
            'value_type': dp.value_type,
            'unit': dp.default_unit,
            'description': desc,
            'is_computed': is_computed,
            'formula': formula,
            'dependencies': []
        }
        
        # Get dependencies for this computed field
        deps = (FieldVariableMapping.query
               .filter_by(computed_field_id=dp.field_id)
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
    
    # Get ESG data for computed fields
    esg_data = ESGData.query_for_tenant(db.session).filter_by(
        entity_id=current_user.entity_id,
        reporting_date=selected_date
    ).all()
    
    entity_data_entries = {}
    for entry in esg_data:
        entity_data_entries[entry.field_id] = {
            'raw_value': entry.raw_value,
            'calculated_value': entry.calculated_value,
            'entity_id': entry.entity_id,
            'data_id': entry.data_id
        }
    
    debug_info = {
        'user_id': current_user.id,
        'username': current_user.name,
        'entity_id': current_user.entity_id,
        'selected_date': selected_date.strftime('%Y-%m-%d'),
        'computed_points': computed_points,
        'entity_data_entries': entity_data_entries,
        'computed_fields_count': len(computed_points)
    }
    
    return jsonify({
        'success': True,
        'debug_info': debug_info
    })
        