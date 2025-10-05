/**
 * Dimensional Data Handler for User Dashboard V2
 * Handles dimensional data matrix rendering and submission
 */

class DimensionalDataHandler {
    /**
     * Initialize the dimensional data handler
     * @param {HTMLElement} containerElement - Container element for the dimension matrix
     */
    constructor(containerElement) {
        this.container = containerElement;
        this.currentMatrix = null;
        this.currentFieldId = null;
        this.currentEntityId = null;
        this.currentReportingDate = null;
        this.matrixData = {};
    }

    /**
     * Load dimension matrix from API
     * @param {string} fieldId - Framework field ID
     * @param {number} entityId - Entity ID
     * @param {string} reportingDate - Reporting date (YYYY-MM-DD)
     */
    async loadDimensionMatrix(fieldId, entityId, reportingDate) {
        try {
            const response = await fetch(
                `/user/v2/api/dimension-matrix/${fieldId}?entity_id=${entityId}&reporting_date=${reportingDate}`
            );

            if (!response.ok) {
                throw new Error('Failed to load dimension matrix');
            }

            const matrix = await response.json();

            if (!matrix.success) {
                throw new Error(matrix.error || 'Failed to load dimension matrix');
            }

            this.currentMatrix = matrix;
            this.currentFieldId = fieldId;
            this.currentEntityId = entityId;
            this.currentReportingDate = reportingDate;

            this.renderMatrix(matrix);

            return matrix;
        } catch (error) {
            console.error('Error loading dimension matrix:', error);
            this.showError('Failed to load dimension matrix: ' + error.message);
            throw error;
        }
    }

    /**
     * Render the dimension matrix based on number of dimensions
     * @param {Object} matrix - Matrix data from API
     */
    renderMatrix(matrix) {
        if (!matrix.has_dimensions || matrix.dimensions.length === 0) {
            this.renderSimpleInput(matrix);
            return;
        }

        // Clear container
        this.container.innerHTML = '';

        // Add header
        const header = document.createElement('h4');
        header.className = 'dimension-matrix-header';
        header.textContent = 'Dimensional Breakdown';
        this.container.appendChild(header);

        // Render based on number of dimensions
        if (matrix.dimensions.length === 1) {
            this.render1DMatrix(matrix);
        } else if (matrix.dimensions.length === 2) {
            this.render2DMatrix(matrix);
        } else {
            this.renderMultiDimensionalList(matrix);
        }

        // Attach calculation listeners
        this.attachCalculationListeners();

        // Load existing data if available
        if (matrix.existing_data) {
            this.loadExistingData(matrix.existing_data);
        }
    }

