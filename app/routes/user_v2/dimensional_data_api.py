"""
Dimensional Data API for User Dashboard V2
Provides REST API endpoints for dimensional data operations.
"""

from flask import jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
from . import user_v2_bp
from app.decorators.auth import tenant_required_for
from app.models.esg_data import ESGData
from app.models.dimension import Dimension, DimensionValue
from app.services.user_v2.dimensional_data_service import DimensionalDataService
from app.services.user_v2.aggregation_service import AggregationService
from app.extensions import db
import logging

logger = logging.getLogger(__name__)


@user_v2_bp.route('/api/dimension-matrix/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_dimension_matrix(field_id):
    """
    Get dimension matrix for a field.

    Query Parameters:
        - entity_id: Entity ID (required)
        - reporting_date: Reporting date in YYYY-MM-DD format (optional)

    Returns:
        JSON with dimension matrix structure and existing data
    """
    try:
        entity_id = request.args.get('entity_id', type=int)
        reporting_date = request.args.get('reporting_date')

        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'entity_id is required'
            }), 400

        # Get dimension matrix
        matrix = DimensionalDataService.prepare_dimension_matrix(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date
        )

        return jsonify(matrix)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_v2_bp.route('/api/submit-dimensional-data', methods=['POST'])
@login_required
@tenant_required_for('USER')
def submit_dimensional_data():
    """
    Submit dimensional data for a field.

    Request Body:
        {
            "field_id": "field-uuid",
            "entity_id": 1,
            "reporting_date": "2024-01-31",
            "dimensional_data": {
                "dimensions": ["gender", "age"],
                "breakdowns": [
                    {
                        "dimensions": {"gender": "Male", "age": "<30"},
                        "raw_value": 100,
                        "notes": "Optional notes"
                    },
                    ...
                ]
            },
            "notes": "Optional overall notes",
            "attachments": []
        }

    Returns:
        JSON with success status and calculated totals
    """
    try:
        data = request.get_json()

        # Validate required fields
        field_id = data.get('field_id')
        entity_id = data.get('entity_id')
        reporting_date = data.get('reporting_date')
        dimensional_data = data.get('dimensional_data')

        if not all([field_id, entity_id, reporting_date, dimensional_data]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: field_id, entity_id, reporting_date, dimensional_data'
            }), 400

        # Validate dimensional data structure
        is_valid, error = DimensionalDataService.validate_dimensional_data(
            field_id, dimensional_data
        )

        if not is_valid:
            return jsonify({
                'success': False,
                'error': error
            }), 400

        # Build complete dimension_values JSON
        dimension_values = DimensionalDataService.build_dimension_values_json(dimensional_data)

        # Get totals for raw_value
        totals = dimension_values.get('totals', {})
        overall_total = totals.get('overall', 0)

        # Convert reporting_date string to date object
        reporting_date_obj = datetime.strptime(reporting_date, '%Y-%m-%d').date()

        # Find or create ESGData entry
        esg_data = ESGData.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date_obj,
            company_id=current_user.company_id
        ).first()

        if esg_data:
            # Update existing entry
            esg_data.raw_value = str(overall_total)
            esg_data.dimension_values = dimension_values
            esg_data.updated_at = datetime.utcnow()
        else:
            # Create new entry
            esg_data = ESGData(
                field_id=field_id,
                entity_id=entity_id,
                reporting_date=reporting_date_obj,
                raw_value=str(overall_total),
                dimension_values=dimension_values,
                company_id=current_user.company_id
            )
            db.session.add(esg_data)

        # Commit to database
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Dimensional data saved successfully',
            'data_id': esg_data.data_id,
            'totals': totals,
            'overall_total': overall_total,
            'metadata': dimension_values.get('metadata', {})
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid date format: {str(e)}'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_v2_bp.route('/api/calculate-totals', methods=['POST'])
@login_required
@tenant_required_for('USER')
def calculate_totals():
    """
    Calculate totals from dimensional data without saving.

    Request Body:
        {
            "dimensional_data": {
                "dimensions": ["gender", "age"],
                "breakdowns": [...]
            }
        }

    Returns:
        JSON with calculated totals
    """
    try:
        data = request.get_json()
        dimensional_data = data.get('dimensional_data')

        if not dimensional_data:
            return jsonify({
                'success': False,
                'error': 'dimensional_data is required'
            }), 400

        # Calculate totals
        totals = DimensionalDataService.calculate_totals(dimensional_data)

        return jsonify({
            'success': True,
            'totals': totals
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_v2_bp.route('/api/dimension-values/<dimension_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_dimension_values(dimension_id):
    """
    Get all values for a specific dimension.

    Returns:
        JSON with dimension values
    """
    try:
        # Get dimension
        dimension = Dimension.query.filter_by(
            dimension_id=dimension_id,
            company_id=current_user.company_id
        ).first()

        if not dimension:
            return jsonify({
                'success': False,
                'error': 'Dimension not found'
            }), 404

        # Get ordered values
        values = dimension.get_ordered_values()

        return jsonify({
            'success': True,
            'dimension_id': dimension.dimension_id,
            'dimension_name': dimension.name,
            'description': dimension.description,
            'values': [
                {
                    'value_id': v.value_id,
                    'value': v.value,
                    'display_name': v.display_name or v.value,
                    'display_order': v.display_order,
                    'is_active': v.is_active
                }
                for v in values
            ]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_v2_bp.route('/api/aggregate-by-dimension', methods=['POST'])
@login_required
@tenant_required_for('USER')
def aggregate_by_dimension():
    """
    Aggregate data by a specific dimension.

    Request Body:
        {
            "field_id": "field-uuid",
            "entity_id": 1,
            "dimension_name": "gender",
            "reporting_date": "2024-01-31"
        }

    Returns:
        JSON with aggregated values
    """
    try:
        data = request.get_json()

        field_id = data.get('field_id')
        entity_id = data.get('entity_id')
        dimension_name = data.get('dimension_name')
        reporting_date = data.get('reporting_date')

        if not all([field_id, entity_id, dimension_name, reporting_date]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        result = AggregationService.aggregate_by_dimension(
            field_id=field_id,
            entity_id=entity_id,
            dimension_name=dimension_name,
            reporting_date=reporting_date
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_v2_bp.route('/api/cross-entity-totals', methods=['POST'])
@login_required
@tenant_required_for('USER')
def cross_entity_totals():
    """
    Calculate totals across multiple entities.

    Request Body:
        {
            "field_id": "field-uuid",
            "entity_ids": [1, 2, 3],
            "reporting_date": "2024-01-31",
            "aggregate_dimensions": true
        }

    Returns:
        JSON with cross-entity totals
    """
    try:
        data = request.get_json()

        field_id = data.get('field_id')
        entity_ids = data.get('entity_ids', [])
        reporting_date = data.get('reporting_date')
        aggregate_dimensions = data.get('aggregate_dimensions', False)

        if not all([field_id, entity_ids, reporting_date]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        result = AggregationService.calculate_cross_entity_totals(
            field_id=field_id,
            entity_ids=entity_ids,
            reporting_date=reporting_date,
            aggregate_dimensions=aggregate_dimensions
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_v2_bp.route('/api/dimension-summary/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_dimension_summary(field_id):
    """
    Get summary of dimensional data for a field.

    Query Parameters:
        - entity_id: Entity ID (required)
        - reporting_date: Reporting date (required)

    Returns:
        JSON with dimension summary
    """
    try:
        entity_id = request.args.get('entity_id', type=int)
        reporting_date = request.args.get('reporting_date')

        if not entity_id or not reporting_date:
            return jsonify({
                'success': False,
                'error': 'entity_id and reporting_date are required'
            }), 400

        summary = DimensionalDataService.get_dimension_summary(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date
        )

        return jsonify(summary)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_v2_bp.route('/api/dimension-breakdown/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_dimension_breakdown(field_id):
    """
    Get comprehensive breakdown of dimensional data.

    Query Parameters:
        - entity_id: Entity ID (required)
        - reporting_date: Reporting date (required)

    Returns:
        JSON with detailed breakdown
    """
    try:
        entity_id = request.args.get('entity_id', type=int)
        reporting_date = request.args.get('reporting_date')

        if not entity_id or not reporting_date:
            return jsonify({
                'success': False,
                'error': 'entity_id and reporting_date are required'
            }), 400

        breakdown = AggregationService.get_dimension_breakdown_summary(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date
        )

        return jsonify(breakdown)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Phase 4: Bulk Paste Endpoints for Excel/Sheets Integration
# ============================================================

@user_v2_bp.route('/api/parse-bulk-paste', methods=['POST'])
@login_required
@tenant_required_for('USER')
def parse_bulk_paste():
    """
    Parse bulk pasted data from Excel/Google Sheets.

    Request Body:
        {
            "field_id": "uuid",
            "clipboard_data": "tab-separated or comma-separated data",
            "has_headers": true
        }

    Returns:
        JSON with parsed data structure and validation results
    """
    try:
        data = request.get_json()

        field_id = data.get('field_id')
        clipboard_data = data.get('clipboard_data')
        has_headers = data.get('has_headers', True)

        if not field_id or not clipboard_data:
            return jsonify({
                'success': False,
                'error': 'field_id and clipboard_data are required'
            }), 400

        # Parse the clipboard data
        result = DimensionalDataService.parse_bulk_paste_data(
            field_id=field_id,
            clipboard_data=clipboard_data,
            has_headers=has_headers
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error parsing bulk paste: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_v2_bp.route('/api/validate-bulk-data', methods=['POST'])
@login_required
@tenant_required_for('USER')
def validate_bulk_data():
    """
    Validate bulk pasted data before applying.

    Request Body:
        {
            "field_id": "uuid",
            "entity_id": 123,
            "reporting_date": "2025-01-15",
            "parsed_data": [
                {
                    "value": 100,
                    "dimensions": {"gender": "Male", "age": "<30"}
                },
                ...
            ]
        }

    Returns:
        JSON with validation results
    """
    try:
        data = request.get_json()

        field_id = data.get('field_id')
        entity_id = data.get('entity_id')
        reporting_date = data.get('reporting_date')
        parsed_data = data.get('parsed_data')

        if not all([field_id, entity_id, reporting_date, parsed_data]):
            return jsonify({
                'success': False,
                'error': 'field_id, entity_id, reporting_date, and parsed_data are required'
            }), 400

        # Validate the bulk data
        result = DimensionalDataService.validate_bulk_paste_data(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date,
            parsed_data=parsed_data
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error validating bulk data: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_v2_bp.route('/api/apply-bulk-paste', methods=['POST'])
@login_required
@tenant_required_for('USER')
def apply_bulk_paste():
    """
    Apply validated bulk pasted data.

    Request Body:
        {
            "field_id": "uuid",
            "entity_id": 123,
            "reporting_date": "2025-01-15",
            "parsed_data": [
                {
                    "value": 100,
                    "dimensions": {"gender": "Male", "age": "<30"}
                },
                ...
            ]
        }

    Returns:
        JSON with application results
    """
    try:
        data = request.get_json()

        field_id = data.get('field_id')
        entity_id = data.get('entity_id')
        reporting_date = data.get('reporting_date')
        parsed_data = data.get('parsed_data')

        if not all([field_id, entity_id, reporting_date, parsed_data]):
            return jsonify({
                'success': False,
                'error': 'field_id, entity_id, reporting_date, and parsed_data are required'
            }), 400

        # Apply the bulk paste
        result = DimensionalDataService.apply_bulk_paste_data(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date,
            parsed_data=parsed_data,
            company_id=current_user.company_id,
            user_id=current_user.id
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error applying bulk paste: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
