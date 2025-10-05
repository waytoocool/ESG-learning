# Phase 3: Computation Context - Requirements & Specifications

## Overview
Implement contextual information modals for computed fields that show formulas, dependencies, calculation steps, and historical trends to help users understand how computed values are derived.

## Requirements

### 3.1 Computation Context Modal
- [ ] Display formula/calculation logic in user-friendly format
- [ ] Show dependency tree (which raw fields feed into this computed field)
- [ ] Display step-by-step calculation breakdown
- [ ] Show current values used in calculation
- [ ] Highlight missing dependencies or data gaps
- [ ] Support nested computed fields (computed fields that depend on other computed fields)

### 3.2 Dependency Visualization
- [ ] Visual tree or graph showing data flow
- [ ] Color-code dependencies by status:
  - Green: All data available
  - Yellow: Partial data available
  - Red: Missing required data
- [ ] Interactive - click on dependency to view its details
- [ ] Show entity-level dependencies for aggregations

### 3.3 Historical Trends Integration
- [ ] Display historical values in a trend chart
- [ ] Show calculation history over time
- [ ] Highlight anomalies or significant changes
- [ ] Compare against previous periods
- [ ] Export trend data

### 3.4 Formula Display Enhancement
- [ ] Convert technical formulas to readable format
- [ ] Display unit conversions in calculations
- [ ] Show intermediate calculation steps
- [ ] Provide contextual help for formula components
- [ ] Support for complex formulas (aggregations, conditionals, etc.)

### 3.5 UI/UX Requirements
- [ ] Accessible via info icon next to computed field values
- [ ] Modal or expandable panel interface
- [ ] Responsive design for mobile devices
- [ ] Print-friendly view for documentation
- [ ] Keyboard navigation support

## Technical Specifications

### Backend Services

#### ComputationContextService
```python
# app/services/user_v2/computation_context_service.py

class ComputationContextService:
    """Service for handling computation context and dependency analysis."""

    @staticmethod
    def get_computation_context(field_id, entity_id, reporting_date):
        """
        Get complete computation context for a computed field.

        Returns:
        {
            'field': {field details},
            'formula': 'readable formula string',
            'dependencies': [list of dependent fields],
            'dependency_tree': {hierarchical dependency structure},
            'calculation_steps': [step-by-step breakdown],
            'current_values': {field_id: value mapping},
            'missing_dependencies': [list of missing data],
            'historical_trend': [historical values],
            'last_calculated': datetime,
            'calculation_status': 'complete'|'partial'|'failed'
        }
        """
        pass

    @staticmethod
    def build_dependency_tree(field_id, entity_id, max_depth=5):
        """
        Build hierarchical dependency tree for a computed field.

        Returns:
        {
            'field_id': field_id,
            'field_name': 'Field Name',
            'value': current_value,
            'status': 'available'|'missing'|'partial',
            'dependencies': [
                {recursive tree structure for each dependency}
            ]
        }
        """
        pass

    @staticmethod
    def get_calculation_steps(field_id, entity_id, reporting_date):
        """
        Break down calculation into step-by-step process.

        Returns:
        [
            {
                'step': 1,
                'description': 'Sum all employee counts by department',
                'operation': 'SUM',
                'inputs': {field_id: value},
                'output': value,
                'unit': 'employees'
            },
            ...
        ]
        """
        pass

    @staticmethod
    def format_formula_for_display(formula_expression):
        """
        Convert technical formula to user-friendly format.

        Example:
        Input: "SUM(field_abc123) / COUNT(field_xyz789)"
        Output: "Total Energy Consumption (kWh) ÷ Number of Facilities"
        """
        pass

    @staticmethod
    def get_historical_calculation_trend(field_id, entity_id, periods=12):
        """
        Get historical trend of calculated values.

        Returns:
        {
            'field_id': field_id,
            'entity_id': entity_id,
            'data_points': [
                {
                    'date': '2024-01-01',
                    'value': 1000,
                    'status': 'complete',
                    'calculation_time': datetime
                },
                ...
            ],
            'trend': 'increasing'|'decreasing'|'stable',
            'change_rate': 5.2  # percentage
        }
        """
        pass

    @staticmethod
    def validate_dependencies(field_id, entity_id, reporting_date):
        """
        Check if all dependencies are satisfied.

        Returns:
        {
            'is_complete': True|False,
            'satisfied_count': 5,
            'total_count': 6,
            'missing': [
                {
                    'field_id': 'abc123',
                    'field_name': 'Employee Count',
                    'reason': 'No data submitted for this period'
                }
            ]
        }
        """
        pass
```

### API Endpoints

