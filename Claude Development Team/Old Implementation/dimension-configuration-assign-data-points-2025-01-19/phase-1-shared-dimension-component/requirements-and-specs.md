# Phase 1: Shared Dimension Component - Requirements & Specifications

**Phase:** 1 of 2
**Phase Name:** Shared Dimension Component
**Start Date:** 2025-01-19
**Estimated Duration:** 2 days
**Owner:** Backend Developer

---

## Phase Overview

Create a reusable, framework-agnostic dimension management component that can be used in both:
1. **Frameworks Page** (existing functionality - refactor to use shared component)
2. **Assign Data Points Page** (new functionality - Phase 2)

This phase focuses on extracting and generalizing the dimension management logic from the Frameworks page into a shared, reusable module.

---

## Objectives

1. ✅ Extract dimension management logic from `frameworks-dimensions.js` into shared component
2. ✅ Create reusable Dimension Management Modal
3. ✅ Implement computed field dimension validation service
4. ✅ Create dimension UI components (badges, tooltips, buttons)
5. ✅ Ensure backward compatibility with Frameworks page
6. ✅ Write comprehensive unit tests

---

## Deliverables

### 1. Shared JavaScript Module
**File:** `app/static/js/shared/DimensionManagerShared.js`

**Responsibilities:**
- Manage dimension modal lifecycle (open/close)
- Load field dimensions via API
- Load available company dimensions via API
- Handle dimension assignment/removal
- Handle inline dimension creation
- Computed field validation
- Event emission for UI updates

**Public API:**
```javascript
window.DimensionManagerShared = {
    // Initialize the module
    init(config),

    // Open dimension modal for a specific field
    openDimensionModal(fieldId, fieldName, context),

    // Close dimension modal
    closeDimensionModal(),

    // Refresh dimension data for a field
    refreshFieldDimensions(fieldId),

    // Validate computed field dimensions
    validateComputedFieldDimensions(fieldId, dimensionIds),

    // Create new dimension inline
    createDimensionInline(dimensionData),

    // Event listeners
    on(event, callback),
    off(event, callback)
};
```

**Events Emitted:**
- `dimension-assigned` - When dimension is added to field
- `dimension-removed` - When dimension is removed from field
- `dimension-created` - When new dimension is created
- `validation-error` - When computed field validation fails
- `modal-opened` - When modal opens
- `modal-closed` - When modal closes

---

### 2. Dimension Management Modal Template
**File:** `app/templates/shared/_dimension_management_modal.html`

**Structure:**
```html
<!-- Dimension Management Modal -->
<div class="modal fade" id="dimensionManagementModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <!-- Header -->
            <div class="modal-header">
                <h5 class="modal-title">
                    Manage Dimensions: <span id="dimModalFieldName"></span>
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>

            <!-- Body -->
            <div class="modal-body">
                <!-- Assigned Dimensions Section -->
                <div class="assigned-dimensions-section">
                    <h6>Currently Assigned Dimensions</h6>
                    <div id="assignedDimensionsList"></div>
                    <div class="empty-state" id="noAssignedDimensions">
                        No dimensions assigned yet.
                    </div>
                </div>

                <hr>

                <!-- Available Dimensions Section -->
                <div class="available-dimensions-section">
                    <h6>Available Dimensions</h6>
                    <div id="availableDimensionsList"></div>
                    <div class="empty-state" id="noAvailableDimensions">
                        All dimensions have been assigned.
                    </div>
                </div>

                <!-- Create New Dimension Inline -->
                <div class="create-dimension-section mt-3">
                    <button type="button" id="createNewDimensionBtn" class="btn btn-outline-primary btn-sm">
                        <i class="fas fa-plus"></i> Create New Dimension
                    </button>
                </div>

                <!-- Inline Creation Form (initially hidden) -->
                <div id="inlineDimensionForm" style="display: none;">
                    <!-- Dimension creation form fields -->
                </div>
            </div>

            <!-- Footer -->
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>
```

