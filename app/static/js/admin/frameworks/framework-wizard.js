document.addEventListener('DOMContentLoaded', function() {
    // Wizard State Management
    const wizardState = {
        currentStep: 1,
        totalSteps: 4,
        formData: {
            basics: {},
            topics: [],
            dataPoints: [],
            settings: {}
        },
        draftId: null,
        isComplete: false
    };

    // Make wizardState globally accessible for other modules
    window.frameworkWizardState = wizardState;

    // DOM Elements
    const stepperItems = document.querySelectorAll('.stepper-item');
    const wizardSteps = document.querySelectorAll('.wizard-step');
    const nextBtn = document.getElementById('nextStep');
    const prevBtn = document.getElementById('prevStep');
    const skipBtn = document.getElementById('skipStep');
    const saveDraftBtn = document.getElementById('saveDraft');
    const publishBtn = document.getElementById('publishFramework');
    const closeWizardBtn = document.getElementById('closeWizard');

    // Form Elements
    const frameworkNameInput = document.getElementById('frameworkName');
    const frameworkSlugSpan = document.getElementById('frameworkSlug');
    const basicsForm = document.getElementById('basicsForm');

    // Data Point Elements (reuse from existing implementation)
    const dataPointDrawer = document.getElementById('dataPointDrawer');
    const drawerOverlay = document.getElementById('drawerOverlay');
    const addDataPointWizardBtn = document.getElementById('addDataPointWizard');
    const dataPointsWizardContainer = document.getElementById('dataPointsWizardContainer');
    const emptyDataPointsWizardState = document.getElementById('emptyDataPointsWizardState');

    // Initialize wizard
    initializeWizard();

    function initializeWizard() {
        // Check if we're in edit mode
        if (window.editMode && window.frameworkData) {
            initializeEditMode();
        } else {
            // Set today's date as default for new frameworks
            
            // Load any existing draft
            loadDraftIfExists();
        }

        // Initialize FrameworksTopics module for the wizard
        if (window.FrameworksTopics) {
            const frameworkId = wizardState.formData.framework_id || (window.editMode && window.frameworkData ? window.frameworkData.framework_id : null);
            window.FrameworksTopics.initialize(frameworkId, 'topicsWizardContainer', wizardState);
        }

        // Setup event listeners
        setupEventListeners();
        
        // Update stepper display
        updateStepperDisplay();
    }

    function setupEventListeners() {
        // Navigation buttons
        nextBtn.addEventListener('click', handleNextStep);
        prevBtn.addEventListener('click', handlePrevStep);
        skipBtn.addEventListener('click', handleSkipStep);
        saveDraftBtn.addEventListener('click', handleSaveDraft);
        publishBtn.addEventListener('click', handlePublishFramework);
        closeWizardBtn.addEventListener('click', handleCloseWizard);

        // Stepper navigation
        stepperItems.forEach(item => {
            item.addEventListener('click', function() {
                const targetStep = parseInt(this.getAttribute('data-step'));
                if (targetStep < wizardState.currentStep || this.classList.contains('completed')) {
                    goToStep(targetStep);
                }
            });
        });

        // Auto-slug generation
        frameworkNameInput.addEventListener('input', function() {
            const slug = generateSlug(this.value);
            frameworkSlugSpan.textContent = slug || 'will-be-generated';
        });

        // Form change tracking
        basicsForm.addEventListener('input', function() {
            saveBasicsData();
        });

        // Company-wide topics checkbox
        const useCompanyTopicsCheckbox = document.getElementById('useCompanyTopics');
        if (useCompanyTopicsCheckbox) {
            useCompanyTopicsCheckbox.addEventListener('change', function() {
                if (window.FrameworksTopics) {
                    window.FrameworksTopics.toggleCompanyTopics(this.checked);
                }
            });
        }

            // Data point management - use unified module
    addDataPointWizardBtn.addEventListener('click', function() {
        if (window.FrameworksDataPoints) {
            window.FrameworksDataPoints.setContext('wizard', wizardState);
            window.FrameworksDataPoints.openDataPointDrawer();
        }
    });

        // Template import - use unified module
        document.querySelectorAll('[data-template]').forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                const template = this.getAttribute('data-template');
                importTemplate(template);
            });
        });

        // Search functionality - use unified module
        const searchInput = document.getElementById('searchDataPoints');
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                if (window.FrameworksDataPoints && window.FrameworksDataPoints.filterDataPoints) {
                    window.FrameworksDataPoints.filterDataPoints(this.value);
                }
            });
        }

        // View toggle - wizard-specific
        document.querySelectorAll('[data-view]').forEach(btn => {
            btn.addEventListener('click', function() {
                const view = this.getAttribute('data-view');
                toggleDataPointsView(view);
                
                // Update active state
                document.querySelectorAll('[data-view]').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }

    async function handleNextStep() {
        if (validateCurrentStep()) {
            if (wizardState.currentStep === 1) {
                // Save basics and get or use framework_id
                saveBasicsData();

                // If framework_id already exists (edit mode), skip creation call
                if (wizardState.formData.framework_id) {
                    // Optionally we could update basics here, but for the wizard flow
                    // we just proceed to the next step.
                    goToStep(wizardState.currentStep + 1);
                    return;
                }

                try {
                    const response = await fetch('/admin/frameworks/create_initial', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            framework_name: wizardState.formData.basics.name,
                            description: wizardState.formData.basics.description
                        })
                    });
                    const data = await response.json();
                    if (data.success) {
                        wizardState.formData.framework_id = data.framework_id;
                        if (window.FrameworksTopics && window.FrameworksTopics.setFrameworkId) {
                            window.FrameworksTopics.setFrameworkId(data.framework_id);
                        }
                        showSuccessMessage('Framework draft saved!');
                        goToStep(wizardState.currentStep + 1);
                    } else {
                        alert('Error saving framework basics: ' + (data.error || 'Unknown error'));
                    }
                } catch (error) {
                    console.error('Error saving framework basics:', error);
                    alert('Error saving framework basics.');
                }
            } else if (wizardState.currentStep === 2) {
                // Save topics
                try {
                    const allTopics = window.FrameworksTopics.getTopics();
                    const unsavedTopics = allTopics.filter(t => !t.topic_id);
                    let proceedNext = true;
                    if (unsavedTopics.length > 0) {
                        const response = await fetch(`/admin/frameworks/add_topics/${wizardState.formData.framework_id}`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(unsavedTopics)
                        });
                        const data = await response.json();
                        if (data.success) {
                            showSuccessMessage('Topics saved!');
                            // Reload to ensure IDs assigned
                            if (window.FrameworksTopics && window.FrameworksTopics.setFrameworkId) {
                                window.FrameworksTopics.setFrameworkId(wizardState.formData.framework_id);
                            }
                        } else {
                            alert('Error saving topics: ' + (data.error || 'Unknown error'));
                            proceedNext = false;
                        }
                    }
                    if (proceedNext) {
                        goToStep(wizardState.currentStep + 1);
                    }
                } catch (error) {
                    console.error('Error saving topics:', error);
                    alert('Error saving topics.');
                }
            } else if (wizardState.currentStep === 3) {
                // Save data points
                try {
                    // Save only data points that don't have field_id yet (newly added)
                    const allPoints = window.FrameworksDataPoints.getDataPoints();
                    const unsaved = allPoints.filter(dp => !dp.field_id);
                    let proceed = true;
                    if (unsaved.length > 0) {
                        const response = await fetch(`/admin/frameworks/add_data_points/${wizardState.formData.framework_id}`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(unsaved)
                        });
                        const data = await response.json();
                        if (data.success) {
                            showSuccessMessage('Data points saved!');
                        } else {
                            alert('Error saving data points: ' + (data.error || 'Unknown error'));
                            proceed = false;
                        }
                    }
                    if (proceed) {
                        goToStep(wizardState.currentStep + 1);
                    }
                } catch (error) {
                    console.error('Error saving data points:', error);
                    alert('Error saving data points.');
                }
            } else {
                goToStep(wizardState.currentStep + 1);
            }
        }
    }

    function handlePrevStep() {
        if (wizardState.currentStep > 1) {
            goToStep(wizardState.currentStep - 1);
        }
    }

    function handleSkipStep() {
        // Only allow skipping step 2 (Topics)
        if (wizardState.currentStep === 2) {
            // Mark step as skipped
            const stepperItem = document.querySelector(`[data-step="2"]`);
            stepperItem.querySelector('.stepper-badge').classList.remove('d-none');
            
            goToStep(3);
        }
    }

    function handleSaveDraft() {
        saveDraft();
    }

    function handlePublishFramework() {
        if (validateAllSteps()) {
            publishFramework();
        }
    }

    function handleCloseWizard() {
        if (confirm('Are you sure you want to close the wizard? Any unsaved changes will be lost.')) {
            window.location.href = '/admin/frameworks';
        }
    }

    async function goToStep(stepNumber) {
        // Hide all steps
        wizardSteps.forEach(step => step.classList.remove('active'));
        
        // Show target step
        const targetStep = document.getElementById(`step-${stepNumber}`);
        if (targetStep) {
            wizardState.currentStep = stepNumber;
            targetStep.classList.add('active');
            
            updateStepperDisplay();
            updateNavigationButtons();
            
            // Step-specific actions
            if (stepNumber === 2) {
                // Fetch and display topics for the current framework
                if (wizardState.formData.framework_id && window.FrameworksTopics) {
                    try {
                        const response = await fetch(`/admin/frameworks/${wizardState.formData.framework_id}/topics`);
                        const data = await response.json();
                        const topicsArr = Array.isArray(data) ? data : (data.success ? data.topics : []);
                        wizardState.formData.topics = topicsArr;
                        window.FrameworksTopics.setTopics(topicsArr);
                        window.FrameworksTopics.refresh();
                        const emptyTopicsState = document.getElementById('emptyTopicsState');
                        if (emptyTopicsState) {
                            if (topicsArr.length > 0 || window.FrameworksTopics.getCustomTopics().length > 0) {
                                emptyTopicsState.classList.add('d-none');
                            } else {
                                emptyTopicsState.classList.remove('d-none');
                            }
                        }
                        // log if empty and error present in non-array payload
                        if (topicsArr.length === 0 && !Array.isArray(data) && data.error) {
                            console.error('Error fetching topics for step 2:', data.error);
                        }
                    } catch (error) {
                        console.error('Error fetching topics for step 2:', error);
                    }
                }
            } else if (stepNumber === 3) {
                // Fetch and display data points for the current framework
                if (wizardState.formData.framework_id && window.FrameworksDataPoints) {
                    try {
                        const response = await fetch(`/admin/frameworks/${wizardState.formData.framework_id}/data_points`);
                        const data = await response.json();
                        if (data.success) {
                            wizardState.formData.dataPoints = data.data_points.map(field => ({
                                id: field.field_id,
                                name: field.field_name,
                                field_code: field.field_code,
                                description: field.description,
                                value_type: field.value_type,
                                unit_category: field.unit_category,
                                default_unit: field.default_unit,
                                topic_id: field.topic_id,
                                is_computed: field.is_computed,
                                formula_expression: field.formula_expression
                            }));
                            window.FrameworksDataPoints.setContext('wizard', wizardState);
                            window.FrameworksDataPoints.setDataPoints(wizardState.formData.dataPoints);
                        } else {
                            console.error('Error fetching data points for step 3:', data.error);
                        }
                    } catch (error) {
                        console.error('Error fetching data points for step 3:', error);
                    }
                }
            } else if (stepNumber === 4) {
                populateReviewSection();
            }
        }
    }

    function updateStepperDisplay() {
        stepperItems.forEach((item, index) => {
            const stepNumber = index + 1;
            
            // Remove all classes
            item.classList.remove('active', 'completed');
            
            if (stepNumber < wizardState.currentStep) {
                item.classList.add('completed');
            } else if (stepNumber === wizardState.currentStep) {
                item.classList.add('active');
            }
        });
    }

    function updateNavigationButtons() {
        // Previous button
        prevBtn.style.display = wizardState.currentStep > 1 ? 'block' : 'none';
        
        // Skip button (only show on step 2)
        skipBtn.style.display = wizardState.currentStep === 2 ? 'block' : 'none';
        
        // Next/Publish buttons
        if (wizardState.currentStep === wizardState.totalSteps) {
            nextBtn.style.display = 'none';
            publishBtn.style.display = 'block';
        } else {
            nextBtn.style.display = 'block';
            publishBtn.style.display = 'none';
        }
    }

    function validateCurrentStep() {
        switch (wizardState.currentStep) {
            case 1:
                return validateBasicsStep();
            case 2:
                return true; // Topics are optional
            case 3:
                return validateDataPointsStep();
            case 4:
                return true; // Review step
            default:
                return true;
        }
    }

    function validateBasicsStep() {
        const name = document.getElementById('frameworkName').value.trim();
        
        if (!name) {
            showValidationError('frameworkName', 'Framework name is required');
            return false;
        }
        
        clearValidationError('frameworkName');
        return true;
    }

    function validateDataPointsStep() {
        if (wizardState.formData.dataPoints.length === 0) {
            alert('Please add at least one data point to your framework');
            return false;
        }
        return true;
    }

    function validateAllSteps() {
        // Validate all required steps before publishing
        saveBasicsData();
        return validateBasicsStep() && validateDataPointsStep();
    }

    function showValidationError(fieldId, message) {
        const field = document.getElementById(fieldId);
        field.classList.add('is-invalid');
        
        // Remove existing error message
        const existingError = field.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }
        
        // Add error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    function clearValidationError(fieldId) {
        const field = document.getElementById(fieldId);
        field.classList.remove('is-invalid');
        
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    function saveBasicsData() {
        wizardState.formData.basics = {
            name: document.getElementById('frameworkName').value.trim(),
            description: document.getElementById('frameworkDescription').value.trim(),
            category: null, // Removed from form
            effective_date: null, // Removed from form
            slug: generateSlug(document.getElementById('frameworkName').value)
        };
    }

    function generateSlug(text) {
        if (!text) return '';
        return text.toLowerCase()
            .replace(/[^a-zA-Z0-9\s-]/g, '')
            .replace(/[\s-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    // Data Points Management - using unified module
    // All data point functions now handled by FrameworksDataPoints module
    
    // Wizard-specific data point functions
    function toggleDataPointsView(view) {
        const container = dataPointsWizardContainer;
        
        if (view === 'list') {
            container.classList.add('list-view');
        } else {
            container.classList.remove('list-view');
        }
    }
    
    function importTemplate(templateKey) {
        // Show loading state
        const importBtn = document.querySelector(`[data-template="${templateKey}"]`);
        const originalText = importBtn.textContent;
        importBtn.textContent = 'Importing...';
        importBtn.disabled = true;
        
        fetch('/admin/import_template', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ template_key: templateKey })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data_points) {
                // Add imported data points to wizard state
                data.data_points.forEach(dp => {
                    dp.id = Date.now() + Math.random();
                    wizardState.formData.dataPoints.push(dp);
                });
                
                // Use unified module to render cards
                if (window.FrameworksDataPoints) {
                    window.FrameworksDataPoints.setContext('wizard', wizardState);
                    window.FrameworksDataPoints.setDataPoints(wizardState.formData.dataPoints);
                }
                
                alert(`Successfully imported ${data.data_points.length} data points from ${templateKey.toUpperCase()}`);
            } else {
                alert('Error importing template: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Import error:', error);
            alert('Error importing template');
        })
        .finally(() => {
            importBtn.textContent = originalText;
            importBtn.disabled = false;
        });
    }

    async function populateReviewSection() {
        const frameworkId = wizardState.formData.framework_id;
        if (!frameworkId) {
            console.error("Cannot populate review section: framework_id is missing.");
            return;
        }

        // Populate basics review
        const basicsContent = document.getElementById('reviewBasicsContent');
        const basics = wizardState.formData.basics;
        
        basicsContent.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <strong>Name:</strong> ${basics.name || 'Not specified'}
                </div>
                <div class="col-12 mt-2">
                    <strong>Description:</strong><br>
                    ${basics.description || 'No description provided'}
                </div>
                <div class="col-md-6 mt-2">
                    <strong>Slug:</strong> <code>${basics.slug || 'will-be-generated'}</code>
                </div>
            </div>
        `;
        
        // Fetch and populate topics review
        const topicsContent = document.getElementById('reviewTopicsContent');
        try {
            const topicsResponse = await fetch(`/admin/frameworks/${frameworkId}/topics`, { credentials: 'include' });
            const topicsData = await topicsResponse.json();
            const topics = Array.isArray(topicsData) ? topicsData : (topicsData.success ? topicsData.topics : []);
            document.getElementById('topicsCount').textContent = topics.length;
            if (topics.length === 0) {
                topicsContent.innerHTML = '<p class="text-muted">No topics added</p>';
            } else {
                const topicsList = topics.map(topic => 
                    `<div class="border-bottom pb-2 mb-2">
                        <strong>${topic.name}</strong>
                        ${topic.description ? `<br><small class="text-muted">${topic.description}</small>` : ''}
                    </div>`
                ).join('');
                topicsContent.innerHTML = topicsList;
            }
            // Log error if empty array and message available
            if (topics.length === 0 && !Array.isArray(topicsData) && topicsData.error) {
                console.error('Error fetching topics for review:', topicsData.error);
                topicsContent.innerHTML = '<p class="text-danger">Error loading topics.</p>';
            }
        } catch (error) {
            console.error('Error fetching topics for review:', error);
            topicsContent.innerHTML = '<p class="text-danger">Error loading topics.</p>';
        }

        // Fetch and populate data points review
        const dataPointsContent = document.getElementById('reviewDataPointsContent');
        try {
            const dataPointsResponse = await fetch(`/admin/frameworks/${frameworkId}/data_points`, { credentials: 'include' });
            const dataPointsData = await dataPointsResponse.json();
            if (dataPointsData.success) {
                const dataPoints = dataPointsData.data_points;
                document.getElementById('dataPointsCount').textContent = dataPoints.length;
                if (dataPoints.length === 0) {
                    dataPointsContent.innerHTML = '<p class="text-muted">No data points added</p>';
                } else {
                    const dataPointsList = dataPoints.map(dp => 
                        `<div class="border-bottom pb-2 mb-2">
                            <strong>${dp.field_name}</strong> <code>${dp.field_code}</code><br>
                            <small class="text-muted">${dp.value_type}${dp.unit_category ? ` • ${dp.unit_category}` : ''}${dp.is_computed ? ' • Computed' : ''}</small>
                        </div>`
                    ).join('');
                    dataPointsContent.innerHTML = dataPointsList;
                }
            } else {
                console.error('Error fetching data points for review:', dataPointsData.error);
                dataPointsContent.innerHTML = '<p class="text-danger">Error loading data points.</p>';
            }
        } catch (error) {
            console.error('Error fetching data points for review:', error);
            dataPointsContent.innerHTML = '<p class="text-danger">Error loading data points.</p>';
        }

        // Initialize Bootstrap accordion manually to fix collapse behavior
        setTimeout(() => {
            const accordionItems = document.querySelectorAll('#reviewAccordion .accordion-collapse');
            accordionItems.forEach(item => {
                // Destroy any existing collapse instance
                const existingCollapse = bootstrap.Collapse.getInstance(item);
                if (existingCollapse) {
                    existingCollapse.dispose();
                }
                // Create new collapse instance
                new bootstrap.Collapse(item, {
                    toggle: false
                });
            });
            console.log('Bootstrap accordion initialized for Step 4');
        }, 100);
    }

    function saveDraft() {
        saveBasicsData();
        
        const draftData = {
            basics: wizardState.formData.basics,
            step: wizardState.currentStep,
            framework_id: wizardState.formData.framework_id // Include framework_id if already created
        };
        
        fetch('/admin/frameworks/draft', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(draftData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                wizardState.draftId = data.draft_id;
                showSuccessMessage('Draft saved successfully');
            } else {
                alert('Error saving draft: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Save draft error:', error);
            alert('Error saving draft');
        });
    }

    async function publishFramework() {
        // Since data is saved incrementally, this function primarily confirms completion.
        // If there were any finalization steps (e.g., setting a 'published' flag), they would go here.
        // For now, we just show the success modal.
        showSuccessModal(window.editMode);
    }

    function showSuccessModal(isEditMode = false) {
        // Create and show success modal with confetti effect
        const modal = document.createElement('div');
        modal.className = 'modal fade show';
        modal.style.display = 'block';
        
        const title = isEditMode ? 'Framework Updated Successfully! ✅' : 'Framework Created Successfully! 🎉';
        const message = isEditMode ? 'Your framework changes have been saved.' : 'Your framework has been published and is ready to use.';
        const secondaryButton = isEditMode ? 'Continue Editing' : 'Create Another';
        const secondaryAction = isEditMode ? 'window.location.reload()' : 'window.location.reload()';
        
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content text-center">
                    <div class="modal-body py-5">
                        <div class="success-animation mb-4">
                            <i class="fas fa-check-circle text-success" style="font-size: 4rem;"></i>
                        </div>
                        <h3>${title}</h3>
                        <p class="text-muted">${message}</p>
                        <div class="mt-4">
                            <button type="button" class="btn btn-success" onclick="window.location.href='/admin/frameworks'">
                                View Frameworks
                            </button>
                            <button type="button" class="btn btn-outline-secondary ms-2" onclick="${secondaryAction}">
                                ${secondaryButton}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Add backdrop
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop fade show';
        document.body.appendChild(backdrop);
    }

    function showSuccessMessage(message) {
        // Create temporary success message
        const messageDiv = document.createElement('div');
        messageDiv.className = 'alert alert-success alert-dismissible position-fixed';
        messageDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        messageDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(messageDiv);
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 3000);
    }

    async function initializeEditMode() {
        const data = window.frameworkData;
        
        // Populate wizard state with existing basics data
        wizardState.formData.basics = {
            framework_id: data.framework_id,
            name: data.framework_name,
            description: data.description,
            created_at: data.created_at
        };

        // Expose framework_id at the root level of formData for later checks
        wizardState.formData.framework_id = data.framework_id;
        
        // Populate form fields
        document.getElementById('frameworkName').value = data.framework_name || '';
        document.getElementById('frameworkDescription').value = data.description || '';
        
        // Update slug display
        const slug = generateSlug(data.framework_name || '');
        document.getElementById('frameworkSlug').textContent = slug || 'will-be-generated';
        
        // Fetch topics and data points from backend
        try {
            const topicsResponse = await fetch(`/admin/frameworks/${data.framework_id}/topics`);
            const topicsData = await topicsResponse.json();
            const topicsArr = Array.isArray(topicsData) ? topicsData : (topicsData.success ? topicsData.topics : []);
            wizardState.formData.topics = topicsArr;
            if (window.FrameworksTopics) {
                window.FrameworksTopics.setTopics(topicsArr);
            }

            const dataPointsResponse = await fetch(`/admin/frameworks/${data.framework_id}/data_points`);
            const dataPointsData = await dataPointsResponse.json();
            if (dataPointsData.success) {
                wizardState.formData.dataPoints = dataPointsData.data_points.map(field => ({
                    id: field.field_id,
                    name: field.field_name,
                    field_code: field.field_code,
                    description: field.description,
                    value_type: field.value_type,
                    unit_category: field.unit_category,
                    default_unit: field.default_unit,
                    topic_id: field.topic_id,
                    is_computed: field.is_computed,
                    formula_expression: field.formula_expression
                }));
                if (window.FrameworksDataPoints) {
                    window.FrameworksDataPoints.setDataPoints(wizardState.formData.dataPoints);
                }
            }
        } catch (error) {
            console.error('Error fetching framework details for edit mode:', error);
            alert('Error loading framework details.');
        }
    }

    function loadDraftIfExists() {
        // Check URL for draft ID or load from localStorage
        const urlParams = new URLSearchParams(window.location.search);
        const draftId = urlParams.get('draft');
        
        if (draftId) {
            loadDraft(draftId);
        }
    }

    async function loadDraft(draftId) {
        try {
            const response = await fetch(`/admin/frameworks/draft/${draftId}`);
            const data = await response.json();
            if (data.success && data.draft) {
                wizardState.formData.basics = data.draft.basics || {};
                wizardState.formData.framework_id = data.draft.framework_id || null;
                wizardState.draftId = draftId;
                
                // Populate forms
                populateBasicsForm();
                
                // If framework_id exists, fetch topics and data points from backend
                if (wizardState.formData.framework_id) {
                    await window.FrameworksTopics.loadFrameworkTopics(wizardState.formData.framework_id);
                    await window.FrameworksDataPoints.fetchDataPoints(wizardState.formData.framework_id);
                }

                // Go to saved step
                if (data.draft.step) {
                    goToStep(data.draft.step);
                }
                
                showSuccessMessage('Draft loaded successfully');
            }
        } catch (error) {
            console.error('Load draft error:', error);
        }
    }

    function populateBasicsForm() {
        const basics = wizardState.formData.basics;
        if (basics) {
            document.getElementById('frameworkName').value = basics.name || '';
            document.getElementById('frameworkDescription').value = basics.description || '';
            // Removed category and effective_date fields
            
            if (basics.name) {
                frameworkSlugSpan.textContent = basics.slug || generateSlug(basics.name);
            }
        }
    }

    // Data point event listeners are now handled by unified module
    // FrameworksDataPoints module handles all drawer, form, and computed field interactions
}); 