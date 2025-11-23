/**
 * Auto-Save Handler for User V2 Dashboard
 * =========================================
 *
 * Handles automatic saving of draft data during form editing.
 *
 * Features:
 * - Auto-save every 30 seconds of inactivity
 * - localStorage backup for offline support
 * - Save status indicator
 * - Draft recovery on modal open
 * - Conflict resolution
 *
 * Usage:
 *   const autoSave = new AutoSaveHandler({
 *       fieldId: 123,
 *       entityId: 456,
 *       reportingDate: '2025-01-15',
 *       getFormData: () => { return {...} },
 *       onSaveSuccess: (result) => { console.log('Saved!') },
 *       onSaveError: (error) => { console.error('Error!') }
 *   });
 *   autoSave.start();
 */

class AutoSaveHandler {
    constructor(options = {}) {
        // Required options
        this.fieldId = options.fieldId;
        this.entityId = options.entityId;
        this.reportingDate = options.reportingDate;
        this.getFormData = options.getFormData; // Function that returns current form state

        // Optional callbacks
        this.onSaveSuccess = options.onSaveSuccess || (() => {});
        this.onSaveError = options.onSaveError || ((error) => console.error('Auto-save error:', error));
        this.onDraftRestored = options.onDraftRestored || (() => {});

        // Configuration
        this.autoSaveInterval = options.autoSaveInterval || 30000; // 30 seconds
        this.localStorageKey = `draft_${this.fieldId}_${this.entityId}_${this.reportingDate}`;
        this.apiEndpoint = '/api/user/v2';

        // State
        this.autoSaveTimer = null;
        this.lastSaveTimestamp = null;
        this.draftId = null;
        this.isSaving = false;
        this.isDirty = false; // Has unsaved changes
        this.isActive = false;

        // Status indicator element (will be created)
        this.statusElement = null;

        // Bind methods
        this.handleFormChange = this.handleFormChange.bind(this);
        this.saveDraft = this.saveDraft.bind(this);
        this.restoreDraft = this.restoreDraft.bind(this);
    }

    /**
     * Start auto-save functionality
     */
    start() {
        if (this.isActive) {
            console.warn('Auto-save already active');
            return;
        }

        this.isActive = true;
        this.createStatusIndicator();

        // Check for existing draft
        this.checkForDraft();

        console.log(`Auto-save started for field ${this.fieldId}`);
    }

    /**
     * Stop auto-save functionality
     */
    stop() {
        if (!this.isActive) return;

        this.isActive = false;

        // Clear timer
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
            this.autoSaveTimer = null;
        }

        // Remove status indicator
        if (this.statusElement) {
            this.statusElement.remove();
            this.statusElement = null;
        }

