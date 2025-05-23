document.addEventListener('DOMContentLoaded', function() {
    const cardDeck = document.getElementById('frameworkCardDeck');
    const scrollLeftBtn = document.getElementById('scrollLeft');
    const scrollRightBtn = document.getElementById('scrollRight');

    // Only initialize scroll functionality if the elements exist
    if (cardDeck && scrollLeftBtn && scrollRightBtn) {
        function updateScrollButtons() {
            scrollLeftBtn.disabled = cardDeck.scrollLeft === 0;
            scrollRightBtn.disabled = 
                cardDeck.scrollLeft + cardDeck.clientWidth >= cardDeck.scrollWidth;
        }

        scrollLeftBtn.addEventListener('click', function() {
            cardDeck.scrollBy({
                left: -cardDeck.clientWidth,
                behavior: 'smooth'
            });
        });

        scrollRightBtn.addEventListener('click', function() {
            cardDeck.scrollBy({
                left: cardDeck.clientWidth,
                behavior: 'smooth'
            });
        });

        // Initial button state
        updateScrollButtons();

        // Update scroll buttons on scroll and resize
        cardDeck.addEventListener('scroll', updateScrollButtons);
        window.addEventListener('resize', updateScrollButtons);
    }

    // Rest of the previous JavaScript remains the same (data points, modal handling, etc.)
    const dataPointsContainer = document.getElementById('dataPointsContainer');
    const addDataPointBtn = document.getElementById('addDataPoint');
    const createFrameworkForm = document.getElementById('createFrameworkForm');

    // Add Data Point to Table
    addDataPointBtn.addEventListener('click', function() {
        const rowId = Date.now();
        const newRow = document.createElement('tr');
        newRow.innerHTML = `
            <td>
                <input type="text" class="form-control form-control-sm" name="data_point_name[]" required>
            </td>
            <td>
                <input type="text" class="form-control form-control-sm" name="data_point_description[]">
            </td>
            <td class="text-center">
                <input type="checkbox" class="form-check-input is-computed-checkbox" name="data_point_is_computed[]" value="true">
            </td>
            <td class="formula-cell">
                <div class="formula-inputs d-none">
                    <div class="mb-3">
                        <label class="form-label">Formula Expression</label>
                        <input type="text" class="form-control form-control-sm formula-expression" 
                               name="formula_expression[]" placeholder="e.g., (A + B) / C">
                        <small class="text-muted">Use variables (A, B, C...) to represent fields</small>
                    </div>
                    <div class="raw-fields-container">
                        <!-- Raw fields will be added here -->
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-success add-raw-field mt-2">
                        <i class="fas fa-plus"></i> Add Field Mapping
                    </button>
                </div>
            </td>
            <td>
                <button type="button" class="btn btn-danger btn-sm remove-data-point">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;

        // Handle computed checkbox change
        const computedCheckbox = newRow.querySelector('.is-computed-checkbox');
        const formulaInputs = newRow.querySelector('.formula-inputs');
        
        computedCheckbox.addEventListener('change', function() {
            formulaInputs.classList.toggle('d-none', !this.checked);
        });

        // Handle adding raw fields
        const addRawFieldBtn = newRow.querySelector('.add-raw-field');
        const rawFieldsContainer = newRow.querySelector('.raw-fields-container');

        addRawFieldBtn.addEventListener('click', function() {
            const rawFieldGroup = document.createElement('div');
            rawFieldGroup.className = 'raw-field-group mb-2';
            rawFieldGroup.innerHTML = `
                <div class="d-flex gap-2 align-items-center">
                    <input type="text" class="form-control form-control-sm variable-name" 
                           placeholder="Variable (e.g., A)" style="width: 80px;"
                           maxlength="1" required>
                    <input type="number" class="form-control form-control-sm coefficient" 
                           placeholder="Coefficient" style="width: 100px;"
                           step="0.001" value="1">
                    <span class="mx-2">=</span>
                    <select class="form-control form-control-sm framework-select">
                        <option value="">Select Framework</option>
                        <!-- Will be populated dynamically -->
                    </select>
                    <select class="form-control form-control-sm raw-field-select" name="raw_field_name[]">
                        <option value="">Select Field</option>
                    </select>
                    <button type="button" class="btn btn-danger btn-sm remove-raw-field">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;

            // Add event listener for remove button
            rawFieldGroup.querySelector('.remove-raw-field').addEventListener('click', function() {
                rawFieldGroup.remove();
                updateDependencies();
            });

            // Populate framework options
            const frameworkSelect = rawFieldGroup.querySelector('.framework-select');
            populateFrameworkOptions(frameworkSelect);

            // Handle framework selection change
            frameworkSelect.addEventListener('change', function() {
                const rawFieldSelect = this.nextElementSibling;
                populateRawFieldOptions(rawFieldSelect, this.value);
            });

            rawFieldsContainer.appendChild(rawFieldGroup);
            updateDependencies();
        });

        // Remove data point row
        newRow.querySelector('.remove-data-point').addEventListener('click', function() {
            newRow.remove();
            updateDependencies();
        });

        dataPointsContainer.appendChild(newRow);
    });

    // Helper function to populate framework options
    function populateFrameworkOptions(selectElement) {
        // Fetch frameworks from the server
        fetch('/admin/get_frameworks')
            .then(response => response.json())
            .then(frameworks => {
                selectElement.innerHTML = `
                    <option value="">Select Framework</option>
                    ${frameworks.map(fw => `
                        <option value="${fw.framework_id}">${fw.framework_name}</option>
                    `).join('')}
                `;
            })
            .catch(error => console.error('Error fetching frameworks:', error));
    }

    // Helper function to populate raw field options based on selected framework
    function populateRawFieldOptions(selectElement, frameworkId) {
        if (!frameworkId) {
            selectElement.innerHTML = '<option value="">Select Field</option>';
            return;
        }

        // Fetch fields for the selected framework
        fetch(`/admin/get_framework_fields/${frameworkId}`)
            .then(response => response.json())
            .then(fields => {
                selectElement.innerHTML = `
                    <option value="">Select Field</option>
                    ${fields.map(field => `
                        <option value="${field.field_id}">${field.field_name}</option>
                    `).join('')}
                `;
            })
            .catch(error => console.error('Error fetching fields:', error));
    }

    // Function to update dependencies object
    function updateDependencies() {
        const dependencies = {};
        
        document.querySelectorAll('.is-computed-checkbox:checked').forEach(checkbox => {
            const row = checkbox.closest('tr');
            const computedFieldName = row.querySelector('input[name="data_point_name[]"]').value;
            const formulaExpression = row.querySelector('.formula-expression').value;
            
            const fieldMappings = Array.from(row.querySelectorAll('.raw-field-group')).map(group => ({
                variable: group.querySelector('.variable-name').value,
                framework_id: group.querySelector('.framework-select').value,
                field_id: group.querySelector('.raw-field-select').value,
                field_name: group.querySelector('.raw-field-select option:checked').text,
                coefficient: parseFloat(group.querySelector('.coefficient').value) || 1
            }));

            if (computedFieldName && formulaExpression && fieldMappings.length > 0) {
                dependencies[computedFieldName] = {
                    formula: formulaExpression,
                    fieldMappings: fieldMappings
                };
            }
        });

        // Store dependencies in a hidden input
        let dependenciesInput = document.getElementById('dependencies-input');
        if (!dependenciesInput) {
            dependenciesInput = document.createElement('input');
            dependenciesInput.type = 'hidden';
            dependenciesInput.id = 'dependencies-input';
            dependenciesInput.name = 'dependencies';
            createFrameworkForm.appendChild(dependenciesInput);
        }
        dependenciesInput.value = JSON.stringify(dependencies);
    }

    // Form validation
    createFrameworkForm.addEventListener('submit', function(event) {
        event.preventDefault();
        updateDependencies();
        
        // Validate dependencies
        const dependencies = JSON.parse(document.getElementById('dependencies-input').value);
        let isValid = true;
        
        for (const [computedField, data] of Object.entries(dependencies)) {
            if (!data.formula) {
                alert(`Please enter a formula expression for computed field: ${computedField}`);
                isValid = false;
                break;
            }
            
            // Validate that all variables in formula have mappings
            const variables = new Set(data.formula.match(/[A-Z]/g) || []);
            const mappedVariables = new Set(data.fieldMappings.map(m => m.variable));
            
            const unmappedVariables = [...variables].filter(v => !mappedVariables.has(v));
            if (unmappedVariables.length > 0) {
                alert(`Missing field mappings for variables: ${unmappedVariables.join(', ')} in field: ${computedField}`);
                isValid = false;
                break;
            }

            // Validate that all mappings have complete information
            for (const mapping of data.fieldMappings) {
                if (!mapping.variable || !mapping.framework_id || !mapping.field_id) {
                    alert(`Please complete all field mappings for: ${computedField}`);
                    isValid = false;
                    break;
                }
            }
        }
        
        if (isValid) {
            this.submit();
        }
    });

    // Handle Framework Details Modal
    document.querySelectorAll('.view-details-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const frameworkCard = this.closest('.framework-card');
            const frameworkId = frameworkCard.dataset.frameworkId;
            
            // Add loading state
            const modalBody = document.getElementById('frameworkModalBody');
            modalBody.innerHTML = '<div class="text-center">Loading...</div>';
            
            fetch(`/admin/frameworks/${frameworkId}`)
                .then(response => {
                    if (!response.ok) {
                        return response.text().then(text => {
                            throw new Error(`HTTP error! status: ${response.status}, message: ${text}`);
                        });
                    }
                    return response.json();
                })
                .then(framework => {
                    const modalTitle = document.getElementById('frameworkModalTitle');
                    const modalBody = document.getElementById('frameworkModalBody');

                    modalTitle.textContent = framework.framework_name;
                    modalBody.innerHTML = `
                        <p><strong>Description:</strong> ${framework.description || 'No description available'}</p>
                        <p><strong>Created At:</strong> ${new Date(framework.created_at).toLocaleDateString()}</p>
                        
                        <h5>Data Points</h5>
                        ${framework.data_fields && framework.data_fields.length > 0 ? 
                            `<table class="table">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Type</th>
                                        <th>Formula</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${framework.data_fields.map(field => `
                                        <tr>
                                            <td>${field.field_name}</td>
                                            <td>${field.is_computed ? 'Computed' : 'Raw'}</td>
                                            <td>${field.formula || 'N/A'}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>` 
                            : '<p>No data points available</p>'}
                    `;
                })
                .catch(error => {
                    const modalBody = document.getElementById('frameworkModalBody');
                    modalBody.innerHTML = `
                        <div class="alert alert-danger">
                            Error loading framework details. Please try again later.
                        </div>`;
                });
        });
    });

    // Form Validation
    createFrameworkForm.addEventListener('submit', function(event) {
        const frameworkName = document.getElementById('framework_name');
        
        if (!frameworkName.value.trim()) {
            event.preventDefault();
            alert('Framework Name is required');
            frameworkName.focus();
        }
    });
});