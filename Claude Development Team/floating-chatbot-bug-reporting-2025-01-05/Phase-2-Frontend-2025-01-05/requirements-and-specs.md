# Phase 2: Frontend Development - Requirements & Specifications

**Phase:** Frontend Development
**Start Date:** 2025-01-05
**Duration:** 2 days
**Dependencies:** Phase 1 (Backend) must be complete
**Risk Level:** Medium

## Phase Objectives

Implement the complete frontend user interface for the bug reporting chatbot, including the floating widget, multi-step form, data capture mechanisms, and screenshot functionality.

## Deliverables

1. Floating chatbot widget UI
2. Multi-step report form
3. Automatic data capture system
4. Screenshot capture and annotation tools
5. Integration with backend API

## Detailed Requirements

### 1. Floating Chatbot Widget (`app/static/css/chatbot.css`, `app/static/js/chatbot/chatbot.js`)

#### 1.1 Widget UI Components

**HTML Structure:**
```html
<!-- Floating trigger button -->
<button id="chatbot-trigger" class="chatbot-trigger">
    <svg><!-- Bug icon --></svg>
    <span class="chatbot-badge" id="chatbot-badge"></span>
</button>

<!-- Chatbot container -->
<div id="chatbot-container" class="chatbot-container hidden">
    <div class="chatbot-header">
        <h3>Report an Issue</h3>
        <button class="chatbot-close">×</button>
    </div>
    <div class="chatbot-body">
        <!-- Multi-step form will be inserted here -->
    </div>
    <div class="chatbot-footer">
        <div class="chatbot-progress">
            <div class="progress-bar"></div>
        </div>
    </div>
</div>
```

**CSS Requirements:**
```css
/* Positioning */
.chatbot-trigger {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9998;
    /* Circular button with shadow */
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.chatbot-container {
    position: fixed;
    bottom: 100px;
    right: 20px;
    width: 400px;
    max-height: 600px;
    z-index: 9999;
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

/* Responsive design */
@media (max-width: 768px) {
    .chatbot-container {
        width: calc(100vw - 40px);
        max-height: calc(100vh - 140px);
        right: 20px;
        left: 20px;
    }
}
```

**JavaScript Behavior:**
```javascript
class ChatbotWidget {
    constructor() {
        this.isOpen = false;
        this.currentStep = 1;
        this.formData = {};
        this.init();
    }

    init() {
        this.createWidget();
        this.attachEventListeners();
        this.initDataCapture();
    }

    createWidget() {
        // Create and inject HTML structure
    }

    toggle() {
        this.isOpen = !this.isOpen;
        // Smooth animation
        // If opening, initialize form
    }

    close() {
        // Save form state to localStorage
        // Animate close
    }

    attachEventListeners() {
        // Trigger button click
        // Close button click
        // Form navigation
        // Escape key to close
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.bugReportChatbot = new ChatbotWidget();
});
```

#### 1.2 Animations

**Requirements:**
- Smooth fade-in/out for container (300ms)
- Bounce effect on trigger button (subtle)
- Progress bar smooth transitions
- Form step transitions (slide left/right)

**CSS Transitions:**
```css
.chatbot-container {
    transition: opacity 0.3s ease, transform 0.3s ease;
    transform-origin: bottom right;
}

.chatbot-container.hidden {
    opacity: 0;
    transform: scale(0.95);
    pointer-events: none;
}

.chatbot-container.visible {
    opacity: 1;
    transform: scale(1);
}

.chatbot-trigger {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.chatbot-trigger:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}
```

### 2. Multi-Step Form (`app/static/js/chatbot/form-steps.js`)

#### 2.1 Step 1: Category Selection

**HTML:**
```html
<div class="form-step" data-step="1">
    <h4>What would you like to report?</h4>
    <div class="category-grid">
        <button class="category-card" data-category="bug">
            <svg><!-- Bug icon --></svg>
            <span>Bug Report</span>
            <p>Something isn't working</p>
        </button>
        <button class="category-card" data-category="feature_request">
            <svg><!-- Lightbulb icon --></svg>
            <span>Feature Request</span>
            <p>Suggest an improvement</p>
        </button>
        <button class="category-card" data-category="help">
            <svg><!-- Question icon --></svg>
            <span>Help</span>
            <p>I need assistance</p>
        </button>
        <button class="category-card" data-category="other">
            <svg><!-- Other icon --></svg>
            <span>Other</span>
            <p>Something else</p>
        </button>
    </div>
</div>
```

