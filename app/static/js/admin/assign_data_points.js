// 1. Add tracking of previous points and assignments
let previousPoints = [];
let entityAssignments = {};  // Store current entity assignments

async function loadExistingDataPoints() {
    try {
        const [dataPointsResponse, assignmentsResponse] = await Promise.all([
            fetch('/admin/get_existing_data_points'),
            fetch('/admin/get_data_point_assignments')
        ]);
        
        const existingPoints = await dataPointsResponse.json();
        const assignments = await assignmentsResponse.json();
        
        // Store previous points and initialize assignments
        previousPoints = existingPoints;
        // Convert all entity IDs to strings for consistent comparison
        entityAssignments = Object.fromEntries(
            Object.entries(assignments).map(([key, values]) => [
                key,
                values.map(v => v.toString())
            ])
        );
        
        // Clear existing content
        selectedFields.innerHTML = '';
        
        // Populate the selected fields
        existingPoints.forEach(point => {
            const card = createDataPointCard(point, true); // true indicates it's in selected area
            selectedFields.appendChild(card);
        });

        // Then, create the accordion with assignments
        await createDataPointsAccordion(existingPoints);
    } catch (error) {
        console.error('Error loading existing data points:', error);
        showToast('Error loading existing data points', 'error');
    }
}

// 2. Create a reusable function for creating data point cards
function createDataPointCard(field, isSelected = false) {
    const card = document.createElement('div');
    card.className = 'data-point-card';
    card.setAttribute('draggable', 'true');
    card.setAttribute('data-field-id', field.field_id);
    card.innerHTML = `
        <span class="dp-name">${field.field_name}</span>
        <button class="btn btn-sm ${isSelected ? 'btn-danger remove-field' : 'btn-primary add-field'}">
            ${isSelected ? '-' : '+'}
        </button>
    `;
    
    // Add drag event listeners
    card.addEventListener('dragstart', handleDragStart);
    card.addEventListener('dragend', handleDragEnd);
    
    // Add button click handler
    const button = card.querySelector('button');
    button.addEventListener('click', () => {
        if (isSelected) {
            card.remove();
            showToast('Data point removed from selection', 'notice');
        } else {
            moveCardToSelected(card);
        }
    });
    
    return card;
}

// 3. Add separate drag event handlers
function handleDragStart(e) {
    e.dataTransfer.setData('text/plain', e.target.dataset.fieldId);
    this.classList.add('dragging');
}

function handleDragEnd(e) {
    this.classList.remove('dragging');
}