#### 1. Get Computation Context
```python
@user_v2_bp.route('/api/computation-context/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_computation_context(field_id):
    """
    Get complete computation context for a computed field.

    Query Parameters:
    - entity_id: Entity ID
    - reporting_date: Date for calculation

    Returns:
    {
        'success': True,
        'context': {computation context object}
    }
    """
    entity_id = request.args.get('entity_id')
    reporting_date = request.args.get('reporting_date')

    context = ComputationContextService.get_computation_context(
        field_id, entity_id, reporting_date
    )

    return jsonify({
        'success': True,
        'context': context
    })
```

#### 2. Get Dependency Tree
```python
@user_v2_bp.route('/api/dependency-tree/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_dependency_tree(field_id):
    """
    Get hierarchical dependency tree for a computed field.

    Query Parameters:
    - entity_id: Entity ID
    - max_depth: Maximum depth for tree (default: 5)

    Returns:
    {
        'success': True,
        'tree': {dependency tree object}
    }
    """
    entity_id = request.args.get('entity_id')
    max_depth = int(request.args.get('max_depth', 5))

    tree = ComputationContextService.build_dependency_tree(
        field_id, entity_id, max_depth
    )

    return jsonify({
        'success': True,
        'tree': tree
    })
```

#### 3. Get Calculation Steps
```python
@user_v2_bp.route('/api/calculation-steps/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_calculation_steps(field_id):
    """
    Get step-by-step calculation breakdown.

    Query Parameters:
    - entity_id: Entity ID
    - reporting_date: Date for calculation

    Returns:
    {
        'success': True,
        'steps': [calculation steps]
    }
    """
    entity_id = request.args.get('entity_id')
    reporting_date = request.args.get('reporting_date')

    steps = ComputationContextService.get_calculation_steps(
        field_id, entity_id, reporting_date
    )

    return jsonify({
        'success': True,
        'steps': steps
    })
```

#### 4. Get Historical Trend
```python
@user_v2_bp.route('/api/historical-trend/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_historical_trend(field_id):
    """
    Get historical calculation trend.

    Query Parameters:
    - entity_id: Entity ID
    - periods: Number of periods (default: 12)

    Returns:
    {
        'success': True,
        'trend': {trend data object}
    }
    """
    entity_id = request.args.get('entity_id')
    periods = int(request.args.get('periods', 12))

    trend = ComputationContextService.get_historical_calculation_trend(
        field_id, entity_id, periods
    )

    return jsonify({
        'success': True,
        'trend': trend
    })
```

#### 5. Validate Dependencies
```python
@user_v2_bp.route('/api/validate-dependencies/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def validate_dependencies(field_id):
    """
    Check if all dependencies are satisfied.

    Query Parameters:
    - entity_id: Entity ID
    - reporting_date: Date to check

    Returns:
    {
        'success': True,
        'validation': {validation results}
    }
    """
    entity_id = request.args.get('entity_id')
    reporting_date = request.args.get('reporting_date')

    validation = ComputationContextService.validate_dependencies(
        field_id, entity_id, reporting_date
    )

    return jsonify({
        'success': True,
        'validation': validation
    })
```

### Frontend Implementation

