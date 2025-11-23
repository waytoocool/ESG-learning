/**
 * Bug Report Chatbot Widget - Main Controller
 * Multi-step form for submitting bug reports with automatic data capture
 */

class ChatbotWidget {
    constructor() {
        this.isOpen = false;
        this.currentStep = 1;
        this.totalSteps = 4;
        this.formData = {
            category: null,
            severity: 'medium',
            title: '',
            description: '',
            steps_to_reproduce: '',
            expected_behavior: '',
            actual_behavior: '',
            screenshot: null,
            screenshot_annotations: null
        };
        this.init();
    }

    /**
     * Initialize the chatbot widget
     */
    init() {
        this.createWidget();
        this.attachEventListeners();
        this.loadFormState();
    }

    /**
     * Create the HTML structure for the widget
     */
    createWidget() {
        const widgetHTML = `
            <!-- Floating trigger button -->
            <button id="chatbot-trigger" class="chatbot-trigger" title="Report an issue or get help">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/>
                </svg>
                <span class="chatbot-badge hidden" id="chatbot-badge">1</span>
            </button>

            <!-- Chatbot container -->
            <div id="chatbot-container" class="chatbot-container hidden">
                <div class="chatbot-header">
                    <h3>Report an Issue</h3>
                    <button class="chatbot-close" id="chatbot-close">&times;</button>
                </div>
                <div class="chatbot-body" id="chatbot-body">
                    ${this.renderStep1()}
                    ${this.renderStep2()}
                    ${this.renderStep3()}
                    ${this.renderStep4()}
                </div>
                <div class="chatbot-footer">
                    <div class="chatbot-progress">
                        <div class="progress-bar" id="progress-bar" style="width: 25%;"></div>
                    </div>
                </div>
            </div>
        `;

        // Insert into DOM
        document.body.insertAdjacentHTML('beforeend', widgetHTML);
    }

