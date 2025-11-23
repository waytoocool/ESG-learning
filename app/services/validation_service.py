"""
Validation Service for Automated ESG Data Validation

This service implements automated validation checks for ESG data submissions:
1. Required Attachments - Check if supporting documents are present when required
2. Historical Trend Analysis - Compare values with historical data to detect anomalies
3. Computed Field Impact - Validate impact on computed fields when dependencies change

Author: Claude Code
Date: 2025-11-21
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, UTC, date
from ..models import ESGData, DataPointAssignment, Company, FrameworkDataField
from ..extensions import db


class ValidationService:
    """Service for automated ESG data validation."""

    # Configuration constants
    LOOKBACK_PERIODS = 2  # Number of sequential periods to compare
    ENABLE_SEASONAL_COMPARISON = True  # Compare with same period last year

    @classmethod
    def validate_submission(cls,
                           field_id: str,
                           entity_id: int,
                           value: float,
                           reporting_date: date,
                           company_id: int,
                           assignment_id: Optional[str] = None,
                           dimension_values: Optional[Dict] = None,
                           attachments: Optional[List] = None) -> Dict[str, Any]:
        """
        Run all validation checks on a data submission.

        Args:
            field_id: Framework data field ID
            entity_id: Entity ID
            value: Submitted value
            reporting_date: Reporting date
            company_id: Company ID
            assignment_id: Optional assignment ID
            dimension_values: Optional dimensional breakdown
            attachments: Optional list of attachments

        Returns:
            {
                "passed": bool,
                "risk_score": int,
                "flags": [ValidationFlag],
                "timestamp": str
            }
        """
        flags = []

        # Get company and assignment for configuration
        company = Company.query.get(company_id)
        if not company:
            return {
                "passed": False,
                "risk_score": 100,
                "flags": [{
                    "type": "error",
                    "severity": "error",
                    "message": "Company not found"
                }],
                "timestamp": datetime.now(UTC).isoformat()
            }

        assignment = cls._resolve_assignment(field_id, entity_id,
                                             reporting_date, assignment_id)

        # 1. Check required attachments
        if assignment and assignment.attachment_required:
            attachment_flag = cls._check_required_attachments(attachments)
            if attachment_flag:
                flags.append(attachment_flag)

        # 2. Historical trend analysis
        trend_flags = cls._check_historical_trends(
            field_id=field_id,
            entity_id=entity_id,
            value=value,
            reporting_date=reporting_date,
            company=company,
            assignment=assignment,
            dimension_values=dimension_values
        )
        flags.extend(trend_flags)

        # 3. Computed field impact validation
        computed_flags = cls._check_computed_field_impact(
            field_id=field_id,
            entity_id=entity_id,
            value=value,
            reporting_date=reporting_date,
            company=company
        )
        flags.extend(computed_flags)

        # Calculate risk score
        risk_score = cls._calculate_risk_score(flags)

        return {
            "passed": len([f for f in flags if f.get('severity') in ['error', 'warning']]) == 0,
            "risk_score": risk_score,
            "flags": flags,
            "timestamp": datetime.now(UTC).isoformat()
        }

    @classmethod
    def _check_required_attachments(cls, attachments: Optional[List]) -> Optional[Dict]:
        """
        Check if required attachments are present.

        Args:
            attachments: List of attachment objects or None

        Returns:
            Validation flag dict or None if check passes
        """
        if not attachments or len(attachments) == 0:
            return {
                "type": "required_attachment",
                "severity": "warning",
                "message": "Supporting document is required for this field",
                "details": {
                    "attachment_count": 0
                }
            }
        return None

    @classmethod
    def _check_historical_trends(cls,
                                 field_id: str,
                                 entity_id: int,
                                 value: float,
                                 reporting_date: date,
                                 company: Company,
                                 assignment: Optional[DataPointAssignment],
                                 dimension_values: Optional[Dict]) -> List[Dict]:
        """
        Check value against historical trends.
        Compares with:
        - Last 2 sequential periods
        - Same period last year (seasonal)

        Args:
            field_id: Framework data field ID
            entity_id: Entity ID
            value: Current value
            reporting_date: Reporting date
            company: Company object
            assignment: DataPointAssignment object
            dimension_values: Optional dimensional breakdown

        Returns:
            List of validation flag dicts
        """
        flags = []
        threshold_pct = company.get_validation_threshold()

        # Get historical values
        historical_data = cls._get_historical_values(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date,
            assignment=assignment,
            dimension_values=dimension_values
        )

        # No historical data - show info message
        if not historical_data['sequential'] and not historical_data['seasonal']:
            flags.append({
                "type": "no_historical_data",
                "severity": "info",
                "message": "No historical data available for comparison. This is your first submission for this period.",
                "details": {}
            })
            return flags

        # Compare with sequential periods
        for hist_value in historical_data['sequential']:
            variance_pct = cls._calculate_variance(value, hist_value['value'])

            if abs(variance_pct) > threshold_pct:
                flags.append({
                    "type": "trend_variance",
                    "severity": "warning",
                    "message": f"Value {'increased' if variance_pct > 0 else 'decreased'} "
                              f"{abs(variance_pct):.1f}% vs {hist_value['period_label']}",
                    "details": {
                        "current_value": value,
                        "historical_value": hist_value['value'],
                        "historical_period": hist_value['period_label'],
                        "variance_pct": variance_pct,
                        "threshold_pct": threshold_pct,
                        "comparison_type": "sequential"
                    }
                })

        # Compare with seasonal (same period last year)
        if historical_data['seasonal']:
            seasonal_value = historical_data['seasonal']
            variance_pct = cls._calculate_variance(value, seasonal_value['value'])

            if abs(variance_pct) > threshold_pct:
                flags.append({
                    "type": "trend_variance",
                    "severity": "warning",
                    "message": f"Value {'increased' if variance_pct > 0 else 'decreased'} "
                              f"{abs(variance_pct):.1f}% vs {seasonal_value['period_label']} "
                              f"(same period last year)",
                    "details": {
                        "current_value": value,
                        "historical_value": seasonal_value['value'],
                        "historical_period": seasonal_value['period_label'],
                        "variance_pct": variance_pct,
                        "threshold_pct": threshold_pct,
                        "comparison_type": "seasonal"
                    }
                })

        return flags

    @classmethod
    def _check_computed_field_impact(cls,
                                     field_id: str,
                                     entity_id: int,
                                     value: float,
                                     reporting_date: date,
                                     company: Company) -> List[Dict]:
        """
        Check impact on computed fields when dependency changes.

        Args:
            field_id: Framework data field ID (the dependency being changed)
            entity_id: Entity ID
            value: New value for the dependency
            reporting_date: Reporting date
            company: Company object

        Returns:
            List of validation flag dicts
        """
        from ..services.dependency_service import DependencyService

        flags = []
        threshold_pct = company.get_validation_threshold()

        # Find computed fields that depend on this field
        try:
            dependent_fields = DependencyService.get_dependent_computed_fields(field_id)
        except Exception as e:
            # If DependencyService not fully implemented, skip validation
            print(f"[ValidationService] Skipping computed field validation: {str(e)}")
            return flags

        for computed_field in dependent_fields:
            # Calculate projected computed field value
            projection = cls._calculate_projected_computed_value(
                computed_field=computed_field,
                entity_id=entity_id,
                reporting_date=reporting_date,
                changed_dependency_id=field_id,
                changed_dependency_value=value
            )

            # Skip if dependencies incomplete
            if not projection['complete']:
                continue

            projected_value = projection['value']

            # Get historical values for computed field
            computed_historical = cls._get_historical_values(
                field_id=computed_field.field_id,
                entity_id=entity_id,
                reporting_date=reporting_date,
                assignment=None,
                dimension_values=None
            )

            # Compare projected value with historical
            if computed_historical['sequential']:
                last_value = computed_historical['sequential'][0]['value']
                variance_pct = cls._calculate_variance(projected_value, last_value)

                if abs(variance_pct) > threshold_pct:
                    flags.append({
                        "type": "computed_field_impact",
                        "severity": "warning",
                        "message": f"This change will cause {computed_field.name} to "
                                  f"{'increase' if variance_pct > 0 else 'decrease'} "
                                  f"by {abs(variance_pct):.1f}%",
                        "details": {
                            "computed_field_id": computed_field.field_id,
                            "computed_field_name": computed_field.name,
                            "projected_value": projected_value,
                            "current_value": last_value,
                            "variance_pct": variance_pct,
                            "threshold_pct": threshold_pct
                        }
                    })

        return flags

    @classmethod
    def _get_historical_values(cls,
                               field_id: str,
                               entity_id: int,
                               reporting_date: date,
                               assignment: Optional[DataPointAssignment],
                               dimension_values: Optional[Dict]) -> Dict[str, Any]:
        """
        Get historical values for comparison.

        Returns:
            {
                "sequential": [
                    {"value": 1200, "period_label": "Nov 2024", "date": "2024-11-30"},
                    {"value": 1180, "period_label": "Oct 2024", "date": "2024-10-31"}
                ],
                "seasonal": {"value": 1150, "period_label": "Dec 2023", "date": "2023-12-31"}
            }
        """
        from dateutil.relativedelta import relativedelta

        result = {
            "sequential": [],
            "seasonal": None
        }

        frequency = assignment.frequency if assignment else 'Annual'

        # Determine period delta based on frequency
        if frequency == 'Monthly':
            period_delta = relativedelta(months=1)
            seasonal_delta = relativedelta(years=1)
        elif frequency == 'Quarterly':
            period_delta = relativedelta(months=3)
            seasonal_delta = relativedelta(years=1)
        else:  # Annual
            period_delta = relativedelta(years=1)
            seasonal_delta = relativedelta(years=1)

        # FIRST: Check for existing data at the SAME reporting_date (for data revisions/updates)
        existing_query = ESGData.query.filter(
            ESGData.field_id == field_id,
            ESGData.entity_id == entity_id,
            ESGData.reporting_date == reporting_date,
            ESGData.is_draft == False
        )

        if dimension_values:
            existing_data = existing_query.all()
            matching_data = [d for d in existing_data if d.dimension_values == dimension_values]
            existing_entry = matching_data[0] if matching_data else None
        else:
            existing_entry = existing_query.first()

        # If existing data found, treat it as "current period" comparison for revision detection
        if existing_entry:
            period_label = cls._format_period_label(reporting_date, frequency)
            result["sequential"].append({
                "value": float(existing_entry.calculated_value or existing_entry.raw_value or 0),
                "period_label": f"{period_label} (existing)",
                "date": reporting_date.isoformat(),
                "is_current_period": True  # Flag to indicate this is comparing against existing data
            })

        # Get sequential periods (last 2)
        for i in range(1, cls.LOOKBACK_PERIODS + 1):
            past_date = reporting_date - (period_delta * i)

            # Query for historical data
            query = ESGData.query.filter(
                ESGData.field_id == field_id,
                ESGData.entity_id == entity_id,
                ESGData.reporting_date == past_date,
                ESGData.is_draft == False
            )

            # Match dimensions if provided
            if dimension_values:
                # For dimensional data, need to match dimension_values
                hist_data = query.all()
                matching_data = [d for d in hist_data
                               if d.dimension_values == dimension_values]
                if matching_data:
                    hist_entry = matching_data[0]
                else:
                    continue
            else:
                hist_entry = query.first()

            if hist_entry:
                period_label = cls._format_period_label(past_date, frequency)
                result["sequential"].append({
                    "value": float(hist_entry.calculated_value or hist_entry.raw_value or 0),
                    "period_label": period_label,
                    "date": past_date.isoformat()
                })

        # Get seasonal comparison (same period last year)
        if cls.ENABLE_SEASONAL_COMPARISON:
            seasonal_date = reporting_date - seasonal_delta

            query = ESGData.query.filter(
                ESGData.field_id == field_id,
                ESGData.entity_id == entity_id,
                ESGData.reporting_date == seasonal_date,
                ESGData.is_draft == False
            )

            if dimension_values:
                hist_data = query.all()
                matching_data = [d for d in hist_data
                               if d.dimension_values == dimension_values]
                seasonal_entry = matching_data[0] if matching_data else None
            else:
                seasonal_entry = query.first()

            if seasonal_entry:
                period_label = cls._format_period_label(seasonal_date, frequency)
                result["seasonal"] = {
                    "value": float(seasonal_entry.calculated_value or seasonal_entry.raw_value or 0),
                    "period_label": period_label,
                    "date": seasonal_date.isoformat()
                }

        return result

    @classmethod
    def _calculate_projected_computed_value(cls,
                                           computed_field: FrameworkDataField,
                                           entity_id: int,
                                           reporting_date: date,
                                           changed_dependency_id: str,
                                           changed_dependency_value: float) -> Dict[str, Any]:
        """
        Calculate projected value for computed field with new dependency value.

        Returns:
            {
                "complete": bool,  # All dependencies have values
                "value": float,    # Projected computed value
                "dependencies": {...}
            }
        """
        from ..services.dependency_service import DependencyService

        try:
            # Get all dependencies for this computed field
            dependencies = DependencyService.get_dependencies(computed_field.field_id)

            # Collect dependency values
            dependency_values = {}

            for dep_field_id in dependencies:
                if dep_field_id == changed_dependency_id:
                    # Use the new value being submitted
                    dependency_values[dep_field_id] = changed_dependency_value
                else:
                    # Get existing value from database
                    existing = ESGData.query.filter(
                        ESGData.field_id == dep_field_id,
                        ESGData.entity_id == entity_id,
                        ESGData.reporting_date == reporting_date,
                        ESGData.is_draft == False
                    ).first()

                    if existing:
                        dependency_values[dep_field_id] = float(
                            existing.calculated_value or existing.raw_value or 0
                        )

            # Check if all dependencies have values
            complete = len(dependency_values) == len(dependencies)

            if not complete:
                return {"complete": False, "value": None, "dependencies": dependency_values}

            # Calculate projected value using formula
            projected_value = DependencyService.calculate_computed_value(
                computed_field=computed_field,
                dependency_values=dependency_values
            )

            return {
                "complete": True,
                "value": projected_value,
                "dependencies": dependency_values
            }
        except Exception as e:
            print(f"[ValidationService] Error calculating projected value: {str(e)}")
            return {"complete": False, "value": None, "error": str(e)}

    @staticmethod
    def _calculate_variance(new_value: float, old_value: float) -> float:
        """
        Calculate percentage variance between two values.

        Args:
            new_value: New value
            old_value: Old value

        Returns:
            Percentage change (positive for increase, negative for decrease)
        """
        if old_value == 0:
            return 0 if new_value == 0 else 100
        return ((new_value - old_value) / abs(old_value)) * 100

    @staticmethod
    def _calculate_risk_score(flags: List[Dict]) -> int:
        """
        Calculate risk score based on validation flags.

        Scoring:
        - ERROR: +25 points each
        - WARNING: +10 points each
        - INFO: +2 points each

        Max: 100

        Args:
            flags: List of validation flag dicts

        Returns:
            Risk score (0-100)
        """
        score = 0

        for flag in flags:
            severity = flag.get('severity', 'info')
            if severity == 'error':
                score += 25
            elif severity == 'warning':
                score += 10
            elif severity == 'info':
                score += 2

        return min(score, 100)  # Cap at 100

    @staticmethod
    def _format_period_label(date_obj: date, frequency: str) -> str:
        """
        Format date as period label based on frequency.

        Args:
            date_obj: Date to format
            frequency: Data collection frequency (Monthly/Quarterly/Annual)

        Returns:
            Formatted period label (e.g., "Nov 2024", "Q4 2024", "FY 2024")
        """
        from calendar import month_abbr

        if frequency == 'Monthly':
            return f"{month_abbr[date_obj.month]} {date_obj.year}"
        elif frequency == 'Quarterly':
            quarter = (date_obj.month - 1) // 3 + 1
            return f"Q{quarter} {date_obj.year}"
        else:  # Annual
            return f"FY {date_obj.year}"

    @staticmethod
    def _resolve_assignment(field_id: str,
                           entity_id: int,
                           reporting_date: date,
                           assignment_id: Optional[str]) -> Optional[DataPointAssignment]:
        """
        Resolve assignment for validation context.

        Args:
            field_id: Framework data field ID
            entity_id: Entity ID
            reporting_date: Reporting date
            assignment_id: Optional assignment ID

        Returns:
            DataPointAssignment or None
        """
        if assignment_id:
            return DataPointAssignment.query.get(assignment_id)

        # Fallback to assignment resolution
        try:
            from ..services.assignment_versioning import resolve_assignment
            return resolve_assignment(field_id, entity_id, reporting_date)
        except Exception as e:
            print(f"[ValidationService] Could not resolve assignment: {str(e)}")
            return None
