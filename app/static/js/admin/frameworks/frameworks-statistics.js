/**
 * Frameworks Statistics Module
 * Handles statistics display and chart rendering
 */

window.FrameworksStatistics = (function() {
    'use strict';

    // Statistics Functions (exact copies from original)
    function updateStatWithAnimation(elementId, newValue) {
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
    }

    function initializeFrameworkStats() {
        console.log('Loading framework stats...');
        
        fetch('/admin/frameworks/stats', { credentials: 'include' })
            .then(response => response.json())
            .then(data => {
                console.log('Framework stats response:', data);
                if (data.success) {
                    // Remove skeleton loaders and update with real data
                    updateStatWithAnimation('total-frameworks-stat', data.total_frameworks);
                    updateStatWithAnimation('active-assignments-stat', data.active_assignments);
                    updateStatWithAnimation('overall-coverage-stat', `${data.overall_coverage}%`);
                    
                    const recentActivityDate = data.recent_activity ? new Date(data.recent_activity) : null;
                    if (recentActivityDate) {
                        updateStatWithAnimation('recent-activity-stat', recentActivityDate.toLocaleDateString());
                    } else {
                        updateStatWithAnimation('recent-activity-stat', 'N/A');
                    }
                } else {
                    console.error('Stats API returned error:', data.error);
                }
            })
            .catch(error => {
                console.error('Error loading framework stats:', error);
                // Show error state
                updateStatWithAnimation('total-frameworks-stat', 'Error');
                updateStatWithAnimation('active-assignments-stat', 'Error');
                updateStatWithAnimation('overall-coverage-stat', 'Error');
                updateStatWithAnimation('recent-activity-stat', 'Error');
            });

        console.log('Loading framework chart data...');
        fetch('/admin/frameworks/chart_data', { credentials: 'include' })
            .then(response => response.json())
            .then(data => {
                console.log('Framework chart data response:', data);
                if (data.success) {
                    renderTopFrameworksChart(data.top_5_frameworks);
                    renderFrameworkTypeChart(data.framework_type_distribution);
                } else {
                    console.error('Chart data API returned error:', data.error);
                }
            })
            .catch(error => console.error('Error loading framework chart data:', error));
    }

    function renderTopFrameworksChart(frameworks) {
        console.log('Rendering top frameworks chart with data:', frameworks);
        const ctx = document.getElementById('topFrameworksChart');
        if (!ctx) {
            console.error('topFrameworksChart element not found');
            return;
        }
        
        new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: frameworks.map(f => f.name),
                datasets: [{
                    label: 'Coverage %',
                    data: frameworks.map(f => f.coverage),
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false,
                            ticks: {
                                font: {
                                    size: 10 // Smaller font size for x-axis labels
                                }
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 10 // Smaller font size for legend
                            }
                        }
                    }
                }
            }
        });
    }

    function renderFrameworkTypeChart(distribution) {
        console.log('Rendering framework type chart with data:', distribution);
        const ctx = document.getElementById('frameworkTypeChart');
        if (!ctx) {
            console.error('frameworkTypeChart element not found');
            return;
        }
        
        new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Global', 'Company'],
                datasets: [{
                    data: [distribution.global, distribution.company],
                    backgroundColor: ['rgba(23, 162, 184, 0.6)', 'rgba(47, 71, 40, 0.6)'],
                    borderColor: ['rgba(23, 162, 184, 1)', 'rgba(47, 71, 40, 1)'],
                    borderWidth: 1,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 10 // Smaller font size for legend
                            }
                        }
                    }
                }
            }
        });
    }

    // Public API
    return {
        initialize: function() {
            console.log('FrameworksStatistics: Initializing...');
            // Wait a bit for DOM to be ready
            setTimeout(() => {
                initializeFrameworkStats();
                console.log('FrameworksStatistics: Initialization complete');
            }, 100);
        },
        
        // Core functions
        updateStatWithAnimation: updateStatWithAnimation,
        initializeFrameworkStats: initializeFrameworkStats,
        renderTopFrameworksChart: renderTopFrameworksChart,
        renderFrameworkTypeChart: renderFrameworkTypeChart,
        
        // Utility functions
        refresh: function() {
            initializeFrameworkStats();
        },

        /**
         * Check if module is ready
         */
        isReady: function() {
            return true; // Statistics module is ready when initialized
        }
    };
})(); 