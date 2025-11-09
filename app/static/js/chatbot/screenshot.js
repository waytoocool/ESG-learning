/**
 * Screenshot Capture Service with Annotation Tools
 * Captures screenshots using html2canvas and provides annotation capabilities
 */

class ScreenshotCapture {
    constructor() {
        this.screenshot = null;
        this.annotations = [];
        this.canvas = null;
        this.ctx = null;
        this.isDrawing = false;
        this.currentTool = null;
        this.startX = 0;
        this.startY = 0;
    }

    /**
     * Capture a screenshot of the current page
     */
    async capture() {
        // Check if html2canvas is loaded
        if (typeof html2canvas === 'undefined') {
            alert('Screenshot library not loaded. Please refresh the page and try again.');
            return;
        }

        // Hide chatbot elements before capturing
        const chatbot = document.getElementById('chatbot-container');
        const trigger = document.getElementById('chatbot-trigger');

        if (chatbot) chatbot.style.display = 'none';
        if (trigger) trigger.style.display = 'none';

        try {
            // Capture screenshot using html2canvas
            const canvas = await html2canvas(document.body, {
                allowTaint: true,
                useCORS: true,
                logging: false,
                width: window.innerWidth,
                height: window.innerHeight,
                windowWidth: window.innerWidth,
                windowHeight: window.innerHeight
            });

            // Validate canvas was created successfully
            if (!canvas || !canvas.toDataURL) {
                throw new Error('Canvas creation failed - invalid canvas object');
            }

            // Convert to base64
            this.screenshot = canvas.toDataURL('image/png');

            // Validate screenshot data
            if (!this.screenshot || this.screenshot.length < 100) {
                throw new Error('Screenshot data is invalid or empty');
            }

            // Show annotation modal only if screenshot was captured successfully
            this.showAnnotationModal();

        } catch (error) {
            console.error('Screenshot capture failed:', error);
            // Show user-friendly error message
            const errorMsg = error.message || 'Failed to capture screenshot. Please try again.';
            alert(errorMsg);

            // Reset screenshot data
            this.screenshot = null;
        } finally {
            // Restore chatbot visibility
            if (chatbot) chatbot.style.display = 'block';
            if (trigger) trigger.style.display = 'block';
        }
    }

    /**
     * Show the annotation modal
     */
    showAnnotationModal() {
        // Remove existing modal if any
        const existingModal = document.getElementById('screenshot-annotation-modal');
        if (existingModal) {
            existingModal.remove();
        }

        // Create modal overlay
        const modal = document.createElement('div');
        modal.id = 'screenshot-annotation-modal';
        modal.className = 'screenshot-modal';
        modal.innerHTML = `
            <div class="screenshot-modal-content">
                <div class="screenshot-modal-header">
                    <h3>Annotate Screenshot</h3>
                    <button class="btn-close" onclick="screenshotCapture.closeModal()">&times;</button>
                </div>
                <div class="screenshot-modal-toolbar">
                    <button class="tool-btn" data-tool="arrow" title="Draw Arrow">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 2L2 22h20L12 2zm0 4l7 14H5l7-14z"/>
                        </svg>
                        Arrow
                    </button>
                    <button class="tool-btn" data-tool="rectangle" title="Draw Rectangle">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <rect x="3" y="3" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        Box
                    </button>
                    <button class="tool-btn" data-tool="text" title="Add Text">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M5 4v3h5.5v12h3V7H19V4z"/>
                        </svg>
                        Text
                    </button>
                    <button class="tool-btn" data-tool="clear" title="Clear Annotations">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                        </svg>
                        Clear
                    </button>
                </div>
                <div class="screenshot-modal-body">
                    <canvas id="screenshot-canvas"></canvas>
                </div>
                <div class="screenshot-modal-footer">
                    <button class="btn-secondary" onclick="screenshotCapture.closeModal()">Cancel</button>
                    <button class="btn-primary" onclick="screenshotCapture.saveScreenshot()">Save Screenshot</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Load screenshot onto canvas
        this.loadScreenshotToCanvas();

        // Attach tool event listeners
        this.attachToolListeners();
    }

    /**
     * Load the screenshot image onto the canvas
     */
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

    /**
     * Attach event listeners to annotation tools
     */
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
        this.canvas.addEventListener('mouseleave', () => {
            if (this.isDrawing) {
                this.isDrawing = false;
            }
        });
    }

    /**
     * Select a drawing tool
     */
    selectTool(tool) {
        this.currentTool = tool;

        // Update UI
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        const activeBtn = document.querySelector(`[data-tool="${tool}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
    }

    /**
     * Start drawing
     */
    startDrawing(e) {
        if (!this.currentTool || this.currentTool === 'clear') return;

        this.isDrawing = true;
        const rect = this.canvas.getBoundingClientRect();
        this.startX = e.clientX - rect.left;
        this.startY = e.clientY - rect.top;
    }

    /**
     * Draw while mouse is moving
     */
    draw(e) {
        if (!this.isDrawing) return;

        const rect = this.canvas.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;

        // Redraw everything
        this.redrawCanvas();

        // Draw current annotation preview
        this.ctx.strokeStyle = '#FF0000';
        this.ctx.lineWidth = 3;
        this.ctx.fillStyle = '#FF0000';

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

    /**
     * Stop drawing and save annotation
     */
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

    /**
     * Draw an arrow from start to end point
     */
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

    /**
     * Redraw the canvas with screenshot and all annotations
     */
    redrawCanvas() {
        if (!this.canvas || !this.ctx) return;

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

    /**
     * Clear all annotations
     */
    clearAnnotations() {
        this.annotations = [];
        this.redrawCanvas();
    }

    /**
     * Save the annotated screenshot
     */
    saveScreenshot() {
        // Finalize screenshot with annotations
        if (this.canvas) {
            this.screenshot = this.canvas.toDataURL('image/png');
        }

        // Close modal
        this.closeModal();

        // Update chatbot UI
        if (window.bugReportChatbot) {
            window.bugReportChatbot.setScreenshot(this.screenshot, this.annotations);
        }
    }

    /**
     * Close the annotation modal
     */
    closeModal() {
        const modal = document.getElementById('screenshot-annotation-modal');
        if (modal) {
            modal.remove();
        }

        // Reset state
        this.canvas = null;
        this.ctx = null;
        this.isDrawing = false;
        this.currentTool = null;
    }

    /**
     * Reset the screenshot capture
     */
    reset() {
        this.screenshot = null;
        this.annotations = [];
        this.closeModal();
    }
}

// Initialize
window.screenshotCapture = new ScreenshotCapture();