**JavaScript Logic:**
```javascript
selectCategory(category) {
    this.formData.category = category;

    // Only show severity step for bugs
    if (category === 'bug') {
        this.goToStep(2);
    } else {
        this.goToStep(3); // Skip severity for non-bugs
    }
}
```

#### 2.2 Step 2: Severity Selection (Bugs Only)

**HTML:**
```html
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
        <button class="btn-secondary" onclick="chatbot.goToStep(1)">Back</button>
        <button class="btn-primary" onclick="chatbot.goToStep(3)">Next</button>
    </div>
</div>
```

#### 2.3 Step 3: Issue Details

**HTML:**
```html
<div class="form-step" data-step="3">
    <h4>Tell us about the issue</h4>
    <form id="issue-details-form">
        <div class="form-group">
            <label for="title">Title <span class="required">*</span></label>
            <input type="text" id="title" class="form-control"
                   placeholder="Brief description of the issue" required>
            <small class="form-hint">Keep it short and descriptive</small>
        </div>

        <div class="form-group">
            <label for="description">Description <span class="required">*</span></label>
            <textarea id="description" class="form-control" rows="4"
                      placeholder="Provide more details about the issue" required></textarea>
            <small class="form-hint">What happened? What were you trying to do?</small>
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
            <button type="button" class="btn-screenshot" onclick="chatbot.captureScreenshot()">
                <svg><!-- Camera icon --></svg>
                Capture Screenshot
            </button>
            <div id="screenshot-preview" class="screenshot-preview hidden">
                <img id="screenshot-img" src="" alt="Screenshot">
                <button type="button" class="btn-remove" onclick="chatbot.removeScreenshot()">Remove</button>
            </div>
        </div>
    </form>
    <div class="form-actions">
        <button class="btn-secondary" onclick="chatbot.previousStep()">Back</button>
        <button class="btn-primary" onclick="chatbot.goToStep(4)">Review</button>
    </div>
</div>
```

**Validation Logic:**
```javascript
validateStep3() {
    const title = document.getElementById('title').value.trim();
    const description = document.getElementById('description').value.trim();

    if (!title) {
        this.showError('title', 'Title is required');
        return false;
    }

    if (title.length < 10) {
        this.showError('title', 'Title must be at least 10 characters');
        return false;
    }

    if (!description) {
        this.showError('description', 'Description is required');
        return false;
    }

    if (description.length < 20) {
        this.showError('description', 'Please provide more details (at least 20 characters)');
        return false;
    }

    return true;
}
```

#### 2.4 Step 4: Review & Submit

**HTML:**
```html
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
        <button class="btn-secondary" onclick="chatbot.goToStep(3)">Back</button>
        <button class="btn-primary btn-submit" onclick="chatbot.submitReport()">
            <span class="btn-text">Submit Report</span>
            <span class="btn-spinner hidden">Submitting...</span>
        </button>
    </div>
</div>
```

**Review Population:**
```javascript
populateReview() {
    document.getElementById('review-category').textContent =
        this.formData.category.replace('_', ' ').toUpperCase();

    if (this.formData.severity) {
        document.getElementById('review-severity').textContent =
            this.formData.severity.toUpperCase();
    } else {
        document.getElementById('review-severity-container').style.display = 'none';
    }

    document.getElementById('review-title').textContent = this.formData.title;
    document.getElementById('review-description').textContent = this.formData.description;

    // Update debug info counts
    const consoleErrors = this.debugData.consoleErrors || [];
    const apiHistory = this.debugData.apiHistory || [];

    document.getElementById('console-error-count').textContent = consoleErrors.length;
    document.getElementById('api-call-count').textContent = apiHistory.length;

    if (this.formData.screenshot) {
        document.getElementById('screenshot-info').classList.remove('hidden');
    }
}
```

### 3. Automatic Data Capture (`app/static/js/chatbot/data-capture.js`)

#### 3.1 Browser Information