        console.log(`Auto-save stopped for field ${this.fieldId}`);
    }

    /**
     * Handle form change event
     * Resets the auto-save timer
     */
    handleFormChange() {
        if (!this.isActive) return;

        this.isDirty = true;

        // Reset timer
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }

        // Start new timer
        this.autoSaveTimer = setTimeout(() => {
            if (this.isDirty) {
                this.saveDraft();
            }
        }, this.autoSaveInterval);

        // Update status
        this.updateStatus('pending', 'Unsaved changes');
    }

    /**
     * Save draft to localStorage only
     */
    async saveDraft() {
        if (this.isSaving || !this.isDirty) return;

        this.isSaving = true;
        this.updateStatus('saving', 'Saving draft...');

        try {
            // Get current form data
            const formData = this.getFormData();

            // Save to localStorage
            this.saveToLocalStorage(formData);

            this.lastSaveTimestamp = new Date();
            this.isDirty = false;

            this.updateStatus('saved', `Saved at ${this.formatTime(this.lastSaveTimestamp)}`);
            this.onSaveSuccess({ success: true, timestamp: this.lastSaveTimestamp });

        } catch (error) {
            console.error('Error saving draft:', error);
            this.updateStatus('error', 'Auto-save failed');
            this.onSaveError(error);
        } finally {
            this.isSaving = false;
        }
    }

    /**
     * Save draft to localStorage
     */
    saveToLocalStorage(formData) {
        try {
            const draftData = {
                formData: formData,
                timestamp: new Date().toISOString(),
                fieldId: this.fieldId,
                entityId: this.entityId,
                reportingDate: this.reportingDate
            };

            localStorage.setItem(this.localStorageKey, JSON.stringify(draftData));
        } catch (error) {
            if (error.name === 'QuotaExceededError') {
                console.error('localStorage quota exceeded');
                // Try to clear old drafts
                this.cleanupLocalStorage();
            } else {
                console.error('Error saving to localStorage:', error);
            }
        }
    }

    /**
     * Check for existing draft from localStorage
     */
    async checkForDraft() {
        try {
            // Check localStorage
            const localDraft = this.getFromLocalStorage();
            if (localDraft) {
                this.showDraftRestorePrompt(localDraft.formData, 'local', localDraft.timestamp);
            }
        } catch (error) {
            console.error('Error checking for draft:', error);
        }
    }

    /**
     * Get draft from localStorage
     */
    getFromLocalStorage() {
        try {
            const data = localStorage.getItem(this.localStorageKey);
            if (data) {
                return JSON.parse(data);
            }
        } catch (error) {
            console.error('Error reading from localStorage:', error);
        }
        return null;
    }

    /**
     * Show draft restore prompt
     */
    showDraftRestorePrompt(draftData, source, timestamp) {
        const age = this.calculateAge(timestamp);
        const sourceText = source === 'server' ? 'on server' : 'locally';

        const message = `Found unsaved draft from ${age} ago (saved ${sourceText}). Restore it?`;

        if (confirm(message)) {
            this.restoreDraft(draftData);
        } else {
            // User declined, discard the draft
            this.discardDraft();
        }
    }

    /**
     * Restore draft data to form
     */
    restoreDraft(draftData) {
        try {
            this.onDraftRestored(draftData);
            this.isDirty = false;
            this.updateStatus('restored', 'Draft restored');

            // Clear localStorage since we've restored
            this.clearLocalStorage();
        } catch (error) {
            console.error('Error restoring draft:', error);
            alert('Error restoring draft. Please try again.');
        }
    }

    /**
     * Discard current draft
     */
    async discardDraft() {
        if (!this.draftId) {
            // No server draft, just clear localStorage
            this.clearLocalStorage();
            return;
        }

        try {
            const response = await fetch(`${this.apiEndpoint}/discard-draft/${this.draftId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                this.draftId = null;
                this.clearLocalStorage();
                this.updateStatus('idle', 'Ready');
            }
        } catch (error) {
            console.error('Error discarding draft:', error);
        }
    }

    /**
     * Clear localStorage draft
     */
    clearLocalStorage() {
        try {
            localStorage.removeItem(this.localStorageKey);
        } catch (error) {
            console.error('Error clearing localStorage:', error);
        }
    }

    /**
     * Clean up old localStorage drafts
     */
    cleanupLocalStorage() {
        const maxAge = 7 * 24 * 60 * 60 * 1000; // 7 days in milliseconds

        try {
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key && key.startsWith('draft_')) {
                    const data = JSON.parse(localStorage.getItem(key));
                    const age = new Date() - new Date(data.timestamp);

                    if (age > maxAge) {
                        localStorage.removeItem(key);
                    }
                }
            }
        } catch (error) {
            console.error('Error cleaning up localStorage:', error);
        }
    }

    /**
     * Create status indicator element
     */
    createStatusIndicator() {
        // Look for existing status container in modal header
        let container = document.querySelector('.auto-save-status-container');

        if (!container) {
            // Create container if it doesn't exist
            container = document.createElement('div');
            container.className = 'auto-save-status-container';

            // Try to insert into modal header
            const modalHeader = document.querySelector('.modal-header');
            if (modalHeader) {
                modalHeader.appendChild(container);
            } else {
                // Fallback to body
                document.body.appendChild(container);
            }
        }

        // Create status element
        this.statusElement = document.createElement('div');
        this.statusElement.className = 'auto-save-status';
        this.statusElement.innerHTML = `
            <span class="status-icon"></span>
            <span class="status-text">Ready</span>
        `;

        container.appendChild(this.statusElement);
    }

    /**
     * Update status indicator
     */
    updateStatus(status, text) {
        if (!this.statusElement) return;

        const icon = this.statusElement.querySelector('.status-icon');
        const textEl = this.statusElement.querySelector('.status-text');

        // Remove all status classes
        this.statusElement.classList.remove('status-pending', 'status-saving', 'status-saved', 'status-error', 'status-restored');

        // Add new status class
        this.statusElement.classList.add(`status-${status}`);

        // Update icon
        const icons = {
            idle: '',
            pending: '⚠️',
            saving: '⏳',
            saved: '✓',
            error: '❌',
            restored: '↺'
        };
        icon.textContent = icons[status] || '';

        // Update text
        textEl.textContent = text;
    }

    /**
     * Format time for display
     */
    formatTime(date) {
        if (!date) return '';

        const d = new Date(date);
        const hours = d.getHours().toString().padStart(2, '0');
        const minutes = d.getMinutes().toString().padStart(2, '0');

        return `${hours}:${minutes}`;
    }

    /**
     * Calculate age of draft
     */
    calculateAge(timestamp) {
        const now = new Date();
        const then = new Date(timestamp);
        const diff = now - then;

        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days} day${days > 1 ? 's' : ''}`;
        if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''}`;
        if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''}`;
        return 'just now';
    }

    /**
     * Force immediate save
     */
    forceSave() {
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }

        this.isDirty = true;
        return this.saveDraft();
    }

    /**
     * Update reporting date and migrate localStorage key
     * Used when date is selected after modal opens
     * @param {string} newDate - New reporting date (YYYY-MM-DD)
     */
    updateReportingDate(newDate) {
        if (!newDate) {
            console.warn('AutoSaveHandler.updateReportingDate: Invalid date provided');
            return;
        }

        const oldKey = this.localStorageKey;

        // Update reporting date
        this.reportingDate = newDate;
        this.localStorageKey = `draft_${this.fieldId}_${this.entityId}_${this.reportingDate}`;

        console.log(`Auto-save: Updated date from ${oldKey} to ${this.localStorageKey}`);

        // If there was data in memory with undefined date, save it now with proper date
        if (this.isDirty) {
            this.forceSave();
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AutoSaveHandler;
}
