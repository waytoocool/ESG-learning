/**
 * Assignment Import Module
 * Handles CSV import functionality for data point assignments
 *
 * Dependencies: PopupManager, ImportConfirmationDialog
 */

class AssignmentImporter {
    constructor(dataPointsManager) {
        this.dataPointsManager = dataPointsManager;
        console.log('AssignmentImporter initialized');
    }

    /**
     * Main import method - triggers file selection and processing
     */
    async importAssignments() {
        try {
            console.log('Starting import process...');

            // Create file input
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = '.csv,.xlsx,.xls';
            fileInput.style.display = 'none';

            fileInput.onchange = async (event) => {
                const file = event.target.files[0];
                if (!file) return;

                try {
                    if (file.name.endsWith('.csv')) {
                        await this.processCsvImport(file);
                    } else {
                        PopupManager.showWarning('Import Format', 'Excel import is not yet supported. Please use CSV format.');
                    }
                } catch (error) {
                    console.error('Error processing import file:', error);
                    PopupManager.showError('Import Failed', 'Failed to process the import file. Please check the file format.');
                }

                // Clean up
                document.body.removeChild(fileInput);
            };

            document.body.appendChild(fileInput);
            fileInput.click();

        } catch (error) {
            console.error('Error starting import:', error);
            PopupManager.showError('Import Failed', 'Failed to start import process. Please try again.');
        }
    }

    /**
     * Process CSV file import
     */
    async processCsvImport(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onload = async (e) => {
                try {
                    const csvText = e.target.result;
                    const lines = csvText.split('\n');

                    if (lines.length < 2) {
                        PopupManager.showWarning('Import Format', 'Import file appears to be empty or has no data rows.');
                        resolve();
                        return;
                    }

                    // Parse CSV (simple implementation)
                    const headers = this.parseCsvLine(lines[0]);
                    const dataRows = lines.slice(1).filter(line => line.trim()).map(line => this.parseCsvLine(line));

                    console.log('Parsed import data:', { headers, dataRows: dataRows.length });

                    // Find required columns
                    const fieldIdCol = headers.findIndex(h => h.toLowerCase().includes('field id'));
                    const fieldNameCol = headers.findIndex(h => h.toLowerCase().includes('field name'));
                    const frequencyCol = headers.findIndex(h => h.toLowerCase().includes('frequency'));
                    const unitCol = headers.findIndex(h => h.toLowerCase().includes('unit'));
                    const entitiesCol = headers.findIndex(h => h.toLowerCase().includes('assigned entities') || h.toLowerCase().includes('entities'));
                    const topicCol = headers.findIndex(h => h.toLowerCase().includes('topic'));

                    if (fieldIdCol === -1) {
                        PopupManager.showError('Import Format', 'Required column "Field ID" not found in import file.');
                        resolve();
                        return;
                    }

                    // Prepare assignments data for validation
                    const assignmentsToValidate = [];

                    for (const row of dataRows) {
                        if (row.length <= fieldIdCol) continue;

                        const fieldId = row[fieldIdCol]?.trim();
                        const fieldName = (fieldNameCol >= 0 && row[fieldNameCol]) ? row[fieldNameCol].trim() : fieldId;

                        if (!fieldId) continue;

                        // Parse assigned entities (comma or semicolon-separated, handle quoted values)
                        const assignedEntitiesRaw = (entitiesCol >= 0 && row[entitiesCol]) ? row[entitiesCol].trim() : '';
                        const assignedEntities = assignedEntitiesRaw ?
                            assignedEntitiesRaw.split(/[,;]/).map(e => e.trim()).filter(e => e.length > 0) :
                            [];

                        // Build assignment data for validation
                        const assignmentData = {
                            field_id: fieldId,
                            field_name: fieldName,
                            frequency: (frequencyCol >= 0 && row[frequencyCol]) ? row[frequencyCol].trim() : 'Annual',
                            unit: (unitCol >= 0 && row[unitCol]) ? row[unitCol].trim() : null,
                            assigned_entities: assignedEntities,
                            topic: (topicCol >= 0 && row[topicCol]) ? row[topicCol].trim() : null
                        };

                        assignmentsToValidate.push(assignmentData);
                    }

                    // Initialize counters
                    let importCount = 0;
                    let skipCount = 0;
                    let validationResults = [];
                    let successfulImports = [];
                    let saveSuccess = false;

                    // Step 1: Call validation endpoint
                    console.log('Validating import data with backend...');

                    const validationResponse = await fetch('/admin/api/assignments/validate-import', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            assignments: assignmentsToValidate
                        })
                    });

