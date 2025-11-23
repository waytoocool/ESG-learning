# Phase 2: Dimensional Data Support - Requirements & Specifications

## Overview
Implement comprehensive dimensional data collection with automatic total calculations and matrix-based input.

## Requirements

### 2.1 Dimensional Input Fields
- [ ] Generate input grid based on field dimensions
- [ ] Create dimension combination matrix
- [ ] Implement real-time total calculation
- [ ] Add validation for dimension values
- [ ] Support multi-dimensional fields (2+ dimensions)

### 2.2 Data Storage Enhancement
- [ ] Implement enhanced JSON structure for dimension_values
- [ ] Store dimensional breakdowns
- [ ] Calculate and store totals (overall + by-dimension)
- [ ] Include metadata (completeness, timestamp)
- [ ] Version schema for future migrations

### 2.3 UI Enhancements
- [ ] Color-code dimension groups
- [ ] Add expand/collapse for dimension sections
- [ ] Implement smart defaults based on patterns
- [ ] Add copy from previous period feature
- [ ] Show completeness indicators

### 2.4 Backend Services
- [ ] Create DimensionalDataService
  - Generate dimension matrix
  - Calculate totals
  - Validate dimensional data
- [ ] Create AggregationService
  - Aggregate by dimension
  - Cross-entity totals
  - Historical aggregations
- [ ] Update ValidationService
  - Dimension combination validation
  - Value range validation
  - Completeness checks

### 2.5 API Endpoints
- [ ] `POST /api/user/v2/submit-dimensional-data` - Submit dimensional data
- [ ] `GET /api/user/v2/dimension-matrix/{field_id}` - Get dimension matrix
- [ ] `POST /api/user/v2/calculate-totals` - Calculate totals
- [ ] `GET /api/user/v2/dimension-values/{dimension_id}` - Get dimension values

## Technical Specifications

### Enhanced JSON Structure

```python
# ESGData.dimension_values enhanced structure
{
    "version": 2,
    "dimensions": ["gender", "age"],
    "breakdowns": [
        {
            "dimensions": {"gender": "Male", "age": "<30"},
            "raw_value": 100,
            "notes": "Q1 2024"
        },
        {
            "dimensions": {"gender": "Male", "age": "30-50"},
            "raw_value": 150,
            "notes": null
        },
        {
            "dimensions": {"gender": "Female", "age": "<30"},
            "raw_value": 120,
            "notes": null
        }
    ],
    "totals": {
        "overall": 500,
        "by_dimension": {
            "gender": {
                "Male": 250,
                "Female": 215,
                "Other": 35
            },
            "age": {
                "<30": 165,
                "30-50": 230,
                ">50": 105
            }
        }
    },
    "metadata": {
        "last_updated": "2024-01-31T10:30:00Z",
        "completed_combinations": 6,
        "total_combinations": 6,
        "is_complete": true
    }
}
```

### Dimension Matrix UI

```html
<!-- Example: Gender x Age matrix -->
<div class="dimension-matrix">
    <h4>Dimensional Breakdown</h4>

    <table class="matrix-table">
        <thead>
            <tr>
                <th>Gender / Age</th>
                <th>&lt;30</th>
                <th>30-50</th>
                <th>&gt;50</th>
                <th>Total</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Male</td>
                <td><input type="number" name="Male_<30" value="100"></td>
                <td><input type="number" name="Male_30-50" value="150"></td>
                <td><input type="number" name="Male_>50" value="80"></td>
                <td class="total-cell">330</td>
            </tr>
            <tr>
                <td>Female</td>
                <td><input type="number" name="Female_<30" value="120"></td>
                <td><input type="number" name="Female_30-50" value="100"></td>
                <td><input type="number" name="Female_>50" value="70"></td>
                <td class="total-cell">290</td>
            </tr>
            <tr class="total-row">
                <td>Total</td>
                <td class="total-cell">220</td>
                <td class="total-cell">250</td>
                <td class="total-cell">150</td>
                <td class="grand-total">620</td>
            </tr>
        </tbody>
    </table>
</div>
```

### DimensionalDataService

