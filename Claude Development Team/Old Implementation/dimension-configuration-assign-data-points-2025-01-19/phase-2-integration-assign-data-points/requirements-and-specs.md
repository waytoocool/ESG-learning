# Phase 2: Integration with Assign Data Points - Requirements & Specifications

**Phase:** 2 of 2
**Phase Name:** Integration with Assign Data Points Page
**Start Date:** 2025-01-19 (after Phase 1 completion)
**Estimated Duration:** 1.5 days
**Owner:** Backend Developer
**Dependencies:** Phase 1 complete

---

## Phase Overview

Integrate the shared dimension component from Phase 1 into the Assign Data Points page, providing administrators with a unified workflow for configuring data point assignments including dimensions.

---

## Objectives

1. ✅ Add dimension badges to field cards in Selected Data Points panel
2. ✅ Add "Manage Dimensions" button to field card actions
3. ✅ Integrate Dimension Management Modal into assign data points page
4. ✅ Implement dimension tooltips
5. ✅ Add optional toolbar button for quick access
6. ✅ Ensure real-time UI updates
7. ✅ Comprehensive UI/UX testing with `@ui-testing-agent`

---

## Deliverables

### 1. Dimension Configuration Module
**File:** `app/static/js/admin/assign_data_points/DimensionConfigModule.js`

**Purpose:** Integration layer between shared dimension component and assign data points page

