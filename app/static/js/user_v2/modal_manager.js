/**
 * Modal Manager
 * Handles modal opening, tab switching, field info/history loading, and export functionality
 */

class ModalManager {
    constructor() {
        this.modal = null;
        this.currentFieldId = null;
        this.currentFieldType = null;
        this.currentDateSelector = null;
        this.historyPaginationState = {
            currentFieldId: null,
            currentOffset: 0,
            limit: 20,
            totalCount: 0,
            loadedHistory: []
        };

        // Store globally for access by other modules
        window.currentFieldId = this.currentFieldId;
        window.currentFieldType = this.currentFieldType;
        window.currentDateSelector = this.currentDateSelector;

        this.init();
    }

    init() {
        const modalElement = document.getElementById('dataCollectionModal');
        if (modalElement) {
            this.modal = new bootstrap.Modal(modalElement);
            this.attachEventListeners();
            console.log('[ModalManager] Initialized');
        }
    }

    attachEventListeners() {
        // Attach modal open handlers to all "Enter Data" buttons
        document.querySelectorAll('.open-data-modal').forEach(button => {
            button.addEventListener('click', (event) => this.handleModalOpen(event));
        });

        // Attach tab switching handlers
        document.querySelectorAll('.modal-tabs .tab').forEach(tab => {
            tab.addEventListener('click', (event) => this.handleTabSwitch(event));
        });

        // Attach other UI handlers
        this.attachUIHandlers();
    }

    /**
     * Handle modal opening when "Enter Data" button is clicked
     * @param {Event} event - Click event
     */
    async handleModalOpen(event) {
        const button = event.currentTarget;
        const fieldId = button.dataset.fieldId;
        const fieldName = button.dataset.fieldName;
        const fieldType = button.dataset.fieldType;

        // Store field ID and type globally
        this.currentFieldId = fieldId;
        this.currentFieldType = fieldType;
        window.currentFieldId = fieldId;
        window.currentFieldType = fieldType;

        // Get selected date from dashboard
        const selectedDate = document.getElementById('selectedDate')?.value;
        const reportingDateInput = document.getElementById('reportingDate');
        if (reportingDateInput && selectedDate) {
            reportingDateInput.value = selectedDate;
        }

        console.log('[ModalManager] Opening modal for field:', fieldId, fieldType, 'with date:', selectedDate);

        const entityId = window.currentEntityId || null;

        // Handle computed vs raw input fields
        if (fieldType === 'computed') {
            await this.setupComputedFieldModal(fieldId, fieldName, entityId, selectedDate);
        } else {
            await this.setupRawInputModal(fieldId, fieldName, entityId, selectedDate);
        }

        // Show modal
        this.modal.show();

        // Check if date is selected and disable inputs accordingly
        const reportingDate = document.getElementById('reportingDate')?.value;
        if (window.toggleFormInputs) {
            window.toggleFormInputs(!!reportingDate);
        }

        // Initialize date selector
        await this.initializeDateSelector(fieldId, entityId);
    }

