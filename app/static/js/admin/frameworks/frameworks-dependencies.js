/**
 * Frameworks Dependencies Module
 * Handles dependency tracking and field dependency management
 */

window.FrameworksDependencies = (function() {
    'use strict';

    // Enhanced dependency tracking (exact copy from original)
    function checkFieldDependencies(fieldId) {
        if (!fieldId) return;
        
        fetch(`/admin/fields/${fieldId}/dependants`)
            .then(response => response.json())
            .then(data => {
                const dependencyInfo = document.querySelector(`[data-field-id="${fieldId}"] .dependency-info`);
                if (dependencyInfo) {
                    if (data.dependant_count > 0) {
                        dependencyInfo.innerHTML = `
                            <span class="badge bg-warning" title="This field has dependants">
                                🔗 ${data.dependant_count} dependant(s)
                            </span>
                        `;
                        dependencyInfo.addEventListener('click', () => showDependantsModal(data));
                    } else {
                        dependencyInfo.innerHTML = '';
                    }
                }
            })
            .catch(error => console.error('Error checking dependencies:', error));
    }

    function showDependantsModal(dependencyData) {
        const modalContent = `
            <div class="modal fade" id="dependantsModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Fields Depending on: ${dependencyData.field_name}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p><strong>Dependant Count:</strong> ${dependencyData.dependant_count}</p>
                            <div class="list-group">
                                ${dependencyData.dependants.map(dep => `
                                    <div class="list-group-item">
                                        <strong>${dep.field_name}</strong> (${dep.field_code})
                                        <br><small class="text-muted">Framework: ${dep.framework_name}</small>
                                        <br><small class="text-info">Formula: ${dep.formula_expression}</small>
                                        ${dep.topic_name ? `<br><small class="text-secondary">Topic: ${dep.topic_name}</small>` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('dependantsModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add new modal
        document.body.insertAdjacentHTML('beforeend', modalContent);
        const modal = new bootstrap.Modal(document.getElementById('dependantsModal'));
        modal.show();
        
        // Clean up when modal is hidden
        document.getElementById('dependantsModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    }

    // Setup event delegation for dependency tracking
    function setupDependencyEventListeners() {
        // Event delegation for dependency management
        document.addEventListener('click', function(e) {
            if (e.target.closest('.dependency-info')) {
                const fieldId = e.target.closest('[data-field-id]')?.getAttribute('data-field-id');
                if (fieldId) {
                    checkFieldDependencies(fieldId);
                }
            }
        });
    }

    // Public API
    return {
        initialize: function() {
            console.log('FrameworksDependencies: Initializing...');
            setupDependencyEventListeners();
        },
        
        // Core functions
        checkFieldDependencies: checkFieldDependencies,
        showDependantsModal: showDependantsModal,
        setupDependencyEventListeners: setupDependencyEventListeners,
        
        refresh: function() {
            // Re-check dependencies for all fields
            const fieldsWithDependencies = document.querySelectorAll('[data-field-id]');
            fieldsWithDependencies.forEach(field => {
                const fieldId = field.getAttribute('data-field-id');
                if (fieldId) {
                    checkFieldDependencies(fieldId);
                }
            });
        },
        
        isReady: function() {
            return true;
        }
    };
})(); 