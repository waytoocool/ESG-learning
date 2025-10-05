"""
Aggregation Service for User Dashboard V2
Handles data aggregation across dimensions and entities.
"""

from typing import Dict, List, Any, Optional
from app.models.esg_data import ESGData
from app.models.entity import Entity
from app.extensions import db
from flask_login import current_user
from sqlalchemy import func
from datetime import datetime, date


class AggregationService:
    """Service for data aggregation and calculations."""

    @staticmethod
    def aggregate_by_dimension(
        field_id: str,
        entity_id: int,
        dimension_name: str,
        reporting_date: str
    ) -> Dict[str, Any]:
        """
        Aggregate data by a specific dimension.

        Args:
            field_id: Framework field ID
            entity_id: Entity ID
            dimension_name: Name of dimension to aggregate by
            reporting_date: Reporting date

        Returns:
            Dictionary with aggregated values by dimension
        """
        # Get the ESG data entry
        esg_data = ESGData.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date,
            company_id=current_user.company_id
        ).first()

        if not esg_data or not esg_data.dimension_values:
            return {
                'success': False,
                'error': 'No dimensional data found'
            }

        dim_values = esg_data.dimension_values
        if dim_values.get('version') != 2:
            return {
                'success': False,
                'error': 'Incompatible data version'
            }

        # Check if the dimension exists in the data
        dimensions = dim_values.get('dimensions', [])
        if dimension_name not in dimensions:
            return {
                'success': False,
                'error': f'Dimension {dimension_name} not found in data'
            }

        # Get pre-calculated totals if available
        totals = dim_values.get('totals', {})
        by_dimension = totals.get('by_dimension', {})

        if dimension_name in by_dimension:
            return {
                'success': True,
                'dimension_name': dimension_name,
                'aggregated_values': by_dimension[dimension_name],
                'total': totals.get('overall', 0)
            }

        # If not pre-calculated, calculate from breakdowns
        breakdowns = dim_values.get('breakdowns', [])
        aggregated = {}

        for breakdown in breakdowns:
            dim_value = breakdown.get('dimensions', {}).get(dimension_name)
            if dim_value and breakdown.get('raw_value') is not None:
                try:
                    current = aggregated.get(dim_value, 0)
                    aggregated[dim_value] = current + float(breakdown.get('raw_value', 0))
                except (ValueError, TypeError):
                    continue

        return {
            'success': True,
            'dimension_name': dimension_name,
            'aggregated_values': aggregated,
            'total': sum(aggregated.values())
        }

    @staticmethod
    def calculate_cross_entity_totals(
        field_id: str,
        entity_ids: List[int],
        reporting_date: str,
        aggregate_dimensions: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate totals across multiple entities.

        Args:
            field_id: Framework field ID
            entity_ids: List of entity IDs to aggregate
            reporting_date: Reporting date
            aggregate_dimensions: Whether to aggregate dimensional data

        Returns:
            Dictionary with cross-entity totals
        """
        # Query all ESG data for the given entities
        esg_data_list = ESGData.query.filter(
            ESGData.field_id == field_id,
            ESGData.entity_id.in_(entity_ids),
            ESGData.reporting_date == reporting_date,
            ESGData.company_id == current_user.company_id
        ).all()

        if not esg_data_list:
            return {
                'success': False,
                'error': 'No data found for specified entities'
            }

        # Calculate simple total
        simple_total = 0
        entity_values = {}

        for data in esg_data_list:
            entity_name = data.entity.name if data.entity else f"Entity {data.entity_id}"

            if data.dimension_values and data.dimension_values.get('version') == 2:
                # Use overall total from dimensional data
                totals = data.dimension_values.get('totals', {})
                value = totals.get('overall', 0)
            elif data.raw_value:
                # Use raw value
                try:
                    value = float(data.raw_value)
                except (ValueError, TypeError):
                    value = 0
            else:
                value = 0

            simple_total += value
            entity_values[entity_name] = value

        result = {
            'success': True,
            'field_id': field_id,
            'reporting_date': reporting_date,
            'entity_count': len(esg_data_list),
            'total': simple_total,
            'by_entity': entity_values
        }

        # Add dimensional aggregation if requested
        if aggregate_dimensions:
            dimensional_aggregation = AggregationService._aggregate_dimensions_across_entities(
                esg_data_list
            )
            result['dimensional_aggregation'] = dimensional_aggregation

        return result

    @staticmethod
    def _aggregate_dimensions_across_entities(esg_data_list: List[ESGData]) -> Dict[str, Any]:
        """
        Aggregate dimensional data across multiple entities.

        Args:
            esg_data_list: List of ESGData records

        Returns:
            Dictionary with aggregated dimensional data
        """
        # Collect all dimensions
        all_dimensions = set()
        dimension_aggregates = {}

        for data in esg_data_list:
            if not data.dimension_values or data.dimension_values.get('version') != 2:
                continue

            dimensions = data.dimension_values.get('dimensions', [])
            all_dimensions.update(dimensions)

            # Aggregate by each dimension
            totals = data.dimension_values.get('totals', {})
            by_dimension = totals.get('by_dimension', {})

            for dim_name, dim_totals in by_dimension.items():
                if dim_name not in dimension_aggregates:
                    dimension_aggregates[dim_name] = {}

                for dim_value, value in dim_totals.items():
                    current = dimension_aggregates[dim_name].get(dim_value, 0)
                    dimension_aggregates[dim_name][dim_value] = current + value

        return {
            'dimensions': list(all_dimensions),
            'by_dimension': dimension_aggregates
        }

    @staticmethod
    def aggregate_historical_data(
        field_id: str,
        entity_id: int,
        start_date: str,
        end_date: str,
        dimension_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Aggregate data across a date range.

        Args:
            field_id: Framework field ID
            entity_id: Entity ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            dimension_name: Optional dimension to aggregate by

        Returns:
            Dictionary with historical aggregation
        """
        # Convert string dates to date objects
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Query historical data
        historical_data = ESGData.query.filter(
            ESGData.field_id == field_id,
            ESGData.entity_id == entity_id,
            ESGData.reporting_date >= start,
            ESGData.reporting_date <= end,
            ESGData.company_id == current_user.company_id
        ).order_by(ESGData.reporting_date).all()

        if not historical_data:
            return {
                'success': False,
                'error': 'No historical data found'
            }

        # Build time series
        time_series = []
        dimension_time_series = {}

        for data in historical_data:
            date_str = data.reporting_date.isoformat()

            # Get value
            if data.dimension_values and data.dimension_values.get('version') == 2:
                totals = data.dimension_values.get('totals', {})
                value = totals.get('overall', 0)

                # If specific dimension requested, get its breakdown
                if dimension_name:
                    by_dimension = totals.get('by_dimension', {})
                    if dimension_name in by_dimension:
                        for dim_value, dim_total in by_dimension[dimension_name].items():
                            if dim_value not in dimension_time_series:
                                dimension_time_series[dim_value] = []
                            dimension_time_series[dim_value].append({
                                'date': date_str,
                                'value': dim_total
                            })
            else:
                try:
                    value = float(data.raw_value) if data.raw_value else 0
                except (ValueError, TypeError):
                    value = 0

            time_series.append({
                'date': date_str,
                'value': value
            })

        result = {
            'success': True,
            'field_id': field_id,
            'entity_id': entity_id,
            'start_date': start_date,
            'end_date': end_date,
            'data_points': len(time_series),
            'time_series': time_series,
            'total': sum(point['value'] for point in time_series)
        }

        if dimension_time_series:
            result['dimension_time_series'] = dimension_time_series

        return result

    @staticmethod
    def calculate_completion_rate(
        field_id: str,
        entity_ids: List[int],
        reporting_date: str
    ) -> Dict[str, Any]:
        """
        Calculate completion rate for dimensional data.

        Args:
            field_id: Framework field ID
            entity_ids: List of entity IDs
            reporting_date: Reporting date

        Returns:
            Dictionary with completion statistics
        """
        esg_data_list = ESGData.query.filter(
            ESGData.field_id == field_id,
            ESGData.entity_id.in_(entity_ids),
            ESGData.reporting_date == reporting_date,
            ESGData.company_id == current_user.company_id
        ).all()

        total_entities = len(entity_ids)
        entities_with_data = len(esg_data_list)
        complete_entities = 0
        partial_entities = 0

        for data in esg_data_list:
            if data.dimension_values and data.dimension_values.get('version') == 2:
                metadata = data.dimension_values.get('metadata', {})
                if metadata.get('is_complete', False):
                    complete_entities += 1
                else:
                    partial_entities += 1
            elif data.raw_value:
                complete_entities += 1

        return {
            'total_entities': total_entities,
            'entities_with_data': entities_with_data,
            'complete_entities': complete_entities,
            'partial_entities': partial_entities,
            'missing_entities': total_entities - entities_with_data,
            'completion_rate': (complete_entities / total_entities * 100) if total_entities > 0 else 0,
            'data_rate': (entities_with_data / total_entities * 100) if total_entities > 0 else 0
        }

    @staticmethod
    def get_dimension_breakdown_summary(
        field_id: str,
        entity_id: int,
        reporting_date: str
    ) -> Dict[str, Any]:
        """
        Get a comprehensive summary of dimensional breakdowns.

        Args:
            field_id: Framework field ID
            entity_id: Entity ID
            reporting_date: Reporting date

        Returns:
            Dictionary with breakdown summary
        """
        esg_data = ESGData.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date,
            company_id=current_user.company_id
        ).first()

        if not esg_data or not esg_data.dimension_values:
            return {
                'success': False,
                'has_dimensions': False
            }

        dim_values = esg_data.dimension_values
        if dim_values.get('version') != 2:
            return {
                'success': False,
                'error': 'Incompatible data version'
            }

        dimensions = dim_values.get('dimensions', [])
        breakdowns = dim_values.get('breakdowns', [])
        totals = dim_values.get('totals', {})
        metadata = dim_values.get('metadata', {})

        # Build summary
        breakdown_summary = []
        for breakdown in breakdowns:
            breakdown_summary.append({
                'dimensions': breakdown.get('dimensions', {}),
                'value': breakdown.get('raw_value'),
                'notes': breakdown.get('notes'),
                'has_value': breakdown.get('raw_value') is not None
            })

        return {
            'success': True,
            'has_dimensions': True,
            'dimensions': dimensions,
            'total_combinations': metadata.get('total_combinations', 0),
            'completed_combinations': metadata.get('completed_combinations', 0),
            'is_complete': metadata.get('is_complete', False),
            'overall_total': totals.get('overall', 0),
            'by_dimension': totals.get('by_dimension', {}),
            'breakdowns': breakdown_summary,
            'last_updated': metadata.get('last_updated')
        }
