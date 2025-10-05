/**
 * Smart Number Formatter for User V2 Dashboard
 * =============================================
 *
 * Provides intelligent number formatting for data entry fields.
 *
 * Features:
 * - Thousand separators (1,234,567)
 * - Decimal precision based on field type
 * - Scientific notation support (1.5E+6)
 * - Currency symbols ($ € £)
 * - Percentage handling (50% → 0.5)
 * - Unit conversion suggestions
 *
 * Field Types Supported:
 * - INTEGER: No decimals, thousand separators
 * - DECIMAL: 2 decimals (configurable), thousand separators
 * - PERCENTAGE: 2 decimals + %
 * - CURRENCY: 2 decimals + symbol
 * - SCIENTIFIC: 2 significant figures + E notation
 *
 * Usage:
 *   const formatter = new NumberFormatter({
 *       fieldType: 'DECIMAL',
 *       unit: 'kWh',
 *       decimals: 2
 *   });
 *
 *   // Format for display
 *   const display = formatter.format(1234567.89);  // "1,234,567.89"
 *
 *   // Parse for editing
 *   const raw = formatter.parse("1,234,567.89");  // 1234567.89
 *
 *   // Apply to input element
 *   formatter.attachToInput(inputElement);
 */

class NumberFormatter {
    constructor(options = {}) {
        // Configuration
        this.fieldType = options.fieldType || 'DECIMAL';  // INTEGER, DECIMAL, PERCENTAGE, CURRENCY, SCIENTIFIC
        this.unit = options.unit || '';
        this.decimals = options.decimals !== undefined ? options.decimals : this.getDefaultDecimals();
        this.currencySymbol = options.currencySymbol || '$';
        this.locale = options.locale || 'en-US';

        // Unit conversion configuration
        this.enableUnitConversion = options.enableUnitConversion !== false;
        this.unitConversionThreshold = options.unitConversionThreshold || 1000;

        // State
        this.lastValue = null;
    }

    /**
     * Get default decimals based on field type
     */
    getDefaultDecimals() {
        const defaults = {
            'INTEGER': 0,
            'DECIMAL': 2,
            'PERCENTAGE': 2,
            'CURRENCY': 2,
            'SCIENTIFIC': 2
        };
        return defaults[this.fieldType] || 2;
    }

    /**
     * Format a number for display
     */
    format(value) {
        if (value === null || value === undefined || value === '') {
            return '';
        }

        // Parse if string
        const num = typeof value === 'string' ? this.parse(value) : value;

        if (isNaN(num)) {
            return value; // Return as-is if not a valid number
        }

        // Format based on type
        switch (this.fieldType) {
            case 'INTEGER':
                return this.formatInteger(num);

            case 'DECIMAL':
                return this.formatDecimal(num);

            case 'PERCENTAGE':
                return this.formatPercentage(num);

            case 'CURRENCY':
                return this.formatCurrency(num);

            case 'SCIENTIFIC':
                return this.formatScientific(num);

            default:
                return this.formatDecimal(num);
        }
    }

    /**
     * Parse a formatted string back to number
     */
    parse(value) {
        if (value === null || value === undefined || value === '') {
            return null;
        }

        // Convert to string
        let str = String(value).trim();

        // Handle empty
        if (str === '') return null;

        // Remove currency symbols
        str = str.replace(/[$€£¥]/g, '');

        // Handle percentage
        const hasPercentage = str.includes('%');
        str = str.replace(/%/g, '');

        // Remove thousand separators
        str = str.replace(/,/g, '');

        // Handle scientific notation
        if (str.match(/[eE]/)) {
            const num = parseFloat(str);
            return isNaN(num) ? null : num;
        }

        // Parse number
        const num = parseFloat(str);

        if (isNaN(num)) {
            return null;
        }

        // If percentage was present, convert to decimal
        if (hasPercentage) {
            return num / 100;
        }

        return num;
    }

