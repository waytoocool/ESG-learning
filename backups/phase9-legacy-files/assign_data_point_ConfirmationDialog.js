// Import Confirmation Dialog for Assignment Data Points
// Provides detailed validation preview and confirmation before importing CSV files

class ImportConfirmationDialog {
    constructor() {
        this.currentValidationData = null;
        this.currentFileData = null;
    }

    /**
     * Show validation preview dialog with detailed results
     */
    async showValidationDialog(validationData, originalFileData) {
        this.currentValidationData = validationData;
        this.currentFileData = originalFileData;

        return new Promise((resolve) => {
            this.populateValidationModal(validationData);
            this.showModal('importValidationModal', resolve);
        });
    }

    /**
     * Populate the validation modal with data
     */
    populateValidationModal(data) {
        const { validation, results, preview } = data;

        // Update status
        this.updateValidationStatus(validation);

        // Update summary
        this.updateSummarySection(validation);

        // Update preview
        this.updatePreviewSection(preview);

        // Update detailed results
        this.updateDetailedResultsSection(results);

        // Update button states
        this.updateButtonStates(validation);
    }

    /**
     * Update validation status in header
     */
    updateValidationStatus(validation) {
        const statusIcon = document.querySelector('#importValidationModal .validation-status .status-icon');
        const statusText = document.querySelector('#importValidationModal .validation-status .status-text');
        const validationStatus = document.querySelector('#importValidationModal .validation-status');

        let icon = '⚠️';
        let color = '#ff9800';
        let text = 'Validation Issues Found';

        if (validation.error_count === 0 && validation.warning_count === 0) {
            icon = '✅';
            color = '#4caf50';
            text = 'Ready to Import';
        } else if (validation.error_count > 0) {
            icon = '❌';
            color = '#f44336';
            text = 'Cannot Import - Errors Found';
        }

        // Add null checks before setting properties
        if (statusIcon) {
            statusIcon.textContent = icon;
        } else {
            console.warn('Status icon element not found in DOM');
        }

        if (statusText) {
            statusText.textContent = text;
        } else {
            console.warn('Status text element not found in DOM');
        }

        if (validationStatus) {
            validationStatus.style.color = color;
        } else {
            console.warn('Validation status element not found in DOM');
        }
    }

    /**
     * Update summary section
     */
    updateSummarySection(validation) {
        const elements = {
            totalRecords: document.getElementById('totalRecords'),
            validCount: document.getElementById('validCount'),
            warningCount: document.getElementById('warningCount'),
            errorCount: document.getElementById('errorCount')
        };

        // Add null checks for each element
        if (elements.totalRecords) {
            elements.totalRecords.textContent = validation.total_records;
        } else {
            console.warn('Total records element not found in DOM');
        }

        if (elements.validCount) {
            elements.validCount.textContent = validation.valid_count;
        } else {
            console.warn('Valid count element not found in DOM');
        }

        if (elements.warningCount) {
            elements.warningCount.textContent = validation.warning_count;
        } else {
            console.warn('Warning count element not found in DOM');
        }

        if (elements.errorCount) {
            elements.errorCount.textContent = validation.error_count;
        } else {
            console.warn('Error count element not found in DOM');
        }
    }

    /**
     * Update preview section
     */
    updatePreviewSection(preview) {
        const previewCount = document.getElementById('previewCount');
        const previewList = document.getElementById('previewList');

        if (!preview || preview.length === 0) {
            if (previewCount) {
                previewCount.textContent = 'No valid records to import';
            } else {
                console.warn('Preview count element not found in DOM');
            }

            if (previewList) {
                previewList.innerHTML = '<div style="padding: 20px; text-align: center; color: #9ca3af; font-style: italic;">No records available</div>';
            } else {
                console.warn('Preview list element not found in DOM');
            }
            return;
        }

        const showingText = preview.length > 10 ? `Showing first 10 of ${preview.length} records` : `${preview.length} records to import`;

        if (previewCount) {
            previewCount.textContent = showingText;
        } else {
            console.warn('Preview count element not found in DOM');
        }

        const previewRows = preview.slice(0, 10).map(item => `
            <div class="preview-item ${item.action}">
                <div class="field-info">
                    <strong>${item.field_name}</strong>
                    <small>(${item.field_id})</small>
                </div>
                <div class="action-info">
                    <span class="action-badge">${item.action.toUpperCase()}</span>
                    <span class="entities">${item.entities.join(', ')}</span>
                    ${item.deactivations > 0 ? `<span class="deactivation-note">Will deactivate ${item.deactivations} existing assignments</span>` : ''}
                </div>
            </div>
        `).join('');

        if (previewList) {
            previewList.innerHTML = previewRows;
        } else {
            console.warn('Preview list element not found in DOM');
        }
    }