                    const validationData = await validationResponse.json();

                    if (!validationData.success) {
                        PopupManager.showError('Validation Failed', validationData.error || 'Failed to validate import data.');
                        resolve();
                        return;
                    }

                    // Step 2: Show confirmation dialog with validation results
                    // Note: Using simple confirm to bypass modal issues temporarily
                    let userConfirmed;
                    console.log('DEBUG: Validation successful, showing confirmation. Validation data:', validationData);
                    userConfirmed = confirm(`Import ${assignmentsToValidate.length} assignments? This will update your data point assignments.\n\nValidation Summary:\nTotal: ${validationData.validation.total_records}\nValid: ${validationData.validation.valid_count}\nWarnings: ${validationData.validation.warning_count}\nErrors: ${validationData.validation.error_count}`);
                    console.log('DEBUG: User confirmed:', userConfirmed);

                    if (!userConfirmed) {
                        console.log('User cancelled import');
                        resolve();
                        return;
                    }

                    // Step 3: Proceed with actual import if user confirmed
                    console.log('User confirmed import, proceeding...');

                    try {
                        const importResponse = await fetch('/admin/api/assignments/import', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                assignments: assignmentsToValidate
                            })
                        });

                        const importResult = await importResponse.json();

                        if (importResult.success) {
                            saveSuccess = true;
                            console.log('DEBUG: Backend import successful, processing results...', {
                                resultCount: importResult.results ? importResult.results.length : 0,
                                summary: importResult.summary
                            });

                            // Update local UI state for successful assignments
                            try {
                                importResult.results.forEach((fieldResult, index) => {
                                    console.log(`DEBUG: Processing result ${index + 1}:`, fieldResult);

                                    if (fieldResult.success) {
                                        // Update frontend selections for successful imports
                                        const field = this.dataPointsManager.availableFields ?
                                            this.dataPointsManager.availableFields.find(f => f.field_id === fieldResult.field_id) : null;

                                        console.log(`DEBUG: Found field for ${fieldResult.field_id}:`, field ? 'YES' : 'NO');

                                        if (field) {
                                            this.dataPointsManager.selectedDataPoints.set(fieldResult.field_id, field);
                                            this.dataPointsManager.currentSelectedPoints.add(fieldResult.field_id);

                                            // Build basic config for UI display
                                            const assignmentData = assignmentsToValidate.find(a => a.field_id === fieldResult.field_id);
                                            if (assignmentData) {
                                                this.dataPointsManager.configurations.set(fieldResult.field_id, {
                                                    frequency: assignmentData.frequency,
                                                    unit: assignmentData.unit,
                                                    collection_method: 'Manual Entry',
                                                    validation_rules: 'Required',
                                                    approval_required: false
                                                });
                                            }

                                            successfulImports.push(fieldResult.field_id);
                                            console.log(`DEBUG: Successfully processed field ${fieldResult.field_id}`);
                                        } else {
                                            console.log(`DEBUG: Field ${fieldResult.field_id} not found in availableFields`);
                                            // Add field-level error from backend
                                            validationResults.push({
                                                type: 'error',
                                                field: fieldResult.field_name,
                                                message: fieldResult.message
                                            });
                                        }
                                    } else {
                                        console.log(`DEBUG: Field result failed:`, fieldResult);
                                    }
                                });
                            } catch (processError) {
                                console.error('DEBUG: Error processing import results:', processError);
                                validationResults.push({
                                    type: 'error',
                                    field: 'Frontend Processing',
                                    message: `Error processing results: ${processError.message}`
                                });
                            }

                            // Update counts based on backend results
                            importCount = importResult.summary.total_created + importResult.summary.total_updated;
                            skipCount = importResult.summary.total_skipped;

                        } else {
                            throw new Error(importResult.error || importResult.message || 'Import failed');
                        }
                    } catch (error) {
                        console.error('Failed to import to backend:', error);
                        validationResults.push({
                            type: 'error',
                            field: 'Backend',
                            message: `Failed to import: ${error.message}`
                        });
                    }

                    // Update UI with successful imports - wrapped in try-catch to identify DOM errors
                    try {
                        console.log('DEBUG: About to call updateUIComponents...', {
                            dataPointsManager: this.dataPointsManager,
                            hasUpdateUIComponents: typeof this.dataPointsManager?.updateUIComponents === 'function'
                        });

                        if (this.dataPointsManager && typeof this.dataPointsManager.updateUIComponents === 'function') {
                            this.dataPointsManager.updateUIComponents();
                            console.log('DEBUG: updateUIComponents completed successfully');
                        } else {
                            console.warn('DEBUG: updateUIComponents is not available or not a function');
                        }
                    } catch (domError) {
                        console.error('DEBUG: DOM manipulation error in updateUIComponents:', domError);
                        console.error('DEBUG: Error stack:', domError.stack);
                        // Continue with import completion even if UI update fails
                    }

                    // Show detailed validation results - wrapped in try-catch to identify DOM errors
                    try {
                        console.log('DEBUG: About to show import results...', {
                            importCount,
                            skipCount,
                            validationResultsCount: validationResults.length,
                            successfulImportsCount: successfulImports.length,
                            saveSuccess
                        });

                        this.showImportResults(importCount, skipCount, validationResults, successfulImports, saveSuccess);
                        console.log('DEBUG: Import results displayed successfully');
                    } catch (resultsError) {
                        console.error('DEBUG: Error showing import results:', resultsError);
                        console.error('DEBUG: Results error stack:', resultsError.stack);

                        // Fallback: try basic alert if popup fails
                        try {
                            alert(`Import completed. Created/Updated: ${importCount}, Skipped: ${skipCount}`);
                        } catch (alertError) {
                            console.error('DEBUG: Even alert failed:', alertError);
                        }
                    }

                    console.log('Import completed:', { importCount, skipCount, validationResults });

                    resolve();
                } catch (error) {
                    console.error('Error during import process:', error);
                    PopupManager.showError('Import Failed', 'Failed to process the import. Please try again.');
                    reject(error);
                }
            };

            reader.onerror = () => {
                reject(new Error('Failed to read file'));
            };

            reader.readAsText(file);
        });
    }

    /**
     * Parse a single CSV line handling quoted values
     */
    parseCsvLine(line) {
        const result = [];
        let current = '';
        let inQuotes = false;

        for (let i = 0; i < line.length; i++) {
            const char = line[i];

            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                result.push(current.trim());
                current = '';
            } else {
                current += char;
            }
        }

        result.push(current.trim());
        return result;
    }

    /**
     * Show import results to user
     */
    showImportResults(importCount, skipCount, validationResults, successfulImports, saveSuccess) {
        const totalProcessed = importCount + skipCount;

        // Build detailed results HTML
        let resultsHtml = `
            <div class="import-results">
                <div class="results-summary">
                    <h4>Import Summary</h4>
                    <p><strong>Total Records Processed:</strong> ${totalProcessed}</p>
                    <p><strong>Successfully Imported:</strong> ${importCount}</p>
                    <p><strong>Skipped:</strong> ${skipCount}</p>
                    <p><strong>Backend Save:</strong> ${saveSuccess ? 'SUCCESS' : 'FAILED'}</p>
                </div>`;

        if (validationResults.length > 0) {
            resultsHtml += `
                <div class="validation-details">
                    <h4>Import Details</h4>
                    <ul>`;

            validationResults.forEach(result => {
                const statusClass = result.type === 'error' ? 'error' : 'warning';
                resultsHtml += `<li class="${statusClass}"><strong>${result.field}:</strong> ${result.message}</li>`;
            });

            resultsHtml += `</ul></div>`;
        }

        resultsHtml += `</div>`;

        // Show results in popup
        if (saveSuccess && importCount > 0) {
            PopupManager.showSuccess('Import Completed', resultsHtml);
        } else if (totalProcessed > 0) {
            PopupManager.showWarning('Import Completed with Issues', resultsHtml);
        } else {
            PopupManager.showWarning('No Data Imported', 'No valid assignments were found to import.');
        }
    }
}

// Export for use in other modules
window.AssignmentImporter = AssignmentImporter;