async function createDataPointsAccordion(dataPoints) {
    try {
        const entitiesResponse = await fetch('/admin/get_entities');
        const entities = await entitiesResponse.json();
        
        // Get existing assignment configurations
        const configResponse = await fetch('/admin/get_assignment_configurations');
        const configurations = await configResponse.json();

        dataPointsAccordion.innerHTML = dataPoints.map((dp, index) => {
            const fieldId = dp.field_id || dp.dataset?.fieldId;
            const currentAssignments = entityAssignments[fieldId] || [];
            const config = configurations[fieldId] || {};
            
            return `
            <div class="accordion-item" data-field-id="${fieldId}">
                <h2 class="accordion-header" id="heading${fieldId}">
                    <button class="accordion-button ${index === 0 ? '' : 'collapsed'}" 
                            type="button" 
                            data-bs-toggle="collapse" 
                            data-bs-target="#collapse${fieldId}"
                            aria-expanded="${index === 0 ? 'true' : 'false'}"
                            aria-controls="collapse${fieldId}">
                        ${dp.field_name || dp.querySelector('.dp-name').textContent}
                        ${config.frequency ? `<span class="frequency-badge ms-2">${config.frequency}</span>` : ''}
                    </button>
                </h2>
                <div id="collapse${fieldId}" 
                     class="accordion-collapse collapse ${index === 0 ? 'show' : ''}"
                     aria-labelledby="heading${fieldId}"
                     data-bs-parent="#dataPointsAccordion">
                    <div class="accordion-body">
                        <!-- FY and Frequency Configuration -->
                        <div class="fy-frequency-config">
                            <h5>Financial Year & Frequency Configuration</h5>
                            <div class="config-grid">
                                <div class="config-field">
                                    <label>FY Start Month:</label>
                                    <select class="fy-start-month" data-field-id="${fieldId}">
                                        <option value="1" ${config.fy_start_month === 1 ? 'selected' : ''}>January</option>
                                        <option value="4" ${config.fy_start_month === 4 || !config.fy_start_month ? 'selected' : ''}>April</option>
                                        <option value="7" ${config.fy_start_month === 7 ? 'selected' : ''}>July</option>
                                        <option value="10" ${config.fy_start_month === 10 ? 'selected' : ''}>October</option>
                                    </select>
                                </div>
                                <div class="config-field">
                                    <label>Frequency:</label>
                                    <select class="frequency-select" data-field-id="${fieldId}">
                                        <option value="Annual" ${config.frequency === 'Annual' || !config.frequency ? 'selected' : ''}>Annual</option>
                                        <option value="Quarterly" ${config.frequency === 'Quarterly' ? 'selected' : ''}>Quarterly</option>
                                        <option value="Monthly" ${config.frequency === 'Monthly' ? 'selected' : ''}>Monthly</option>
                                    </select>
                                </div>
                                <div class="config-field">
                                    <label>FY Start Year:</label>
                                    <input type="number" class="fy-start-year" data-field-id="${fieldId}" 
                                           value="${config.fy_start_year || new Date().getFullYear()}" 
                                           min="2020" max="2030">
                                </div>
                                <div class="config-field">
                                    <label>FY End Year:</label>
                                    <input type="number" class="fy-end-year" data-field-id="${fieldId}" 
                                           value="${config.fy_end_year || (new Date().getFullYear() + 1)}" 
                                           min="2020" max="2030">
                                </div>
                            </div>
                            ${config.fy_display ? `<div class="fy-display">Current FY: ${config.fy_display}</div>` : ''}
                        </div>
                        
                        <!-- Entity Assignment Section -->
                        <div class="entity-assignment-section">
                            <div class="entity-selector">
                                <label>Select Entities:</label>
                                <select multiple class="entity-select form-control" 
                                        data-field-id="${fieldId}">
                                    ${entities.map(entity => `
                                        <option value="${entity.id}" 
                                            ${currentAssignments.includes(entity.id.toString()) ? 'selected' : ''}>
                                            ${entity.name}
                                        </option>
                                    `).join('')}
                                </select>
                                <div class="selected-entities-count mt-2">
                                    Selected: <span>${currentAssignments.length}</span> entities
                                </div>
                            </div>
                            <div class="mt-3">
                                <button class="save-assignment-btn btn btn-primary" 
                                        data-field-id="${fieldId}">
                                    Save Assignment Configuration
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `}).join('');

        // Initialize Bootstrap collapse functionality
        const accordionItems = document.querySelectorAll('.accordion-collapse');
        accordionItems.forEach(item => {
            new bootstrap.Collapse(item, {
                toggle: false
            });
        });

        // Add event listeners
        setupAccordionEventListeners();
    } catch (error) {
        console.error('Error creating accordion:', error);
        showToast('Error creating data points display', 'error');
    }
}

