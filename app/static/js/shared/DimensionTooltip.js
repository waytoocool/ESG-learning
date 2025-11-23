/**
 * Dimension Tooltip Component
 * Handles tooltip initialization and lifecycle for dimension badges
 *
 * Part of Phase 1: Shared Dimension Component
 * Feature: Dimension Configuration in Assign Data Points
 */

window.DimensionTooltip = (function() {
    'use strict';

    /**
     * Initialize tooltip for a badge element
     * @param {HTMLElement} badgeElement - Badge DOM element
     * @param {Object} dimensionData - Dimension data with values
     * @returns {bootstrap.Tooltip|null} Tooltip instance
     */
    function init(badgeElement, dimensionData) {
        if (!badgeElement) {
            console.warn('[DimensionTooltip] Badge element is null');
            return null;
        }

        if (!window.bootstrap || !window.bootstrap.Tooltip) {
            console.warn('[DimensionTooltip] Bootstrap Tooltip not available');
            return null;
        }

        // Destroy existing tooltip if present
        destroy(badgeElement);

        // Build tooltip text
        const tooltipText = buildTooltipText(dimensionData);

        // Set tooltip attributes
        badgeElement.setAttribute('data-bs-toggle', 'tooltip');
        badgeElement.setAttribute('data-bs-placement', 'top');
        badgeElement.setAttribute('title', tooltipText);

        // Initialize Bootstrap tooltip with custom config
        const tooltip = new bootstrap.Tooltip(badgeElement, {
            delay: { show: 500, hide: 100 },
            trigger: 'hover',
            html: false,
            animation: true
        });

        return tooltip;
    }

    /**
     * Build tooltip text from dimension data
     * @param {Object} dimensionData - Dimension data
     * @returns {string} Tooltip text
     */
    function buildTooltipText(dimensionData) {
        if (!dimensionData) return '';

        const name = dimensionData.name || 'Dimension';

        if (!dimensionData.values || dimensionData.values.length === 0) {
            return name;
        }

        const values = dimensionData.values
            .map(v => v.display_name || v.value)
            .join(', ');

        return `${name}: ${values}`;
    }

    /**
     * Destroy tooltip for a badge element
     * @param {HTMLElement} badgeElement - Badge DOM element
     */
    function destroy(badgeElement) {
        if (!badgeElement) return;

        const tooltip = bootstrap.Tooltip.getInstance(badgeElement);
        if (tooltip) {
            tooltip.dispose();
        }
    }

    /**
     * Update tooltip text for an existing badge
     * @param {HTMLElement} badgeElement - Badge DOM element
     * @param {Object} dimensionData - Updated dimension data
     */
    function update(badgeElement, dimensionData) {
        if (!badgeElement) return;

        const tooltip = bootstrap.Tooltip.getInstance(badgeElement);
        if (tooltip) {
            const newText = buildTooltipText(dimensionData);
            badgeElement.setAttribute('title', newText);
            // Reinitialize to apply new title
            tooltip.dispose();
            init(badgeElement, dimensionData);
        }
    }

    /**
     * Initialize tooltips for all badges in a container
     * @param {string|HTMLElement} container - Container ID or element
     * @param {Array} dimensionsData - Array of dimension data objects
     */
    function initAll(container, dimensionsData) {
        const containerEl = typeof container === 'string' ?
            document.getElementById(container) || document.querySelector(container) :
            container;

        if (!containerEl) {
            console.warn('[DimensionTooltip] Container not found');
            return;
        }

        const badges = containerEl.querySelectorAll('.dimension-badge');

        badges.forEach((badge, index) => {
            const dimensionId = badge.getAttribute('data-dimension-id');
            const dimensionData = dimensionsData.find(d => d.dimension_id === dimensionId);

            if (dimensionData) {
                init(badge, dimensionData);
            }
        });
    }

    /**
     * Destroy all tooltips in a container
     * @param {string|HTMLElement} container - Container ID or element
     */
    function destroyAll(container) {
        const containerEl = typeof container === 'string' ?
            document.getElementById(container) || document.querySelector(container) :
            container;

        if (!containerEl) return;

        const badges = containerEl.querySelectorAll('.dimension-badge[data-bs-toggle="tooltip"]');
        badges.forEach(badge => destroy(badge));
    }

    // Public API
    return {
        init,
        destroy,
        update,
        buildTooltipText,
        initAll,
        destroyAll
    };
})();