    /**
     * Format as integer with thousand separators
     */
    formatInteger(num) {
        const rounded = Math.round(num);
        return new Intl.NumberFormat(this.locale, {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(rounded);
    }

    /**
     * Format as decimal with thousand separators
     */
    formatDecimal(num) {
        return new Intl.NumberFormat(this.locale, {
            minimumFractionDigits: this.decimals,
            maximumFractionDigits: this.decimals
        }).format(num);
    }

    /**
     * Format as percentage
     */
    formatPercentage(num) {
        // Assume num is in decimal form (0.5 for 50%)
        const percentage = num * 100;

        return new Intl.NumberFormat(this.locale, {
            minimumFractionDigits: this.decimals,
            maximumFractionDigits: this.decimals
        }).format(percentage) + '%';
    }

    /**
     * Format as currency
     */
    formatCurrency(num) {
        return this.currencySymbol + new Intl.NumberFormat(this.locale, {
            minimumFractionDigits: this.decimals,
            maximumFractionDigits: this.decimals
        }).format(num);
    }

    /**
     * Format as scientific notation
     */
    formatScientific(num) {
        // Use scientific notation for very large or very small numbers
        if (Math.abs(num) >= 1e6 || (Math.abs(num) < 0.01 && num !== 0)) {
            return num.toExponential(this.decimals);
        }

        // Otherwise use decimal
        return this.formatDecimal(num);
    }

    /**
     * Attach formatter to an input element
     */
    attachToInput(inputElement) {
        if (!inputElement) return;

        // Store reference
        inputElement._numberFormatter = this;

        // Initialize with existing value if present
        const existingValue = inputElement.value;
        if (existingValue) {
            const raw = this.parse(existingValue);
            if (raw !== null) {
                inputElement.dataset.rawValue = String(raw);
                inputElement.value = this.format(raw);
            }
        }

        // Handle focus: show raw value for editing
        inputElement.addEventListener('focus', (e) => {
            // Get raw value from data attribute or parse current value
            const raw = e.target.dataset.rawValue
                ? parseFloat(e.target.dataset.rawValue)
                : this.parse(e.target.value);

            if (raw !== null && !isNaN(raw)) {
                e.target.value = String(raw);
                this.lastValue = raw;
            }
        });

        // Handle blur: format for display and store raw value
        inputElement.addEventListener('blur', (e) => {
            const raw = this.parse(e.target.value);
            if (raw !== null && !isNaN(raw)) {
                // Store raw value in data attribute for form submission
                e.target.dataset.rawValue = String(raw);
                // Display formatted value
                e.target.value = this.format(raw);
                this.lastValue = raw;

                // Check for unit conversion suggestions
                if (this.enableUnitConversion) {
                    this.suggestUnitConversion(raw, inputElement);
                }
            } else if (e.target.value === '') {
                // Clear data attribute if empty
                delete e.target.dataset.rawValue;
            }
        });

        // Handle input: validate as user types
        inputElement.addEventListener('input', (e) => {
            this.validateInput(e.target);
        });
    }

    /**
     * Validate input as user types
     */
    validateInput(inputElement) {
        const value = inputElement.value;

        // Allow empty
        if (value === '') return;

        // Check if valid number characters
        const validChars = /^[-+]?[0-9.,eE%$€£¥\s]*$/;
        if (!validChars.test(value)) {
            // Remove invalid characters
            inputElement.value = value.replace(/[^-+0-9.,eE%$€£¥\s]/g, '');
        }
    }

    /**
     * Suggest unit conversion if appropriate
     */
    suggestUnitConversion(value, inputElement) {
        if (!this.unit) return;

        const conversion = this.getUnitConversion(value, this.unit);

        if (conversion) {
            this.showConversionSuggestion(
                inputElement,
                `${value} ${this.unit} = ${conversion.value} ${conversion.unit}`
            );
        }
    }

    /**
     * Get unit conversion suggestion
     */
    getUnitConversion(value, unit) {
        // Unit conversion rules
        const conversions = {
            // Energy
            'Wh': { threshold: 1000, factor: 0.001, unit: 'kWh' },
            'kWh': { threshold: 1000, factor: 0.001, unit: 'MWh' },
            'MWh': { threshold: 1000, factor: 0.001, unit: 'GWh' },

            // Distance
            'm': { threshold: 1000, factor: 0.001, unit: 'km' },
            'km': { threshold: 1000, factor: 0.001, unit: 'Mm' },

            // Weight
            'g': { threshold: 1000, factor: 0.001, unit: 'kg' },
            'kg': { threshold: 1000, factor: 0.001, unit: 't' },
            't': { threshold: 1000, factor: 0.001, unit: 'kt' },

            // Volume
            'mL': { threshold: 1000, factor: 0.001, unit: 'L' },
            'L': { threshold: 1000, factor: 0.001, unit: 'kL' },

            // CO2
            'kg CO2e': { threshold: 1000, factor: 0.001, unit: 't CO2e' },
            't CO2e': { threshold: 1000, factor: 0.001, unit: 'kt CO2e' },
        };

        const conversion = conversions[unit];

        if (conversion && Math.abs(value) >= conversion.threshold) {
            return {
                value: this.formatDecimal(value * conversion.factor),
                unit: conversion.unit
            };
        }

        return null;
    }

    /**
     * Show conversion suggestion tooltip
     */
    showConversionSuggestion(inputElement, message) {
        // Remove existing tooltip
        const existing = document.querySelector('.unit-conversion-tooltip');
        if (existing) {
            existing.remove();
        }

        // Create tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'unit-conversion-tooltip';
        tooltip.textContent = message;

        // Position near input
        const rect = inputElement.getBoundingClientRect();
        tooltip.style.position = 'absolute';
        tooltip.style.top = `${rect.bottom + 5}px`;
        tooltip.style.left = `${rect.left}px`;

        document.body.appendChild(tooltip);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            tooltip.remove();
        }, 5000);
    }

    /**
     * Format a number with smart defaults
     */
    static smartFormat(value, options = {}) {
        // Auto-detect field type if not specified
        if (!options.fieldType) {
            if (String(value).includes('%')) {
                options.fieldType = 'PERCENTAGE';
            } else if (String(value).includes('$') || String(value).includes('€') || String(value).includes('£')) {
                options.fieldType = 'CURRENCY';
            } else if (String(value).includes('e') || String(value).includes('E')) {
                options.fieldType = 'SCIENTIFIC';
            } else if (value % 1 === 0) {
                options.fieldType = 'INTEGER';
            } else {
                options.fieldType = 'DECIMAL';
            }
        }

        const formatter = new NumberFormatter(options);
        return formatter.format(value);
    }

    /**
     * Apply formatting to all number inputs in a container
     */
    static applyToContainer(container, defaultOptions = {}) {
        const inputs = container.querySelectorAll('input[type="number"], input[data-format="number"]');

        inputs.forEach(input => {
            const options = {
                ...defaultOptions,
                fieldType: input.dataset.fieldType || defaultOptions.fieldType,
                unit: input.dataset.unit || defaultOptions.unit,
                decimals: input.dataset.decimals ? parseInt(input.dataset.decimals) : defaultOptions.decimals
            };

            const formatter = new NumberFormatter(options);
            formatter.attachToInput(input);
        });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NumberFormatter;
}