```python
# app/services/user_v2/dimensional_data_service.py

class DimensionalDataService:
    """Service for handling dimensional data operations."""

    @staticmethod
    def prepare_dimension_matrix(field_id, entity_id):
        """Generate dimension matrix structure for a field."""
        field = FrameworkDataField.query.get(field_id)
        field_dimensions = FieldDimension.query.filter_by(field_id=field_id).all()

        # Get dimension values
        dimension_data = {}
        for fd in field_dimensions:
            dimension = fd.dimension
            values = dimension.get_ordered_values()
            dimension_data[dimension.name] = [
                {
                    'value': v.value,
                    'display_name': v.display_name or v.value,
                    'order': v.display_order
                }
                for v in values
            ]

        # Generate all combinations
        combinations = generate_dimension_combinations(dimension_data)

        return {
            'field_id': field_id,
            'dimensions': list(dimension_data.keys()),
            'dimension_values': dimension_data,
            'combinations': combinations,
            'total_combinations': len(combinations)
        }

    @staticmethod
    def calculate_totals(dimensional_data):
        """Calculate totals across all dimensions."""
        breakdowns = dimensional_data.get('breakdowns', [])
        dimensions = dimensional_data.get('dimensions', [])

        # Calculate overall total
        overall_total = sum(
            float(b.get('raw_value', 0))
            for b in breakdowns
            if b.get('raw_value')
        )

        # Calculate per-dimension totals
        by_dimension = {}
        for dim_name in dimensions:
            dim_totals = {}
            for breakdown in breakdowns:
                dim_value = breakdown['dimensions'].get(dim_name)
                if dim_value:
                    current = dim_totals.get(dim_value, 0)
                    dim_totals[dim_value] = current + float(breakdown.get('raw_value', 0))
            by_dimension[dim_name] = dim_totals

        return {
            'overall': overall_total,
            'by_dimension': by_dimension
        }

    @staticmethod
    def validate_dimensional_data(field_id, dimensional_data):
        """Validate dimensional data completeness and correctness."""
        field_dimensions = FieldDimension.query.filter_by(field_id=field_id).all()

        # Check all required dimensions present
        required_dims = {fd.dimension.name for fd in field_dimensions if fd.is_required}
        provided_dims = set(dimensional_data.get('dimensions', []))

        if not required_dims.issubset(provided_dims):
            missing = required_dims - provided_dims
            return False, f"Missing required dimensions: {', '.join(missing)}"

        # Validate all combinations
        breakdowns = dimensional_data.get('breakdowns', [])
        for breakdown in breakdowns:
            dims = breakdown.get('dimensions', {})

            # Check each dimension value is valid
            for dim_name, dim_value in dims.items():
                if not validate_dimension_value(dim_name, dim_value):
                    return False, f"Invalid value '{dim_value}' for dimension '{dim_name}'"

        return True, None
```

### API Endpoints

#### Submit Dimensional Data
```python
@user_v2_bp.route('/api/submit-dimensional-data', methods=['POST'])
@login_required
@tenant_required_for('USER')
def submit_dimensional_data():
    """Submit dimensional data for a field."""
    data = request.get_json()

    field_id = data.get('field_id')
    entity_id = data.get('entity_id')
    reporting_date = data.get('reporting_date')
    dimensional_data = data.get('dimensional_data')

    # Validate
    is_valid, error = DimensionalDataService.validate_dimensional_data(
        field_id, dimensional_data
    )
    if not is_valid:
        return jsonify({'success': False, 'error': error}), 400

    # Calculate totals
    totals = DimensionalDataService.calculate_totals(dimensional_data)

    # Build complete structure
    dimension_values = {
        'version': 2,
        'dimensions': dimensional_data.get('dimensions'),
        'breakdowns': dimensional_data.get('breakdowns'),
        'totals': totals,
        'metadata': {
            'last_updated': datetime.utcnow().isoformat(),
            'completed_combinations': len(dimensional_data.get('breakdowns', [])),
            'total_combinations': len(dimensional_data.get('breakdowns', [])),
            'is_complete': True
        }
    }

    # Save to ESGData
    esg_data = ESGData.query.filter_by(
        field_id=field_id,
        entity_id=entity_id,
        reporting_date=reporting_date
    ).first()

    if not esg_data:
        esg_data = ESGData(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date,
            raw_value=totals['overall'],
            dimension_values=dimension_values,
            company_id=current_user.company_id
        )
        db.session.add(esg_data)
    else:
        esg_data.raw_value = totals['overall']
        esg_data.dimension_values = dimension_values

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Dimensional data saved successfully',
        'totals': totals
    })
```

#### Get Dimension Matrix
```python
@user_v2_bp.route('/api/dimension-matrix/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_dimension_matrix(field_id):
    """Get dimension matrix for a field."""
    entity_id = request.args.get('entity_id')

    matrix = DimensionalDataService.prepare_dimension_matrix(field_id, entity_id)

    # Check for existing data
    reporting_date = request.args.get('reporting_date')
    if reporting_date:
        esg_data = ESGData.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date
        ).first()

        if esg_data and esg_data.dimension_values:
            matrix['existing_data'] = esg_data.dimension_values

    return jsonify(matrix)
```

## JavaScript Implementation