**Features:**
- Dynamic content loading based on `fieldId`
- Real-time updates when dimensions are added/removed
- Loading states during API calls
- Error state handling
- Responsive design

---

### 3. Computed Field Validation Service
**File:** `app/static/js/shared/ComputedFieldDimensionValidator.js`

**Purpose:** Validate that computed fields and their dependencies have consistent dimensions

**Public API:**
```javascript
window.ComputedFieldDimensionValidator = {
    // Validate before assigning dimensions to computed field
    validateBeforeAssignment(fieldId, dimensionIds),

    // Validate before removing dimension from raw field
    validateBeforeRemoval(fieldId, dimensionId),

    // Get validation errors in user-friendly format
    formatValidationErrors(validationResult)
};
```

**Validation Logic:**

**Rule 1: Computed Field Assignment**
```javascript
// When assigning dimensions to a computed field
// Check: All dependencies have AT LEAST those dimensions

async function validateBeforeAssignment(computedFieldId, newDimensionIds) {
    // 1. Check if field is computed
    const field = await fetchField(computedFieldId);
    if (!field.is_computed) return { valid: true };

    // 2. Get all dependencies from formula
    const dependencies = await fetchDependencies(computedFieldId);

    // 3. For each dependency, check if it has all required dimensions
    const errors = [];
    for (const dep of dependencies) {
        const depDimensions = await fetchFieldDimensions(dep.field_id);
        const missingDims = newDimensionIds.filter(
            dimId => !depDimensions.includes(dimId)
        );

        if (missingDims.length > 0) {
            errors.push({
                fieldId: dep.field_id,
                fieldName: dep.field_name,
                missingDimensions: missingDims,
                currentDimensions: depDimensions
            });
        }
    }

    return {
        valid: errors.length === 0,
        errors: errors
    };
}
```

**Rule 2: Raw Field Dimension Removal**
```javascript
// When removing dimension from a raw field
// Check: No computed fields depend on this dimension

async function validateBeforeRemoval(rawFieldId, dimensionId) {
    // 1. Find all computed fields that use this raw field
    const computedFields = await fetchComputedFieldsUsingField(rawFieldId);

    // 2. Check if any computed field requires this dimension
    const conflicts = [];
    for (const cf of computedFields) {
        const cfDimensions = await fetchFieldDimensions(cf.field_id);
        if (cfDimensions.includes(dimensionId)) {
            conflicts.push({
                fieldId: cf.field_id,
                fieldName: cf.field_name,
                requiredDimensions: cfDimensions
            });
        }
    }

    return {
        valid: conflicts.length === 0,
        conflicts: conflicts
    };
}
```

**Error Formatting:**
```javascript
function formatValidationErrors(validationResult) {
    if (validationResult.valid) return null;

    // Format assignment errors
    if (validationResult.errors) {
        return {
            title: 'Cannot assign dimensions',
            message: 'The following dependencies are missing required dimensions:',
            details: validationResult.errors.map(err => ({
                field: err.fieldName,
                missing: err.missingDimensions.map(getDimensionName),
                current: err.currentDimensions.map(getDimensionName)
            }))
        };
    }

    // Format removal errors
    if (validationResult.conflicts) {
        return {
            title: 'Cannot remove dimension',
            message: 'This dimension is required by the following computed fields:',
            details: validationResult.conflicts.map(cf => ({
                field: cf.fieldName,
                required: cf.requiredDimensions.map(getDimensionName)
            }))
        };
    }
}
```

---

### 4. Dimension UI Components

#### A. Dimension Badge Component
**File:** `app/static/js/shared/DimensionBadge.js`

**Purpose:** Render dimension name badges

**API:**
```javascript
window.DimensionBadge = {
    // Render badges for a list of dimensions
    render(dimensions, containerId),

    // Add tooltip to badge
    addTooltip(badgeElement, dimensionValues),

    // Clear all badges
    clear(containerId)
};
```