**Public API:**
```javascript
window.DimensionConfigModule = (function() {
    'use strict';

    /**
     * Initialize dimension configuration
     */
    function init() {
        // Initialize shared dimension manager
        DimensionManagerShared.init({
            context: 'assign-data-points',
            containerId: 'dimensionManagementModal',
            onDimensionAssigned: handleDimensionAssigned,
            onDimensionRemoved: handleDimensionRemoved,
            onDimensionCreated: handleDimensionCreated
        });

        // Set up event listeners
        setupEventListeners();
    }

    /**
     * Open dimension modal for a specific field
     */
    function openDimensionModal(fieldId, fieldName) {
        DimensionManagerShared.openDimensionModal(fieldId, fieldName, 'assign-data-points');
    }

    /**
     * Refresh dimension badges for a field
     */
    async function refreshDimensionBadges(fieldId) {
        const dimensions = await loadFieldDimensions(fieldId);
        renderDimensionBadges(fieldId, dimensions);
        updateManageDimensionsButtonState(fieldId, dimensions);
    }

    /**
     * Render dimension badges in field card
     */
    function renderDimensionBadges(fieldId, dimensions) {
        const container = document.querySelector(
            `[data-field-id="${fieldId}"] .dimension-badges-container`
        );
        if (!container) return;

        if (dimensions.length === 0) {
            container.innerHTML = '';
            container.style.display = 'none';
            return;
        }

        container.style.display = 'flex';
        container.innerHTML = dimensions.map(dim => `
            <span class="dimension-badge"
                  data-dimension-id="${dim.dimension_id}"
                  title="${dim.name}: ${dim.values.map(v => v.display_name).join(', ')}">
                ${dim.name}
            </span>
        `).join('');

        // Initialize tooltips
        dimensions.forEach(dim => {
            const badge = container.querySelector(`[data-dimension-id="${dim.dimension_id}"]`);
            if (badge) {
                DimensionTooltip.init(badge, dim);
            }
        });
    }

    /**
     * Update "Manage Dimensions" button state
     */
    function updateManageDimensionsButtonState(fieldId, dimensions) {
        const button = document.querySelector(
            `[data-field-id="${fieldId}"] .manage-dimensions-btn`
        );
        if (!button) return;

        if (dimensions.length > 0) {
            button.classList.add('has-dimensions');
            button.classList.remove('no-dimensions');
        } else {
            button.classList.add('no-dimensions');
            button.classList.remove('has-dimensions');
        }
    }

    /**
     * Handle dimension assigned event
     */
    function handleDimensionAssigned(data) {
        const { fieldId, dimension } = data;

        // Refresh badges
        refreshDimensionBadges(fieldId);

        // Emit event for other modules
        AppEvents.emit('dimension-config-changed', {
            fieldId,
            action: 'assigned',
            dimension
        });

        // Show success notification
        showNotification('success', `Dimension "${dimension.name}" assigned successfully`);
    }

    /**
     * Handle dimension removed event
     */
    function handleDimensionRemoved(data) {
        const { fieldId, dimension } = data;

        // Refresh badges
        refreshDimensionBadges(fieldId);

        // Emit event for other modules
        AppEvents.emit('dimension-config-changed', {
            fieldId,
            action: 'removed',
            dimension
        });

        // Show success notification
        showNotification('success', `Dimension "${dimension.name}" removed successfully`);
    }

    /**
     * Handle dimension created event
     */
    function handleDimensionCreated(data) {
        const { dimension } = data;

        // Show success notification
        showNotification('success', `Dimension "${dimension.name}" created successfully`);
    }

    /**
     * Setup event listeners for assign data points page
     */
    function setupEventListeners() {
        // Listen for field cards being rendered
        AppEvents.on('state-dataPoint-added', (dataPoint) => {
            refreshDimensionBadges(dataPoint.field_id);
        });

        // Listen for field cards being removed
        AppEvents.on('state-dataPoint-removed', (dataPoint) => {
            // Cleanup tooltips
            const container = document.querySelector(
                `[data-field-id="${dataPoint.field_id}"] .dimension-badges-container`
            );
            if (container) {
                container.querySelectorAll('.dimension-badge').forEach(badge => {
                    DimensionTooltip.destroy(badge);
                });
            }
        });

        // Toolbar "Manage Dimensions" button (optional)
        const toolbarBtn = document.getElementById('manageDimensionsToolbar');
        if (toolbarBtn) {
            toolbarBtn.addEventListener('click', handleToolbarManageDimensions);
        }
    }

    /**
     * Handle toolbar "Manage Dimensions" button click
     */
    function handleToolbarManageDimensions() {
        // Only works if exactly 1 field is selected
        const selectedFields = Array.from(AppState.selectedDataPoints.values());

        if (selectedFields.length !== 1) {
            showNotification('warning', 'Please select exactly one field to manage dimensions');
            return;
        }

        const field = selectedFields[0];
        openDimensionModal(field.field_id, field.field_name);
    }

    /**
     * Load field dimensions from API
     */
    async function loadFieldDimensions(fieldId) {
        try {
            const response = await fetch(`/admin/fields/${fieldId}/dimensions`);
            if (!response.ok) throw new Error('Failed to load dimensions');
            const data = await response.json();
            return data.dimensions || [];
        } catch (error) {
            console.error('Error loading field dimensions:', error);
            return [];
        }
    }

    /**
     * Show notification
     */
    function showNotification(type, message) {
        // Use existing notification system
        if (window.showNotification) {
            window.showNotification(type, message);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    // Public API
    return {
        init,
        openDimensionModal,
        refreshDimensionBadges
    };
})();
```

---

### 2. Updated Field Card Template
**File:** `app/static/js/admin/assign_data_points/SelectedDataPointsPanel.js`

**Changes:** Add dimension badges and "Manage Dimensions" button to field card template

