import { PopupManager } from '../common/popup.js';

export function initializeDashboard(PopupManager) {
    // Initialize tabs
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // Update active states for buttons
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Update active states for content
            tabContents.forEach(content => {
                content.classList.remove('active');
                content.style.display = 'none';
            });
            
            // Show selected tab
            const activeTab = document.getElementById(tabId + 'Tab');
            if (activeTab) {
                activeTab.classList.add('active');
                activeTab.style.display = 'block';
                
                if (tabId === 'history') {
                    loadHistoricalData();
                }
            }
        });
    });

    // Fix date selection handling
    const dateForm = document.getElementById('dateForm');
    const dateSelect = document.getElementById('dateSelect');
    
    if (dateSelect) {
        dateSelect.addEventListener('change', function() {
            window.location.href = `/user/dashboard?date=${this.value}`;
        });
    }

    // Fix month navigation
    const prevMonth = document.getElementById('prevMonth');
    const nextMonth = document.getElementById('nextMonth');

    if (prevMonth && nextMonth && dateSelect) {
        prevMonth.addEventListener('click', () => {
            const date = new Date(dateSelect.value + '-01');
            date.setMonth(date.getMonth() - 1);
            const newDate = date.toISOString().slice(0, 7);
            window.location.href = `/user/dashboard?date=${newDate}`;
        });

        nextMonth.addEventListener('click', () => {
            const date = new Date(dateSelect.value + '-01');
            date.setMonth(date.getMonth() + 1);
            const newDate = date.toISOString().slice(0, 7);
            window.location.href = `/user/dashboard?date=${newDate}`;
        });
    }

    // Initialize tabs
    const entryTab = document.getElementById('entryTab');
    const historyTab = document.getElementById('historyTab');
    
    if (entryTab) {
        entryTab.classList.add('active');
        entryTab.style.display = 'block';
    }
    
    if (historyTab) {
        historyTab.style.display = 'none';
    }

    // Form submission handling
    const form = document.getElementById('dataEntryForm');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!confirm('Are you sure you want to save these changes?')) {
                return;
            }

            try {
                const submitButton = this.querySelector('button[type="submit"]');
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

                const response = await fetch(this.action, {
                    method: 'POST',
                    body: new FormData(this)
                });

                // Handle JSON response
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    // If the response is JSON, handle it accordingly
                    const data = await response.json();
                    if (data.success) {
                        PopupManager.showSuccess('Success', data.message || 'Data saved successfully');
                        if (data.redirect) {
                            window.location.href = data.redirect;
                        }
                    } else {
                        PopupManager.showError('Error', data.error || 'Failed to save data');
                    }
                } else if (response.redirected) {
                    // Handle redirect with success message
                    PopupManager.showSuccess('Success', 'Data saved successfully');
                    window.location.href = response.url;
                } else {
                    PopupManager.showError('Error', 'Unexpected response from server');
                }
            } catch (error) {
                console.error('Error:', error);
                PopupManager.showError('Error', 'An error occurred while saving the data. Please try again.');
            } finally {
                submitButton.disabled = false;
                submitButton.innerHTML = 'Save Data';
            }
        });
    }

    // Initialize date pickers for history tab
    const today = new Date();
    const yearMonth = today.toISOString().slice(0, 7);
    
    const historyEndDate = document.getElementById('historyEndDate');
    const historyStartDate = document.getElementById('historyStartDate');
    
    if (historyEndDate) {
        historyEndDate.value = yearMonth;
    }
    
    if (historyStartDate) {
        const startDate = new Date(today.getFullYear(), today.getMonth() - 11);
        historyStartDate.value = startDate.toISOString().slice(0, 7);
    }

    // Add file upload handling
    document.querySelectorAll('.file-input').forEach(input => {
        input.addEventListener('change', async function(e) {
            const files = Array.from(this.files);
            const cell = this.closest('.attachment-cell');
            const dataId = cell.dataset.id;
            
            for (const file of files) {
                try {
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('data_id', dataId);
                    
                    const response = await fetch('/user/upload_attachment', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        updateAttachmentsList(cell, dataId);
                        PopupManager.showSuccess('Upload Success', `File ${file.name} uploaded successfully`);
                    } else {
                        PopupManager.showError('Upload Error', `Error uploading ${file.name}: ${result.error}`);
                    }
                } catch (error) {
                    console.error('Upload error:', error);
                    PopupManager.showError('Upload Error', `Error uploading ${file.name}`);
                }
            }
            
            // Clear input
            this.value = '';
        });
    });

    initializeDateNavigation();
    initializeFormValidation();

    async function loadHistoricalData() {
        const dataPointId = document.getElementById('historyDataPoint')?.value || '';
        const startDate = document.getElementById('historyStartDate')?.value || '';
        const endDate = document.getElementById('historyEndDate')?.value || '';
        
        const historyDiv = document.getElementById('historyData');
        if (!historyDiv) return;
        
        historyDiv.innerHTML = '<p>Loading historical data...</p>';
        
        try {
            // Log the URL we're fetching
            const url = `/user/api/historical-data?dataPoint=${dataPointId}&start=${startDate}&end=${endDate}`;
            console.log('Fetching from:', url);
            
            const response = await fetch(url);
            
            // Log the raw response
            const rawText = await response.text();
            console.log('Raw response:', rawText);
            
            // Try to parse as JSON
            let result;
            try {
                result = JSON.parse(rawText);
            } catch (e) {
                throw new Error(`Invalid JSON response: ${rawText.substring(0, 100)}...`);
            }
            
            if (!result.success) {
                throw new Error(result.error || 'Failed to load historical data');
            }
            
            if (result.data.length === 0) {
                historyDiv.innerHTML = '<p class="no-data-message">No historical data found for the selected criteria.</p>';
                return;
            }
            
            // Create table to display data
            const table = document.createElement('table');
            table.className = 'data-table';
            
            // Add headers
            const thead = document.createElement('thead');
            thead.innerHTML = `
                <tr>
                    <th>Date</th>
                    <th>Data Point</th>
                    <th>Raw Value</th>
                    <th>Calculated Value</th>
                    <th>Last Updated</th>
                </tr>
            `;
            table.appendChild(thead);
            
            // Add data rows
            const tbody = document.createElement('tbody');
            result.data.forEach(entry => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${new Date(entry.reporting_date).toLocaleDateString()}</td>
                    <td>${entry.data_point_name}</td>
                    <td>${entry.raw_value || '-'}</td>
                    <td>${entry.calculated_value || '-'}</td>
                    <td>${new Date(entry.updated_at).toLocaleString()}</td>
                `;
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);
            
            // Clear and update the history div
            historyDiv.innerHTML = '';
            historyDiv.appendChild(table);
            
        } catch (error) {
            console.error('Error loading historical data:', error);
            historyDiv.innerHTML = `
                <div class="alert alert-danger">
                    Error loading historical data: ${error.message}
                </div>
            `;
        }
    }

    // Add event listeners for filter changes
    document.getElementById('historyDataPoint')?.addEventListener('change', loadHistoricalData);
    document.getElementById('historyStartDate')?.addEventListener('change', loadHistoricalData);
    document.getElementById('historyEndDate')?.addEventListener('change', loadHistoricalData);

    async function updateAttachmentsList(cell, dataId) {
        try {
            const response = await fetch(`/user/attachments/${dataId}`);
            const result = await response.json();
            
            if (result.success) {
                const list = cell.querySelector('.attachment-list');
                list.innerHTML = result.attachments.map(att => `
                    <div class="attachment-item">
                        <i class="fas fa-file"></i>
                        <span>${att.filename}</span>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Error fetching attachments:', error);
        }
    }

    // Initialize attachment lists
    document.querySelectorAll('.attachment-cell').forEach(cell => {
        updateAttachmentsList(cell, cell.dataset.id);
    });

    // Enhanced date navigation
    function initializeDateNavigation() {
        const dateSelect = document.getElementById('dateSelect');
        const prevMonth = document.getElementById('prevMonth');
        const nextMonth = document.getElementById('nextMonth');

        function updateDate(offset) {
            const currentDate = new Date(dateSelect.value + '-01');
            currentDate.setMonth(currentDate.getMonth() + offset);
            dateSelect.value = currentDate.toISOString().slice(0, 7);
            document.getElementById('dateForm').submit();
        }

        prevMonth?.addEventListener('click', () => updateDate(-1));
        nextMonth?.addEventListener('click', () => updateDate(1));

        // Add keyboard navigation for data entry
        const inputs = document.querySelectorAll('.data-input');
        inputs.forEach((input, index) => {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === 'ArrowDown') {
                    e.preventDefault();
                    const nextInput = inputs[index + 1];
                    if (nextInput) nextInput.focus();
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    const prevInput = inputs[index - 1];
                    if (prevInput) prevInput.focus();
                }
            });
        });
    }

    // Enhanced form validation
    function initializeFormValidation() {
        const form = document.getElementById('dataEntryForm');
        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Validate required fields
            let isValid = true;
            const requiredInputs = form.querySelectorAll('[required]');
            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            });

            if (!isValid) {
                alert('Please fill in all required fields');
                return;
            }

            // Show confirmation dialog
            if (confirm('Are you sure you want to save these changes?')) {
                form.submit();
            }
        });
    }

    // Update the expand button event listener
    document.querySelectorAll('.expand-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Prevent the event from bubbling up to the form
            e.preventDefault();
            e.stopPropagation();
            
            const computedRow = this.closest('.computed-field-row');
            const computedFieldId = computedRow.querySelector('.data-point-name').dataset.fieldId;
            
            // Toggle button state
            this.classList.toggle('expanded');
            const isExpanded = this.classList.contains('expanded');
            
            // Update icon rotation
            const icon = this.querySelector('i');
            if (icon) {
                icon.style.transform = isExpanded ? 'rotate(90deg)' : 'rotate(0)';
            }
            
            // Toggle dependency rows
            const dependencyRows = document.querySelectorAll(`tr[data-parent="${computedFieldId}"]`);
            dependencyRows.forEach(row => {
                row.style.display = isExpanded ? 'table-row' : 'none';
            });
            
            return false; // Prevent form submission
        });
    });

    // Add real-time calculation for computed fields
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('data-input')) {
            const dependencyRow = e.target.closest('.dependency-row');
            if (dependencyRow) {
                const parentId = dependencyRow.dataset.parent;
                // After computing the value, update the display
                const computedValue = updateComputedValue(parentId);
                if (computedValue !== null) {
                    updateComputedValueDisplay(parentId, computedValue);
                }
            }
        }
    });

    function updateComputedValue(computedFieldId) {
        // This function would need to be implemented based on your computation logic
        // It should gather all dependency values and calculate the result
        // Then update the computed-value-display
    }

    // Add this function to update computed values display
    function updateComputedValueDisplay(fieldId, value) {
        const displayElement = document.querySelector(`.computed-value-display[data-field-id="${fieldId}"]`);
        if (displayElement) {
            if (value !== null && value !== undefined) {
                displayElement.textContent = Number(value).toFixed(2);
                PopupManager.showInfo('Success', 'Computed value updated');
            } else {
                displayElement.innerHTML = '<span class="text-muted">Pending calculation...</span>';
                PopupManager.showWarning('Notice', 'Waiting for all required values');
            }
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        // Table sorting
        const table = document.querySelector('.data-table');
        const headers = table.querySelectorAll('th.sortable');
        
        headers.forEach(header => {
            header.addEventListener('click', () => {
                const sortBy = header.dataset.sort;
                const isAsc = !header.classList.contains('sorted-asc');
                
                // Remove existing sort classes
                headers.forEach(h => {
                    h.classList.remove('sorted-asc', 'sorted-desc');
                });
                
                // Add new sort class
                header.classList.add(isAsc ? 'sorted-asc' : 'sorted-desc');
                
                // Sort the table
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));
                
                rows.sort((a, b) => {
                    const aVal = a.querySelector(`td[data-label="${sortBy}"]`).textContent;
                    const bVal = b.querySelector(`td[data-label="${sortBy}"]`).textContent;
                    return isAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                });
                
                rows.forEach(row => tbody.appendChild(row));
            });
        });
        
        // Input validation
        const numericInputs = document.querySelectorAll('.numeric-input');
        numericInputs.forEach(input => {
            input.addEventListener('input', function() {
                const value = this.value;
                const isValid = !isNaN(value) && value !== '';
                
                this.classList.toggle('invalid', !isValid);
                
                const validationMessage = this.parentElement.querySelector('.validation-message');
                if (!isValid) {
                    if (!validationMessage) {
                        const message = document.createElement('div');
                        message.className = 'validation-message';
                        message.textContent = 'Please enter a valid number';
                        this.parentElement.appendChild(message);
                    }
                } else if (validationMessage) {
                    validationMessage.remove();
                }
            });
        });
    });
}