    /**
     * Render Step 1: Category Selection
     */
    renderStep1() {
        return `
            <div class="form-step active" data-step="1">
                <h4>What would you like to report?</h4>
                <div class="category-grid">
                    <button class="category-card" data-category="bug">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M20 8h-2.81c-.45-.78-1.07-1.45-1.82-1.96L17 4.41 15.59 3l-2.17 2.17C12.96 5.06 12.49 5 12 5c-.49 0-.96.06-1.41.17L8.41 3 7 4.41l1.62 1.63C7.88 6.55 7.26 7.22 6.81 8H4v2h2.09c-.05.33-.09.66-.09 1v1H4v2h2v1c0 .34.04.67.09 1H4v2h2.81c1.04 1.79 2.97 3 5.19 3s4.15-1.21 5.19-3H20v-2h-2.09c.05-.33.09-.66.09-1v-1h2v-2h-2v-1c0-.34-.04-.67-.09-1H20V8zm-6 8h-4v-2h4v2zm0-4h-4v-2h4v2z"/>
                        </svg>
                        <span>Bug Report</span>
                        <p>Something isn't working</p>
                    </button>
                    <button class="category-card" data-category="feature_request">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M9 21c0 .5.4 1 1 1h4c.6 0 1-.5 1-1v-1H9v1zm3-19C8.1 2 5 5.1 5 9c0 2.4 1.2 4.5 3 5.7V17c0 .5.4 1 1 1h6c.6 0 1-.5 1-1v-2.3c1.8-1.3 3-3.4 3-5.7 0-3.9-3.1-7-7-7z"/>
                        </svg>
                        <span>Feature Request</span>
                        <p>Suggest an improvement</p>
                    </button>
                    <button class="category-card" data-category="help">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/>
                        </svg>
                        <span>Help</span>
                        <p>I need assistance</p>
                    </button>
                    <button class="category-card" data-category="other">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M6 10c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm12 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm-6 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
                        </svg>
                        <span>Other</span>
                        <p>Something else</p>
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Render Step 2: Severity Selection
     */
    renderStep2() {
        return `
            <div class="form-step" data-step="2">
                <h4>How severe is this issue?</h4>
                <div class="severity-list">
                    <label class="severity-option critical">
                        <input type="radio" name="severity" value="critical">
                        <div class="severity-content">
                            <strong>Critical</strong>
                            <p>System unusable, data loss, security issue</p>
                        </div>
                    </label>
                    <label class="severity-option high">
                        <input type="radio" name="severity" value="high">
                        <div class="severity-content">
                            <strong>High</strong>
                            <p>Major feature broken, blocking work</p>
                        </div>
                    </label>
                    <label class="severity-option medium">
                        <input type="radio" name="severity" value="medium" checked>
                        <div class="severity-content">
                            <strong>Medium</strong>
                            <p>Partial functionality affected</p>
                        </div>
                    </label>
                    <label class="severity-option low">
                        <input type="radio" name="severity" value="low">
                        <div class="severity-content">
                            <strong>Low</strong>
                            <p>Minor cosmetic issue</p>
                        </div>
                    </label>
                </div>
                <div class="form-actions">
                    <button class="btn-secondary" id="step2-back">Back</button>
                    <button class="btn-primary" id="step2-next">Next</button>
                </div>
            </div>
        `;
    }

    /**
     * Render Step 3: Issue Details
     */
    renderStep3() {
        return `
            <div class="form-step" data-step="3">
                <h4>Tell us about the issue</h4>
                <form id="issue-details-form">
                    <div class="form-group">
                        <label for="title">Title <span class="required">*</span></label>
                        <input type="text" id="title" class="form-control"
                               placeholder="Brief description of the issue" required>
                        <small class="form-hint">Keep it short and descriptive</small>
                        <small class="form-error hidden" id="title-error"></small>
                    </div>

                    <div class="form-group">
                        <label for="description">Description <span class="required">*</span></label>
                        <textarea id="description" class="form-control" rows="4"
                                  placeholder="Provide more details about the issue" required></textarea>
                        <small class="form-hint">What happened? What were you trying to do?</small>
                        <small class="form-error hidden" id="description-error"></small>
                    </div>

                    <div class="form-group">
                        <label for="steps">Steps to Reproduce</label>
                        <textarea id="steps" class="form-control" rows="3"
                                  placeholder="1. Go to...&#10;2. Click on...&#10;3. See error"></textarea>
                    </div>

                    <div class="form-group">
                        <label for="expected">Expected Behavior</label>
                        <textarea id="expected" class="form-control" rows="2"
                                  placeholder="What did you expect to happen?"></textarea>
                    </div>

                    <div class="form-group">
                        <label for="actual">Actual Behavior</label>
                        <textarea id="actual" class="form-control" rows="2"
                                  placeholder="What actually happened?"></textarea>
                    </div>

                    <div class="form-group">
                        <label>Screenshot (Optional)</label>
                        <button type="button" class="btn-screenshot" id="capture-screenshot-btn">
                            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <circle cx="12" cy="12" r="3.2"/>
                                <path d="M9 2L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-3.17L15 2H9zm3 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"/>
                            </svg>
                            Capture Screenshot
                        </button>
                        <div id="screenshot-preview" class="screenshot-preview hidden">
                            <img id="screenshot-img" src="" alt="Screenshot">
                            <button type="button" class="btn-remove" id="remove-screenshot-btn">Remove</button>
                        </div>
                    </div>
                </form>
                <div class="form-actions">
                    <button class="btn-secondary" id="step3-back">Back</button>
                    <button class="btn-primary" id="step3-next">Review</button>
                </div>
            </div>
        `;
    }

    /**
     * Render Step 4: Review & Submit
     */
    renderStep4() {
        return `
            <div class="form-step" data-step="4">
                <h4>Review Your Report</h4>
                <div class="review-section">
                    <div class="review-item">
                        <strong>Category:</strong>
                        <span id="review-category"></span>
                    </div>
                    <div class="review-item" id="review-severity-container">
                        <strong>Severity:</strong>
                        <span id="review-severity"></span>
                    </div>
                    <div class="review-item">
                        <strong>Title:</strong>
                        <span id="review-title"></span>
                    </div>
                    <div class="review-item">
                        <strong>Description:</strong>
                        <p id="review-description"></p>
                    </div>
                </div>

                <div class="debug-info-section">
                    <h5>Debugging Information Included:</h5>
                    <ul class="debug-info-list">
                        <li>✓ Browser information and version</li>
                        <li>✓ Current page URL</li>
                        <li id="console-errors-info">✓ <span id="console-error-count">0</span> console errors</li>
                        <li id="api-history-info">✓ <span id="api-call-count">0</span> recent API calls</li>
                        <li id="screenshot-info" class="hidden">✓ Screenshot attached</li>
                    </ul>
                    <small class="privacy-note">
                        ⓘ We do not capture passwords or sensitive personal information
                    </small>
                </div>

                <div class="form-actions">
                    <button class="btn-secondary" id="step4-back">Back</button>
                    <button class="btn-primary btn-submit" id="submit-btn">
                        <span class="btn-text">Submit Report</span>
                        <span class="btn-spinner hidden"></span>
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Trigger button
        document.getElementById('chatbot-trigger').addEventListener('click', () => {
            this.toggle();
        });

        // Close button
        document.getElementById('chatbot-close').addEventListener('click', () => {
            this.close();
        });

        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });

        // Category selection
        document.querySelectorAll('.category-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const category = e.currentTarget.dataset.category;
                this.selectCategory(category);
            });
        });

        // Step 2 buttons
        document.getElementById('step2-back').addEventListener('click', () => {
            this.goToStep(1);
        });
        document.getElementById('step2-next').addEventListener('click', () => {
            this.captureSeverity();
            this.goToStep(3);
        });

        // Severity radio buttons
        document.querySelectorAll('input[name="severity"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.formData.severity = radio.value;
            });
        });

        // Step 3 buttons
        document.getElementById('step3-back').addEventListener('click', () => {
            this.previousStep();
        });
        document.getElementById('step3-next').addEventListener('click', () => {
            if (this.validateStep3()) {
                this.captureFormData();
                this.populateReview();
                this.goToStep(4);
            }
        });

        // Screenshot buttons
        document.getElementById('capture-screenshot-btn').addEventListener('click', () => {
            this.captureScreenshot();
        });
        document.getElementById('remove-screenshot-btn').addEventListener('click', () => {
            this.removeScreenshot();
        });

        // Step 4 buttons
        document.getElementById('step4-back').addEventListener('click', () => {
            this.goToStep(3);
        });
        document.getElementById('submit-btn').addEventListener('click', () => {
            this.submitReport();
        });

        // Form inputs - auto-save
        const autoSaveFields = ['title', 'description', 'steps', 'expected', 'actual'];
        autoSaveFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.addEventListener('input', () => {
                    this.saveFormState();
                });
            }
        });

        // Scroll indicator
        const chatbotBody = document.getElementById('chatbot-body');
        if (chatbotBody) {
            chatbotBody.addEventListener('scroll', () => {
                this.updateScrollIndicator();
            });
        }
    }

    /**
     * Update scroll indicator based on scroll position
     */
    updateScrollIndicator() {
        const chatbotBody = document.getElementById('chatbot-body');
        if (!chatbotBody) return;

        const hasScroll = chatbotBody.scrollHeight > chatbotBody.clientHeight;
        const isAtBottom = chatbotBody.scrollHeight - chatbotBody.scrollTop <= chatbotBody.clientHeight + 5;

        if (hasScroll) {
            chatbotBody.classList.add('has-scroll');
        } else {
            chatbotBody.classList.remove('has-scroll');
        }

        if (isAtBottom) {
            chatbotBody.classList.add('scrolled-bottom');
        } else {
            chatbotBody.classList.remove('scrolled-bottom');
        }
    }

    /**
     * Toggle chatbot open/close
     */
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    /**
     * Open chatbot
     */
    open() {
        this.isOpen = true;
        const container = document.getElementById('chatbot-container');
        if (container) {
            container.classList.remove('hidden');
            container.classList.add('visible');
            // Check scroll state after opening
            setTimeout(() => this.updateScrollIndicator(), 100);
        } else {
            console.error('Chatbot container not found');
        }
    }

    /**
     * Close chatbot
     */
    close() {
        this.isOpen = false;
        const container = document.getElementById('chatbot-container');
        if (container) {
            container.classList.remove('visible');
            container.classList.add('hidden');
        } else {
            console.error('Chatbot container not found');
        }
        this.saveFormState();
    }

    /**
     * Go to a specific step
     */
    goToStep(step) {
        // Hide all steps
        document.querySelectorAll('.form-step').forEach(s => {
            s.classList.remove('active');
        });

        // Show target step
        const targetStep = document.querySelector(`[data-step="${step}"]`);
        if (targetStep) {
            targetStep.classList.add('active');
            this.currentStep = step;
            this.updateProgress();
            // Update scroll indicator after step change
            setTimeout(() => this.updateScrollIndicator(), 100);
        }
    }

    /**
     * Go to previous step
     */
    previousStep() {
        if (this.formData.category === 'bug') {
            this.goToStep(2);
        } else {
            this.goToStep(1);
        }
    }

    /**
     * Update progress bar
     */
    updateProgress() {
        const progress = (this.currentStep / this.totalSteps) * 100;
        document.getElementById('progress-bar').style.width = `${progress}%`;
    }

    /**
     * Select category
     */
    selectCategory(category) {
        this.formData.category = category;

        // Update UI
        document.querySelectorAll('.category-card').forEach(card => {
            card.classList.remove('selected');
        });

        const selectedCard = document.querySelector(`[data-category="${category}"]`);
        if (selectedCard) {
            selectedCard.classList.add('selected');
        } else {
            console.warn(`Category card not found for category: ${category}`);
        }

        // Navigate to next step
        setTimeout(() => {
            if (category === 'bug') {
                this.goToStep(2);
            } else {
                this.goToStep(3);
            }
        }, 300);
    }

    /**
     * Capture severity selection
     */
    captureSeverity() {
        const selectedSeverity = document.querySelector('input[name="severity"]:checked');
        if (selectedSeverity) {
            this.formData.severity = selectedSeverity.value;
        }
    }

    /**
     * Validate Step 3
     */
    validateStep3() {
        const title = document.getElementById('title').value.trim();
        const description = document.getElementById('description').value.trim();
        let isValid = true;

        // Clear previous errors
        document.getElementById('title-error').classList.add('hidden');
        document.getElementById('description-error').classList.add('hidden');
        document.getElementById('title').classList.remove('error');
        document.getElementById('description').classList.remove('error');

        if (!title) {
            this.showError('title', 'Title is required');
            isValid = false;
        } else if (title.length < 10) {
            this.showError('title', 'Title must be at least 10 characters');
            isValid = false;
        }

        if (!description) {
            this.showError('description', 'Description is required');
            isValid = false;
        } else if (description.length < 20) {
            this.showError('description', 'Please provide more details (at least 20 characters)');
            isValid = false;
        }

        return isValid;
    }

    /**
     * Show validation error
     */
    showError(fieldId, message) {
        const errorElement = document.getElementById(`${fieldId}-error`);
        const fieldElement = document.getElementById(fieldId);

        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.remove('hidden');
        }
        if (fieldElement) {
            fieldElement.classList.add('error');
        }
    }

    /**
     * Capture form data
     */
    captureFormData() {
        this.formData.title = document.getElementById('title').value.trim();
        this.formData.description = document.getElementById('description').value.trim();
        this.formData.steps_to_reproduce = document.getElementById('steps').value.trim();
        this.formData.expected_behavior = document.getElementById('expected').value.trim();
        this.formData.actual_behavior = document.getElementById('actual').value.trim();
    }

    /**
     * Populate review step
     */
    populateReview() {
        // Category
        const categoryLabels = {
            'bug': 'Bug Report',
            'feature_request': 'Feature Request',
            'help': 'Help',
            'other': 'Other'
        };
        document.getElementById('review-category').textContent = categoryLabels[this.formData.category] || this.formData.category;

        // Severity
        if (this.formData.category === 'bug') {
            document.getElementById('review-severity').textContent = this.formData.severity.toUpperCase();
            document.getElementById('review-severity-container').style.display = 'block';
        } else {
            document.getElementById('review-severity-container').style.display = 'none';
        }

        // Title and description
        document.getElementById('review-title').textContent = this.formData.title;
        document.getElementById('review-description').textContent = this.formData.description;

        // Debug info counts
        const debugData = window.bugReportDataCapture.getData();
        document.getElementById('console-error-count').textContent = debugData.consoleErrors.length;
        document.getElementById('api-call-count').textContent = debugData.apiHistory.length;

        // Screenshot
        if (this.formData.screenshot) {
            document.getElementById('screenshot-info').classList.remove('hidden');
        } else {
            document.getElementById('screenshot-info').classList.add('hidden');
        }
    }

    /**
     * Capture screenshot
     */
    captureScreenshot() {
        if (window.screenshotCapture) {
            window.screenshotCapture.capture();
        } else {
            alert('Screenshot feature is not available');
        }
    }

    /**
     * Set screenshot (called by screenshot service)
     */
    setScreenshot(screenshotData, annotations) {
        this.formData.screenshot = screenshotData;
        this.formData.screenshot_annotations = annotations;

        // Show preview
        const preview = document.getElementById('screenshot-preview');
        const img = document.getElementById('screenshot-img');
        img.src = screenshotData;
        preview.classList.remove('hidden');
    }

    /**
     * Remove screenshot
     */
    removeScreenshot() {
        this.formData.screenshot = null;
        this.formData.screenshot_annotations = null;
        document.getElementById('screenshot-preview').classList.add('hidden');
    }

    /**
     * Submit report
     */
    async submitReport() {
        const submitBtn = document.getElementById('submit-btn');

        if (!submitBtn) {
            console.error('Submit button not found');
            return;
        }

        submitBtn.disabled = true;

        // Get button state elements with null checks
        const btnText = submitBtn.querySelector('.btn-text');
        const btnSpinner = submitBtn.querySelector('.btn-spinner');

        if (btnText) {
            btnText.classList.add('hidden');
        } else {
            console.warn('Button text element not found');
        }

        if (btnSpinner) {
            btnSpinner.classList.remove('hidden');
        } else {
            console.warn('Button spinner element not found');
        }

        try {
            // Collect all data
            const debugData = window.bugReportDataCapture.getData();

            const reportData = {
                category: this.formData.category,
                severity: this.formData.severity,
                title: this.formData.title,
                description: this.formData.description,
                steps_to_reproduce: this.formData.steps_to_reproduce,
                expected_behavior: this.formData.expected_behavior,
                actual_behavior: this.formData.actual_behavior,

                // Debug data
                browser_info: debugData.browserInfo,
                page_url: debugData.pageUrl,
                page_title: debugData.pageTitle,
                viewport_size: debugData.browserInfo.viewportSize,
                screen_resolution: debugData.browserInfo.screenResolution,
                console_errors: debugData.consoleErrors,
                api_history: debugData.apiHistory,
                user_actions: debugData.userActions,

                // Screenshot
                screenshot_data: this.formData.screenshot,
                screenshot_annotations: this.formData.screenshot_annotations
            };

            // Submit to API
            const response = await fetch('/api/support/report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(reportData)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.showSuccessMessage(result.ticket_number);
                this.reset();
                setTimeout(() => {
                    this.close();
                }, 3000);
            } else {
                this.showErrorMessage(result.message || 'Failed to submit report');
            }

        } catch (error) {
            console.error('Submission error:', error);
            this.showErrorMessage('Network error. Please try again.');
        } finally {
            submitBtn.disabled = false;

            // Restore button state with null checks
            if (btnText) {
                btnText.classList.remove('hidden');
            }

            if (btnSpinner) {
                btnSpinner.classList.add('hidden');
            }
        }
    }

    /**
     * Show success message
     */
    showSuccessMessage(ticketNumber) {
        const container = document.getElementById('chatbot-body');
        container.innerHTML = `
            <div class="success-message">
                <svg class="success-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                <h3>Thank You!</h3>
                <p>Your issue has been reported successfully.</p>
                <div class="ticket-number-box">
                    <strong>Ticket Number:</strong>
                    <code>${ticketNumber}</code>
                </div>
                <p class="success-note">
                    You will receive a confirmation email shortly with your ticket details.
                </p>
            </div>
        `;
    }

    /**
     * Show error message
     */
    showErrorMessage(message) {
        const body = document.getElementById('chatbot-body');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <svg class="error-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
            </svg>
            <p>${message}</p>
        `;
        body.insertBefore(errorDiv, body.firstChild);

        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    /**
     * Save form state to localStorage
     */
    saveFormState() {
        try {
            localStorage.setItem('chatbot_form_state', JSON.stringify(this.formData));
        } catch (e) {
            console.error('Failed to save form state:', e);
        }
    }

    /**
     * Load form state from localStorage
     */
    loadFormState() {
        try {
            const savedState = localStorage.getItem('chatbot_form_state');
            if (savedState) {
                const state = JSON.parse(savedState);

                // Restore form fields
                if (state.title) document.getElementById('title').value = state.title;
                if (state.description) document.getElementById('description').value = state.description;
                if (state.steps_to_reproduce) document.getElementById('steps').value = state.steps_to_reproduce;
                if (state.expected_behavior) document.getElementById('expected').value = state.expected_behavior;
                if (state.actual_behavior) document.getElementById('actual').value = state.actual_behavior;
            }
        } catch (e) {
            console.error('Failed to load form state:', e);
        }
    }

    /**
     * Reset form
     */
    reset() {
        this.formData = {
            category: null,
            severity: 'medium',
            title: '',
            description: '',
            steps_to_reproduce: '',
            expected_behavior: '',
            actual_behavior: '',
            screenshot: null,
            screenshot_annotations: null
        };

        localStorage.removeItem('chatbot_form_state');

        // Reset to step 1
        this.goToStep(1);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if user is authenticated
    const body = document.body;
    const isAuthenticated = body.dataset.authenticated === 'true' ||
                           document.querySelector('.user-info') !== null;

    if (isAuthenticated) {
        window.bugReportChatbot = new ChatbotWidget();
    }
});
