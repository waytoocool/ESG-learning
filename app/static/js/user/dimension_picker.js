/**
 * Phase 2.5: Dimension Picker Functionality for User Dashboard
 * Handles dimension selection during data entry
 */

class DimensionPickerManager {
    constructor() {
        this.fieldDimensions = new Map(); // fieldId -> dimensions array
        this.selectedDimensions = new Map(); // fieldId -> {dimensionId: valueId}
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        console.log('📊 DimensionPickerManager initialized');
    }
    
    setupEventListeners() {
        // Listen for dimension selection changes
        document.addEventListener('change', (e) => {
            if (e.target.type === 'radio' && e.target.name.startsWith('dimension_')) {
                this.handleDimensionSelection(e.target);
            }
        });
        
        // Listen for form submission to validate required dimensions
        document.addEventListener('submit', (e) => {
            if (e.target.id === 'dataEntryForm') {
                if (!this.validateRequiredDimensions()) {
                    e.preventDefault();
                    alert('Please select all required dimensions before submitting.');
                }
            }
        });
    }
    
    handleDimensionSelection(radioInput) {
        const fieldId = radioInput.dataset.fieldId;
        const dimensionId = radioInput.dataset.dimensionId;
        const dimensionName = radioInput.dataset.dimensionName;
        const valueId = radioInput.value;
        const dimensionValue = radioInput.dataset.dimensionValue;
        
        if (!this.selectedDimensions.has(fieldId)) {
            this.selectedDimensions.set(fieldId, {});
        }
        
        // Store by dimension name (lowercase) to match backend expectations
        this.selectedDimensions.get(fieldId)[dimensionName.toLowerCase()] = dimensionValue;
        
        console.log(`📊 Selected dimension: Field ${fieldId}, Dimension ${dimensionName}, Value: ${dimensionValue}`);
        
        // Update hidden input for form submission
        this.updateDimensionDataInput(fieldId);
        
        // Trigger any computed field recalculation if needed
        this.triggerComputedFieldUpdate(fieldId);
    }
    
    updateDimensionDataInput(fieldId) {
        const fieldDimensions = this.selectedDimensions.get(fieldId) || {};
        
        // Create or update hidden input to store dimension data
        let hiddenInput = document.querySelector(`input[name="field_${fieldId}_dimensions"]`);
        if (!hiddenInput) {
            hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = `field_${fieldId}_dimensions`;
            
            // Insert after the main field input
            const mainInput = document.querySelector(`input[name="field_${fieldId}"]`);
            if (mainInput && mainInput.parentNode) {
                mainInput.parentNode.insertBefore(hiddenInput, mainInput.nextSibling);
            }
        }
        
        hiddenInput.value = JSON.stringify(fieldDimensions);
    }
    
    validateRequiredDimensions() {
        const requiredDimensionInputs = document.querySelectorAll('input[type="radio"][required]');
        const requiredGroups = new Set();
        
        // Collect all required radio groups
        requiredDimensionInputs.forEach(input => {
            requiredGroups.add(input.name);
        });
        
        // Check if each required group has a selection
        for (const groupName of requiredGroups) {
            const isSelected = document.querySelector(`input[name="${groupName}"]:checked`);
            if (!isSelected) {
                return false;
            }
        }
        
        return true;
    }
    
    triggerComputedFieldUpdate(fieldId) {
        // Trigger computed field recalculation if this field affects any computed fields
        if (window.computedFieldsManager && window.computedFieldsManager.onDataChange) {
            window.computedFieldsManager.onDataChange(fieldId);
        }
    }
    
    // Load dimensions for a specific field (called during data loading)
    loadFieldDimensions(fieldId, dimensions) {
        this.fieldDimensions.set(fieldId, dimensions);
    }
    
    // Get selected dimensions for a field
    getSelectedDimensions(fieldId) {
        return this.selectedDimensions.get(fieldId) || {};
    }
    
    // Set selected dimensions for a field (for loading existing data)
    setSelectedDimensions(fieldId, dimensions) {
        this.selectedDimensions.set(fieldId, dimensions);
        
        // Update radio button selections
        Object.entries(dimensions).forEach(([dimensionId, dimData]) => {
            const radioInput = document.querySelector(
                `input[name="dimension_${fieldId}_${dimensionId}"][value="${dimData.value_id}"]`
            );
            if (radioInput) {
                radioInput.checked = true;
            }
        });
        
        this.updateDimensionDataInput(fieldId);
    }
    
    // Clear dimensions for a field
    clearFieldDimensions(fieldId) {
        this.selectedDimensions.delete(fieldId);
        
        // Clear radio button selections
        const radioInputs = document.querySelectorAll(`input[type="radio"][data-field-id="${fieldId}"]`);
        radioInputs.forEach(input => {
            input.checked = false;
        });
        
        // Remove hidden input
        const hiddenInput = document.querySelector(`input[name="field_${fieldId}_dimensions"]`);
        if (hiddenInput) {
            hiddenInput.remove();
        }
    }
    
