/**
 * Frameworks Permissions Module
 * Handles permission-based functionality and access control
 */

window.FrameworksPermissions = (function() {
    'use strict';

    // Permission-based Action Handling (exact copy from original)
    function handleFrameworkPermissions() {
        const frameworkCards = document.querySelectorAll('.framework-card');
        
        frameworkCards.forEach(card => {
            const isGlobal = card.getAttribute('data-is-global') === 'true';
            const isEditable = card.getAttribute('data-is-editable') === 'true';
            
            // If it's a global framework and not editable by current user
            if (isGlobal && !isEditable) {
                // Add read-only styling if not already present
                if (!card.classList.contains('read-only')) {
                    card.classList.add('read-only');
                }
                
                // Disable any edit/delete buttons (if they exist in the future)
                const editButtons = card.querySelectorAll('.btn-edit, .btn-delete, .edit-framework-btn, .delete-framework-btn');
                editButtons.forEach(btn => {
                    btn.disabled = true;
                    btn.classList.add('disabled');
                    btn.title = 'Global frameworks can only be edited by their owners';
                });
                
                // Add tooltip to the card
                card.title = 'This is a global framework - read-only access';
            }
        });
    }

    // Check if user has specific permission
    function hasPermission(permission) {
        // This would typically check against user's permissions
        // For now, return true as a placeholder
        return true;
    }

    // Check if framework is editable by current user
    function isFrameworkEditable(frameworkCard) {
        const isGlobal = frameworkCard.getAttribute('data-is-global') === 'true';
        const isEditable = frameworkCard.getAttribute('data-is-editable') === 'true';
        
        return !isGlobal || isEditable;
    }

    // Apply permission-based styling to UI elements
    function applyPermissionStyling() {
        const restrictedElements = document.querySelectorAll('[data-permission-required]');
        
        restrictedElements.forEach(element => {
            const requiredPermission = element.getAttribute('data-permission-required');
            
            if (!hasPermission(requiredPermission)) {
                element.classList.add('disabled');
                element.setAttribute('disabled', 'disabled');
                element.title = 'You do not have permission to perform this action';
            }
        });
    }

    // Setup permission-based event listeners
    function setupPermissionEventListeners() {
        document.addEventListener('click', function(e) {
            // Check if clicked element requires permission
            const element = e.target.closest('[data-permission-required]');
            if (element) {
                const requiredPermission = element.getAttribute('data-permission-required');
                
                if (!hasPermission(requiredPermission)) {
                    e.preventDefault();
                    e.stopPropagation();
                    alert('You do not have permission to perform this action');
                    return false;
                }
            }
            
            // Check framework-specific permissions
            const frameworkElement = e.target.closest('.framework-card');
            if (frameworkElement && e.target.closest('.edit-framework-btn, .delete-framework-btn')) {
                if (!isFrameworkEditable(frameworkElement)) {
                    e.preventDefault();
                    e.stopPropagation();
                    alert('You do not have permission to edit this framework');
                    return false;
                }
            }
        });
    }

    // Public API
    return {
        initialize: function() {
            console.log('FrameworksPermissions: Initializing...');
            handleFrameworkPermissions();
            applyPermissionStyling();
            setupPermissionEventListeners();
        },
        
        // Core functions
        handleFrameworkPermissions: handleFrameworkPermissions,
        hasPermission: hasPermission,
        isFrameworkEditable: isFrameworkEditable,
        applyPermissionStyling: applyPermissionStyling,
        setupPermissionEventListeners: setupPermissionEventListeners,
        
        refresh: function() {
            handleFrameworkPermissions();
            applyPermissionStyling();
        },
        
        isReady: function() {
            return true;
        }
    };
})(); 