```javascript
class DataCaptureService {
    constructor() {
        this.data = {
            browserInfo: {},
            consoleErrors: [],
            apiHistory: [],
            userActions: []
        };
        this.init();
    }

    init() {
        this.captureBrowserInfo();
        this.setupConsoleMonitoring();
        this.setupAPIMonitoring();
        this.setupUserActionTracking();
    }

    captureBrowserInfo() {
        const nav = navigator;
        this.data.browserInfo = {
            userAgent: nav.userAgent,
            platform: nav.platform,
            language: nav.language,
            languages: nav.languages,
            cookieEnabled: nav.cookieEnabled,
            onLine: nav.onLine,
            screenWidth: screen.width,
            screenHeight: screen.height,
            screenResolution: `${screen.width}x${screen.height}`,
            viewportWidth: window.innerWidth,
            viewportHeight: window.innerHeight,
            viewportSize: `${window.innerWidth}x${window.innerHeight}`,
            colorDepth: screen.colorDepth,
            pixelRatio: window.devicePixelRatio,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            timezoneOffset: new Date().getTimezoneOffset()
        };

        // Parse user agent for browser name and version
        const ua = nav.userAgent;
        let browserName = 'Unknown';
        let browserVersion = 'Unknown';

        if (ua.indexOf('Firefox') > -1) {
            browserName = 'Firefox';
            browserVersion = ua.match(/Firefox\/([0-9.]+)/)?.[1] || 'Unknown';
        } else if (ua.indexOf('Chrome') > -1) {
            browserName = 'Chrome';
            browserVersion = ua.match(/Chrome\/([0-9.]+)/)?.[1] || 'Unknown';
        } else if (ua.indexOf('Safari') > -1) {
            browserName = 'Safari';
            browserVersion = ua.match(/Version\/([0-9.]+)/)?.[1] || 'Unknown';
        } else if (ua.indexOf('Edge') > -1) {
            browserName = 'Edge';
            browserVersion = ua.match(/Edge\/([0-9.]+)/)?.[1] || 'Unknown';
        }

        this.data.browserInfo.name = browserName;
        this.data.browserInfo.version = browserVersion;
    }

    setupConsoleMonitoring() {
        // Store original console methods
        const originalError = console.error;
        const originalWarn = console.warn;

        // Override console.error
        console.error = (...args) => {
            this.captureConsoleError('error', args);
            originalError.apply(console, args);
        };

        // Override console.warn
        console.warn = (...args) => {
            this.captureConsoleError('warning', args);
            originalWarn.apply(console, args);
        };

        // Listen for unhandled errors
        window.addEventListener('error', (event) => {
            this.captureConsoleError('error', [event.message], {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });

        // Listen for unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.captureConsoleError('error', [event.reason]);
        });
    }

    captureConsoleError(level, args, metadata = {}) {
        const errorEntry = {
            level: level,
            message: args.map(arg =>
                typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
            ).join(' '),
            timestamp: new Date().toISOString(),
            ...metadata
        };

        this.data.consoleErrors.push(errorEntry);

        // Keep only last 50 errors
        if (this.data.consoleErrors.length > 50) {
            this.data.consoleErrors.shift();
        }
    }

    setupAPIMonitoring() {
        // Intercept fetch
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const startTime = Date.now();
            const url = typeof args[0] === 'string' ? args[0] : args[0].url;
            const method = args[1]?.method || 'GET';

            try {
                const response = await originalFetch(...args);
                const endTime = Date.now();

                this.captureAPICall({
                    url: url,
                    method: method,
                    status: response.status,
                    statusText: response.statusText,
                    duration: endTime - startTime,
                    timestamp: new Date().toISOString(),
                    success: response.ok
                });

                return response;
            } catch (error) {
                const endTime = Date.now();

                this.captureAPICall({
                    url: url,
                    method: method,
                    status: 0,
                    statusText: error.message,
                    duration: endTime - startTime,
                    timestamp: new Date().toISOString(),
                    success: false,
                    error: error.message
                });

                throw error;
            }
        };

        // Intercept XMLHttpRequest
        const originalOpen = XMLHttpRequest.prototype.open;
        const originalSend = XMLHttpRequest.prototype.send;

        XMLHttpRequest.prototype.open = function(method, url, ...args) {
            this._captureData = { method, url, startTime: Date.now() };
            return originalOpen.apply(this, [method, url, ...args]);
        };

        XMLHttpRequest.prototype.send = function(...args) {
            const captureData = this._captureData;

            this.addEventListener('loadend', () => {
                if (captureData) {
                    window.bugReportDataCapture.captureAPICall({
                        url: captureData.url,
                        method: captureData.method,
                        status: this.status,
                        statusText: this.statusText,
                        duration: Date.now() - captureData.startTime,
                        timestamp: new Date().toISOString(),
                        success: this.status >= 200 && this.status < 300
                    });
                }
            });

            return originalSend.apply(this, args);
        };
    }

    captureAPICall(callData) {
        this.data.apiHistory.push(callData);

        // Keep only last 20 API calls
        if (this.data.apiHistory.length > 20) {
            this.data.apiHistory.shift();
        }
    }

    setupUserActionTracking() {
        // Track clicks
        document.addEventListener('click', (event) => {
            this.captureUserAction('click', event.target);
        }, true);

        // Track form inputs (excluding password fields)
        document.addEventListener('input', (event) => {
            if (event.target.type !== 'password') {
                this.captureUserAction('input', event.target);
            }
        }, true);

        // Track page navigations
        let lastUrl = location.href;
        new MutationObserver(() => {
            const currentUrl = location.href;
            if (currentUrl !== lastUrl) {
                this.captureUserAction('navigation', null, { from: lastUrl, to: currentUrl });
                lastUrl = currentUrl;
            }
        }).observe(document, { subtree: true, childList: true });
    }

    captureUserAction(type, element, metadata = {}) {
        const action = {
            type: type,
            timestamp: new Date().toISOString(),
            ...metadata
        };

        if (element) {
            action.element = {
                tagName: element.tagName,
                id: element.id,
                className: element.className,
                text: element.textContent?.substring(0, 50)
            };
        }

        this.data.userActions.push(action);

        // Keep only last 10 actions
        if (this.data.userActions.length > 10) {
            this.data.userActions.shift();
        }
    }

    getData() {
        return {
            ...this.data,
            pageUrl: window.location.href,
            pageTitle: document.title
        };
    }
}

// Initialize on page load
window.bugReportDataCapture = new DataCaptureService();
```

