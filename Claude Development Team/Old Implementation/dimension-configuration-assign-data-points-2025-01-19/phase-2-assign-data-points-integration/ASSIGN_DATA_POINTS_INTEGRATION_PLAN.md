# Assign Data Points - Dimension Integration Plan

**Date:** 2025-01-20
**Phase:** Phase 2 - Assign Data Points Integration
**Purpose:** Integrate shared dimension component into Assign Data Points page

---

## Overview

This plan outlines the integration of the shared dimension management component into the Assign Data Points page. Unlike the Frameworks page (which had inline dimension code to replace), the Assign Data Points page currently has **NO dimension management functionality**. We're adding it from scratch.

### Key Differences from Frameworks Integration:

1. **Frameworks Page**: Replaced existing dimension code with shared component
2. **Assign Data Points Page**: Adding brand new dimension management feature

---

## Current State Analysis

### Assign Data Points Architecture:

**Modular JavaScript Structure:**
- `/app/static/js/admin/assign_data_points/main.js` - Event system & state
- `/app/static/js/admin/assign_data_points/SelectDataPointsPanel.js` - Left panel (field selection)
- `/app/static/js/admin/assign_data_points/SelectedDataPointsPanel.js` - Right panel (selected fields)
- `/app/static/js/admin/assign_data_points/PopupsModule.js` - Modal management
- `/app/static/js/admin/assign_data_points/CoreUI.js` - UI utilities

**Template:**
- `/app/templates/admin/assign_data_points_v2.html` - Main page template

**No Existing Dimension Features:**
- ❌ No dimension badges displayed on field cards
- ❌ No "Manage Dimensions" buttons
- ❌ No dimension modal

---

## Integration Plan

### Step 1: Update HTML Template (assign_data_points_v2.html)

#### 1.1 Add Shared Component Files

**Location:** In `{% block extra_css %}` section (around line 937)

```html
<!-- Shared Dimension Component CSS -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/shared/dimension-management.css') }}">
```

**Location:** In `{% block afterbody %}` section, BEFORE the modular scripts (around line 943)

```html
<!-- Phase 2: Shared Dimension Component Scripts -->
<script src="{{ url_for('static', filename='js/shared/DimensionBadge.js') }}"></script>
<script src="{{ url_for('static', filename='js/shared/DimensionTooltip.js') }}"></script>
<script src="{{ url_for('static', filename='js/shared/ComputedFieldDimensionValidator.js') }}"></script>
<script src="{{ url_for('static', filename='js/shared/DimensionManagerShared.js') }}"></script>
```

#### 1.2 Add Shared Modal Template

**Location:** After the existing modals, before `{% endblock %}` (around line 935)

```html
<!-- Phase 2: Dimension Management Modal -->
{% include 'shared/_dimension_management_modal.html' %}
```

#### 1.3 Add Dimension Badge Containers to Field Cards

**Location:** In the field card templates (search for data point display sections)

Find the selected data point template and add dimension badge container:

```html
<!-- Add after field metadata section -->
<div class="dimension-badges-container"
     id="field-badges-{{ field.field_id }}"
     data-field-id="{{ field.field_id }}">
    <!-- Dimension badges will be rendered here by DimensionBadge.js -->
</div>
```

#### 1.4 Add "Manage Dimensions" Button to Field Actions

**Location:** In field card action buttons section

```html
<!-- Add alongside other action buttons (Config, Entities, etc.) -->
<button type="button"
        class="action-btn manage-dimensions-btn"
        data-field-id="{{ field.field_id }}"
        data-field-name="{{ field.field_name }}"
        title="Manage field dimensions">
    <i class="fas fa-layer-group"></i> Dimensions
</button>
```

---

### Step 2: Create Dimension Module (DimensionModule.js)

Create new module: `/app/static/js/admin/assign_data_points/DimensionModule.js`

