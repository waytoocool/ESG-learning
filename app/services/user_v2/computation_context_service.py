"""
Computation Context Service
============================

Service for providing contextual information about computed fields including
formulas, dependencies, calculation steps, and historical trends.

This service helps users understand how computed values are derived and
identify any data gaps or missing dependencies.

Author: Backend Developer Agent
Phase: 3 - Computation Context
Date: 2025-01-04
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from flask import current_app
from sqlalchemy import and_, or_, func

from ...models.framework import FrameworkDataField, FieldVariableMapping
from ...models.esg_data import ESGData
from ...models.entity import Entity
from ...models.data_assignment import DataPointAssignment
from ...extensions import db
from ..assignment_versioning import resolve_assignment


class ComputationContextService:
    """Service for handling computation context and dependency analysis."""

    @staticmethod
    def get_computation_context(field_id: str, entity_id: int, reporting_date: date) -> Dict[str, Any]:
        """
        Get complete computation context for a computed field.

        Args:
            field_id: ID of the computed field
            entity_id: Entity ID for context
            reporting_date: Date for which to get context

        Returns:
            Dictionary containing:
            - field: Field details
            - formula: User-friendly formula string
            - dependencies: List of dependent fields
            - dependency_tree: Hierarchical dependency structure
            - calculation_steps: Step-by-step breakdown
            - current_values: Field ID to value mapping
            - missing_dependencies: List of missing data
            - historical_trend: Historical values
            - last_calculated: Last calculation timestamp
            - calculation_status: 'complete'|'partial'|'failed'
        """
        try:
            # Get the computed field
            field = FrameworkDataField.query.get(field_id)
            if not field or not field.is_computed:
                return {
                    'success': False,
                    'error': 'Field not found or not a computed field'
                }

            # Get assignment for this field
            assignment = resolve_assignment(field_id, entity_id, reporting_date)
            if not assignment:
                return {
                    'success': False,
                    'error': 'No assignment found for this field'
                }

            # Build dependency tree
            dependency_tree = ComputationContextService.build_dependency_tree(
                field_id, entity_id, reporting_date
            )

            # Get calculation steps
            calculation_steps = ComputationContextService.get_calculation_steps(
                field_id, entity_id, reporting_date
            )

            # Validate dependencies
            validation = ComputationContextService.validate_dependencies(
                field_id, entity_id, reporting_date
            )

            # Get historical trend
            historical_trend = ComputationContextService.get_historical_calculation_trend(
                field_id, entity_id, periods=12
            )

            # Format formula for display
            readable_formula = ComputationContextService.format_formula_for_display(
                field.formula_expression, field_id
            )

            # Get current values
            current_values = {}
            for mapping in field.variable_mappings:
                dep_data = ESGData.query.filter(
                    ESGData.field_id == mapping.raw_field_id,
                    ESGData.entity_id == entity_id,
                    ESGData.reporting_date <= reporting_date
                ).order_by(ESGData.reporting_date.desc()).first()

                if dep_data:
                    current_values[mapping.raw_field_id] = {
                        'value': dep_data.raw_value,
                        'date': dep_data.reporting_date.isoformat(),
                        'variable': mapping.variable_name
                    }

            # Check if computed value exists
            computed_data = ESGData.query.filter(
                ESGData.field_id == field_id,
                ESGData.entity_id == entity_id,
                ESGData.reporting_date == reporting_date
            ).first()

            # Determine calculation status
            if validation['is_complete']:
                calculation_status = 'complete'
            elif validation['satisfied_count'] > 0:
                calculation_status = 'partial'
            else:
                calculation_status = 'failed'

            return {
                'success': True,
                'field': {
                    'field_id': field.field_id,
                    'field_name': field.field_name,
                    'field_code': field.field_code,
                    'description': field.description,
                    'unit': field.default_unit,
                    'is_computed': field.is_computed
                },
                'formula': readable_formula,
                'dependencies': [
                    {
                        'field_id': mapping.raw_field_id,
                        'field_name': mapping.raw_field.field_name,
                        'variable_name': mapping.variable_name,
                        'coefficient': mapping.coefficient
                    }
                    for mapping in field.variable_mappings
                ],
                'dependency_tree': dependency_tree,
                'calculation_steps': calculation_steps,
                'current_values': current_values,
                'missing_dependencies': validation['missing'],
                'historical_trend': historical_trend,  # Return full object with data_points, trend, change_rate
                'last_calculated': computed_data.updated_at.isoformat() if computed_data else None,
                'calculation_status': calculation_status,
                'validation': validation
            }

        except Exception as e:
            current_app.logger.error(f'Error getting computation context: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def build_dependency_tree(field_id: str, entity_id: int, reporting_date: date,
                            max_depth: int = 5, current_depth: int = 0) -> Dict[str, Any]:
        """
        Build hierarchical dependency tree for a computed field.

        Args:
            field_id: ID of the field
            entity_id: Entity ID
            reporting_date: Date for context
            max_depth: Maximum recursion depth
            current_depth: Current recursion level

        Returns:
            Dictionary with:
            - field_id: Field identifier
            - field_name: Human-readable name
            - value: Current value
            - status: 'available'|'missing'|'partial'
            - dependencies: Recursive list of dependencies
        """
        try:
            # Prevent infinite recursion
            if current_depth >= max_depth:
                return {
                    'field_id': field_id,
                    'field_name': 'Max depth reached',
                    'status': 'unknown',
                    'dependencies': []
                }

            # Get field
            field = FrameworkDataField.query.get(field_id)
            if not field:
                return {
                    'field_id': field_id,
                    'field_name': 'Unknown field',
                    'status': 'missing',
                    'dependencies': []
                }

            # Get current value
            data = ESGData.query.filter(
                ESGData.field_id == field_id,
                ESGData.entity_id == entity_id,
                ESGData.reporting_date == reporting_date
            ).first()

            value = data.raw_value if data else None
            status = 'available' if value is not None else 'missing'

            # Build tree node
            node = {
                'field_id': field.field_id,
                'field_name': field.field_name,
                'field_code': field.field_code,
                'value': value,
                'unit': field.default_unit,
                'status': status,
                'is_computed': field.is_computed,
                'dependencies': []
            }

            # If this is a computed field, recursively get dependencies
            if field.is_computed:
                for mapping in field.variable_mappings:
                    dependency_node = ComputationContextService.build_dependency_tree(
                        mapping.raw_field_id,
                        entity_id,
                        reporting_date,
                        max_depth,
                        current_depth + 1
                    )
                    dependency_node['variable_name'] = mapping.variable_name
                    dependency_node['coefficient'] = mapping.coefficient
                    node['dependencies'].append(dependency_node)

                # Update status based on dependencies
                if node['dependencies']:
                    dep_statuses = [dep['status'] for dep in node['dependencies']]
                    if all(s == 'available' for s in dep_statuses):
                        node['status'] = 'available'
                    elif any(s == 'available' for s in dep_statuses):
                        node['status'] = 'partial'
                    else:
                        node['status'] = 'missing'

            return node

        except Exception as e:
            current_app.logger.error(f'Error building dependency tree: {str(e)}')
            return {
                'field_id': field_id,
                'field_name': 'Error',
                'status': 'error',
                'error': str(e),
                'dependencies': []
            }

    @staticmethod
    def get_calculation_steps(field_id: str, entity_id: int, reporting_date: date) -> List[Dict[str, Any]]:
        """
        Break down calculation into step-by-step process.

        Args:
            field_id: ID of the computed field
            entity_id: Entity ID
            reporting_date: Date for calculation

        Returns:
            List of dictionaries with:
            - step: Step number
            - description: Human-readable description
            - operation: Operation type
            - inputs: Input values
            - output: Step output
            - unit: Unit of measurement
        """
        try:
            field = FrameworkDataField.query.get(field_id)
            if not field or not field.is_computed:
                return []

            steps = []
            step_number = 1

            # Step 1: Gather dependency values
            dependency_values = {}
            for mapping in field.variable_mappings:
                dep_field = mapping.raw_field
                assignment = resolve_assignment(mapping.raw_field_id, entity_id, reporting_date)

                if assignment:
                    # Get aggregation period based on frequency
                    if assignment.frequency == 'Annual':
                        company = assignment.company
                        fy_year = reporting_date.year if reporting_date.month >= company.get_fy_start_month() else reporting_date.year - 1
                        period_start = company.get_fy_start_date(fy_year)
                        period_end = min(company.get_fy_end_date(fy_year), reporting_date)
                    else:
                        period_start = reporting_date - relativedelta(months=1)
                        period_end = reporting_date

                    # Get values in period
                    values = ESGData.query.filter(
                        ESGData.field_id == mapping.raw_field_id,
                        ESGData.entity_id == entity_id,
                        ESGData.reporting_date >= period_start,
                        ESGData.reporting_date <= period_end,
                        ESGData.raw_value.isnot(None)
                    ).order_by(ESGData.reporting_date).all()

                    if values:
                        # For now, use latest value (can be enhanced with aggregation logic)
                        latest_value = float(values[-1].raw_value) if values[-1].raw_value else 0
                        dependency_values[mapping.variable_name] = latest_value * mapping.coefficient

                        steps.append({
                            'step': step_number,
                            'description': f'Get value for {dep_field.field_name}',
                            'operation': 'FETCH',
                            'inputs': {
                                'field': dep_field.field_name,
                                'period': f'{period_start.isoformat()} to {period_end.isoformat()}',
                                'values_count': len(values)
                            },
                            'output': latest_value,
                            'unit': dep_field.default_unit,
                            'details': f'Retrieved {len(values)} value(s), using latest: {latest_value}'
                        })
                        step_number += 1

                        # If coefficient is applied
                        if mapping.coefficient != 1.0:
                            steps.append({
                                'step': step_number,
                                'description': f'Apply coefficient to {mapping.variable_name}',
                                'operation': 'MULTIPLY',
                                'inputs': {
                                    'value': latest_value,
                                    'coefficient': mapping.coefficient
                                },
                                'output': latest_value * mapping.coefficient,
                                'unit': dep_field.default_unit,
                                'details': f'{latest_value} × {mapping.coefficient} = {latest_value * mapping.coefficient}'
                            })
                            step_number += 1

            # Step: Evaluate formula
            if dependency_values:
                formula = field.formula_expression
                computed_formula = formula

                for var_name, value in dependency_values.items():
                    computed_formula = computed_formula.replace(var_name, str(value))

                try:
                    result = eval(computed_formula)
                    steps.append({
                        'step': step_number,
                        'description': f'Calculate formula: {formula}',
                        'operation': 'FORMULA',
                        'inputs': dependency_values,
                        'output': result,
                        'unit': field.default_unit,
                        'details': f'{formula} = {computed_formula} = {result}'
                    })
                    step_number += 1

                    # Apply constant multiplier if present
                    if field.constant_multiplier and field.constant_multiplier != 1.0:
                        final_result = result * field.constant_multiplier
                        steps.append({
                            'step': step_number,
                            'description': 'Apply constant multiplier',
                            'operation': 'MULTIPLY',
                            'inputs': {
                                'value': result,
                                'multiplier': field.constant_multiplier
                            },
                            'output': final_result,
                            'unit': field.default_unit,
                            'details': f'{result} × {field.constant_multiplier} = {final_result}'
                        })

                except Exception as e:
                    steps.append({
                        'step': step_number,
                        'description': 'Formula evaluation failed',
                        'operation': 'ERROR',
                        'inputs': dependency_values,
                        'output': None,
                        'unit': None,
                        'details': f'Error: {str(e)}'
                    })

            return steps

        except Exception as e:
            current_app.logger.error(f'Error getting calculation steps: {str(e)}')
            return [{
                'step': 1,
                'description': 'Error generating calculation steps',
                'operation': 'ERROR',
                'inputs': {},
                'output': None,
                'unit': None,
                'details': str(e)
            }]

    @staticmethod
    def format_formula_for_display(formula_expression: str, field_id: str) -> str:
        """
        Convert technical formula to user-friendly format.

        Args:
            formula_expression: Technical formula like "(A + B) / C"
            field_id: ID of the computed field

        Returns:
            User-friendly formula string
        """
        try:
            if not formula_expression:
                return "No formula defined"

            field = FrameworkDataField.query.get(field_id)
            if not field:
                return formula_expression

            # Create a readable version by replacing variables with field names
            readable = formula_expression
            for mapping in field.variable_mappings:
                dep_field = mapping.raw_field
                field_label = f"{dep_field.field_name}"
                if mapping.coefficient != 1.0:
                    field_label = f"({mapping.coefficient} × {field_label})"
                readable = readable.replace(mapping.variable_name, field_label)

            # Replace operators with symbols
            readable = readable.replace('*', ' × ')
            readable = readable.replace('/', ' ÷ ')
            readable = readable.replace('+', ' + ')
            readable = readable.replace('-', ' − ')

            # Add constant multiplier if present
            if field.constant_multiplier and field.constant_multiplier != 1.0:
                readable = f"({readable}) × {field.constant_multiplier}"

            return readable

        except Exception as e:
            current_app.logger.error(f'Error formatting formula: {str(e)}')
            return formula_expression

    @staticmethod
    def get_historical_calculation_trend(field_id: str, entity_id: int, periods: int = 12) -> Dict[str, Any]:
        """
        Get historical trend of calculated values.

        Args:
            field_id: ID of the computed field
            entity_id: Entity ID
            periods: Number of historical periods to retrieve

        Returns:
            Dictionary with:
            - field_id: Field identifier
            - entity_id: Entity identifier
            - data_points: List of historical values
            - trend: 'increasing'|'decreasing'|'stable'
            - change_rate: Percentage change
        """
        try:
            field = FrameworkDataField.query.get(field_id)
            if not field:
                return {
                    'field_id': field_id,
                    'entity_id': entity_id,
                    'data_points': [],
                    'trend': 'unknown',
                    'change_rate': 0
                }

            # Get historical data
            historical_data = ESGData.query.filter(
                ESGData.field_id == field_id,
                ESGData.entity_id == entity_id,
                ESGData.raw_value.isnot(None)
            ).order_by(ESGData.reporting_date.desc()).limit(periods).all()

            # Reverse to get chronological order
            historical_data = list(reversed(historical_data))

            data_points = []
            for data in historical_data:
                try:
                    value = float(data.raw_value) if data.raw_value else None
                    data_points.append({
                        'date': data.reporting_date.isoformat(),
                        'value': value,
                        'status': 'complete' if value is not None else 'missing',
                        'calculation_time': data.updated_at.isoformat() if data.updated_at else None
                    })
                except (ValueError, TypeError):
                    data_points.append({
                        'date': data.reporting_date.isoformat(),
                        'value': None,
                        'status': 'invalid',
                        'calculation_time': None
                    })

            # Calculate trend
            trend = 'stable'
            change_rate = 0

            if len(data_points) >= 2:
                values = [dp['value'] for dp in data_points if dp['value'] is not None]
                if len(values) >= 2:
                    first_value = values[0]
                    last_value = values[-1]

                    if first_value != 0:
                        change_rate = ((last_value - first_value) / first_value) * 100

                        if change_rate > 5:
                            trend = 'increasing'
                        elif change_rate < -5:
                            trend = 'decreasing'
                        else:
                            trend = 'stable'

            return {
                'field_id': field_id,
                'entity_id': entity_id,
                'data_points': data_points,
                'trend': trend,
                'change_rate': round(change_rate, 2)
            }

        except Exception as e:
            current_app.logger.error(f'Error getting historical trend: {str(e)}')
            return {
                'field_id': field_id,
                'entity_id': entity_id,
                'data_points': [],
                'trend': 'error',
                'change_rate': 0,
                'error': str(e)
            }

    @staticmethod
    def validate_dependencies(field_id: str, entity_id: int, reporting_date: date) -> Dict[str, Any]:
        """
        Check if all dependencies are satisfied.

        Args:
            field_id: ID of the computed field
            entity_id: Entity ID
            reporting_date: Date to check

        Returns:
            Dictionary with:
            - is_complete: True if all dependencies satisfied
            - satisfied_count: Number of satisfied dependencies
            - total_count: Total number of dependencies
            - missing: List of missing dependencies
        """
        try:
            field = FrameworkDataField.query.get(field_id)
            if not field or not field.is_computed:
                return {
                    'is_complete': False,
                    'satisfied_count': 0,
                    'total_count': 0,
                    'missing': []
                }

            total_count = len(field.variable_mappings)
            satisfied_count = 0
            missing = []

            for mapping in field.variable_mappings:
                dep_field = mapping.raw_field

                # Check if assignment exists
                assignment = resolve_assignment(mapping.raw_field_id, entity_id, reporting_date)
                if not assignment:
                    missing.append({
                        'field_id': mapping.raw_field_id,
                        'field_name': dep_field.field_name,
                        'reason': 'No assignment found for this field'
                    })
                    continue

                # Check if data exists
                data = ESGData.query.filter(
                    ESGData.field_id == mapping.raw_field_id,
                    ESGData.entity_id == entity_id,
                    ESGData.reporting_date <= reporting_date,
                    ESGData.raw_value.isnot(None)
                ).first()

                if data:
                    satisfied_count += 1
                else:
                    missing.append({
                        'field_id': mapping.raw_field_id,
                        'field_name': dep_field.field_name,
                        'reason': 'No data submitted for this period'
                    })

            return {
                'is_complete': satisfied_count == total_count,
                'satisfied_count': satisfied_count,
                'total_count': total_count,
                'missing': missing,
                'completeness_percentage': (satisfied_count / total_count * 100) if total_count > 0 else 0
            }

        except Exception as e:
            current_app.logger.error(f'Error validating dependencies: {str(e)}')
            return {
                'is_complete': False,
                'satisfied_count': 0,
                'total_count': 0,
                'missing': [],
                'error': str(e)
            }
