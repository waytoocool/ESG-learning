from flask import render_template, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import date, datetime
from ...decorators.auth import tenant_required_for
from ...services.user_v2.entity_service import EntityService
from ...services.user_v2.field_service import FieldService
from ...models.esg_data import ESGData
from ...models.data_assignment import DataPointAssignment
from ...extensions import db
from . import user_v2_bp

@user_v2_bp.route('/dashboard')
@login_required
@tenant_required_for('USER')
def dashboard():
    """
    New modal-based data entry dashboard (Phase 1 - Full Implementation).

    This route implements the new user dashboard with:
    - Entity switcher for admin users
    - Data points table with assignment information
    - Modal dialog structure for data entry
    - Separation of raw and computed fields
    """
    # Check if user has opted into the new interface
    if not current_user.use_new_data_entry:
        # If user hasn't opted in, redirect to old dashboard
        current_app.logger.info(
            f'User {current_user.id} accessed v2 dashboard but has not opted in - redirecting to legacy'
        )
        return redirect(url_for('user.dashboard'))

    current_app.logger.info(
        f'User {current_user.id} accessing new v2 dashboard (Phase 1)'
    )

    # Check if user has an entity assigned
    if not current_user.entity_id:
        current_app.logger.warning(f'User {current_user.id} has no entity assigned')
        return render_template('user_v2/dashboard.html',
                             error_message='No entity assigned to user. Please contact your administrator.',
                             entities=[],
                             current_entity=None,
                             raw_input_fields=[],
                             computed_fields=[],
                             user_name=current_user.name)

    # Get current entity
    current_entity = EntityService.get_current_entity(current_user.id)
    if not current_entity:
        current_app.logger.error(f'Entity {current_user.entity_id} not found for user {current_user.id}')
        return render_template('user_v2/dashboard.html',
                             error_message='Entity not found. Please contact your administrator.',
                             entities=[],
                             current_entity=None,
                             raw_input_fields=[],
                             computed_fields=[],
                             user_name=current_user.name)

    # Get all accessible entities (for entity switcher)
    entities = EntityService.get_user_entities(current_user.id)
    current_app.logger.info(f'User {current_user.id} has access to {len(entities)} entities')

    # Get assigned fields for current entity
    all_fields = FieldService.get_assigned_fields_for_entity(
        entity_id=current_entity.id,
        include_computed=True
    )
    current_app.logger.info(f'Found {len(all_fields)} assigned fields for entity {current_entity.id}')

    # Separate raw input fields from computed fields
    raw_input_fields = []
    computed_fields = []

    for field_data in all_fields:
        # Get field status (check if data exists for current date)
        today = date.today()
        data_entry = ESGData.query.filter_by(
            field_id=field_data['field_id'],
            entity_id=current_entity.id,
            reporting_date=today
        ).first()

        # Determine status
        if data_entry:
            if data_entry.raw_value is not None or data_entry.calculated_value is not None:
                status = 'complete'
            else:
                status = 'partial'
        else:
            status = 'empty'

        # Add status to field data
        field_data['status'] = status

        # Categorize field
        if field_data['is_computed']:
            computed_fields.append(field_data)
        else:
            raw_input_fields.append(field_data)

    current_app.logger.info(
        f'Categorized fields: {len(raw_input_fields)} raw, {len(computed_fields)} computed'
    )

    # Prepare context data
    context = {
        'user_name': current_user.name,
        'user_role': current_user.role,
        'current_entity': {
            'id': current_entity.id,
            'name': current_entity.name,
            'type': current_entity.entity_type
        },
        'entities': [
            {
                'id': e.id,
                'name': e.name,
                'type': e.entity_type,
                'is_current': e.id == current_entity.id
            } for e in entities
        ],
        'raw_input_fields': raw_input_fields,
        'computed_fields': computed_fields,
        'total_fields': len(all_fields),
        'raw_count': len(raw_input_fields),
        'computed_count': len(computed_fields),
        'selected_date': date.today().isoformat()
    }

    return render_template('user_v2/dashboard.html', **context)