```javascript
/**
 * Dimension Management Module for Assign Data Points
 * Integrates shared dimension component with assign data points workflow
 */

window.DimensionModule = (function() {
    'use strict';

    let initialized = false;

    /**
     * Initialize dimension management
     */
    function init() {
        if (initialized) {
            console.warn('[DimensionModule] Already initialized');
            return;
        }

        console.log('[DimensionModule] Initializing...');

        // Initialize shared dimension component
        if (typeof window.DimensionManagerShared !== 'undefined') {
            window.DimensionManagerShared.init({
                context: 'assign-data-points',
                containerId: 'dimensionManagementModal',

                // Callback when dimension is assigned to a field
                onDimensionAssigned: function(fieldId, dimensionData) {
                    console.log('[DimensionModule] Dimension assigned:', fieldId, dimensionData);

                    // Refresh dimension badges for this field
                    refreshFieldDimensions(fieldId);

                    // Emit event for other modules to react
                    window.AppEvents.emit('dimension-assigned', { fieldId, dimensionData });
                },

                // Callback when dimension is removed from a field
                onDimensionRemoved: function(fieldId, dimensionId) {
                    console.log('[DimensionModule] Dimension removed:', fieldId, dimensionId);

                    // Refresh dimension badges for this field
                    refreshFieldDimensions(fieldId);

                    // Emit event for other modules to react
                    window.AppEvents.emit('dimension-removed', { fieldId, dimensionId });
                },

                // Callback when new dimension is created
                onDimensionCreated: function(dimensionData) {
                    console.log('[DimensionModule] New dimension created:', dimensionData);

                    // Emit event for other modules to react
                    window.AppEvents.emit('dimension-created', dimensionData);
                },

                // Callback when validation error occurs
                onValidationError: function(errorData) {
                    console.error('[DimensionModule] Validation error:', errorData);

                    // Show error notification using existing popup system
                    if (window.PopupManager) {
                        window.PopupManager.show({
                            type: 'error',
                            title: errorData.title || 'Validation Error',
                            message: errorData.message || 'Cannot perform this operation'
                        });
                    }
                }
            });

            console.log('[DimensionModule] Shared component initialized');
        } else {
            console.error('[DimensionModule] DimensionManagerShared not found');
        }

        // Setup event listeners for "Manage Dimensions" buttons
        setupEventListeners();

        initialized = true;
        console.log('[DimensionModule] Initialization complete');
    }

    /**
     * Setup event listeners for dimension management buttons
     */
    function setupEventListeners() {
        // Use event delegation for dynamically added fields
        document.addEventListener('click', function(e) {
            // Check if clicked element is a "Manage Dimensions" button
            const btn = e.target.closest('.manage-dimensions-btn');
            if (!btn) return;

            e.preventDefault();
            e.stopPropagation();

            const fieldId = btn.dataset.fieldId;
            const fieldName = btn.dataset.fieldName;

            console.log('[DimensionModule] Opening dimension modal for:', fieldId, fieldName);

            // Open dimension modal using shared component
            if (window.DimensionManagerShared) {
                window.DimensionManagerShared.openDimensionModal(
                    fieldId,
                    fieldName,
                    'assign-data-points'
                );
            }
        });

        console.log('[DimensionModule] Event listeners attached');
    }

    /**
     * Refresh dimension badges for a field
     */
    async function refreshFieldDimensions(fieldId) {
        try {
            console.log('[DimensionModule] Refreshing dimensions for field:', fieldId);

            // Fetch field dimensions from server
            const response = await fetch(`/admin/fields/${fieldId}/dimensions`);
            const data = await response.json();

            if (data.success && data.dimensions) {
                // Render dimension badges
                renderDimensionBadges(fieldId, data.dimensions);
            }
        } catch (error) {
            console.error('[DimensionModule] Error refreshing field dimensions:', error);
        }
    }

    /**
     * Render dimension badges for a field
     */
    function renderDimensionBadges(fieldId, dimensions) {
        const containerId = `field-badges-${fieldId}`;
        const container = document.getElementById(containerId);

        if (!container) {
            console.warn('[DimensionModule] Badge container not found:', containerId);
            return;
        }

        // Use shared DimensionBadge component to render badges
        if (window.DimensionBadge) {
            window.DimensionBadge.render(dimensions, containerId);

            // Initialize tooltips using shared DimensionTooltip component
            if (window.DimensionTooltip) {
                window.DimensionTooltip.initAll(container, dimensions);
            }
        }
    }

    /**
     * Load dimensions for all selected fields
     */
    async function loadDimensionsForFields(fieldIds) {
        console.log('[DimensionModule] Loading dimensions for fields:', fieldIds);

        for (const fieldId of fieldIds) {
            await refreshFieldDimensions(fieldId);
        }
    }

    // Public API
    return {
        init: init,
        refreshFieldDimensions: refreshFieldDimensions,
        renderDimensionBadges: renderDimensionBadges,
        loadDimensionsForFields: loadDimensionsForFields
    };
})();
```

---

### Step 3: Update Main.js to Initialize Dimension Module

**Location:** `/app/static/js/admin/assign_data_points/main.js`

**Add to DOMContentLoaded initialization** (around line 100+):

```javascript
// Initialize Dimension Management Module
if (typeof window.DimensionModule !== 'undefined') {
    window.DimensionModule.init();
    console.log('[Main] DimensionModule initialized');
} else {
    console.warn('[Main] DimensionModule not available');
}
```

---

### Step 4: Update Template Script Loading Order