### Matrix Rendering
```javascript
// app/static/js/user_v2/dimensional_data_handler.js

class DimensionalDataHandler {
    constructor(modalElement) {
        this.modal = modalElement;
        this.matrixContainer = null;
        this.currentMatrix = null;
    }

    async loadDimensionMatrix(fieldId, entityId, reportingDate) {
        const response = await fetch(
            `/user/v2/api/dimension-matrix/${fieldId}?entity_id=${entityId}&reporting_date=${reportingDate}`
        );
        const matrix = await response.json();
        this.currentMatrix = matrix;
        this.renderMatrix(matrix);
    }

    renderMatrix(matrix) {
        if (matrix.dimensions.length === 0) {
            // No dimensions - simple input
            this.renderSimpleInput();
            return;
        }

        if (matrix.dimensions.length === 2) {
            // 2D matrix
            this.render2DMatrix(matrix);
        } else {
            // Multiple dimensions - render as list
            this.renderMultiDimensionalList(matrix);
        }

        // Attach event listeners for real-time total calculation
        this.attachCalculationListeners();
    }

    render2DMatrix(matrix) {
        const [dim1, dim2] = matrix.dimensions;
        const dim1Values = matrix.dimension_values[dim1];
        const dim2Values = matrix.dimension_values[dim2];

        let html = `
            <table class="matrix-table">
                <thead>
                    <tr>
                        <th>${dim1} / ${dim2}</th>
        `;

        // Column headers
        dim2Values.forEach(v => {
            html += `<th>${v.display_name}</th>`;
        });
        html += '<th class="total-header">Total</th></tr></thead><tbody>';

        // Rows
        dim1Values.forEach(v1 => {
            html += `<tr><td>${v1.display_name}</td>`;

            dim2Values.forEach(v2 => {
                const key = `${v1.value}_${v2.value}`;
                const existingValue = this.getExistingValue(v1.value, v2.value);
                html += `
                    <td>
                        <input type="number"
                               class="matrix-input"
                               data-dim1="${v1.value}"
                               data-dim2="${v2.value}"
                               value="${existingValue || ''}"
                               min="0">
                    </td>
                `;
            });

            html += `<td class="row-total" data-row="${v1.value}">0</td></tr>`;
        });

        // Total row
        html += '<tr class="total-row"><td>Total</td>';
        dim2Values.forEach(v => {
            html += `<td class="col-total" data-col="${v.value}">0</td>`;
        });
        html += '<td class="grand-total">0</td></tr></tbody></table>';

        this.matrixContainer.innerHTML = html;
    }

    attachCalculationListeners() {
        const inputs = this.matrixContainer.querySelectorAll('.matrix-input');
        inputs.forEach(input => {
            input.addEventListener('input', () => this.calculateTotals());
        });
    }

    calculateTotals() {
        const inputs = this.matrixContainer.querySelectorAll('.matrix-input');
        const [dim1, dim2] = this.currentMatrix.dimensions;

        // Calculate row totals
        const rowTotals = {};
        const colTotals = {};
        let grandTotal = 0;

        inputs.forEach(input => {
            const value = parseFloat(input.value) || 0;
            const row = input.dataset.dim1;
            const col = input.dataset.dim2;

            rowTotals[row] = (rowTotals[row] || 0) + value;
            colTotals[col] = (colTotals[col] || 0) + value;
            grandTotal += value;
        });

        // Update UI
        Object.keys(rowTotals).forEach(row => {
            const cell = this.matrixContainer.querySelector(`.row-total[data-row="${row}"]`);
            if (cell) cell.textContent = rowTotals[row];
        });

        Object.keys(colTotals).forEach(col => {
            const cell = this.matrixContainer.querySelector(`.col-total[data-col="${col}"]`);
            if (cell) cell.textContent = colTotals[col];
        });

        const grandTotalCell = this.matrixContainer.querySelector('.grand-total');
        if (grandTotalCell) grandTotalCell.textContent = grandTotal;
    }

    async submitDimensionalData() {
        const inputs = this.matrixContainer.querySelectorAll('.matrix-input');
        const breakdowns = [];

        inputs.forEach(input => {
            if (input.value) {
                const dimensions = {};
                const [dim1, dim2] = this.currentMatrix.dimensions;
                dimensions[dim1] = input.dataset.dim1;
                dimensions[dim2] = input.dataset.dim2;

                breakdowns.push({
                    dimensions: dimensions,
                    raw_value: parseFloat(input.value),
                    notes: null
                });
            }
        });

        const payload = {
            field_id: this.currentFieldId,
            entity_id: this.currentEntityId,
            reporting_date: this.currentReportingDate,
            dimensional_data: {
                dimensions: this.currentMatrix.dimensions,
                breakdowns: breakdowns
            }
        };

        const response = await fetch('/user/v2/api/submit-dimensional-data', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (result.success) {
            showSuccess('Data saved successfully!');
            this.modal.close();
        } else {
            showError(result.error);
        }
    }
}
```

## Success Criteria
- ✓ 2D dimension matrix renders correctly
- ✓ Real-time totals calculate accurately
- ✓ Data saves with proper JSON structure
- ✓ Validation prevents invalid submissions
- ✓ Existing data loads into matrix
- ✓ Multi-dimensional fields supported
- ✓ Mobile responsive matrix
- ✓ Accessibility maintained

## Implementation Tasks
1. Create DimensionalDataService
2. Create AggregationService
3. Implement API endpoints
4. Build matrix rendering JavaScript
5. Add real-time calculation
6. Implement data submission
7. Add validation logic
8. Test with various dimension configurations
9. Handle edge cases (1D, 3D+ dimensions)
10. Performance optimization