#### JavaScript Handler
```javascript
// app/static/js/user_v2/computation_context_handler.js

class ComputationContextHandler {
    constructor(modalElement) {
        this.modal = modalElement;
        this.currentFieldId = null;
        this.currentEntityId = null;
        this.currentDate = null;
    }

    async loadComputationContext(fieldId, entityId, reportingDate) {
        /**
         * Load and display computation context modal.
         */
        this.currentFieldId = fieldId;
        this.currentEntityId = entityId;
        this.currentDate = reportingDate;

        // Fetch context data
        const response = await fetch(
            `/user/v2/api/computation-context/${fieldId}?entity_id=${entityId}&reporting_date=${reportingDate}`
        );
        const data = await response.json();

        if (data.success) {
            this.renderContext(data.context);
            this.modal.show();
        }
    }

    renderContext(context) {
        /**
         * Render computation context in modal.
         */
        const container = this.modal.querySelector('.context-container');

        let html = `
            <div class="computation-context">
                <!-- Header -->
                <div class="context-header">
                    <h3>${context.field.field_name}</h3>
                    <span class="status-badge ${context.calculation_status}">
                        ${this.formatStatus(context.calculation_status)}
                    </span>
                </div>

                <!-- Formula Display -->
                <div class="formula-section">
                    <h4>Formula</h4>
                    <div class="formula-display">${context.formula}</div>
                </div>

                <!-- Calculation Steps -->
                <div class="steps-section">
                    <h4>Calculation Steps</h4>
                    ${this.renderCalculationSteps(context.calculation_steps)}
                </div>

                <!-- Dependency Tree -->
                <div class="dependencies-section">
                    <h4>Dependencies</h4>
                    ${this.renderDependencyTree(context.dependency_tree)}
                </div>

                <!-- Missing Dependencies Warning -->
                ${this.renderMissingDependencies(context.missing_dependencies)}

                <!-- Historical Trend -->
                <div class="trend-section">
                    <h4>Historical Trend</h4>
                    <canvas id="trend-chart"></canvas>
                </div>
            </div>
        `;

        container.innerHTML = html;

        // Render trend chart
        if (context.historical_trend && context.historical_trend.length > 0) {
            this.renderTrendChart(context.historical_trend);
        }
    }

    renderCalculationSteps(steps) {
        /**
         * Render step-by-step calculation breakdown.
         */
        if (!steps || steps.length === 0) {
            return '<p class="no-data">No calculation steps available</p>';
        }

        let html = '<div class="calculation-steps">';

        steps.forEach(step => {
            html += `
                <div class="step">
                    <div class="step-number">${step.step}</div>
                    <div class="step-content">
                        <div class="step-description">${step.description}</div>
                        <div class="step-operation">${step.operation}</div>
                        <div class="step-inputs">
                            ${this.formatStepInputs(step.inputs)}
                        </div>
                        <div class="step-output">
                            Result: <strong>${step.output} ${step.unit || ''}</strong>
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    renderDependencyTree(tree) {
        /**
         * Render hierarchical dependency tree.
         */
        if (!tree) {
            return '<p class="no-data">No dependencies</p>';
        }

        return this.renderTreeNode(tree, 0);
    }

    renderTreeNode(node, level) {
        /**
         * Recursively render tree nodes.
         */
        const indent = level * 20;
        const statusClass = node.status || 'unknown';

        let html = `
            <div class="tree-node" style="margin-left: ${indent}px;">
                <div class="node-content ${statusClass}">
                    <span class="node-icon">${this.getStatusIcon(node.status)}</span>
                    <span class="node-name">${node.field_name}</span>
                    <span class="node-value">${node.value || 'N/A'}</span>
                </div>
        `;

        if (node.dependencies && node.dependencies.length > 0) {
            html += '<div class="node-children">';
            node.dependencies.forEach(child => {
                html += this.renderTreeNode(child, level + 1);
            });
            html += '</div>';
        }

        html += '</div>';
        return html;
    }

    renderMissingDependencies(missing) {
        /**
         * Render warning for missing dependencies.
         */
        if (!missing || missing.length === 0) {
            return '';
        }

        let html = `
            <div class="missing-dependencies warning">
                <h4>⚠️ Missing Dependencies</h4>
                <ul>
        `;

        missing.forEach(item => {
            html += `
                <li>
                    <strong>${item.field_name}</strong>: ${item.reason}
                </li>
            `;
        });

        html += '</ul></div>';
        return html;
    }

    renderTrendChart(trendData) {
        /**
         * Render historical trend chart using Chart.js.
         */
        const ctx = document.getElementById('trend-chart');

        const labels = trendData.map(d => d.date);
        const values = trendData.map(d => d.value);

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Calculated Value',
                    data: values,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    formatStatus(status) {
        const statusMap = {
            'complete': 'Complete',
            'partial': 'Partial Data',
            'failed': 'Calculation Failed'
        };
        return statusMap[status] || status;
    }

    getStatusIcon(status) {
        const iconMap = {
            'available': '✓',
            'missing': '✗',
            'partial': '⚠'
        };
        return iconMap[status] || '•';
    }

    formatStepInputs(inputs) {
        if (!inputs || Object.keys(inputs).length === 0) {
            return 'No inputs';
        }

        return Object.entries(inputs)
            .map(([key, value]) => `${key}: ${value}`)
            .join(', ');
    }
}
```

#### CSS Styling
```css
/* app/static/css/user_v2/computation_context.css */

.computation-context {
    padding: 20px;
}

.context-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid #e0e0e0;
}

.context-header h3 {
    margin: 0;
    color: #2c3e50;
}

.status-badge {
    padding: 5px 15px;
    border-radius: 20px;
    font-size: 0.9em;
    font-weight: 500;
}

.status-badge.complete {
    background-color: #27ae60;
    color: white;
}

.status-badge.partial {
    background-color: #f39c12;
    color: white;
}

.status-badge.failed {
    background-color: #e74c3c;
    color: white;
}

