/**
 * Dashboard Initialization
 * Phase 4: Advanced features initialization
 * Handles keyboard shortcuts, file uploads, computed field views, performance optimization, and number formatting
 */

class DashboardInitializer {
    constructor() {
        this.features = {
            keyboardShortcuts: null,
            fileUploadHandler: null,
            computedFieldView: null,
            perfOptimizer: null,
            numberFormatter: null,
            autoSaveHandler: null
        };

        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            console.log('[Dashboard Init] Initializing advanced features...');

            this.initializeKeyboardShortcuts();
            this.initializeFileUploadHandler();
            this.initializeComputedFieldView();
            this.initializePerformanceOptimizer();
            this.initializeNumberFormatter();
            this.attachModalEventHandlers();

            console.log('[Dashboard Init] Advanced features initialization complete');
        });
    }

    /**
     * Initialize keyboard shortcuts
     */
    initializeKeyboardShortcuts() {
        try {
            if (typeof KeyboardShortcutHandler !== 'undefined') {
                this.features.keyboardShortcuts = new KeyboardShortcutHandler({
                    onSave: () => {
                        if (this.features.autoSaveHandler && this.features.autoSaveHandler.isActive) {
                            this.features.autoSaveHandler.forceSave();
                        } else {
                            console.log('[Dashboard Init] Save triggered but auto-save not active');
                        }
                    },
                    onSubmit: () => {
                        const submitBtn = document.querySelector('#dataCollectionModal .btn-primary[type="submit"]');
                        if (submitBtn) {
                            submitBtn.click();
                        }
                    },
                    onClose: () => {
                        const modal = document.getElementById('dataCollectionModal');
                        if (modal) {
                            const bsModal = bootstrap.Modal.getInstance(modal);
                            if (bsModal) {
                                bsModal.hide();
                            }
                        }
                    }
                });
                this.features.keyboardShortcuts.enable();
                window.keyboardShortcuts = this.features.keyboardShortcuts;
                console.log('[Dashboard Init] ✅ Keyboard shortcuts initialized');
            }
        } catch (error) {
            console.error('[Dashboard Init] Error initializing keyboard shortcuts:', error);
        }
    }

    /**
     * Initialize file upload handler
     */
    initializeFileUploadHandler() {
        try {
            if (typeof FileUploadHandler !== 'undefined') {
                this.features.fileUploadHandler = new FileUploadHandler({
                    uploadAreaId: 'fileUploadArea',
                    fileInputId: 'fileInput',
                    fileListId: 'fileList'
                });
                window.fileUploadHandler = this.features.fileUploadHandler;
                console.log('[Dashboard Init] ✅ File upload handler initialized');
            }
        } catch (error) {
            console.error('[Dashboard Init] Error initializing file upload handler:', error);
        }
    }

    /**
     * Initialize computed field view
     */
    initializeComputedFieldView() {
        try {
            if (typeof ComputedFieldView !== 'undefined') {
                this.features.computedFieldView = new ComputedFieldView('computed-field-view-container');
                window.computedFieldView = this.features.computedFieldView;
                console.log('[Dashboard Init] ✅ Computed field view initialized');
            }
        } catch (error) {
            console.error('[Dashboard Init] Error initializing computed field view:', error);
        }
    }

    /**
     * Initialize performance optimizer
     */
    initializePerformanceOptimizer() {
        try {
            if (typeof PerformanceOptimizer !== 'undefined') {
                this.features.perfOptimizer = new PerformanceOptimizer({
                    enableLazyLoading: true,
                    enableCaching: true,
                    enableWebWorkers: false
                });
                this.features.perfOptimizer.initialize();
                window.perfOptimizer = this.features.perfOptimizer;
                console.log('[Dashboard Init] ✅ Performance optimizer initialized');
            }
        } catch (error) {
            console.error('[Dashboard Init] Error initializing performance optimizer:', error);
        }
    }

    /**
     * Initialize number formatter
     */
    initializeNumberFormatter() {
        try {
            if (typeof NumberFormatter !== 'undefined') {
                // Create global function to attach formatters
                window.attachNumberFormatters = (container) => {
                    const selector = container
                        ? container.querySelectorAll('input[type="number"], input[data-format="number"]')
                        : document.querySelectorAll('input[type="number"], input[data-format="number"]');

                    selector.forEach(input => {
                        if (input._numberFormatter) return;

                        const formatter = new NumberFormatter({
                            fieldType: input.dataset.fieldType || 'DECIMAL',
                            unit: input.dataset.unit || '',
                            decimals: input.dataset.decimals ? parseInt(input.dataset.decimals) : 2
                        });
                        formatter.attachToInput(input);
                    });
                };

                // Attach to existing inputs
                window.attachNumberFormatters();
                console.log('[Dashboard Init] ✅ Number formatter initialized');

                // Create instance for global use
                this.features.numberFormatter = new NumberFormatter();
                window.numberFormatter = this.features.numberFormatter;
            }
        } catch (error) {
            console.error('[Dashboard Init] Error initializing number formatter:', error);
        }
    }

    /**
     * Attach modal event handlers
     */
    attachModalEventHandlers() {
        const dataCollectionModalEl = document.getElementById('dataCollectionModal');
        if (!dataCollectionModalEl) return;

        // Modal shown event - initialize auto-save
        dataCollectionModalEl.addEventListener('shown.bs.modal', (event) => {
            this.handleModalShown(event);
        });

        // Modal hidden event - cleanup
        dataCollectionModalEl.addEventListener('hidden.bs.modal', async (event) => {
            await this.handleModalHidden(event);
        });
    }

    /**
     * Handle modal shown event
     * @param {Event} event - Modal shown event
     */
    handleModalShown(event) {
        console.log('[Dashboard Init] Modal shown event fired');

        const fieldId = window.currentFieldId;
        if (!fieldId) {
            console.warn('[Dashboard Init] No field ID available for auto-save');
            return;
        }

        // Update keyboard shortcuts state
        if (this.features.keyboardShortcuts) {
            this.features.keyboardShortcuts.setModalOpen(true);
        }

        // Initialize auto-save
        const entityId = window.currentEntityId || null;
        const reportingDate = document.getElementById('reportingDate')?.value;

        if (typeof AutoSaveHandler !== 'undefined' && fieldId && entityId && reportingDate) {
            this.initializeAutoSave(fieldId, entityId, reportingDate);
        } else {
            console.log('[Dashboard Init] Auto-save NOT started - waiting for date selection');
        }
    }

    /**
     * Initialize auto-save handler
     * @param {string} fieldId - Field ID
     * @param {number} entityId - Entity ID
     * @param {string} reportingDate - Reporting date
     */
    initializeAutoSave(fieldId, entityId, reportingDate) {
        try {
            // Stop existing auto-save if any
            if (this.features.autoSaveHandler) {
                this.features.autoSaveHandler.stop();
            }

            // Create new auto-save handler
            this.features.autoSaveHandler = new AutoSaveHandler({
                fieldId: fieldId,
                entityId: entityId,
                reportingDate: reportingDate,
                getFormData: () => {
                    const valueInput = document.getElementById('fieldValue');
                    const notesInput = document.getElementById('fieldNotes');

                    const data = {
                        value: valueInput ? valueInput.value : null,
                        notes: notesInput ? notesInput.value : null
                    };

                    // Capture dimensional data if present
                    if (window.dimensionalDataHandler) {
                        if (typeof window.dimensionalDataHandler.getCurrentData === 'function') {
                            const dimensionalData = window.dimensionalDataHandler.getCurrentData();
                            if (dimensionalData) {
                                data.dimension_values = dimensionalData;
                            }
                        }
                    }

                    return data;
                },
                onSaveSuccess: (result) => {
                    console.log('[Auto-save] Draft saved successfully:', result);
                },
                onSaveError: (error) => {
                    console.error('[Auto-save] Error saving draft:', error);
                },
                onDraftRestored: (draftData) => {
                    console.log('[Dashboard Init] Restoring draft data:', draftData);

                    const valueInput = document.getElementById('fieldValue');
                    const notesInput = document.getElementById('fieldNotes');

                    if (valueInput && draftData.value) {
                        valueInput.value = draftData.value;
                    }
                    if (notesInput && draftData.notes) {
                        notesInput.value = draftData.notes;
                    }

                    // Restore dimensional data if present
                    if (draftData.dimension_values && window.dimensionalDataHandler) {
                        if (typeof window.dimensionalDataHandler.setCurrentData === 'function') {
                            window.dimensionalDataHandler.setCurrentData(draftData.dimension_values);
                            console.log('[Dashboard Init] ✅ Dimensional data restored');
                        }
                    }
                }
            });

            this.features.autoSaveHandler.start();
            window.autoSaveHandler = this.features.autoSaveHandler;
            console.log('[Dashboard Init] ✅ Auto-save started for field:', fieldId);

            // Attach input handlers
            const dataCollectionModalEl = document.getElementById('dataCollectionModal');
            const formInputs = dataCollectionModalEl.querySelectorAll('input, textarea, select');
            formInputs.forEach(input => {
                input.addEventListener('input', () => {
                    if (this.features.autoSaveHandler) {
                        this.features.autoSaveHandler.handleFormChange();
                    }
                });
            });

        } catch (error) {
            console.error('[Dashboard Init] Error initializing auto-save:', error);
        }
    }

    /**
     * Handle modal hidden event
     * @param {Event} event - Modal hidden event
     */
    async handleModalHidden(event) {
        console.log('[Dashboard Init] Modal hidden event fired');

        // Update keyboard shortcuts state
        if (this.features.keyboardShortcuts) {
            this.features.keyboardShortcuts.setModalOpen(false);
        }

        // Save draft immediately if there are unsaved changes
        if (this.features.autoSaveHandler && this.features.autoSaveHandler.isDirty) {
            console.log('[Dashboard Init] Saving draft before closing modal...');
            try {
                await this.features.autoSaveHandler.saveDraft();
                console.log('[Dashboard Init] Draft saved successfully on modal close');
            } catch (error) {
                console.error('[Dashboard Init] Error saving draft on modal close:', error);
            }
        }

        // Stop auto-save
        if (this.features.autoSaveHandler) {
            this.features.autoSaveHandler.stop();
            this.features.autoSaveHandler = null;
            window.autoSaveHandler = null;
            console.log('[Dashboard Init] Auto-save stopped');
        }

        // Reset file upload handler
        if (this.features.fileUploadHandler) {
            this.features.fileUploadHandler.reset();
            console.log('[Dashboard Init] File upload handler reset');
        }

        // Reset computed field view
        if (this.features.computedFieldView) {
            this.features.computedFieldView.reset();
            console.log('[Dashboard Init] Computed field view reset');
        }

        // Reset field tracking
        window.currentFieldId = null;
        window.currentFieldType = null;
    }
}

// Make available globally
window.DashboardInitializer = DashboardInitializer;

// Auto-initialize
if (!window.dashboardInitializer) {
    window.dashboardInitializer = new DashboardInitializer();
}