**Location:** `/app/templates/admin/assign_data_points_v2.html` in `{% block afterbody %}`

Update script loading order to include DimensionModule:

```html
<!-- Phase 1: Add foundation modules BEFORE legacy files -->
<script src="{{ url_for('static', filename='js/admin/assign_data_points/main.js') }}"></script>
<script src="{{ url_for('static', filename='js/admin/assign_data_points/ServicesModule.js') }}"></script>

<!-- Phase 2: Shared Dimension Component (ADDED) -->
<script src="{{ url_for('static', filename='js/shared/DimensionBadge.js') }}"></script>
<script src="{{ url_for('static', filename='js/shared/DimensionTooltip.js') }}"></script>
<script src="{{ url_for('static', filename='js/shared/ComputedFieldDimensionValidator.js') }}"></script>
<script src="{{ url_for('static', filename='js/shared/DimensionManagerShared.js') }}"></script>

<!-- Phase 3: Add CoreUI module BEFORE legacy files -->
<script src="{{ url_for('static', filename='js/admin/assign_data_points/CoreUI.js') }}"></script>

<!-- ... other modules ... -->

<!-- Phase 9.5: Add DimensionModule (NEW) -->
<script src="{{ url_for('static', filename='js/admin/assign_data_points/DimensionModule.js') }}"></script>

<!-- All module initialization handled by main.js DOMContentLoaded -->
```

---

## Expected User Experience

### Before Integration:
- ✗ No way to configure dimensions on data points
- ✗ No visibility into which fields have dimensions
- ✗ No computed field dimension validation

### After Integration:
- ✓ "Manage Dimensions" button on each field card
- ✓ Dimension badges displayed showing assigned dimensions
- ✓ Click button → Modal opens showing assigned/available dimensions
- ✓ Assign/remove dimensions with instant feedback
- ✓ Create new dimensions inline
- ✓ Computed field validation prevents dimension conflicts
- ✓ Tooltips show dimension values on hover

---

## Testing Checklist

### Functional Tests:

- [ ] **Page Loads**
  - Assign Data Points page loads without errors
  - Console shows DimensionModule initialization
  - No JavaScript errors

- [ ] **Manage Dimensions Button**
  - Button appears on each selected field card
  - Button is styled consistently
  - Click opens dimension modal

- [ ] **Dimension Modal**
  - Modal opens with correct field name
  - Assigned dimensions section populated
  - Available dimensions section populated
  - Loading states display correctly

- [ ] **Assign Dimension**
  - Click "Assign" button
  - Dimension moves to assigned section
  - Badge appears on field card
  - Tooltip shows dimension values

- [ ] **Remove Dimension**
  - Click "Remove" button
  - Dimension moves to available section
  - Badge removed from field card

- [ ] **Create New Dimension**
  - Click "Create New Dimension"
  - Inline form appears
  - Fill name, description, values
  - Save → dimension created and assigned
  - Badge appears on field card

- [ ] **Computed Field Validation - Assignment**
  - Try to assign dimensions to computed field
  - If dependencies lack dimensions → validation blocks
  - Error modal shows missing dimensions
  - Clear actionable guidance provided

- [ ] **Computed Field Validation - Removal**
  - Try to remove dimension from raw field
  - If computed field requires it → validation blocks
  - Error modal shows dependent fields
  - Clear guidance provided

### Integration Tests:

- [ ] **Works with Existing Features**
  - Field selection still works
  - Configuration modal still works
  - Entity assignment still works
  - Save/export functions still work

- [ ] **No Breaking Changes**
  - All existing buttons functional
  - All existing modals functional
  - No visual regressions
  - No performance issues

---

## Implementation Timeline

- **Step 1: HTML Updates** - 30 minutes
- **Step 2: Create DimensionModule.js** - 1 hour
- **Step 3: Update main.js** - 15 minutes
- **Step 4: Update Script Loading** - 15 minutes
- **Step 5: Testing** - 1.5 hours
- **Step 6: Documentation** - 30 minutes

**Total Estimated Time: ~4 hours**

---

## Success Criteria

1. ✅ Dimension management available on Assign Data Points page
2. ✅ Consistent UX with Frameworks page
3. ✅ All validation rules enforced
4. ✅ No breaking changes to existing functionality
5. ✅ Console logs confirm new code active
6. ✅ Performance remains acceptable

---

## Next Steps After Phase 2

Once Phase 2 is complete:

1. **Phase 3**: Add dimension filtering in data views
2. **Phase 4**: Dimensional data entry in user dashboard
3. **Phase 5**: Dimension-based reporting and analytics

---

**Status:** Ready to implement
**Dependencies:** Phase 1 (Shared Component) - ✅ Complete
