/**
 * Data Capture Service for Bug Report Chatbot
 * Captures browser information, console errors, API calls, and user actions
 */

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

    /**
     * Initialize all data capture mechanisms
     */
    init() {
        this.captureBrowserInfo();
        this.setupConsoleMonitoring();
        this.setupAPIMonitoring();
        this.setupUserActionTracking();
    }

    /**
     * Capture comprehensive browser information
     */
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
        } else if (ua.indexOf('Edg') > -1) {
            browserName = 'Edge';
            browserVersion = ua.match(/Edg\/([0-9.]+)/)?.[1] || 'Unknown';
        } else if (ua.indexOf('Chrome') > -1) {
            browserName = 'Chrome';
            browserVersion = ua.match(/Chrome\/([0-9.]+)/)?.[1] || 'Unknown';
        } else if (ua.indexOf('Safari') > -1) {
            browserName = 'Safari';
            browserVersion = ua.match(/Version\/([0-9.]+)/)?.[1] || 'Unknown';
        }

        this.data.browserInfo.name = browserName;
        this.data.browserInfo.version = browserVersion;
    }

    /**
     * Set up console error and warning monitoring
     */
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
                colno: event.colno,
                stack: event.error?.stack
            });
        });

        // Listen for unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.captureConsoleError('error', [event.reason], {
                type: 'unhandledrejection'
            });
        });
    }

    /**
     * Capture a console error or warning
     */
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

    /**
     * Set up API call monitoring (fetch and XMLHttpRequest)
     */
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
                if (captureData && window.bugReportDataCapture) {
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

    /**
     * Capture an API call
     */
    captureAPICall(callData) {
        this.data.apiHistory.push(callData);

        // Keep only last 20 API calls
        if (this.data.apiHistory.length > 20) {
            this.data.apiHistory.shift();
        }
    }

    /**
     * Set up user action tracking
     */
    setupUserActionTracking() {
        // Track clicks (debounced to avoid excessive logging)
        let clickTimeout = null;
        document.addEventListener('click', (event) => {
            if (clickTimeout) return;

            clickTimeout = setTimeout(() => {
                clickTimeout = null;
            }, 100);

            this.captureUserAction('click', event.target);
        }, true);

        // Track form inputs (excluding password fields)
        let inputTimeout = null;
        document.addEventListener('input', (event) => {
            if (event.target.type === 'password') return;

            if (inputTimeout) clearTimeout(inputTimeout);

            inputTimeout = setTimeout(() => {
                this.captureUserAction('input', event.target);
            }, 500);
        }, true);

        // Track page navigations (SPA-style)
        let lastUrl = location.href;
        new MutationObserver(() => {
            const currentUrl = location.href;
            if (currentUrl !== lastUrl) {
                this.captureUserAction('navigation', null, { from: lastUrl, to: currentUrl });
                lastUrl = currentUrl;
            }
        }).observe(document, { subtree: true, childList: true });

        // Track initial page load
        this.captureUserAction('pageload', null, {
            url: window.location.href,
            referrer: document.referrer
        });
    }

    /**
     * Capture a user action
     */
    captureUserAction(type, element, metadata = {}) {
        const action = {
            type: type,
            timestamp: new Date().toISOString(),
            ...metadata
        };

        if (element) {
            action.element = {
                tagName: element.tagName,
                id: element.id || null,
                className: element.className || null,
                text: element.textContent?.substring(0, 50) || null
            };
        }

        this.data.userActions.push(action);

        // Keep only last 10 actions
        if (this.data.userActions.length > 10) {
            this.data.userActions.shift();
        }
    }

    /**
     * Get all captured data
     */
    getData() {
        return {
            ...this.data,
            pageUrl: window.location.href,
            pageTitle: document.title,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Reset all captured data
     */
    reset() {
        this.data.consoleErrors = [];
        this.data.apiHistory = [];
        this.data.userActions = [];
    }
}

// Initialize on page load
window.bugReportDataCapture = new DataCaptureService();
