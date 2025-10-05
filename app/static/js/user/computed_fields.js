/**
 * Computed Fields Management Module
 * Handles on-demand computation and intelligent display of computed fields
 */

class ComputedFieldsManager {
    constructor() {
        this.computationCache = new Map();
        this.pendingComputations = new Set();
        this.initializeEventListeners();
        console.log('🧮 ComputedFieldsManager initialized');
    }

    initializeEventListeners() {
        // Listen for date changes to trigger computation checks
        document.addEventListener('dateChanged', (event) => {
            console.log('📅 Date changed event received:', event.detail.date);
            this.handleDateChange(event.detail.date);
        });

        // Listen for computed field display requests
        document.addEventListener('click', (event) => {
            if (event.target.classList.contains('compute-on-demand-btn')) {
                this.handleComputeRequest(event.target);
            }
        });

        // Use a more robust hover system for tooltips
        document.addEventListener('mouseenter', (event) => {
            const trigger = event.target.closest('.computed-info-trigger');
            if (trigger) {
                console.log('🖱️ Mouse enter on tooltip trigger:', trigger.dataset.tooltipId);
                this.handleTooltipShow(trigger);
                return;
            }
            
            const tooltip = event.target.closest('.computed-tooltip-portal');
            if (tooltip) {
                console.log('🖱️ Mouse enter on tooltip content:', tooltip.id);
                this.cancelTooltipHide(tooltip);
                return;
            }
        }, true);

        document.addEventListener('mouseleave', (event) => {
            const trigger = event.target.closest('.computed-info-trigger');
            if (trigger) {
                console.log('🖱️ Mouse leave on tooltip trigger:', trigger.dataset.tooltipId);
                // Small delay to allow moving to tooltip
                setTimeout(() => {
                    const tooltip = document.getElementById(`tooltip-${trigger.dataset.tooltipId}`);
                    if (tooltip && !this.isMouseOverTooltipArea(trigger, tooltip)) {
                        this.handleTooltipHide(trigger);
                    }
                }, 100);
                return;
            }
            
            const tooltip = event.target.closest('.computed-tooltip-portal');
            if (tooltip) {
                console.log('🖱️ Mouse leave on tooltip content:', tooltip.id);
                // Find the associated trigger
                const tooltipId = tooltip.id.replace('tooltip-', '');
                const trigger = document.querySelector(`[data-tooltip-id="${tooltipId}"]`);
                if (trigger && !this.isMouseOverTooltipArea(trigger, tooltip)) {
                    this.scheduleTooltipHide(tooltip);
                }
                return;
            }
        }, true);
    }

    // Helper method to check if mouse is over tooltip area (trigger + tooltip)
    isMouseOverTooltipArea(trigger, tooltip) {
        if (!trigger || !tooltip) return false;
        
        const triggerRect = trigger.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        // Get current mouse position
        const mouseX = event.clientX || 0;
        const mouseY = event.clientY || 0;
        
        // Add buffer zone for more forgiving hover detection
        const buffer = 5;
        
        // Check if mouse is over trigger (with buffer)
        const overTrigger = mouseX >= (triggerRect.left - buffer) && 
                           mouseX <= (triggerRect.right + buffer) &&
                           mouseY >= (triggerRect.top - buffer) && 
                           mouseY <= (triggerRect.bottom + buffer);
        
        // Check if mouse is over tooltip (with buffer)
        const overTooltip = mouseX >= (tooltipRect.left - buffer) && 
                           mouseX <= (tooltipRect.right + buffer) &&
                           mouseY >= (tooltipRect.top - buffer) && 
                           mouseY <= (tooltipRect.bottom + buffer);
        
        // Also check if mouse is in the gap between trigger and tooltip
        const inGap = this.isMouseInGap(triggerRect, tooltipRect, mouseX, mouseY);
        
        return overTrigger || overTooltip || inGap;
    }

    // Helper method to check if mouse is in the gap between trigger and tooltip
    isMouseInGap(triggerRect, tooltipRect, mouseX, mouseY) {
        // Check if mouse is in the vertical gap between trigger and tooltip
        const triggerCenterX = triggerRect.left + (triggerRect.width / 2);
        const tooltipCenterX = tooltipRect.left + (tooltipRect.width / 2);
        
        // Allow some horizontal tolerance
        const horizontalTolerance = 50;
        const leftBound = Math.min(triggerCenterX, tooltipCenterX) - horizontalTolerance;
        const rightBound = Math.max(triggerCenterX, tooltipCenterX) + horizontalTolerance;
        
        // Check if mouse is horizontally within the gap area
        const inHorizontalRange = mouseX >= leftBound && mouseX <= rightBound;
        
        // Check if mouse is vertically in the gap
        let inVerticalGap = false;
        if (tooltipRect.top > triggerRect.bottom) {
            // Tooltip is below trigger
            inVerticalGap = mouseY >= triggerRect.bottom && mouseY <= tooltipRect.top;
        } else if (triggerRect.top > tooltipRect.bottom) {
            // Tooltip is above trigger
            inVerticalGap = mouseY >= tooltipRect.bottom && mouseY <= triggerRect.top;
        }
        
        return inHorizontalRange && inVerticalGap;
    }

