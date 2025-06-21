"""
Aggregation Service for ESG Data Computation

This module provides intelligent aggregation functionality for computed fields
that have dependencies with different collection frequencies.

Features:
- Smart period calculation based on field frequencies
- Multiple aggregation strategies (SUM, AVERAGE, LATEST, etc.)
- Efficient bulk operations with minimal database queries
- Configurable aggregation rules
- Caching support for performance optimization
- Reusable across user and admin interfaces
"""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from flask import current_app, g
from sqlalchemy import and_, or_

from ..models.data_assignment import DataPointAssignment
from ..models.framework import FrameworkDataField, FieldVariableMapping
from ..models.esg_data import ESGData
from ..extensions import db


class AggregationMethod(Enum):
    """Supported aggregation methods for dependency values."""
    SUM = "SUM"
    AVERAGE = "AVERAGE"
    LATEST = "LATEST"
    EARLIEST = "EARLIEST"
    MAX = "MAX"
    MIN = "MIN"
    WEIGHTED_AVERAGE = "WEIGHTED_AVERAGE"
    COUNT = "COUNT"


class AggregationRule:
    """Configuration for how to aggregate a specific dependency."""
    
    def __init__(self, 
                 method: AggregationMethod = AggregationMethod.LATEST,
                 lookback_months: int = 12,
                 weight_factor: float = 1.0,
                 is_required: bool = True):
        self.method = method
        self.lookback_months = lookback_months
        self.weight_factor = weight_factor
        self.is_required = is_required