function setupAccordionEventListeners() {
    // Add event listeners for entity selects
    document.querySelectorAll('.entity-select').forEach(select => {
        select.addEventListener('change', function() {
            const fieldId = this.dataset.fieldId;
            // Convert all entity IDs to strings for consistent comparison
            const selectedEntities = Array.from(this.selectedOptions).map(opt => opt.value.toString());
            
            // Update the entityAssignments state
            entityAssignments[fieldId] = selectedEntities;
            
            const count = selectedEntities.length;
            this.closest('.entity-selector')
                .querySelector('.selected-entities-count span')
                .textContent = count;
        });
    });

    // Add event listeners for save buttons
    document.querySelectorAll('.save-assignment-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const fieldId = this.dataset.fieldId;
            const selectedEntities = entityAssignments[fieldId] || [];
            
            // Get FY and frequency configuration values
            const accordionItem = this.closest('.accordion-item');
            const fyStartMonth = accordionItem.querySelector('.fy-start-month').value;
            const fyStartYear = accordionItem.querySelector('.fy-start-year').value;
            const fyEndYear = accordionItem.querySelector('.fy-end-year').value;
            const frequency = accordionItem.querySelector('.frequency-select').value;

            // Validate configuration
            if (!fyStartYear || !fyEndYear) {
                showToast('Please provide both FY start and end years', 'error');
                return;
            }
            
            if (parseInt(fyEndYear) <= parseInt(fyStartYear)) {
                showToast('FY end year must be greater than start year', 'error');
                return;
            }

            try {
                const response = await fetch('/admin/assign_data_points', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        data_point_id: fieldId,
                        entity_ids: selectedEntities,
                        fy_start_month: parseInt(fyStartMonth),
                        fy_start_year: parseInt(fyStartYear),
                        fy_end_year: parseInt(fyEndYear),
                        frequency: frequency
                    })
                });

                if (response.ok) {
                    showToast(`Successfully configured assignment with ${frequency} frequency for FY ${fyStartYear}-${fyEndYear}`, 'success');
                    
                    // Update the FY display
                    const monthNames = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                    const fyDisplay = `${monthNames[parseInt(fyStartMonth)]} ${fyStartYear} - ${monthNames[parseInt(fyStartMonth)]} ${fyEndYear}`;
                    
                    const fyDisplayDiv = accordionItem.querySelector('.fy-display');
                    if (fyDisplayDiv) {
                        fyDisplayDiv.textContent = `Current FY: ${fyDisplay}`;
                    } else {
                        // Create the display if it doesn't exist
                        const configSection = accordionItem.querySelector('.fy-frequency-config');
                        const newFyDisplay = document.createElement('div');
                        newFyDisplay.className = 'fy-display';
                        newFyDisplay.textContent = `Current FY: ${fyDisplay}`;
                        configSection.appendChild(newFyDisplay);
                    }
                    
                    // Update frequency badge in header
                    const accordionHeader = accordionItem.querySelector('.accordion-button');
                    const existingBadge = accordionHeader.querySelector('.frequency-badge');
                    if (existingBadge) {
                        existingBadge.textContent = frequency;
                    } else {
                        const badge = document.createElement('span');
                        badge.className = 'frequency-badge ms-2';
                        badge.textContent = frequency;
                        accordionHeader.appendChild(badge);
                    }
                } else {
                    const errorData = await response.json();
                    showToast(`Error: ${errorData.message}`, 'error');
                }
            } catch (error) {
                console.error('Error saving assignment configuration:', error);
                showToast('Error saving assignment configuration', 'error');
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const openAssignModalButton = document.getElementById('openAssignModal');
    const assignModal = document.getElementById('assignModal');
    const closeModalButtons = document.querySelectorAll('.close-modal');
    const confirmDataPointsButton = document.getElementById('confirmDataPoints');
    const selectedFields = document.getElementById('selectedFields');
    const dataPointsAccordion = document.getElementById('dataPointsAccordion');

    // Initialize PopupManager
    PopupManager.init();

    // Add framework select handler
    const frameworkSelect = document.getElementById('framework_select');
    const availableFields = document.getElementById('availableFields');

    frameworkSelect.addEventListener('change', async function() {
        const frameworkId = this.value;
        availableFields.innerHTML = ''; // Clear existing fields
        
        if (!frameworkId) {
            showToast('Framework selection cleared', 'notice');
            return;
        }

        try {
            const response = await fetch(`/admin/get_framework_fields/${frameworkId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch framework fields');
            }
            
            const fields = await response.json();
            
            if (fields.length === 0) {
                showToast('No data points available for this framework', 'notice');
                return;
            }
            
            showToast(`Loaded ${fields.length} data points`, 'success');

            // Filter out already selected fields
            const selectedFieldIds = Array.from(selectedFields.children)
                .map(card => card.dataset.fieldId);
            
            const availableFieldsData = fields.filter(field => 
                !selectedFieldIds.includes(field.field_id.toString()));

            // Create cards for available fields
            availableFieldsData.forEach(field => {
                const card = createDataPointCard(field, false);
                availableFields.appendChild(card);
                
                // Add drag event listeners explicitly
                card.addEventListener('dragstart', handleDragStart);
                card.addEventListener('dragend', handleDragEnd);
                
                // Add click handler for the add button
                const addButton = card.querySelector('.add-field');
                if (addButton) {
                    addButton.addEventListener('click', () => moveCardToSelected(card));
                }
            });

        } catch (error) {
            console.error('Error:', error);
            showToast('Error loading framework fields: ' + error.message, 'error');
        }
    });

    function moveCardToSelected(card) {
        // Create a clone of the card
        const clone = createDataPointCard({
            field_id: card.dataset.fieldId,
            field_name: card.querySelector('.dp-name').textContent
        }, true);
        
        // Add to selected fields
        selectedFields.appendChild(clone);
        
        // Remove original if it exists in available fields
        if (card.parentElement === availableFields) {
            card.remove();
        }
        
        showToast('Data point added to selection', 'success');
    }

    function setupDragAndDrop() {
        [availableFields, selectedFields].forEach(container => {
            container.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.currentTarget.classList.add('drag-over');
            });

            container.addEventListener('dragleave', (e) => {
                e.currentTarget.classList.remove('drag-over');
            });

            container.addEventListener('drop', (e) => {
                e.preventDefault();
                e.currentTarget.classList.remove('drag-over');
                const fieldId = e.dataTransfer.getData('text/plain');
                const draggedCard = document.querySelector(`[data-field-id="${fieldId}"]`);
                
                if (e.currentTarget === selectedFields) {
                    moveCardToSelected(draggedCard);
                }
            });
        });
    }

    // Function to open the modal
    function openModal() {
        assignModal.style.display = 'block';
    }

    // Function to close the modal
    function closeModal() {
        assignModal.style.display = 'none';
    }

    // Add event listener to open the modal
    openAssignModalButton.addEventListener('click', openModal);

    // Add event listeners to close the modal
    closeModalButtons.forEach(button => {
        button.addEventListener('click', closeModal);
    });

    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === assignModal) {
            closeModal();
        }
    });

    // Load existing data points when the page loads
    loadExistingDataPoints();

    // Confirm data points selection
    confirmDataPointsButton.addEventListener('click', async function() {
        const selectedDataPoints = Array.from(selectedFields.children);
        
        try {
            // Save the selected data points first
            const saveResponse = await fetch('/admin/save_data_points', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    field_ids: selectedDataPoints.map(dp => dp.dataset.fieldId)
                })
            });

            if (!saveResponse.ok) {
                throw new Error('Failed to save data points');
            }

            showToast('Data points saved successfully', 'success');

            // When removing data points
            const removedPoints = previousPoints.filter(p => !selectedDataPoints.includes(p));
            if (removedPoints.length > 0) {
                showToast(`Removed ${removedPoints.length} data point(s)`, 'notice');
            }

            // Continue with the existing code for entity assignments
            const entitiesResponse = await fetch('/admin/get_entities');
            const entities = await entitiesResponse.json();

            // Display selected data points as accordion panels
            dataPointsAccordion.innerHTML = selectedDataPoints.map((dp, index) => {
                const fieldId = dp.dataset.fieldId;
                const currentAssignments = entityAssignments[fieldId] || [];
                
                return `
                <div class="accordion-item" data-field-id="${fieldId}">
                    <h2 class="accordion-header" id="heading${fieldId}">
                        <button class="accordion-button ${index === 0 ? '' : 'collapsed'}" 
                                type="button" 
                                data-bs-toggle="collapse" 
                                data-bs-target="#collapse${fieldId}"
                                aria-expanded="${index === 0 ? 'true' : 'false'}"
                                aria-controls="collapse${fieldId}">
                            ${dp.querySelector('.dp-name').textContent}
                        </button>
                    </h2>
                    <div id="collapse${fieldId}" 
                         class="accordion-collapse collapse ${index === 0 ? 'show' : ''}"
                         aria-labelledby="heading${fieldId}"
                         data-bs-parent="#dataPointsAccordion">
                        <div class="accordion-body">
                            <div class="entity-assignment-section">
                                <div class="entity-selector">
                                    <label>Select Entities:</label>
                                    <select multiple class="entity-select form-control" 
                                            data-field-id="${fieldId}">
                                        ${entities.map(entity => `
                                            <option value="${entity.id}" 
                                                ${currentAssignments.includes(entity.id.toString()) ? 'selected' : ''}>
                                                ${entity.name}
                                            </option>
                                        `).join('')}
                                    </select>
                                    <div class="selected-entities-count mt-2">
                                        Selected: <span>${currentAssignments.length}</span> entities
                                    </div>
                                </div>
                                <div class="mt-3">
                                    <button class="save-assignment-btn btn btn-primary" 
                                            data-field-id="${fieldId}">
                                        Save Assignments
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `}).join('');

            // Initialize Bootstrap collapse functionality for all accordion items
            const accordionItems = document.querySelectorAll('.accordion-collapse');
            accordionItems.forEach(item => {
                new bootstrap.Collapse(item, {
                    toggle: false
                });
            });

            // Add event listeners for entity selects
            document.querySelectorAll('.entity-select').forEach(select => {
                select.addEventListener('change', function() {
                    const fieldId = this.dataset.fieldId;
                    const selectedEntities = Array.from(this.selectedOptions).map(opt => opt.value);
                    
                    // Update the entityAssignments state
                    entityAssignments[fieldId] = selectedEntities;
                    
                    const count = this.selectedOptions.length;
                    this.closest('.entity-selector')
                        .querySelector('.selected-entities-count span')
                        .textContent = count;
                });
            });

            // Add event listeners for save buttons
            document.querySelectorAll('.save-assignment-btn').forEach(btn => {
                btn.addEventListener('click', async function() {
                    const fieldId = this.dataset.fieldId;
                    const selectedEntities = entityAssignments[fieldId] || [];
                    
                    try {
                        const response = await fetch('/admin/assign_data_points', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                data_point_id: fieldId,
                                entity_ids: selectedEntities
                            })
                        });

                        if (response.ok) {
                            showToast(`Successfully assigned to ${selectedEntities.length} entities`, 'success');
                        }
                    } catch (error) {
                        showToast('Error saving assignments: ' + error.message, 'error');
                    }
                });
            });

            closeModal();
        } catch (error) {
            showToast('Error saving data points: ' + error.message, 'error');
            return;
        }
    });

    // Helper function to show toast messages
    function showToast(message, type = 'notice') {
        switch(type) {
            case 'success':
                PopupManager.showSuccess('Success', message);
                break;
            case 'error':
                PopupManager.showError('Error', message);
                break;
            case 'notice':
            default:
                PopupManager.showInfo('Notice', message);
        }
    }
});