    /**
     * Setup modal for computed field view
     * @param {string} fieldId - Field ID
     * @param {string} fieldName - Field name
     * @param {number} entityId - Entity ID
     * @param {string} selectedDate - Selected date
     */
    async setupComputedFieldModal(fieldId, fieldName, entityId, selectedDate) {
        console.log('[ModalManager] Setting up computed field modal');

        // Toggle containers
        const computedContainer = document.getElementById('computed-field-view-container');
        const formContainer = document.getElementById('data-entry-form-container');
        if (computedContainer && formContainer) {
            computedContainer.style.display = 'block';
            formContainer.style.display = 'none';
        }

        // Update modal title
        document.getElementById('dataCollectionModalLabel').innerHTML =
            'View Computed Field: <span id="modalFieldName">' + fieldName + '</span>';

        // Update tab label
        const entryTab = document.querySelector('[data-tab="entry"]');
        if (entryTab) {
            entryTab.textContent = 'Calculation & Dependencies';
        }

        // Hide submit button
        const submitBtn = document.getElementById('submitDataBtn');
        if (submitBtn) submitBtn.style.display = 'none';

        // Determine date to use
        let dateToUse = selectedDate || document.getElementById('reportingDate')?.value;
        if (!dateToUse) {
            const now = new Date();
            const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
            dateToUse = lastDay.toISOString().split('T')[0];
        }

        window.currentReportingDate = dateToUse;

        // Load computed field view
        if (dateToUse && entityId && window.computedFieldView) {
            try {
                const fieldCard = event.currentTarget.closest('[data-frequency]');
                const frequency = fieldCard ? fieldCard.dataset.frequency : 'monthly';
                await window.computedFieldView.load(fieldId, entityId, dateToUse, frequency);
            } catch (error) {
                console.error('[ModalManager] Error loading computed field view:', error);
                const entryTabContent = document.getElementById('entry-tab');
                if (entryTabContent) {
                    entryTabContent.innerHTML = '<div class="alert alert-danger">Error loading calculation details. Please try again.</div>';
                }
            }
        }
    }

    /**
     * Setup modal for raw input field
     * @param {string} fieldId - Field ID
     * @param {string} fieldName - Field name
     * @param {number} entityId - Entity ID
     * @param {string} selectedDate - Selected date
     */
    async setupRawInputModal(fieldId, fieldName, entityId, selectedDate) {
        console.log('[ModalManager] Setting up raw input field modal');

        // Toggle containers
        const computedContainer = document.getElementById('computed-field-view-container');
        const formContainer = document.getElementById('data-entry-form-container');
        if (computedContainer && formContainer) {
            computedContainer.style.display = 'none';
            formContainer.style.display = 'block';
        }

        // Update modal title
        document.getElementById('dataCollectionModalLabel').innerHTML =
            'Enter Data: <span id="modalFieldName">' + fieldName + '</span>';

        // Update tab label
        const entryTab = document.querySelector('[data-tab="entry"]');
        if (entryTab) {
            entryTab.textContent = 'Current Entry';
        }

        // Show submit button
        const submitBtn = document.getElementById('submitDataBtn');
        if (submitBtn) submitBtn.style.display = 'inline-flex';

        // Load existing notes
        if (fieldId && entityId && selectedDate && window.loadExistingNotes) {
            await window.loadExistingNotes(fieldId, entityId, selectedDate);
        }

        // Load existing data and attachments
        if (fieldId && entityId && selectedDate && window.fileUploadHandler) {
            try {
                const response = await fetch(`/api/user/v2/field-data/${fieldId}?entity_id=${entityId}&reporting_date=${selectedDate}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.data_id) {
                        window.fileUploadHandler.setDataId(data.data_id);
                        await window.fileUploadHandler.loadExistingAttachments(data.data_id);
                        console.log('[ModalManager] Loaded existing data_id:', data.data_id);
                    }
                }
            } catch (error) {
                console.log('[ModalManager] No existing data found (new entry)');
            }
        }
    }

    /**
     * Initialize date selector for the field
     * @param {string} fieldId - Field ID
     * @param {number} entityId - Entity ID
     */
    async initializeDateSelector(fieldId, entityId) {
        setTimeout(async () => {
            if (typeof DateSelector !== 'undefined') {
                try {
                    // Destroy previous instance if exists
                    if (this.currentDateSelector) {
                        this.currentDateSelector.destroy();
                    }

                    const fyYear = window.currentFYYear || null;

                    // Create new date selector instance
                    this.currentDateSelector = new DateSelector({
                        fieldId: fieldId,
                        entityId: entityId,
                        fyYear: fyYear,
                        containerId: 'dateSelectorContainer',
                        onDateSelect: async (dateInfo) => await this.handleDateSelection(dateInfo, fieldId, entityId)
                    });

                    window.currentDateSelector = this.currentDateSelector;

                    // Initialize and load dates
                    const result = await this.currentDateSelector.init();
                    if (result.success) {
                        console.log(`[ModalManager] Date selector loaded with ${result.datesCount} dates`);

                        // Load dimensional matrix for raw input fields
                        if (this.currentFieldType !== 'computed' && window.dimensionalDataHandler && fieldId && entityId) {
                            await this.loadDimensionalMatrix(fieldId, entityId);
                        }
                    } else {
                        console.error('[ModalManager] Failed to load date selector:', result.error);
                    }
                } catch (error) {
                    console.error('[ModalManager] Error initializing date selector:', error);
                }
            } else {
                console.error('[ModalManager] DateSelector class not available');
            }
        }, 100);
    }

    /**
     * Handle date selection from date selector
     * @param {Object} dateInfo - Date information
     * @param {string} fieldId - Field ID
     * @param {number} entityId - Entity ID
     */
    async handleDateSelection(dateInfo, fieldId, entityId) {
        console.log('[ModalManager] Date selected:', dateInfo);

        // Update hidden input
        document.getElementById('reportingDate').value = dateInfo.date;

        // Enable form inputs
        if (window.toggleFormInputs) {
            window.toggleFormInputs(true);
        }

        // Update auto-save handler
        if (window.autoSaveHandler && window.autoSaveHandler.updateReportingDate) {
            window.autoSaveHandler.updateReportingDate(dateInfo.date);
            if (!window.autoSaveHandler.isActive) {
                window.autoSaveHandler.start();
            }
        }

        // Load existing notes
        if (window.loadExistingNotes && fieldId && entityId) {
            await window.loadExistingNotes(fieldId, entityId, dateInfo.date);
        }

        // Load data_id and attachments
        if (window.fileUploadHandler && fieldId && entityId) {
            try {
                const response = await fetch(`/api/user/v2/field-data/${fieldId}?entity_id=${entityId}&reporting_date=${dateInfo.date}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.data_id) {
                        window.fileUploadHandler.setDataId(data.data_id);
                        await window.fileUploadHandler.loadExistingAttachments(data.data_id);
                    } else {
                        window.fileUploadHandler.reset();
                    }
                } else {
                    window.fileUploadHandler.reset();
                }
            } catch (error) {
                window.fileUploadHandler.reset();
            }
        }