    /**
     * Update detailed validation results section
     */
    updateDetailedResultsSection(results) {
        const validationDetails = document.getElementById('validationDetails');

        if (!validationDetails) {
            console.warn('Validation details element not found in DOM');
            return;
        }

        const errorResults = results.filter(r => r.status === 'error');
        const warningResults = results.filter(r => r.status === 'warning');

        let detailsHTML = '';

        if (errorResults.length > 0) {
            detailsHTML += `
                <div class="error-section">
                    <h5>❌ Errors (${errorResults.length})</h5>
                    <div class="result-list">
                        ${errorResults.map(result => this.createResultItem(result, 'error')).join('')}
                    </div>
                </div>
            `;
        }

        if (warningResults.length > 0) {
            detailsHTML += `
                <div class="warning-section">
                    <h5>⚠️ Warnings (${warningResults.length})</h5>
                    <div class="result-list">
                        ${warningResults.map(result => this.createResultItem(result, 'warning')).join('')}
                    </div>
                </div>
            `;
        }

        validationDetails.innerHTML = detailsHTML;
    }

    /**
     * Create individual result item
     */
    createResultItem(result, type) {
        const issuesText = result.issues.join(', ');
        const deactivationsText = result.assignments_to_deactivate.length > 0
            ? `<div class="deactivation-info">Will deactivate: ${result.assignments_to_deactivate.map(a => a.entity_name).join(', ')}</div>`
            : '';

        return `
            <div class="result-item ${type}">
                <div class="result-header">
                    <strong>${result.field_name}</strong>
                    <small>(${result.field_id})</small>
                </div>
                <div class="result-issues">${issuesText}</div>
                ${deactivationsText}
            </div>
        `;
    }

    /**
     * Update button states
     */
    updateButtonStates(validation) {
        const confirmBtn = document.getElementById('confirmImport');

        if (confirmBtn) {
            if (validation.can_proceed) {
                confirmBtn.disabled = false;
                confirmBtn.textContent = 'Proceed with Import';
            } else {
                confirmBtn.disabled = true;
                confirmBtn.textContent = 'Cannot Import';
            }
        } else {
            console.warn('Confirm import button not found in DOM');
        }
    }

    /**
     * Show modal with proper event handling
     */
    showModal(modalId, resolve) {
        const modal = document.getElementById(modalId);
        const confirmBtn = document.getElementById('confirmImport');
        const cancelBtns = modal.querySelectorAll('#cancelImport, #cancelImportBtn');

        // Show modal
        modal.style.display = 'flex';
        requestAnimationFrame(() => {
            modal.classList.add('show');
            // Focus appropriate button
            if (this.currentValidationData?.validation?.can_proceed) {
                confirmBtn.focus();
            } else {
                cancelBtns[0].focus();
            }
        });

        // Event handlers
        const handleConfirm = () => {
            this.hideModal(modal);
            resolve(true);
        };

        const handleCancel = () => {
            this.hideModal(modal);
            resolve(false);
        };

        // Add event listeners
        confirmBtn.addEventListener('click', handleConfirm, { once: true });
        cancelBtns.forEach(btn => {
            btn.addEventListener('click', handleCancel, { once: true });
        });

        // ESC key support
        const handleKeydown = (e) => {
            if (e.key === 'Escape') {
                document.removeEventListener('keydown', handleKeydown);
                handleCancel();
            }
        };
        document.addEventListener('keydown', handleKeydown);

        // Click outside to cancel
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                handleCancel();
            }
        }, { once: true });
    }

    /**
     * Hide modal with animation
     */
    hideModal(modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }

    /**
     * Show final import results dialog (persistent)
     */
    showResultsDialog(title, resultsHTML) {
        const modal = document.getElementById('importResultsModal');
        const titleElement = document.getElementById('resultsTitle');
        const bodyElement = document.getElementById('resultsBody');
        const closeBtns = modal.querySelectorAll('#closeResults, #closeResultsBtn');

        // Populate content
        titleElement.textContent = title;
        bodyElement.innerHTML = resultsHTML;

        // Show modal
        modal.style.display = 'flex';
        requestAnimationFrame(() => {
            modal.classList.add('show');
            closeBtns[0].focus();
        });

        const handleClose = () => {
            this.hideModal(modal);
        };

        // Add event listeners
        closeBtns.forEach(btn => {
            btn.addEventListener('click', handleClose, { once: true });
        });

        // ESC key support
        document.addEventListener('keydown', function escHandler(e) {
            if (e.key === 'Escape') {
                document.removeEventListener('keydown', escHandler);
                handleClose();
            }
        });
    }
}

// Make globally available
window.ImportConfirmationDialog = ImportConfirmationDialog;