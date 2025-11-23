# Frameworks Page Refactoring Guide

**Date:** 2025-01-19
**Phase:** Phase 1 - Shared Dimension Component
**Purpose:** Refactor the Frameworks page to use the new shared dimension component

---

## Overview

This guide provides step-by-step instructions for refactoring the existing Frameworks page to use the new shared dimension management component. The refactoring will:

1. **Remove duplicate code** - Eliminate inline dimension management logic
2. **Use shared component** - Leverage `DimensionManagerShared.js`
3. **Maintain backward compatibility** - Ensure all existing features continue to work
4. **Improve maintainability** - Single source of truth for dimension management

---

## Current State

### Files to Refactor

**JavaScript:**
- `/app/static/js/admin/frameworks/frameworks-dimensions.js` (~400 lines)
  - Contains inline dimension management logic
  - Handles dimension modal display
  - Manages dimension assignment/removal
  - Inline dimension creation

**HTML Template:**
- `/app/templates/admin/frameworks.html`
  - Contains dimension modal HTML
  - Dimension badge display
  - Management buttons

**CSS:**
- `/app/static/css/admin/frameworks.css`
  - Dimension-specific styling
  - Modal styles
  - Badge styles

---

## Step 1: Update HTML Template

### 1.1 Include Shared Component Files

**Location:** `/app/templates/admin/frameworks.html`

Add the following script and stylesheet references BEFORE existing dimension scripts:

```html
<!-- Shared Dimension Component CSS -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/shared/dimension-management.css') }}">

<!-- Shared Dimension Component Scripts -->
<script src="{{ url_for('static', filename='js/shared/DimensionBadge.js') }}"></script>
<script src="{{ url_for('static', filename='js/shared/DimensionTooltip.js') }}"></script>
<script src="{{ url_for('static', filename='js/shared/ComputedFieldDimensionValidator.js') }}"></script>
<script src="{{ url_for('static', filename='js/shared/DimensionManagerShared.js') }}"></script>
```

### 1.2 Include Shared Modal Template

Replace the existing dimension modal HTML with:

```html
<!-- Include Shared Dimension Management Modal -->
{% include 'shared/_dimension_management_modal.html' %}
```

**Remove:** The old dimension modal markup (if it exists inline in frameworks.html)

### 1.3 Update Dimension Badge Display

Replace inline badge HTML with container that will be populated by `DimensionBadge.js`:

**Before:**
```html
<div class="dimension-badges">
    <!-- Manually rendered badges -->
    <span class="badge">Gender</span>
    <span class="badge">Age Group</span>
</div>
```

**After:**
```html
<div class="dimension-badges-container"
     id="field-badges-{{ field.field_id }}"
     data-field-id="{{ field.field_id }}">
    <!-- Badges will be rendered by DimensionBadge.js -->
</div>
```

---

## Step 2: Refactor JavaScript

### 2.1 Initialize Shared Component

**Location:** `/app/static/js/admin/frameworks/frameworks-dimensions.js`

**Add at the top of the file:**

```javascript
/**
 * Frameworks Dimension Management
 * Uses shared dimension component for consistent UX
 */

// Initialize shared dimension manager with frameworks-specific config
DimensionManagerShared.init({
    context: 'frameworks',
    containerId: 'dimensionManagementModal',

    // Callbacks for frameworks-specific actions
    onDimensionAssigned: function(fieldId, dimensionId) {
        console.log('[Frameworks] Dimension assigned:', fieldId, dimensionId);
        // Reload field dimensions display
        refreshFieldDimensions(fieldId);
        // Update any framework-specific UI
        updateFrameworkFieldCard(fieldId);
    },

    onDimensionRemoved: function(fieldId, dimensionId) {
        console.log('[Frameworks] Dimension removed:', fieldId, dimensionId);
        // Reload field dimensions display
        refreshFieldDimensions(fieldId);
        // Update any framework-specific UI
        updateFrameworkFieldCard(fieldId);
    },

    onDimensionCreated: function(dimensionData) {
        console.log('[Frameworks] New dimension created:', dimensionData);
        // Optionally refresh available dimensions list
        refreshAvailableDimensions();
    },

    onValidationError: function(errorData) {
        console.error('[Frameworks] Validation error:', errorData);
        // Show error notification (using existing framework notification system)
        showFrameworkNotification('error', errorData.title, errorData.message);
    }
});
```

### 2.2 Replace Dimension Modal Opening Logic

**Before (remove this):**
```javascript
function openDimensionModal(fieldId, fieldName) {
    // 50+ lines of modal setup code
    // Load dimensions
    // Populate lists
    // Setup event listeners
    // etc.
}
```

**After (use this):**
```javascript
function openDimensionModal(fieldId, fieldName) {
    // Simply delegate to shared component
    DimensionManagerShared.openDimensionModal(fieldId, fieldName, 'frameworks');
}
```

### 2.3 Replace Badge Rendering Logic

