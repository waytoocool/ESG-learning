/**
 * Bulk Paste Handler for User V2 Dashboard
 * =========================================
 *
 * Handles pasting data from Excel/Google Sheets directly into dimensional data tables.
 *
 * Features:
 * - Multi-cell paste from clipboard
 * - TSV/CSV format detection
 * - Dimension mapping (auto-detect columns)
 * - Format validation
 * - Preview before apply
 * - Error highlighting
 *
 * Supported Formats:
 * 1. Simple list (single column)
 * 2. Dimensional table (2D with headers)
 * 3. With dimension labels
 *
 * Usage:
 *   const bulkPaste = new BulkPasteHandler({
 *       targetTable: tableElement,
 *       dimensions: ['gender', 'age'],
 *       onPaste: (data) => { ... },
 *       onError: (error) => { ... }
 *   });
 *   bulkPaste.enable();
 */

class BulkPasteHandler {
    constructor(options = {}) {
        // Configuration
        this.targetTable = options.targetTable;
        this.dimensions = options.dimensions || [];
        this.fieldType = options.fieldType || 'DECIMAL';

        // Callbacks
        this.onPaste = options.onPaste || ((data) => console.log('Pasted:', data));
        this.onError = options.onError || ((error) => console.error('Paste error:', error));
        this.onValidate = options.onValidate || null;

        // API endpoint
        this.apiEndpoint = '/api/user/v2';

        // State
        this.isEnabled = false;
        this.pasteListener = null;

        // Preview modal
        this.previewModal = null;

        // Bind methods
        this.handlePaste = this.handlePaste.bind(this);
    }

    /**
     * Enable bulk paste functionality
     */
    enable() {
        if (this.isEnabled) {
            console.warn('Bulk paste already enabled');
            return;
        }

        this.isEnabled = true;

        // Add paste listener
        this.pasteListener = this.handlePaste;
        document.addEventListener('paste', this.pasteListener);

        // Add visual indicator
        this.showPasteIndicator();

        console.log('Bulk paste enabled');
    }

    /**
     * Disable bulk paste functionality
     */
    disable() {
        if (!this.isEnabled) return;

        this.isEnabled = false;

        // Remove paste listener
        if (this.pasteListener) {
            document.removeEventListener('paste', this.pasteListener);
            this.pasteListener = null;
        }

        // Remove indicator
        this.hidePasteIndicator();

        console.log('Bulk paste disabled');
    }

    /**
     * Handle paste event
     */
    async handlePaste(e) {
        if (!this.isEnabled) return;

        // Only handle paste when not in a regular input field
        if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
            // Allow normal paste in input fields
            return;
        }

        // Check if modal is open and target table is visible
        if (!this.targetTable || !this.isTableVisible()) {
            return;
        }

        e.preventDefault();

