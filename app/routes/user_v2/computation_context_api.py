"""
Computation Context API Endpoints
==================================

API endpoints for accessing computation context information for computed fields.

These endpoints provide:
- Complete computation context with formulas and dependencies
- Hierarchical dependency trees
- Step-by-step calculation breakdowns
- Historical trends
- Dependency validation

Author: Backend Developer Agent
Phase: 3 - Computation Context
Date: 2025-01-04
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from datetime import date, datetime
from typing import Optional

from ...decorators.auth import tenant_required_for
from ...services.user_v2.computation_context_service import ComputationContextService
from app import db

# Create blueprint for computation context API
computation_context_api_bp = Blueprint(
    'computation_context_api',
    __name__,
    url_prefix='/user/v2/api'
)


def parse_date_param(date_str: Optional[str], default: Optional[date] = None) -> Optional[date]:
    """
    Helper function to parse date parameter from request.

    Args:
        date_str: Date string in ISO format (YYYY-MM-DD)
        default: Default date if parsing fails

    Returns:
        Parsed date object or default
    """
    if not date_str:
        return default

    try:
        return datetime.fromisoformat(date_str).date()
    except (ValueError, AttributeError):
        return default


@computation_context_api_bp.route('/computation-context/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER', 'ADMIN')
def get_computation_context(field_id):
    """
    Get complete computation context for a computed field.

    Query Parameters:
        - entity_id (int): Entity ID for context
        - reporting_date (str): Date for calculation (ISO format YYYY-MM-DD)

    Returns:
        JSON response with:
        - success (bool): Whether the request was successful
        - context (dict): Complete computation context object
        - error (str): Error message if failed

    Example:
        GET /user/v2/api/computation-context/abc123?entity_id=1&reporting_date=2024-12-31

    Response:
        {
            "success": true,
            "context": {
                "field": {...},
                "formula": "Total Energy (kWh) ÷ Number of Facilities",
                "dependencies": [...],
                "dependency_tree": {...},
                "calculation_steps": [...],
                "current_values": {...},
                "missing_dependencies": [...],
                "historical_trend": [...],
                "calculation_status": "complete"
            }
        }
    """
    try:
        # Get query parameters
        entity_id = request.args.get('entity_id', type=int)
        reporting_date_str = request.args.get('reporting_date')

        # Validate parameters
        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'entity_id parameter is required'
            }), 400

        if not reporting_date_str:
            return jsonify({
                'success': False,
                'error': 'reporting_date parameter is required'
            }), 400

        # Parse reporting date
        reporting_date = parse_date_param(reporting_date_str)
        if not reporting_date:
            return jsonify({
                'success': False,
                'error': 'Invalid reporting_date format. Use YYYY-MM-DD'
            }), 400

        # Get computation context
        context = ComputationContextService.get_computation_context(
            field_id, entity_id, reporting_date
        )

        # Check if context retrieval was successful
        if not context.get('success', True):
            return jsonify(context), 404

        return jsonify({
            'success': True,
            'context': context
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to get computation context: {str(e)}'
        }), 500


@computation_context_api_bp.route('/dependency-tree/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER', 'ADMIN')
def get_dependency_tree(field_id):
    """
    Get hierarchical dependency tree for a computed field.

    Query Parameters:
        - entity_id (int): Entity ID for context
        - reporting_date (str): Date for calculation (ISO format YYYY-MM-DD)
        - max_depth (int): Maximum tree depth (default: 5)

    Returns:
        JSON response with:
        - success (bool): Whether the request was successful
        - tree (dict): Hierarchical dependency tree
        - error (str): Error message if failed

    Example:
        GET /user/v2/api/dependency-tree/abc123?entity_id=1&reporting_date=2024-12-31&max_depth=5

    Response:
        {
            "success": true,
            "tree": {
                "field_id": "abc123",
                "field_name": "Total Emissions",
                "value": 1000,
                "status": "available",
                "dependencies": [...]
            }
        }
    """
    try:
        # Get query parameters
        entity_id = request.args.get('entity_id', type=int)
        reporting_date_str = request.args.get('reporting_date')
        max_depth = request.args.get('max_depth', type=int, default=5)

        # Validate parameters
        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'entity_id parameter is required'
            }), 400

        if not reporting_date_str:
            return jsonify({
                'success': False,
                'error': 'reporting_date parameter is required'
            }), 400

        # Parse reporting date
        reporting_date = parse_date_param(reporting_date_str)
        if not reporting_date:
            return jsonify({
                'success': False,
                'error': 'Invalid reporting_date format. Use YYYY-MM-DD'
            }), 400

        # Validate max_depth
        if max_depth < 1 or max_depth > 10:
            return jsonify({
                'success': False,
                'error': 'max_depth must be between 1 and 10'
            }), 400

        # Build dependency tree
        tree = ComputationContextService.build_dependency_tree(
            field_id, entity_id, reporting_date, max_depth
        )

        return jsonify({
            'success': True,
            'tree': tree
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to build dependency tree: {str(e)}'
        }), 500


@computation_context_api_bp.route('/calculation-steps/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER', 'ADMIN')
def get_calculation_steps(field_id):
    """
    Get step-by-step calculation breakdown for a computed field.

    Query Parameters:
        - entity_id (int): Entity ID for context
        - reporting_date (str): Date for calculation (ISO format YYYY-MM-DD)

    Returns:
        JSON response with:
        - success (bool): Whether the request was successful
        - steps (list): List of calculation steps
        - error (str): Error message if failed

    Example:
        GET /user/v2/api/calculation-steps/abc123?entity_id=1&reporting_date=2024-12-31

    Response:
        {
            "success": true,
            "steps": [
                {
                    "step": 1,
                    "description": "Get value for Energy Consumption",
                    "operation": "FETCH",
                    "inputs": {...},
                    "output": 1000,
                    "unit": "kWh"
                },
                ...
            ]
        }
    """
    try:
        # Get query parameters
        entity_id = request.args.get('entity_id', type=int)
        reporting_date_str = request.args.get('reporting_date')

        # Validate parameters
        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'entity_id parameter is required'
            }), 400

        if not reporting_date_str:
            return jsonify({
                'success': False,
                'error': 'reporting_date parameter is required'
            }), 400

        # Parse reporting date
        reporting_date = parse_date_param(reporting_date_str)
        if not reporting_date:
            return jsonify({
                'success': False,
                'error': 'Invalid reporting_date format. Use YYYY-MM-DD'
            }), 400

        # Get calculation steps
        steps = ComputationContextService.get_calculation_steps(
            field_id, entity_id, reporting_date
        )

        return jsonify({
            'success': True,
            'steps': steps
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to get calculation steps: {str(e)}'
        }), 500


@computation_context_api_bp.route('/historical-trend/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER', 'ADMIN')
def get_historical_trend(field_id):
    """
    Get historical calculation trend for a computed field.

    Query Parameters:
        - entity_id (int): Entity ID for context
        - periods (int): Number of historical periods (default: 12)

    Returns:
        JSON response with:
        - success (bool): Whether the request was successful
        - trend (dict): Historical trend data
        - error (str): Error message if failed

    Example:
        GET /user/v2/api/historical-trend/abc123?entity_id=1&periods=12

    Response:
        {
            "success": true,
            "trend": {
                "field_id": "abc123",
                "entity_id": 1,
                "data_points": [
                    {
                        "date": "2024-01-01",
                        "value": 1000,
                        "status": "complete"
                    },
                    ...
                ],
                "trend": "increasing",
                "change_rate": 5.2
            }
        }
    """
    try:
        # Get query parameters
        entity_id = request.args.get('entity_id', type=int)
        periods = request.args.get('periods', type=int, default=12)

        # Validate parameters
        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'entity_id parameter is required'
            }), 400

        # Validate periods
        if periods < 1 or periods > 100:
            return jsonify({
                'success': False,
                'error': 'periods must be between 1 and 100'
            }), 400

        # Get historical trend
        trend = ComputationContextService.get_historical_calculation_trend(
            field_id, entity_id, periods
        )

        return jsonify({
            'success': True,
            'trend': trend
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to get historical trend: {str(e)}'
        }), 500


@computation_context_api_bp.route('/validate-dependencies/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER', 'ADMIN')
def validate_dependencies(field_id):
    """
    Check if all dependencies are satisfied for a computed field.

    Query Parameters:
        - entity_id (int): Entity ID for context
        - reporting_date (str): Date to check (ISO format YYYY-MM-DD)

    Returns:
        JSON response with:
        - success (bool): Whether the request was successful
        - validation (dict): Dependency validation results
        - error (str): Error message if failed

    Example:
        GET /user/v2/api/validate-dependencies/abc123?entity_id=1&reporting_date=2024-12-31

    Response:
        {
            "success": true,
            "validation": {
                "is_complete": true,
                "satisfied_count": 5,
                "total_count": 5,
                "missing": [],
                "completeness_percentage": 100.0
            }
        }
    """
    try:
        # Get query parameters
        entity_id = request.args.get('entity_id', type=int)
        reporting_date_str = request.args.get('reporting_date')

        # Validate parameters
        if not entity_id:
            return jsonify({
                'success': False,
                'error': 'entity_id parameter is required'
            }), 400

        if not reporting_date_str:
            return jsonify({
                'success': False,
                'error': 'reporting_date parameter is required'
            }), 400

        # Parse reporting date
        reporting_date = parse_date_param(reporting_date_str)
        if not reporting_date:
            return jsonify({
                'success': False,
                'error': 'Invalid reporting_date format. Use YYYY-MM-DD'
            }), 400

        # Validate dependencies
        validation = ComputationContextService.validate_dependencies(
            field_id, entity_id, reporting_date
        )

        return jsonify({
            'success': True,
            'validation': validation
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to validate dependencies: {str(e)}'
        }), 500
