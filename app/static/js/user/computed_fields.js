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
                const valueDisplay = fieldRow.querySelector('.computed-value');
                
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
            console.error('❌ Error handling date change for computed fields:', error);
        }
    }

    async updateComputedFieldDisplay(fieldId, reportingDate, valueDisplay) {
        try {
            console.log(`🔄 Updating computed field display for field ${fieldId} on ${reportingDate}`);
            
            // Check if we have a cached result
            const cacheKey = `${fieldId}-${reportingDate}`;
            if (this.computationCache.has(cacheKey)) {
                const cachedResult = this.computationCache.get(cacheKey);
                console.log(`💾 Using cached result for ${cacheKey}:`, cachedResult);
                this.displayComputedValue(valueDisplay, cachedResult);
                return;
            }

            // Avoid duplicate requests
            if (this.pendingComputations.has(cacheKey)) {
                console.log(`⏳ Request already pending for ${cacheKey}`);
                return;
            }

            this.pendingComputations.add(cacheKey);
            console.log(`🚀 Starting computation check for ${cacheKey}`);
            
            // First check if there's already a computed value in the database
            const existingValueUrl = `/user/api/field-aggregation-details/${fieldId}?reporting_date=${reportingDate}`;
            console.log(`📡 Checking existing value at: ${existingValueUrl}`);
            
            const existingValueResponse = await fetch(existingValueUrl);
            console.log(`📡 Existing value response status: ${existingValueResponse.status}`);
            
            if (existingValueResponse.ok) {
                const existingData = await existingValueResponse.json();
                console.log(`📊 Existing value data:`, existingData);
                
                if (existingData.success && existingData.current_value !== null) {
                    // Display existing value
                    const result = {
                        fieldId: fieldId,
                        reportingDate: reportingDate,
                        eligible: true,
                        value: existingData.current_value,
                        status: 'existing',
                        message: 'Existing computed value'
                    };
                    console.log(`✅ Found existing value:`, result);
                    this.computationCache.set(cacheKey, result);
                    this.displayComputedValue(valueDisplay, result);
                    return;
                }
            } else {
                console.warn(`⚠️ Failed to fetch existing value: ${existingValueResponse.status} ${existingValueResponse.statusText}`);
            }
            
            // Show loading state
            valueDisplay.innerHTML = `
                <div class="computation-status loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Checking data...</span>
                </div>
            `;

            // Check if computation is eligible
            const eligibilityUrl = '/user/api/check-computation-eligibility';
            const eligibilityPayload = {
                computed_field_id: fieldId,
                reporting_date: reportingDate
            };
            
            console.log(`📡 Checking eligibility at: ${eligibilityUrl}`, eligibilityPayload);
            
            const eligibilityResponse = await fetch(eligibilityUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(eligibilityPayload)
            });

            console.log(`📡 Eligibility response status: ${eligibilityResponse.status}`);
            const eligibilityData = await eligibilityResponse.json();
            console.log(`📊 Eligibility data:`, eligibilityData);

            if (!eligibilityData.success) {
                throw new Error(eligibilityData.error);
            }

            const result = {
                fieldId: fieldId,
                reportingDate: reportingDate,
                eligible: eligibilityData.eligible,
                reason: eligibilityData.reason,
                value: null,
                status: 'checked'
            };

            if (eligibilityData.eligible) {
                console.log(`✅ Field is eligible for computation, attempting computation...`);
                
                // Attempt computation
                const computeUrl = '/user/api/compute-field-on-demand';
                const computePayload = {
                    computed_field_id: fieldId,
                    reporting_date: reportingDate,
                    force_compute: false
                };
                
                console.log(`📡 Computing at: ${computeUrl}`, computePayload);
                
                const computeResponse = await fetch(computeUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(computePayload)
                });

                console.log(`📡 Compute response status: ${computeResponse.status}`);
                const computeData = await computeResponse.json();
                console.log(`📊 Compute data:`, computeData);

                if (computeData.success) {
                    result.value = computeData.value;
                    result.status = computeData.status;
                    result.message = computeData.message;
                    console.log(`✅ Computation successful:`, result);
                } else {
                    result.error = computeData.error;
                    result.status = 'error';
                    console.log(`❌ Computation failed:`, result);
                }
            } else {
                console.log(`⚠️ Field not eligible for computation: ${eligibilityData.reason}`);
            }

            // Cache the result
            this.computationCache.set(cacheKey, result);
            console.log(`💾 Cached result for ${cacheKey}:`, result);
            
            // Display the result
            this.displayComputedValue(valueDisplay, result);

        } catch (error) {
            console.error('❌ Error updating computed field display:', error);
            valueDisplay.innerHTML = `
                <div class="computation-status error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Error: ${error.message}</span>
                </div>
            `;
        } finally {
            this.pendingComputations.delete(`${fieldId}-${reportingDate}`);
        }
    }

    displayComputedValue(valueDisplay, result) {
        console.log(`🎨 Displaying computed value:`, result);
        
        if (result.value !== null && result.value !== undefined) {
            // Display computed value with professional info tooltip
            const uniqueId = `computed-${result.fieldId}-${Date.now()}`;
            valueDisplay.innerHTML = `
                <div class="computed-field-container">
                    <div class="computed-value-display">
                        <span class="computed-number">${Number(result.value).toFixed(2)}</span>
                        <div class="computed-info-trigger" 
                             data-field-id="${result.fieldId}"
                             data-reporting-date="${result.reportingDate}"
                             data-tooltip-id="${uniqueId}">
                            <i class="fas fa-info-circle"></i>
                        </div>
                    </div>
                    <small class="text-muted computed-status">${result.message || 'Computed'}</small>
                </div>
            `;
            
            console.log(`✅ Displayed computed value: ${result.value}`);
        } else if (result.eligible === false) {
            // Show insufficient data message with option to force compute
            valueDisplay.innerHTML = `
                <div class="computation-status insufficient">
                    <i class="fas fa-exclamation-circle text-warning"></i>
                    <span class="status-text">Insufficient Data</span>
                    <small class="text-muted d-block">${result.reason}</small>
                    <button class="btn btn-sm btn-outline-primary mt-1 compute-on-demand-btn" 
                            data-field-id="${result.fieldId}" 
                            data-reporting-date="${result.reportingDate}">
                        <i class="fas fa-calculator"></i> Compute Anyway
                    </button>
                </div>
            `;
            console.log(`⚠️ Displayed insufficient data message: ${result.reason}`);
        } else if (result.status === 'error') {
            // Show error message
            valueDisplay.innerHTML = `
                <div class="computation-status error">
                    <i class="fas fa-exclamation-triangle text-danger"></i>
                    <span class="status-text">Error</span>
                    <small class="text-muted d-block">${result.error || 'Computation failed'}</small>
                </div>
            `;
            console.log(`❌ Displayed error message: ${result.error}`);
        } else {
            // Show not calculated
            valueDisplay.innerHTML = `
                <div class="computation-status not-calculated">
                    <i class="fas fa-clock text-muted"></i>
                    <span class="status-text">Not Calculated</span>
                    <button class="btn btn-sm btn-outline-primary mt-1 compute-on-demand-btn" 
                            data-field-id="${result.fieldId}" 
                            data-reporting-date="${result.reportingDate}">
                        <i class="fas fa-calculator"></i> Calculate
                    </button>
                </div>
            `;
            console.log(`🕐 Displayed not calculated message for result:`, result);
        }
    }

    async handleComputeRequest(button) {
        const fieldId = button.dataset.fieldId;
        const reportingDate = button.dataset.reportingDate;
        const forceCompute = button.textContent.includes('Anyway');

        try {
            // Show loading state
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Computing...';

            const response = await fetch('/user/api/compute-field-on-demand', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    computed_field_id: fieldId,
                    reporting_date: reportingDate,
                    force_compute: forceCompute
                })
            });

            const data = await response.json();

            if (data.success) {
                // Update cache
                const cacheKey = `${fieldId}-${reportingDate}`;
                const result = {
                    fieldId: fieldId,
                    reportingDate: reportingDate,
                    eligible: true,
                    value: data.value,
                    status: data.status,
                    message: data.message
                };
                this.computationCache.set(cacheKey, result);

                // Update display
                const valueDisplay = button.closest('.computed-value');
                this.displayComputedValue(valueDisplay, result);

                // Show success message
                this.showNotification('success', 'Field computed successfully!');

                // Trigger refresh of the dashboard to show new value
                if (window.dashboard && window.dashboard.refreshData) {
                    window.dashboard.refreshData();
                }

            } else {
                throw new Error(data.error || 'Computation failed');
            }

        } catch (error) {
            console.error('Error computing field:', error);
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-calculator"></i> Try Again';
            this.showNotification('error', `Computation failed: ${error.message}`);
        }
    }

    showNotification(type, message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';
        
        notification.innerHTML = `
            <strong>${type === 'success' ? 'Success!' : 'Error!'}</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    // Method to clear cache when data changes
    clearCache() {
        this.computationCache.clear();
        console.log('🧹 Computation cache cleared');
        
        // Also clean up any orphaned portal tooltips
        this.cleanupOrphanedTooltips();
    }

    cleanupOrphanedTooltips() {
        const orphanedTooltips = document.querySelectorAll('.computed-tooltip-portal');
        orphanedTooltips.forEach(tooltip => {
            // Clear any pending cleanup timeout
            if (tooltip.cleanupTimeout) {
                clearTimeout(tooltip.cleanupTimeout);
                delete tooltip.cleanupTimeout;
            }
            
            if (tooltip.parentNode) {
                tooltip.parentNode.removeChild(tooltip);
                console.log('🧹 Removed orphaned portal tooltip:', tooltip.id);
            }
        });
    }

    // Method to get computation status for a field
    getComputationStatus(fieldId, reportingDate) {
        const cacheKey = `${fieldId}-${reportingDate}`;
        return this.computationCache.get(cacheKey) || null;
    }

    async handleTooltipShow(trigger) {
        const fieldId = trigger.dataset.fieldId;
        const reportingDate = trigger.dataset.reportingDate;
        const tooltipId = trigger.dataset.tooltipId;
        let tooltip = document.getElementById(`tooltip-${tooltipId}`);
        
        // If tooltip doesn't exist, create it
        if (!tooltip) {
            console.log(`🔧 Creating new portal tooltip: tooltip-${tooltipId}`);
            tooltip = document.createElement('div');
            tooltip.id = `tooltip-${tooltipId}`;
            tooltip.className = 'computed-tooltip-portal';
            tooltip.innerHTML = `
                <div class="tooltip-content">
                    <div class="tooltip-loading">
                        <i class="fas fa-spinner fa-spin"></i>
                        <span>Loading details...</span>
                    </div>
                </div>
            `;
            document.body.appendChild(tooltip);
        }
        
        // Clear any pending cleanup for this tooltip
        if (tooltip.cleanupTimeout) {
            clearTimeout(tooltip.cleanupTimeout);
            delete tooltip.cleanupTimeout;
            console.log(`🔄 Cancelled cleanup for tooltip: tooltip-${tooltipId}`);
        }
        
        // Smart positioning to prevent tooltip from going off-screen
        this.positionTooltip(trigger, tooltip);
        
        // Show tooltip immediately
        tooltip.classList.add('show');
        console.log(`👁️ Showing tooltip: tooltip-${tooltipId}`);
        
        // Check if details are already loaded
        const contentDiv = tooltip.querySelector('.tooltip-content');
        if (!contentDiv || contentDiv.dataset.loaded === 'true') return;
        
        try {
            console.log(`📊 Loading computation details for field ${fieldId} on ${reportingDate}`);
            
            const response = await fetch(`/user/api/field-aggregation-details/${fieldId}?reporting_date=${reportingDate}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to load computation details');
            }
            
            // Display the computation details in tooltip format
            this.displayTooltipDetails(contentDiv, data.aggregation_details, data.current_value);
            contentDiv.dataset.loaded = 'true';
            
        } catch (error) {
            console.error('❌ Error loading computation details:', error);
            contentDiv.innerHTML = `
                <div class="tooltip-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Unable to load details</span>
                </div>
            `;
        }
    }

    positionTooltip(trigger, tooltip) {
        // Reset positioning classes first
        tooltip.classList.remove('position-left', 'position-right', 'position-top');
        
        // Temporarily show tooltip to measure it
        tooltip.style.visibility = 'hidden';
        tooltip.style.opacity = '1';
        tooltip.style.display = 'block';
        tooltip.style.position = 'fixed';
        tooltip.style.zIndex = '9999';
        
        // Wait for next frame to ensure rendering
        requestAnimationFrame(() => {
            // Get viewport dimensions
            const viewport = {
                width: window.innerWidth,
                height: window.innerHeight
            };
            
            // Get trigger element position relative to viewport
            const triggerRect = trigger.getBoundingClientRect();
            
            // Get tooltip dimensions
            const tooltipRect = tooltip.getBoundingClientRect();
            const tooltipWidth = tooltipRect.width;
            const tooltipHeight = tooltipRect.height;
            
            console.log('🎯 Positioning portal tooltip:', {
                viewport,
                triggerRect: {
                    top: triggerRect.top,
                    bottom: triggerRect.bottom,
                    left: triggerRect.left,
                    right: triggerRect.right,
                    width: triggerRect.width,
                    height: triggerRect.height
                },
                tooltipDimensions: {
                    width: tooltipWidth,
                    height: tooltipHeight
                }
            });
            
            // Calculate initial position (centered below trigger)
            let tooltipTop = triggerRect.bottom + 12;
            let tooltipLeft = triggerRect.left + (triggerRect.width / 2) - (tooltipWidth / 2);
            
            // Check vertical positioning
            const spaceBelow = viewport.height - triggerRect.bottom;
            const spaceAbove = triggerRect.top;
            const tooltipHeightWithMargin = tooltipHeight + 24;
            
            console.log('📏 Vertical space check:', {
                spaceBelow,
                spaceAbove,
                tooltipHeightWithMargin,
                needsRepositioning: spaceBelow < tooltipHeightWithMargin
            });
            
            // Position above if not enough space below
            if (spaceBelow < tooltipHeightWithMargin && spaceAbove > tooltipHeightWithMargin) {
                tooltipTop = triggerRect.top - tooltipHeight - 12;
                tooltip.classList.add('position-top');
                console.log('📍 Positioning tooltip above trigger');
            } else if (spaceBelow < tooltipHeightWithMargin) {
                // Not enough space above or below - position above anyway but closer to trigger
                tooltipTop = Math.max(8, triggerRect.top - tooltipHeight - 12);
                tooltip.classList.add('position-top');
                console.log('⚠️ Limited space - positioning above with adjustment');
            }
            
            // Check horizontal positioning
            const rightEdge = tooltipLeft + tooltipWidth;
            const leftEdge = tooltipLeft;
            
            console.log('📏 Horizontal space check:', {
                tooltipLeft,
                leftEdge,
                rightEdge,
                viewportWidth: viewport.width
            });
            
            if (rightEdge > viewport.width - 20) {
                // Would go off right edge - align to right
                tooltipLeft = viewport.width - tooltipWidth - 20;
                tooltip.classList.add('position-right');
                console.log('📍 Adjusting tooltip to prevent right edge overflow');
            } else if (leftEdge < 20) {
                // Would go off left edge - align to left
                tooltipLeft = 20;
                tooltip.classList.add('position-left');
                console.log('📍 Adjusting tooltip to prevent left edge overflow');
            }
            
            // Apply final positioning
            tooltip.style.top = `${Math.max(8, tooltipTop)}px`;
            tooltip.style.left = `${Math.max(8, tooltipLeft)}px`;
            
            // Reset visibility
            tooltip.style.visibility = '';
            tooltip.style.opacity = '';
            
            console.log('✅ Portal tooltip positioned at:', {
                top: tooltip.style.top,
                left: tooltip.style.left,
                classes: Array.from(tooltip.classList)
            });
        });
    }

    handleTooltipHide(trigger) {
        const tooltipId = trigger.dataset.tooltipId;
        const tooltip = document.getElementById(`tooltip-${tooltipId}`);
        
        if (tooltip) {
            console.log(`👁️ Hiding tooltip: tooltip-${tooltipId}`);
            this.scheduleTooltipHide(tooltip);
        }
    }

    displayTooltipDetails(container, details, currentValue) {
        if (!details || !details.dependencies) {
            container.innerHTML = `
                <div class="tooltip-error">
                    <span>No computation details available</span>
                </div>
            `;
            return;
        }

        // Enhanced formula display that shows coefficients
        let formulaDisplay = details.formula || 'No formula available';
        let enhancedFormula = formulaDisplay;
        
        // Create a mapping of variables to their coefficients
        const variableInfo = {};
        details.dependencies.forEach(dep => {
            variableInfo[dep.variable] = {
                coefficient: dep.coefficient || 1.0,
                name: dep.field_name,
                aggregatedValue: dep.aggregated_value
            };
        });
        
        // Enhance the formula to show coefficients when they're not 1.0
        Object.entries(variableInfo).forEach(([variable, info]) => {
            if (info.coefficient !== 1.0) {
                const regex = new RegExp(`\\b${variable}\\b`, 'g');
                enhancedFormula = enhancedFormula.replace(regex, `${info.coefficient}×${variable}`);
            }
        });
        
        // Build step-by-step calculation
        const steps = [];
        details.dependencies.forEach(dep => {
            const coefficient = dep.coefficient || 1.0;
            const aggregatedValue = dep.aggregated_value !== null ? Number(dep.aggregated_value) : 0;
            const finalValue = aggregatedValue * coefficient;
            
            if (coefficient !== 1.0) {
                steps.push({
                    variable: dep.variable,
                    fieldName: dep.field_name,
                    baseValue: aggregatedValue.toFixed(2),
                    coefficient: coefficient,
                    finalValue: finalValue.toFixed(2),
                    calculation: `${aggregatedValue.toFixed(2)} × ${coefficient} = ${finalValue.toFixed(2)}`,
                    rawValues: dep.values_used || []
                });
            } else {
                steps.push({
                    variable: dep.variable,
                    fieldName: dep.field_name,
                    finalValue: finalValue.toFixed(2),
                    calculation: finalValue.toFixed(2),
                    rawValues: dep.values_used || []
                });
            }
        });
        
        container.innerHTML = `
            <div class="tooltip-header">
                <strong>Computation Details</strong>
            </div>
            
            <div class="tooltip-section">
                <div class="tooltip-label">Formula:</div>
                <div class="tooltip-formula">${enhancedFormula}</div>
            </div>
            
            <div class="tooltip-section">
                <div class="tooltip-label">Input Data:</div>
                <div class="tooltip-inputs">
                    ${steps.map(step => `
                        <div class="tooltip-input-item">
                            <div class="input-header">
                                <span class="input-variable">${step.variable}</span>
                                <span class="input-field">${step.fieldName}</span>
                                ${step.coefficient && step.coefficient !== 1.0 ? `
                                    <span class="input-coefficient">×${step.coefficient}</span>
                                ` : ''}
                            </div>
                            ${step.rawValues && step.rawValues.length > 0 ? `
                                <div class="input-values">
                                    <small class="input-values-label">Raw values submitted:</small>
                                    <div class="input-values-list">
                                        ${step.rawValues.map(val => `
                                            <span class="input-value-item">
                                                <span class="input-date">${val.date}</span>
                                                <span class="input-amount">${Number(val.value).toFixed(2)}</span>
                                            </span>
                                        `).join('')}
                                    </div>
                                    <div class="input-aggregation">
                                        <span class="aggregation-result">
                                            Aggregated (SUM): <strong>${step.baseValue}</strong>
                                        </span>
                                    </div>
                                </div>
                            ` : `
                                <div class="input-no-values">
                                    <small class="text-muted">No raw values available</small>
                                </div>
                            `}
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="tooltip-section">
                <div class="tooltip-label">Calculation:</div>
                <div class="tooltip-steps">
                    ${steps.map(step => `
                        <div class="tooltip-step">
                            <span class="step-variable">${step.variable}</span>
                            <span class="step-equals">=</span>
                            <span class="step-calculation">${step.calculation}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="tooltip-section">
                <div class="tooltip-result">
                    <span class="result-formula">${enhancedFormula}</span>
                    <span class="result-equals">=</span>
                    <span class="result-value">${Number(currentValue).toFixed(2)}</span>
                </div>
            </div>
        `;
    }
}

// Initialize the computed fields manager
const computedFieldsManager = new ComputedFieldsManager();

// Make it globally available
window.computedFieldsManager = computedFieldsManager; 