        try {
            // Get clipboard data
            const clipboardData = e.clipboardData || window.clipboardData;
            const pastedData = clipboardData.getData('text');

            if (!pastedData) {
                console.log('No text data in clipboard');
                return;
            }

            // Parse the pasted data
            const parsedData = this.parseClipboardData(pastedData);

            if (!parsedData || parsedData.rows.length === 0) {
                this.onError({ message: 'No valid data to paste' });
                return;
            }

            // Show preview
            this.showPreview(parsedData);

        } catch (error) {
            console.error('Error handling paste:', error);
            this.onError(error);
        }
    }

    /**
     * Parse clipboard data (TSV/CSV)
     */
    parseClipboardData(text) {
        const lines = text.trim().split('\n');

        if (lines.length === 0) {
            return null;
        }

        // Detect delimiter (tab or comma)
        const delimiter = lines[0].includes('\t') ? '\t' : ',';

        // Parse rows
        const rows = lines.map(line => {
            return line.split(delimiter).map(cell => cell.trim());
        });

        // Detect if first row is header
        const hasHeader = this.detectHeader(rows);

        let headers = [];
        let dataRows = rows;

        if (hasHeader) {
            headers = rows[0];
            dataRows = rows.slice(1);
        } else {
            // Generate default headers
            headers = dataRows[0].map((_, i) => `Column ${i + 1}`);
        }

        return {
            headers: headers,
            rows: dataRows,
            hasHeader: hasHeader,
            delimiter: delimiter
        };
    }

    /**
     * Detect if first row is a header
     */
    detectHeader(rows) {
        if (rows.length < 2) return false;

        const firstRow = rows[0];
        const secondRow = rows[1];

        // If first row has non-numeric values and second row has numeric, it's likely a header
        const firstRowNumeric = firstRow.every(cell => !isNaN(parseFloat(cell)));
        const secondRowNumeric = secondRow.some(cell => !isNaN(parseFloat(cell)));

        return !firstRowNumeric && secondRowNumeric;
    }

    /**
     * Show preview modal
     */
    showPreview(parsedData) {
        // Create preview modal if doesn't exist
        if (!this.previewModal) {
            this.previewModal = this.createPreviewModal();
            document.body.appendChild(this.previewModal);
        }

        // Populate preview
        this.populatePreview(parsedData);

        // Show modal
        this.previewModal.style.display = 'flex';
    }

    /**
     * Hide preview modal
     */
    hidePreview() {
        if (this.previewModal) {
            this.previewModal.style.display = 'none';
        }
    }

    /**
     * Create preview modal element
     */
    createPreviewModal() {
        const modal = document.createElement('div');
        modal.className = 'bulk-paste-preview-modal';
        modal.innerHTML = `
            <div class="preview-content">
                <div class="preview-header">
                    <h3>Bulk Paste Preview</h3>
                    <button class="close-preview" onclick="this.closest('.bulk-paste-preview-modal').style.display='none'">
                        &times;
                    </button>
                </div>

                <div class="preview-body">
                    <div class="dimension-mapping">
                        <h4>Dimension Mapping</h4>
                        <div class="mapping-controls">
                            <!-- Dimension mapping dropdowns will be added here -->
                        </div>
                    </div>

                    <div class="preview-table-container">
                        <table class="preview-table">
                            <thead></thead>
                            <tbody></tbody>
                        </table>
                    </div>

                    <div class="validation-summary">
                        <div class="validation-stats">
                            <span class="stat-valid">✓ <span class="count-valid">0</span> valid</span>
                            <span class="stat-invalid">❌ <span class="count-invalid">0</span> invalid</span>
                        </div>
                    </div>
                </div>

                <div class="preview-footer">
                    <button class="btn btn-secondary cancel-paste">Cancel</button>
                    <button class="btn btn-primary apply-paste">Apply</button>
                </div>
            </div>
        `;

        // Add event listeners
        modal.querySelector('.cancel-paste').addEventListener('click', () => {
            this.hidePreview();
        });

        modal.querySelector('.apply-paste').addEventListener('click', () => {
            this.applyPaste();
        });

        return modal;
    }

    /**
     * Populate preview with parsed data
     */
    populatePreview(parsedData) {
        const table = this.previewModal.querySelector('.preview-table');
        const thead = table.querySelector('thead');
        const tbody = table.querySelector('tbody');

        // Store parsed data
        this.currentParsedData = parsedData;

        // Clear existing content
        thead.innerHTML = '';
        tbody.innerHTML = '';

        // Create header row
        const headerRow = document.createElement('tr');
        parsedData.headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);

        // Create data rows
        let validCount = 0;
        let invalidCount = 0;

        parsedData.rows.forEach((row, rowIndex) => {
            const tr = document.createElement('tr');

            let rowValid = true;

            row.forEach((cell, cellIndex) => {
                const td = document.createElement('td');
                td.textContent = cell;

                // Validate cell
                const isValid = this.validateCell(cell);

                if (!isValid) {
                    td.classList.add('invalid-cell');
                    rowValid = false;
                }

                tr.appendChild(td);
            });

            if (rowValid) {
                validCount++;
                tr.classList.add('valid-row');
            } else {
                invalidCount++;
                tr.classList.add('invalid-row');
            }

            tbody.appendChild(tr);
        });

        // Update validation stats
        this.previewModal.querySelector('.count-valid').textContent = validCount;
        this.previewModal.querySelector('.count-invalid').textContent = invalidCount;

        // Enable/disable apply button
        const applyButton = this.previewModal.querySelector('.apply-paste');
        applyButton.disabled = validCount === 0;

        // Create dimension mapping controls
        this.createDimensionMapping(parsedData);
    }

    /**
     * Create dimension mapping controls
     */
    createDimensionMapping(parsedData) {
        const container = this.previewModal.querySelector('.mapping-controls');
        container.innerHTML = '';

        // If we have expected dimensions, create mapping dropdowns
        if (this.dimensions.length > 0) {
            this.dimensions.forEach(dimension => {
                const control = document.createElement('div');
                control.className = 'mapping-control';

                const label = document.createElement('label');
                label.textContent = `${dimension}:`;

                const select = document.createElement('select');
                select.dataset.dimension = dimension;

                // Add options
                const noneOption = document.createElement('option');
                noneOption.value = '';
                noneOption.textContent = '-- Not mapped --';
                select.appendChild(noneOption);

                parsedData.headers.forEach((header, index) => {
                    const option = document.createElement('option');
                    option.value = index;
                    option.textContent = header;

                    // Auto-select if header matches dimension name
                    if (header.toLowerCase().includes(dimension.toLowerCase())) {
                        option.selected = true;
                    }

                    select.appendChild(option);
                });

                control.appendChild(label);
                control.appendChild(select);
                container.appendChild(control);
            });
        }
    }

    /**
     * Validate a cell value
     */
    validateCell(value) {
        if (!value || value.trim() === '') {
            return true; // Empty is OK
        }

        // For numeric fields, check if it's a valid number
        if (['INTEGER', 'DECIMAL', 'PERCENTAGE', 'CURRENCY'].includes(this.fieldType)) {
            const num = parseFloat(value.replace(/[,$%]/g, ''));
            return !isNaN(num);
        }

        // For text fields, always valid
        return true;
    }

    /**
     * Apply the paste
     */
    async applyPaste() {
        if (!this.currentParsedData) return;

        try {
            // Get dimension mapping
            const dimensionMapping = this.getDimensionMapping();

            // Transform data based on mapping
            const transformedData = this.transformDataWithMapping(
                this.currentParsedData,
                dimensionMapping
            );

            // Validate with server if callback provided
            if (this.onValidate) {
                const validation = await this.onValidate(transformedData);
                if (!validation.valid) {
                    alert('Validation failed: ' + validation.message);
                    return;
                }
            }

            // Call onPaste callback
            await this.onPaste(transformedData);

            // Hide preview
            this.hidePreview();

            // Show success message
            this.showSuccess(`Successfully pasted ${transformedData.length} rows`);

        } catch (error) {
            console.error('Error applying paste:', error);
            this.onError(error);
        }
    }

    /**
     * Get dimension mapping from controls
     */
    getDimensionMapping() {
        const mapping = {};

        const selects = this.previewModal.querySelectorAll('.mapping-control select');
        selects.forEach(select => {
            const dimension = select.dataset.dimension;
            const columnIndex = select.value;

            if (columnIndex !== '') {
                mapping[dimension] = parseInt(columnIndex);
            }
        });

        return mapping;
    }

    /**
     * Transform data based on dimension mapping
     */
    transformDataWithMapping(parsedData, dimensionMapping) {
        const transformed = [];

        parsedData.rows.forEach(row => {
            const dataPoint = {
                value: null,
                dimensions: {}
            };

            // Extract dimension values based on mapping
            for (const [dimension, columnIndex] of Object.entries(dimensionMapping)) {
                if (row[columnIndex]) {
                    dataPoint.dimensions[dimension] = row[columnIndex];
                }
            }

            // Find the value column (first numeric column not mapped to a dimension)
            for (let i = 0; i < row.length; i++) {
                if (!Object.values(dimensionMapping).includes(i)) {
                    const value = this.parseValue(row[i]);
                    if (value !== null) {
                        dataPoint.value = value;
                        break;
                    }
                }
            }

            if (dataPoint.value !== null) {
                transformed.push(dataPoint);
            }
        });

        return transformed;
    }

    /**
     * Parse value based on field type
     */
    parseValue(value) {
        if (!value || value.trim() === '') {
            return null;
        }

        // Remove formatting
        const cleaned = value.replace(/[,$]/g, '');

        // Handle percentage
        if (cleaned.includes('%')) {
            const num = parseFloat(cleaned.replace(/%/g, ''));
            return isNaN(num) ? null : num / 100;
        }

        const num = parseFloat(cleaned);
        return isNaN(num) ? null : num;
    }

    /**
     * Check if target table is visible
     */
    isTableVisible() {
        if (!this.targetTable) return false;

        const style = window.getComputedStyle(this.targetTable);
        return style.display !== 'none' && style.visibility !== 'hidden';
    }

    /**
     * Show paste indicator
     */
    showPasteIndicator() {
        // Add indicator to target table
        if (this.targetTable) {
            const indicator = document.createElement('div');
            indicator.className = 'bulk-paste-indicator';
            indicator.innerHTML = `
                <span class="indicator-icon">📋</span>
                <span class="indicator-text">Ctrl+V to paste from Excel</span>
            `;

            this.targetTable.parentElement.insertBefore(indicator, this.targetTable);
        }
    }

    /**
     * Hide paste indicator
     */
    hidePasteIndicator() {
        const indicators = document.querySelectorAll('.bulk-paste-indicator');
        indicators.forEach(indicator => indicator.remove());
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        const toast = document.createElement('div');
        toast.className = 'bulk-paste-success-toast';
        toast.innerHTML = `
            <span class="toast-icon">✓</span>
            <span class="toast-message">${message}</span>
        `;

        document.body.appendChild(toast);

        // Auto-hide after 3 seconds
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BulkPasteHandler;
}
