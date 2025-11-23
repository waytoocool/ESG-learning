/**
 * ComputedFieldView Component
 *
 * Enhancement #1: Computed Field Modal
 *
 * Manages the display of computed field calculation details including:
 * - Computed result with status
 * - Calculation formula with variable mapping
 * - Dependencies table with current values
 * - Edit/Add buttons for each dependency
 * - Missing data warnings
 *
 * Usage:
 *   const view = new ComputedFieldView('entry-tab');
 *   await view.load(fieldId, entityId, reportingDate);
 */

class ComputedFieldView {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`[ComputedFieldView] Container element '${containerId}' not found`);
        }

        // State
        this.currentFieldId = null;
        this.currentEntityId = null;
        this.currentDate = null;
        this.currentFrequency = null;
        this.data = null;
        this.dateSelector = null;
    }

    /**
     * Load and render computed field view
     */
    async load(fieldId, entityId, reportingDate, frequency = null) {
        if (!this.container) {
            console.error('[ComputedFieldView] No container available');
            return;
        }

        // Store current context
        this.currentFieldId = fieldId;
        this.currentEntityId = entityId;
        this.currentDate = reportingDate;
        this.currentFrequency = frequency;

        // Show loading state
        this.container.innerHTML = this.renderLoading();

        try {
            // Fetch computed field details from API
            const response = await fetch(
                `/api/user/v2/computed-field-details/${fieldId}?` +
                `entity_id=${entityId}&reporting_date=${reportingDate}`
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to load computed field details');
            }

            this.data = await response.json();

            if (!this.data.success) {
                throw new Error(this.data.error || 'Failed to load computed field details');
            }

            // Extract frequency from data if not provided
            if (!this.currentFrequency && this.data.frequency) {
                this.currentFrequency = this.data.frequency;
            }

            // Render the view
            this.render();

        } catch (error) {
            console.error('[ComputedFieldView] Error loading data:', error);
            this.renderError(error.message);
        }
    }

    /**
     * Render complete computed field view
     */
    render() {
        if (!this.data || !this.container) {
            return;
        }

        // Render computed field view content into the dedicated container
        const html = `
            <div class="computed-field-view">
                ${this.renderDateSelector()}
                ${this.renderComputedResult()}
                ${this.renderMissingDataWarning()}
                ${this.renderFormula()}
                ${this.renderDependencies()}
            </div>
        `;

        this.container.innerHTML = html;
        this.initializeDateSelector();
        this.attachEditHandlers();
    }

    /**
     * Render computed result section
     */
    renderComputedResult() {
        const { result } = this.data;
        const statusConfig = this.getStatusConfig(result.status);

        return `
            <div class="result-section ${result.status}">
                <div class="result-header">
                    <span class="material-icons result-icon">calculate</span>
                    <h5>Computed Result</h5>
                </div>
                <div class="result-content">
                    <div class="result-value">
                        ${result.value !== null ? this.formatValue(result.value) : 'No Calculated Value'}
                        ${result.unit ? `<span class="result-unit">${this.escapeHtml(result.unit)}</span>` : ''}
                    </div>
                    <div class="result-meta">
                        <span class="result-status ${statusConfig.class}">
                            <span class="material-icons">${statusConfig.icon}</span>
                            ${statusConfig.label}
                        </span>
                        ${result.calculated_at ? `
                            <span class="result-timestamp">
                                <span class="material-icons">schedule</span>
                                Last calculated: ${this.formatDateTime(result.calculated_at)}
                            </span>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render missing data warning (conditional)
     */
    renderMissingDataWarning() {
        const { missing_dependencies } = this.data;

        if (!missing_dependencies || missing_dependencies.length === 0) {
            return '';
        }

        const missingList = missing_dependencies.map(dep => `
            <li>
                <strong>${this.escapeHtml(dep.field_name)}</strong>
                (Variable ${this.escapeHtml(dep.variable)}) - No data for selected date
            </li>
        `).join('');

        return `
            <div class="missing-data-warning">
                <div class="warning-header">
                    <span class="material-icons">warning</span>
                    <h5>Cannot Calculate - Missing Data</h5>
                </div>
                <p>This field requires data from ${missing_dependencies.length}
                   ${missing_dependencies.length === 1 ? 'dependency' : 'dependencies'}:</p>
                <ul class="missing-list">
                    ${missingList}
                </ul>
                <p class="warning-action">Click "Add Data" buttons below to provide missing values.</p>
            </div>
        `;
    }

    /**
     * Render calculation formula section
     */
    renderFormula() {
        const { formula, constant_multiplier, variable_mapping } = this.data;

        // Build human-readable formula
        let readableFormula = formula || 'N/A';

        if (variable_mapping) {
            // Replace variables with field names
            Object.entries(variable_mapping).forEach(([variable, info]) => {
                const coefficient = info.coefficient !== 1.0 ? `${info.coefficient} × ` : '';
                const replacement = coefficient + this.escapeHtml(info.field_name);
                readableFormula = readableFormula.replace(new RegExp(variable, 'g'), replacement);
            });
        }

        // Add constant multiplier if not 1.0
        if (constant_multiplier && constant_multiplier !== 1.0) {
            readableFormula = `${constant_multiplier} × (${readableFormula})`;
        }

        // Build variable mapping display
        const variableMappingHtml = variable_mapping ?
            Object.entries(variable_mapping).map(([variable, info]) => `
                <div class="variable-item">
                    <span class="variable-name">${this.escapeHtml(variable)}</span> =
                    <span class="variable-field">${this.escapeHtml(info.field_name)}</span>
                    ${info.coefficient !== 1.0 ?
                        `<span class="variable-coefficient">(× ${info.coefficient})</span>` :
                        ''}
                </div>
            `).join('') :
            '<p class="text-muted">No variables defined</p>';

        return `
            <div class="formula-section">
                <div class="formula-header">
                    <span class="material-icons">functions</span>
                    <h5>Calculation Formula</h5>
                </div>
                <div class="formula-content">
                    <div class="formula-expression">
                        ${readableFormula}
                    </div>
                    <div class="variable-mapping">
                        <h6>Variable Mapping:</h6>
                        ${variableMappingHtml}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render dependencies table
     */
    renderDependencies() {
        const { dependencies } = this.data;

        if (!dependencies || dependencies.length === 0) {
            return `
                <div class="dependencies-section">
                    <div class="dependencies-header">
                        <span class="material-icons">link</span>
                        <h5>Dependencies</h5>
                    </div>
                    <p class="text-muted">No dependencies configured for this field.</p>
                </div>
            `;
        }

        const rows = dependencies.map(dep => this.renderDependencyRow(dep)).join('');

        return `
            <div class="dependencies-section">
                <div class="dependencies-header">
                    <span class="material-icons">link</span>
                    <h5>Dependencies</h5>
                </div>
                <div class="table-responsive">
                    <table class="table dependencies-table">
                        <thead>
                            <tr>
                                <th>Variable</th>
                                <th>Field Name</th>
                                <th>Value</th>
                                <th>Status</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rows}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    /**
     * Render a single dependency row
     */
    renderDependencyRow(dep) {
        const statusIcon = this.getStatusIcon(dep.status);
        const valueDisplay = dep.value !== null ?
            `${this.formatValue(dep.value)} ${dep.unit || ''}` :
            '<span class="text-muted">N/A</span>';

        // Show notes preview if available
        const notesPreview = dep.notes ? `
            <div class="dependency-notes" title="${this.escapeHtml(dep.notes)}">
                <small>
                    <span class="material-icons">comment</span>
                    ${this.escapeHtml(this.truncateText(dep.notes, 50))}
                </small>
            </div>
        ` : '';

        // Field type badge
        const fieldTypeBadge = dep.field_type === 'computed' ?
            '<span class="badge badge-info">Computed</span>' : '';

        const actionButton = dep.status === 'available' ?
            `<button class="btn btn-sm btn-outline-primary btn-edit-dependency"
                     data-field-id="${this.escapeHtml(dep.field_id)}"
                     data-field-name="${this.escapeHtml(dep.field_name)}"
                     data-field-type="${this.escapeHtml(dep.field_type)}"
                     data-entity-id="${this.currentEntityId || ''}"
                     data-reporting-date="${this.currentDate || ''}"
                     type="button">
                <span class="material-icons">edit</span> Edit
            </button>` :
            `<button class="btn btn-sm btn-success btn-add-dependency"
                     data-field-id="${this.escapeHtml(dep.field_id)}"
                     data-field-name="${this.escapeHtml(dep.field_name)}"
                     data-field-type="${this.escapeHtml(dep.field_type)}"
                     data-entity-id="${this.currentEntityId || ''}"
                     data-reporting-date="${this.currentDate || ''}"
                     type="button">
                <span class="material-icons">add</span> Add Data
            </button>`;

        return `
            <tr class="dependency-row status-${dep.status}">
                <td class="variable-cell">
                    <span class="variable-badge">${this.escapeHtml(dep.variable)}</span>
                    ${dep.coefficient !== 1.0 ? `<small>(× ${dep.coefficient})</small>` : ''}
                </td>
                <td class="field-name-cell">
                    <div>${this.escapeHtml(dep.field_name)} ${fieldTypeBadge}</div>
                    ${notesPreview}
                </td>
                <td class="value-cell">${valueDisplay}</td>
                <td class="status-cell">${statusIcon} ${this.formatStatus(dep.status)}</td>
                <td class="action-cell">${actionButton}</td>
            </tr>
        `;
    }

    /**
     * Render date selector section
     * Bug Fix #1: Add date selector for computed fields
     */
    renderDateSelector() {
        return `
            <div class="date-selector-section mb-4">
                <div class="d-flex align-items-center justify-content-between mb-2">
                    <label class="form-label mb-0">
                        <span class="material-icons align-middle">event</span>
                        Viewing Date
                    </label>
                    <span class="badge bg-secondary">${this.currentFrequency || 'Unknown'} Frequency</span>
                </div>
                <div id="computedFieldDateSelectorContainer">
                    <!-- Date selector will be initialized here -->
                    <div class="text-center text-muted py-2">
                        <small>Loading date selector...</small>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Initialize date selector component
     * Bug Fix #1: Initialize DateSelector for computed field view
     */
    async initializeDateSelector() {
        if (!window.DateSelector) {
            console.error('[ComputedFieldView] DateSelector class not available');
            return;
        }

        const container = document.getElementById('computedFieldDateSelectorContainer');
        if (!container) {
            console.error('[ComputedFieldView] Date selector container not found');
            return;
        }

        try {
            // Get fiscal year from global context
            const fyYear = window.currentFyYear || null;

            // Create new DateSelector instance with proper configuration
            this.dateSelector = new window.DateSelector({
                fieldId: this.currentFieldId,
                entityId: this.currentEntityId,
                fyYear: fyYear,
                containerId: 'computedFieldDateSelectorContainer',
                onDateSelect: async (dateInfo) => {
                    // DateSelector passes an object with {date, dateFormatted, status, hasDimensionalData}
                    // Extract the date string for use in API calls
                    const selectedDate = dateInfo.date;
                    console.log('[ComputedFieldView] Date selected:', selectedDate);
                    await this.onDateChange(selectedDate);
                }
            });

            // Initialize the date selector (it will fetch dates and render)
            const result = await this.dateSelector.init();

            if (result.success) {
                console.log('[ComputedFieldView] Date selector initialized with', result.datesCount, 'dates');

                // Auto-select the current date if it exists in the list
                if (this.currentDate && this.dateSelector.dates.some(d => d.date === this.currentDate)) {
                    this.dateSelector.selectDate(this.currentDate);
                }
            } else {
                throw new Error(result.error || 'Failed to initialize date selector');
            }

        } catch (error) {
            console.error('[ComputedFieldView] Error initializing date selector:', error);
            container.innerHTML = `
                <div class="alert alert-warning">
                    <small>Unable to load date selector. Viewing data for: ${this.currentDate || 'current period'}</small>
                </div>
            `;
        }
    }

    /**
     * Handle date change event
     * Bug Fix #1: Reload computed field data when date changes
     */
    async onDateChange(newDate) {
        if (!newDate || newDate === this.currentDate) {
            return;
        }

        console.log('[ComputedFieldView] Reloading data for new date:', newDate);

        // Update current date
        this.currentDate = newDate;

        // Update global reporting date for dependency modals
        window.currentReportingDate = newDate;

        // Show loading state (but keep date selector)
        const resultSection = this.container.querySelector('.computed-field-view > :not(.date-selector-section)');
        if (resultSection) {
            const loadingHtml = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Refreshing calculation...</p>
                </div>
            `;
            // Keep date selector, show loading for rest
            const dateSelector = this.container.querySelector('.date-selector-section');
            this.container.innerHTML = '';
            if (dateSelector) {
                this.container.appendChild(dateSelector);
            }
            this.container.insertAdjacentHTML('beforeend', loadingHtml);
        }

        // Reload data for new date
        await this.load(this.currentFieldId, this.currentEntityId, newDate, this.currentFrequency);
    }

    /**
     * Attach event handlers to edit/add buttons
     */
    attachEditHandlers() {
        if (!this.container) return;

        // Edit dependency buttons
        this.container.querySelectorAll('.btn-edit-dependency, .btn-add-dependency').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const fieldId = e.currentTarget.dataset.fieldId;
                const fieldName = e.currentTarget.dataset.fieldName;
                const fieldType = e.currentTarget.dataset.fieldType;
                const entityId = e.currentTarget.dataset.entityId;
                const reportingDate = e.currentTarget.dataset.reportingDate;

                this.openDependencyModal(fieldId, fieldName, fieldType, entityId, reportingDate);
            });
        });
    }

    /**
     * Open modal for dependency field
     * Bug Fix #2: Improved dependency modal opening
     */
    openDependencyModal(fieldId, fieldName, fieldType, entityId, reportingDate) {
        console.log('[ComputedFieldView] Opening dependency modal:', {fieldId, fieldName, fieldType, entityId, reportingDate});

        // Try method 1: Find and click the field card button
        const fieldCard = document.querySelector(`[data-field-id="${fieldId}"]`);
        if (fieldCard) {
            const button = fieldCard.querySelector('.open-data-modal');
            if (button) {
                // Close current modal first
                const currentModal = bootstrap.Modal.getInstance(document.getElementById('dataCollectionModal'));
                if (currentModal) {
                    currentModal.hide();
                }

                // Wait for modal to close, then open dependency modal
                setTimeout(() => {
                    button.click();
                }, 300);
                return;
            }
        }

        // Method 2: Programmatically open the modal if field card not found
        // This handles cases where the dependency field might not be visible on current dashboard
        console.log('[ComputedFieldView] Field card not found, opening modal programmatically');

        // Close current modal and wait for it to fully close
        const modalElement = document.getElementById('dataCollectionModal');
        const currentModal = bootstrap.Modal.getInstance(modalElement);

        if (currentModal) {
            // Use event listener to wait for modal to fully close
            modalElement.addEventListener('hidden.bs.modal', () => {
                this.openDependencyModalAfterClose(fieldId, fieldName, fieldType, entityId, reportingDate);
            }, { once: true });
            currentModal.hide();
        } else {
            // Modal not open, can open dependency modal immediately
            this.openDependencyModalAfterClose(fieldId, fieldName, fieldType, entityId, reportingDate);
        }
    }

    /**
     * Helper method to open dependency modal after computed field modal closes
     * BUGFIX: Separated into own method to properly handle modal lifecycle
     */
    async openDependencyModalAfterClose(fieldId, fieldName, fieldType, entityId, reportingDate) {
            // Toggle visibility: hide computed field view, show data entry form
            const computedContainer = document.getElementById('computed-field-view-container');
            const formContainer = document.getElementById('data-entry-form-container');

            if (computedContainer && formContainer) {
                computedContainer.style.display = 'none';
                formContainer.style.display = 'block';
                console.log('[ComputedFieldView] Toggled to data entry form view');
            }

            // Set up modal state
            window.currentFieldId = fieldId;
            window.currentFieldType = fieldType || 'raw_input';

            // BUGFIX #3: Use entityId and reportingDate passed from button data attributes
            // If not provided, fall back to instance properties and then global variables
            const finalEntityId = entityId || this.currentEntityId || window.currentEntityId || null;
            const finalReportingDate = reportingDate || this.currentDate || window.currentReportingDate || null;

            // Store entity ID globally so modal initialization can access it
            window.currentEntityId = finalEntityId;
            window.currentReportingDate = finalReportingDate;

            console.log('[ComputedFieldView] Opening dependency modal with:', {
                fieldId,
                entityId: finalEntityId,
                reportingDate: finalReportingDate
            });

            // Update modal title
            const modalLabel = document.getElementById('dataCollectionModalLabel');
            if (modalLabel) {
                modalLabel.innerHTML = `Enter Data: <span id="modalFieldName">${this.escapeHtml(fieldName)}</span>`;
            }

            // Reset tab label
            const entryTab = document.querySelector('[data-tab="entry"]');
            if (entryTab) {
                entryTab.textContent = 'Current Entry';
            }

            // Show submit button
            const submitBtn = document.getElementById('submitDataBtn');
            if (submitBtn) submitBtn.style.display = 'inline-flex';

            // Populate reporting date
            const reportingDateInput = document.getElementById('reportingDate');
            if (reportingDateInput && reportingDate) {
                reportingDateInput.value = reportingDate;
            }

            // Programmatically load field data and open modal
            try {
                // BUGFIX: Only fetch data if we have a valid reporting date
                // If no date is selected, open the modal empty so user can select date first
                if (reportingDate && reportingDate !== 'null' && reportingDate !== 'undefined') {
                    // Get field API endpoint
                    const apiUrl = `/api/user/v2/field-data/${fieldId}?entity_id=${entityId}&reporting_date=${reportingDate}`;

                    // Fetch field data
                    const response = await fetch(apiUrl);

                    if (response.ok) {
                        const data = await response.json();

                        // Populate form with data if it exists
                        if (data.success && data.data_id) {
                            // Pre-populate the value if exists
                            const dataValueInput = document.getElementById('dataValue');
                            if (dataValueInput && data.raw_value !== null) {
                                dataValueInput.value = data.raw_value;
                            }

                            // Pre-populate notes if exists
                            const notesInput = document.getElementById('fieldNotes');
                            if (notesInput && data.notes) {
                                notesInput.value = data.notes;
                            }
                        }
                    }
                } else {
                    console.log('[ComputedFieldView] No reporting date available - opening modal for date selection');
                }

                // Open modal regardless of whether data exists (allow new entry)
                const modal = new bootstrap.Modal(document.getElementById('dataCollectionModal'));
                modal.show();

                console.log('[ComputedFieldView] Dependency modal opened programmatically for:', fieldName);

            } catch (error) {
                console.error('[ComputedFieldView] Error loading dependency field:', error);

                // Still try to open the modal even if data fetch fails
                // User can still enter new data
                try {
                    const modal = new bootstrap.Modal(document.getElementById('dataCollectionModal'));
                    modal.show();
                    console.log('[ComputedFieldView] Modal opened despite fetch error, user can enter new data');
                } catch (modalError) {
                    console.error('[ComputedFieldView] Failed to open modal:', modalError);
                    alert(`Unable to open "${fieldName}" field. Please try accessing it from the dashboard.`);
                }
            }
    }

    /**
     * Render loading state
     */
    renderLoading() {
        return `
            <div class="computed-field-loading">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p>Loading calculation details...</p>
            </div>
        `;
    }

    /**
     * Render error state
     */
    renderError(message) {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="alert alert-danger">
                <span class="material-icons">error</span>
                <strong>Error loading computed field:</strong> ${this.escapeHtml(message)}
            </div>
        `;
    }

    /**
     * Get status configuration
     */
    getStatusConfig(status) {
        const configs = {
            'complete': {
                label: 'Complete',
                icon: 'check_circle',
                class: 'status-complete'
            },
            'partial': {
                label: 'Partial Data',
                icon: 'warning',
                class: 'status-partial'
            },
            'no_data': {
                label: 'No Data',
                icon: 'info',
                class: 'status-no-data'
            },
            'failed': {
                label: 'Calculation Failed',
                icon: 'error',
                class: 'status-failed'
            }
        };

        return configs[status] || configs['no_data'];
    }

    /**
     * Get status icon for dependency
     */
    getStatusIcon(status) {
        const icons = {
            'available': '<span class="material-icons text-success">check_circle</span>',
            'missing': '<span class="material-icons text-danger">cancel</span>',
            'pending': '<span class="material-icons text-warning">pending</span>'
        };

        return icons[status] || icons['missing'];
    }

    /**
     * Format value for display
     */
    formatValue(value) {
        if (value === null || value === undefined) {
            return 'N/A';
        }

        // Try to parse as number
        const num = parseFloat(value);
        if (!isNaN(num)) {
            // Format with commas for thousands
            return num.toLocaleString('en-US', {
                maximumFractionDigits: 2,
                minimumFractionDigits: 0
            });
        }

        return this.escapeHtml(String(value));
    }

    /**
     * Format status for display
     */
    formatStatus(status) {
        const statusMap = {
            'available': 'Available',
            'missing': 'Missing',
            'pending': 'Pending'
        };

        return statusMap[status] || status;
    }

    /**
     * Format datetime string
     */
    formatDateTime(isoString) {
        try {
            const date = new Date(isoString);
            return date.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return isoString;
        }
    }

    /**
     * Truncate text with ellipsis
     */
    truncateText(text, maxLength) {
        if (!text || text.length <= maxLength) {
            return text;
        }
        return text.substring(0, maxLength) + '...';
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (text === null || text === undefined) {
            return '';
        }

        const div = document.createElement('div');
        div.textContent = String(text);
        return div.innerHTML;
    }

    /**
     * Reset the view
     */
    reset() {
        this.currentFieldId = null;
        this.currentEntityId = null;
        this.currentDate = null;
        this.data = null;

        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

// Export for global use
window.ComputedFieldView = ComputedFieldView;
