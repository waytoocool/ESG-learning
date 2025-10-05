/**
 * Keyboard Shortcuts Handler for User V2 Dashboard
 * =================================================
 *
 * Provides comprehensive keyboard navigation for the data entry interface.
 *
 * Global Shortcuts:
 * - Ctrl/Cmd+S: Save current entry
 * - Ctrl/Cmd+Enter: Submit and close modal
 * - ESC: Close modal (with unsaved changes warning)
 * - Ctrl/Cmd+Shift+N: Open next incomplete field
 * - Ctrl/Cmd+Shift+P: Open previous field
 *
 * Modal-Specific Shortcuts:
 * - Tab: Navigate to next input field
 * - Shift+Tab: Navigate to previous input field
 * - Ctrl/Cmd+D: Duplicate previous period's data
 * - Ctrl/Cmd+R: Clear all fields in current tab
 * - Alt+1/2/3: Switch between modal tabs
 *
 * Table Navigation:
 * - Arrow Up/Down: Navigate between rows
 * - Arrow Left/Right: Navigate between columns
 * - Enter: Open modal for selected field
 * - Space: Toggle field selection
 *
 * Help Overlay:
 * - Ctrl/Cmd+?: Show keyboard shortcuts help
 *
 * Usage:
 *   const shortcuts = new KeyboardShortcutHandler({
 *       onSave: () => { ... },
 *       onSubmit: () => { ... },
 *       onClose: () => { ... },
 *       ...
 *   });
 *   shortcuts.enable();
 */

class KeyboardShortcutHandler {
    constructor(options = {}) {
        // Callbacks
        this.onSave = options.onSave || (() => console.log('Save triggered'));
        this.onSubmit = options.onSubmit || (() => console.log('Submit triggered'));
        this.onClose = options.onClose || (() => console.log('Close triggered'));
        this.onNextField = options.onNextField || (() => console.log('Next field'));
        this.onPreviousField = options.onPreviousField || (() => console.log('Previous field'));
        this.onDuplicatePrevious = options.onDuplicatePrevious || (() => console.log('Duplicate previous'));
        this.onClearFields = options.onClearFields || (() => console.log('Clear fields'));
        this.onSwitchTab = options.onSwitchTab || ((tabIndex) => console.log('Switch to tab', tabIndex));

        // State
        this.isEnabled = false;
        this.isModalOpen = false;
        this.currentSelection = { row: 0, col: 0 };

        // Help overlay
        this.helpOverlay = null;

        // Detect OS for Cmd/Ctrl
        this.isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
        this.modifierKey = this.isMac ? 'metaKey' : 'ctrlKey';

        // Bind event handlers
        this.handleKeyDown = this.handleKeyDown.bind(this);
        this.handleTableKeyNav = this.handleTableKeyNav.bind(this);
        this.showHelp = this.showHelp.bind(this);
        this.hideHelp = this.hideHelp.bind(this);
    }

    /**
     * Enable keyboard shortcuts
     */
    enable() {
        if (this.isEnabled) {
            console.warn('Keyboard shortcuts already enabled');
            return;
        }

        this.isEnabled = true;

        // Add global event listener
        document.addEventListener('keydown', this.handleKeyDown);

        console.log('Keyboard shortcuts enabled');
    }

    /**
     * Disable keyboard shortcuts
     */
    disable() {
        if (!this.isEnabled) return;

        this.isEnabled = false;

        // Remove event listener
        document.removeEventListener('keydown', this.handleKeyDown);

        // Hide help if showing
        this.hideHelp();

        console.log('Keyboard shortcuts disabled');
    }

    /**
     * Set modal state
     */
    setModalOpen(isOpen) {
        this.isModalOpen = isOpen;
    }

