/**
 * Dimension Badge Component
 * Renders dimension name badges with optional tooltips
 *
 * Part of Phase 1: Shared Dimension Component
 * Feature: Dimension Configuration in Assign Data Points
 */

window.DimensionBadge = (function() {
    'use strict';

    /**
     * Render dimension badges in a container
     * @param {Array} dimensions - Array of dimension objects
     * @param {string} containerId - ID of container element
     */
    function render(dimensions, containerId) {
        const container = document.getElementById(containerId) ||
                         document.querySelector(containerId);

        if (!container) {
            console.warn(`[DimensionBadge] Container not found: ${containerId}`);
            return;
        }

        if (!dimensions || dimensions.length === 0) {
            container.innerHTML = '';
            container.style.display = 'none';
            return;
        }

        container.style.display = 'flex';
        container.innerHTML = dimensions.map(dim => createBadgeHTML(dim)).join('');
    }

    /**
     * Render badges in a specific DOM element
     * @param {Array} dimensions - Array of dimension objects
     * @param {HTMLElement} element - DOM element
     */
    function renderInElement(dimensions, element) {
        if (!element) {
            console.warn('[DimensionBadge] Element is null or undefined');
            return;
        }

        if (!dimensions || dimensions.length === 0) {
            element.innerHTML = '';
            element.style.display = 'none';
            return;
        }

        element.style.display = 'flex';
        element.innerHTML = dimensions.map(dim => createBadgeHTML(dim)).join('');
    }

    /**
     * Create HTML for a single badge
     * @param {Object} dimension - Dimension object
     * @returns {string} HTML string
     */
    function createBadgeHTML(dimension) {
        const valuesList = dimension.values ?
            dimension.values.map(v => v.display_name || v.value).join(', ') :
            '';

        const tooltipText = valuesList ? `${dimension.name}: ${valuesList}` : dimension.name;

        return `
            <span class="dimension-badge"
                  data-dimension-id="${dimension.dimension_id}"
                  data-bs-toggle="tooltip"
                  data-bs-placement="top"
                  title="${tooltipText}">
                ${dimension.name}
            </span>
        `;
    }

    /**
     * Add tooltip to badge element
     * @param {HTMLElement} badgeElement - Badge DOM element
     * @param {Object} dimensionData - Dimension data with values
     */
    function addTooltip(badgeElement, dimensionData) {
        if (!badgeElement || !dimensionData) return;

        const valuesList = dimensionData.values ?
            dimensionData.values.map(v => v.display_name || v.value).join(', ') :
            '';

        const tooltipText = valuesList ?
            `${dimensionData.name}: ${valuesList}` :
            dimensionData.name;

        badgeElement.setAttribute('data-bs-toggle', 'tooltip');
        badgeElement.setAttribute('data-bs-placement', 'top');
        badgeElement.setAttribute('title', tooltipText);

        // Initialize Bootstrap tooltip
        if (window.bootstrap && window.bootstrap.Tooltip) {
            new bootstrap.Tooltip(badgeElement, {
                delay: { show: 500, hide: 100 }
            });
        }
    }

    /**
     * Clear all badges in container
     * @param {string} containerId - ID of container element
     */
    function clear(containerId) {
        const container = document.getElementById(containerId) ||
                         document.querySelector(containerId);

        if (container) {
            // Dispose of any tooltips first
            container.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
                const tooltip = bootstrap.Tooltip.getInstance(el);
                if (tooltip) {
                    tooltip.dispose();
                }
            });

            container.innerHTML = '';
            container.style.display = 'none';
        }
    }

    /**
     * Get dimension ID from badge element
     * @param {HTMLElement} badgeElement - Badge DOM element
     * @returns {string|null} Dimension ID
     */
    function getDimensionId(badgeElement) {
        return badgeElement ? badgeElement.getAttribute('data-dimension-id') : null;
    }

    // Public API
    return {
        render,
        renderInElement,
        createBadgeHTML,
        addTooltip,
        clear,
        getDimensionId
    };
})();
