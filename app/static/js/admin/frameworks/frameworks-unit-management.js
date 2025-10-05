/**
 * Frameworks Unit Management Module
 * Handles unit-aware inputs, unit options, and unit converter
 */

window.FrameworksUnitManagement = (function() {
    'use strict';

    // Unit-aware input setup (exact copy from original)
    function setupUnitAwareInputs(row) {
        const unitCategorySelect = row.querySelector('select[name="unit_category[]"]');
        const defaultUnitInput = row.querySelector('input[name="default_unit[]"]');
        
        if (unitCategorySelect && defaultUnitInput) {
            unitCategorySelect.addEventListener('change', function() {
                loadUnitOptions(this.value, defaultUnitInput);
            });
            
            // Add unit converter button next to unit input
            const unitContainer = defaultUnitInput.parentElement;
            const convertBtn = document.createElement('button');
            convertBtn.type = 'button';
            convertBtn.className = 'btn btn-sm btn-outline-info mt-1';
            convertBtn.innerHTML = '<i class="fas fa-exchange-alt"></i> Convert';
            convertBtn.addEventListener('click', () => openUnitConverter(unitCategorySelect.value));
            unitContainer.appendChild(convertBtn);
        }
    }

    function loadUnitOptions(unitCategory, unitInput) {
        if (!unitCategory) {
            unitInput.placeholder = 'Enter custom unit';
            return;
        }
        
        fetch(`/admin/unit_categories`)
            .then(response => response.json())
            .then(data => {
                const categoryUnits = data[unitCategory] || [];
                const datalist = document.createElement('datalist');
                datalist.id = `units-${Date.now()}`;
                
                categoryUnits.forEach(unit => {
                    const option = document.createElement('option');
                    option.value = unit;
                    datalist.appendChild(option);
                });
                
                unitInput.setAttribute('list', datalist.id);
                unitInput.placeholder = `e.g., ${categoryUnits.slice(0, 3).join(', ')}`;
                document.body.appendChild(datalist);
            })
            .catch(error => console.error('Error loading unit options:', error));
    }

    // Unit Converter Modal (exact copy from original)
    function openUnitConverter(unitCategory) {
        const modal = new bootstrap.Modal(document.getElementById('unitConverterModal'));
        
        if (unitCategory) {
            loadUnitsForConverter(unitCategory);
        }
        
        modal.show();
    }

    function loadUnitsForConverter(unitCategory) {
        fetch(`/admin/unit_categories`)
            .then(response => response.json())
            .then(data => {
                const units = data[unitCategory] || [];
                const fromUnitSelect = document.getElementById('fromUnit');
                const toUnitSelect = document.getElementById('toUnit');
                
                // Clear existing options
                fromUnitSelect.innerHTML = '<option value="">Select unit</option>';
                toUnitSelect.innerHTML = '<option value="">Select unit</option>';
                
                units.forEach(unit => {
                    const fromOption = new Option(unit, unit);
                    const toOption = new Option(unit, unit);
                    fromUnitSelect.appendChild(fromOption);
                    toUnitSelect.appendChild(toOption);
                });
            })
            .catch(error => console.error('Error loading units for converter:', error));
    }

    // Data points drawer unit options (exact copy from original)
    function loadUnitOptionsForDrawer(unitCategory, unitInput) {
        if (!unitCategory) {
            unitInput.placeholder = 'Enter custom unit';
            return;
        }
        
        fetch(`/admin/unit_categories`)
            .then(response => response.json())
            .then(data => {
                const categoryUnits = data[unitCategory] || [];
                const datalist = document.createElement('datalist');
                datalist.id = `drawer-units-${Date.now()}`;
                
                categoryUnits.forEach(unit => {
                    const option = document.createElement('option');
                    option.value = unit;
                    datalist.appendChild(option);
                });
                
                unitInput.setAttribute('list', datalist.id);
                unitInput.placeholder = `e.g., ${categoryUnits.slice(0, 3).join(', ')}`;
                document.body.appendChild(datalist);
            })
            .catch(error => console.error('Error loading unit options for drawer:', error));
    }

    // Public API
    return {
        initialize: function() {
            console.log('FrameworksUnitManagement: Initializing...');
            // Setup unit converter modal listeners if modal exists
            const convertBtn = document.getElementById('convertUnitsBtn');
            if (convertBtn) {
                convertBtn.addEventListener('click', function() {
                    const fromUnit = document.getElementById('fromUnit').value;
                    const toUnit = document.getElementById('toUnit').value;
                    const fromValue = parseFloat(document.getElementById('fromValue').value);
                    
                    if (!fromUnit || !toUnit || isNaN(fromValue)) {
                        alert('Please fill in all fields');
                        return;
                    }
                    
                    // Simple conversion logic - in a real app, this would use a proper conversion library
                    document.getElementById('conversionResult').textContent = 
                        `${fromValue} ${fromUnit} = ${fromValue} ${toUnit} (conversion logic needed)`;
                });
            }
        },
        
        // Core functions
        setupUnitAwareInputs: setupUnitAwareInputs,
        loadUnitOptions: loadUnitOptions,
        openUnitConverter: openUnitConverter,
        loadUnitsForConverter: loadUnitsForConverter,
        loadUnitOptionsForDrawer: loadUnitOptionsForDrawer,
        
        refresh: function() {
            // No refresh needed for unit management
        },
        
        isReady: function() {
            return true;
        }
    };
})(); 