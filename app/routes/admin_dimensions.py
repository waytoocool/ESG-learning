"""
Phase 2.5: Dimension Management Routes

This module contains API endpoints for managing dimensions and dimensional data
in the ESG DataVault system. Dimensions allow for complex data breakdowns like
gender, age groups, departments, etc.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from ..decorators.auth import admin_or_super_admin_required
from ..models import Dimension, DimensionValue, FieldDimension, FrameworkDataField
from ..extensions import db
from ..middleware.tenant import get_current_tenant
from sqlalchemy.sql import func


def is_super_admin():
    """Check if current user is a super admin (no company_id)"""
    from flask_login import current_user
    return current_user.role == 'SUPER_ADMIN'


def register_dimension_routes(admin_bp):
    """Register dimension management routes with the admin blueprint."""
    
    @admin_bp.route('/dimensions', methods=['POST'])
    @login_required
    @admin_or_super_admin_required
    def create_dimension():
        """Create a new dimension for data categorization."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'Request body must be valid JSON'}), 400

            name = (data.get('name') or '').strip()
            description = (data.get('description') or '').strip()
            dimension_values = data.get('values', [])
            
            if not name:
                return jsonify({'success': False, 'message': 'Dimension name is required'}), 400
                
            # Get company_id based on admin level
            if is_super_admin():
                company_id = data.get('company_id')
                if not company_id:
                    return jsonify({'success': False, 'message': 'Company ID is required for super admin'}), 400
            else:
                tenant = get_current_tenant()
                if not tenant:
                    return jsonify({'success': False, 'message': 'No tenant context found'}), 400
                company_id = tenant.id
            
            # Check if dimension already exists
            if is_super_admin():
                existing = Dimension.query.filter_by(name=name, company_id=company_id).first()
            else:
                existing = Dimension.query_for_tenant(db.session).filter_by(name=name).first()
            
            if existing:
                return jsonify({'success': False, 'message': 'Dimension with this name already exists'}), 400
            
            # Create dimension
            dimension = Dimension(
                name=name,
                company_id=company_id,
                description=description
            )
            
            db.session.add(dimension)
            db.session.flush()  # Get dimension_id
            
            # Create dimension values
            for i, value_data in enumerate(dimension_values):
                if isinstance(value_data, str):
                    value = value_data.strip()
                    display_name = value
                else:
                    value = value_data.get('value', '').strip()
                    display_name = value_data.get('display_name', value).strip()
                
                if value:
                    dim_value = DimensionValue(
                        dimension_id=dimension.dimension_id,
                        value=value,
                        company_id=company_id,
                        display_name=display_name,
                        display_order=i
                    )
                    db.session.add(dim_value)
            
            db.session.commit()
            
            # Prepare the dimension data to return
            dimension_data = {
                'dimension_id': dimension.dimension_id,
                'name': dimension.name,
                'description': dimension.description,
                'is_system_default': dimension.is_system_default,
                'values': [
                    {
                        'value_id': value.value_id,
                        'value': value.value,
                        'display_name': value.effective_display_name,
                        'display_order': value.display_order,
                        'is_active': value.is_active
                    }
                    for value in dimension.get_ordered_values()
                ],
                'created_at': dimension.created_at.isoformat() if dimension.created_at else None
            }

            return jsonify({
                'success': True,
                'message': 'Dimension created successfully',
                'dimension': dimension_data
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception('Error creating dimension') # This will log the full traceback
            return jsonify({'success': False, 'message': 'Error creating dimension'}), 500

    @admin_bp.route('/dimensions')
    @login_required
    @admin_or_super_admin_required
    def get_dimensions():
        """Get all dimensions for the current tenant."""
        try:
            if is_super_admin():
                dimensions = Dimension.query.all()
            else:
                dimensions = Dimension.query_for_tenant(db.session).all()
            
            dimensions_data = []
            for dimension in dimensions:
                values_data = [
                    {
                        'value_id': value.value_id,
                        'value': value.value,
                        'display_name': value.effective_display_name,
                        'display_order': value.display_order,
                        'is_active': value.is_active
                    }
                    for value in dimension.get_ordered_values()
                ]
                
                dimensions_data.append({
                    'dimension_id': dimension.dimension_id,
                    'name': dimension.name,
                    'description': dimension.description,
                    'is_system_default': dimension.is_system_default,
                    'values': values_data,
                    'created_at': dimension.created_at.isoformat() if dimension.created_at else None
                })
            
            return jsonify({
                'success': True,
                'dimensions': dimensions_data
            })
            
        except Exception as e:
            current_app.logger.error(f'Error getting dimensions: {str(e)}')
            return jsonify({'success': False, 'message': 'Error getting dimensions'}), 500

    @admin_bp.route('/dimensions/<dimension_id>/values', methods=['POST'])
    @login_required
    @admin_or_super_admin_required
    def create_dimension_value(dimension_id):
        """Create a new value for a dimension."""
        try:
            data = request.get_json()
            value = data.get('value', '').strip()
            display_name = data.get('display_name', '').strip()
            
            if not value:
                return jsonify({'success': False, 'message': 'Value is required'}), 400
            
            # Check dimension exists and is accessible
            if is_super_admin():
                dimension = Dimension.query.get(dimension_id)
            else:
                dimension = Dimension.get_for_tenant(db.session, dimension_id)
            
            if not dimension:
                return jsonify({'success': False, 'message': 'Dimension not found'}), 404
            
            # Check if value already exists
            existing = DimensionValue.query.filter_by(
                dimension_id=dimension_id,
                value=value
            ).first()
            
            if existing:
                return jsonify({'success': False, 'message': 'Value already exists in this dimension'}), 400
            
            # Get next display order
            max_order = db.session.query(func.max(DimensionValue.display_order)).filter_by(
                dimension_id=dimension_id
            ).scalar() or 0
            
            # Create dimension value
            dim_value = DimensionValue(
                dimension_id=dimension_id,
                value=value,
                company_id=dimension.company_id,
                display_name=display_name or value,
                display_order=max_order + 1
            )
            
            db.session.add(dim_value)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Dimension value created successfully',
                'value_id': dim_value.value_id
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating dimension value: {str(e)}')
            return jsonify({'success': False, 'message': 'Error creating dimension value'}), 500

    @admin_bp.route('/fields/<field_id>/dimensions', methods=['POST'])
    @login_required
    @admin_or_super_admin_required
    def assign_field_dimensions(field_id):
        """Assign dimensions to a field."""
        try:
            data = request.get_json()
            dimension_ids = data.get('dimension_ids', [])
            
            # Check field exists and is accessible
            if is_super_admin():
                field = FrameworkDataField.query.get(field_id)
            else:
                field = FrameworkDataField.get_for_tenant(db.session, field_id)
            
            if not field:
                return jsonify({'success': False, 'message': 'Field not found'}), 404
            
            # Remove existing field dimensions
            existing_assignments = FieldDimension.query.filter_by(field_id=field_id).all()
            for assignment in existing_assignments:
                db.session.delete(assignment)
            
            # Create new field dimension assignments
            for dimension_id in dimension_ids:
                # Verify dimension exists and is accessible
                if is_super_admin():
                    dimension = Dimension.query.get(dimension_id)
                else:
                    dimension = Dimension.get_for_tenant(db.session, dimension_id)
                
                if dimension:
                    field_dimension = FieldDimension(
                        field_id=field_id,
                        dimension_id=dimension_id,
                        company_id=field.company_id
                    )
                    db.session.add(field_dimension)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Field dimensions updated successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error assigning field dimensions: {str(e)}')
            return jsonify({'success': False, 'message': 'Error assigning field dimensions'}), 500

    @admin_bp.route('/fields/<field_id>/dimensions')
    @login_required
    @admin_or_super_admin_required
    def get_field_dimensions(field_id):
        """Get dimensions assigned to a field."""
        try:
            # Check field exists and is accessible
            if is_super_admin():
                field = FrameworkDataField.query.get(field_id)
            else:
                field = FrameworkDataField.get_for_tenant(db.session, field_id)
            
            if not field:
                return jsonify({'success': False, 'message': 'Field not found'}), 404
            
            # Get field dimensions
            field_dimensions = FieldDimension.query.filter_by(field_id=field_id).all()
            
            dimensions_data = []
            for fd in field_dimensions:
                dimension = fd.dimension
                values_data = [
                    {
                        'value_id': value.value_id,
                        'value': value.value,
                        'display_name': value.effective_display_name,
                        'display_order': value.display_order
                    }
                    for value in dimension.get_ordered_values()
                ]
                
                dimensions_data.append({
                    'dimension_id': dimension.dimension_id,
                    'name': dimension.name,
                    'description': dimension.description,
                    'is_required': fd.is_required,
                    'values': values_data
                })
            
            return jsonify({
                'success': True,
                'dimensions': dimensions_data
            })
            
        except Exception as e:
            current_app.logger.error(f'Error getting field dimensions: {str(e)}')
            return jsonify({'success': False, 'message': 'Error getting field dimensions'}), 500

    @admin_bp.route('/validate_dimension_filter', methods=['POST'])
    @login_required
    @admin_or_super_admin_required
    def validate_dimension_filter():
        """Validate a dimension filter for field variable mapping."""
        try:
            data = request.get_json()
            field_id = data.get('field_id')
            dimension_filter = data.get('dimension_filter', {})
            
            if not field_id:
                return jsonify({'success': False, 'message': 'Field ID is required'}), 400
            
            # Check field exists and get its dimensions
            if is_super_admin():
                field = FrameworkDataField.query.get(field_id)
            else:
                field = FrameworkDataField.get_for_tenant(db.session, field_id)
            
            if not field:
                return jsonify({'success': False, 'message': 'Field not found'}), 404
            
            # Get field dimensions
            field_dimensions = {fd.dimension.name: fd.dimension for fd in field.field_dimensions}
            
            validation_errors = []
            valid_filter = {}
            
            for dim_name, dim_value in dimension_filter.items():
                if dim_name not in field_dimensions:
                    validation_errors.append(f'Dimension "{dim_name}" is not assigned to this field')
                    continue
                
                dimension = field_dimensions[dim_name]
                valid_values = [v.value for v in dimension.dimension_values if v.is_active]
                
                if dim_value not in valid_values:
                    validation_errors.append(f'Value "{dim_value}" is not valid for dimension "{dim_name}"')
                    continue
                
                valid_filter[dim_name] = dim_value
            
            return jsonify({
                'success': True,
                'valid': len(validation_errors) == 0,
                'errors': validation_errors,
                'valid_filter': valid_filter
            })
            
        except Exception as e:
            current_app.logger.error(f'Error validating dimension filter: {str(e)}')
            return jsonify({'success': False, 'message': 'Error validating dimension filter'}), 500

    @admin_bp.route('/system_dimensions', methods=['POST'])
    @login_required
    @admin_or_super_admin_required
    def create_system_dimensions():
        """Bootstrap system default dimensions like Gender and Age Group."""
        try:
            if not is_super_admin():
                return jsonify({'success': False, 'message': 'Only super admin can create system dimensions'}), 403
            
            data = request.get_json()
            company_id = data.get('company_id')
            
            if not company_id:
                return jsonify({'success': False, 'message': 'Company ID is required'}), 400
            
            # Default system dimensions
            system_dimensions = [
                {
                    'name': 'Gender',
                    'description': 'Employee gender breakdown',
                    'values': ['Male', 'Female', 'Other', 'Prefer not to say']
                },
                {
                    'name': 'Age Group',
                    'description': 'Employee age group breakdown',
                    'values': ['<30', '30-50', '>50']
                },
                {
                    'name': 'Employment Type',
                    'description': 'Type of employment',
                    'values': ['Full-time', 'Part-time', 'Contract', 'Temporary']
                },
                {
                    'name': 'Department',
                    'description': 'Department or division',
                    'values': ['IT', 'Finance', 'HR', 'Operations', 'Sales', 'Marketing', 'Other']
                }
            ]
            
            created_dimensions = []
            
            for dim_config in system_dimensions:
                # Check if dimension already exists
                existing = Dimension.query.filter_by(
                    name=dim_config['name'],
                    company_id=company_id
                ).first()
                
                if existing:
                    continue
                
                # Create dimension
                dimension = Dimension(
                    name=dim_config['name'],
                    company_id=company_id,
                    description=dim_config['description'],
                    is_system_default=True
                )
                
                db.session.add(dimension)
                db.session.flush()
                
                # Create dimension values
                for i, value in enumerate(dim_config['values']):
                    dim_value = DimensionValue(
                        dimension_id=dimension.dimension_id,
                        value=value,
                        company_id=company_id,
                        display_name=value,
                        display_order=i
                    )
                    db.session.add(dim_value)
                
                created_dimensions.append(dim_config['name'])
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Created {len(created_dimensions)} system dimensions',
                'created_dimensions': created_dimensions
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating system dimensions: {str(e)}')
            return jsonify({'success': False, 'message': 'Error creating system dimensions'}), 500 