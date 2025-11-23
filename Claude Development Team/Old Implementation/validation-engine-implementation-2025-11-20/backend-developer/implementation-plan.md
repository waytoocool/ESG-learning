# Automated Validation Engine - Implementation Plan

**Project:** Validation Engine Implementation
**Developer Role:** Backend Developer
**Start Date:** 2025-11-20
**Estimated Duration:** 3 weeks

---

## 📋 Implementation Overview

This document outlines the technical implementation plan for the Automated Validation Engine, including database changes, service layer implementation, API endpoints, and UI integration points.

---

## 🗓️ Implementation Phases

### **Phase 1: Database Schema & Models (Days 1-3)**

#### **Task 1.1: Company Model Enhancement**
**File:** `app/models/company.py`

```python
class Company(db.Model):
    # ... existing fields ...

    # NEW: Validation configuration
    validation_trend_threshold_pct = db.Column(
        db.Float,
        default=20.0,
        nullable=False,
        comment="Percentage threshold for trend variance warnings"
    )

    def get_validation_threshold(self):
        """Get validation threshold with fallback to default."""
        return self.validation_trend_threshold_pct or 20.0
```

**Migration:**
```sql
ALTER TABLE company ADD COLUMN validation_trend_threshold_pct FLOAT DEFAULT 20.0 NOT NULL;
```

---

#### **Task 1.2: DataPointAssignment Model Enhancement**
**File:** `app/models/data_assignment.py`

```python
class DataPointAssignment(db.Model, TenantScopedQueryMixin, TenantScopedModelMixin):
    # ... existing fields ...

    # NEW: Attachment requirement flag
    attachment_required = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        comment="Whether supporting documents are required for this assignment"
    )
```

**Migration:**
```sql
ALTER TABLE data_point_assignments ADD COLUMN attachment_required BOOLEAN DEFAULT FALSE NOT NULL;
```

---

#### **Task 1.3: ESGData Model Enhancement**
**File:** `app/models/esg_data.py`

```python
class ESGData(db.Model, TenantScopedQueryMixin, TenantScopedModelMixin):
    # ... existing fields ...

    # NEW: Review workflow fields
    review_status = db.Column(
        db.Enum('draft', 'submitted', 'pending_review',
                'approved', 'rejected', 'needs_revision',
                name='review_status_type'),
        default='draft',
        nullable=False,
        index=True
    )

    submitted_at = db.Column(
        db.DateTime,
        nullable=True,
        comment="When data was submitted for review"
    )

    # NEW: Validation results storage
    validation_results = db.Column(
        db.JSON,
        nullable=True,
        comment="Validation check results and warnings"
    )

    # Add index for review status queries
    __table_args__ = (
        # ... existing indexes ...
        db.Index('idx_esg_review_status', 'review_status', 'company_id'),
    )
```

**Migration:**
```sql
-- Add review_status enum
CREATE TYPE review_status_type AS ENUM (
    'draft', 'submitted', 'pending_review',
    'approved', 'rejected', 'needs_revision'
);

-- Add columns
ALTER TABLE esg_data ADD COLUMN review_status review_status_type DEFAULT 'draft' NOT NULL;
ALTER TABLE esg_data ADD COLUMN submitted_at TIMESTAMP NULL;
ALTER TABLE esg_data ADD COLUMN validation_results JSON NULL;

-- Add index
CREATE INDEX idx_esg_review_status ON esg_data(review_status, company_id);
```

---

#### **Task 1.4: AuditLog Enhancement**
**File:** `app/models/audit_log.py`

Add new action types:
```python
class AuditLog(db.Model):
    action_type = db.Column(db.Enum(
        # ... existing types ...
        'Data_Submitted',
        'Validation_Passed',
        'Validation_Warning',
        'User_Acknowledged_Warning',
        name='audit_action_type'
    ), nullable=False)
```

---

### **Phase 2: Validation Service Implementation (Days 4-7)**