**Before (remove this):**
```javascript
function renderDimensionBadges(fieldId, dimensions) {
    const container = document.getElementById(`field-badges-${fieldId}`);
    let html = '';
    dimensions.forEach(dim => {
        html += `<span class="dimension-badge"
                      title="${dim.name}: ${dim.values.join(', ')}">
                    ${dim.name}
                </span>`;
    });
    container.innerHTML = html;
}
```

**After (use this):**
```javascript
function renderDimensionBadges(fieldId, dimensions) {
    const containerId = `field-badges-${fieldId}`;
    DimensionBadge.render(dimensions, containerId);
    DimensionTooltip.initAll(
        document.getElementById(containerId),
        dimensions
    );
}
```

### 2.4 Remove Inline Dimension Creation Logic

**Remove (~100 lines):**
- Inline form display/hide functions
- Dimension creation validation
- API call to create dimension
- Form reset logic

**Replace with:**
The shared component handles this internally via `DimensionManagerShared.js`

### 2.5 Remove Validation Logic

**Remove (~50 lines):**
- Computed field dependency validation
- Dimension removal conflict checking
- Error modal display

**Replace with:**
The shared component handles this via `ComputedFieldDimensionValidator.js`

---

## Step 3: Update Framework-Specific Functions

### 3.1 Keep Framework Field Loading

**Keep this function** (framework-specific):

```javascript
async function loadFrameworkFields(frameworkId) {
    // This is framework-specific logic
    // Load fields for selected framework
    // Render field cards
    // Initialize dimension displays

    const fields = await fetchFrameworkFields(frameworkId);

    fields.forEach(field => {
        renderFieldCard(field);

        // Use shared component to render badges
        if (field.dimensions && field.dimensions.length > 0) {
            renderDimensionBadges(field.field_id, field.dimensions);
        }
    });
}
```

### 3.2 Refresh Field Dimensions

**Keep this function** (called from shared component callbacks):

```javascript
async function refreshFieldDimensions(fieldId) {
    try {
        const response = await fetch(`/admin/fields/${fieldId}/dimensions`);
        const data = await response.json();

        if (data.success) {
            // Re-render badges using shared component
            renderDimensionBadges(fieldId, data.dimensions);
        }
    } catch (error) {
        console.error('Error refreshing field dimensions:', error);
    }
}
```

---

## Step 4: CSS Cleanup

### 4.1 Remove Duplicate Styles

**Location:** `/app/static/css/admin/frameworks.css`

**Remove these classes** (now in shared CSS):
- `.dimension-badge`
- `.dimension-card`
- `.assigned-dimension`
- `.available-dimension`
- `.dimension-modal` (if exists)
- `.inline-dimension-form`
- `.dimension-section`

**Keep framework-specific styles:**
- Framework field card styles
- Framework layout styles
- Non-dimension related styles

---

## Step 5: Testing Checklist

### 5.1 Functional Tests

- [ ] **Open Dimension Modal**
  - Click "Manage Dimensions" button on field card
  - Modal opens with correct field name in header
  - Assigned dimensions show in top section
  - Available dimensions show in bottom section

- [ ] **Assign Dimension**
  - Click "Assign" button on available dimension
  - Dimension moves to assigned section
  - Badge appears on field card
  - Tooltip shows dimension values on hover

- [ ] **Remove Dimension**
  - Click "Remove" button on assigned dimension
  - Dimension moves to available section
  - Badge removed from field card

- [ ] **Create New Dimension**
  - Click "Create New Dimension" button
  - Inline form appears
  - Fill in name, description, values
  - Click "Save & Assign"
  - New dimension created and assigned
  - Badge appears on field card

- [ ] **Computed Field Validation - Assignment**
  - Try to assign dimensions to computed field
  - If dependencies lack dimensions, validation blocks
  - Error modal shows missing dimensions per dependency
  - Clear explanation of what needs to be fixed

- [ ] **Computed Field Validation - Removal**
  - Try to remove dimension from raw field
  - If computed field requires it, validation blocks
  - Error modal shows which computed fields need it
  - Clear guidance on resolution

### 5.2 UI/UX Tests

- [ ] **Dimension Badges**
  - Badges display correctly
  - Tooltips appear after 500ms hover
  - Tooltips show all dimension values
  - Badges styled consistently

- [ ] **Modal Appearance**
  - Modal is responsive on mobile
  - Sections clearly separated
  - Empty states show when appropriate
  - Loading states display during API calls

- [ ] **Error Messages**
  - Validation errors are clear and actionable
  - Error modal has red header
  - Detailed field-by-field breakdown
  - Guidance on how to fix

### 5.3 Integration Tests

- [ ] **Framework Page Still Works**
  - All existing functionality preserved
  - No console errors
  - No visual regressions
  - Framework-specific features work

- [ ] **No Breaking Changes**
  - Existing field management works
  - Field creation/editing works
  - Topic management works
  - Framework sync works

---

## Step 6: Performance Optimization

### 6.1 Lazy Load Dimensions

Only load dimensions when modal is opened:

