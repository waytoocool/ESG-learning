/**
 * Enhanced User Dashboard Date Validation
 * Provides interactive date selection, data filtering, CSV upload, and progress tracking
 */

class EnhancedDateValidator {
    constructor() {
        this.assignmentConfigs = new Map();
        this.allValidDates = new Set();
        this.dateToDataPointsMap = new Map();
        this.allDataPoints = [];
        this.isFormBlocked = true; // Start blocked until date is selected
        this.selectedDate = null;
        this.currentDataPoints = []; // Currently displayed data points
        this.esgDataByDate = {};
        this.baseEntityDataEntries = {};
        this.init();
    }

    async init() {
        console.log('🚀 Initializing Enhanced Date Validator');
        
        // Load all data points from the page
        this.loadDataPointsFromPage();
        
        // Load assignment configurations using the new unified API
        await this.loadAllAssignmentConfigs();
        
        // Set up the enhanced UI
        this.setupEnhancedUI();
        
        // Set up CSV upload functionality
        this.setupCSVUpload();
        
        // Initially block the form until a date is selected
        this.blockForm();
    }

    loadDataPointsFromPage() {
        // Extract data points from the JSON script tag
        const dataScript = document.getElementById('dataPointsData');
        if (!dataScript) {
            console.error('❌ Could not find data points data');
            return;
        }
        
        try {
            const data = JSON.parse(dataScript.textContent);
            const { rawInputPoints, computedPoints, rawDependencies, entityDataEntries, esgDataByDate } = data;
            
            console.log('📊 Raw data from server:', {
                rawInputPoints: rawInputPoints.length,
                computedPoints: computedPoints.length,
                rawDependencies: Object.keys(rawDependencies).length,
                entityDataEntries: Object.keys(entityDataEntries).length,
                esgDataByDate: Object.keys(esgDataByDate).length
            });
            
            console.log('📊 ESG data by date:', esgDataByDate);
            
            // Store the complete ESG data by date for later use
            this.esgDataByDate = esgDataByDate;
            this.baseEntityDataEntries = entityDataEntries;
            
            this.loadDataPointsWithData(rawInputPoints, computedPoints, rawDependencies, entityDataEntries);
            
        } catch (error) {
            console.error('❌ Error parsing data points data:', error);
        }
    }

    loadDataPointsWithData(rawInputPoints, computedPoints, rawDependencies, entityDataEntries) {
        console.log('📊 Entity data entries:', entityDataEntries);
        
        this.allDataPoints = [];
        
        // Add raw input points
        rawInputPoints.forEach(dp => {
            const current_value = entityDataEntries[dp.id]?.raw_value || '';
            console.log(`📊 Raw input point ${dp.id} (${dp.name}): ${current_value}`);
            this.allDataPoints.push({
                ...dp,
                type: 'raw',
                current_value: current_value
            });
        });
        
        // Add shared dependencies
        Object.entries(rawDependencies).forEach(([fieldId, dep]) => {
            const current_value = entityDataEntries[fieldId]?.raw_value || '';
            console.log(`📊 Shared dependency ${fieldId} (${dep.data.name}): ${current_value}`);
            this.allDataPoints.push({
                ...dep.data,
                id: fieldId,
                type: 'shared',
                current_value: current_value
            });
        });
        
        // Add computed points
        computedPoints.forEach(dp => {
            const current_value = entityDataEntries[dp.id]?.calculated_value || 'Not calculated';
            console.log(`📊 Computed point ${dp.id} (${dp.name}): ${current_value}`);
            this.allDataPoints.push({
                ...dp,
                type: 'computed',
                current_value: current_value
            });
        });
        
        console.log(`📊 Loaded ${this.allDataPoints.length} data points from page`);
    }

    async loadAllAssignmentConfigs() {
        try {
            console.log('📊 Loading all assignment configurations');
            
            const response = await fetch('/user/api/assignment-configurations');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Populate assignment configs
            Object.entries(data.configurations).forEach(([dataPointId, config]) => {
                this.assignmentConfigs.set(dataPointId, config);
            });
            
            // Populate all valid dates
            data.all_valid_dates.forEach(date => {
                this.allValidDates.add(date);
            });
            
            // Populate date to data points mapping
            Object.entries(data.date_to_data_points).forEach(([date, dataPoints]) => {
                this.dateToDataPointsMap.set(date, dataPoints);
            });
            
            console.log(`✅ Loaded ${this.assignmentConfigs.size} assignment configurations`);
            console.log(`📅 Found ${this.allValidDates.size} unique valid dates`);
            
        } catch (error) {
            console.error('❌ Error loading assignment configurations:', error);
        }
    }