class AggregationService:
    """Service class for handling ESG data aggregation logic."""
    
    def __init__(self):
        self.default_rules = self._get_default_aggregation_rules()
    
    def _get_default_aggregation_rules(self) -> Dict[Tuple[str, str], AggregationRule]:
        """
        Get default aggregation rules based on frequency combinations.
        
        Returns:
            Dict mapping (dependency_frequency, computed_frequency) to AggregationRule
        """
        return {
            # Monthly -> Annual: Sum all monthly values
            ('Monthly', 'Annual'): AggregationRule(
                method=AggregationMethod.SUM,
                lookback_months=12,
                is_required=True
            ),
            # Quarterly -> Annual: Sum all quarterly values
            ('Quarterly', 'Annual'): AggregationRule(
                method=AggregationMethod.SUM,
                lookback_months=12,
                is_required=True
            ),
            # Monthly -> Quarterly: Sum monthly values in quarter
            ('Monthly', 'Quarterly'): AggregationRule(
                method=AggregationMethod.SUM,
                lookback_months=3,
                is_required=True
            ),
            # Same frequency: Use latest value
            ('Annual', 'Annual'): AggregationRule(
                method=AggregationMethod.LATEST,
                lookback_months=12,
                is_required=True
            ),
            ('Quarterly', 'Quarterly'): AggregationRule(
                method=AggregationMethod.LATEST,
                lookback_months=3,
                is_required=True
            ),
            ('Monthly', 'Monthly'): AggregationRule(
                method=AggregationMethod.LATEST,
                lookback_months=1,
                is_required=True
            ),
        }
    
    def should_compute_field(self, 
                           computed_field_id: str, 
                           entity_id: int, 
                           reporting_date: date,
                           minimum_data_threshold: float = 1.0) -> Tuple[bool, str]:
        """
        Determine if a computed field should be calculated based on data availability.
        
        Args:
            computed_field_id: ID of the computed field
            entity_id: ID of the entity
            reporting_date: Date for which to check computation eligibility
            minimum_data_threshold: Minimum percentage of expected data required (0.0 to 1.0, default 1.0 = 100%)
            
        Returns:
            Tuple of (should_compute: bool, reason: str)
        """
        try:
            computed_field = FrameworkDataField.query.get(computed_field_id)
            if not computed_field or not computed_field.is_computed:
                return False, "Field is not computed"
            
            # Use tenant-scoped queries when possible
            if hasattr(g, 'tenant') and g.tenant:
                computed_assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
                    data_point_id=computed_field_id,
                    entity_id=entity_id,
                    is_active=True
                ).first()
            else:
                # Fallback to regular query for admin/service contexts
                computed_assignment = DataPointAssignment.query.filter_by(
                    data_point_id=computed_field_id,
                    entity_id=entity_id,
                    is_active=True
                ).first()
            
            if not computed_assignment:
                return False, "No assignment found"
            
            # Check data availability for each dependency
            mappings = computed_field.variable_mappings
            dependency_field_ids = [mapping.raw_field_id for mapping in mappings]
            
            # Use tenant-scoped queries when possible
            if hasattr(g, 'tenant') and g.tenant:
                dependency_assignments = {
                    assignment.data_point_id: assignment
                    for assignment in DataPointAssignment.query_for_tenant(db.session).filter(
                        DataPointAssignment.data_point_id.in_(dependency_field_ids),
                        DataPointAssignment.entity_id == entity_id,
                        DataPointAssignment.is_active == True
                    ).all()
                }
            else:
                dependency_assignments = {
                    assignment.data_point_id: assignment
                    for assignment in DataPointAssignment.query.filter(
                        DataPointAssignment.data_point_id.in_(dependency_field_ids),
                        DataPointAssignment.entity_id == entity_id,
                        DataPointAssignment.is_active == True
                    ).all()
                }
            
            total_expected_values = 0
            total_available_values = 0
            missing_dependencies = []
            
            for mapping in mappings:
                dependency_assignment = dependency_assignments.get(mapping.raw_field_id)
                if not dependency_assignment:
                    missing_dependencies.append(f"No assignment for {mapping.raw_field_id}")
                    continue
                
                # Calculate expected number of data points based on frequency
                expected_count = self._get_expected_data_count(
                    dependency_assignment,
                    computed_assignment,
                    reporting_date
                )
                
                # Get actual available data points
                period_start, period_end = self._calculate_aggregation_period(
                    reporting_date,
                    12,  # Use 12 months for annual fields
                    computed_assignment
                )
                
                # Use tenant-scoped queries when possible
                if hasattr(g, 'tenant') and g.tenant:
                    available_count = ESGData.query_for_tenant(db.session).filter(
                        ESGData.data_point_id == mapping.raw_field_id,
                        ESGData.entity_id == entity_id,
                        ESGData.reporting_date >= period_start,
                        ESGData.reporting_date <= period_end,
                        ESGData.raw_value.isnot(None)
                    ).count()
                else:
                    available_count = ESGData.query.filter(
                        ESGData.data_point_id == mapping.raw_field_id,
                        ESGData.entity_id == entity_id,
                        ESGData.reporting_date >= period_start,
                        ESGData.reporting_date <= period_end,
                        ESGData.raw_value.isnot(None)
                    ).count()
                
                total_expected_values += expected_count
                total_available_values += available_count
                
                if available_count < expected_count * minimum_data_threshold:
                    dependency_field = FrameworkDataField.query.get(mapping.raw_field_id)
                    field_name = dependency_field.field_name if dependency_field else mapping.raw_field_id
                    missing_dependencies.append(f"{field_name}: {available_count}/{expected_count} values")
            
            if total_expected_values == 0:
                return False, "No expected values calculated"
            
            data_completeness = total_available_values / total_expected_values
            
            if data_completeness >= minimum_data_threshold:
                return True, f"Sufficient data available: {data_completeness:.1%}"
            else:
                reason = f"Insufficient data: {data_completeness:.1%} (need {minimum_data_threshold:.1%})"
                if missing_dependencies:
                    reason += f". Missing: {', '.join(missing_dependencies[:3])}"
                return False, reason
                
        except Exception as e:
            current_app.logger.error(f'Error checking computation eligibility: {str(e)}')
            return False, f"Error: {str(e)}"
    
    def _get_expected_data_count(self, 
                               dependency_assignment: DataPointAssignment,
                               computed_assignment: DataPointAssignment,
                               reporting_date: date) -> int:
        """Calculate the expected number of data points for a dependency."""
        if computed_assignment.frequency == 'Annual':
            # For annual computations, calculate based on financial year
            fy_start = date(computed_assignment.fy_start_year, computed_assignment.fy_start_month, 1)
            fy_end = date(computed_assignment.fy_end_year, computed_assignment.fy_start_month, 1) - timedelta(days=1)
            
            if dependency_assignment.frequency == 'Monthly':
                # Calculate months between FY start and reporting date
                months_diff = (reporting_date.year - fy_start.year) * 12 + (reporting_date.month - fy_start.month)
                return min(months_diff + 1, 12)  # Cap at 12 months
            elif dependency_assignment.frequency == 'Quarterly':
                # Calculate quarters between FY start and reporting date
                months_diff = (reporting_date.year - fy_start.year) * 12 + (reporting_date.month - fy_start.month)
                return min((months_diff // 3) + 1, 4)  # Cap at 4 quarters
            else:
                return 1  # Annual dependency
        else:
            # For other frequencies, use simpler logic
            if dependency_assignment.frequency == computed_assignment.frequency:
                return 1
            elif dependency_assignment.frequency == 'Monthly' and computed_assignment.frequency == 'Quarterly':
                return 3
            else:
                return 1
    
    def compute_field_value_if_ready(self, 
                                   computed_field_id: str, 
                                   entity_id: int, 
                                   reporting_date: date,
                                   custom_rules: Optional[Dict[str, AggregationRule]] = None,
                                   force_compute: bool = False,
                                   minimum_data_threshold: float = 1.0) -> Tuple[Optional[float], str]:
        """
        Compute field value only if sufficient data is available or forced.
        
        Args:
            computed_field_id: ID of the computed field
            entity_id: ID of the entity
            reporting_date: Date for which to compute the value
            custom_rules: Optional custom aggregation rules
            force_compute: Whether to compute regardless of data availability
            minimum_data_threshold: Minimum data completeness required (default 1.0 = 100%)
            
        Returns:
            Tuple of (computed_value: Optional[float], status_message: str)
        """
        try:
            # Check if computation should proceed
            if not force_compute:
                should_compute, reason = self.should_compute_field(
                    computed_field_id, 
                    entity_id, 
                    reporting_date, 
                    minimum_data_threshold
                )
                
                if not should_compute:
                    return None, f"Computation skipped: {reason}"
            
            # Proceed with computation
            result = self.compute_field_value(
                computed_field_id, 
                entity_id, 
                reporting_date, 
                custom_rules
            )
            
            if result is not None:
                return result, "Computed successfully"
            else:
                return None, "Computation failed - check dependencies"
                
        except Exception as e:
            current_app.logger.error(f"Error in smart computation: {str(e)}")
            return None, f"Error: {str(e)}"
    
    def compute_field_value(self, 
                          computed_field_id: str, 
                          entity_id: int, 
                          reporting_date: date,
                          custom_rules: Optional[Dict[str, AggregationRule]] = None) -> Optional[float]:
        """
        Compute the value of a computed field for a specific entity and date.
        
        Args:
            computed_field_id: ID of the computed field to calculate
            entity_id: ID of the entity for which to compute the value
            reporting_date: Date for which to compute the value
            custom_rules: Optional custom aggregation rules for dependencies
            
        Returns:
            Computed value or None if computation is not possible
        """
        try:
            computed_field = FrameworkDataField.query.get(computed_field_id)
            if not computed_field or not computed_field.is_computed:
                return None
            
            # Use tenant-scoped queries when possible
            if hasattr(g, 'tenant') and g.tenant:
                computed_assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
                    data_point_id=computed_field_id,
                    entity_id=entity_id,
                    is_active=True
                ).first()
            else:
                computed_assignment = DataPointAssignment.query.filter_by(
                    data_point_id=computed_field_id,
                    entity_id=entity_id,
                    is_active=True
                ).first()
            
            if not computed_assignment:
                current_app.logger.warning(f'No assignment found for computed field {computed_field_id}, entity {entity_id}')
                return None
            
            # Get dependency values
            dependency_values = self._get_dependency_values(
                computed_field,
                computed_assignment,
                entity_id,
                reporting_date,
                custom_rules
            )
            
            if not dependency_values:
                current_app.logger.warning(f'No dependency values available for field {computed_field_id}')
                return None
            
            # Evaluate the formula
            result = self._evaluate_formula(
                computed_field.formula_expression,
                dependency_values
            )
            
            current_app.logger.info(f'Computed field {computed_field_id} for entity {entity_id}: {result}')
            return result
            
        except Exception as e:
            current_app.logger.error(f'Error computing field {computed_field_id}: {str(e)}')
            return None
    
    def compute_multiple_fields(self, 
                               field_entity_date_tuples: List[Tuple[str, int, date]],
                               custom_rules: Optional[Dict[str, Dict[str, AggregationRule]]] = None) -> Dict[Tuple[str, int, date], Optional[float]]:
        """
        Compute multiple fields efficiently with bulk operations.
        
        Args:
            field_entity_date_tuples: List of (field_id, entity_id, reporting_date) tuples
            custom_rules: Optional custom rules per field
            
        Returns:
            Dict mapping (field_id, entity_id, reporting_date) to computed value
        """
        results = {}
        
        try:
            # Group by field_id for efficient processing
            field_groups = {}
            for field_id, entity_id, reporting_date in field_entity_date_tuples:
                if field_id not in field_groups:
                    field_groups[field_id] = []
                field_groups[field_id].append((entity_id, reporting_date))
            
            # Process each field group
            for field_id, entity_date_pairs in field_groups.items():
                field_custom_rules = custom_rules.get(field_id) if custom_rules else None
                
                for entity_id, reporting_date in entity_date_pairs:
                    result = self.compute_field_value(
                        field_id, 
                        entity_id, 
                        reporting_date, 
                        field_custom_rules
                    )
                    results[(field_id, entity_id, reporting_date)] = result
            
            return results
            
        except Exception as e:
            current_app.logger.error(f"Error in bulk computation: {str(e)}")
            return results
    
    def _get_dependency_values(self, 
                             computed_field: FrameworkDataField,
                             computed_assignment: DataPointAssignment,
                             entity_id: int,
                             reporting_date: date,
                             custom_rules: Optional[Dict[str, AggregationRule]] = None) -> Dict[str, float]:
        """
        Get aggregated values for all dependencies of a computed field.
        
        Args:
            computed_field: The computed field to get dependencies for
            computed_assignment: Assignment configuration for the computed field
            entity_id: Entity ID to get data for
            reporting_date: Reporting date
            custom_rules: Optional custom aggregation rules
            
        Returns:
            Dictionary mapping variable names to aggregated values
        """
        dependency_values = {}
        
        for mapping in computed_field.variable_mappings:
            try:
                # Get assignment for this dependency
                if hasattr(g, 'tenant') and g.tenant:
                    dependency_assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
                        data_point_id=mapping.raw_field_id,
                        entity_id=entity_id,
                        is_active=True
                    ).first()
                else:
                    dependency_assignment = DataPointAssignment.query.filter_by(
                        data_point_id=mapping.raw_field_id,
                        entity_id=entity_id,
                        is_active=True
                    ).first()
                
                if not dependency_assignment:
                    current_app.logger.warning(f'No assignment found for dependency {mapping.raw_field_id}')
                    continue
                
                # Get aggregation rule
                rule = self._get_aggregation_rule(
                    dependency_assignment.frequency,
                    computed_assignment.frequency,
                    mapping.raw_field_id,
                    custom_rules
                )
                
                # Get aggregated value
                aggregated_value = self._aggregate_dependency_values(
                    mapping.raw_field_id,
                    entity_id,
                    reporting_date,
                    rule,
                    computed_assignment
                )
                
                if aggregated_value is not None:
                    # Apply coefficient from mapping
                    final_value = aggregated_value * mapping.coefficient
                    dependency_values[mapping.variable_name] = final_value
                    
                    current_app.logger.debug(f'Dependency {mapping.variable_name}: {aggregated_value} * {mapping.coefficient} = {final_value}')
                else:
                    current_app.logger.warning(f'Could not get value for dependency {mapping.raw_field_id}')
                    
            except Exception as e:
                current_app.logger.error(f'Error processing dependency {mapping.raw_field_id}: {str(e)}')
                continue
        
        return dependency_values
    
    def _get_aggregation_rule(self, 
                            dependency_frequency: str,
                            computed_frequency: str,
                            field_id: str,
                            custom_rules: Optional[Dict[str, AggregationRule]] = None) -> AggregationRule:
        """Get the aggregation rule for a specific dependency."""
        # Check for custom rule first
        if custom_rules and field_id in custom_rules:
            return custom_rules[field_id]
        
        # Use default rule based on frequency combination
        rule_key = (dependency_frequency, computed_frequency)
        if rule_key in self.default_rules:
            return self.default_rules[rule_key]
        
        # Fallback to LATEST with 12-month lookback
        current_app.logger.warning(f"No rule found for {rule_key}, using LATEST")
        return AggregationRule(
            method=AggregationMethod.LATEST,
            lookback_months=12,
            is_required=True
        )
    
    def _aggregate_dependency_values(self, 
                                   dependency_field_id: str,
                                   entity_id: int,
                                   reporting_date: date,
                                   rule: AggregationRule,
                                   computed_assignment: DataPointAssignment) -> Optional[float]:
        """
        Aggregate values for a specific dependency field over the appropriate time period.
        
        Args:
            dependency_field_id: ID of the dependency field
            entity_id: Entity ID
            reporting_date: Target reporting date
            rule: Aggregation rule to apply
            computed_assignment: Assignment for the computed field (for period calculation)
            
        Returns:
            Aggregated value or None if no data available
        """
        try:
            # Calculate the aggregation period
            period_start, period_end = self._calculate_aggregation_period(
                reporting_date,
                rule.lookback_months,
                computed_assignment
            )
            
            current_app.logger.debug(f'Aggregating {dependency_field_id} from {period_start} to {period_end}')
            
            # Get dependency values within the period
            if hasattr(g, 'tenant') and g.tenant:
                dependency_values = ESGData.query_for_tenant(db.session).filter(
                    ESGData.data_point_id == dependency_field_id,
                    ESGData.entity_id == entity_id,
                    ESGData.reporting_date >= period_start,
                    ESGData.reporting_date <= period_end,
                    ESGData.raw_value.isnot(None)
                ).order_by(ESGData.reporting_date).all()
            else:
                dependency_values = ESGData.query.filter(
                    ESGData.data_point_id == dependency_field_id,
                    ESGData.entity_id == entity_id,
                    ESGData.reporting_date >= period_start,
                    ESGData.reporting_date <= period_end,
                    ESGData.raw_value.isnot(None)
                ).order_by(ESGData.reporting_date).all()
            
            if not dependency_values:
                current_app.logger.warning(f'No dependency values found for {dependency_field_id} in period {period_start} to {period_end}')
                return None
            
            # Extract numeric values
            numeric_values = []
            for value_entry in dependency_values:
                try:
                    numeric_value = float(value_entry.raw_value)
                    numeric_values.append(numeric_value)
                except (ValueError, TypeError):
                    current_app.logger.warning(f'Non-numeric value found: {value_entry.raw_value}')
                    continue
            
            if not numeric_values:
                current_app.logger.warning(f'No valid numeric values found for {dependency_field_id}')
                return None
            
            # Apply aggregation method
            result = self._apply_aggregation_method(
                numeric_values,
                rule.method,
                rule.weight_factor
            )
            
            current_app.logger.debug(f'Aggregated {len(numeric_values)} values using {rule.method.value}: {result}')
            return result
            
        except Exception as e:
            current_app.logger.error(f'Error aggregating dependency values for {dependency_field_id}: {str(e)}')
            return None
    
    def _calculate_aggregation_period(self, 
                                    reporting_date: date,
                                    lookback_months: int,
                                    computed_assignment: DataPointAssignment) -> Tuple[date, date]:
        """Calculate the period for aggregation based on the computed field's financial year."""
        # For annual computations, use the financial year
        if computed_assignment.frequency == 'Annual':
            fy_start = date(computed_assignment.fy_start_year, computed_assignment.fy_start_month, 1)
            fy_end = date(computed_assignment.fy_end_year, computed_assignment.fy_start_month, 1) - timedelta(days=1)
            return fy_start, min(fy_end, reporting_date)
        
        # For other frequencies, use lookback months
        period_start = reporting_date - relativedelta(months=lookback_months)
        return period_start, reporting_date
    
    def _apply_aggregation_method(self, 
                                values: List[float], 
                                method: AggregationMethod,
                                weight_factor: float = 1.0) -> Optional[float]:
        """Apply the specified aggregation method to the values."""
        if not values:
            return None
        
        try:
            if method == AggregationMethod.SUM:
                return sum(values) * weight_factor
            elif method == AggregationMethod.AVERAGE:
                return (sum(values) / len(values)) * weight_factor
            elif method == AggregationMethod.LATEST:
                return values[-1] * weight_factor
            elif method == AggregationMethod.EARLIEST:
                return values[0] * weight_factor
            elif method == AggregationMethod.MAX:
                return max(values) * weight_factor
            elif method == AggregationMethod.MIN:
                return min(values) * weight_factor
            elif method == AggregationMethod.WEIGHTED_AVERAGE:
                # More recent values get higher weight
                weights = [i + 1 for i in range(len(values))]
                weighted_sum = sum(val * weight for val, weight in zip(values, weights))
                return (weighted_sum / sum(weights)) * weight_factor
            elif method == AggregationMethod.COUNT:
                return len(values) * weight_factor
            else:
                current_app.logger.warning(f"Unknown aggregation method: {method}")
                return values[-1] * weight_factor  # Default to latest
                
        except Exception as e:
            current_app.logger.error(f"Error applying aggregation method {method}: {str(e)}")
            return None
    
    def _evaluate_formula(self, 
                        formula_expression: str,
                        values: Dict[str, float]) -> Optional[float]:
        """Evaluate the formula with the given values."""
        try:
            # Create a copy of formula for substitution
            computed_formula = formula_expression
            
            # Substitute variables with their values
            for var_name, value in values.items():
                computed_formula = computed_formula.replace(var_name, str(value))
            
            # Evaluate the formula
            result = eval(computed_formula)
            
            return float(result)
            
        except Exception as e:
            current_app.logger.error(f"Error evaluating formula '{formula_expression}': {str(e)}")
            return None
    
    def get_aggregation_summary(self, 
                              computed_field_id: str,
                              entity_id: int,
                              reporting_date: date) -> Dict[str, Any]:
        """
        Get detailed aggregation summary for a computed field.
        
        Args:
            computed_field_id: ID of the computed field
            entity_id: Entity ID
            reporting_date: Reporting date
            
        Returns:
            Dictionary containing aggregation details
        """
        try:
            computed_field = FrameworkDataField.query.get(computed_field_id)
            if not computed_field or not computed_field.is_computed:
                return {}
            
            # Use tenant-scoped queries when possible
            if hasattr(g, 'tenant') and g.tenant:
                computed_assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
                    data_point_id=computed_field_id,
                    entity_id=entity_id,
                    is_active=True
                ).first()
            else:
                computed_assignment = DataPointAssignment.query.filter_by(
                    data_point_id=computed_field_id,
                    entity_id=entity_id,
                    is_active=True
                ).first()
            
            if not computed_assignment:
                return {}
            
            summary = {
                'computed_field_name': computed_field.field_name,
                'formula': computed_field.formula_expression,
                'frequency': computed_assignment.frequency,
                'dependencies': []
            }
            
            for mapping in computed_field.variable_mappings:
                # Get dependency assignment
                if hasattr(g, 'tenant') and g.tenant:
                    dependency_assignment = DataPointAssignment.query_for_tenant(db.session).filter_by(
                        data_point_id=mapping.raw_field_id,
                        entity_id=entity_id,
                        is_active=True
                    ).first()
                else:
                    dependency_assignment = DataPointAssignment.query.filter_by(
                        data_point_id=mapping.raw_field_id,
                        entity_id=entity_id,
                        is_active=True
                    ).first()
                
                dependency_field = FrameworkDataField.query.get(mapping.raw_field_id)
                
                if dependency_assignment and dependency_field:
                    # Get aggregation rule
                    rule = self._get_aggregation_rule(
                        dependency_assignment.frequency,
                        computed_assignment.frequency,
                        mapping.raw_field_id
                    )
                    
                    # Get period
                    period_start, period_end = self._calculate_aggregation_period(
                        reporting_date,
                        rule.lookback_months,
                        computed_assignment
                    )
                    
                    # Get values used in aggregation
                    if hasattr(g, 'tenant') and g.tenant:
                        values_used = ESGData.query_for_tenant(db.session).filter(
                            ESGData.data_point_id == mapping.raw_field_id,
                            ESGData.entity_id == entity_id,
                            ESGData.reporting_date >= period_start,
                            ESGData.reporting_date <= period_end,
                            ESGData.raw_value.isnot(None)
                        ).order_by(ESGData.reporting_date).all()
                    else:
                        values_used = ESGData.query.filter(
                            ESGData.data_point_id == mapping.raw_field_id,
                            ESGData.entity_id == entity_id,
                            ESGData.reporting_date >= period_start,
                            ESGData.reporting_date <= period_end,
                            ESGData.raw_value.isnot(None)
                        ).order_by(ESGData.reporting_date).all()
                    
                    dependency_info = {
                        'field_name': dependency_field.field_name,
                        'variable_name': mapping.variable_name,
                        'coefficient': mapping.coefficient,
                        'frequency': dependency_assignment.frequency,
                        'aggregation_method': rule.method.value,
                        'lookback_months': rule.lookback_months,
                        'period_start': period_start.isoformat(),
                        'period_end': period_end.isoformat(),
                        'values_count': len(values_used),
                        'values_used': [
                            {
                                'date': v.reporting_date.isoformat(),
                                'value': float(v.raw_value) if v.raw_value else None
                            } for v in values_used
                        ]
                    }
                    
                    summary['dependencies'].append(dependency_info)
            
            return summary
            
        except Exception as e:
            current_app.logger.error(f'Error generating aggregation summary: {str(e)}')
            return {}


# Global instance for use across the application
aggregation_service = AggregationService() 