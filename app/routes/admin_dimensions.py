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
                # Use query_for_tenant with correct primary key column name
                dimension = Dimension.query_for_tenant(db.session).filter_by(dimension_id=dimension_id).first()
            
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

            current_app.logger.debug(f'[assign_field_dimensions] Received data: {data}')
            current_app.logger.debug(f'[assign_field_dimensions] dimension_ids type: {type(dimension_ids)}, value: {dimension_ids}')

            # Check field exists and is accessible
            if is_super_admin():
                field = FrameworkDataField.query.get(field_id)
            else:
                # FrameworkDataField doesn't have get_for_tenant, use standard query with company_id
                from flask_login import current_user
                company_id = current_user.company_id
                field = FrameworkDataField.query.filter_by(
                    field_id=field_id,
                    company_id=company_id
                ).first()

            if not field:
                return jsonify({'success': False, 'message': 'Field not found'}), 404

            # Remove existing field dimensions
            existing_assignments = FieldDimension.query.filter_by(field_id=field_id).all()
            for assignment in existing_assignments:
                db.session.delete(assignment)

            # Create new field dimension assignments
            for dimension_id in dimension_ids:
                current_app.logger.debug(f'[assign_field_dimensions] Processing dimension_id type: {type(dimension_id)}, value: {dimension_id}')

                # Verify dimension exists and is accessible
                if is_super_admin():
                    dimension = Dimension.query.get(dimension_id)
                else:
                    # Use query_for_tenant with correct primary key column name
                    dimension = Dimension.query_for_tenant(db.session).filter_by(dimension_id=dimension_id).first()

                current_app.logger.debug(f'[assign_field_dimensions] Found dimension: {dimension is not None}, dimension_id: {dimension_id if dimension else "NOT FOUND"}')

                if dimension:
                    field_dimension = FieldDimension(
                        field_id=field_id,
                        dimension_id=dimension_id,
                        company_id=field.company_id
                    )
                    db.session.add(field_dimension)
                    current_app.logger.debug(f'[assign_field_dimensions] Added FieldDimension to session')

            db.session.commit()
            current_app.logger.debug(f'[assign_field_dimensions] Committed changes successfully')

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
                # FrameworkDataField doesn't have get_for_tenant, use standard query with company_id
                from flask_login import current_user
                company_id = current_user.company_id
                field = FrameworkDataField.query.filter_by(
                    field_id=field_id,
                    company_id=company_id
                ).first()

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
                    'field_dimension_id': fd.field_dimension_id,
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
            import traceback
            current_app.logger.error(f'Error getting field dimensions: {str(e)}')
            current_app.logger.error(f'Traceback: {traceback.format_exc()}')
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
                # FrameworkDataField doesn't have get_for_tenant, use standard query with company_id
                from flask_login import current_user
                company_id = current_user.company_id
                field = FrameworkDataField.query.filter_by(
                    field_id=field_id,
                    company_id=company_id
                ).first()
            
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

    @admin_bp.route('/fields/<field_id>/dimensions/validate', methods=['POST'])
    @login_required
    @admin_or_super_admin_required
    def validate_field_dimension_operation(field_id):
        """
        Validate dimension operations for computed field consistency.

        This endpoint enforces the business rule: when assigning dimensions to a computed field,
        all dependencies (raw fields) MUST have AT LEAST the same dimensions. Dependencies can
        have MORE dimensions but CANNOT have FEWER.

        Args:
            field_id (str): Field ID for the operation

        Request Body:
            action (str): 'assign' or 'remove'
            dimension_ids (list): For 'assign' action - list of dimension IDs
            dimension_id (str): For 'remove' action - single dimension ID

        Returns:
            JSON: Validation result with errors/conflicts if invalid
        """
        try:
            data = request.get_json()
            action = data.get('action')

            if action not in ['assign', 'remove']:
                return jsonify({
                    'success': False,
                    'valid': False,
                    'error': 'Invalid action. Must be "assign" or "remove"'
                }), 400

            # Check field exists and is accessible
            if is_super_admin():
                field = FrameworkDataField.query.get(field_id)
            else:
                # FrameworkDataField doesn't have get_for_tenant, use standard query with company_id
                from flask_login import current_user
                company_id = current_user.company_id
                field = FrameworkDataField.query.filter_by(
                    field_id=field_id,
                    company_id=company_id
                ).first()

            if not field:
                return jsonify({
                    'success': False,
                    'valid': False,
                    'error': 'Field not found'
                }), 404

            # Validate based on action
            if action == 'assign':
                dimension_ids = data.get('dimension_ids', [])
                result = validate_dimension_assignment(field, dimension_ids)
            else:  # remove
                dimension_id = data.get('dimension_id')
                if not dimension_id:
                    return jsonify({
                        'success': False,
                        'valid': False,
                        'error': 'dimension_id is required for remove action'
                    }), 400
                result = validate_dimension_removal(field, dimension_id)

            return jsonify(result)

        except Exception as e:
            current_app.logger.error(f'Error validating dimension operation: {str(e)}')
            return jsonify({
                'success': False,
                'valid': False,
                'error': 'Error validating dimension operation'
            }), 500