**HTML Output:**
```html
<span class="dimension-badge" data-dimension-id="dim-123" title="Gender: Male, Female, Other">
    Gender
</span>
```

**CSS:**
```css
.dimension-badge {
    display: inline-flex;
    align-items: center;
    padding: 3px 10px;
    background: #e3f2fd;
    border: 1px solid #90caf9;
    border-radius: 12px;
    font-size: 11px;
    color: #1976d2;
    margin-right: 6px;
    margin-bottom: 4px;
    cursor: help;
    transition: all 0.2s ease;
}

.dimension-badge:hover {
    background: #bbdefb;
    border-color: #64b5f6;
}
```

#### B. Dimension Tooltip Component
**File:** `app/static/js/shared/DimensionTooltip.js`

**Purpose:** Show dimension values on hover

**API:**
```javascript
window.DimensionTooltip = {
    // Initialize tooltip for badge
    init(badgeElement, dimensionData),

    // Destroy tooltip
    destroy(badgeElement)
};
```

**Implementation:**
- Uses Bootstrap Tooltip component
- 500ms delay before showing
- Auto-hide on mouse leave
- Shows dimension name and values

---

### 5. CSS Styling
**File:** `app/static/css/shared/dimension-management.css`

**Sections:**
1. Dimension badges
2. Dimension modal layout
3. Assigned/Available dimension cards
4. Inline creation form
5. Loading states
6. Error states
7. Responsive breakpoints

---

### 6. Backend API Enhancements
**File:** `app/routes/admin_dimensions.py`

**New Endpoint:** Computed Field Validation
```python
@admin_bp.route('/fields/<field_id>/dimensions/validate', methods=['POST'])
@login_required
@admin_or_super_admin_required
def validate_field_dimensions(field_id):
    """
    Validate dimension assignment for computed fields.

    Request Body:
    {
        "dimension_ids": ["dim-1", "dim-2"],
        "action": "assign" or "remove",
        "dimension_id": "dim-1"  // For remove action
    }

    Response:
    {
        "valid": true/false,
        "errors": [...],  // For assignment validation
        "conflicts": [...]  // For removal validation
    }
    """
    data = request.get_json()
    action = data.get('action', 'assign')

    field = FrameworkDataField.query.get_or_404(field_id)

    if action == 'assign':
        dimension_ids = data.get('dimension_ids', [])
        result = validate_computed_field_assignment(field, dimension_ids)
    elif action == 'remove':
        dimension_id = data.get('dimension_id')
        result = validate_dimension_removal(field, dimension_id)
    else:
        return jsonify({'error': 'Invalid action'}), 400

    return jsonify(result)
```

**Validation Functions:**
```python
def validate_computed_field_assignment(field, dimension_ids):
    """Validate that all dependencies have required dimensions."""
    if not field.is_computed:
        return {'valid': True}

    # Get dependencies
    dependencies = field.get_dependencies()
    errors = []

    for dep in dependencies:
        dep_dimensions = get_field_dimension_ids(dep.field_id)
        missing_dims = [d for d in dimension_ids if d not in dep_dimensions]

        if missing_dims:
            errors.append({
                'field_id': dep.field_id,
                'field_name': dep.field_name,
                'missing_dimensions': missing_dims,
                'current_dimensions': dep_dimensions
            })

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def validate_dimension_removal(field, dimension_id):
    """Validate that no computed fields require this dimension."""
    # Find computed fields that use this field
    computed_fields = find_computed_fields_using(field.field_id)
    conflicts = []

    for cf in computed_fields:
        cf_dimensions = get_field_dimension_ids(cf.field_id)
        if dimension_id in cf_dimensions:
            conflicts.append({
                'field_id': cf.field_id,
                'field_name': cf.field_name,
                'required_dimensions': cf_dimensions
            })

    return {
        'valid': len(conflicts) == 0,
        'conflicts': conflicts
    }
```