```javascript
// Don't pre-load all field dimensions on page load
// Let the shared component load them on-demand

// Instead of:
// loadAllFieldDimensions(); // On page load

// Do:
// DimensionManagerShared will load on modal open
```

### 6.2 Event Delegation

Use event delegation for dimension button clicks:

```javascript
// Instead of adding listener to each button:
// document.querySelectorAll('.manage-dimensions-btn').forEach(...)

// Use delegation on container:
document.addEventListener('click', function(e) {
    if (e.target.matches('.manage-dimensions-btn')) {
        const fieldId = e.target.dataset.fieldId;
        const fieldName = e.target.dataset.fieldName;
        openDimensionModal(fieldId, fieldName);
    }
});
```

---

## Step 7: Code Cleanup

### 7.1 Remove Old Files (Optional)

If there were dedicated dimension files for frameworks:

**Consider removing:**
- `/app/static/js/admin/frameworks/dimension-modal.js` (if exists)
- `/app/static/css/admin/frameworks/dimension-modal.css` (if exists)

**Update references in:**
- `/app/templates/admin/frameworks.html` (remove old script/link tags)

### 7.2 Update Comments

Add comments indicating shared component usage:

```javascript
/**
 * Dimension management for frameworks page
 * Uses shared dimension component from /static/js/shared/
 * See: DimensionManagerShared.js, DimensionBadge.js, etc.
 */
```

---

## Expected Results

### Before Refactoring

```
frameworks.html (500 lines)
├── Inline dimension modal HTML (150 lines)
├── Field cards with manual badge rendering
└── Scripts:
    ├── frameworks.js (400 lines)
    └── frameworks-dimensions.js (400 lines)
        ├── Modal management (150 lines)
        ├── Dimension CRUD (100 lines)
        ├── Validation logic (100 lines)
        └── Badge rendering (50 lines)

Total: ~800 lines of dimension code
```

### After Refactoring

```
frameworks.html (400 lines) [-100 lines]
├── Include shared modal template (1 line)
├── Include shared scripts (4 lines)
├── Field cards with badge containers
└── Scripts:
    ├── frameworks.js (400 lines) [unchanged]
    └── frameworks-dimensions.js (150 lines) [-250 lines]
        ├── DimensionManagerShared.init() (50 lines)
        ├── openDimensionModal() delegation (5 lines)
        ├── renderDimensionBadges() delegation (10 lines)
        ├── Framework-specific callbacks (50 lines)
        └── Framework field loading (35 lines)

Total: ~150 lines of dimension code (uses shared component)
Reduction: ~650 lines removed (81% reduction)
```

---

## Migration Timeline

### Phase 1: Preparation (1 hour)
- Review existing frameworks dimension code
- Identify framework-specific vs. reusable logic
- Create backup of current files

### Phase 2: HTML Updates (30 minutes)
- Include shared component files
- Replace modal markup
- Update badge containers

### Phase 3: JavaScript Refactoring (2 hours)
- Initialize shared component
- Replace modal opening logic
- Replace badge rendering
- Remove inline creation code
- Remove validation code
- Update callbacks

### Phase 4: CSS Cleanup (30 minutes)
- Remove duplicate styles
- Verify framework-specific styles remain

### Phase 5: Testing (2 hours)
- Functional testing (all checklist items)
- UI/UX testing
- Integration testing
- Performance verification

### Phase 6: Documentation (30 minutes)
- Update code comments
- Document shared component usage
- Create internal wiki entry (optional)

**Total Time: ~6.5 hours**

---

## Rollback Plan

If issues arise during refactoring:

1. **Git Reset**
   ```bash
   git checkout -- app/static/js/admin/frameworks/
   git checkout -- app/templates/admin/frameworks.html
   git checkout -- app/static/css/admin/frameworks.css
   ```

2. **Feature Flag** (Optional)
   ```javascript
   const USE_SHARED_DIMENSION_COMPONENT = false; // Set to true when ready

   if (USE_SHARED_DIMENSION_COMPONENT) {
       DimensionManagerShared.init({...});
   } else {
       // Use old inline logic
   }
   ```

---

## Support and Questions

For questions during refactoring:

1. **Shared Component Docs:** See `/static/js/shared/DimensionManagerShared.js` (JSDoc comments)
2. **API Reference:** See Phase 1 requirements-and-specs.md
3. **Test Cases:** See Phase 1 requirements-and-specs.md Section 8

---

## Summary

This refactoring will:

✅ **Reduce code duplication** - Remove ~650 lines from frameworks page
✅ **Improve maintainability** - Single source of truth for dimension logic
✅ **Ensure consistency** - Same UX across Frameworks and Assign Data Points
✅ **Enhance validation** - Centralized computed field dimension validation
✅ **Preserve functionality** - All existing features continue to work
✅ **Enable future features** - Easy to add dimension features to both pages

**Next Steps:** After completing this refactoring, proceed to Phase 2 to integrate the shared component into the Assign Data Points page.
