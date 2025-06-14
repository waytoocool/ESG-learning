// Enhanced Reusable Notification System
const PopupManager = {
    activePopups: new Set(),
    maxPopups: 3,

    init() {
        // Create popup container if it doesn't exist
        if (!document.getElementById('notificationPopup')) {
            const popupHTML = `
                <div id="notificationPopup" class="popup-message">
                    <div class="popup-header">
                        <div id="popupTitle" class="popup-title"></div>
                        <button class="close-button" aria-label="Close notification">&times;</button>
                    </div>
                    <div id="popupMessage" class="popup-content"></div>
                    <div class="progress-bar"></div>
                </div>`;
            document.body.insertAdjacentHTML('beforeend', popupHTML);
        }
        
        // Add event listener for close button
        document.querySelector('#notificationPopup .close-button')?.addEventListener('click', () => {
            this.closePopup();
        });

        // Add keyboard accessibility
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllPopups();
            }
        });
    },

    showPopup(title, message, type = 'info', duration = 4000, persistent = false) {
        // Limit number of active popups
        if (this.activePopups.size >= this.maxPopups) {
            this.closeOldestPopup();
        }

        const popup = document.getElementById('notificationPopup');
        const titleElement = document.getElementById('popupTitle');
        const messageElement = document.getElementById('popupMessage');
        const progressBar = popup.querySelector('.progress-bar');

        // Clear existing classes and add new ones
        popup.className = 'popup-message';
        popup.classList.add(type);

        // Set content with icons
        const icon = this.getIcon(type);
        titleElement.innerHTML = `${icon}${title}`;
        messageElement.innerHTML = message;
        
        // Show popup with animation
        popup.classList.add('show');
        this.activePopups.add(popup);

        // Handle progress bar and auto-dismiss
        if (!persistent && duration > 0) {
            if (progressBar) {
                progressBar.style.animationDuration = `${duration}ms`;
            }
            
            setTimeout(() => {
                this.closePopup();
            }, duration);
        } else if (progressBar) {
            progressBar.style.display = 'none';
        }

        // Add focus for screen readers
        popup.setAttribute('role', 'alert');
        popup.setAttribute('aria-live', 'polite');
        
        return popup;
    },

    showSuccess(title, message, duration = 4000) {
        return this.showPopup(title, message, 'success', duration);
    },

    showError(title, message, persistent = true) {
        return this.showPopup(title, message, 'error', persistent ? 0 : 6000, persistent);
    },

    showWarning(title, message, duration = 5000) {
        return this.showPopup(title, message, 'warning', duration);
    },

    showInfo(title, message, duration = 4000) {
        return this.showPopup(title, message, 'info', duration);
    },

    getIcon(type) {
        const icons = {
            success: '<i class="fas fa-check-circle"></i>',
            error: '<i class="fas fa-times-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>',
            info: '<i class="fas fa-info-circle"></i>',
            notice: '<i class="fas fa-bell"></i>'
        };
        return icons[type] || icons.info;
    },

    closePopup(popupElement = null) {
        const popup = popupElement || document.getElementById('notificationPopup');
        if (!popup || !popup.classList.contains('show')) return;

        popup.classList.add('hide');
        this.activePopups.delete(popup);
        
        popup.addEventListener('animationend', () => {
            popup.classList.remove('show', 'hide');
            popup.removeAttribute('role');
            popup.removeAttribute('aria-live');
            
            // Reset progress bar
            const progressBar = popup.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.display = 'block';
                progressBar.style.animationDuration = '4s';
            }
        }, { once: true });
    },

    closeOldestPopup() {
        if (this.activePopups.size > 0) {
            const oldestPopup = this.activePopups.values().next().value;
            this.closePopup(oldestPopup);
        }
    },

    closeAllPopups() {
        Array.from(this.activePopups).forEach(popup => {
            this.closePopup(popup);
        });
    },

    // Utility method for quick notifications
    toast(message, type = 'info', duration = 3000) {
        return this.showPopup(
            type.charAt(0).toUpperCase() + type.slice(1), 
            message, 
            type, 
            duration
        );
    },

    // Method for confirmation-style notifications
    confirm(title, message, onConfirm, onCancel) {
        const popup = this.showPopup(title, message + `
            <div class="mt-3">
                <button class="btn btn-sm btn-success me-2" id="confirmBtn">
                    <i class="fas fa-check"></i> Confirm
                </button>
                <button class="btn btn-sm btn-secondary" id="cancelBtn">
                    <i class="fas fa-times"></i> Cancel
                </button>
            </div>
        `, 'warning', 0, true);

        // Add event listeners for buttons
        popup.querySelector('#confirmBtn')?.addEventListener('click', () => {
            this.closePopup(popup);
            if (onConfirm) onConfirm();
        });

        popup.querySelector('#cancelBtn')?.addEventListener('click', () => {
            this.closePopup(popup);
            if (onCancel) onCancel();
        });

        return popup;
    }
};

// Export for ES6 modules
export { PopupManager };

// Make PopupManager globally available for backward compatibility
window.PopupManager = PopupManager;

// Auto-initialize when script loads
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => PopupManager.init());
    } else {
        PopupManager.init();
    }
    console.log('✅ Global PopupManager initialized');
}

// For backward compatibility
function showPopup(title, message, type) {
    PopupManager.showPopup(title, message, type);
}

// Export backward compatibility function as well
export { showPopup };