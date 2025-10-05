/**
 * Phase 2.5: Computed Field Dimension Configuration
 * Handles dimension filtering and aggregation configuration for computed fields
 */

class ComputedFieldDimensionManager {
    constructor() {
        this.availableDimensions = [];
        this.init();
    }
    
    init() {
        this.loadAvailableDimensions();
        console.log('ComputedFieldDimensionManager initialized');
    }
    
    loadAvailableDimensions() {
        fetch('/admin/dimensions')
            .then(response => response.json())
            .then(data => {
                this.availableDimensions = data.dimensions || [];
                console.log('Loaded dimensions for computed fields:', this.availableDimensions.length);
            })
            .catch(error => {
                console.error('Error loading dimensions:', error);
                this.availableDimensions = [];
            });
    }
    
    // Add raw field mapping with dimension support
    addRawFieldMapping(row) {
        const rawFieldsContainer = row.querySelector('.raw-fields-container');
        if (!rawFieldsContainer) return;
        
        const mappingId = Date.now() + Math.random();
        const mappingDiv = document.createElement('div');
        mappingDiv.className = 'raw-field-mapping border rounded p-3 mb-3';
        mappingDiv.setAttribute('data-mapping-id', mappingId);
        
        mappingDiv.innerHTML = 
            '<div class="row g-3">' +
                '<div class="col-md-2">' +
                    '<label class="form-label">Variable</label>' +
                    '<input type="text" class="form-control form-control-sm variable-input" placeholder="A" maxlength="1" pattern="[A-Z]" required>' +
                '</div>' +
                '<div class="col-md-3">' +
                    '<label class="form-label">Framework</label>' +
                    '<select class="form-control form-control-sm framework-select" required>' +
                        '<option value="">Select Framework</option>' +
                    '</select>' +
                '</div>' +
                '<div class="col-md-4">' +
                    '<label class="form-label">Field</label>' +
                    '<select class="form-control form-control-sm field-select" disabled required>' +
                        '<option value="">Select Framework First</option>' +
                    '</select>' +
                '</div>' +
                '<div class="col-md-2">' +
                    '<label class="form-label">Coefficient</label>' +
                    '<input type="number" class="form-control form-control-sm coefficient-input" value="1" step="any" required>' +
                '</div>' +
                '<div class="col-md-1">' +
                    '<label class="form-label">&nbsp;</label>' +
                    '<button type="button" class="btn btn-danger btn-sm d-block remove-mapping-btn">' +
                        '<i class="fas fa-trash"></i>' +
                    '</button>' +
                '</div>' +
            '</div>' +
            
            '<div class="computed-field-dimension-config">' +
                '<h6><i class="fas fa-tags"></i> Dimension Aggregation</h6>' +
                
                '<div class="aggregation-type-selector">' +
                    '<div class="form-check">' +
                        '<input class="form-check-input aggregation-type-radio" type="radio" name="aggregation_type_' + mappingId + '" id="sum_all_' + mappingId + '" value="SUM_ALL_DIMENSIONS" checked>' +
                        '<label class="form-check-label" for="sum_all_' + mappingId + '">' +
                            '<strong>Sum All Dimensions</strong>' +
                            '<small class="d-block text-muted">Aggregate all dimensional values (e.g., All Male + Female employees)</small>' +
                        '</label>' +
                    '</div>' +
                    '<div class="form-check">' +
                        '<input class="form-check-input aggregation-type-radio" type="radio" name="aggregation_type_' + mappingId + '" id="specific_dimension_' + mappingId + '" value="SPECIFIC_DIMENSION">' +
                        '<label class="form-check-label" for="specific_dimension_' + mappingId + '">' +
                            '<strong>Specific Dimension Filter</strong>' +
                            '<small class="d-block text-muted">Filter to specific dimensional values (e.g., Only Male employees under 30)</small>' +
                        '</label>' +
                    '</div>' +
                '</div>' +
                
                '<div class="dimension-filter-section" style="display: none;">' +
                    '<div class="dimension-filter-builder">' +
                        '<div class="d-flex justify-content-between align-items-center mb-3">' +
                            '<label class="form-label mb-0">Dimension Filters</label>' +
                            '<button type="button" class="btn btn-outline-primary btn-sm add-dimension-filter-btn">' +
                                '<i class="fas fa-plus"></i> Add Filter' +
                            '</button>' +
                        '</div>' +
                        '<div class="dimension-filters-container">' +
                        '</div>' +
                        '<small class="text-muted">' +
                            'Only data matching all selected dimension values will be included in the calculation.' +
                        '</small>' +
                    '</div>' +
                '</div>' +
                
                '<input type="hidden" class="aggregation-type-input" name="aggregation_type[]" value="SUM_ALL_DIMENSIONS">' +
                '<input type="hidden" class="dimension-filter-input" name="dimension_filter[]" value="">' +
            '</div>';
        
        rawFieldsContainer.appendChild(mappingDiv);
        
        // Setup event listeners for this mapping
        this.setupMappingEventListeners(mappingDiv, mappingId);
        
        // Load available frameworks
        this.loadFrameworksForMapping(mappingDiv);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.computedFieldDimensionManager === 'undefined') {
        window.computedFieldDimensionManager = new ComputedFieldDimensionManager();
    }
}); 