        // Reload dimensional matrix
        if (window.dimensionalDataHandler && fieldId) {
            await this.loadDimensionalMatrix(fieldId, entityId, dateInfo.date);
        }
    }

    /**
     * Load dimensional matrix for a field
     * @param {string} fieldId - Field ID
     * @param {number} entityId - Entity ID
     * @param {string} dateToUse - Optional date override
     */
    async loadDimensionalMatrix(fieldId, entityId, dateToUse = null) {
        try {
            console.log('[ModalManager] Loading dimension matrix for field:', fieldId);

            // Determine date to use
            if (!dateToUse) {
                const selectedDate = document.getElementById('selectedDate')?.value;
                const reportingDateInput = document.getElementById('reportingDate');
                dateToUse = selectedDate;
                if (!dateToUse && reportingDateInput) {
                    dateToUse = reportingDateInput.value;
                }
                if (!dateToUse) {
                    const now = new Date();
                    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
                    dateToUse = lastDay.toISOString().split('T')[0];
                }
            }

            // Show loading state
            const matrixContainer = document.getElementById('dimensionMatrixContainer');
            if (matrixContainer) {
                matrixContainer.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Loading data...</p></div>';
            }

            // Load matrix
            const matrix = await window.dimensionalDataHandler.loadDimensionMatrix(fieldId, entityId, dateToUse);

            // Show/hide dimensional matrix based on field
            const valueInput = document.getElementById('dataValue');
            const valueContainer = valueInput ? valueInput.closest('.mb-3') : null;

            if (matrix.has_dimensions) {
                if (matrixContainer) matrixContainer.style.display = 'block';
                if (valueContainer) valueContainer.style.display = 'none';

                // Attach number formatters
                if (window.attachNumberFormatters) {
                    setTimeout(() => {
                        window.attachNumberFormatters(matrixContainer);
                        if (window.formInputsEnabled === false && window.toggleFormInputs) {
                            window.toggleFormInputs(false);
                        }
                    }, 50);
                }
            } else {
                if (matrixContainer) matrixContainer.style.display = 'none';
                if (valueContainer) valueContainer.style.display = 'block';
            }

            console.log('[ModalManager] Dimension matrix loaded successfully');
        } catch (error) {
            console.error('[ModalManager] Error loading dimension matrix:', error);
            const matrixContainer = document.getElementById('dimensionMatrixContainer');
            if (matrixContainer) {
                matrixContainer.innerHTML = '<div class="alert alert-danger">Failed to load data. Please try again.</div>';
            }
        }
    }

    /**
     * Handle tab switching
     * @param {Event} event - Click event
     */
    async handleTabSwitch(event) {
        const tab = event.currentTarget;
        const tabName = tab.dataset.tab;

        // Update tab buttons
        document.querySelectorAll('.modal-tabs .tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.getElementById(tabName + '-tab').classList.add('active');

        // Load data for specific tabs
        if (tabName === 'info' && this.currentFieldId) {
            await this.loadFieldInfo(this.currentFieldId);
        } else if (tabName === 'history' && this.currentFieldId) {
            await this.loadFieldHistory(this.currentFieldId);
        }
    }

    /**
     * Load field info tab content
     * @param {string} fieldId - Field ID
     */
    async loadFieldInfo(fieldId) {
        const infoContent = document.getElementById('fieldInfoContent');
        if (!infoContent) return;

        try {
            infoContent.innerHTML = '<p class="text-muted">Loading field information...</p>';

            const response = await fetch(`/api/user/v2/field-metadata/${fieldId}`);
            const data = await response.json();

            if (data.success) {
                let html = '<div class="field-info">';
                html += `<h4>${data.field_name}</h4>`;
                html += `<p class="text-muted">${data.description}</p>`;
                html += '<hr>';
                html += '<dl class="row">';
                html += `<dt class="col-sm-4">Type:</dt><dd class="col-sm-8">${data.field_type === 'computed' ? 'Computed Field' : 'Raw Input'}</dd>`;
                html += `<dt class="col-sm-4">Data Type:</dt><dd class="col-sm-8">${data.data_type || 'N/A'}</dd>`;
                html += `<dt class="col-sm-4">Unit:</dt><dd class="col-sm-8">${data.unit || 'N/A'}</dd>`;
                if (data.framework) {
                    html += `<dt class="col-sm-4">Framework:</dt><dd class="col-sm-8">${data.framework}</dd>`;
                }
                if (data.topic) {
                    html += `<dt class="col-sm-4">Topic:</dt><dd class="col-sm-8">${data.topic}</dd>`;
                }
                if (data.frequency) {
                    html += `<dt class="col-sm-4">Frequency:</dt><dd class="col-sm-8">${data.frequency}</dd>`;
                }
                html += '</dl>';

                // Show formula and dependencies for computed fields
                if (data.field_type === 'computed' && data.formula) {
                    html += '<hr>';
                    html += '<h5>Calculation Formula</h5>';
                    html += `<p><code>${data.formula}</code></p>`;

                    if (data.dependencies && data.dependencies.length > 0) {
                        html += '<h5>Dependencies</h5>';
                        html += '<ul>';
                        data.dependencies.forEach(dep => {
                            html += `<li><strong>${dep.variable}:</strong> ${dep.field_name} ${dep.unit ? '(' + dep.unit + ')' : ''}</li>`;
                        });
                        html += '</ul>';
                    }
                }

                html += '</div>';
                infoContent.innerHTML = html;
            } else {
                infoContent.innerHTML = `<p class="text-danger">Error: ${data.error}</p>`;
            }
        } catch (error) {
            console.error('[ModalManager] Error loading field info:', error);
            infoContent.innerHTML = '<p class="text-danger">Error loading field information. Please try again.</p>';
        }
    }

    /**
     * Load field history tab content
     * @param {string} fieldId - Field ID
     * @param {boolean} reset - Reset pagination state
     */
    async loadFieldHistory(fieldId, reset = true) {
        const historyContent = document.getElementById('historicalDataContent');
        if (!historyContent) return;

        // Reset state if loading new field
        if (reset || this.historyPaginationState.currentFieldId !== fieldId) {
            this.historyPaginationState.currentFieldId = fieldId;
            this.historyPaginationState.currentOffset = 0;
            this.historyPaginationState.loadedHistory = [];
        }

        try {
            if (reset) {
                historyContent.innerHTML = '<p class="text-muted">Loading historical data...</p>';
            }

            const response = await fetch(
                `/api/user/v2/field-history/${fieldId}?limit=${this.historyPaginationState.limit}&offset=${this.historyPaginationState.currentOffset}`
            );
            const data = await response.json();

            if (data.success) {
                this.historyPaginationState.totalCount = data.total_count;
                this.historyPaginationState.loadedHistory.push(...data.history);

                this.renderHistoryTable(
                    this.historyPaginationState.loadedHistory,
                    data.total_count,
                    data.has_more,
                    fieldId
                );
            } else {
                historyContent.innerHTML = `<p class="text-danger">Error: ${data.error}</p>`;
            }
        } catch (error) {
            console.error('[ModalManager] Error loading field history:', error);
            historyContent.innerHTML = '<p class="text-danger">Error loading historical data. Please try again.</p>';
        }
    }

    /**
     * Render history table
     * @param {Array} history - History entries
     * @param {number} totalCount - Total count
     * @param {boolean} hasMore - Has more entries
     * @param {string} fieldId - Field ID
     */
    renderHistoryTable(history, totalCount, hasMore, fieldId) {
        const historyContent = document.getElementById('historicalDataContent');

        if (history.length === 0) {
            historyContent.innerHTML = '<p class="text-muted">No historical data available for this field.</p>';
            return;
        }

        let html = '<div class="historical-data">';

        // Header with export buttons
        html += '<div class="d-flex justify-content-between align-items-center mb-3">';
        html += `<h5 class="mb-0">Historical Submissions (Showing ${history.length} of ${totalCount})</h5>`;
        html += '<div class="export-buttons">';
        html += `<button class="btn btn-sm btn-outline-success me-2" onclick="window.modalManager.exportFieldHistory('${fieldId}', 'csv')" title="Export to CSV">`;
        html += '<i class="bi bi-download"></i> CSV</button>';
        html += `<button class="btn btn-sm btn-outline-success" onclick="window.modalManager.exportFieldHistory('${fieldId}', 'excel')" title="Export to Excel">`;
        html += '<i class="bi bi-file-earmark-excel"></i> Excel</button>';
        html += '</div>';
        html += '</div>';

        html += '<table class="table table-sm table-striped">';
        html += '<thead><tr><th>Reporting Date</th><th>Value</th><th>Notes</th><th>Attachments</th><th>Submitted On</th></tr></thead>';
        html += '<tbody>';

        history.forEach(entry => {
            const submittedDate = entry.created_at ? new Date(entry.created_at).toLocaleDateString() : 'N/A';
            const valueDisplay = entry.value !== null ? `${entry.value} ${entry.unit || ''}` : 'N/A';

            const notesDisplay = entry.has_notes
                ? `<span class="notes-indicator" title="${this.escapeHtml(entry.notes)}">💬 ${this.truncateText(entry.notes, 30)}</span>`
                : '<span class="text-muted">-</span>';

            const attachmentsDisplay = entry.attachments && entry.attachments.length > 0
                ? entry.attachments.map(att => `
                    <a href="/user/v2/api/download-attachment/${att.id}"
                       class="attachment-link"
                       title="${this.escapeHtml(att.filename)} (${this.formatFileSize(att.file_size)})"
                       download>
                      <span class="material-icons text-sm">attach_file</span>
                      ${this.escapeHtml(this.truncateText(att.filename, 15))}
                    </a>
                  `).join('')
                : '<span class="text-muted">-</span>';

            html += '<tr>';
            html += `<td>${entry.reporting_date}</td>`;
            html += `<td>${valueDisplay}${entry.has_dimensions ? ' <span class="badge badge-info">Dimensional</span>' : ''}</td>`;
            html += `<td>${notesDisplay}</td>`;
            html += `<td class="attachments-cell">${attachmentsDisplay}</td>`;
            html += `<td>${submittedDate}</td>`;
            html += '</tr>';
        });

        html += '</tbody></table>';

        // Add "Load More" button if there's more data
        if (hasMore) {
            html += '<div class="text-center mt-3">';
            html += `<button class="btn btn-sm btn-outline-primary load-more-btn" onclick="window.modalManager.loadMoreHistory('${fieldId}')">`;
            html += 'Load More <i class="bi bi-arrow-down"></i></button>';
            html += '</div>';
        }

        html += '</div>';
        historyContent.innerHTML = html;
    }

    /**
     * Load more history entries
     * @param {string} fieldId - Field ID
     */
    async loadMoreHistory(fieldId) {
        this.historyPaginationState.currentOffset += this.historyPaginationState.limit;
        await this.loadFieldHistory(fieldId, false);
    }

    /**
     * Export field history
     * @param {string} fieldId - Field ID
     * @param {string} format - Export format (csv or excel)
     */
    async exportFieldHistory(fieldId, format) {
        try {
            const entityId = document.getElementById('entitySelect')?.value || window.currentEntityId;
            const url = `/api/user/v2/export/field-history/${fieldId}?format=${format}&entity_id=${entityId}`;

            const buttons = document.querySelectorAll('.export-buttons button');
            buttons.forEach(btn => {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Exporting...';
            });

            window.location.href = url;

            setTimeout(() => {
                buttons.forEach(btn => {
                    btn.disabled = false;
                    if (btn.onclick.toString().includes('csv')) {
                        btn.innerHTML = '<i class="bi bi-download"></i> CSV';
                    } else {
                        btn.innerHTML = '<i class="bi bi-file-earmark-excel"></i> Excel';
                    }
                });
            }, 2000);

        } catch (error) {
            console.error('[ModalManager] Error exporting field history:', error);
            alert('Failed to export data. Please try again.');
        }
    }

    /**
     * Attach other UI event handlers
     */
    attachUIHandlers() {
        // Entity switcher (for admins)
        const entitySelect = document.getElementById('entitySelect');
        if (entitySelect) {
            entitySelect.addEventListener('change', function() {
                window.location.reload();
            });
        }

        // Fiscal Year selector
        const fySelect = document.getElementById('fySelect');
        if (fySelect) {
            fySelect.addEventListener('change', function() {
                const fyYear = parseInt(this.value);
                const currentUrl = new URL(window.location.href);
                currentUrl.searchParams.set('fy_year', fyYear);
                window.location.href = currentUrl.toString();
            });
        }

        // File upload area
        const fileUploadArea = document.getElementById('fileUploadArea');
        const fileInput = document.getElementById('fileInput');

        if (fileUploadArea && fileInput) {
            fileUploadArea.addEventListener('click', () => fileInput.click());

            fileUploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                fileUploadArea.style.borderColor = '#16a34a';
            });

            fileUploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                fileUploadArea.style.borderColor = '#dee2e6';
            });

            fileUploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                fileUploadArea.style.borderColor = '#dee2e6';
            });
        }

        // Toggle to legacy view
        const toggleViewBtn = document.getElementById('toggleViewBtn');
        if (toggleViewBtn) {
            toggleViewBtn.addEventListener('click', function() {
                window.location.href = document.querySelector('#toggleViewBtn').getAttribute('data-legacy-url');
            });
        }
    }

    // Helper methods
    truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }
}

// Make available globally
window.ModalManager = ModalManager;

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    if (!window.modalManager) {
        window.modalManager = new ModalManager();
    }
});