    /**
     * Main keyboard event handler
     */
    handleKeyDown(e) {
        if (!this.isEnabled) return;

        const isCtrlOrCmd = e[this.modifierKey];
        const isShift = e.shiftKey;
        const isAlt = e.altKey;
        const key = e.key;

        // Check if user is typing in an input field
        const isInputField = ['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName);

        // Global Shortcuts (work everywhere)
        // -----------------------------------

        // Ctrl/Cmd + ? : Show help
        if (isCtrlOrCmd && (key === '?' || key === '/')) {
            e.preventDefault();
            this.showHelp();
            return;
        }

        // Ctrl/Cmd + S : Save
        if (isCtrlOrCmd && key === 's') {
            e.preventDefault();
            this.onSave();
            this.showFeedback('Saving...');
            return;
        }

        // Ctrl/Cmd + Enter : Submit and close
        if (isCtrlOrCmd && key === 'Enter') {
            e.preventDefault();
            this.onSubmit();
            this.showFeedback('Submitting...');
            return;
        }

        // ESC : Close modal (with warning if unsaved)
        if (key === 'Escape') {
            if (this.isModalOpen) {
                e.preventDefault();
                this.onClose();
                return;
            }
            // Also hide help overlay
            if (this.helpOverlay && this.helpOverlay.style.display !== 'none') {
                e.preventDefault();
                this.hideHelp();
                return;
            }
        }

        // Ctrl/Cmd + Shift + N : Next field
        if (isCtrlOrCmd && isShift && key === 'N') {
            e.preventDefault();
            this.onNextField();
            this.showFeedback('Next field');
            return;
        }

        // Ctrl/Cmd + Shift + P : Previous field
        if (isCtrlOrCmd && isShift && key === 'P') {
            e.preventDefault();
            this.onPreviousField();
            this.showFeedback('Previous field');
            return;
        }

        // Modal-Specific Shortcuts
        // -------------------------
        if (this.isModalOpen) {
            // Ctrl/Cmd + D : Duplicate previous period
            if (isCtrlOrCmd && key === 'd') {
                e.preventDefault();
                this.onDuplicatePrevious();
                this.showFeedback('Duplicating previous period...');
                return;
            }

            // Ctrl/Cmd + R : Clear all fields
            if (isCtrlOrCmd && key === 'r') {
                e.preventDefault();
                if (confirm('Clear all fields in this tab?')) {
                    this.onClearFields();
                    this.showFeedback('Fields cleared');
                }
                return;
            }

            // Alt + 1/2/3 : Switch tabs
            if (isAlt && ['1', '2', '3'].includes(key)) {
                e.preventDefault();
                const tabIndex = parseInt(key) - 1;
                this.onSwitchTab(tabIndex);
                this.showFeedback(`Tab ${key}`);
                return;
            }

            // Tab navigation (only if not in input field)
            if (!isInputField) {
                if (key === 'Tab') {
                    e.preventDefault();
                    this.navigateModalInputs(isShift ? 'previous' : 'next');
                    return;
                }
            }
        }

        // Table Navigation (only when modal is closed and not in input)
        // -------------------------------------------------------------
        if (!this.isModalOpen && !isInputField) {
            this.handleTableKeyNav(e);
        }
    }

    /**
     * Handle table keyboard navigation
     */
    handleTableKeyNav(e) {
        const key = e.key;

        // Arrow keys for navigation
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(key)) {
            e.preventDefault();

            const table = document.querySelector('.data-points-table tbody');
            if (!table) return;

            const rows = table.querySelectorAll('tr');
            const currentRow = rows[this.currentSelection.row];
            if (!currentRow) return;

            const cells = currentRow.querySelectorAll('td');

            // Update selection based on arrow key
            switch (key) {
                case 'ArrowUp':
                    this.currentSelection.row = Math.max(0, this.currentSelection.row - 1);
                    break;
                case 'ArrowDown':
                    this.currentSelection.row = Math.min(rows.length - 1, this.currentSelection.row + 1);
                    break;
                case 'ArrowLeft':
                    this.currentSelection.col = Math.max(0, this.currentSelection.col - 1);
                    break;
                case 'ArrowRight':
                    this.currentSelection.col = Math.min(cells.length - 1, this.currentSelection.col + 1);
                    break;
            }

            // Highlight selected cell
            this.highlightTableCell(this.currentSelection.row, this.currentSelection.col);
            return;
        }

        // Enter: Open modal for selected field
        if (key === 'Enter') {
            e.preventDefault();

            const table = document.querySelector('.data-points-table tbody');
            if (!table) return;

            const rows = table.querySelectorAll('tr');
            const currentRow = rows[this.currentSelection.row];
            if (!currentRow) return;

            const cells = currentRow.querySelectorAll('td');
            const targetCell = cells[this.currentSelection.col];

            // Look for button or clickable element in cell
            const button = targetCell?.querySelector('button, a, [data-field-id]');
            if (button) {
                button.click();
            }
            return;
        }

        // Space: Toggle selection (for future multi-select feature)
        if (key === ' ') {
            e.preventDefault();
            // Placeholder for future implementation
            console.log('Space - toggle selection');
            return;
        }
    }