### 4. Screenshot Capture (`app/static/js/chatbot/screenshot.js`)

#### 4.1 Screenshot Capture with html2canvas

```javascript
class ScreenshotCapture {
    constructor() {
        this.screenshot = null;
        this.annotations = [];
        this.canvas = null;
        this.ctx = null;
        this.isDrawing = false;
        this.currentTool = null;
    }

    async capture() {
        // Hide chatbot before capturing
        const chatbot = document.getElementById('chatbot-container');
        const trigger = document.getElementById('chatbot-trigger');

        chatbot.style.display = 'none';
        trigger.style.display = 'none';

        try {
            // Capture screenshot using html2canvas
            const canvas = await html2canvas(document.body, {
                allowTaint: true,
                useCORS: true,
                logging: false,
                width: window.innerWidth,
                height: window.innerHeight
            });

            // Convert to base64
            this.screenshot = canvas.toDataURL('image/png');

            // Show annotation modal
            this.showAnnotationModal();

        } catch (error) {
            console.error('Screenshot capture failed:', error);
            alert('Failed to capture screenshot. Please try again.');
        } finally {
            // Restore chatbot visibility
            chatbot.style.display = 'block';
            trigger.style.display = 'block';
        }
    }

    showAnnotationModal() {
        // Create modal overlay
        const modal = document.createElement('div');
        modal.id = 'screenshot-annotation-modal';
        modal.className = 'screenshot-modal';
        modal.innerHTML = `
            <div class="screenshot-modal-content">
                <div class="screenshot-modal-header">
                    <h3>Annotate Screenshot</h3>
                    <button class="btn-close" onclick="screenshotCapture.closeModal()">×</button>
                </div>
                <div class="screenshot-modal-toolbar">
                    <button class="tool-btn" data-tool="arrow" title="Draw Arrow">
                        <svg><!-- Arrow icon --></svg>
                    </button>
                    <button class="tool-btn" data-tool="rectangle" title="Draw Rectangle">
                        <svg><!-- Rectangle icon --></svg>
                    </button>
                    <button class="tool-btn" data-tool="text" title="Add Text">
                        <svg><!-- Text icon --></svg>
                    </button>
                    <button class="tool-btn" data-tool="clear" title="Clear Annotations">
                        <svg><!-- Clear icon --></svg>
                    </button>
                </div>
                <div class="screenshot-modal-body">
                    <canvas id="screenshot-canvas"></canvas>
                </div>
                <div class="screenshot-modal-footer">
                    <button class="btn-secondary" onclick="screenshotCapture.closeModal()">Cancel</button>
                    <button class="btn-primary" onclick="screenshotCapture.saveScreenshot()">Save</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Load screenshot onto canvas
        this.loadScreenshotToCanvas();

        // Attach tool event listeners
        this.attachToolListeners();
    }

    loadScreenshotToCanvas() {
        const canvas = document.getElementById('screenshot-canvas');
        const img = new Image();

        img.onload = () => {
            canvas.width = img.width;
            canvas.height = img.height;

            this.canvas = canvas;
            this.ctx = canvas.getContext('2d');
            this.ctx.drawImage(img, 0, 0);
        };

        img.src = this.screenshot;
    }

    attachToolListeners() {
        // Tool button clicks
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tool = e.currentTarget.dataset.tool;

                if (tool === 'clear') {
                    this.clearAnnotations();
                } else {
                    this.selectTool(tool);
                }
            });
        });

        // Canvas drawing events
        this.canvas.addEventListener('mousedown', this.startDrawing.bind(this));
        this.canvas.addEventListener('mousemove', this.draw.bind(this));
        this.canvas.addEventListener('mouseup', this.stopDrawing.bind(this));
    }

    selectTool(tool) {
        this.currentTool = tool;

        // Update UI
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tool="${tool}"]`).classList.add('active');
    }

    startDrawing(e) {
        if (!this.currentTool) return;

        this.isDrawing = true;
        const rect = this.canvas.getBoundingClientRect();
        this.startX = e.clientX - rect.left;
        this.startY = e.clientY - rect.top;
    }

    draw(e) {
        if (!this.isDrawing) return;

        const rect = this.canvas.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;

        // Redraw screenshot and all annotations
        this.redrawCanvas();

        // Draw current annotation preview
        this.ctx.strokeStyle = '#FF0000';
        this.ctx.lineWidth = 3;

        if (this.currentTool === 'arrow') {
            this.drawArrow(this.startX, this.startY, currentX, currentY);
        } else if (this.currentTool === 'rectangle') {
            this.ctx.strokeRect(
                this.startX,
                this.startY,
                currentX - this.startX,
                currentY - this.startY
            );
        }
    }

    stopDrawing(e) {
        if (!this.isDrawing) return;

        const rect = this.canvas.getBoundingClientRect();
        const endX = e.clientX - rect.left;
        const endY = e.clientY - rect.top;

        // Save annotation
        const annotation = {
            tool: this.currentTool,
            startX: this.startX,
            startY: this.startY,
            endX: endX,
            endY: endY
        };

        if (this.currentTool === 'text') {
            const text = prompt('Enter text:');
            if (text) {
                annotation.text = text;
                this.annotations.push(annotation);
            }
        } else {
            this.annotations.push(annotation);
        }

        this.isDrawing = false;
        this.redrawCanvas();
    }

    drawArrow(fromX, fromY, toX, toY) {
        const headLength = 15;
        const angle = Math.atan2(toY - fromY, toX - fromX);

        // Draw line
        this.ctx.beginPath();
        this.ctx.moveTo(fromX, fromY);
        this.ctx.lineTo(toX, toY);
        this.ctx.stroke();

        // Draw arrowhead
        this.ctx.beginPath();
        this.ctx.moveTo(toX, toY);
        this.ctx.lineTo(
            toX - headLength * Math.cos(angle - Math.PI / 6),
            toY - headLength * Math.sin(angle - Math.PI / 6)
        );
        this.ctx.moveTo(toX, toY);
        this.ctx.lineTo(
            toX - headLength * Math.cos(angle + Math.PI / 6),
            toY - headLength * Math.sin(angle + Math.PI / 6)
        );
        this.ctx.stroke();
    }

    redrawCanvas() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Redraw screenshot
        const img = new Image();
        img.onload = () => {
            this.ctx.drawImage(img, 0, 0);

            // Redraw all annotations
            this.ctx.strokeStyle = '#FF0000';
            this.ctx.lineWidth = 3;
            this.ctx.fillStyle = '#FF0000';
            this.ctx.font = '16px Arial';

            this.annotations.forEach(annotation => {
                if (annotation.tool === 'arrow') {
                    this.drawArrow(annotation.startX, annotation.startY, annotation.endX, annotation.endY);
                } else if (annotation.tool === 'rectangle') {
                    this.ctx.strokeRect(
                        annotation.startX,
                        annotation.startY,
                        annotation.endX - annotation.startX,
                        annotation.endY - annotation.startY
                    );
                } else if (annotation.tool === 'text') {
                    this.ctx.fillText(annotation.text, annotation.startX, annotation.startY);
                }
            });
        };
        img.src = this.screenshot;
    }

    clearAnnotations() {
        this.annotations = [];
        this.redrawCanvas();
    }

    saveScreenshot() {
        // Finalize screenshot with annotations
        this.screenshot = this.canvas.toDataURL('image/png');

        // Close modal
        this.closeModal();

        // Update chatbot UI
        window.bugReportChatbot.setScreenshot(this.screenshot, this.annotations);
    }

    closeModal() {
        const modal = document.getElementById('screenshot-annotation-modal');
        if (modal) {
            modal.remove();
        }
    }
}

// Initialize
window.screenshotCapture = new ScreenshotCapture();
```