---

## Implementation Steps

### Step 1: Create Shared Module Structure (4 hours)
1. Create `/static/js/shared/` directory
2. Create `DimensionManagerShared.js` skeleton
3. Define public API and event system
4. Set up module initialization

### Step 2: Extract Dimension Modal Logic (6 hours)
1. Review `frameworks-dimensions.js`
2. Extract modal opening/closing logic
3. Extract dimension loading logic
4. Extract assignment/removal logic
5. Make generic (remove framework-specific code)
6. Add parameter-based initialization

### Step 3: Create Validation Service (4 hours)
1. Create `ComputedFieldDimensionValidator.js`
2. Implement assignment validation logic
3. Implement removal validation logic
4. Add error formatting
5. Write unit tests for validation logic

### Step 4: Create UI Components (4 hours)
1. Create `DimensionBadge.js`
2. Create `DimensionTooltip.js`
3. Implement badge rendering
4. Implement tooltip functionality
5. Add CSS styling

### Step 5: Create Modal Template (2 hours)
1. Create `_dimension_management_modal.html`
2. Add assigned dimensions section
3. Add available dimensions section
4. Add inline creation form
5. Add loading/error states

### Step 6: Backend Validation Endpoint (3 hours)
1. Add validation endpoint to `admin_dimensions.py`
2. Implement validation functions
3. Add comprehensive error messages
4. Test with various scenarios

### Step 7: Refactor Frameworks Page (3 hours)
1. Update `frameworks-dimensions.js` to use shared component
2. Remove duplicated code
3. Test backward compatibility
4. Ensure no regression

### Step 8: Testing (4 hours)
1. Unit tests for validation logic
2. Integration tests for API endpoints
3. Manual testing of frameworks page
4. Performance testing

**Total Estimated Time:** 30 hours (2 working days with buffer)

---

## Testing Requirements

### Unit Tests
1. Dimension validation logic (20+ test cases)
2. Badge rendering
3. Tooltip functionality
4. Event emission

### Integration Tests
1. Frameworks page still works (no regression)
2. Modal opens and closes correctly
3. Dimensions can be assigned/removed
4. Validation blocks invalid operations
5. Error messages display correctly

### Manual Testing Checklist
- [ ] Frameworks page dimension management works as before
- [ ] Modal opens with correct field context
- [ ] Assigned dimensions display correctly
- [ ] Available dimensions display correctly
- [ ] Add dimension button works
- [ ] Remove dimension button works
- [ ] Validation prevents invalid computed field configs
- [ ] Error messages are clear and actionable
- [ ] Tooltips show dimension values
- [ ] Loading states display during API calls
- [ ] Success/error notifications appear

---

## Success Criteria

1. ✅ Shared component created and functional
2. ✅ Frameworks page refactored to use shared component (no regression)
3. ✅ Computed field validation working correctly
4. ✅ UI components render properly
5. ✅ All unit tests pass
6. ✅ All integration tests pass
7. ✅ Code review approved
8. ✅ Documentation complete

---

## Dependencies

**Existing Code:**
- `app/routes/admin_dimensions.py` (dimension APIs)
- `app/static/js/admin/frameworks/frameworks-dimensions.js` (current implementation)
- `app/models/dimension.py` (dimension models)
- `app/models/framework.py` (field models)

**External Libraries:**
- Bootstrap 5 (modal, tooltip)
- Font Awesome (icons)
- jQuery (DOM manipulation)

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking frameworks page | HIGH | Thorough testing, backward compatibility checks |
| Validation too strict | MEDIUM | User testing, clear error messages |
| Performance issues | LOW | Optimize queries, implement caching |

---

## Next Phase

After Phase 1 completion, proceed to **Phase 2: Integration with Assign Data Points** where the shared component will be integrated into the assign data points workflow.
