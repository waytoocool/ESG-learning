/**
 * Computation Context Handler
 * Handles displaying computation context modals for computed fields
 *
 * Features:
 * - Formula display in human-readable format
 * - Dependency tree visualization
 * - Step-by-step calculation breakdown
 * - Historical trend charts
 * - Missing dependency warnings
 */

class ComputationContextHandler {
    constructor(modalElement) {
        this.modal = modalElement;
        this.currentFieldId = null;
        this.currentEntityId = null;
        this.currentDate = null;
        this.chartInstance = null;
    }

    /**
     * Load and display computation context modal
     */
    async loadComputationContext(fieldId, entityId, reportingDate) {
        this.currentFieldId = fieldId;
        this.currentEntityId = entityId;
        this.currentDate = reportingDate;

        try {
            // Show loading state
            this.showLoading();

            // Fetch context data
            const response = await fetch(
                `/user/v2/api/computation-context/${fieldId}?entity_id=${entityId}&reporting_date=${reportingDate}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                this.renderContext(data.context);
                this.modal.showModal();
            } else {
                this.showError(data.error || 'Failed to load computation context');
            }
        } catch (error) {
            console.error('Error loading computation context:', error);
            this.showError('Failed to load computation context. Please try again.');
        }
    }

    /**
     * Show loading state
     */
    showLoading() {
        const container = this.modal.querySelector('.context-container');
        container.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Loading computation context...</p>
            </div>
        `;
    }

    /**
     * Show error message
     */
    showError(message) {
        const container = this.modal.querySelector('.context-container');
        container.innerHTML = `
            <div class="error-state">
                <div class="error-icon">⚠️</div>
                <p>${message}</p>
                <button onclick="document.getElementById('computationContextModal').close()" class="btn-primary">
                    Close
                </button>
            </div>
        `;
    }

    /**
     * Render computation context in modal
     */
    renderContext(context) {
        const container = this.modal.querySelector('.context-container');

        let html = `
            <div class="computation-context">
                <!-- Header -->
                <div class="context-header">
                    <div class="header-content">
                        <h3>${this.escapeHtml(context.field.field_name)}</h3>
                        <p class="field-code">${this.escapeHtml(context.field.field_code || '')}</p>
                    </div>
                    <span class="status-badge ${context.calculation_status}">
                        ${this.formatStatus(context.calculation_status)}
                    </span>
                </div>

                <!-- Formula Display -->
                <div class="formula-section">
                    <h4>📐 Formula</h4>
                    <div class="formula-display">${this.escapeHtml(context.formula)}</div>
                </div>

                <!-- Missing Dependencies Warning -->
                ${this.renderMissingDependencies(context.missing_dependencies)}

                <!-- Calculation Steps -->
                <div class="steps-section">
                    <h4>🔢 Calculation Steps</h4>
                    ${this.renderCalculationSteps(context.calculation_steps)}
                </div>

                <!-- Dependency Tree -->
                <div class="dependencies-section">
                    <h4>🌳 Dependencies</h4>
                    ${this.renderDependencyTree(context.dependency_tree)}
                </div>

                <!-- Historical Trend -->
                ${this.renderHistoricalTrend(context.historical_trend)}
            </div>
        `;

        container.innerHTML = html;

        // Render trend chart if data available
        if (context.historical_trend && context.historical_trend.data_points && context.historical_trend.data_points.length > 0) {
            this.renderTrendChart(context.historical_trend);
        }
    }

    /**
     * Render step-by-step calculation breakdown
     */
    renderCalculationSteps(steps) {
        if (!steps || steps.length === 0) {
            return '<p class="no-data">No calculation steps available</p>';
        }

        let html = '<div class="calculation-steps">';

        steps.forEach(step => {
            html += `
                <div class="step">
                    <div class="step-number">${step.step}</div>
                    <div class="step-content">
                        <div class="step-description">${this.escapeHtml(step.description)}</div>
                        <div class="step-operation">${this.escapeHtml(step.operation)}</div>
                        ${this.renderStepInputs(step.inputs)}
                        <div class="step-output">
                            Result: <strong>${this.formatValue(step.output)} ${this.escapeHtml(step.unit || '')}</strong>
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    /**
     * Render step inputs
     */
    renderStepInputs(inputs) {
        if (!inputs || Object.keys(inputs).length === 0) {
            return '';
        }

        let html = '<div class="step-inputs"><strong>Inputs:</strong> ';
        const inputStrings = [];

        for (const [key, value] of Object.entries(inputs)) {
            inputStrings.push(`${this.escapeHtml(key)}: ${this.formatValue(value)}`);
        }

        html += inputStrings.join(', ') + '</div>';
        return html;
    }

    /**
     * Render hierarchical dependency tree
     */
    renderDependencyTree(tree) {
        if (!tree) {
            return '<p class="no-data">No dependencies</p>';
        }

        return '<div class="dependency-tree">' + this.renderTreeNode(tree, 0) + '</div>';
    }

    /**
     * Recursively render tree nodes
     */
    renderTreeNode(node, level) {
        const indent = level * 20;
        const statusClass = node.status || 'unknown';
        const hasChildren = node.dependencies && node.dependencies.length > 0;

        let html = `
            <div class="tree-node level-${level}" style="margin-left: ${indent}px;">
                <div class="node-content ${statusClass}">
                    <span class="node-icon">${this.getStatusIcon(node.status)}</span>
                    <span class="node-name">${this.escapeHtml(node.field_name)}</span>
                    <span class="node-value">${this.formatValue(node.value)}</span>
                </div>
        `;

        if (hasChildren) {
            html += '<div class="node-children">';
            node.dependencies.forEach(child => {
                html += this.renderTreeNode(child, level + 1);
            });
            html += '</div>';
        }

        html += '</div>';
        return html;
    }

    /**
     * Render warning for missing dependencies
     */
    renderMissingDependencies(missing) {
        if (!missing || missing.length === 0) {
            return '';
        }

        let html = `
            <div class="missing-dependencies warning">
                <h4>⚠️ Missing Dependencies</h4>
                <p>The following dependencies are missing data for the selected date:</p>
                <ul>
        `;

        missing.forEach(item => {
            html += `
                <li>
                    <strong>${this.escapeHtml(item.field_name)}</strong>:
                    ${this.escapeHtml(item.reason)}
                </li>
            `;
        });

        html += '</ul></div>';
        return html;
    }

    /**
     * Render historical trend section
     */
    renderHistoricalTrend(trend) {
        if (!trend || !trend.data_points || trend.data_points.length === 0) {
            return '';
        }

        return `
            <div class="trend-section">
                <h4>📈 Historical Trend</h4>
                <div class="trend-stats">
                    <div class="trend-stat">
                        <span class="stat-label">Trend:</span>
                        <span class="stat-value trend-${trend.trend}">
                            ${this.getTrendIcon(trend.trend)} ${this.formatTrend(trend.trend)}
                        </span>
                    </div>
                    <div class="trend-stat">
                        <span class="stat-label">Change Rate:</span>
                        <span class="stat-value">${this.formatPercentage(trend.change_rate)}</span>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="trend-chart"></canvas>
                </div>
            </div>
        `;
    }

    /**
     * Render trend chart using Chart.js
     */
    renderTrendChart(trendData) {
        // Wait for next tick to ensure canvas element exists
        setTimeout(() => {
            const ctx = document.getElementById('trend-chart');
            if (!ctx) return;

            // Destroy previous chart if exists
            if (this.chartInstance) {
                this.chartInstance.destroy();
            }

            const labels = trendData.data_points.map(d => this.formatDate(d.date));
            const values = trendData.data_points.map(d => d.value || 0);

            this.chartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Calculated Value',
                        data: values,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.1,
                        fill: true,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            callbacks: {
                                label: (context) => {
                                    const dataPoint = trendData.data_points[context.dataIndex];
                                    return `Value: ${this.formatValue(context.parsed.y)} (${dataPoint.status})`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: (value) => this.formatValue(value)
                            }
                        }
                    },
                    interaction: {
                        mode: 'nearest',
                        axis: 'x',
                        intersect: false
                    }
                }
            });
        }, 100);
    }

    /**
     * Format status for display
     */
    formatStatus(status) {
        const statusMap = {
            'complete': 'Complete',
            'partial': 'Partial Data',
            'failed': 'Calculation Failed',
            'no_data': 'No Data'
        };
        return statusMap[status] || status;
    }

    /**
     * Get status icon
     */
    getStatusIcon(status) {
        const iconMap = {
            'available': '✓',
            'missing': '✗',
            'partial': '⚠'
        };
        return iconMap[status] || '•';
    }

    /**
     * Format trend for display
     */
    formatTrend(trend) {
        const trendMap = {
            'increasing': 'Increasing',
            'decreasing': 'Decreasing',
            'stable': 'Stable'
        };
        return trendMap[trend] || trend;
    }

    /**
     * Get trend icon
     */
    getTrendIcon(trend) {
        const iconMap = {
            'increasing': '↑',
            'decreasing': '↓',
            'stable': '→'
        };
        return iconMap[trend] || '•';
    }

    /**
     * Format value for display
     */
    formatValue(value) {
        if (value === null || value === undefined) {
            return 'N/A';
        }
        if (typeof value === 'number') {
            return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
        }
        return value;
    }

    /**
     * Format percentage
     */
    formatPercentage(value) {
        if (value === null || value === undefined) {
            return 'N/A';
        }
        const sign = value >= 0 ? '+' : '';
        return `${sign}${value.toFixed(2)}%`;
    }

    /**
     * Format date
     */
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('computationContextModal');
    if (modal) {
        window.computationContextHandler = new ComputationContextHandler(modal);
    }
});

/**
 * Global function to show computation context
 * Called from dashboard when user clicks info icon on computed field
 */
function showComputationContext(fieldId, entityId, reportingDate) {
    if (window.computationContextHandler) {
        window.computationContextHandler.loadComputationContext(fieldId, entityId, reportingDate);
    } else {
        console.error('ComputationContextHandler not initialized');
    }
}