    // Enhanced input creation with dimension support
    createEnhancedInput(dataPoint) {
        const hasUnitCategory = dataPoint.unit_category && dataPoint.unit_category !== '';
        const hasDimensions = dataPoint.dimensions && dataPoint.dimensions.length > 0;
        
        let containerClass = 'unit-aware-input-container';
        if (hasDimensions) {
            containerClass += ' has-dimensions';
        }
        
        if (!hasUnitCategory && !hasDimensions) {
            // Simple input for fields without unit categories or dimensions
            return `<input type="${dataPoint.value_type === 'numeric' ? 'number' : 'text'}"
                           class="data-input form-control"
                           name="field_${dataPoint.id}"
                           value="${dataPoint.current_value || ''}"
                           ${dataPoint.value_type === 'numeric' ? 'step="any"' : ''}
                           placeholder="Enter ${dataPoint.value_type} value">`;
        }
        
        // Build enhanced input with dimensions
        const unitSelectId = `unit_${dataPoint.id}`;
        const inputId = `field_${dataPoint.id}`;
        
        const optionsMarkup = (dataPoint.unit_options && dataPoint.unit_options.length)
            ? dataPoint.unit_options.map(opt => `<option value="${opt.value}">${opt.label}</option>`).join('')
            : '<option value="">Loading...</option>';
        
        // Main input group
        let inputGroupHTML = `
            <div class="input-group">
                <input type="${dataPoint.value_type === 'numeric' ? 'number' : 'text'}"
                       class="data-input form-control unit-aware-input"
                       name="field_${dataPoint.id}"
                       id="${inputId}"
                       value="${dataPoint.current_value || ''}"
                       ${dataPoint.value_type === 'numeric' ? 'step="any"' : ''}
                       placeholder="Enter ${dataPoint.value_type} value"
                       data-field-id="${dataPoint.id}"
                       data-unit-category="${dataPoint.unit_category || ''}"
                       data-default-unit="${dataPoint.default_unit || ''}">`;
        
        // Add unit selector if applicable
        if (hasUnitCategory) {
            inputGroupHTML += `
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
                </button>`;
        }
        
        inputGroupHTML += `</div>`;
        
        // Add dimension pickers if applicable
        let dimensionPickersHTML = '';
        if (hasDimensions) {
            dimensionPickersHTML = this.createDimensionPickers(dataPoint);
            this.loadFieldDimensions(dataPoint.id, dataPoint.dimensions);
        }
        
        // Add info text
        let infoHTML = '';
        const infoParts = [];
        
        if (hasUnitCategory) {
            infoParts.push(`Default: ${dataPoint.default_unit || 'None'} | Category: ${dataPoint.unit_category}`);
        }
        
        if (hasDimensions) {
            const requiredDims = dataPoint.dimensions.filter(dim => dim.is_required).length;
            infoParts.push(`${dataPoint.dimensions.length} dimension(s)${requiredDims > 0 ? ` (${requiredDims} required)` : ''}`);
        }
        
        if (infoParts.length > 0) {
            infoHTML = `<small class="text-muted unit-info">${infoParts.join(' | ')}</small>`;
        }
        
        return `
            <div class="${containerClass}" data-field-id="${dataPoint.id}">
                ${hasDimensions ? '<div class="dimension-indicators">' + this.createDimensionIndicators(dataPoint.dimensions) + '</div>' : ''}
                ${inputGroupHTML}
                ${dimensionPickersHTML}
                ${infoHTML}
            </div>`;
    }
    
    createDimensionIndicators(dimensions) {
        return dimensions.map(dim => `
            <span class="dimension-indicator ${dim.is_required ? 'required' : ''}">
                ${dim.name}${dim.is_required ? ' *' : ''}
            </span>
        `).join('');
    }
    
    createDimensionPickers(dataPoint) {
        if (!dataPoint.dimensions || dataPoint.dimensions.length === 0) {
            return '';
        }
        
        return dataPoint.dimensions.map(dimension => {
            const pickerId = `dimension_${dataPoint.id}_${dimension.dimension_id}`;
            const isRequired = dimension.is_required;
            
            return `
                <div class="dimension-picker" data-dimension-id="${dimension.dimension_id}">
                    <h6>${dimension.name}${isRequired ? ' <span class="dimension-required-indicator">*</span>' : ''}</h6>
                    ${dimension.values.map(value => `
                        <div class="dimension-option">
                            <input type="radio" 
                                   id="${pickerId}_${value.value_id}" 
                                   name="${pickerId}"
                                   value="${value.value_id}"
                                   data-dimension-value="${value.value}"
                                   data-field-id="${dataPoint.id}"
                                   data-dimension-id="${dimension.dimension_id}"
                                   data-dimension-name="${dimension.name}"
                                   ${isRequired ? 'required' : ''}>
                            <label for="${pickerId}_${value.value_id}">
                                ${value.effective_display_name || value.display_name || value.value}
                            </label>
                        </div>
                    `).join('')}
                </div>
            `;
        }).join('');
    }
}

// Initialize dimension picker manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.dimensionPickerManager = new DimensionPickerManager();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DimensionPickerManager;
} 