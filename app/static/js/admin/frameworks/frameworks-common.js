/**
 * Frameworks Common Module
 * Shared utilities and helpers for all framework-related functionality
 */

window.FrameworksCommon = (function() {
    'use strict';

    // Private variables
    let currentCompanyId = null;
    let csrfToken = null;

    // Public API
    return {
        /**
         * Initialize common functionality
         */
        initialize: function() {
            console.log('FrameworksCommon: Initializing...');
            this.initializeCSRF();
            this.initializeCompanyId();
            console.log('FrameworksCommon: Initialization complete. Company ID:', currentCompanyId);
        },

        /**
         * Initialize CSRF token for API calls
         */
        initializeCSRF: function() {
            const csrfMeta = document.querySelector('meta[name="csrf-token"]');
            if (csrfMeta) {
                csrfToken = csrfMeta.getAttribute('content');
            }
        },

        /**
         * Initialize company ID from page context
         */
        initializeCompanyId: function() {
            // Try to get company ID from various sources
            const companyIdMeta = document.querySelector('meta[name="company-id"]');
            if (companyIdMeta) {
                currentCompanyId = companyIdMeta.getAttribute('content');
            }
            
            // Fallback: try to get from global variable or data attribute
            if (!currentCompanyId && window.currentUser && window.currentUser.company_id) {
                currentCompanyId = window.currentUser.company_id;
            }
        },

        /**
         * Get current company ID
         */
        getCurrentCompanyId: function() {
            return currentCompanyId;
        },

        /**
         * Generate slug from field name
         */
        generateSlug: function(fieldName) {
            if (!fieldName) return '';
            // Convert to lowercase, replace spaces and special chars with underscores
            let slug = fieldName.toLowerCase().replace(/[^a-zA-Z0-9\s-]/g, '');
            slug = slug.replace(/[\s-]+/g, '_').replace(/^_+|_+$/g, '');
            return slug;
        },

        /**
         * Update stat with animation
         */
        updateStatWithAnimation: function(elementId, newValue) {
            const element = document.getElementById(elementId);
            if (element) {
                const skeletonLoader = element.querySelector('.skeleton-loader');
                if (skeletonLoader) {
                    skeletonLoader.style.opacity = '0';
                    setTimeout(() => {
                        element.textContent = newValue;
                        element.style.opacity = '0';
                        element.style.transform = 'translateY(10px)';
                        setTimeout(() => {
                            element.style.transition = 'all 0.3s ease';
                            element.style.opacity = '1';
                            element.style.transform = 'translateY(0)';
                        }, 50);
                    }, 200);
                } else {
                    element.textContent = newValue;
                }
            }
        },

        /**
         * Make API call with proper headers and error handling
         */
        apiCall: function(url, options = {}) {
            const defaultOptions = {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'include'
            };

            // Add CSRF token if available
            if (csrfToken) {
                defaultOptions.headers['X-CSRFToken'] = csrfToken;
            }

            // Merge options
            const finalOptions = {
                ...defaultOptions,
                ...options,
                headers: {
                    ...defaultOptions.headers,
                    ...options.headers
                }
            };

            return fetch(url, finalOptions)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .catch(error => {
                    console.error('API call failed:', error);
                    throw error;
                });
        },

        /**
         * Show loading state on element
         */
        showLoading: function(elementId, message = 'Loading...') {
            const element = document.getElementById(elementId);
            if (element) {
                element.innerHTML = `
                    <div class="text-center p-3">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">${message}</span>
                        </div>
                        <p class="mt-2 text-muted">${message}</p>
                    </div>
                `;
            }
        },

        /**
         * Show error state on element
         */
        showError: function(elementId, error) {
            const element = document.getElementById(elementId);
            if (element) {
                element.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i>
                        <strong>Error:</strong> ${error}
                    </div>
                `;
            }
        },

        /**
         * Show success message
         */
        showSuccess: function(message) {
            this.showNotification(message, 'success');
        },

        /**
         * Show notification
         */
        showNotification: function(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
            notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
            notification.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            document.body.appendChild(notification);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 5000);
        },

        /**
         * Debounce function for search inputs
         */
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        /**
         * Format date for display
         */
        formatDate: function(dateString) {
            if (!dateString) return 'N/A';
            const date = new Date(dateString);
            return date.toLocaleDateString();
        },

        /**
         * Format date and time for display
         */
        formatDateTime: function(dateString) {
            if (!dateString) return 'N/A';
            const date = new Date(dateString);
            return date.toLocaleString();
        },

        /**
         * Validate form data
         */
        validateForm: function(formElement) {
            const errors = [];
            const requiredFields = formElement.querySelectorAll('[required]');
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    errors.push(`${field.name || field.id} is required`);
                }
            });

            return {
                isValid: errors.length === 0,
                errors: errors
            };
        },

        /**
         * Get form data as object
         */
        getFormData: function(formElement) {
            const formData = new FormData(formElement);
            const data = {};
            
            for (let [key, value] of formData.entries()) {
                if (data[key]) {
                    // Handle multiple values (like checkboxes)
                    if (!Array.isArray(data[key])) {
                        data[key] = [data[key]];
                    }
                    data[key].push(value);
                } else {
                    data[key] = value;
                }
            }
            
            return data;
        },

        /**
         * Check if user has permission
         */
        hasPermission: function(permission) {
            if (window.currentUser && window.currentUser.permissions) {
                return window.currentUser.permissions.includes(permission);
            }
            return false;
        },

        /**
         * Log debug information
         */
        debug: function(message, data = null) {
            if (window.debug || localStorage.getItem('framework_debug')) {
                console.log(`[FrameworksCommon] ${message}`, data);
            }
        },

        /**
         * Module ready check
         */
        isReady: function() {
            const ready = true; // Changed to always return true since company ID is optional
            console.log('FrameworksCommon: isReady check:', ready, 'Company ID:', currentCompanyId);
            return ready;
        }
    };
})();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        FrameworksCommon.initialize();
    });
} else {
    FrameworksCommon.initialize();
} 