#### **Task 2.1: Create ValidationService Class**
**File:** `app/services/validation_service.py` (NEW)

```python
from typing import Dict, List, Optional, Any
from datetime import datetime, UTC
from ..models import ESGData, DataPointAssignment, Company, FrameworkDataField
from ..extensions import db
import statistics

class ValidationService:
    """Service for automated ESG data validation."""

    LOOKBACK_PERIODS = 2
    ENABLE_SEASONAL_COMPARISON = True

    @classmethod
    def validate_submission(cls,
                           field_id: str,
                           entity_id: int,
                           value: float,
                           reporting_date,
                           company_id: int,
                           assignment_id: Optional[str] = None,
                           dimension_values: Optional[Dict] = None,
                           attachments: Optional[List] = None) -> Dict[str, Any]:
        """
        Run all validation checks on a data submission.

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
            "passed": len(flags) == 0,
            "risk_score": risk_score,
            "flags": flags,
            "timestamp": datetime.now(UTC).isoformat()
        }

    @classmethod
    def _check_required_attachments(cls, attachments: Optional[List]) -> Optional[Dict]:
        """Check if required attachments are present."""
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
                                 reporting_date,
                                 company: Company,
                                 assignment: Optional[DataPointAssignment],
                                 dimension_values: Optional[Dict]) -> List[Dict]:
        """
        Check value against historical trends.
        Compares with:
        - Last 2 sequential periods
        - Same period last year (seasonal)
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
        for idx, hist_value in enumerate(historical_data['sequential']):
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
                                     reporting_date,
                                     company: Company) -> List[Dict]:
        """
        Check impact on computed fields when dependency changes.
        """
        from ..services.dependency_service import DependencyService

        flags = []
        threshold_pct = company.get_validation_threshold()

        # Find computed fields that depend on this field
        dependent_fields = DependencyService.get_dependent_computed_fields(field_id)

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
                               reporting_date,
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
        from calendar import month_abbr

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
                    "value": float(hist_entry.calculated_value or hist_entry.raw_value),
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
                    "value": float(seasonal_entry.calculated_value or seasonal_entry.raw_value),
                    "period_label": period_label,
                    "date": seasonal_date.isoformat()
                }

        return result

    @classmethod
    def _calculate_projected_computed_value(cls,
                                           computed_field: FrameworkDataField,
                                           entity_id: int,
                                           reporting_date,
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
                        existing.calculated_value or existing.raw_value
                    )

        # Check if all dependencies have values
        complete = len(dependency_values) == len(dependencies)

        if not complete:
            return {"complete": False, "value": None, "dependencies": dependency_values}

        # Calculate projected value using formula
        try:
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
            return {"complete": False, "value": None, "error": str(e)}

    @staticmethod
    def _calculate_variance(new_value: float, old_value: float) -> float:
        """Calculate percentage variance between two values."""
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
    def _format_period_label(date, frequency: str) -> str:
        """Format date as period label based on frequency."""
        from calendar import month_abbr

        if frequency == 'Monthly':
            return f"{month_abbr[date.month]} {date.year}"
        elif frequency == 'Quarterly':
            quarter = (date.month - 1) // 3 + 1
            return f"Q{quarter} {date.year}"
        else:  # Annual
            return f"FY {date.year}"

    @staticmethod
    def _resolve_assignment(field_id: str,
                           entity_id: int,
                           reporting_date,
                           assignment_id: Optional[str]) -> Optional[DataPointAssignment]:
        """Resolve assignment for validation context."""
        if assignment_id:
            return DataPointAssignment.query.get(assignment_id)

        # Fallback to assignment resolution
        from ..services.assignment_versioning import resolve_assignment
        return resolve_assignment(field_id, entity_id, reporting_date)
```

---

#### **Task 2.2: Create DependencyService Helper**
**File:** `app/services/dependency_service.py` (if not exists)

