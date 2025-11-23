"""
Export API for historical data - User V2

This module provides endpoints for exporting historical field data to CSV and Excel formats.
Supports both dimensional and non-dimensional data with proper column expansion.
"""

from flask import Blueprint, send_file, request, jsonify
from flask_login import login_required, current_user
from io import BytesIO
import pandas as pd
from datetime import datetime
from sqlalchemy import desc

from ...decorators.auth import tenant_required_for
from ...models.esg_data import ESGData
from ...models.framework import FrameworkDataField
from ...models.data_assignment import DataPointAssignment

export_api_bp = Blueprint('user_v2_export_api', __name__, url_prefix='/api/user/v2/export')


@export_api_bp.route('/field-history/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def export_field_history(field_id):
    """
    Export field history to CSV or Excel.

    Query Parameters:
        entity_id (optional): Entity ID (defaults to current user's entity)
        format: 'csv' or 'excel' (default: 'csv')
        limit (optional): Max entries to export (default: all)

    Returns:
        File download with proper MIME type and filename
    """
    try:
        # Get parameters
        entity_id = request.args.get('entity_id', type=int) or current_user.entity_id
        export_format = request.args.get('format', 'csv').lower()
        limit = request.args.get('limit', type=int)

        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'No entity context available'
            }), 400

        # Validate export format
        if export_format not in ['csv', 'excel']:
            return jsonify({
                'success': False,
                'error': 'Invalid format. Must be "csv" or "excel"'
            }), 400

        # Get field details
        field = FrameworkDataField.query.filter_by(field_id=field_id).first()
        if not field:
            return jsonify({
                'success': False,
                'error': 'Field not found'
            }), 404

        # Check if field is assigned to this entity
        assignment = DataPointAssignment.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            series_status='active'
        ).first()

        if not assignment:
            return jsonify({
                'success': False,
                'error': 'Field not assigned to this entity'
            }), 404

        # Build query for historical data
        query = ESGData.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            is_draft=False
        ).order_by(desc(ESGData.reporting_date))

        if limit:
            query = query.limit(limit)

        historical_entries = query.all()

        if not historical_entries:
            return jsonify({
                'success': False,
                'error': 'No historical data available to export'
            }), 404

        # Build dataframe
        data = []
        dimension_columns = set()  # Track unique dimension keys

        for entry in historical_entries:
            # Determine value to show
            if field.is_computed:
                value = entry.calculated_value
            else:
                value = entry.raw_value

            # Check if entry has dimensional data
            has_dimensions = entry.dimension_values is not None and len(entry.dimension_values) > 0 if entry.dimension_values else False

            # Base row data
            row = {
                'Reporting Date': entry.reporting_date.isoformat(),
                'Value': value,
                'Unit': entry.unit or field.default_unit,
                'Has Dimensions': 'Yes' if has_dimensions else 'No',
                'Notes': entry.notes if entry.notes else '',  # Enhancement #2: Include notes
                'Created At': entry.created_at.isoformat() if entry.created_at else None,
                'Updated At': entry.updated_at.isoformat() if entry.updated_at else None
            }

            # Add dimension columns if applicable
            if has_dimensions and entry.dimension_values:
                # Handle dimensional data based on structure
                if 'breakdowns' in entry.dimension_values:
                    # New dimensional data format
                    for breakdown in entry.dimension_values.get('breakdowns', []):
                        dims = breakdown.get('dimensions', {})
                        for dim_key, dim_value in dims.items():
                            column_name = f'Dimension: {dim_key}'
                            row[column_name] = dim_value
                            dimension_columns.add(column_name)
                else:
                    # Old dimensional data format (flat structure)
                    for dim_key, dim_value in entry.dimension_values.items():
                        if dim_key not in ['dimensions', 'breakdowns']:
                            column_name = f'Dimension: {dim_key}'
                            row[column_name] = dim_value
                            dimension_columns.add(column_name)

            data.append(row)

        # Create DataFrame
        df = pd.DataFrame(data)

        # Reorder columns: base columns first, then dimensions
        base_columns = ['Reporting Date', 'Value', 'Unit', 'Has Dimensions', 'Notes', 'Created At', 'Updated At']  # Enhancement #2: Added Notes column
        dimension_columns_sorted = sorted(list(dimension_columns))
        final_columns = base_columns + dimension_columns_sorted

        # Ensure all columns exist (fill missing with None)
        for col in final_columns:
            if col not in df.columns:
                df[col] = None

        df = df[final_columns]

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_field_name = field.field_name.replace(' ', '_').replace('/', '_').replace('\\', '_')

        # Create file in memory
        output = BytesIO()

        if export_format == 'excel':
            # Export to Excel
            filename = f'{safe_field_name}_history_{timestamp}.xlsx'
            df.to_excel(output, index=False, engine='openpyxl', sheet_name='Historical Data')
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            # Export to CSV
            filename = f'{safe_field_name}_history_{timestamp}.csv'
            df.to_csv(output, index=False, encoding='utf-8')
            mimetype = 'text/csv'

        output.seek(0)

        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Export failed: {str(e)}'
        }), 500