**Updated Template:**
```javascript
function renderFieldCard(dataPoint) {
    const configStatus = AppState.configurations.get(dataPoint.field_id);
    const hasConfig = configStatus && configStatus.configured;

    return `
        <div class="selected-field-card"
             data-field-id="${dataPoint.field_id}"
             data-framework-id="${dataPoint.framework_id}">

            <!-- Checkbox and Field Name -->
            <div class="field-header">
                <input type="checkbox"
                       class="field-checkbox"
                       data-field-id="${dataPoint.field_id}"
                       ${AppState.selectedDataPoints.has(dataPoint.field_id) ? 'checked' : ''}>
                <span class="field-name">${dataPoint.field_name}</span>
            </div>

            <!-- Field Metadata -->
            <div class="field-metadata">
                <span class="field-framework">${dataPoint.framework_name}</span>
                <span class="field-separator">·</span>
                <span class="field-frequency">${configStatus?.frequency || 'Annual'}</span>
                <span class="field-separator">·</span>
                <span class="field-topic">${dataPoint.topic_name || 'No Topic'}</span>
            </div>

            <!-- NEW: Dimension Badges Container -->
            <div class="dimension-badges-container" style="display: none;">
                <!-- Populated by DimensionConfigModule -->
            </div>

            <!-- Entity Assignments -->
            <div class="field-entities">
                <span class="entities-count">
                    ▸ ${getEntityCount(dataPoint.field_id)} entities assigned
                </span>
            </div>

            <!-- Action Buttons -->
            <div class="field-actions">
                <button class="btn-icon btn-configure"
                        data-field-id="${dataPoint.field_id}"
                        title="Configure">
                    <i class="fas fa-cog"></i>
                </button>

                <!-- NEW: Manage Dimensions Button -->
                <button class="btn-icon btn-manage-dimensions manage-dimensions-btn no-dimensions"
                        data-field-id="${dataPoint.field_id}"
                        title="Manage Dimensions">
                    <i class="fas fa-sliders-h"></i>
                </button>

                <button class="btn-icon btn-info"
                        data-field-id="${dataPoint.field_id}"
                        title="Field Info">
                    <i class="fas fa-info-circle"></i>
                </button>

                <button class="btn-icon btn-remove"
                        data-field-id="${dataPoint.field_id}"
                        title="Remove">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
}
```

**Event Listeners:**
```javascript
// Add event listener for "Manage Dimensions" buttons
container.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn-manage-dimensions');
    if (btn) {
        const fieldId = btn.dataset.fieldId;
        const fieldCard = btn.closest('.selected-field-card');
        const fieldName = fieldCard.querySelector('.field-name').textContent;

        DimensionConfigModule.openDimensionModal(fieldId, fieldName);
    }
});
```

---

### 3. Updated HTML Template
**File:** `app/templates/admin/assign_data_points_v2.html`

**Changes:**

**A. Include Shared Component Scripts (before closing `</body>`):**
```html
<!-- Phase 10: Dimension Configuration -->
<!-- Shared Components -->
<script src="{{ url_for('static', filename='js/shared/DimensionManagerShared.js') }}"></script>
<script src="{{ url_for('static', filename='js/shared/ComputedFieldDimensionValidator.js') }}"></script>
<script src="{{ url_for('static', filename='js/shared/DimensionBadge.js') }}"></script>
<script src="{{ url_for('static', filename='js/shared/DimensionTooltip.js') }}"></script>

<!-- Assign Data Points Integration -->
<script src="{{ url_for('static', filename='js/admin/assign_data_points/DimensionConfigModule.js') }}"></script>
```

**B. Include Dimension Management Modal:**
```html
<!-- Include Shared Dimension Management Modal -->
{% include 'shared/_dimension_management_modal.html' %}
```

**C. Include CSS:**
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/shared/dimension-management.css') }}">
```

**D. Optional Toolbar Button (after "Assign Entities" button):**
```html
<button id="manageDimensionsToolbar" class="btn btn-outline-primary" disabled
        title="Select a single field to manage dimensions">
    <i class="fas fa-sliders-h" aria-hidden="true"></i> Manage Dimensions
</button>
```

**E. Initialize Dimension Module:**
```javascript
// In DOMContentLoaded event handler
document.addEventListener('DOMContentLoaded', function() {
    // ... existing initialization ...

    // Phase 10: Initialize Dimension Configuration
    if (window.DimensionConfigModule) {
        DimensionConfigModule.init();
    }
});
```

---

### 4. CSS Enhancements
**File:** `app/static/css/admin/assign_data_points_redesigned.css`

