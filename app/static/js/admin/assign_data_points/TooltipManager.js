/**
 * TooltipManager.js
 * Manages rich hover tooltips for computed fields showing dependencies, formula, and metadata
 */

const TooltipManager = (function() {
    'use strict';

    // State
    const state = {
        tooltipElement: null,
        currentTarget: null,
        hideTimeout: null,
        showTimeout: null,
        initialized: false
    };

    // Configuration
    const config = {
        showDelay: 400,      // Delay before showing tooltip (ms)
        hideDelay: 100,      // Delay before hiding tooltip (ms)
        offsetX: 0,          // Horizontal offset from cursor
        offsetY: 15,         // Vertical offset from cursor
        boundaryPadding: 10  // Padding from viewport edges
    };

    /**
     * Initialize the tooltip manager
     */
    function init() {
        if (state.initialized) {
            console.log('[TooltipManager] Already initialized');
            return;
        }

        console.log('[TooltipManager] Initializing...');

        // Create tooltip element
        createTooltipElement();

        // Set up event delegation
        setupEventListeners();

        state.initialized = true;
        console.log('[TooltipManager] Initialized successfully');
    }

    /**
     * Create the tooltip DOM element
     */
    function createTooltipElement() {
        state.tooltipElement = document.createElement('div');
        state.tooltipElement.className = 'computed-field-tooltip';
        state.tooltipElement.style.display = 'none';
        document.body.appendChild(state.tooltipElement);
    }

    /**
     * Set up event listeners for hover interactions
     */
    function setupEventListeners() {
        // Use event delegation on document body
        document.addEventListener('mouseover', handleMouseOver);
        document.addEventListener('mouseout', handleMouseOut);
        document.addEventListener('mousemove', handleMouseMove);

        // Hide tooltip on scroll
        document.addEventListener('scroll', hideTooltip, true);
    }

    /**
     * Handle mouse over event
     */
    function handleMouseOver(e) {
        const target = findTooltipTrigger(e.target);

        if (target) {
            // Clear any pending hide timeout
            if (state.hideTimeout) {
                clearTimeout(state.hideTimeout);
                state.hideTimeout = null;
            }

            // Set show timeout
            state.showTimeout = setTimeout(() => {
                showTooltip(target, e);
            }, config.showDelay);

            state.currentTarget = target;
        }
    }

    /**
     * Handle mouse out event
     */
    function handleMouseOut(e) {
        const target = findTooltipTrigger(e.target);

        if (target) {
            // Clear show timeout if exists
            if (state.showTimeout) {
                clearTimeout(state.showTimeout);
                state.showTimeout = null;
            }

            // Set hide timeout
            state.hideTimeout = setTimeout(() => {
                hideTooltip();
            }, config.hideDelay);
        }
    }

    /**
     * Handle mouse move event for tooltip positioning
     */
    function handleMouseMove(e) {
        if (state.tooltipElement && state.tooltipElement.classList.contains('show')) {
            positionTooltip(e);
        }
    }

    /**
     * Find the tooltip trigger element
     */
    function findTooltipTrigger(element) {
        // Check if element or parent has computed badge or is computed field
        let current = element;
        let maxDepth = 5; // Limit traversal depth

        while (current && maxDepth > 0) {
            if (current.classList) {
                // Exclude action buttons area - tooltips should not trigger on these
                if (current.classList.contains('point-actions') ||
                    current.closest('.point-actions')) {
                    return null;
                }

                // Exclude individual action buttons
                if (current.classList.contains('action-btn') ||
                    current.classList.contains('remove-point') ||
                    current.classList.contains('configure-single') ||
                    current.classList.contains('assign-single') ||
                    current.classList.contains('field-info-single')) {
                    return null;
                }

                // Check for computed badge - this is the primary trigger
                if (current.classList.contains('computed-badge')) {
                    return current;
                }

                // Check for computed field item in left panel
                if (current.classList.contains('field-item') && current.classList.contains('is-computed')) {
                    return current.querySelector('.computed-badge') || current;
                }

                // Check for computed field in selected panel
                // Only trigger if we're inside the point-content area (text/title), not the whole item
                if (current.classList.contains('selected-point-item') && current.classList.contains('is-computed')) {
                    // Check if we're hovering over the content area
                    const isInContentArea = element.closest('.point-content') ||
                                          element.classList.contains('point-content');

                    if (isInContentArea) {
                        return current.querySelector('.computed-badge') || current;
                    }

                    // If not in content area, don't trigger tooltip
                    return null;
                }
            }

            current = current.parentElement;
            maxDepth--;
        }

        return null;
    }

    /**
     * Show tooltip for target element
     */
    function showTooltip(target, event) {
        if (!target || !state.tooltipElement) return;

        // Get field ID from target
        const fieldId = getFieldIdFromElement(target);
        if (!fieldId) {
            console.warn('[TooltipManager] Could not determine field ID');
            return;
        }

        // Get tooltip data
        const tooltipData = getTooltipData(fieldId);
        if (!tooltipData) {
            console.warn('[TooltipManager] No tooltip data for field:', fieldId);
            return;
        }

        // Generate tooltip HTML
        const html = generateTooltipHTML(tooltipData);
        state.tooltipElement.innerHTML = html;

        // Show tooltip
        state.tooltipElement.style.display = 'block';

        // Position tooltip
        positionTooltip(event);

        // Add show class for animation
        requestAnimationFrame(() => {
            state.tooltipElement.classList.add('show');
        });

        console.log('[TooltipManager] Tooltip shown for field:', fieldId);
    }

    /**
     * Hide tooltip
     */
    function hideTooltip() {
        if (!state.tooltipElement) return;

        state.tooltipElement.classList.remove('show');

        // Wait for animation to complete
        setTimeout(() => {
            if (!state.tooltipElement.classList.contains('show')) {
                state.tooltipElement.style.display = 'none';
            }
        }, 200);

        state.currentTarget = null;
    }

    /**
     * Position tooltip relative to mouse cursor
     */
    function positionTooltip(event) {
        if (!state.tooltipElement || !event) return;

        const tooltip = state.tooltipElement;
        const mouseX = event.clientX;
        const mouseY = event.clientY;

        // Get tooltip dimensions
        const tooltipRect = tooltip.getBoundingClientRect();
        const tooltipWidth = tooltipRect.width;
        const tooltipHeight = tooltipRect.height;

        // Get viewport dimensions
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        // Calculate initial position (below and to the right of cursor)
        let left = mouseX + config.offsetX;
        let top = mouseY + config.offsetY;

        // Adjust if tooltip would go off right edge
        if (left + tooltipWidth + config.boundaryPadding > viewportWidth) {
            left = mouseX - tooltipWidth - config.offsetX;
            tooltip.classList.remove('position-right');
            tooltip.classList.add('position-left');
        } else {
            tooltip.classList.remove('position-left');
            tooltip.classList.add('position-right');
        }

        // Adjust if tooltip would go off bottom edge
        if (top + tooltipHeight + config.boundaryPadding > viewportHeight) {
            top = mouseY - tooltipHeight - config.offsetY;
            tooltip.classList.remove('position-bottom');
            tooltip.classList.add('position-top');
        } else {
            tooltip.classList.remove('position-top');
            tooltip.classList.add('position-bottom');
        }

        // Ensure tooltip stays within viewport
        left = Math.max(config.boundaryPadding, Math.min(left, viewportWidth - tooltipWidth - config.boundaryPadding));
        top = Math.max(config.boundaryPadding, Math.min(top, viewportHeight - tooltipHeight - config.boundaryPadding));

        // Apply position
        tooltip.style.left = `${left}px`;
        tooltip.style.top = `${top}px`;
    }

    /**
     * Get field ID from DOM element
     */
    function getFieldIdFromElement(element) {
        // Try to find field ID from various possible attributes
        let current = element;
        let maxDepth = 10;

        while (current && maxDepth > 0) {
            // Check for data-field-id attribute
            if (current.dataset && current.dataset.fieldId) {
                return current.dataset.fieldId;
            }

            // Check for id that contains field ID
            if (current.id) {
                const matches = current.id.match(/field-(.+)/);
                if (matches) {
                    return matches[1];
                }
            }

            // For selected panel items, try to find from field name element
            if (current.classList && current.classList.contains('selected-point-item')) {
                const fieldItem = current.querySelector('[data-field-id]');
                if (fieldItem) {
                    return fieldItem.dataset.fieldId;
                }

                // Try to find from any child element with field ID
                const allElements = current.querySelectorAll('[data-field-id]');
                if (allElements.length > 0) {
                    return allElements[0].dataset.fieldId;
                }
            }

            current = current.parentElement;
            maxDepth--;
        }

        return null;
    }

    /**
     * Get tooltip data for a field
     */
    function getTooltipData(fieldId) {
        // Check if DependencyManager is available
        if (!window.DependencyManager || !window.DependencyManager.isReady()) {
            console.warn('[TooltipManager] DependencyManager not ready');
            return null;
        }

        // Check if field is computed
        if (!window.DependencyManager.isComputedField(fieldId)) {
            return null;
        }

        // Get field metadata
        const metadata = window.DependencyManager.getFieldMetadata(fieldId);
        if (!metadata) {
            return null;
        }

        // Get dependencies (returns array of field IDs)
        const dependencyIds = window.DependencyManager.getDependencies(fieldId);

        // Convert dependency IDs to objects with field names
        const dependencies = [];
        if (dependencyIds && dependencyIds.length > 0) {
            dependencyIds.forEach(depId => {
                const depMetadata = window.DependencyManager.getFieldMetadata(depId);
                if (depMetadata) {
                    dependencies.push({
                        field_id: depId,
                        field_name: depMetadata.field_name || 'Unknown'
                    });
                }
            });
        }

        return {
            fieldId: fieldId,
            fieldName: metadata.field_name || 'Unknown Field',
            formula: metadata.formula || 'No formula available',
            dependencies: dependencies,
            dependencyCount: dependencies.length,
            frequency: metadata.frequency || null,
            unit: metadata.unit || null
        };
    }

    /**
     * Generate HTML for tooltip
     */
    function generateTooltipHTML(data) {
        const { fieldName, formula, dependencies, dependencyCount, frequency, unit } = data;

        let html = `
            <div class="tooltip-header">
                <span class="tooltip-icon">🧮</span>
                <span class="tooltip-title">Computed Field</span>
            </div>
        `;

        // Add formula section with variable mapping
        if (formula && formula !== 'No formula available') {
            html += `
                <div class="tooltip-section">
                    <div class="tooltip-label">Formula</div>
                    <div class="tooltip-formula">${escapeHtml(formula)}</div>
                </div>
            `;
        }

        // Add dependencies section with variable labels (A, B, C...)
        if (dependencies && dependencies.length > 0) {
            const variableLabels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];

            html += `
                <div class="tooltip-section tooltip-dependencies">
                    <div class="tooltip-label">Variables (${dependencyCount})</div>
                    <ul>
            `;

            dependencies.forEach((dep, index) => {
                const depName = dep.field_name || dep.name || 'Unknown';
                const varLabel = variableLabels[index] || `Var${index + 1}`;
                html += `<li><strong>${varLabel}</strong> = ${escapeHtml(depName)}</li>`;
            });

            html += `
                    </ul>
                </div>
            `;
        }

        // Add metadata section
        const metadataItems = [];
        if (frequency) {
            metadataItems.push(`<div class="tooltip-metadata-item">
                <span class="tooltip-metadata-icon">📅</span>
                <span>${frequency}</span>
            </div>`);
        }
        if (unit) {
            metadataItems.push(`<div class="tooltip-metadata-item">
                <span class="tooltip-metadata-icon">📊</span>
                <span>${escapeHtml(unit)}</span>
            </div>`);
        }

        if (metadataItems.length > 0) {
            html += `
                <div class="tooltip-metadata">
                    ${metadataItems.join('')}
                </div>
            `;
        }

        return html;
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Check if manager is ready
     */
    function isReady() {
        return state.initialized;
    }

    /**
     * Destroy the tooltip manager
     */
    function destroy() {
        if (!state.initialized) return;

        // Remove event listeners
        document.removeEventListener('mouseover', handleMouseOver);
        document.removeEventListener('mouseout', handleMouseOut);
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('scroll', hideTooltip, true);

        // Remove tooltip element
        if (state.tooltipElement && state.tooltipElement.parentNode) {
            state.tooltipElement.parentNode.removeChild(state.tooltipElement);
        }

        // Clear timeouts
        if (state.showTimeout) clearTimeout(state.showTimeout);
        if (state.hideTimeout) clearTimeout(state.hideTimeout);

        // Reset state
        state.tooltipElement = null;
        state.currentTarget = null;
        state.hideTimeout = null;
        state.showTimeout = null;
        state.initialized = false;

        console.log('[TooltipManager] Destroyed');
    }

    // Public API
    return {
        init,
        isReady,
        destroy,
        // Expose for debugging
        _state: state,
        _config: config
    };
})();

// Auto-initialize if DependencyManager is available
if (typeof window !== 'undefined') {
    window.TooltipManager = TooltipManager;
}
