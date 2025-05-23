// 1. Add tracking of previous points
let previousPoints = [];

async function loadExistingDataPoints() {
    try {
        const [dataPointsResponse, assignmentsResponse] = await Promise.all([
            fetch('/admin/get_existing_data_points'),
            fetch('/admin/get_data_point_assignments')
        ]);
        
        const existingPoints = await dataPointsResponse.json();
        const assignments = await assignmentsResponse.json();
        
        // Store previous points for comparison later
        previousPoints = existingPoints;
        
        // Clear existing content
        selectedFields.innerHTML = '';
        
        // Populate the selected fields
        existingPoints.forEach(point => {
            const card = createDataPointCard(point, true); // true indicates it's in selected area
            selectedFields.appendChild(card);
        });

        // Then, create the accordion with assignments
        await createDataPointsAccordion(existingPoints, assignments);
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

async function createDataPointsAccordion(dataPoints, assignments) {
    try {
        const entitiesResponse = await fetch('/admin/get_entities');
        const entities = await entitiesResponse.json();

        dataPointsAccordion.innerHTML = dataPoints.map((dp, index) => `
            <div class="accordion-item" data-field-id="${dp.field_id}">
                <h2 class="accordion-header" id="heading${dp.field_id}">
                    <button class="accordion-button ${index === 0 ? '' : 'collapsed'}" 
                            type="button" 
                            data-bs-toggle="collapse" 
                            data-bs-target="#collapse${dp.field_id}"
                            aria-expanded="${index === 0 ? 'true' : 'false'}"
                            aria-controls="collapse${dp.field_id}">
                        ${dp.field_name}
                    </button>
                </h2>
                <div id="collapse${dp.field_id}" 
                     class="accordion-collapse collapse ${index === 0 ? 'show' : ''}"
                     aria-labelledby="heading${dp.field_id}"
                     data-bs-parent="#dataPointsAccordion">
                    <div class="accordion-body">
                        <div class="entity-assignment-section">
                            <div class="entity-selector">
                                <label>Select Entities:</label>
                                <select multiple class="entity-select form-control" 
                                        data-field-id="${dp.field_id}">
                                    ${entities.map(entity => `
                                        <option value="${entity.id}" ${assignments[dp.field_id]?.includes(entity.id) ? 'selected' : ''}>
                                            ${entity.name}
                                        </option>
                                    `).join('')}
                                </select>
                                <div class="selected-entities-count mt-2">
                                    Selected: <span>${assignments[dp.field_id]?.length || 0}</span> entities
                                </div>
                            </div>
                            <div class="mt-3">
                                <button class="save-assignment-btn btn btn-primary" 
                                        data-field-id="${dp.field_id}">
                                    Save Assignments
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

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
            const entitySelect = document.querySelector(`.entity-select[data-field-id="${fieldId}"]`);
            const selectedEntities = Array.from(entitySelect.selectedOptions).map(opt => opt.value);

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
                    showToast('Assignments saved successfully!', 'success');
                }
            } catch (error) {
                console.error('Error saving assignments:', error);
                showToast('Error saving assignments', 'error');
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
            dataPointsAccordion.innerHTML = selectedDataPoints.map((dp, index) => `
                <div class="accordion-item" data-field-id="${dp.dataset.fieldId}">
                    <h2 class="accordion-header" id="heading${dp.dataset.fieldId}">
                        <button class="accordion-button ${index === 0 ? '' : 'collapsed'}" 
                                type="button" 
                                data-bs-toggle="collapse" 
                                data-bs-target="#collapse${dp.dataset.fieldId}"
                                aria-expanded="${index === 0 ? 'true' : 'false'}"
                                aria-controls="collapse${dp.dataset.fieldId}">
                            ${dp.querySelector('.dp-name').textContent}
                        </button>
                    </h2>
                    <div id="collapse${dp.dataset.fieldId}" 
                         class="accordion-collapse collapse ${index === 0 ? 'show' : ''}"
                         aria-labelledby="heading${dp.dataset.fieldId}"
                         data-bs-parent="#dataPointsAccordion">
                        <div class="accordion-body">
                            <div class="entity-assignment-section">
                                <div class="entity-selector">
                                    <label>Select Entities:</label>
                                    <select multiple class="entity-select form-control" 
                                            data-field-id="${dp.dataset.fieldId}">
                                        ${entities.map(entity => `
                                            <option value="${entity.id}">${entity.name}</option>
                                        `).join('')}
                                    </select>
                                    <div class="selected-entities-count mt-2">
                                        Selected: <span>0</span> entities
                                    </div>
                                </div>
                                <div class="mt-3">
                                    <button class="save-assignment-btn btn btn-primary" 
                                            data-field-id="${dp.dataset.fieldId}">
                                        Save Assignments
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');

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
                    const entitySelect = document.querySelector(`.entity-select[data-field-id="${fieldId}"]`);
                    const selectedEntities = Array.from(entitySelect.selectedOptions);
                    
                    try {
                        const response = await fetch('/admin/assign_data_points', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                data_point_id: fieldId,
                                entity_ids: selectedEntities.map(opt => opt.value)
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
        let title;
        switch(type) {
            case 'success':
                title = 'Success';
                break;
            case 'error':
                title = 'Error';
                break;
            default:
                title = 'Notice';
        }
        PopupManager.showPopup(title, message, type);
    }
});