```python
class DependencyService:
    """Service for managing computed field dependencies."""

    @classmethod
    def get_dependent_computed_fields(cls, field_id: str) -> List[FrameworkDataField]:
        """Get all computed fields that depend on the given field."""
        # Implementation depends on existing computed field dependency tracking
        # This should return computed fields where field_id is in their dependencies
        pass

    @classmethod
    def get_dependencies(cls, computed_field_id: str) -> List[str]:
        """Get all dependency field IDs for a computed field."""
        # Return list of field_ids that this computed field depends on
        pass

    @classmethod
    def calculate_computed_value(cls,
                                computed_field: FrameworkDataField,
                                dependency_values: Dict[str, float]) -> float:
        """Calculate computed field value from dependency values."""
        # Execute the computed field formula with dependency values
        pass
```

---

### **Phase 3: API Endpoints (Days 8-10)**

#### **Task 3.1: Validation API Endpoint**
**File:** `app/routes/user_v2/validation_api.py` (NEW)

```python
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ...services.validation_service import ValidationService
from ...models import ESGData
from ...extensions import db

validation_api = Blueprint('validation_api', __name__)

@validation_api.route('/api/user/validate-submission', methods=['POST'])
@login_required
def validate_submission():
    """
    Validate ESG data submission before saving.

    Request Body:
        {
            "field_id": "abc-123",
            "entity_id": 1,
            "value": 1500,
            "reporting_date": "2024-12-31",
            "assignment_id": "def-456",
            "dimension_values": {"gender": "Male"},
            "has_attachments": true
        }

    Response:
        {
            "success": true,
            "validation": {
                "passed": false,
                "risk_score": 35,
                "flags": [...]
            }
        }
    """
    try:
        data = request.get_json()

        # Run validation
        validation_result = ValidationService.validate_submission(
            field_id=data['field_id'],
            entity_id=data['entity_id'],
            value=float(data['value']),
            reporting_date=data['reporting_date'],
            company_id=current_user.company_id,
            assignment_id=data.get('assignment_id'),
            dimension_values=data.get('dimension_values'),
            attachments=[{'exists': True}] if data.get('has_attachments') else []
        )

        return jsonify({
            'success': True,
            'validation': validation_result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

---

#### **Task 3.2: Company Settings API Endpoint**
**File:** `app/routes/admin.py` (UPDATE)

```python
@admin.route('/api/admin/company-settings', methods=['POST'])
@login_required
@admin_required
def update_company_settings():
    """Update company validation settings."""
    try:
        data = request.get_json()
        company = current_user.company

        if 'validation_trend_threshold_pct' in data:
            threshold = float(data['validation_trend_threshold_pct'])

            # Validate threshold range
            if threshold < 0 or threshold > 100:
                return jsonify({
                    'success': False,
                    'error': 'Threshold must be between 0 and 100'
                }), 400

            company.validation_trend_threshold_pct = threshold
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Validation settings updated successfully'
            })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

---

### **Phase 4: UI Implementation (Days 11-15)**

#### **Task 4.1: Validation Modal Component**
**File:** `app/static/js/user_v2/validation_modal.js` (NEW)

