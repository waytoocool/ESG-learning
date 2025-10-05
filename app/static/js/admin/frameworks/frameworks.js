/**
 * Frameworks Main Loader
 * Coordinates all framework modules and provides unified API
 */

window.Frameworks = (function() {
    'use strict';

    // Module dependencies - updated to include new modules
    const dependencies = [
        'FrameworksCommon',
        'FrameworksStatistics', 
        'FrameworksMain',
        'FrameworksTopics',
        'FrameworksDimensions',
        'FrameworksDataPoints',
        'FrameworksFieldMapping',
        'FrameworksUnitManagement',
        'FrameworksDependencies',
        'FrameworksUIUtils',
        'FrameworksPermissions'
    ];

    // Public API
    return {
        /**
         * Initialize all framework modules
         */
        initialize: function() {
            console.log('Frameworks: Initializing framework system...');

            // Check if all dependencies are loaded
            const missingDeps = dependencies.filter(dep => !window[dep]);
            if (missingDeps.length > 0) {
                console.warn('Missing dependencies, retrying in 500ms:', missingDeps);
                setTimeout(() => this.initialize(), 500);
                return;
            }

            console.log('All dependencies loaded, starting initialization...');

            // Initialize all modules in order
            try {
                // Common module should initialize first
                if (window.FrameworksCommon && window.FrameworksCommon.initialize) {
                    console.log('Initializing FrameworksCommon...');
                    window.FrameworksCommon.initialize();
                }

                // Wait for common module to be ready, then initialize others
                this.waitForCommon(() => {
                    console.log('FrameworksCommon ready, initializing other modules...');
                    
                    if (window.FrameworksStatistics && window.FrameworksStatistics.initialize) {
                        window.FrameworksStatistics.initialize();
                    }
                    
                    if (window.FrameworksMain && window.FrameworksMain.initialize) {
                        window.FrameworksMain.initialize();
                    }
                    
                    if (window.FrameworksTopics && window.FrameworksTopics.initialize) {
                        window.FrameworksTopics.initialize();
                    }
                    
                    if (window.FrameworksDimensions && window.FrameworksDimensions.initialize) {
                        window.FrameworksDimensions.initialize();
                    }
                    
                    if (window.FrameworksDataPoints && window.FrameworksDataPoints.initialize) {
                        window.FrameworksDataPoints.initialize();
                    }
                    
                    // Initialize new modules
                    if (window.FrameworksFieldMapping && window.FrameworksFieldMapping.initialize) {
                        window.FrameworksFieldMapping.initialize();
                    }
                    
                    if (window.FrameworksUnitManagement && window.FrameworksUnitManagement.initialize) {
                        window.FrameworksUnitManagement.initialize();
                    }
                    
                    if (window.FrameworksDependencies && window.FrameworksDependencies.initialize) {
                        window.FrameworksDependencies.initialize();
                    }
                    
                    if (window.FrameworksUIUtils && window.FrameworksUIUtils.initialize) {
                        window.FrameworksUIUtils.initialize();
                    }
                    
                    if (window.FrameworksPermissions && window.FrameworksPermissions.initialize) {
                        window.FrameworksPermissions.initialize();
                    }

                    console.log('Frameworks: All modules initialized successfully');
                });

            } catch (error) {
                console.error('Error initializing frameworks:', error);
            }
        },

        /**
         * Wait for common module to be ready
         */
        waitForCommon: function(callback) {
            if (window.FrameworksCommon && window.FrameworksCommon.isReady && window.FrameworksCommon.isReady()) {
                callback();
            } else {
                setTimeout(() => this.waitForCommon(callback), 100);
            }
        },

        /**
         * Get module instance
         */
        getModule: function(moduleName) {
            const moduleMap = {
                'common': window.FrameworksCommon,
                'statistics': window.FrameworksStatistics,
                'main': window.FrameworksMain,
                'topics': window.FrameworksTopics,
                'dimensions': window.FrameworksDimensions,
                'datapoints': window.FrameworksDataPoints,
                'fieldmapping': window.FrameworksFieldMapping,
                'unitmanagement': window.FrameworksUnitManagement,
                'dependencies': window.FrameworksDependencies,
                'uiutils': window.FrameworksUIUtils,
                'permissions': window.FrameworksPermissions
            };

            return moduleMap[moduleName];
        },

        /**
         * Check if all modules are ready
         */
        isReady: function() {
            return dependencies.every(dep => {
                const module = window[dep];
                return module && (module.isReady ? module.isReady() : true);
            });
        },

        /**
         * Refresh all modules
         */
        refresh: function() {
            console.log('Frameworks: Refreshing all modules...');
            
            // Refresh all modules
            dependencies.forEach(dep => {
                const module = window[dep];
                if (module && module.refresh) {
                    module.refresh();
                }
            });
        },

        /**
         * Show notification using common module
         */
        showNotification: function(message, type = 'info') {
            if (window.FrameworksCommon && window.FrameworksCommon.showNotification) {
                window.FrameworksCommon.showNotification(message, type);
            }
        },

        /**
         * Make API call using common module
         */
        apiCall: function(url, options = {}) {
            if (window.FrameworksCommon && window.FrameworksCommon.apiCall) {
                return window.FrameworksCommon.apiCall(url, options);
            }
            return Promise.reject(new Error('FrameworksCommon module not available'));
        },

        /**
         * Get framework statistics
         */
        getStats: function() {
            if (window.FrameworksStatistics && window.FrameworksStatistics.getStatsData) {
                return window.FrameworksStatistics.getStatsData();
            }
            return null;
        },

        /**
         * Get frameworks data
         */
        getFrameworks: function() {
            if (window.FrameworksMain && window.FrameworksMain.getFrameworks) {
                return window.FrameworksMain.getFrameworks();
            }
            return { all: [], filtered: [], current: {} };
        },

        /**
         * Get topics data
         */
        getTopics: function() {
            if (window.FrameworksTopics && window.FrameworksTopics.getTopics) {
                return window.FrameworksTopics.getTopics();
            }
            return { framework: [], custom: [], all: [] };
        },

        /**
         * Load framework details
         */
        loadFrameworkDetails: function(frameworkId) {
            if (window.FrameworksMain && window.FrameworksMain.loadFrameworkDetails) {
                window.FrameworksMain.loadFrameworkDetails(frameworkId);
            }
        },

        /**
         * Set framework filter
         */
        setFilter: function(filter) {
            if (window.FrameworksMain && window.FrameworksMain.setCurrentTypeFilter) {
                window.FrameworksMain.setCurrentTypeFilter(filter);
            }
        },

        /**
         * Set sort order
         */
        setSort: function(sort) {
            if (window.FrameworksMain && window.FrameworksMain.setSort) {
                window.FrameworksMain.setSort(sort);
            }
        },

        /**
         * Load framework topics
         */
        loadFrameworkTopics: function(frameworkId) {
            if (window.FrameworksTopics && window.FrameworksTopics.loadFrameworkTopics) {
                window.FrameworksTopics.loadFrameworkTopics(frameworkId);
            }
        },

        /**
         * Update topic dropdown
         */
        updateTopicDropdown: function(selectElement) {
            if (window.FrameworksTopics && window.FrameworksTopics.updateTopicDropdowns) {
                window.FrameworksTopics.updateTopicDropdowns();
            }
        },

        /**
         * Open dimension modal
         */
        openDimensionModal: function(rowId, fieldName, row) {
            if (window.FrameworksDimensions && window.FrameworksDimensions.openDimensionModal) {
                window.FrameworksDimensions.openDimensionModal(rowId, fieldName, row);
            }
        },

        /**
         * Setup dimension management for row
         */
        setupDimensionManagement: function(row) {
            if (window.FrameworksDimensions && window.FrameworksDimensions.setupDimensionManagement) {
                window.FrameworksDimensions.setupDimensionManagement(row);
            }
        },

        /**
         * Get available dimensions
         */
        getAvailableDimensions: function() {
            if (window.FrameworksDimensions && window.FrameworksDimensions.getAvailableDimensions) {
                return window.FrameworksDimensions.getAvailableDimensions();
            }
            return [];
        },

        /**
         * Open data point drawer
         */
        openDataPointDrawer: function(dataPointIndex = -1) {
            if (window.FrameworksDataPoints && window.FrameworksDataPoints.openDataPointDrawer) {
                window.FrameworksDataPoints.openDataPointDrawer(dataPointIndex);
            }
        },

        /**
         * Get data points
         */
        getDataPoints: function() {
            if (window.FrameworksDataPoints && window.FrameworksDataPoints.getDataPoints) {
                return window.FrameworksDataPoints.getDataPoints();
            }
            return [];
        },

        /**
         * Set data points
         */
        setDataPoints: function(dataPoints) {
            if (window.FrameworksDataPoints && window.FrameworksDataPoints.setDataPoints) {
                window.FrameworksDataPoints.setDataPoints(dataPoints);
            }
        },

        /**
         * Import template data points
         */
        importTemplate: function(templateData) {
            if (window.FrameworksDataPoints && window.FrameworksDataPoints.importTemplate) {
                window.FrameworksDataPoints.importTemplate(templateData);
            }
        },

        /**
         * Filter data points
         */
        filterDataPoints: function(searchTerm) {
            if (window.FrameworksDataPoints && window.FrameworksDataPoints.filterDataPoints) {
                window.FrameworksDataPoints.filterDataPoints(searchTerm);
            }
        },

        /**
         * Add row event listeners (new function)
         */
        addRowEventListeners: function(row) {
            if (window.FrameworksFieldMapping && window.FrameworksFieldMapping.addRowEventListeners) {
                window.FrameworksFieldMapping.addRowEventListeners(row);
            }
        },

        /**
         * Setup unit aware inputs (new function)
         */
        setupUnitAwareInputs: function(row) {
            if (window.FrameworksUnitManagement && window.FrameworksUnitManagement.setupUnitAwareInputs) {
                window.FrameworksUnitManagement.setupUnitAwareInputs(row);
            }
        },

        /**
         * Check field dependencies (new function)
         */
        checkFieldDependencies: function(fieldId) {
            if (window.FrameworksDependencies && window.FrameworksDependencies.checkFieldDependencies) {
                window.FrameworksDependencies.checkFieldDependencies(fieldId);
            }
        },

        /**
         * Debug information
         */
        debug: function() {
            console.log('Frameworks Debug Information:');
            console.log('- Dependencies:', dependencies.map(dep => ({
                name: dep,
                loaded: !!window[dep],
                ready: window[dep] && window[dep].isReady ? window[dep].isReady() : 'unknown'
            })));
            console.log('- Stats:', this.getStats());
            console.log('- Frameworks:', this.getFrameworks());
            console.log('- Topics:', this.getTopics());
        },

        /**
         * Clean up all modules
         */
        cleanup: function() {
            console.log('Frameworks: Cleaning up modules...');
            
            // Remove event listeners and cleanup
            dependencies.forEach(dep => {
                if (window[dep] && window[dep].cleanup) {
                    window[dep].cleanup();
                }
            });
        }
    };
})();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM loaded, initializing Frameworks...');
        Frameworks.initialize();
    });
} else {
    console.log('DOM already loaded, initializing Frameworks...');
    Frameworks.initialize();
}

// Fallback initialization check after 2 seconds
setTimeout(() => {
    if (!Frameworks.isReady()) {
        console.warn('Frameworks not ready after 2 seconds, attempting reinitialize...');
        Frameworks.initialize();
    }
}, 2000);

// Global access for debugging
window.FrameworksDebug = {
    showInfo: () => Frameworks.debug(),
    refresh: () => Frameworks.refresh(),
    getStats: () => Frameworks.getStats(),
    getFrameworks: () => Frameworks.getFrameworks(),
    getTopics: () => Frameworks.getTopics(),
    getModule: (name) => Frameworks.getModule(name)
};

// Expose main API
window.Frameworks = Frameworks; 