    /**
     * Highlight table cell for keyboard navigation
     */
    highlightTableCell(row, col) {
        // Remove previous highlights
        document.querySelectorAll('.keyboard-selected').forEach(el => {
            el.classList.remove('keyboard-selected');
        });

        // Add highlight to selected cell
        const table = document.querySelector('.data-points-table tbody');
        if (!table) return;

        const rows = table.querySelectorAll('tr');
        const targetRow = rows[row];
        if (!targetRow) return;

        const cells = targetRow.querySelectorAll('td');
        const targetCell = cells[col];
        if (targetCell) {
            targetCell.classList.add('keyboard-selected');

            // Scroll into view if needed
            targetCell.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
    }

    /**
     * Navigate modal inputs with Tab
     */
    navigateModalInputs(direction) {
        const modal = document.querySelector('.modal.show');
        if (!modal) return;

        const inputs = modal.querySelectorAll('input, textarea, select, button');
        const currentIndex = Array.from(inputs).indexOf(document.activeElement);

        let nextIndex;
        if (direction === 'next') {
            nextIndex = (currentIndex + 1) % inputs.length;
        } else {
            nextIndex = currentIndex <= 0 ? inputs.length - 1 : currentIndex - 1;
        }

        inputs[nextIndex]?.focus();
    }

    /**
     * Show visual feedback for shortcut execution
     */
    showFeedback(message) {
        // Create feedback element if doesn't exist
        let feedback = document.getElementById('keyboard-feedback');

        if (!feedback) {
            feedback = document.createElement('div');
            feedback.id = 'keyboard-feedback';
            feedback.className = 'keyboard-feedback';
            document.body.appendChild(feedback);
        }

        // Show message
        feedback.textContent = message;
        feedback.classList.add('show');

        // Hide after 2 seconds
        setTimeout(() => {
            feedback.classList.remove('show');
        }, 2000);
    }

    /**
     * Show keyboard shortcuts help overlay
     */
    showHelp() {
        // Create help overlay if doesn't exist
        if (!this.helpOverlay) {
            this.helpOverlay = this.createHelpOverlay();
            document.body.appendChild(this.helpOverlay);
        }

        this.helpOverlay.style.display = 'flex';
    }

    /**
     * Hide keyboard shortcuts help overlay
     */
    hideHelp() {
        if (this.helpOverlay) {
            this.helpOverlay.style.display = 'none';
        }
    }

    /**
     * Create help overlay element
     */
    createHelpOverlay() {
        const modKey = this.isMac ? 'Cmd' : 'Ctrl';

        const overlay = document.createElement('div');
        overlay.className = 'keyboard-shortcuts-help-overlay';
        overlay.innerHTML = `
            <div class="help-content">
                <div class="help-header">
                    <h2>Keyboard Shortcuts</h2>
                    <button class="close-help" onclick="this.closest('.keyboard-shortcuts-help-overlay').style.display='none'">
                        &times;
                    </button>
                </div>

                <div class="help-sections">
                    <div class="help-section">
                        <h3>Global Shortcuts</h3>
                        <table class="shortcuts-table">
                            <tr>
                                <td><kbd>${modKey}</kbd> + <kbd>S</kbd></td>
                                <td>Save current entry</td>
                            </tr>
                            <tr>
                                <td><kbd>${modKey}</kbd> + <kbd>Enter</kbd></td>
                                <td>Submit and close modal</td>
                            </tr>
                            <tr>
                                <td><kbd>ESC</kbd></td>
                                <td>Close modal</td>
                            </tr>
                            <tr>
                                <td><kbd>${modKey}</kbd> + <kbd>Shift</kbd> + <kbd>N</kbd></td>
                                <td>Open next incomplete field</td>
                            </tr>
                            <tr>
                                <td><kbd>${modKey}</kbd> + <kbd>Shift</kbd> + <kbd>P</kbd></td>
                                <td>Open previous field</td>
                            </tr>
                            <tr>
                                <td><kbd>${modKey}</kbd> + <kbd>?</kbd></td>
                                <td>Show this help</td>
                            </tr>
                        </table>
                    </div>

                    <div class="help-section">
                        <h3>Modal Shortcuts</h3>
                        <table class="shortcuts-table">
                            <tr>
                                <td><kbd>Tab</kbd></td>
                                <td>Navigate to next input</td>
                            </tr>
                            <tr>
                                <td><kbd>Shift</kbd> + <kbd>Tab</kbd></td>
                                <td>Navigate to previous input</td>
                            </tr>
                            <tr>
                                <td><kbd>${modKey}</kbd> + <kbd>D</kbd></td>
                                <td>Duplicate previous period</td>
                            </tr>
                            <tr>
                                <td><kbd>${modKey}</kbd> + <kbd>R</kbd></td>
                                <td>Clear all fields</td>
                            </tr>
                            <tr>
                                <td><kbd>Alt</kbd> + <kbd>1/2/3</kbd></td>
                                <td>Switch between tabs</td>
                            </tr>
                        </table>
                    </div>

                    <div class="help-section">
                        <h3>Table Navigation</h3>
                        <table class="shortcuts-table">
                            <tr>
                                <td><kbd>↑</kbd> <kbd>↓</kbd></td>
                                <td>Navigate between rows</td>
                            </tr>
                            <tr>
                                <td><kbd>←</kbd> <kbd>→</kbd></td>
                                <td>Navigate between columns</td>
                            </tr>
                            <tr>
                                <td><kbd>Enter</kbd></td>
                                <td>Open modal for selected field</td>
                            </tr>
                            <tr>
                                <td><kbd>Space</kbd></td>
                                <td>Toggle field selection</td>
                            </tr>
                        </table>
                    </div>
                </div>

                <div class="help-footer">
                    <p>Press <kbd>ESC</kbd> to close this help</p>
                </div>
            </div>
        `;

        // Click outside to close
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                this.hideHelp();
            }
        });

        return overlay;
    }

    /**
     * Reset table selection
     */
    resetSelection() {
        this.currentSelection = { row: 0, col: 0 };
        document.querySelectorAll('.keyboard-selected').forEach(el => {
            el.classList.remove('keyboard-selected');
        });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KeyboardShortcutHandler;
}