    // Helper method to cancel tooltip hide
    cancelTooltipHide(tooltip) {
        if (tooltip.cleanupTimeout) {
            clearTimeout(tooltip.cleanupTimeout);
            delete tooltip.cleanupTimeout;
            console.log('🔄 Cancelled tooltip hide:', tooltip.id);
        }
        // Ensure tooltip is visible
        tooltip.classList.add('show');
    }

    // Helper method to schedule tooltip hide
    scheduleTooltipHide(tooltip) {
        tooltip.classList.remove('show');
        tooltip.cleanupTimeout = setTimeout(() => {
            if (tooltip && tooltip.parentNode) {
                tooltip.parentNode.removeChild(tooltip);
                console.log(`🧹 Cleaned up tooltip: ${tooltip.id}`);
            }
        }, 300);
    }

    async handleDateChange(selectedDate) {
        try {
            console.log('🔍 Looking for computed field rows...');
            const computedFields = document.querySelectorAll('.computed-field-row');
            console.log(`📊 Found ${computedFields.length} computed field rows`);
            
            if (computedFields.length === 0) {
                console.warn('⚠️ No computed field rows found! Checking for alternative selectors...');
                
                // Try alternative selectors
                const alternativeRows = document.querySelectorAll('tr[data-id]');
                console.log(`🔍 Found ${alternativeRows.length} rows with data-id`);
                
                alternativeRows.forEach((row, index) => {
                    const badge = row.querySelector('.badge');
                    const isComputed = badge && badge.textContent.includes('Computed');
                    console.log(`Row ${index}: computed=${isComputed}, badge=${badge?.textContent}`);
                });
            }
            
            for (const fieldRow of computedFields) {
                const dataPointName = fieldRow.querySelector('.data-point-name');
                const valueDisplay = fieldRow.querySelector('.computed-value, .computed-field-container');
                
                console.log('🔍 Processing computed field row:', {
                    hasDataPointName: !!dataPointName,
                    hasValueDisplay: !!valueDisplay,
                    fieldId: dataPointName?.dataset?.fieldId,
                    rowHTML: fieldRow.outerHTML.substring(0, 200) + '...'
                });
                
                if (dataPointName && dataPointName.dataset && dataPointName.dataset.fieldId) {
                    const fieldId = dataPointName.dataset.fieldId;
                    
                    if (valueDisplay) {
                        console.log(`🧮 Updating computed field display for field ${fieldId}`);
                        await this.updateComputedFieldDisplay(fieldId, selectedDate, valueDisplay);
                    } else {
                        console.warn(`⚠️ No value display found for field ${fieldId}`);
                    }
                } else {
                    console.warn('⚠️ Missing field ID or data-point-name element:', {
                        dataPointName: !!dataPointName,
                        dataset: dataPointName?.dataset,
                        fieldId: dataPointName?.dataset?.fieldId
                    });
                }
            }
        } catch (error) {
            console.error('❌ Error handling date change:', error);
        }
    }