```javascript
/**
 * Validation Modal Component
 * Shows validation warnings and collects user explanations
 */
class ValidationModal {
    constructor() {
        this.modal = null;
        this.currentValidation = null;
        this.onConfirm = null;
    }

    show(validationResults, onConfirmCallback) {
        this.currentValidation = validationResults;
        this.onConfirm = onConfirmCallback;

        this.render();
        this.bindEvents();

        // Show modal
        $(this.modal).modal('show');
    }

    render() {
        const flags = this.currentValidation.flags || [];

        // Group flags by type
        const trendWarnings = flags.filter(f => f.type === 'trend_variance');
        const computedWarnings = flags.filter(f => f.type === 'computed_field_impact');
        const attachmentWarnings = flags.filter(f => f.type === 'required_attachment');
        const infoMessages = flags.filter(f => f.severity === 'info');

        let html = `
            <div class="modal fade" id="validationModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-warning">
                            <h5 class="modal-title">
                                <i class="fas fa-exclamation-triangle"></i>
                                Validation Warnings
                            </h5>
                            <button type="button" class="close" data-dismiss="modal">
                                <span>&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <p class="mb-3">Please review the following issues:</p>

                            ${this.renderInfoMessages(infoMessages)}
                            ${this.renderTrendWarnings(trendWarnings)}
                            ${this.renderComputedWarnings(computedWarnings)}
                            ${this.renderAttachmentWarnings(attachmentWarnings)}

                            <hr>

                            <div class="form-group">
                                <label for="validationNotes">
                                    <i class="fas fa-edit"></i>
                                    Please explain these changes: *
                                </label>
                                <textarea
                                    class="form-control"
                                    id="validationNotes"
                                    rows="4"
                                    maxlength="2000"
                                    placeholder="E.g., New facility opened, operational changes, data correction, etc."
                                    required
                                ></textarea>
                                <small class="form-text text-muted">
                                    <span id="noteCharCount">0</span> / 2000 characters
                                </small>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">
                                Cancel
                            </button>
                            <button type="button" class="btn btn-primary" id="btnReviewSubmit">
                                Review & Submit
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if present
        $('#validationModal').remove();

        // Append new modal
        $('body').append(html);
        this.modal = document.getElementById('validationModal');
    }

    renderInfoMessages(infoMessages) {
        if (infoMessages.length === 0) return '';

        return `
            <div class="alert alert-info">
                <strong><i class="fas fa-info-circle"></i> Information</strong>
                <ul class="mb-0 mt-2">
                    ${infoMessages.map(msg => `<li>${msg.message}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    renderTrendWarnings(trendWarnings) {
        if (trendWarnings.length === 0) return '';

        return `
            <div class="alert alert-warning">
                <strong><i class="fas fa-chart-line"></i> Trend Analysis Warnings</strong>
                <ul class="mb-2 mt-2">
                    ${trendWarnings.map(w => `
                        <li>
                            ${w.message}
                            <small class="d-block text-muted">
                                ${w.details.current_value.toFixed(2)}
                                (was ${w.details.historical_value.toFixed(2)})
                            </small>
                        </li>
                    `).join('')}
                </ul>
                ${this.renderHistoricalContext(trendWarnings)}
            </div>
        `;
    }

    renderHistoricalContext(trendWarnings) {
        if (trendWarnings.length === 0) return '';

        const sequential = trendWarnings.filter(w =>
            w.details.comparison_type === 'sequential'
        );
        const seasonal = trendWarnings.filter(w =>
            w.details.comparison_type === 'seasonal'
        );

        if (sequential.length === 0 && seasonal.length === 0) return '';

        return `
            <small class="text-muted">
                <strong>Previous values:</strong><br>
                ${sequential.map(w =>
                    `• ${w.details.historical_period}: ${w.details.historical_value.toFixed(2)}`
                ).join('<br>')}
                ${seasonal.length > 0 ? '<br>' + seasonal.map(w =>
                    `• ${w.details.historical_period} (same period last year): ${w.details.historical_value.toFixed(2)}`
                ).join('<br>') : ''}
            </small>
        `;
    }

    renderComputedWarnings(computedWarnings) {
        if (computedWarnings.length === 0) return '';

        return `
            <div class="alert alert-warning">
                <strong><i class="fas fa-calculator"></i> Computed Field Impact</strong>
                <ul class="mb-0 mt-2">
                    ${computedWarnings.map(w => `
                        <li>
                            ${w.message}
                            <small class="d-block text-muted">
                                ${w.details.computed_field_name}:
                                ${w.details.current_value?.toFixed(2) || 'N/A'} →
                                ${w.details.projected_value.toFixed(2)}
                            </small>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    renderAttachmentWarnings(attachmentWarnings) {
        if (attachmentWarnings.length === 0) return '';

        return `
            <div class="alert alert-warning">
                <strong><i class="fas fa-paperclip"></i> Missing Attachment</strong>
                <ul class="mb-0 mt-2">
                    ${attachmentWarnings.map(w => `<li>${w.message}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    bindEvents() {
        const notesField = document.getElementById('validationNotes');
        const charCount = document.getElementById('noteCharCount');
        const submitBtn = document.getElementById('btnReviewSubmit');

        // Character counter
        $(notesField).on('input', () => {
            charCount.textContent = notesField.value.length;
        });

        // Review & Submit button
        $(submitBtn).on('click', () => {
            const notes = notesField.value.trim();

            if (!notes) {
                alert('Please add a note explaining these changes.');
                notesField.focus();
                return;
            }

            if (notes.length < 10) {
                alert('Please provide a more detailed explanation (at least 10 characters).');
                notesField.focus();
                return;
            }

            // Close modal and call confirm callback
            $(this.modal).modal('hide');
            if (this.onConfirm) {
                this.onConfirm(notes);
            }
        });
    }
}

// Export for use in other modules
window.ValidationModal = ValidationModal;
```

---

#### **Task 4.2: Integrate Validation into Save Flow**
**File:** `app/static/js/user_v2/data_submission.js` (UPDATE)

```javascript
// Add at top of file
const validationModal = new ValidationModal();

// Modify existing save function
async function saveDataEntry(formData) {
    try {
        // Step 1: Run validation
        const validationResult = await validateSubmission(formData);

        // Step 2: If warnings, show modal
        if (!validationResult.passed) {
            return new Promise((resolve, reject) => {
                validationModal.show(validationResult, async (explanationNotes) => {
                    try {
                        // User confirmed - proceed with save
                        formData.validation_results = validationResult;
                        formData.notes = formData.notes
                            ? formData.notes + '\n\n[Validation Notes]\n' + explanationNotes
                            : explanationNotes;

                        const saveResult = await performSave(formData);
                        resolve(saveResult);
                    } catch (error) {
                        reject(error);
                    }
                });
            });
        }

        // Step 3: No warnings - proceed directly
        formData.validation_results = validationResult;
        return await performSave(formData);

    } catch (error) {
        console.error('Save error:', error);
        throw error;
    }
}

async function validateSubmission(formData) {
    const response = await fetch('/api/user/validate-submission', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            field_id: formData.field_id,
            entity_id: formData.entity_id,
            value: formData.value,
            reporting_date: formData.reporting_date,
            assignment_id: formData.assignment_id,
            dimension_values: formData.dimension_values,
            has_attachments: formData.attachments && formData.attachments.length > 0
        })
    });

    const result = await response.json();

    if (!result.success) {
        throw new Error('Validation failed: ' + result.error);
    }

    return result.validation;
}