    /**
     * Render 1-dimensional matrix (simple list)
     * @param {Object} matrix - Matrix data
     */
    render1DMatrix(matrix) {
        const dim = matrix.dimensions[0];
        const values = matrix.dimension_values[dim];

        const html = `
            <div class="dimension-1d-container">
                <h5>${dim}</h5>
                <table class="matrix-table matrix-1d">
                    <thead>
                        <tr>
                            <th>${dim}</th>
                            <th>Value</th>
                            <th>Notes</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${values.map(v => `
                            <tr>
                                <td>${v.display_name}</td>
                                <td>
                                    <input type="number"
                                           class="matrix-input"
                                           data-dim1="${v.value}"
                                           step="0.01"
                                           min="0"
                                           placeholder="0">
                                </td>
                                <td>
                                    <input type="text"
                                           class="matrix-notes"
                                           data-dim1="${v.value}"
                                           placeholder="Optional notes">
                                </td>
                            </tr>
                        `).join('')}
                        <tr class="total-row">
                            <td><strong>Total</strong></td>
                            <td class="total-cell">0</td>
                            <td></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;

        this.container.insertAdjacentHTML('beforeend', html);
    }

    /**
     * Render 2-dimensional matrix (table grid)
     * @param {Object} matrix - Matrix data
     */
    render2DMatrix(matrix) {
        const [dim1, dim2] = matrix.dimensions;
        const dim1Values = matrix.dimension_values[dim1];
        const dim2Values = matrix.dimension_values[dim2];

        let html = `
            <div class="dimension-2d-container">
                <table class="matrix-table matrix-2d">
                    <thead>
                        <tr>
                            <th class="corner-cell">${dim1} / ${dim2}</th>
        `;

        // Column headers
        dim2Values.forEach(v => {
            html += `<th class="col-header">${v.display_name}</th>`;
        });
        html += '<th class="total-header">Total</th></tr></thead><tbody>';

        // Rows
        dim1Values.forEach(v1 => {
            html += `<tr><td class="row-header">${v1.display_name}</td>`;

            dim2Values.forEach(v2 => {
                html += `
                    <td>
                        <input type="number"
                               class="matrix-input"
                               data-dim1="${v1.value}"
                               data-dim2="${v2.value}"
                               step="0.01"
                               min="0"
                               placeholder="0">
                    </td>
                `;
            });

            html += `<td class="row-total" data-row="${v1.value}">0</td></tr>`;
        });

        // Total row
        html += '<tr class="total-row"><td><strong>Total</strong></td>';
        dim2Values.forEach(v => {
            html += `<td class="col-total" data-col="${v.value}">0</td>`;
        });
        html += '<td class="grand-total">0</td></tr></tbody></table></div>';

        this.container.insertAdjacentHTML('beforeend', html);
    }

    /**
     * Render multi-dimensional data as list
     * @param {Object} matrix - Matrix data
     */
    renderMultiDimensionalList(matrix) {
        const combinations = matrix.combinations;

        let html = `
            <div class="dimension-multi-container">
                <p class="dimension-info">
                    ${matrix.dimensions.length} dimensions: ${matrix.dimensions.join(', ')}
                </p>
                <div class="combination-list">
        `;

        combinations.forEach((combo, index) => {
            const label = Object.entries(combo)
                .map(([k, v]) => `${k}: ${v}`)
                .join(' | ');

            html += `
                <div class="combination-item">
                    <label class="combination-label">${label}</label>
                    <input type="number"
                           class="matrix-input"
                           data-combination='${JSON.stringify(combo)}'
                           data-index="${index}"
                           step="0.01"
                           min="0"
                           placeholder="0">
                </div>
            `;
        });

        html += `
                </div>
                <div class="multi-total">
                    <strong>Total:</strong> <span class="grand-total">0</span>
                </div>
            </div>
        `;

        this.container.insertAdjacentHTML('beforeend', html);
    }

    /**
     * Render simple input for non-dimensional fields
     * @param {Object} matrix - Matrix data
     */
    renderSimpleInput(matrix) {
        const html = `
            <div class="simple-input-container">
                <p>This field does not have dimensional breakdowns.</p>
            </div>
        `;
        this.container.innerHTML = html;
    }

    /**
     * Attach event listeners for real-time calculation
     */
    attachCalculationListeners() {
        const inputs = this.container.querySelectorAll('.matrix-input');
        inputs.forEach(input => {
            input.addEventListener('input', () => this.calculateTotals());
        });

        // Initial calculation
        this.calculateTotals();
    }

    /**
     * Calculate and update totals in real-time
     */
    calculateTotals() {
        const inputs = this.container.querySelectorAll('.matrix-input');

        if (!this.currentMatrix || !this.currentMatrix.dimensions) {
            return;
        }

        const dimensions = this.currentMatrix.dimensions;

        if (dimensions.length === 1) {
            this.calculate1DTotals(inputs);
        } else if (dimensions.length === 2) {
            this.calculate2DTotals(inputs);
        } else {
            this.calculateMultiDimensionalTotals(inputs);
        }
    }

    /**
     * Calculate totals for 1D matrix
     * @param {NodeList} inputs - Input elements
     */
    calculate1DTotals(inputs) {
        let total = 0;

        inputs.forEach(input => {
            const value = parseFloat(input.value) || 0;
            total += value;
        });

        const totalCell = this.container.querySelector('.total-cell');
        if (totalCell) {
            totalCell.textContent = total.toFixed(2);
        }
    }

    /**
     * Calculate totals for 2D matrix
     * @param {NodeList} inputs - Input elements
     */
    calculate2DTotals(inputs) {
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

        // Update row totals
        Object.keys(rowTotals).forEach(row => {
            const cell = this.container.querySelector(`.row-total[data-row="${row}"]`);
            if (cell) {
                cell.textContent = rowTotals[row].toFixed(2);
            }
        });

        // Update column totals
        Object.keys(colTotals).forEach(col => {
            const cell = this.container.querySelector(`.col-total[data-col="${col}"]`);
            if (cell) {
                cell.textContent = colTotals[col].toFixed(2);
            }
        });

        // Update grand total
        const grandTotalCell = this.container.querySelector('.grand-total');
        if (grandTotalCell) {
            grandTotalCell.textContent = grandTotal.toFixed(2);
        }
    }

    /**
     * Calculate totals for multi-dimensional data
     * @param {NodeList} inputs - Input elements
     */
    calculateMultiDimensionalTotals(inputs) {
        let total = 0;

        inputs.forEach(input => {
            const value = parseFloat(input.value) || 0;
            total += value;
        });

        const totalCell = this.container.querySelector('.grand-total');
        if (totalCell) {
            totalCell.textContent = total.toFixed(2);
        }
    }

    /**
     * Load existing data into the matrix
     * @param {Object} existingData - Existing dimension values JSON
     */
    loadExistingData(existingData) {
        if (!existingData || existingData.version !== 2) {
            return;
        }

        const breakdowns = existingData.breakdowns || [];

        breakdowns.forEach(breakdown => {
            const dims = breakdown.dimensions;
            const value = breakdown.raw_value;

            // Find matching input
            const inputs = this.container.querySelectorAll('.matrix-input');
            inputs.forEach(input => {
                if (this.matchesDimensions(input, dims)) {
                    input.value = value || '';
                }
            });
        });

        // Recalculate totals
        this.calculateTotals();
    }

    /**
     * Check if input matches dimension combination
     * @param {HTMLInputElement} input - Input element
     * @param {Object} dimensions - Dimension combination to match
     * @returns {boolean} - True if matches
     */
    matchesDimensions(input, dimensions) {
        if (input.dataset.combination) {
            // Multi-dimensional
            const combo = JSON.parse(input.dataset.combination);
            return JSON.stringify(combo) === JSON.stringify(dimensions);
        } else if (input.dataset.dim1 && input.dataset.dim2) {
            // 2D
            const [dim1, dim2] = this.currentMatrix.dimensions;
            return dimensions[dim1] === input.dataset.dim1 &&
                   dimensions[dim2] === input.dataset.dim2;
        } else if (input.dataset.dim1) {
            // 1D
            const [dim1] = this.currentMatrix.dimensions;
            return dimensions[dim1] === input.dataset.dim1;
        }
        return false;
    }

    /**
     * Collect dimensional data from inputs
     * @returns {Object} - Dimensional data structure for API
     */
    collectDimensionalData() {
        const breakdowns = [];
        const inputs = this.container.querySelectorAll('.matrix-input');

        inputs.forEach(input => {
            const value = parseFloat(input.value);

            if (value !== undefined && !isNaN(value)) {
                const breakdown = {
                    dimensions: this.getInputDimensions(input),
                    raw_value: value,
                    notes: this.getInputNotes(input)
                };
                breakdowns.push(breakdown);
            }
        });

        return {
            dimensions: this.currentMatrix.dimensions,
            breakdowns: breakdowns
        };
    }

    /**
     * Get dimensions from input element
     * @param {HTMLInputElement} input - Input element
     * @returns {Object} - Dimension combination
     */
    getInputDimensions(input) {
        if (input.dataset.combination) {
            return JSON.parse(input.dataset.combination);
        } else if (input.dataset.dim1 && input.dataset.dim2) {
            const [dim1, dim2] = this.currentMatrix.dimensions;
            return {
                [dim1]: input.dataset.dim1,
                [dim2]: input.dataset.dim2
            };
        } else if (input.dataset.dim1) {
            const [dim1] = this.currentMatrix.dimensions;
            return {
                [dim1]: input.dataset.dim1
            };
        }
        return {};
    }

    /**
     * Get notes for input (if available)
     * @param {HTMLInputElement} input - Input element
     * @returns {string|null} - Notes text
     */
    getInputNotes(input) {
        // For 1D matrix with notes fields
        if (input.dataset.dim1) {
            const notesInput = this.container.querySelector(
                `.matrix-notes[data-dim1="${input.dataset.dim1}"]`
            );
            return notesInput ? notesInput.value : null;
        }
        return null;
    }

    /**
     * Submit dimensional data to API
     * @returns {Promise<Object>} - API response
     */
    async submitDimensionalData() {
        try {
            const dimensionalData = this.collectDimensionalData();

            const payload = {
                field_id: this.currentFieldId,
                entity_id: this.currentEntityId,
                reporting_date: this.currentReportingDate,
                dimensional_data: dimensionalData
            };

            const response = await fetch('/user/v2/api/submit-dimensional-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error('Failed to submit dimensional data');
            }

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || 'Failed to submit dimensional data');
            }

            this.showSuccess('Data saved successfully!');
            return result;

        } catch (error) {
            console.error('Error submitting dimensional data:', error);
            this.showError('Failed to save data: ' + error.message);
            throw error;
        }
    }

    /**
     * Show success message
     * @param {string} message - Success message
     */
    showSuccess(message) {
        // This should integrate with your existing notification system
        console.log('SUCCESS:', message);
        if (window.showNotification) {
            window.showNotification(message, 'success');
        }
    }

    /**
     * Show error message
     * @param {string} message - Error message
     */
    showError(message) {
        // This should integrate with your existing notification system
        console.error('ERROR:', message);
        if (window.showNotification) {
            window.showNotification(message, 'error');
        }
    }

    /**
     * Clear the matrix
     */
    clear() {
        this.container.innerHTML = '';
        this.currentMatrix = null;
        this.currentFieldId = null;
        this.currentEntityId = null;
        this.currentReportingDate = null;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DimensionalDataHandler;
}