**Add Styles:**
```css
/* Dimension Badges Container */
.dimension-badges-container {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 6px;
    margin-bottom: 4px;
}

/* Manage Dimensions Button States */
.btn-manage-dimensions {
    transition: all 0.2s ease;
}

.btn-manage-dimensions.no-dimensions {
    color: #6c757d;
    background-color: transparent;
}

.btn-manage-dimensions.no-dimensions:hover {
    color: #495057;
    background-color: #f8f9fa;
}

.btn-manage-dimensions.has-dimensions {
    color: #1976d2;
    background-color: #e3f2fd;
}

.btn-manage-dimensions.has-dimensions:hover {
    color: #0d47a1;
    background-color: #bbdefb;
}

/* Field Card Layout Adjustment */
.selected-field-card {
    /* Ensure proper spacing for dimension badges */
    min-height: 110px; /* Increased from default to accommodate badges */
}
```

---

### 5. Toolbar Button Logic
**File:** `app/static/js/admin/assign_data_points/main.js`

**Add Selection Tracking:**
```javascript
// Update toolbar "Manage Dimensions" button state based on selection
AppEvents.on('state-selectedDataPoints-changed', (selectedDataPoints) => {
    const toolbarBtn = document.getElementById('manageDimensionsToolbar');
    if (!toolbarBtn) return;

    const count = selectedDataPoints.size;

    if (count === 1) {
        toolbarBtn.disabled = false;
        toolbarBtn.title = 'Manage dimensions for selected field';
    } else if (count === 0) {
        toolbarBtn.disabled = true;
        toolbarBtn.title = 'Select a field to manage dimensions';
    } else {
        toolbarBtn.disabled = true;
        toolbarBtn.title = `Select exactly one field (${count} currently selected)`;
    }
});
```

---

## Implementation Steps

### Step 1: Add Dimension Badges to Field Cards (2 hours)
1. Update `SelectedDataPointsPanel.js` field card template
2. Add dimension badges container
3. Create badge rendering function
4. Test badge display with various field configurations

### Step 2: Add "Manage Dimensions" Button (1 hour)
1. Add button to field card template
2. Add button state management (gray/blue)
3. Add click event listener
4. Test button behavior

### Step 3: Create DimensionConfigModule (3 hours)
1. Create `DimensionConfigModule.js`
2. Implement initialization
3. Implement dimension loading
4. Implement badge rendering
5. Implement event handlers
6. Test integration with shared component

### Step 4: Integrate Dimension Modal (2 hours)
1. Include modal template in assign data points page
2. Include shared component scripts
3. Initialize shared component
4. Test modal opening/closing
5. Test dimension assignment/removal

### Step 5: Add Dimension Tooltips (1 hour)
1. Initialize tooltips for badges
2. Test tooltip display
3. Test tooltip content

### Step 6: Add Optional Toolbar Button (1 hour)
1. Add button to toolbar
2. Implement selection-based enabling
3. Add click handler
4. Test with various selection states

### Step 7: CSS Styling (1 hour)
1. Add dimension badge styles
2. Add button state styles
3. Test responsive design
4. Test accessibility

### Step 8: Testing (4 hours)
1. Functional testing (all features)
2. UI/UX testing with `@ui-testing-agent`
3. Cross-browser testing
4. Performance testing

**Total Estimated Time:** 15 hours (1.5 working days with buffer)

---

## Testing Requirements

### Functional Tests

**Test 1: Dimension Badge Display**
- Field with dimensions shows badges
- Field without dimensions shows no badges
- Badges update in real-time when dimensions change

**Test 2: Manage Dimensions Button**
- Button changes color when field has dimensions
- Button opens modal correctly
- Modal shows correct field name

**Test 3: Dimension Assignment**
- Assign dimension via modal
- Badge appears immediately
- Button changes to blue state

**Test 4: Dimension Removal**
- Remove dimension via modal
- Badge disappears immediately
- Button changes to gray state (if no dimensions left)

**Test 5: Dimension Tooltip**
- Hover over badge shows tooltip
- Tooltip shows dimension values
- Tooltip disappears on mouse leave

**Test 6: Toolbar Button**
- Disabled when no fields selected
- Disabled when multiple fields selected
- Enabled when exactly one field selected
- Opens modal for selected field