    async updateComputedFieldDisplay(fieldId, reportingDate, valueDisplay) {
        try {
            // Clear any existing computation status
            this.pendingComputations.delete(fieldId);
            
            // Set loading state
            this.displayComputedValue(valueDisplay, {
                status: 'loading',
                message: 'Checking computation eligibility...'
            });
            
            console.log(`🧮 Updating computed field ${fieldId} for date ${reportingDate}`);
            
            // Check computation eligibility first
            const eligibilityResponse = await fetch('/user/api/check-computation-eligibility', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    computed_field_id: fieldId,
                    reporting_date: reportingDate
                })
            });
            
            if (!eligibilityResponse.ok) {
                throw new Error(`HTTP ${eligibilityResponse.status}: ${eligibilityResponse.statusText}`);
            }
            
            const eligibilityResult = await eligibilityResponse.json();
            console.log(`🧮 Eligibility result for field ${fieldId}:`, eligibilityResult);
            
            if (!eligibilityResult.success) {
                this.displayComputedValue(valueDisplay, {
                    status: 'error',
                    message: eligibilityResult.error || 'Failed to check computation eligibility'
                });
                return;
            }

            if (!eligibilityResult.eligible) {
                this.displayComputedValue(valueDisplay, {
                    status: 'insufficient',
                    message: eligibilityResult.reason || 'Insufficient data for computation',
                    missing_dependencies: eligibilityResult.missing_dependencies || []
                });
                    return;
                }
            
            // If eligible, attempt computation
            this.displayComputedValue(valueDisplay, {
                status: 'loading',
                message: 'Computing value...'
            });
            
            const computeResponse = await fetch('/user/api/compute-field-on-demand', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    computed_field_id: fieldId,
                    reporting_date: reportingDate,
                    force_compute: false
                })
            });
            
            if (!computeResponse.ok) {
                throw new Error(`HTTP ${computeResponse.status}: ${computeResponse.statusText}`);
            }
            
            const computeResult = await computeResponse.json();
            console.log(`🧮 Computation result for field ${fieldId}:`, computeResult);

            if (computeResult.success && computeResult.value !== null && computeResult.value !== undefined) {
                this.displayComputedValue(valueDisplay, {
                    status: 'success',
                    value: computeResult.value,
                    message: computeResult.message || 'Successfully computed'
                });
                
                // Cache the result
                this.computationCache.set(`${fieldId}-${reportingDate}`, {
                    value: computeResult.value,
                    timestamp: Date.now()
                });
            } else {
                this.displayComputedValue(valueDisplay, {
                    status: 'insufficient',
                    message: computeResult.message || 'Unable to compute value'
                });
            }

        } catch (error) {
            console.error(`❌ Error updating computed field ${fieldId}:`, error);
            this.displayComputedValue(valueDisplay, {
                status: 'error',
                message: `Error: ${error.message}`
            });
        }
    }

    displayComputedValue(valueDisplay, result) {
        if (!valueDisplay) {
            console.warn('⚠️ No value display element provided');
            return;
        }
        
        // Clear existing content
        valueDisplay.innerHTML = '';
        
        // Create computation status container
        const statusContainer = document.createElement('div');
        statusContainer.className = `computation-status ${result.status}`;
        
        switch (result.status) {
            case 'loading':
                statusContainer.innerHTML = `
                    <i class="fas fa-spinner fa-spin"></i>
                    <small class="status-text">${result.message}</small>
                `;
                break;
                
            case 'success':
                const fieldId = valueDisplay.closest('tr')?.querySelector('.data-point-name')?.dataset?.fieldId;
                const tooltipId = `computed-${fieldId}-${Date.now()}`;
                
                statusContainer.innerHTML = `
                    <div class="computed-value-display">
                        <span class="computed-number">${result.value}</span>
                        <span class="computed-info-trigger" data-tooltip-id="${tooltipId}">
                            <i class="fas fa-info-circle"></i>
                        </span>
                    </div>
                    <small class="computed-status text-success">${result.message}</small>
                `;
                break;
                
            case 'insufficient':
                statusContainer.innerHTML = `
                    <i class="fas fa-exclamation-triangle"></i>
                    <small class="status-text">${result.message}</small>
                    ${result.missing_dependencies && result.missing_dependencies.length > 0 ? 
                        `<div class="mt-1">
                            <small class="text-muted">Missing: ${result.missing_dependencies.join(', ')}</small>
                        </div>` : ''
                    }
                `;
                break;
                
            case 'error':
                statusContainer.innerHTML = `
                    <i class="fas fa-times-circle"></i>
                    <small class="status-text">${result.message}</small>
                `;
                break;
                
            case 'not-calculated':
            default:
                const computeFieldId = valueDisplay.closest('tr')?.querySelector('.data-point-name')?.dataset?.fieldId;
                statusContainer.innerHTML = `
                    <i class="fas fa-calculator"></i>
                    <small class="status-text">Not calculated</small>
                    <button type="button" 
                            class="btn btn-sm btn-outline-primary compute-on-demand-btn mt-1"
                            data-field-id="${computeFieldId}">
                        <i class="fas fa-play"></i> Compute
                    </button>
            `;
                break;
        }
        
        valueDisplay.appendChild(statusContainer);
    }

    async handleComputeRequest(button) {
        const fieldId = button.dataset.fieldId;
        const reportingDate = document.getElementById('formReportingDate')?.value;
        
        if (!fieldId || !reportingDate) {
            this.showNotification('error', 'Missing field ID or reporting date');
            return;
        }
        
        if (this.pendingComputations.has(fieldId)) {
            console.log(`⏳ Computation already pending for field ${fieldId}`);
            return;
        }
        
        this.pendingComputations.add(fieldId);
        
        try {
            // Find the value display container
            const fieldRow = button.closest('tr');
            const valueDisplay = fieldRow?.querySelector('.computed-field-container, .computed-value');
            
            if (!valueDisplay) {
                throw new Error('Could not find value display container');
                }

            // Update the display
            await this.updateComputedFieldDisplay(fieldId, reportingDate, valueDisplay);

        } catch (error) {
            console.error(`❌ Error in compute request for field ${fieldId}:`, error);
            this.showNotification('error', `Failed to compute field: ${error.message}`);
        } finally {
            this.pendingComputations.delete(fieldId);
        }
    }

    showNotification(type, message) {
        if (window.PopupManager) {
            switch (type) {
                case 'success':
                    window.PopupManager.showSuccess('Computation Success', message);
                    break;
                case 'error':
                    window.PopupManager.showError('Computation Error', message);
                    break;
                case 'warning':
                    window.PopupManager.showWarning('Computation Warning', message);
                    break;
                default:
                    window.PopupManager.showInfo('Computation Info', message);
            }
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    clearCache() {
        this.computationCache.clear();
        console.log('🧹 Computation cache cleared');
    }

    cleanupOrphanedTooltips() {
        const orphanedTooltips = document.querySelectorAll('.computed-tooltip-portal');
        orphanedTooltips.forEach(tooltip => {
            const tooltipId = tooltip.id.replace('tooltip-', '');
            const trigger = document.querySelector(`[data-tooltip-id="${tooltipId}"]`);
            if (!trigger) {
                tooltip.remove();
                console.log(`🧹 Removed orphaned tooltip: ${tooltip.id}`);
            }
        });
    }

    // Get computation status for a field (for external use)
    getComputationStatus(fieldId, reportingDate) {
        return this.computationCache.get(`${fieldId}-${reportingDate}`);
    }

    async handleTooltipShow(trigger) {
        const tooltipId = trigger.dataset.tooltipId;
        const fieldId = trigger.closest('tr')?.querySelector('.data-point-name')?.dataset?.fieldId;
        const reportingDate = document.getElementById('formReportingDate')?.value;
        
        if (!fieldId || !reportingDate) {
            console.warn('⚠️ Missing field ID or reporting date for tooltip');
            return;
        }
        
        // Check if tooltip already exists
        let tooltip = document.getElementById(`tooltip-${tooltipId}`);
        if (tooltip) {
            tooltip.classList.add('show');
            this.cancelTooltipHide(tooltip);
            return;
        }
        
        // Create new tooltip
            tooltip = document.createElement('div');
            tooltip.id = `tooltip-${tooltipId}`;
            tooltip.className = 'computed-tooltip-portal';
        
        // Add to body for portal behavior
        document.body.appendChild(tooltip);
        
        // Set loading content
            tooltip.innerHTML = `
                <div class="tooltip-content">
                <div class="tooltip-header">
                    <i class="fas fa-calculator"></i> Computation Details
                </div>
                <div class="tooltip-section">
                    <div class="tooltip-loading">
                        <i class="fas fa-spinner fa-spin"></i>
                        <span>Loading computation details...</span>
                    </div>
                    </div>
                </div>
            `;
        
        // Position tooltip
        this.positionTooltip(trigger, tooltip);
        
        // Show tooltip
        tooltip.classList.add('show');
        
        try {
            // Fetch aggregation details
            const response = await fetch(`/user/api/field-aggregation-details/${fieldId}?reporting_date=${reportingDate}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.displayTooltipDetails(tooltip, result.aggregation_details, result.current_value);
            } else {
                throw new Error(result.error || 'Failed to load computation details');
            }
            
        } catch (error) {
            console.error('❌ Error loading tooltip details:', error);
            tooltip.innerHTML = `
                <div class="tooltip-content">
                    <div class="tooltip-header">
                        <i class="fas fa-exclamation-triangle"></i> Error
                    </div>
                    <div class="tooltip-section">
                <div class="tooltip-error">
                            <i class="fas fa-times-circle"></i>
                            <span>Failed to load details: ${error.message}</span>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    positionTooltip(trigger, tooltip) {
        const triggerRect = trigger.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        let left = triggerRect.left + (triggerRect.width / 2) - (tooltipRect.width / 2);
        let top = triggerRect.bottom + 8;
        
        // Reset positioning classes
        tooltip.classList.remove('position-left', 'position-right', 'position-top');
        
        // Adjust horizontal position if tooltip goes off screen
        if (left < 10) {
            left = 10;
            tooltip.classList.add('position-left');
        } else if (left + tooltipRect.width > viewportWidth - 10) {
            left = viewportWidth - tooltipRect.width - 10;
            tooltip.classList.add('position-right');
        }
        
        // Adjust vertical position if tooltip goes off screen
        if (top + tooltipRect.height > viewportHeight - 10) {
            top = triggerRect.top - tooltipRect.height - 8;
                tooltip.classList.add('position-top');
            
            // If still off screen, center it
            if (top < 10) {
                top = Math.max(10, (viewportHeight - tooltipRect.height) / 2);
            }
        }
        
        tooltip.style.left = `${left}px`;
        tooltip.style.top = `${top}px`;
    }

    handleTooltipHide(trigger) {
        const tooltipId = trigger.dataset.tooltipId;
        const tooltip = document.getElementById(`tooltip-${tooltipId}`);
        
        if (tooltip) {
            this.scheduleTooltipHide(tooltip);
        }
    }

    displayTooltipDetails(container, details, currentValue) {
        if (!details) {
            container.innerHTML = `
                <div class="tooltip-content">
                    <div class="tooltip-header">
                        <i class="fas fa-info-circle"></i> No Details Available
                    </div>
                    <div class="tooltip-section">
                        <p>No computation details available for this field.</p>
                    </div>
                </div>
            `;
            return;
        }

        let content = `
            <div class="tooltip-content">
                <div class="tooltip-header">
                    <i class="fas fa-calculator"></i> ${details.field_name || 'Computation Details'}
                </div>
        `;
        
        // Current value section
        if (currentValue !== null && currentValue !== undefined) {
            content += `
                <div class="tooltip-section">
                    <div class="tooltip-label">Current Value</div>
                    <div class="tooltip-result">
                        <span class="result-value">${currentValue}</span>
                    </div>
                </div>
            `;
            }
        
        // Formula section
        if (details.formula) {
            content += `
                <div class="tooltip-section">
                    <div class="tooltip-label">Formula</div>
                    <div class="tooltip-formula">${details.formula}</div>
                </div>
            `;
        }
        
        // Input data section
        if (details.input_data && details.input_data.length > 0) {
            content += `
            <div class="tooltip-section">
                    <div class="tooltip-label">Input Data</div>
                <div class="tooltip-inputs">
            `;
            
            details.input_data.forEach(input => {
                content += `
                        <div class="tooltip-input-item">
                            <div class="input-header">
                            <span class="input-variable">${input.variable || 'N/A'}</span>
                            <span class="input-field">${input.field_name || 'Unknown Field'}</span>
                            ${input.coefficient ? `<span class="input-coefficient">×${input.coefficient}</span>` : ''}
                        </div>
                `;
                
                if (input.values && input.values.length > 0) {
                    content += `
                        <div class="input-values">
                            <span class="input-values-label">Values:</span>
                            <div class="input-values-list">
                    `;
                    
                    input.values.forEach(value => {
                        content += `
                            <div class="input-value-item">
                                <span class="input-date">${value.date}</span>
                                <span class="input-amount">${value.value}</span>
                            </div>
                        `;
                    });
                    
                    content += `
                                    </div>
                                    <div class="input-aggregation">
                                        <span class="aggregation-result">
                                    ${input.aggregation_method || 'Sum'}: ${input.aggregated_value || 'N/A'}
                                        </span>
                                    </div>
                                </div>
                    `;
                } else {
                    content += `
                                <div class="input-no-values">
                            <small class="text-muted">No data available</small>
                        </div>
                    `;
                }
                
                content += `</div>`;
            });
            
            content += `
                    </div>
                </div>
            `;
        }
        
        // Computation steps
        if (details.computation_steps && details.computation_steps.length > 0) {
            content += `
            <div class="tooltip-section">
                    <div class="tooltip-label">Computation Steps</div>
                <div class="tooltip-steps">
            `;
            
            details.computation_steps.forEach((step, index) => {
                content += `
                        <div class="tooltip-step">
                        <span class="step-variable">${step.variable || index + 1}</span>
                        <span class="step-field">${step.description || step.field_name || 'Step'}</span>
                            <span class="step-equals">=</span>
                        <span class="step-calculation">${step.value || 'N/A'}</span>
                        </div>
                `;
            });
            
            content += `
                </div>
            </div>
        `;
    }
        
        content += `</div>`;
        
        container.innerHTML = content;
    }
}

// Initialize the computed fields manager when the script loads
if (typeof window !== 'undefined') {
    window.computedFieldsManager = new ComputedFieldsManager();
    console.log('✅ ComputedFieldsManager instance created and assigned to window');
} 