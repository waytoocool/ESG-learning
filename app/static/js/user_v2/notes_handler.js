/**
 * Notes Handler
 * Handles loading existing notes and character counting for the notes field
 */

class NotesHandler {
    constructor(options = {}) {
        this.notesFieldId = options.notesFieldId || 'fieldNotes';
        this.charCountId = options.charCountId || 'notesCharCount';
        this.maxLength = options.maxLength || 1000;
        this.warningThreshold = options.warningThreshold || 750;
        this.dangerThreshold = options.dangerThreshold || 900;

        this.init();
    }

    init() {
        this.attachCharacterCounter();
        console.log('[NotesHandler] Initialized');
    }

    /**
     * Load existing notes for a field
     * @param {string} fieldId - Field ID
     * @param {string} entityId - Entity ID
     * @param {string} reportingDate - Reporting date
     */
    async loadExistingNotes(fieldId, entityId, reportingDate) {
        try {
            const response = await fetch(
                `/api/user/v2/field-data/${fieldId}?entity_id=${entityId}&reporting_date=${reportingDate}`
            );

            if (response.ok) {
                const data = await response.json();
                const notesField = document.getElementById(this.notesFieldId);
                const charCount = document.getElementById(this.charCountId);

                if (data.success && notesField) {
                    // Load notes if they exist
                    if (data.notes) {
                        notesField.value = data.notes;

                        // Update character counter
                        if (charCount) {
                            this.updateCharacterCount(data.notes.length);
                        }
                    } else {
                        // Clear notes field if no notes exist
                        this.clearNotes();
                    }
                }
            } else if (response.status === 404) {
                // No existing data - clear notes field
                this.clearNotes();
            }
        } catch (error) {
            console.error('[NotesHandler] Error loading existing notes:', error);
            // Don't show error to user - just fail silently
            // User can still enter new notes
        }
    }

    /**
     * Clear notes field and reset character counter
     */
    clearNotes() {
        const notesField = document.getElementById(this.notesFieldId);
        const charCount = document.getElementById(this.charCountId);

        if (notesField) notesField.value = '';
        if (charCount) {
            charCount.textContent = '0';
            charCount.classList.remove('text-warning', 'text-danger');
        }
    }

    /**
     * Update character counter display with color coding
     * @param {number} length - Character count
     */
    updateCharacterCount(length) {
        const charCount = document.getElementById(this.charCountId);
        if (!charCount) return;

        charCount.textContent = length;

        // Apply color coding
        if (length > this.dangerThreshold) {
            charCount.classList.add('text-danger');
            charCount.classList.remove('text-warning');
        } else if (length > this.warningThreshold) {
            charCount.classList.add('text-warning');
            charCount.classList.remove('text-danger');
        } else {
            charCount.classList.remove('text-warning', 'text-danger');
        }
    }

    /**
     * Attach character counter event listener to notes field
     */
    attachCharacterCounter() {
        const notesField = document.getElementById(this.notesFieldId);
        const charCount = document.getElementById(this.charCountId);

        if (notesField && charCount) {
            notesField.addEventListener('input', () => {
                const length = notesField.value.length;
                this.updateCharacterCount(length);
            });
            console.log('[NotesHandler] Character counter attached');
        }
    }

    /**
     * Get current notes value
     * @returns {string|null} Notes value or null
     */
    getNotes() {
        const notesField = document.getElementById(this.notesFieldId);
        return notesField ? notesField.value : null;
    }

    /**
     * Set notes value
     * @param {string} notes - Notes text
     */
    setNotes(notes) {
        const notesField = document.getElementById(this.notesFieldId);
        if (notesField) {
            notesField.value = notes || '';
            this.updateCharacterCount(notesField.value.length);
        }
    }
}

// Make available globally for backward compatibility
window.NotesHandler = NotesHandler;

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    if (!window.notesHandler) {
        window.notesHandler = new NotesHandler();

        // Expose loadExistingNotes globally for backward compatibility
        window.loadExistingNotes = function(fieldId, entityId, reportingDate) {
            return window.notesHandler.loadExistingNotes(fieldId, entityId, reportingDate);
        };
    }
});
