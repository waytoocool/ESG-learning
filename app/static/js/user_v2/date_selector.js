/**
 * Compact Date Selector Component
 *
 * Displays valid reporting dates based on assignment frequency with completion status.
 * Features:
 * - Frequency-aware (Monthly/Quarterly/Annual)
 * - Color-coded status (Complete/Pending/Selected)
 * - Fiscal year integration
 * - Dimensional data support
 */

class DateSelector {
    constructor(options = {}) {
        this.fieldId = options.fieldId;
        this.entityId = options.entityId;
        this.fyYear = options.fyYear;
        this.containerId = options.containerId || 'dateSelectorContainer';
        this.onDateSelect = options.onDateSelect || (() => {});

        this.dates = [];
        this.selectedDate = null;
        this.frequency = null;
        this.fyDisplay = null;
    }

    /**
     * Initialize and load dates from API
     */
    async init() {
        try {
            const response = await fetch(
                `/api/user/v2/field-dates/${this.fieldId}?entity_id=${this.entityId}&fy_year=${this.fyYear}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to load dates');
            }

            this.dates = data.valid_dates;
            this.frequency = data.frequency;
            this.fyDisplay = data.fy_display;
            this.fieldName = data.field_name;
            this.hasDimensions = data.has_dimensions;
            this.requiredCombinationsCount = data.required_combinations_count;

            this.render();

            return {
                success: true,
                datesCount: this.dates.length
            };

        } catch (error) {
            console.error('[DateSelector] Error loading dates:', error);
            this.renderError(error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Render the date selector (Mini Calendar Popup version)
     */
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error('[DateSelector] Container not found:', this.containerId);
            return;
        }

        // Count completion stats
        const completeCount = this.dates.filter(d => d.status === 'complete').length;
        const pendingCount = this.dates.filter(d => d.status === 'pending').length;
        const overdueCount = this.dates.filter(d => d.status === 'overdue').length;

        // Selected date display text
        const selectedDateText = this.selectedDate
            ? this.formatDateLong(this.selectedDate)
            : 'Select a reporting date...';

        container.innerHTML = `
            <div class="date-selector-component">
                <!-- Compact Button Trigger -->
                <div class="date-selector-header">
                    <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center gap-2">
                            <span class="material-icons text-sm text-gray-500">calendar_today</span>
                            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                                Reporting Date
                            </span>
                            <span class="text-xs text-gray-500 dark:text-gray-400">
                                (${this.fyDisplay})
                            </span>
                        </div>
                        <span class="text-xs px-2 py-1 rounded ${this.getFrequencyBadgeClass()}">
                            ${this.frequency}
                        </span>
                    </div>
                </div>

                <!-- Compact Date Picker Button -->
                <button type="button"
                        id="datePickerButton"
                        class="date-picker-button">
                    <span class="material-icons">event</span>
                    <span class="date-picker-text">${selectedDateText}</span>
                    <span class="material-icons">expand_more</span>
                </button>

                <!-- Mini Calendar Popup (Hidden by default) -->
                <div id="dateCalendarPopup" class="date-calendar-popup" style="display: none;">
                    <div class="date-calendar-container">
                        <!-- Calendar Header -->
                        <div class="calendar-header">
                            <div class="text-sm font-medium">${this.fyDisplay}</div>
                            <div class="flex items-center gap-2 text-xs">
                                <div class="flex items-center gap-1">
                                    <span class="status-dot complete"></span>
                                    <span>${completeCount} Complete</span>
                                </div>
                                <div class="flex items-center gap-1">
                                    <span class="status-dot pending"></span>
                                    <span>${pendingCount} Pending</span>
                                </div>
                                ${overdueCount > 0 ? `
                                <div class="flex items-center gap-1">
                                    <span class="status-dot overdue"></span>
                                    <span>${overdueCount} Overdue</span>
                                </div>
                                ` : ''}
                            </div>
                        </div>

                        <!-- Calendar Grid -->
                        <div class="calendar-grid">
                            ${this.renderCalendarGrid()}
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Attach click handlers
        this.attachEventHandlers();
    }

    /**
     * Render calendar grid based on frequency
     */
    renderCalendarGrid() {
        if (this.frequency === 'Annual') {
            return this.renderAnnualCalendar();
        } else if (this.frequency === 'Quarterly') {
            return this.renderQuarterlyCalendar();
        } else {
            return this.renderMonthlyCalendar();
        }
    }

    /**
     * Render annual calendar (single date)
     */
    renderAnnualCalendar() {
        const dateInfo = this.dates[0];
        return `
            <div class="calendar-annual">
                ${this.renderDateChip(dateInfo)}
            </div>
        `;
    }

    /**
     * Render quarterly calendar (4 quarters in 2x2 grid)
     */
    renderQuarterlyCalendar() {
        return `
            <div class="calendar-quarterly">
                ${this.dates.map((dateInfo, index) => {
                    const quarter = `Q${index + 1}`;
                    return `
                        <div class="quarter-item">
                            <div class="quarter-label">${quarter}</div>
                            ${this.renderDateChip(dateInfo)}
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    /**
     * Render monthly calendar (12 months in 3x4 grid)
     */
    renderMonthlyCalendar() {
        return `
            <div class="calendar-monthly">
                ${this.dates.map(dateInfo => {
                    const date = new Date(dateInfo.date + 'T00:00:00');
                    const monthName = date.toLocaleString('default', { month: 'short' });
                    return `
                        <div class="month-item">
                            <div class="month-label">${monthName}</div>
                            ${this.renderDateChip(dateInfo)}
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    /**
     * Render individual date chip
     */
    renderDateChip(dateInfo) {
        const isSelected = this.selectedDate === dateInfo.date;
        const statusClass = isSelected ? 'selected' : dateInfo.status;

        return `
            <button type="button"
                    class="date-chip ${statusClass}"
                    data-date="${dateInfo.date}"
                    title="${this.formatDateLong(dateInfo.date)} - ${dateInfo.status}">
                <span class="date-label">${this.formatDateShort(dateInfo.date)}</span>
            </button>
        `;
    }

    /**
     * Get grid columns based on frequency
     */
    getGridColumns() {
        switch (this.frequency) {
            case 'Annual':
                return 1;
            case 'Quarterly':
                return 4;
            case 'Monthly':
                return 4; // 4 columns for monthly (3 rows)
            default:
                return 3;
        }
    }

    /**
     * Get frequency badge color class
     */
    getFrequencyBadgeClass() {
        switch (this.frequency) {
            case 'Annual':
                return 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200';
            case 'Quarterly':
                return 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200';
            case 'Monthly':
                return 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200';
            default:
                return 'bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200';
        }
    }

    /**
     * Format date for display (short)
     */
    formatDateShort(dateStr) {
        const date = new Date(dateStr + 'T00:00:00');
        const month = date.toLocaleString('default', { month: 'short' });
        const day = date.getDate();
        return `${month} ${day}`;
    }

    /**
     * Format date for display (long)
     */
    formatDateLong(dateStr) {
        const date = new Date(dateStr + 'T00:00:00');
        return date.toLocaleDateString('default', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    /**
     * Attach event handlers to date chips and popup controls
     */
    attachEventHandlers() {
        // Date picker button - toggle popup
        const pickerButton = document.getElementById('datePickerButton');
        const popup = document.getElementById('dateCalendarPopup');

        if (pickerButton && popup) {
            pickerButton.addEventListener('click', (e) => {
                e.stopPropagation();
                const isVisible = popup.style.display !== 'none';
                popup.style.display = isVisible ? 'none' : 'block';
            });

            // Close popup when clicking outside
            document.addEventListener('click', (e) => {
                if (popup.style.display === 'block' &&
                    !popup.contains(e.target) &&
                    !pickerButton.contains(e.target)) {
                    popup.style.display = 'none';
                }
            });
        }

        // Date chip click handlers
        const chips = document.querySelectorAll('.date-chip');
        chips.forEach(chip => {
            chip.addEventListener('click', (e) => {
                const date = e.currentTarget.dataset.date;
                this.selectDate(date);
            });
        });
    }

    /**
     * Select a date
     */
    selectDate(date) {
        this.selectedDate = date;

        // Update visual state
        document.querySelectorAll('.date-chip').forEach(chip => {
            chip.classList.remove('selected');
            if (chip.dataset.date === date) {
                chip.classList.add('selected');
            }
        });

        // Update button text
        const pickerButton = document.querySelector('.date-picker-text');
        if (pickerButton) {
            pickerButton.textContent = this.formatDateLong(date);
        }

        // Close popup
        const popup = document.getElementById('dateCalendarPopup');
        if (popup) {
            popup.style.display = 'none';
        }

        // Get date info
        const dateInfo = this.dates.find(d => d.date === date);

        // Call callback
        this.onDateSelect({
            date: date,
            dateFormatted: this.formatDateLong(date),
            status: dateInfo?.status || 'unknown',
            hasDimensionalData: dateInfo?.has_dimensional_data || false
        });
    }

    /**
     * Get selected date
     */
    getSelectedDate() {
        return this.selectedDate;
    }

    /**
     * Render error state
     */
    renderError(errorMessage) {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="date-selector-error">
                <div class="flex items-center gap-2 text-red-600 dark:text-red-400">
                    <span class="material-icons text-sm">error</span>
                    <span class="text-sm">Failed to load dates: ${errorMessage}</span>
                </div>
            </div>
        `;
    }

    /**
     * Refresh dates from API
     */
    async refresh() {
        return await this.init();
    }

    /**
     * Update fiscal year and reload
     */
    async updateFiscalYear(fyYear) {
        this.fyYear = fyYear;
        return await this.init();
    }

    /**
     * Destroy the date selector
     */
    destroy() {
        const container = document.getElementById(this.containerId);
        if (container) {
            container.innerHTML = '';
        }
        this.dates = [];
        this.selectedDate = null;
    }
}

// Export for use in other modules
window.DateSelector = DateSelector;