**Test 7: Integration with Existing Features**
- Dimension config doesn't interfere with Configure modal
- Dimension config doesn't interfere with Entity assignment
- Dimension config doesn't interfere with Save All
- Field Info modal still works

### UI/UX Testing with `@ui-testing-agent`

**Comprehensive Test Suite:**
```markdown
# Dimension Configuration UI/UX Test Suite

## Test Environment
- URL: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points
- User: alice@alpha.com / admin123

## Pre-requisites
1. Company Alpha has dimensions: [Gender, Age Group, Department, Region]
2. Field "Total Employees" has no dimensions assigned
3. Field "Energy Consumption" has dimensions: [Department]

## Test Case 1: Initial State
**Steps:**
1. Navigate to assign data points page
2. Add "Total Employees" to selected data points
3. Observe field card

**Expected:**
- No dimension badges visible
- "Manage Dimensions" button is gray
- No empty space where badges would be

**Screenshot:** `tc1-initial-state.png`

## Test Case 2: Open Dimension Modal
**Steps:**
1. Click "Manage Dimensions" button on "Total Employees"
2. Observe modal

**Expected:**
- Modal opens
- Title shows "Manage Dimensions: Total Employees"
- "Assigned Dimensions" section is empty (shows "No dimensions assigned yet")
- "Available Dimensions" section shows: Gender, Age Group, Department, Region
- Each dimension shows its values

**Screenshot:** `tc2-modal-opened.png`

## Test Case 3: Assign First Dimension
**Steps:**
1. In modal, click "Add" next to "Gender"
2. Observe changes

**Expected:**
- "Gender" moves to "Assigned Dimensions" section
- Shows values: Male, Female, Other
- "Remove" button appears next to "Gender"
- Success notification appears
- Field card shows "Gender" badge (real-time update)
- "Manage Dimensions" button turns blue

**Screenshot:** `tc3-first-dimension-assigned.png`

## Test Case 4: Assign Additional Dimension
**Steps:**
1. Click "Add" next to "Age Group"
2. Observe changes

**Expected:**
- "Age Group" moves to "Assigned Dimensions"
- Field card shows both badges: "Gender" and "Age Group"
- Badges are properly spaced

**Screenshot:** `tc4-multiple-dimensions.png`

## Test Case 5: Dimension Badge Tooltip
**Steps:**
1. Close modal
2. Hover over "Gender" badge for 600ms

**Expected:**
- Tooltip appears after ~500ms
- Tooltip shows: "Gender: Male, Female, Other, Prefer not to say"
- Tooltip positioned correctly (not cut off)

**Screenshot:** `tc5-badge-tooltip.png`

## Test Case 6: Remove Dimension
**Steps:**
1. Reopen modal
2. Click "Remove" next to "Age Group"

**Expected:**
- "Age Group" moves back to "Available Dimensions"
- Field card updates (only "Gender" badge remains)
- Success notification appears

**Screenshot:** `tc6-dimension-removed.png`

## Test Case 7: Field with Existing Dimensions
**Steps:**
1. Add "Energy Consumption" to selected data points
2. Observe field card

**Expected:**
- "Department" badge visible immediately
- "Manage Dimensions" button is blue
- Clicking button shows "Department" in "Assigned Dimensions"

**Screenshot:** `tc7-existing-dimensions.png`

## Test Case 8: Computed Field Validation (Valid)
**Steps:**
1. Create computed field "Energy Intensity" = Energy / Employees
2. Ensure both dependencies have [Gender, Department]
3. Assign [Gender, Department] to "Energy Intensity"

**Expected:**
- Assignment succeeds
- No validation errors
- Both badges appear

**Screenshot:** `tc8-computed-valid.png`

## Test Case 9: Computed Field Validation (Invalid)
**Steps:**
1. Try to assign [Gender, Department] to computed field
2. But "Energy Consumption" only has [Department] (missing Gender)

**Expected:**
- Error modal appears
- Message: "Cannot assign dimensions to 'Energy Intensity'"
- Lists: "Energy Consumption (missing: Gender)"
- Shows current: [Department], required: [Gender, Department]
- No changes saved

**Screenshot:** `tc9-computed-invalid-error.png`

## Test Case 10: Toolbar Button States
**Steps:**
1. Select 0 fields → button disabled, tooltip: "Select a field..."
2. Select 1 field → button enabled, tooltip: "Manage dimensions..."
3. Select 2 fields → button disabled, tooltip: "Select exactly one field (2 currently selected)"

**Expected:**
- Button state updates correctly for each case
- Tooltips are accurate

**Screenshots:**
- `tc10a-button-disabled-none.png`
- `tc10b-button-enabled-one.png`
- `tc10c-button-disabled-multiple.png`

## Test Case 11: Create New Dimension Inline
**Steps:**
1. Open dimension modal
2. Click "Create New Dimension"
3. Fill: Name: "Location", Values: ["Office", "Remote", "Hybrid"]
4. Click "Save"

**Expected:**
- Dimension created successfully
- Automatically assigned to current field
- "Location" badge appears
- "Location" moves to "Assigned Dimensions"

**Screenshot:** `tc11-new-dimension-created.png`

## Test Case 12: Tenant Isolation
**Steps:**
1. As Company Alpha admin, assign "Gender" to "Total Employees"
2. Log out
3. Log in as Company Beta admin (david@beta.com)
4. View "Total Employees" field

**Expected:**
- Company Beta view shows NO dimension badges for "Total Employees"
- Company Alpha's dimension assignment is isolated
- Company Beta can assign different dimensions

**Screenshot:** `tc12-tenant-isolation.png`

## Test Case 13: Responsive Design
**Steps:**
1. Resize browser to mobile width (375px)
2. Observe dimension badges and buttons

**Expected:**
- Badges wrap properly
- "Manage Dimensions" button remains accessible
- Modal is responsive
- No horizontal scrolling

**Screenshot:** `tc13-responsive-mobile.png`

## Test Case 14: Accessibility
**Steps:**
1. Use Tab key to navigate
2. Use Enter key to activate buttons
3. Check ARIA labels

**Expected:**
- All interactive elements are keyboard accessible
- Focus indicators are visible
- Screen reader announces dimension changes
- Tooltips accessible via keyboard

## Test Case 15: Performance
**Steps:**
1. Add 20 fields to selected data points
2. Each field has 3 dimensions
3. Observe rendering time

**Expected:**
- All badges render in < 2 seconds
- No UI lag
- Smooth scrolling
```