### 5. Form Submission (`app/static/js/chatbot/submit.js`)

```javascript
async submitReport() {
    // Show loading state
    const submitBtn = document.querySelector('.btn-submit');
    submitBtn.disabled = true;
    submitBtn.querySelector('.btn-text').classList.add('hidden');
    submitBtn.querySelector('.btn-spinner').classList.remove('hidden');

    try {
        // Collect all form data
        const reportData = {
            category: this.formData.category,
            severity: this.formData.severity || 'medium',
            title: this.formData.title,
            description: this.formData.description,
            steps_to_reproduce: this.formData.steps_to_reproduce,
            expected_behavior: this.formData.expected_behavior,
            actual_behavior: this.formData.actual_behavior,

            // Debug data
            browser_info: window.bugReportDataCapture.data.browserInfo,
            page_url: window.location.href,
            page_title: document.title,
            viewport_size: `${window.innerWidth}x${window.innerHeight}`,
            screen_resolution: `${screen.width}x${screen.height}`,
            console_errors: window.bugReportDataCapture.data.consoleErrors,
            api_history: window.bugReportDataCapture.data.apiHistory,
            user_actions: window.bugReportDataCapture.data.userActions,

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
            // Show success message
            this.showSuccessMessage(result.ticket_number);

            // Reset form
            this.reset();

            // Close chatbot after 3 seconds
            setTimeout(() => {
                this.close();
            }, 3000);
        } else {
            // Show error message
            this.showErrorMessage(result.message || 'Failed to submit report');
        }

    } catch (error) {
        console.error('Submission error:', error);
        this.showErrorMessage('Network error. Please try again.');
    } finally {
        // Restore button state
        submitBtn.disabled = false;
        submitBtn.querySelector('.btn-text').classList.remove('hidden');
        submitBtn.querySelector('.btn-spinner').classList.add('hidden');
    }
}

showSuccessMessage(ticketNumber) {
    const container = document.querySelector('.chatbot-body');
    container.innerHTML = `
        <div class="success-message">
            <svg class="success-icon"><!-- Checkmark icon --></svg>
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