def validate_dimension_assignment(field, dimension_ids):
    """
    Validate assigning dimensions to a computed field.

    Business Rule: All dependencies must have AT LEAST the dimensions being assigned.
    Dependencies can have MORE dimensions, but cannot have FEWER.

    Args:
        field (FrameworkDataField): The computed field
        dimension_ids (list): List of dimension IDs to assign

    Returns:
        dict: Validation result with errors if invalid
    """
    # If not a computed field, always valid
    if not field.is_computed:
        return {
            'success': True,
            'valid': True,
            'message': 'Raw fields can have any dimensions'
        }

    # Get all dependencies recursively
    dependencies = field.get_all_dependencies()

    if not dependencies:
        return {
            'success': True,
            'valid': True,
            'message': 'No dependencies to validate'
        }

    # Convert dimension_ids to set for comparison
    required_dimension_ids = set(dimension_ids)

    # Get dimension names for better error messages
    dimensions_map = {dim.dimension_id: dim for dim in Dimension.query.filter(
        Dimension.dimension_id.in_(dimension_ids)
    ).all()}

    errors = []

    # Check each dependency
    for dep in dependencies:
        # Get current dimensions for this dependency
        dep_field_dims = FieldDimension.query.filter_by(field_id=dep.field_id).all()
        dep_dimension_ids = set(fd.dimension_id for fd in dep_field_dims)

        # Check if dependency has all required dimensions
        missing_dimension_ids = required_dimension_ids - dep_dimension_ids

        if missing_dimension_ids:
            # Get dimension names for error message
            missing_dimensions = [dimensions_map.get(dim_id) for dim_id in missing_dimension_ids]
            current_dimensions = [fd.dimension for fd in dep_field_dims]

            errors.append({
                'field_id': dep.field_id,
                'field_name': dep.field_name,
                'missing_dimension_ids': list(missing_dimension_ids),
                'missing_dimension_names': [d.name for d in missing_dimensions if d],
                'current_dimension_ids': list(dep_dimension_ids),
                'current_dimension_names': [d.name for d in current_dimensions if d]
            })

    if errors:
        return {
            'success': True,
            'valid': False,
            'errors': errors,
            'message': f'Cannot assign dimensions: {len(errors)} dependencies are missing required dimensions'
        }

    return {
        'success': True,
        'valid': True,
        'message': 'All dependencies have required dimensions'
    }


def validate_dimension_removal(field, dimension_id):
    """
    Validate removing a dimension from a raw field.

    Business Rule: Cannot remove a dimension if any computed fields that depend on this
    field require that dimension.

    Args:
        field (FrameworkDataField): The raw field
        dimension_id (str): Dimension ID to remove

    Returns:
        dict: Validation result with conflicts if invalid
    """
    # If this is a computed field, just check if it has dependencies requiring it
    # (though typically we assign to computed fields, not remove from them)

    # Get all computed fields that depend on this field
    dependent_fields = field.get_fields_depending_on_this()

    if not dependent_fields:
        return {
            'success': True,
            'valid': True,
            'message': 'No computed fields depend on this field'
        }

    # Get dimension for error messages
    dimension = Dimension.query.get(dimension_id)
    if not dimension:
        return {
            'success': False,
            'valid': False,
            'error': 'Dimension not found'
        }

    conflicts = []

    # Check each dependent computed field
    for computed_field in dependent_fields:
        # Get dimensions for this computed field
        computed_field_dims = FieldDimension.query.filter_by(
            field_id=computed_field.field_id
        ).all()
        computed_dimension_ids = set(fd.dimension_id for fd in computed_field_dims)

        # If the computed field requires this dimension, it's a conflict
        if dimension_id in computed_dimension_ids:
            all_dimensions = [fd.dimension for fd in computed_field_dims]

            conflicts.append({
                'field_id': computed_field.field_id,
                'field_name': computed_field.field_name,
                'required_dimension_ids': list(computed_dimension_ids),
                'required_dimension_names': [d.name for d in all_dimensions if d]
            })

    if conflicts:
        return {
            'success': True,
            'valid': False,
            'conflicts': conflicts,
            'message': f'Cannot remove dimension "{dimension.name}": {len(conflicts)} computed fields require it'
        }

    return {
        'success': True,
        'valid': True,
        'message': f'Dimension "{dimension.name}" can be safely removed'
    } 