---

## Success Criteria

1. ✅ Dimension badges display correctly in all scenarios
2. ✅ "Manage Dimensions" button functions properly with correct state colors
3. ✅ Dimension modal integrates seamlessly
4. ✅ Dimension tooltips work correctly
5. ✅ Toolbar button states update correctly based on selection
6. ✅ Real-time UI updates work (badges update without page refresh)
7. ✅ All UI/UX test cases pass with `@ui-testing-agent`
8. ✅ No regression in existing assign data points features
9. ✅ Performance targets met (< 2s for 20 fields with dimensions)
10. ✅ Accessibility compliance verified

---

## Dependencies

**Phase 1 Deliverables:**
- `DimensionManagerShared.js`
- `ComputedFieldDimensionValidator.js`
- `DimensionBadge.js`
- `DimensionTooltip.js`
- `_dimension_management_modal.html`
- `dimension-management.css`

**Existing Code:**
- `app/static/js/admin/assign_data_points/main.js`
- `app/static/js/admin/assign_data_points/SelectedDataPointsPanel.js`
- `app/templates/admin/assign_data_points_v2.html`

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| UI clutter with many dimensions | MEDIUM | Limit visible badges, show "+N more" indicator |
| Performance with many fields | LOW | Lazy loading, virtual scrolling |
| Integration conflicts | LOW | Thorough testing, modular design |

---

## Completion

After Phase 2, the feature is complete and ready for:
1. Code review
2. Final UI/UX testing
3. User acceptance testing
4. Production deployment

---

**Next Document:** `IMPLEMENTATION_COMPLETE.md` (summary of both phases)
