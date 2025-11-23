from flask import render_template, redirect, url_for, current_app, request
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

    # Get fiscal year from query param or default to current FY
    from ...services.fiscal_year_service import FiscalYearService
    company = current_user.company

    # Get selected FY from query parameter (if provided)
    selected_fy_year = request.args.get('fy_year', type=int)
    if not selected_fy_year:
        selected_fy_year = FiscalYearService.get_current_fy_year(company)

    current_app.logger.info(f'Dashboard viewing FY: {selected_fy_year}')

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
        # Get field status based on overdue logic (check all past-due dates in selected FY)
        today = date.today()

        # Get the assignment for this field to access frequency and reporting dates
        from ...models.data_assignment import DataPointAssignment

        assignment = DataPointAssignment.query.filter_by(
            field_id=field_data['field_id'],
            entity_id=current_entity.id,
            series_status='active'
        ).first()

        if assignment:
            # Get all valid reporting dates for selected FY
            valid_dates = assignment.get_valid_reporting_dates(selected_fy_year)

            # Filter only past-due dates
            past_due_dates = [
                d for d in valid_dates
                if FiscalYearService.is_overdue(d, company, today)
            ]

            if past_due_dates:
                # Check if all past-due dates have data
                missing_dates = []
                for report_date in past_due_dates:
                    data_entry = ESGData.query.filter_by(
                        field_id=field_data['field_id'],
                        entity_id=current_entity.id,
                        reporting_date=report_date
                    ).first()

                    # Check if data exists and has a value
                    if not data_entry or (data_entry.raw_value is None and data_entry.calculated_value is None):
                        missing_dates.append(report_date)

                # Determine status
                if missing_dates:
                    status = 'overdue'  # Some past-due dates are missing data
                else:
                    status = 'complete'  # All past-due dates have data
            else:
                # No dates are past due yet
                status = 'pending'
        else:
            # No active assignment found
            status = 'pending'

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

    # Get fiscal year information
    current_fy_year = FiscalYearService.get_current_fy_year(company)
    fy_year_list = FiscalYearService.get_fy_year_list(company, years_back=2, years_forward=1)

    # Get FY display for selected year
    fy_start_date = company.get_fy_start_date(selected_fy_year)
    fy_end_date = company.get_fy_end_date(selected_fy_year)
    fy_display = company.get_fy_display(selected_fy_year)

    current_app.logger.info(f'Selected FY: {selected_fy_year}, Display: {fy_display}')

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
        'fields': all_fields,  # Combined list for template iteration
        'total_fields': len(all_fields),
        'raw_count': len(raw_input_fields),
        'computed_count': len(computed_fields),
        'selected_date': date.today().isoformat(),
        # Fiscal year information
        'current_fy_year': selected_fy_year,  # Currently selected FY for display and modal
        'selected_fy_year': selected_fy_year,  # For clarity in template
        'actual_current_fy': current_fy_year,  # Actual current FY (today's FY) for reference
        'fy_year_list': fy_year_list,
        'fy_display': fy_display,
        'fy_start_date': fy_start_date.isoformat(),
        'fy_end_date': fy_end_date.isoformat()
    }

    return render_template('user_v2/dashboard.html', **context)