    setupEnhancedUI() {
        console.log('🎯 Setting up Enhanced UI');
        const showValidDatesBtn = document.getElementById('showValidDatesBtn');
        const csvUploadBtn = document.getElementById('csvUploadBtn');
        const downloadTemplateFromModal = document.getElementById('downloadTemplateFromModal');
        const form = document.getElementById('dataEntryForm');
        
        console.log('🔍 UI Elements found:', {
            showValidDatesBtn: !!showValidDatesBtn,
            csvUploadBtn: !!csvUploadBtn,
            downloadTemplateFromModal: !!downloadTemplateFromModal,
            form: !!form
        });
        
        // Show valid dates button
        if (showValidDatesBtn) {
            showValidDatesBtn.addEventListener('click', () => {
                console.log('🔘 Select Date button clicked');
                this.toggleValidDatesDisplay();
            });
            console.log('✅ Select Date button event listener attached');
        } else {
            console.error('❌ Select Date button not found');
        }

        // CSV upload button
        if (csvUploadBtn) {
            csvUploadBtn.addEventListener('click', () => {
                console.log('🔘 Upload CSV button clicked');
                this.openCSVUploadModal();
            });
            console.log('✅ Upload CSV button event listener attached');
        } else {
            console.error('❌ Upload CSV button not found');
        }

        // Download template from modal
        if (downloadTemplateFromModal) {
            downloadTemplateFromModal.addEventListener('click', () => {
                this.downloadCSVTemplate();
            });
        }

        // Enhanced form submission handler
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                if (this.isFormBlocked) {
                    // Show error using popup system
                    if (window.PopupManager) {
                        window.PopupManager.showError(
                            'Date Required', 
                            'Please select a valid reporting date before submitting data'
                        );
                    } else {
                        console.error('❌ Please select a valid reporting date before submitting data');
                    }
                    return false;
                }
                
                // Show confirmation dialog
                if (!confirm('Are you sure you want to save these changes?')) {
                    return false;
                }
                
                try {
                    const submitButton = form.querySelector('button[type="submit"]');
                    const originalText = submitButton.innerHTML;
                    
                    // Disable button and show loading state
                    submitButton.disabled = true;
                    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

                    const response = await fetch(form.action, {
                        method: 'POST',
                        body: new FormData(form)
                    });

                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        // Handle JSON response
                        const data = await response.json();
                        if (data.success) {
                            // Show success message
                            this.showToast(data.message || 'Data saved successfully');
                            
                            // Redirect if provided
                            if (data.redirect) {
                                setTimeout(() => {
                                    window.location.href = data.redirect;
                                }, 1500);
                            } else {
                                // Refresh current data
                                const refreshed = await this.refreshDataFromServer();
                                if (refreshed && this.selectedDate) {
                                    this.filterAndDisplayDataPoints(this.selectedDate);
                                    this.updateProgress();
                                }
                            }
                        } else {
                            // Show error message using popup system
                            if (window.PopupManager) {
                                window.PopupManager.showError(
                                    'Save Failed', 
                                    data.error || 'Failed to save data'
                                );
                            } else {
                                console.error('❌ Failed to save data:', data.error);
                            }
                        }
                    } else if (response.redirected) {
                        // Handle redirect response
                        this.showToast('Data saved successfully');
                        setTimeout(() => {
                            window.location.href = response.url;
                        }, 1500);
                    } else {
                        // Show error using popup system
                        if (window.PopupManager) {
                            window.PopupManager.showError(
                                'Server Error', 
                                'Unexpected response from server'
                            );
                        } else {
                            console.error('❌ Unexpected response from server');
                        }
                    }
                } catch (error) {
                    console.error('Error submitting form:', error);
                    // Show error using popup system
                    if (window.PopupManager) {
                        window.PopupManager.showError(
                            'Network Error', 
                            'An error occurred while saving the data. Please try again.'
                        );
                    } else {
                        console.error('❌ An error occurred while saving the data. Please try again.');
                    }
                } finally {
                    // Re-enable button
                    const submitButton = form.querySelector('button[type="submit"]');
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.innerHTML = '<i class="fas fa-save"></i> Save Data';
                    }
                }
            });
        }

        // Initial display of valid dates
        this.displayValidDates();
        
        // Setup progress tracking
        this.setupProgressTracking();
    }

    setupProgressTracking() {
        // Listen for input changes to update progress
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('data-input')) {
                this.updateProgress();
            }
        });
        
        // Listen for form changes
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('data-input')) {
                this.updateProgress();
            }
        });
    }

    updateProgress() {
        if (!this.currentDataPoints.length) return;
        
        const progressSection = document.getElementById('progressSection');
        const progressText = document.getElementById('progressText');
        const progressPercentage = document.getElementById('progressPercentage');
        const progressBar = document.getElementById('progressBar');
        const completionIndicators = document.getElementById('completionIndicators');
        
        // Count completed data points (non-computed with values)
        const editableDataPoints = this.currentDataPoints.filter(dp => dp.type !== 'computed');
        let completedCount = 0;
        
        const indicators = [];
        
        editableDataPoints.forEach(dp => {
            // Fix: Use the correct field naming convention after DataPoint model refactoring
            const input = document.querySelector(`input[name="field_${dp.id}"]`);
            const isCompleted = input && input.value && input.value.trim() !== '';
            
            if (isCompleted) {
                completedCount++;
            }
            
            indicators.push({
                completed: isCompleted,
                name: dp.name
            });
        });
        
        const totalCount = editableDataPoints.length;
        const percentage = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;
        
        // Update progress display
        if (progressText) {
            progressText.textContent = `${completedCount} of ${totalCount} data points completed`;
        }
        
        if (progressPercentage) {
            progressPercentage.textContent = `${percentage}%`;
        }
        
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
            progressBar.setAttribute('aria-valuenow', percentage);
        }
        
        // Update completion indicators
        if (completionIndicators) {
            completionIndicators.innerHTML = indicators.map(indicator => `
                <div class="completion-indicator ${indicator.completed ? 'completed' : 'pending'}" 
                     title="${indicator.name}: ${indicator.completed ? 'Completed' : 'Pending'}">
                </div>
            `).join('');
        }
        
        // Show/hide progress section
        if (progressSection) {
            progressSection.style.display = totalCount > 0 ? 'block' : 'none';
        }
    }

    displayValidDates() {
        const validDatesList = document.getElementById('validDatesList');
        if (!validDatesList) return;

        const sortedDates = Array.from(this.allValidDates).sort();

        validDatesList.innerHTML = sortedDates.map(date => `
            <button type="button" 
                    class="date-chip"
                    data-date="${date}">
                ${this.formatDateShort(date)}
                <small>(${this.dateToDataPointsMap.get(date)?.length || 0} points)</small>
            </button>
        `).join('');

        // Add click handlers to the newly created buttons
        validDatesList.querySelectorAll('.date-chip').forEach(chip => {
            chip.addEventListener('click', (e) => {
                const date = e.currentTarget.dataset.date;
                this.selectValidDate(date);
            });
        });
    }

    selectValidDate(date) {
        this.selectedDate = date;
        
        // Update visual selection
        document.querySelectorAll('.date-chip').forEach(chip => {
            chip.classList.remove('selected');
            if (chip.dataset.date === date) {
                chip.classList.add('selected');
            }
        });

        // Update form date
        this.syncFormDate(date);
        
        // Show success notification using popup system
        if (window.PopupManager) {
            window.PopupManager.showSuccess(
                'Date Selected', 
                `Selected reporting date: ${this.formatDate(date)}`
            );
        } else {
            console.log(`✅ Selected date: ${this.formatDate(date)}`);
        }
        
        // Update selected date info
        this.updateSelectedDateInfo(date);
        
        // Show data points due
        this.showDataPointsDue(date);
        
        // Filter and display data points for this date
        this.filterAndDisplayDataPoints(date);
        
        // Enable form
        this.enableForm();
        
        // Hide date selection if visible
        const dateSelectionRow = document.getElementById('dateSelectionRow');
        if (dateSelectionRow && dateSelectionRow.style.display !== 'none') {
            this.toggleValidDatesDisplay();
        }
        
        // Update progress after data points are loaded
        setTimeout(() => this.updateProgress(), 100);
        
        // MANUAL TRIGGER: Ensure computed fields are updated
        setTimeout(() => {
            console.log(`🔄 Manual trigger for computed fields after date selection: ${date}`);
            if (window.computedFieldsManager) {
                console.log('🧮 ComputedFieldsManager found, triggering dateChanged event');
                document.dispatchEvent(new CustomEvent('dateChanged', {
                    detail: { date: date }
                }));
            } else {
                console.warn('⚠️ ComputedFieldsManager not available for manual trigger');
                
                // Try again after a longer delay
                setTimeout(() => {
                    if (window.computedFieldsManager) {
                        console.log('🧮 ComputedFieldsManager found on retry, triggering dateChanged event');
                        document.dispatchEvent(new CustomEvent('dateChanged', {
                            detail: { date: date }
                        }));
                    } else {
                        console.error('❌ ComputedFieldsManager still not available after extended delay');
                    }
                }, 1000);
            }
        }, 300);
    }

    updateSelectedDateInfo(date) {
        const selectedDateInfo = document.getElementById('selectedDateInfo');
        const currentSelectedDate = document.getElementById('currentSelectedDate');
        
        if (selectedDateInfo && currentSelectedDate) {
            currentSelectedDate.textContent = this.formatDate(date);
            selectedDateInfo.style.display = 'block';
        }
    }

    filterAndDisplayDataPoints(date) {
        const dueDataPoints = this.dateToDataPointsMap.get(date) || [];
        const dueDataPointIds = new Set(dueDataPoints.map(dp => dp.id.toString()));
        
        // Get the ESG data entries for this specific date
        const dateKey = date; // date is already in YYYY-MM-DD format
        const entityDataForDate = this.esgDataByDate[dateKey] || {};
        
        console.log(`📋 Loading data for date ${date}:`, entityDataForDate);
        
        // Filter data points that are due for this date
        const filteredDataPoints = this.allDataPoints.filter(dp => 
            dueDataPointIds.has(dp.id.toString())
        );
        
        // Update current values with data for this specific date
        filteredDataPoints.forEach(dp => {
            if (dp.type === 'computed') {
                dp.current_value = entityDataForDate[dp.id]?.calculated_value || 'Not calculated';
            } else {
                dp.current_value = entityDataForDate[dp.id]?.raw_value || '';
            }
            console.log(`📋 Updated ${dp.name} (${dp.id}) with value: ${dp.current_value}`);
        });
        
        this.currentDataPoints = filteredDataPoints;
        
        console.log(`📋 Showing ${filteredDataPoints.length} data points due for ${date}`);
        
        // Populate the table
        this.populateDataPointsTable(filteredDataPoints);
    }

    populateDataPointsTable(dataPoints) {
        const tableBody = document.getElementById('dataPointsTableBody');
        if (!tableBody) {
            console.error('❌ Table body not found');
            return;
        }

        console.log(`📊 Populating table with ${dataPoints.length} data points:`, dataPoints);
        
        // Debug: Check for computed fields
        const computedFields = dataPoints.filter(dp => dp.type === 'computed');
        const rawFields = dataPoints.filter(dp => dp.type !== 'computed');
        console.log(`🧮 Found ${computedFields.length} computed fields and ${rawFields.length} raw fields`);
        
        if (computedFields.length > 0) {
            console.log('🧮 Computed fields details:', computedFields);
        }

        tableBody.innerHTML = dataPoints.map(dp => {
            console.log(`📋 Table row for ${dp.name}: value="${dp.current_value}", type="${dp.type}", is_computed="${dp.is_computed}"`);
            
            // Add computed-field-row class for computed fields
            const rowClass = dp.type === 'computed' ? 'computed-field-row' : '';
            
            return `
            <tr data-id="${dp.id}" class="${rowClass}">
                <td>
                    <span class="field-type-indicator ${dp.type}"></span>
                    <span class="data-point-name" data-field-id="${dp.id}">${dp.name}</span>
                    ${dp.type === 'computed' ? '<small class="text-muted d-block">Auto-calculated</small>' : ''}
                </td>
                <td>
                    ${dp.type === 'computed' ? 
                        '<span class="badge bg-secondary">Computed</span>' : 
                        `<span class="badge bg-primary">${dp.value_type}</span>`
                    }
                </td>
                <td>
                    ${this.getFrequencyBadge(dp)}
                </td>
                <td>
                    ${dp.type === 'computed' ? 
                        `<div class="computed-field-container">
                            <div class="computation-status not-calculated">
                                <i class="fas fa-calculator"></i>
                                <small class="status-text">Not calculated</small>
                                <button type="button" 
                                        class="btn btn-sm btn-outline-primary compute-on-demand-btn mt-1"
                                        data-field-id="${dp.id}">
                                    <i class="fas fa-play"></i> Compute
                                </button>
                            </div>
                        </div>` :
                        this.createUnitAwareInput(dp)
                    }
                </td>
                <td>
                    <div class="attachment-container" data-dp-id="${dp.id}">
                        <div class="attachment-list" id="attachments-${dp.id}">
                            <div class="loading-attachments">
                                <small class="text-muted">Loading...</small>
                            </div>
                        </div>
                        <button type="button" 
                                class="btn btn-outline-secondary btn-sm mt-1"
                                onclick="handleAttachmentClick('${dp.id}', '${dp.current_value ? 'has_data' : 'no_data'}')"
                                title="${dp.current_value ? 'Upload attachment' : 'Save data first to upload attachments'}">
                            <i class="fas fa-paperclip"></i> Add
                        </button>
                    </div>
                </td>
            </tr>
        `}).join('');
        
        // Load attachments for each data point
        dataPoints.forEach(dp => {
            this.loadAttachmentsForDataPoint(dp.id);
        });
        
        // Load unit options for unit-aware inputs
        this.loadUnitOptionsForInputs(dataPoints);
        
        // Setup unit conversion event handlers
        this.setupUnitConversionHandlers();
        
        // Apply compact mode if there are many data points
        this.applyCompactModeIfNeeded(dataPoints.length);
        
        // Trigger computed field updates if ComputedFieldsManager is available
        if (window.computedFieldsManager && this.selectedDate) {
            console.log(`🧮 Triggering computed field updates for date: ${this.selectedDate}`);
            setTimeout(() => {
                document.dispatchEvent(new CustomEvent('dateChanged', {
                    detail: { date: this.selectedDate }
                }));
            }, 100); // Small delay to ensure DOM is updated
        } else {
            console.warn('⚠️ ComputedFieldsManager not available or no selected date:', {
                hasManager: !!window.computedFieldsManager,
                selectedDate: this.selectedDate,
                managerType: typeof window.computedFieldsManager
            });
            
            // Try to trigger computed field updates after a delay
            if (this.selectedDate) {
                console.log('🔄 Retrying computed field updates after delay...');
                setTimeout(() => {
                    if (window.computedFieldsManager) {
                        console.log(`🧮 Delayed trigger for computed field updates: ${this.selectedDate}`);
                        document.dispatchEvent(new CustomEvent('dateChanged', {
                            detail: { date: this.selectedDate }
                        }));
                    } else {
                        console.error('❌ ComputedFieldsManager still not available after delay');
                    }
                }, 500);
            }
        }
        
        console.log('📋 Table populated successfully');
    }

    applyCompactModeIfNeeded(dataPointCount) {
        const table = document.getElementById('dataPointsTable');
        if (!table) return;
        
        // Apply compact mode if there are more than 6 data points for better production experience
        if (dataPointCount > 6) {
            table.classList.add('compact');
            console.log(`📊 Applied compact mode for ${dataPointCount} data points`);
        } else {
            table.classList.remove('compact');
        }
    }

    getFrequencyBadge(dataPoint) {
        // Get frequency from assignment config if available
        const config = this.assignmentConfigs.get(dataPoint.id.toString());
        let frequency = config?.frequency || dataPoint.frequency || 'Unknown';
        
        // Normalize frequency display
        frequency = frequency.charAt(0).toUpperCase() + frequency.slice(1).toLowerCase();
        
        return `<span class="frequency-badge frequency-${frequency.toLowerCase()}">${frequency}</span>`;
    }

    showDataPointsDue(date) {
        const dataPointsDueRow = document.getElementById('dataPointsDueRow');
        const selectedDateDisplay = document.getElementById('selectedDateDisplay');
        const dueList = document.getElementById('dueDataPointsList');
        
        if (!dataPointsDueRow || !dueList) return;

        const dueDataPoints = this.dateToDataPointsMap.get(date) || [];
        
        if (selectedDateDisplay) {
            selectedDateDisplay.textContent = this.formatDate(date);
        }
        
        if (dueDataPoints.length > 0) {
            dueList.innerHTML = dueDataPoints.map(dp => `
                <span class="due-point-badge frequency-${dp.frequency.toLowerCase()}">
                    ${dp.name} (${dp.frequency})
                </span>
            `).join('');
            
            dataPointsDueRow.style.display = 'block';
        } else {
            dataPointsDueRow.style.display = 'none';
        }
    }

    toggleValidDatesDisplay() {
        const dateSelectionRow = document.getElementById('dateSelectionRow');
        const btn = document.getElementById('showValidDatesBtn');
        
        if (dateSelectionRow) {
            const isVisible = dateSelectionRow.style.display !== 'none';
            dateSelectionRow.style.display = isVisible ? 'none' : 'block';
            
            if (btn) {
                btn.innerHTML = isVisible 
                    ? '<i class="fas fa-calendar-alt"></i> Select Date'
                    : '<i class="fas fa-times"></i> Close';
            }
        }
    }

    setupCSVUpload() {
        const csvUploadForm = document.getElementById('csvUploadForm');
        if (csvUploadForm) {
            csvUploadForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleCSVUpload();
            });
        }
    }

    openCSVUploadModal() {
        if (!this.selectedDate) {
            // Show warning using popup system
            if (window.PopupManager) {
                window.PopupManager.showWarning(
                    'Date Required', 
                    'Please select a reporting date first before uploading CSV data'
                );
            } else {
                console.warn('⚠️ Please select a reporting date first');
            }
            return;
        }

        const csvReportingDate = document.getElementById('csvReportingDate');
        if (csvReportingDate) {
            csvReportingDate.value = this.selectedDate;
        }

        const modal = new bootstrap.Modal(document.getElementById('csvUploadModal'));
        modal.show();
    }

    async handleCSVUpload() {
        const form = document.getElementById('csvUploadForm');
        const fileInput = document.getElementById('csvFileInput');
        const resultsDiv = document.getElementById('csvUploadResults');
        
        if (!fileInput.files[0]) {
            this.showCSVResults('Please select a CSV file', 'danger');
            return;
        }

        const formData = new FormData(form);
        
        try {
            resultsDiv.style.display = 'block';
            resultsDiv.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-spinner fa-spin"></i> Processing CSV file...
                    <div class="progress mt-2">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 100%"></div>
                    </div>
                </div>
            `;
            
            const response = await fetch('/user/upload-csv', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                let successMessage = `
                    <div class="alert alert-success">
                        <h6><i class="fas fa-check-circle"></i> Upload Successful!</h6>
                        <ul class="mb-0">
                            <li><strong>Total Records Processed:</strong> ${result.processed_count}</li>
                            <li><strong>Status:</strong> ${result.message}</li>
                        </ul>
                `;
                
                if (result.warnings && result.warnings.length > 0) {
                    successMessage += `
                        <hr>
                        <h6><i class="fas fa-exclamation-triangle text-warning"></i> Warnings:</h6>
                        <ul class="mb-0">
                            ${result.warnings.map(warning => `<li><small>${warning}</small></li>`).join('')}
                        </ul>
                    `;
                }
                
                successMessage += '</div>';
                this.showCSVResults(successMessage, 'html');
                
                // Refresh the data points display
                if (this.selectedDate) {
                    // Force reload the page data to show updated values
                    setTimeout(async () => {
                        // Refresh data from server to get updated values
                        const refreshed = await this.refreshDataFromServer();
                        
                        if (refreshed) {
                            // Re-filter and display for current date with fresh data
                            this.filterAndDisplayDataPoints(this.selectedDate);
                            
                            // Update progress
                            this.updateProgress();
                            
                            console.log('📊 Data refreshed after CSV upload');
                        } else {
                            // Fallback: reload assignment configurations
                            await this.loadAllAssignmentConfigs();
                            this.filterAndDisplayDataPoints(this.selectedDate);
                        }
                    }, 500);
                }
                
                // Close modal after a delay
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('csvUploadModal'));
                    if (modal) modal.hide();
                    
                    // Show success toast
                    this.showToast(`Successfully uploaded ${result.processed_count} records`);
                    
                    // Reset the form
                    const csvForm = document.getElementById('csvUploadForm');
                    if (csvForm) csvForm.reset();
                    
                    // Clear results
                    const resultsDiv = document.getElementById('csvUploadResults');
                    if (resultsDiv) resultsDiv.style.display = 'none';
                    
                }, 3000);
            } else {
                this.showCSVResults(`
                    <div class="alert alert-danger">
                        <h6><i class="fas fa-times-circle"></i> Upload Failed</h6>
                        <p><strong>Error:</strong> ${result.error}</p>
                        <small>Please check your CSV format and try again.</small>
                    </div>
                `, 'html');
            }
        } catch (error) {
            this.showCSVResults(`
                <div class="alert alert-danger">
                    <h6><i class="fas fa-exclamation-triangle"></i> Network Error</h6>
                    <p><strong>Error:</strong> ${error.message}</p>
                    <small>Please check your connection and try again.</small>
                </div>
            `, 'html');
        }
    }

    showCSVResults(message, type) {
        const resultsDiv = document.getElementById('csvUploadResults');
        if (resultsDiv) {
            resultsDiv.style.display = 'block';
            if (type === 'html') {
                resultsDiv.innerHTML = message;
            } else {
                resultsDiv.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
            }
        }
    }

    showToast(message, type = 'success') {
        // Use the enhanced popup system
        if (window.PopupManager) {
            window.PopupManager.toast(message, type);
        } else {
            // Fallback to console if PopupManager is not available
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    blockForm() {
        this.isFormBlocked = true;
        const formBlocker = document.getElementById('formBlocker');
        const dataTableContainer = document.getElementById('dataTableContainer');
        const submitBtn = document.getElementById('submitBtn');
        
        if (formBlocker) formBlocker.style.display = 'block';
        if (dataTableContainer) dataTableContainer.classList.add('form-blocked');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-ban"></i> Select Date First';
        }
    }

    enableForm() {
        this.isFormBlocked = false;
        const formBlocker = document.getElementById('formBlocker');
        const dataTableContainer = document.getElementById('dataTableContainer');
        const submitBtn = document.getElementById('submitBtn');
        
        if (formBlocker) formBlocker.style.display = 'none';
        if (dataTableContainer) dataTableContainer.classList.remove('form-blocked');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save"></i> Save Data';
        }
    }

    syncFormDate(date) {
        const formReportingDate = document.getElementById('formReportingDate');
        if (formReportingDate) {
            formReportingDate.value = date;
        }
    }

    showValidationMessage(message, type) {
        const validationArea = document.getElementById('dateValidationArea');
        if (!validationArea) return;

        const alertClass = type === 'success' ? 'alert-success' : 
                          type === 'warning' ? 'alert-warning' : 'alert-danger';
        
        const icon = type === 'success' ? 'fa-check-circle' : 
                    type === 'warning' ? 'fa-exclamation-triangle' : 'fa-times-circle';

        validationArea.innerHTML = `
            <div class="alert ${alertClass}">
                <i class="fas ${icon}"></i> ${message}
            </div>
        `;
        
        // Auto-hide success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                if (validationArea.innerHTML.includes(message)) {
                    validationArea.innerHTML = '';
                }
            }, 5000);
        }
    }

    formatDate(dateStr) {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        } catch (error) {
            return dateStr;
        }
    }

    formatDateShort(dateStr) {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric'
            });
        } catch (error) {
            return dateStr;
        }
    }

    downloadCSVTemplate() {
        if (!this.selectedDate) {
            // Show warning using popup system
            if (window.PopupManager) {
                window.PopupManager.showWarning(
                    'Date Required', 
                    'Please select a reporting date first to download template'
                );
            } else {
                console.warn('⚠️ Please select a reporting date first to download template');
            }
            return;
        }

        const dueDataPoints = this.dateToDataPointsMap.get(this.selectedDate) || [];
        
        if (dueDataPoints.length === 0) {
            // Show info message using popup system
            if (window.PopupManager) {
                window.PopupManager.showInfo(
                    'No Data Points', 
                    'No data points are due for the selected date'
                );
            } else {
                console.info('ℹ️ No data points are due for the selected date');
            }
            return;
        }

        // Create CSV content with Excel-friendly formatting and frequency column
        // Add BOM for proper Unicode support in Excel
        let csvContent = '\uFEFF';
        csvContent += 'Reporting Date,Data Point Name,Frequency,Value\n';
        
        dueDataPoints.forEach(dp => {
            // Get frequency from assignment config
            const config = this.assignmentConfigs.get(dp.id.toString());
            const frequency = config?.frequency || dp.frequency || 'Unknown';
            
            // Use quoted format which is more universally compatible
            // This preserves the YYYY-MM-DD format in Excel
            csvContent += `"${this.selectedDate}","${dp.name}","${frequency}",""\n`;
        });

        // Create and download file with proper CSV MIME type
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `data_entry_template_${this.selectedDate}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showToast(`Template downloaded for ${this.formatDate(this.selectedDate)}`);
        } else {
            // Show error using popup system
            if (window.PopupManager) {
                window.PopupManager.showError(
                    'Download Failed', 
                    'Download not supported in this browser'
                );
            } else {
                console.error('❌ Download not supported in this browser');
            }
        }
    }

    async refreshDataFromServer() {
        try {
            // Get fresh data from the server
            const response = await fetch(window.location.href);
            if (!response.ok) {
                throw new Error('Failed to refresh data');
            }
            
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Extract the fresh data points data
            const freshDataScript = doc.getElementById('dataPointsData');
            if (freshDataScript) {
                const freshData = JSON.parse(freshDataScript.textContent);
                
                // Update our local data with fresh server data
                const { rawInputPoints, computedPoints, rawDependencies, entityDataEntries } = freshData;
                
                this.allDataPoints = [];
                
                // Add raw input points with fresh values
                rawInputPoints.forEach(dp => {
                    this.allDataPoints.push({
                        ...dp,
                        type: 'raw',
                        current_value: entityDataEntries[dp.id]?.raw_value || ''
                    });
                });
                
                // Add shared dependencies with fresh values
                Object.entries(rawDependencies).forEach(([fieldId, dep]) => {
                    this.allDataPoints.push({
                        ...dep.data,
                        id: fieldId,
                        type: 'shared',
                        current_value: entityDataEntries[fieldId]?.raw_value || ''
                    });
                });
                
                // Add computed points with fresh values
                computedPoints.forEach(dp => {
                    this.allDataPoints.push({
                        ...dp,
                        type: 'computed',
                        current_value: entityDataEntries[dp.id]?.calculated_value || 'Not calculated'
                    });
                });
                
                console.log(`🔄 Refreshed ${this.allDataPoints.length} data points from server`);
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Error refreshing data from server:', error);
            return false;
        }
    }

    async loadAttachmentsForDataPoint(dataPointId) {
        try {
            // First, we need to get the ESGData ID for this data point and current date
            // Since attachments are linked to ESGData entries, not data points directly
            const response = await fetch(`/user/api/data-point-attachments/${dataPointId}?date=${this.selectedDate}`);
            
            if (!response.ok) {
                throw new Error('Failed to fetch attachments');
            }
            
            const result = await response.json();
            this.displayAttachments(dataPointId, result.attachments || []);
            
        } catch (error) {
            console.error(`Error loading attachments for data point ${dataPointId}:`, error);
            this.displayAttachments(dataPointId, []);
        }
    }

    displayAttachments(dataPointId, attachments) {
        const attachmentsList = document.getElementById(`attachments-${dataPointId}`);
        if (!attachmentsList) return;

        if (attachments.length === 0) {
            attachmentsList.innerHTML = '<small class="text-muted">No attachments</small>';
            return;
        }

        attachmentsList.innerHTML = attachments.map(attachment => `
            <div class="attachment-item d-flex align-items-center justify-content-between mb-1">
                <div class="attachment-info">
                    <small class="attachment-name" title="${attachment.filename}">
                        <i class="fas fa-file"></i> ${this.truncateFilename(attachment.filename)}
                    </small>
                    <br>
                    <small class="text-muted">${this.formatFileSize(attachment.file_size)}</small>
                </div>
                <div class="attachment-actions">
                    <button type="button" 
                            class="btn btn-outline-primary btn-xs" 
                            onclick="downloadAttachment('${attachment.id}')"
                            title="Download ${attachment.filename}">
                        <i class="fas fa-download"></i>
                    </button>
                    <button type="button" 
                            class="btn btn-outline-danger btn-xs ml-1" 
                            onclick="deleteAttachment('${attachment.id}', '${dataPointId}')"
                            title="Delete ${attachment.filename}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    truncateFilename(filename, maxLength = 20) {
        if (filename.length <= maxLength) return filename;
        const extension = filename.split('.').pop();
        const nameWithoutExt = filename.substring(0, filename.lastIndexOf('.'));
        const truncatedName = nameWithoutExt.substring(0, maxLength - extension.length - 4) + '...';
        return `${truncatedName}.${extension}`;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    async refreshAttachmentsForDataPoint(dataPointId) {
        await this.loadAttachmentsForDataPoint(dataPointId);
    }

    createUnitAwareInput(dataPoint) {
        const hasUnitCategory = dataPoint.unit_category && dataPoint.unit_category !== '';
        const hasDimensions = dataPoint.dimensions && dataPoint.dimensions.length > 0;

        // If the data point has dimensions, delegate to DimensionPickerManager for enhanced input
        if (hasDimensions && window.dimensionPickerManager && window.dimensionPickerManager.createEnhancedInput) {
            return window.dimensionPickerManager.createEnhancedInput(dataPoint);
        }

        if (!hasUnitCategory) {
            // Regular input for fields without unit categories or dimensions
            return `<input type="${dataPoint.value_type === 'numeric' ? 'number' : 'text'}"
                           class="data-input form-control"
                           name="field_${dataPoint.id}"
                           value="${dataPoint.current_value || ''}"
                           ${dataPoint.value_type === 'numeric' ? 'step="any"' : ''}
                           placeholder="Enter ${dataPoint.value_type} value">`;
        }
        
        // Unit-aware (but no dimensions) input for fields with unit categories
        const unitSelectId = `unit_${dataPoint.id}`;
        const inputId = `field_${dataPoint.id}`;
        
        const optionsMarkup = (dataPoint.unit_options && dataPoint.unit_options.length)
            ? dataPoint.unit_options.map(opt => `<option value="${opt.value}">${opt.label}</option>`).join('')
            : '<option value="">Loading...</option>';
        
        return `
            <div class="unit-aware-input-container" data-field-id="${dataPoint.id}">
                <div class="input-group">
                    <input type="${dataPoint.value_type === 'numeric' ? 'number' : 'text'}"
                           class="data-input form-control unit-aware-input"
                           name="field_${dataPoint.id}"
                           id="${inputId}"
                           value="${dataPoint.current_value || ''}"
                           ${dataPoint.value_type === 'numeric' ? 'step="any"' : ''}
                           placeholder="Enter ${dataPoint.value_type} value"
                           data-field-id="${dataPoint.id}"
                           data-unit-category="${dataPoint.unit_category}"
                           data-default-unit="${dataPoint.default_unit || ''}">
                    <select class="form-select unit-select" 
                            id="${unitSelectId}"
                            name="unit_${dataPoint.id}"
                            data-field-id="${dataPoint.id}"
                            style="max-width: 120px;">
                        ${optionsMarkup}
                    </select>
                    <button type="button" 
                            class="btn btn-outline-secondary btn-sm unit-converter-btn"
                            data-field-id="${dataPoint.id}"
                            data-unit-category="${dataPoint.unit_category}"
                            title="Convert units">
                        <i class="fas fa-exchange-alt"></i>
                    </button>
                </div>
                <small class="text-muted unit-info">
                    Default: ${dataPoint.default_unit || 'None'} | Category: ${dataPoint.unit_category}
                </small>
            </div>`;
    }

    async loadUnitOptionsForInputs(dataPoints) {
        const fieldsWithUnits = dataPoints.filter(dp => dp.unit_category && dp.unit_category !== '');
        
        for (const dp of fieldsWithUnits) {
            const unitSelect = document.getElementById(`unit_${dp.id}`);
            if (unitSelect && unitSelect.options.length > 1) continue;
            
            try {
                const response = await fetch(`/admin/fields/${dp.id}/unit_options`);
                const data = await response.json();
                
                if (data.unit_options) {
                    this.populateUnitSelect(dp.id, data.unit_options, data.default_unit);
                }
            } catch (error) {
                console.error(`Error loading unit options for field ${dp.id}:`, error);
                this.setUnitSelectError(dp.id);
            }
        }
    }

    populateUnitSelect(fieldId, unitOptions, defaultUnit) {
        const unitSelect = document.getElementById(`unit_${fieldId}`);
        if (!unitSelect) return;

        unitSelect.innerHTML = '';
        
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = `Auto (${defaultUnit || 'default'})`;
        unitSelect.appendChild(defaultOption);
        
        unitOptions.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.value;
            optionElement.textContent = option.label;
            unitSelect.appendChild(optionElement);
        });
        
        if (defaultUnit) {
            unitSelect.value = defaultUnit;
        }
    }

    setUnitSelectError(fieldId) {
        const unitSelect = document.getElementById(`unit_${fieldId}`);
        if (!unitSelect) return;
        
        unitSelect.innerHTML = '<option value="">Units unavailable</option>';
        unitSelect.disabled = true;
    }

    setupUnitConversionHandlers() {
        document.addEventListener('click', (e) => {
            if (e.target.closest('.unit-converter-btn')) {
                const btn = e.target.closest('.unit-converter-btn');
                const fieldId = btn.dataset.fieldId;
                const unitCategory = btn.dataset.unitCategory;
                this.openUnitConverter(fieldId, unitCategory);
            }
        });

        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('unit-select')) {
                const fieldId = e.target.dataset.fieldId;
                const selectedUnit = e.target.value;
                this.handleUnitChange(fieldId, selectedUnit);
            }
        });
    }

    handleUnitChange(fieldId, selectedUnit) {
        const input = document.getElementById(`field_${fieldId}`);
        if (!input || !input.value) return;

        const currentValue = parseFloat(input.value);
        if (isNaN(currentValue)) return;

        if (!input.dataset.originalValue) {
            input.dataset.originalValue = currentValue;
            input.dataset.originalUnit = input.dataset.defaultUnit;
        }

        this.showUnitChangeNotification(fieldId, selectedUnit);
    }

    showUnitChangeNotification(fieldId, selectedUnit) {
        const container = document.querySelector(`[data-field-id="${fieldId}"] .unit-aware-input-container`);
        if (!container) return;

        const existingNotification = container.querySelector('.unit-change-notification');
        if (existingNotification) {
            existingNotification.remove();
        }

        if (selectedUnit) {
            const notification = document.createElement('div');
            notification.className = 'unit-change-notification alert alert-info alert-sm mt-1';
            notification.innerHTML = `
                <small>
                    <i class="fas fa-info-circle"></i>
                    Value will be stored in ${selectedUnit}
                </small>
            `;
            container.appendChild(notification);
        }
    }

    async openUnitConverter(fieldId, unitCategory) {
        try {
            const response = await fetch('/admin/unit_categories');
            const categories = await response.json();
            
            if (categories[unitCategory]) {
                this.showUnitConverterModal(fieldId, categories[unitCategory]);
            }
        } catch (error) {
            console.error('Error opening unit converter:', error);
        }
    }

    showUnitConverterModal(fieldId, categoryData) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'unitConverterModal';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Unit Converter - ${categoryData.name}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-5">
                                <label>From:</label>
                                <div class="input-group">
                                    <input type="number" class="form-control" id="convertFromValue" step="any">
                                    <select class="form-select" id="convertFromUnit">
                                        ${categoryData.units.map(unit => 
                                            `<option value="${unit.value}">${unit.label}</option>`
                                        ).join('')}
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-2 text-center">
                                <div class="mt-4">
                                    <i class="fas fa-arrow-right"></i>
                                </div>
                            </div>
                            <div class="col-md-5">
                                <label>To:</label>
                                <div class="input-group">
                                    <input type="number" class="form-control" id="convertToValue" readonly>
                                    <select class="form-select" id="convertToUnit">
                                        ${categoryData.units.map(unit => 
                                            `<option value="${unit.value}">${unit.label}</option>`
                                        ).join('')}
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="mt-3">
                            <button type="button" class="btn btn-primary" id="performConversion">
                                Convert
                            </button>
                            <button type="button" class="btn btn-success" id="useConvertedValue">
                                Use Converted Value
                            </button>
                        </div>
                        <div id="conversionResult" class="mt-3"></div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
        
        this.setupConverterModalHandlers(fieldId, modal, bootstrapModal);
        
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    setupConverterModalHandlers(fieldId, modal, bootstrapModal) {
        const performBtn = modal.querySelector('#performConversion');
        const useBtn = modal.querySelector('#useConvertedValue');
        const fromValue = modal.querySelector('#convertFromValue');
        const fromUnit = modal.querySelector('#convertFromUnit');
        const toValue = modal.querySelector('#convertToValue');
        const toUnit = modal.querySelector('#convertToUnit');
        const result = modal.querySelector('#conversionResult');
        
        performBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/admin/convert_unit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        value: parseFloat(fromValue.value),
                        from_unit: fromUnit.value,
                        to_unit: toUnit.value
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    toValue.value = data.converted_value;
                    result.innerHTML = `
                        <div class="alert alert-success">
                            ${fromValue.value} ${fromUnit.value} = ${data.converted_value} ${toUnit.value}
                        </div>
                    `;
                } else {
                    result.innerHTML = `
                        <div class="alert alert-danger">
                            Conversion failed: ${data.error || 'Unknown error'}
                        </div>
                    `;
                }
            } catch (error) {
                result.innerHTML = `
                    <div class="alert alert-danger">
                        Error: ${error.message}
                    </div>
                `;
            }
        });
        
        useBtn.addEventListener('click', () => {
            if (toValue.value) {
                const input = document.getElementById(`field_${fieldId}`);
                const unitSelect = document.getElementById(`unit_${fieldId}`);
                
                if (input) input.value = toValue.value;
                if (unitSelect) unitSelect.value = toUnit.value;
                
                bootstrapModal.hide();
            }
        });
    }
}

// Global function for attachment handling (called from template)
window.handleAttachmentClick = function(dataId, status) {
    const dataIdInput = document.getElementById('dataIdInput');
    const statusInput = document.getElementById('statusInput');
    
    if (dataIdInput && statusInput) {
        dataIdInput.value = dataId;
        statusInput.value = status;
    }
    
    // Check if data has been saved
    if (status === 'no_data') {
        if (window.PopupManager) {
            window.PopupManager.showWarning(
                'Save Data First',
                'Please enter a value for this data point and save the form before uploading attachments.'
            );
        } else {
            alert('Please enter a value for this data point and save the form before uploading attachments.');
        }
        return;
    }
    
    const modal = new bootstrap.Modal(document.getElementById('uploadModal'));
    modal.show();
};

// Add event listener for the upload button
document.addEventListener('DOMContentLoaded', () => {
    const uploadButton = document.getElementById('uploadButton');
    if (uploadButton) {
        uploadButton.addEventListener('click', async function() {
            const fileInput = document.getElementById('fileInput');
            const dataIdInput = document.getElementById('dataIdInput');
            const statusInput = document.getElementById('statusInput');
            
            if (!fileInput.files.length) {
                if (window.PopupManager) {
                    window.PopupManager.showWarning('No File Selected', 'Please select a file to upload.');
                } else {
                    alert('Please select a file to upload.');
                }
                return;
            }
            
            if (!dataIdInput.value) {
                if (window.PopupManager) {
                    window.PopupManager.showError('Error', 'Data ID is missing.');
                } else {
                    alert('Data ID is missing.');
                }
                return;
            }
            
            if (!statusInput.value) {
                if (window.PopupManager) {
                    window.PopupManager.showError('Error', 'Status is missing.');
                } else {
                    alert('Status is missing.');
                }
                return;
            }
            
            try {
                // Disable button during upload
                uploadButton.disabled = true;
                uploadButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                formData.append('data_id', dataIdInput.value);
                formData.append('status', statusInput.value);
                
                const response = await fetch('/user/upload_attachment', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    if (window.PopupManager) {
                        window.PopupManager.showSuccess('Upload Success', result.message || 'File uploaded successfully');
                    } else {
                        alert('File uploaded successfully');
                    }
                    
                    // Close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('uploadModal'));
                    if (modal) {
                        modal.hide();
                    }
                    
                    // Clear file input
                    fileInput.value = '';
                    
                    // Refresh attachments display for this data point
                    if (window.dashboard && window.dashboard.refreshAttachmentsForDataPoint) {
                        window.dashboard.refreshAttachmentsForDataPoint(dataIdInput.value);
                    }
                    
                } else {
                    if (window.PopupManager) {
                        window.PopupManager.showError('Upload Error', result.error || 'Failed to upload file');
                    } else {
                        alert('Error: ' + (result.error || 'Failed to upload file'));
                    }
                }
                
            } catch (error) {
                console.error('Upload error:', error);
                if (window.PopupManager) {
                    window.PopupManager.showError('Upload Error', 'An error occurred while uploading the file');
                } else {
                    alert('An error occurred while uploading the file');
                }
            } finally {
                // Re-enable button
                uploadButton.disabled = false;
                uploadButton.innerHTML = 'Upload';
            }
        });
    }
});

// Global functions for attachment management
window.downloadAttachment = function(attachmentId) {
    window.open(`/user/download-attachment/${attachmentId}`, '_blank');
};

window.deleteAttachment = async function(attachmentId, dataPointId) {
    if (!confirm('Are you sure you want to delete this attachment?')) {
        return;
    }
    
    try {
        const response = await fetch(`/user/delete-attachment/${attachmentId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            if (window.PopupManager) {
                window.PopupManager.showSuccess('Deleted', 'Attachment deleted successfully');
            } else {
                alert('Attachment deleted successfully');
            }
            
            // Refresh attachments for this data point
            if (window.dashboard && window.dashboard.refreshAttachmentsForDataPoint) {
                window.dashboard.refreshAttachmentsForDataPoint(dataPointId);
            }
        } else {
            if (window.PopupManager) {
                window.PopupManager.showError('Delete Failed', result.error || 'Failed to delete attachment');
            } else {
                alert('Error: ' + (result.error || 'Failed to delete attachment'));
            }
        }
    } catch (error) {
        console.error('Delete error:', error);
        if (window.PopupManager) {
            window.PopupManager.showError('Delete Error', 'An error occurred while deleting the attachment');
        } else {
            alert('An error occurred while deleting the attachment');
        }
    }
}; 