showErrorMessage(message) {
    const container = document.querySelector('.chatbot-body');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
        <svg class="error-icon"><!-- Error icon --></svg>
        <p>${message}</p>
    `;
    container.insertBefore(errorDiv, container.firstChild);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}
```

### 6. Base Template Integration (`app/templates/base.html`)

Add to the end of the `<body>` tag, before `</body>`:

```html
{% if current_user.is_authenticated %}
<!-- Bug Report Chatbot -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/chatbot.css') }}">
<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
<script src="{{ url_for('static', filename='js/chatbot/data-capture.js') }}"></script>
<script src="{{ url_for('static', filename='js/chatbot/screenshot.js') }}"></script>
<script src="{{ url_for('static', filename='js/chatbot/chatbot.js') }}"></script>
{% endif %}
```

## Implementation Steps

### Step 1: Widget UI (3 hours)
1. Create `app/static/css/chatbot.css`
2. Create basic widget structure
3. Implement open/close animations
4. Add responsive design
5. Test on different screen sizes

### Step 2: Multi-Step Form (4 hours)
1. Create form step components
2. Implement step navigation
3. Add form validation
4. Implement progress indicator
5. Add localStorage persistence

### Step 3: Data Capture (3 hours)
1. Create `app/static/js/chatbot/data-capture.js`
2. Implement browser info capture
3. Set up console error monitoring
4. Set up API call interception
5. Set up user action tracking

### Step 4: Screenshot Functionality (4 hours)
1. Create `app/static/js/chatbot/screenshot.js`
2. Integrate html2canvas
3. Build annotation modal
4. Implement drawing tools
5. Handle screenshot save/cancel

### Step 5: Integration & Testing (2 hours)
1. Integrate all components
2. Test complete submission flow
3. Test error handling
4. Cross-browser testing
5. Mobile responsiveness testing

## Acceptance Criteria

- [ ] Chatbot widget appears on all authenticated pages
- [ ] Widget opens/closes smoothly
- [ ] All 4 form steps work correctly
- [ ] Form validation prevents invalid submissions
- [ ] Browser data captured automatically
- [ ] Console errors captured (tested with intentional errors)
- [ ] API calls tracked (verified in review step)
- [ ] Screenshot capture works
- [ ] Annotation tools functional (arrow, rectangle, text)
- [ ] Form submits to API successfully
- [ ] Success message displays ticket number
- [ ] Error handling works for network failures
- [ ] Mobile responsive design works
- [ ] No console errors in clean state
- [ ] localStorage persistence works

## Testing Checklist

### Functional Tests
- [ ] Test category selection (all 4 options)
- [ ] Test severity selection (bugs only)
- [ ] Test form validation (missing required fields)
- [ ] Test screenshot capture
- [ ] Test annotation tools
- [ ] Test form submission
- [ ] Test success/error messages
- [ ] Test form reset after submission

### Cross-Browser Tests
- [ ] Chrome (desktop)
- [ ] Firefox (desktop)
- [ ] Safari (desktop)
- [ ] Edge (desktop)
- [ ] Chrome (mobile)
- [ ] Safari (mobile)

### Responsive Tests
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

### Data Capture Tests
- [ ] Browser info populated correctly
- [ ] Console errors captured
- [ ] API calls tracked
- [ ] User actions recorded
- [ ] Screenshot data included

## Deliverables Checklist

- [ ] `app/static/css/chatbot.css` - Complete
- [ ] `app/static/js/chatbot/chatbot.js` - Complete
- [ ] `app/static/js/chatbot/data-capture.js` - Complete
- [ ] `app/static/js/chatbot/screenshot.js` - Complete
- [ ] `app/templates/base.html` - Updated
- [ ] Cross-browser tested
- [ ] Mobile responsive tested
- [ ] Integration with backend API tested

## Notes for Implementation

1. **Performance:**
   - Lazy load html2canvas only when needed
   - Debounce user action tracking
   - Limit data retention (50 errors, 20 API calls, 10 actions)

2. **Privacy:**
   - Never capture password fields
   - Sanitize localStorage/sessionStorage data
   - Clear sensitive data from screenshots

3. **User Experience:**
   - Save form state to localStorage
   - Show clear progress indicator
   - Provide helpful validation messages
   - Smooth animations

4. **Error Handling:**
   - Graceful fallback if html2canvas fails
   - Network error recovery
   - Form validation feedback

5. **Accessibility:**
   - Keyboard navigation support
   - Focus management
   - ARIA labels
   - Screen reader friendly

## Success Metrics

- Widget loads < 50ms after page load
- Form submission completes < 3 seconds
- Screenshot capture < 2 seconds
- No JavaScript errors in console
- 100% mobile responsive
- All acceptance criteria met

---

**Status:** Ready for Implementation
**Assigned To:** UI Developer / feature-developer agent
**Dependencies:** Phase 1 Backend must be complete
**Review Required:** Yes (code review before Phase 3)