.formula-section,
.steps-section,
.dependencies-section,
.trend-section {
    margin-bottom: 30px;
}

.formula-section h4,
.steps-section h4,
.dependencies-section h4,
.trend-section h4 {
    color: #34495e;
    margin-bottom: 15px;
    font-size: 1.1em;
}

.formula-display {
    background-color: #f8f9fa;
    border-left: 4px solid #3498db;
    padding: 15px;
    font-family: 'Courier New', monospace;
    font-size: 1.1em;
    color: #2c3e50;
    border-radius: 4px;
}

.calculation-steps {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.step {
    display: flex;
    gap: 15px;
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 15px;
    transition: box-shadow 0.2s;
}

.step:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.step-number {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    background-color: #3498db;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 1.2em;
}

.step-content {
    flex-grow: 1;
}

.step-description {
    font-weight: 500;
    color: #2c3e50;
    margin-bottom: 8px;
}

.step-operation {
    color: #7f8c8d;
    font-size: 0.9em;
    margin-bottom: 8px;
}

.step-inputs {
    color: #34495e;
    font-size: 0.95em;
    margin-bottom: 8px;
}

.step-output {
    color: #27ae60;
    font-weight: 500;
    padding-top: 8px;
    border-top: 1px solid #ecf0f1;
}

.tree-node {
    margin-bottom: 5px;
}

.node-content {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.node-content:hover {
    background-color: #f8f9fa;
}

.node-content.available {
    border-left: 3px solid #27ae60;
}

.node-content.missing {
    border-left: 3px solid #e74c3c;
}

.node-content.partial {
    border-left: 3px solid #f39c12;
}

.node-icon {
    font-weight: bold;
    font-size: 1.1em;
}

.node-name {
    flex-grow: 1;
    color: #2c3e50;
}

.node-value {
    font-weight: 500;
    color: #3498db;
}

.missing-dependencies {
    background-color: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 30px;
}

.missing-dependencies h4 {
    color: #856404;
    margin-bottom: 10px;
}

.missing-dependencies ul {
    margin: 0;
    padding-left: 20px;
}

.missing-dependencies li {
    color: #856404;
    margin-bottom: 8px;
}

.trend-section canvas {
    max-height: 300px;
}

.no-data {
    color: #7f8c8d;
    font-style: italic;
    padding: 10px;
}

/* Responsive Design */
@media (max-width: 768px) {
    .context-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
    }

    .step {
        flex-direction: column;
    }

    .step-number {
        align-self: flex-start;
    }
}
```

### Integration with Dashboard

#### Update Dashboard Template
```html
<!-- Add to app/templates/user_v2/dashboard.html -->

<!-- Computation Context Modal -->
<dialog id="computationContextModal" class="modal">
    <div class="modal-header">
        <h2>Computation Context</h2>
        <button class="close-btn" onclick="document.getElementById('computationContextModal').close()">×</button>
    </div>
    <div class="modal-body">
        <div class="context-container">
            <!-- Content will be populated by JavaScript -->
        </div>
    </div>
</dialog>

<!-- Add info icon to computed fields in data table -->
<script>
    const computationContextHandler = new ComputationContextHandler(
        document.getElementById('computationContextModal')
    );

    function showComputationContext(fieldId, entityId, reportingDate) {
        computationContextHandler.loadComputationContext(fieldId, entityId, reportingDate);
    }
</script>
```

## Success Criteria

- ✓ Computation context modal displays for all computed fields
- ✓ Formula shows in user-friendly readable format
- ✓ Dependency tree renders with proper hierarchy
- ✓ Calculation steps show intermediate results
- ✓ Missing dependencies highlighted clearly
- ✓ Historical trend chart displays correctly
- ✓ All API endpoints return expected data
- ✓ Responsive design works on mobile
- ✓ Performance: Modal loads in < 1 second
- ✓ Accessibility: Keyboard navigation supported

## Implementation Tasks

1. Create ComputationContextService with all methods
2. Implement 5 API endpoints
3. Build ComputationContextHandler JavaScript class
4. Create computation_context.css styling
5. Integrate modal into dashboard template
6. Add info icons to computed fields in data table
7. Implement Chart.js for trend visualization
8. Test with various computed field types
9. Handle edge cases (circular dependencies, missing data)
10. Performance optimization for complex dependency trees

## Dependencies

- Chart.js library for trend visualization
- Existing computed field calculation logic in app/services/aggregation.py
- ESGData model for historical data queries
- FrameworkDataField model for field metadata

## Estimated Effort

- Backend Development: 2-3 days
- Frontend Development: 2-3 days
- Testing & Refinement: 1-2 days
- **Total: 5-8 days**
