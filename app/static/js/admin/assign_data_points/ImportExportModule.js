/**
 * ImportExportModule.js
 *
 * Import and Export Functionality Module
 *
 * This module handles all import/export operations including:
 * - CSV file import with validation
 * - Bulk assignment creation
 * - Export to CSV format
 * - Template generation
 * - Import preview and error reporting
 *
 * Dependencies: ServicesModule, VersioningModule, PopupsModule, AppEvents
 *
 * @version 1.0.0
 * @date 2025-01-30
 */

(function() {
    'use strict';

    // Module-level state
    const state = {
        importPreviewData: null,
        validationErrors: [],
        importProgress: 0,
        isImporting: false,
        initialized: false
    };

    // Configuration
    const CONFIG = {
        maxFileSize: 5 * 1024 * 1024,  // 5MB
        supportedFormats: ['.csv'],
        batchSize: 100,                 // Process imports in batches
        progressInterval: 50            // Update progress every N rows
    };

    /**
     * Initialize the ImportExportModule
     */
    function init() {
        if (state.initialized) {
            console.warn('[ImportExportModule] Already initialized');
            return;
        }

        console.log('[ImportExportModule] Initializing...');

        // Set up event listeners
        setupEventListeners();

        // Bind UI elements
        bindUIElements();

        state.initialized = true;
        console.log('[ImportExportModule] Initialization complete');
    }

    /**
     * Set up event listeners
     */
    function setupEventListeners() {
        if (!window.AppEvents) {
            console.error('[ImportExportModule] AppEvents not available');
            return;
        }

        // Listen for toolbar import/export clicks
        window.AppEvents.on('toolbar-import-clicked', handleImportClicked);
        window.AppEvents.on('toolbar-export-clicked', handleExportClicked);

        console.log('[ImportExportModule] Event listeners registered');
    }

    /**
     * Bind UI elements
     *
     * NOTE: Direct button bindings removed to prevent duplicate event handling.
     * CoreUI.js handles button clicks and emits events via AppEvents.
     * This module listens for those events via setupEventListeners().
     */
    function bindUIElements() {
        // UI element binding removed - using event system only
        // CoreUI.js binds the buttons and emits events
        // This module listens via setupEventListeners()

        console.log('[ImportExportModule] UI elements binding skipped - using event system');
    }

    /**
     * Handle import button click
     */
    function handleImportClicked() {
        console.log('[ImportExportModule] Starting import process');

        // Create hidden file input
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = CONFIG.supportedFormats.join(',');
        fileInput.style.display = 'none';

        fileInput.onchange = async (event) => {
            const file = event.target.files[0];
            if (file) {
                await handleImportFile(file);
            }
            document.body.removeChild(fileInput);
        };

        document.body.appendChild(fileInput);
        fileInput.click();
    }

    /**
     * Handle export button click
     */
    async function handleExportClicked() {
        console.log('[ImportExportModule] Starting export process');

        try {
            // Show loading message
            if (window.ServicesModule && window.ServicesModule.showMessage) {
                window.ServicesModule.showMessage('Preparing export...', 'info');
            }

            // Get current assignments
            const assignments = await fetchAssignmentsForExport();

            if (!assignments || assignments.length === 0) {
                if (window.ServicesModule) {
                    window.ServicesModule.showMessage('No assignments to export', 'warning');
                }
                return;
            }

            // Generate CSV
            const csvContent = generateExportCSV(assignments);

            // Download file
            const filename = `assignments_export_${new Date().toISOString().split('T')[0]}.csv`;
            downloadCSV(csvContent, filename);

            // Emit event
            if (window.AppEvents) {
                window.AppEvents.emit('export-generated', {
                    count: assignments.length,
                    filename: filename
                });
            }

            if (window.ServicesModule) {
                window.ServicesModule.showMessage(`Exported ${assignments.length} assignments successfully`, 'success');
            }

        } catch (error) {
            console.error('[ImportExportModule] Export error:', error);
            if (window.ServicesModule) {
                window.ServicesModule.showMessage('Export failed: ' + error.message, 'error');
            }
        }
    }

    /**
     * Handle import file upload
     */
    async function handleImportFile(file) {
        console.log('[ImportExportModule] Processing import file:', file.name);

        try {
            // Validate file
            const validation = validateImportFile(file);
            if (!validation.isValid) {
                if (window.ServicesModule) {
                    window.ServicesModule.showMessage(validation.error, 'error');
                }
                return;
            }

            // Read and parse file
            const fileContent = await readFileContent(file);
            const parsedData = parseCSVFile(fileContent);

            // Validate data (BUG FIX: now async to load entities)
            const validationResult = await validateImportData(parsedData.rows, parsedData.headers);

            // Store preview data
            state.importPreviewData = {
                rows: parsedData.rows,
                headers: parsedData.headers,
                validation: validationResult
            };

            // Show import preview/validation modal
            showImportPreview(validationResult);

        } catch (error) {
            console.error('[ImportExportModule] Import file processing error:', error);
            if (window.ServicesModule) {
                window.ServicesModule.showMessage('Failed to process import file: ' + error.message, 'error');
            }
        }
    }

    /**
     * Validate import file
     */
    function validateImportFile(file) {
        if (!file) {
            return { isValid: false, error: 'No file selected' };
        }

        // Check file size
        if (file.size > CONFIG.maxFileSize) {
            return {
                isValid: false,
                error: `File size exceeds limit (${CONFIG.maxFileSize / 1024 / 1024}MB)`
            };
        }

        // Check file format
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();
        if (!CONFIG.supportedFormats.includes(fileExt)) {
            return {
                isValid: false,
                error: `Unsupported file format. Please use: ${CONFIG.supportedFormats.join(', ')}`
            };
        }

        return { isValid: true };
    }

    /**
     * Read file content as text
     */
    function readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = () => reject(new Error('Failed to read file'));

            reader.readAsText(file);
        });
    }

    /**
     * Parse CSV file content
     */
    function parseCSVFile(csvText) {
        console.log('[ImportExportModule] Parsing CSV content');

        // Remove BOM if present (UTF-8 BOM is EF BB BF, appears as \uFEFF in JavaScript)
        if (csvText.charCodeAt(0) === 0xFEFF) {
            csvText = csvText.slice(1);
            console.log('[ImportExportModule] Removed BOM from CSV');
        }

        // Split by newlines (handle both \r\n and \n) and filter empty lines
        const lines = csvText
            .replace(/\r\n/g, '\n')  // Normalize Windows line endings
            .replace(/\r/g, '\n')    // Normalize old Mac line endings
            .split('\n')
            .filter(line => line.trim());

        if (lines.length < 2) {
            throw new Error('CSV file is empty or has no data rows');
        }

        // Parse header row
        const headers = parseCSVLine(lines[0]);
        console.log('[ImportExportModule] Parsed headers:', headers);

        // Parse data rows
        const rows = lines.slice(1).map((line, index) => ({
            rowNumber: index + 2, // +2 because: +1 for 1-based indexing, +1 for header row
            data: parseCSVLine(line)
        }));

        console.log(`[ImportExportModule] Parsed ${rows.length} data rows`);

        return { headers, rows };
    }

    /**
     * Parse a single CSV line (handles quoted values)
     */
    function parseCSVLine(line) {
        const result = [];
        let current = '';
        let inQuotes = false;

        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            const nextChar = line[i + 1];

            if (char === '"') {
                if (inQuotes && nextChar === '"') {
                    // Escaped quote
                    current += '"';
                    i++; // Skip next quote
                } else {
                    // Toggle quotes
                    inQuotes = !inQuotes;
                }
            } else if (char === ',' && !inQuotes) {
                // Field separator
                result.push(current.trim());
                current = '';
            } else {
                current += char;
            }
        }

        // Add last field
        result.push(current.trim());

        return result;
    }

    /**
     * Validate import data
     */
    async function validateImportData(rows, headers) {
        console.log('[ImportExportModule] Validating import data');

        const validationResult = {
            totalRecords: rows.length,
            validRecords: [],
            invalidRecords: [],
            warnings: []
        };

        // Find required column indices
        const columnMap = mapColumns(headers);

        if (columnMap.field_id === undefined) {
            throw new Error('Required column "Field ID" not found');
        }

        // BUG FIX: Load entities for entity name resolution
        // Check if we have Entity Name column (new format) or Entity ID column (legacy format)
        const useEntityName = columnMap.entity_name !== undefined;
        const useEntityId = columnMap.entity_id !== undefined;

        if (!useEntityName && !useEntityId) {
            throw new Error('Required column "Entity Name" or "Entity ID" not found. Please use "Entity Name" in your CSV.');
        }

        // Load entity lookup map for name-to-ID resolution
        let entityLookup = null;
        if (useEntityName) {
            try {
                const entities = await window.ServicesModule.loadEntities();
                // Create case-insensitive lookup: entity name (lowercase) -> entity object
                entityLookup = {};
                entities.forEach(entity => {
                    const normalizedName = entity.name.toLowerCase().trim();
                    entityLookup[normalizedName] = entity;
                });
                console.log('[ImportExportModule] Loaded entity lookup for validation:', Object.keys(entityLookup).length, 'entities');
            } catch (error) {
                throw new Error('Failed to load entities for import validation: ' + error.message);
            }
        }

        // Validate each row
        rows.forEach(row => {
            const rowValidation = validateRow(row, columnMap, entityLookup, useEntityName);

            if (rowValidation.isValid) {
                validationResult.validRecords.push({
                    rowNumber: row.rowNumber,
                    data: rowValidation.data
                });
            } else {
                validationResult.invalidRecords.push({
                    rowNumber: row.rowNumber,
                    errors: rowValidation.errors
                });
            }

            if (rowValidation.warnings && rowValidation.warnings.length > 0) {
                validationResult.warnings.push({
                    rowNumber: row.rowNumber,
                    warnings: rowValidation.warnings
                });
            }
        });

        console.log('[ImportExportModule] Validation complete:', {
            valid: validationResult.validRecords.length,
            invalid: validationResult.invalidRecords.length,
            warnings: validationResult.warnings.length
        });

        return validationResult;
    }

    /**
     * Map column headers to field names
     */
    function mapColumns(headers) {
        const map = {};

        console.log('[ImportExportModule] Mapping columns from headers:', headers);

        headers.forEach((header, index) => {
            // Clean header: trim whitespace and normalize case
            const normalized = header.toLowerCase().trim();

            console.log(`  [${index}] "${header}" -> normalized: "${normalized}"`);

            if (normalized.includes('field id')) {
                map.field_id = index;
            } else if (normalized.includes('field name')) {
                map.field_name = index;
            } else if (normalized.includes('entity id')) {
                map.entity_id = index;
            } else if (normalized.includes('entity name')) {
                map.entity_name = index;
            } else if (normalized.includes('frequency')) {
                map.frequency = index;
            } else if (normalized.includes('start date')) {
                map.start_date = index;
            } else if (normalized.includes('end date')) {
                map.end_date = index;
            } else if (normalized.includes('required')) {
                map.required = index;
            } else if (normalized.includes('unit')) {
                map.unit = index;
            } else if (normalized.includes('topic')) {
                map.topic = index;
            } else if (normalized.includes('notes')) {
                map.notes = index;
            }
        });

        console.log('[ImportExportModule] Column mapping result:', map);

        return map;
    }

    /**
     * Validate a single row
     */
    function validateRow(row, columnMap, entityLookup = null, useEntityName = false) {
        const errors = [];
        const warnings = [];
        const data = {};

        // Required: field_id
        const fieldId = row.data[columnMap.field_id]?.trim();
        if (!fieldId) {
            errors.push('Field ID is required');
        } else {
            data.field_id = fieldId;
        }

        // ENHANCEMENT: Handle both Entity Name (new format with comma-separated support) and Entity ID (legacy format)
        if (useEntityName) {
            // New format: Entity Name (supports comma-separated entity names)
            let entityNamesStr = row.data[columnMap.entity_name]?.trim();

            // BUG FIX: Remove any remaining surrounding quotes as defensive programming
            // This handles edge cases where parseCSVLine might not remove quotes (e.g., different quote chars, BOM issues)
            if (entityNamesStr && entityNamesStr.startsWith('"') && entityNamesStr.endsWith('"')) {
                entityNamesStr = entityNamesStr.slice(1, -1).trim();
            }

            if (!entityNamesStr) {
                errors.push('Entity Name is required');
            } else if (!entityLookup) {
                errors.push('Entity lookup not available');
            } else {
                // Split by comma and trim each name
                const entityNames = entityNamesStr.split(',').map(n => n.trim()).filter(n => n);

                if (entityNames.length === 0) {
                    errors.push('At least one entity name is required');
                } else {
                    // Validate each entity name and collect entity IDs
                    const entityIds = [];
                    const validEntityNames = [];
                    const invalidEntities = [];

                    entityNames.forEach(entityName => {
                        const normalizedName = entityName.toLowerCase().trim();
                        const entity = entityLookup[normalizedName];

                        if (!entity) {
                            invalidEntities.push(entityName);
                        } else {
                            entityIds.push(entity.id);
                            validEntityNames.push(entity.name); // Store actual entity name for display
                        }
                    });

                    if (invalidEntities.length > 0) {
                        errors.push(`Entity names not found: ${invalidEntities.join(', ')}`);
                    } else if (entityIds.length > 0) {
                        // Store as array for multi-entity assignment
                        data.entity_ids = entityIds;
                        data.entity_names = validEntityNames; // For display

                        // Also keep single entity_id for backward compatibility (use first entity)
                        data.entity_id = entityIds[0];
                        data.entity_name = validEntityNames[0];
                    }
                }
            }
        } else {
            // Legacy format: Entity ID (for backward compatibility)
            const entityId = row.data[columnMap.entity_id]?.trim();
            if (!entityId) {
                errors.push('Entity ID is required');
            } else if (isNaN(parseInt(entityId))) {
                errors.push('Entity ID must be a number');
            } else {
                data.entity_id = parseInt(entityId);
                data.entity_ids = [parseInt(entityId)]; // Also set array for consistency
            }
        }

        // Required: frequency
        const frequency = row.data[columnMap.frequency]?.trim();
        const validFrequencies = ['Once', 'Daily', 'Weekly', 'Monthly', 'Quarterly', 'Annual', 'Biennial'];
        if (!frequency) {
            errors.push('Frequency is required');
        } else if (!validFrequencies.includes(frequency)) {
            errors.push(`Invalid frequency: ${frequency}. Must be one of: ${validFrequencies.join(', ')}`);
        } else {
            data.frequency = frequency;
        }

        // Optional: unit
        if (columnMap.unit !== undefined && row.data[columnMap.unit]) {
            data.unit = row.data[columnMap.unit].trim();
        }

        // Optional: start_date
        if (columnMap.start_date !== undefined && row.data[columnMap.start_date]) {
            const startDate = row.data[columnMap.start_date].trim();
            if (!isValidDate(startDate)) {
                errors.push('Invalid start date format (use YYYY-MM-DD)');
            } else {
                data.start_date = startDate;
            }
        }

        // Optional: end_date
        if (columnMap.end_date !== undefined && row.data[columnMap.end_date]) {
            const endDate = row.data[columnMap.end_date].trim();
            if (!isValidDate(endDate)) {
                errors.push('Invalid end date format (use YYYY-MM-DD)');
            } else {
                data.end_date = endDate;
            }
        }

        // Optional: required flag
        if (columnMap.required !== undefined && row.data[columnMap.required]) {
            const requiredValue = row.data[columnMap.required].trim().toLowerCase();
            data.required = (requiredValue === 'true' || requiredValue === 'yes' || requiredValue === '1');
        }

        // Check for data range validity
        if (data.start_date && data.end_date) {
            if (new Date(data.start_date) > new Date(data.end_date)) {
                errors.push('Start date must be before end date');
            }
        }

        return {
            isValid: errors.length === 0,
            data: data,
            errors: errors,
            warnings: warnings
        };
    }

    /**
     * Validate date format (YYYY-MM-DD)
     */
    function isValidDate(dateString) {
        const regex = /^\d{4}-\d{2}-\d{2}$/;
        if (!regex.test(dateString)) return false;

        const date = new Date(dateString);
        return date instanceof Date && !isNaN(date);
    }

    /**
     * Show import preview modal
     */
    function showImportPreview(validationResult) {
        console.log('[ImportExportModule] Showing import preview');

        // Update validation modal content
        document.getElementById('totalRecords').textContent = validationResult.totalRecords;
        document.getElementById('validCount').textContent = validationResult.validRecords.length;
        document.getElementById('warningCount').textContent = validationResult.warnings.length;
        document.getElementById('errorCount').textContent = validationResult.invalidRecords.length;

        // Update preview content
        const previewList = document.getElementById('previewList');
        if (previewList) {
            previewList.innerHTML = renderPreviewList(validationResult);
        }

        // Show validation details
        const validationDetails = document.getElementById('validationDetails');
        if (validationDetails) {
            validationDetails.innerHTML = renderValidationDetails(validationResult);
        }

        // Show the validation modal
        const validationModal = document.getElementById('importValidationModal');
        if (validationModal) {
            validationModal.style.display = 'flex';
            // Add .show class to trigger opacity transition
            setTimeout(() => {
                validationModal.classList.add('show');
            }, 10);
        }

        // Bind confirm/cancel buttons
        bindImportModalButtons(validationResult);

        // Emit event
        if (window.AppEvents) {
            window.AppEvents.emit('import-preview-ready', validationResult);
        }
    }

    /**
     * Render preview list HTML
     * ENHANCEMENT: Display multiple entity names if available (comma-separated import)
     */
    function renderPreviewList(validationResult) {
        const validCount = validationResult.validRecords.length;

        if (validCount === 0) {
            return '<p class="no-records">No valid records to import</p>';
        }

        const previewItems = validationResult.validRecords.slice(0, 10).map(record => {
            // ENHANCEMENT: Show multiple entities if available
            let entityDisplay;
            if (record.data.entity_names && record.data.entity_names.length > 1) {
                // Multiple entities: show comma-separated with count
                entityDisplay = `${record.data.entity_names.join(', ')} (${record.data.entity_names.length} entities)`;
            } else if (record.data.entity_name) {
                // Single entity name
                entityDisplay = record.data.entity_name;
            } else {
                // Fallback to entity ID
                entityDisplay = `Entity ${record.data.entity_id}`;
            }

            return `
                <div class="preview-item valid">
                    <div class="preview-row">Row ${record.rowNumber}</div>
                    <div class="preview-field">${record.data.field_id}</div>
                    <div class="preview-entity">${entityDisplay}</div>
                    <div class="preview-frequency">${record.data.frequency}</div>
                </div>
            `;
        }).join('');

        const remaining = validCount > 10 ? `<p class="preview-more">... and ${validCount - 10} more records</p>` : '';

        return previewItems + remaining;
    }

    /**
     * Render validation details HTML
     */
    function renderValidationDetails(validationResult) {
        if (validationResult.invalidRecords.length === 0 && validationResult.warnings.length === 0) {
            return '<p class="no-errors">✅ All records passed validation</p>';
        }

        let html = '';

        // Show errors
        if (validationResult.invalidRecords.length > 0) {
            html += '<div class="validation-section error-section"><h5>❌ Errors:</h5><ul>';
            validationResult.invalidRecords.forEach(record => {
                html += `<li>Row ${record.rowNumber}: ${record.errors.join(', ')}</li>`;
            });
            html += '</ul></div>';
        }

        // Show warnings
        if (validationResult.warnings.length > 0) {
            html += '<div class="validation-section warning-section"><h5>⚠️ Warnings:</h5><ul>';
            validationResult.warnings.forEach(record => {
                html += `<li>Row ${record.rowNumber}: ${record.warnings.join(', ')}</li>`;
            });
            html += '</ul></div>';
        }

        return html;
    }

    /**
     * Bind import modal buttons
     */
    function bindImportModalButtons(validationResult) {
        // Confirm import button
        const confirmBtn = document.getElementById('confirmImport');
        if (confirmBtn) {
            // Remove existing listeners
            const newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

            newConfirmBtn.addEventListener('click', async () => {
                await processImportRows(validationResult.validRecords);
                closeImportModal();
            });

            // Disable if no valid records
            newConfirmBtn.disabled = validationResult.validRecords.length === 0;
        }

        // Cancel button
        const cancelBtn = document.getElementById('cancelImportBtn');
        if (cancelBtn) {
            const newCancelBtn = cancelBtn.cloneNode(true);
            cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);

            newCancelBtn.addEventListener('click', closeImportModal);
        }

        // Close button (X)
        const closeBtn = document.getElementById('cancelImport');
        if (closeBtn) {
            const newCloseBtn = closeBtn.cloneNode(true);
            closeBtn.parentNode.replaceChild(newCloseBtn, closeBtn);

            newCloseBtn.addEventListener('click', closeImportModal);
        }
    }

    /**
     * Close import modal
     */
    function closeImportModal() {
        const validationModal = document.getElementById('importValidationModal');
        if (validationModal) {
            validationModal.classList.remove('show');
            setTimeout(() => {
                validationModal.style.display = 'none';
            }, 300); // Match CSS transition duration
        }

        // Clear preview data
        state.importPreviewData = null;
    }

    /**
     * Process import rows
     */
    async function processImportRows(validRecords) {
        console.log(`[ImportExportModule] Processing ${validRecords.length} import rows`);

        state.isImporting = true;
        state.importProgress = 0;

        const results = {
            successCount: 0,
            failCount: 0,
            errors: []
        };

        try {
            // Show progress message
            if (window.ServicesModule) {
                window.ServicesModule.showMessage('Importing assignments...', 'info');
            }

            // Process in batches
            for (let i = 0; i < validRecords.length; i += CONFIG.batchSize) {
                const batch = validRecords.slice(i, Math.min(i + CONFIG.batchSize, validRecords.length));

                for (const record of batch) {
                    try {
                        // ENHANCEMENT: Handle multiple entity IDs from comma-separated entities
                        const entityIds = record.data.entity_ids || [record.data.entity_id];

                        // Create one assignment per entity ID
                        for (const entityId of entityIds) {
                            const assignmentData = {
                                ...record.data,
                                entity_id: entityId
                            };

                            // Create assignment using VersioningModule
                            await window.VersioningModule.createAssignmentVersion(assignmentData, {
                                reason: 'Imported from CSV'
                            });

                            results.successCount++;
                        }
                    } catch (error) {
                        console.error('[ImportExportModule] Error importing row:', record.rowNumber, error);
                        results.failCount++;
                        results.errors.push({
                            row: record.rowNumber,
                            error: error.message
                        });
                    }

                    // Update progress
                    state.importProgress = Math.floor(((i + batch.indexOf(record) + 1) / validRecords.length) * 100);

                    if ((i + batch.indexOf(record) + 1) % CONFIG.progressInterval === 0) {
                        console.log(`[ImportExportModule] Import progress: ${state.importProgress}%`);
                    }
                }
            }

            // Emit completion event
            if (window.AppEvents) {
                window.AppEvents.emit('import-completed', results);
            }

            // Show results
            if (window.ServicesModule) {
                window.ServicesModule.showMessage(
                    `Import complete: ${results.successCount} succeeded, ${results.failCount} failed`,
                    results.failCount === 0 ? 'success' : 'warning'
                );
            }

            console.log('[ImportExportModule] Import complete:', results);

        } catch (error) {
            console.error('[ImportExportModule] Import processing error:', error);
            if (window.ServicesModule) {
                window.ServicesModule.showMessage('Import failed: ' + error.message, 'error');
            }
        } finally {
            state.isImporting = false;
            state.importProgress = 0;
        }
    }

    /**
     * Fetch assignments for export
     */
    async function fetchAssignmentsForExport() {
        console.log('[ImportExportModule] Fetching assignments for export');

        try {
            const response = await window.ServicesModule.apiCall(
                '/api/assignments/export'
            );

            return response.assignments || [];

        } catch (error) {
            console.error('[ImportExportModule] Error fetching assignments:', error);
            throw error;
        }
    }

    /**
     * Generate CSV content from assignments
     */
    function generateExportCSV(assignments) {
        console.log('[ImportExportModule] Generating CSV for export');

        // Define headers - removed: Entity ID, Start Date, End Date, Required, Status, Version
        const headers = [
            'Field ID',
            'Field Name',
            'Entity Name',
            'Frequency',
            'Unit Override',
            'Topic',
            'Notes'
        ];

        // Build rows - matching removed columns
        const rows = assignments.map(assignment => [
            assignment.field_id || '',
            assignment.field_name || '',
            assignment.entity_name || '',
            assignment.frequency || '',
            assignment.unit || '',
            assignment.topic_name || '',
            assignment.notes || ''
        ]);

        // Convert to CSV
        const csvLines = [headers, ...rows].map(row =>
            row.map(value => formatCSVValue(value)).join(',')
        );

        return csvLines.join('\n');
    }

    /**
     * Format value for CSV (handle quotes and commas)
     */
    function formatCSVValue(value) {
        if (value === null || value === undefined) {
            return '';
        }

        const stringValue = String(value);

        // If contains comma, quote, or newline, wrap in quotes and escape internal quotes
        if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
            return '"' + stringValue.replace(/"/g, '""') + '"';
        }

        return stringValue;
    }

    /**
     * Download CSV file
     */
    function downloadCSV(csvContent, filename) {
        console.log('[ImportExportModule] Downloading CSV file:', filename);

        // Create blob
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });

        // Create download link
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Clean up
        URL.revokeObjectURL(url);
    }

    /**
     * Download assignment template
     */
    async function downloadAssignmentTemplate() {
        console.log('[ImportExportModule] Downloading assignment template');

        try {
            const csvContent = generateTemplateCSV();
            const filename = 'assignment_import_template.csv';

            downloadCSV(csvContent, filename);

            if (window.ServicesModule) {
                window.ServicesModule.showMessage('Template downloaded successfully', 'success');
            }

        } catch (error) {
            console.error('[ImportExportModule] Error downloading template:', error);
            if (window.ServicesModule) {
                window.ServicesModule.showMessage('Failed to download template', 'error');
            }
        }
    }

    /**
     * Generate template CSV with sample data
     * BUG FIX: Updated to match export format (Entity Name only, no Entity ID)
     */
    function generateTemplateCSV() {
        const headers = [
            'Field ID',
            'Field Name',
            'Entity Name',
            'Frequency',
            'Unit Override',
            'Topic',
            'Notes'
        ];

        const sampleRows = [
            [
                'GRI-302-1',
                'Energy Consumption',
                'Headquarters',
                'Monthly',
                'kWh',
                'Energy',
                'Main facility tracking'
            ],
            [
                'TCFD-1-A',
                'Climate Risk Assessment',
                'Manufacturing Plant',
                'Quarterly',
                '',
                'Climate Change',
                'Optional reporting'
            ]
        ];

        const csvLines = [headers, ...sampleRows].map(row =>
            row.map(value => formatCSVValue(value)).join(',')
        );

        return csvLines.join('\n');
    }

    // ===========================
    // Public API
    // ===========================

    window.ImportExportModule = {
        // Initialization
        init,

        // Import
        handleImportFile,
        parseCSVFile,
        validateImportData,
        processImportRows,

        // Export
        generateExportCSV,
        downloadCSV,
        fetchAssignmentsForExport,

        // Template
        downloadAssignmentTemplate,

        // Utilities
        parseCSVLine,
        formatCSVValue,
        validateRow,

        // For testing/debugging
        _state: state,
        _config: CONFIG
    };

    console.log('[ImportExportModule] Module loaded');

})();