async function performSave(formData) {
    // Existing save logic
    const response = await fetch('/api/user/save-data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    });

    return await response.json();
}
```

---

#### **Task 4.3: Company Settings UI**
**File:** `app/templates/admin/company_settings.html` (UPDATE)

Add validation settings section:

```html
<div class="card mb-4">
    <div class="card-header">
        <h5 class="mb-0">
            <i class="fas fa-check-circle"></i>
            Validation Settings
        </h5>
    </div>
    <div class="card-body">
        <form id="validationSettingsForm">
            <div class="form-group">
                <label for="validation_threshold">
                    Trend Variance Threshold (%)
                    <i class="fas fa-info-circle"
                       data-toggle="tooltip"
                       title="Data submissions exceeding this threshold will require explanation from users."></i>
                </label>
                <input
                    type="number"
                    class="form-control"
                    id="validation_threshold"
                    name="validation_trend_threshold_pct"
                    value="{{ company.validation_trend_threshold_pct or 20 }}"
                    min="0"
                    max="100"
                    step="0.1"
                    required
                >
                <small class="form-text text-muted">
                    Flag submissions that change by more than this percentage compared to historical values.
                    Default: 20%
                </small>
            </div>

            <button type="submit" class="btn btn-primary">
                <i class="fas fa-save"></i>
                Save Validation Settings
            </button>
        </form>
    </div>
</div>

<script>
$('#validationSettingsForm').on('submit', async function(e) {
    e.preventDefault();

    const threshold = parseFloat($('#validation_threshold').val());

    try {
        const response = await fetch('/api/admin/company-settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                validation_trend_threshold_pct: threshold
            })
        });

        const result = await response.json();

        if (result.success) {
            showNotification('success', 'Validation settings updated successfully');
        } else {
            showNotification('error', result.error);
        }
    } catch (error) {
        showNotification('error', 'Failed to update settings: ' + error.message);
    }
});
</script>
```

---

#### **Task 4.4: Assignment Modal - Add Attachment Required Checkbox**
**File:** `app/static/js/admin/assign_data_points/main.js` (UPDATE)

```javascript
// In the assignment configuration modal rendering
function renderAssignmentModal(field, entities) {
    return `
        <div class="modal" id="assignmentModal">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Configure Assignment</h5>
                        <button type="button" class="close" data-dismiss="modal">
                            <span>&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <!-- Existing frequency selection -->
                        <div class="form-group">
                            <label>Frequency</label>
                            <select class="form-control" id="assignmentFrequency">
                                <option value="Annual">Annual</option>
                                <option value="Quarterly">Quarterly</option>
                                <option value="Monthly">Monthly</option>
                            </select>
                        </div>

                        <!-- NEW: Attachment required checkbox -->
                        <div class="form-group">
                            <div class="custom-control custom-checkbox">
                                <input
                                    type="checkbox"
                                    class="custom-control-input"
                                    id="assignmentAttachmentRequired"
                                >
                                <label class="custom-control-label" for="assignmentAttachmentRequired">
                                    <i class="fas fa-paperclip"></i>
                                    Require attachment for this field
                                </label>
                            </div>
                            <small class="form-text text-muted">
                                Supporting documents will be mandatory for all submissions of this field.
                            </small>
                        </div>

                        <!-- Existing fiscal year and other fields -->
                        <!-- ... -->
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">
                            Cancel
                        </button>
                        <button type="button" class="btn btn-primary" id="btnConfirmAssignment">
                            Assign
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// In assignment submission
async function submitAssignment(field, entities, config) {
    const assignmentData = {
        field_id: field.field_id,
        entity_ids: entities.map(e => e.id),
        frequency: config.frequency,
        fiscal_year: config.fiscal_year,
        attachment_required: $('#assignmentAttachmentRequired').is(':checked') // NEW
    };

    // Submit to API
    const response = await fetch('/api/admin/assign-data-points', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(assignmentData)
    });

    return await response.json();
}
```

---

### **Phase 5: Testing & Refinement (Days 16-18)**

#### **Task 5.1: Unit Tests**
**File:** `tests/test_validation_service.py` (NEW)

```python
import unittest
from datetime import date, timedelta
from app import create_app, db
from app.models import Company, ESGData, DataPointAssignment, FrameworkDataField
from app.services.validation_service import ValidationService

class TestValidationService(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test data
        self.company = Company(
            name='Test Company',
            validation_trend_threshold_pct=20.0
        )
        db.session.add(self.company)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_required_attachment_validation(self):
        """Test required attachment validation."""
        result = ValidationService._check_required_attachments(attachments=None)

        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'required_attachment')
        self.assertEqual(result['severity'], 'warning')

    def test_calculate_variance(self):
        """Test variance calculation."""
        variance = ValidationService._calculate_variance(150, 100)
        self.assertEqual(variance, 50.0)

        variance = ValidationService._calculate_variance(75, 100)
        self.assertEqual(variance, -25.0)

    def test_risk_score_calculation(self):
        """Test risk score calculation."""
        flags = [
            {'severity': 'warning'},
            {'severity': 'warning'},
            {'severity': 'info'}
        ]

        score = ValidationService._calculate_risk_score(flags)
        self.assertEqual(score, 22)  # 10 + 10 + 2

    # Add more tests...
```

---

#### **Task 5.2: Integration Testing**
Use Chrome DevTools MCP or Playwright for end-to-end testing. See separate testing manual.

---

## 📝 Implementation Checklist

### Phase 1: Database (Days 1-3)
- [ ] Update Company model with validation_trend_threshold_pct
- [ ] Update DataPointAssignment model with attachment_required
- [ ] Update ESGData model with review_status, submitted_at, validation_results
- [ ] Update AuditLog with validation action types
- [ ] Run database migrations
- [ ] Test model changes in Python shell

### Phase 2: Services (Days 4-7)
- [ ] Create ValidationService class
- [ ] Implement _check_required_attachments()
- [ ] Implement _check_historical_trends()
- [ ] Implement _check_computed_field_impact()
- [ ] Implement _get_historical_values()
- [ ] Implement _calculate_projected_computed_value()
- [ ] Create/update DependencyService
- [ ] Write unit tests for ValidationService
- [ ] Test service methods with sample data

### Phase 3: APIs (Days 8-10)
- [ ] Create validation_api blueprint
- [ ] Implement /api/user/validate-submission endpoint
- [ ] Update /api/admin/company-settings endpoint
- [ ] Test API endpoints with Postman/curl
- [ ] Add error handling and validation
- [ ] Add audit logging for API calls

### Phase 4: UI (Days 11-15)
- [ ] Create ValidationModal component (validation_modal.js)
- [ ] Update data_submission.js with validation integration
- [ ] Add validation settings section to company_settings.html
- [ ] Update assign_data_points modal with attachment checkbox
- [ ] Test UI components in browser
- [ ] Test validation modal display and interactions
- [ ] Test form submissions with validation
- [ ] Style and polish UI components

### Phase 5: Testing (Days 16-18)
- [ ] Run unit tests
- [ ] Perform integration testing (see testing manual)
- [ ] Test all edge cases
- [ ] Performance testing (validation speed)
- [ ] Cross-browser testing
- [ ] Fix bugs and issues
- [ ] Code review and refactoring
- [ ] Documentation updates

---

## 🚀 Deployment Steps

1. **Backup Database**
   ```bash
   cp instance/esg_data.db instance/esg_data.db.backup
   ```

2. **Run Migrations**
   ```bash
   python manage.py db upgrade
   ```

3. **Deploy Code**
   ```bash
   git checkout feature/validation-engine
   git pull origin feature/validation-engine
   ```

4. **Restart Application**
   ```bash
   sudo systemctl restart esg-datavault
   ```

5. **Verify Deployment**
   - Check application logs
   - Test validation on test company
   - Monitor error rates

---

## 📊 Success Metrics

- [ ] Validation completes in < 2 seconds
- [ ] All validation checks working correctly
- [ ] UI displays warnings properly
- [ ] Users can add notes and submit
- [ ] Audit trail captures validation events
- [ ] No regressions in existing functionality

---

## 🐛 Known Issues & Limitations

1. **Dimensional Data Comparison**: Current implementation compares totals and individual dimensions separately, which may generate many warnings for highly dimensional data.

2. **Incomplete Computed Fields**: Validation skips computed fields with incomplete dependencies, which may miss some edge cases.

3. **Historical Data Requirements**: Needs at least 1 historical value for meaningful trend analysis.

---

## 📚 References

- Requirements Document: `../requirements-and-specs.md`
- Testing Manual: `../testing-manual.md`
- Existing Computed Fields: `app/services/user_v2/field_service.py`
- Existing Assignment System: `app/services/assignment_versioning.py`

---

**Last Updated:** 2025-11-20
**Status:** Ready for Implementation
