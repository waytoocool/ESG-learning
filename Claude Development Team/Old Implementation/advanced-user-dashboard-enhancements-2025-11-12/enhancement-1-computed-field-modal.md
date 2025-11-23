# Enhancement #1: Computed Field Modal - Prevent Data Input & Show Calculation Details

**Date Created:** 2025-11-12
**Status:** Planning Complete - Ready for Implementation
**Priority:** High
**Complexity:** Medium

---

## Problem Statement

### Current Behavior (Bug)
In the user dashboard, computed fields (e.g., "Total rate of new employee hires during the reporting period, by age group, gen..") currently show the same data input modal as raw input fields when users click "View Data". This is incorrect because:

1. **Computed fields should NOT allow manual data entry** - their values are calculated from dependencies
2. Users see input forms, date selectors, and file upload options for fields that should be read-only
3. There's no visibility into how the value is calculated or which fields it depends on
4. Users cannot easily navigate to dependency fields to fix incorrect data

### Expected Behavior
When clicking "View Data" on a computed field, users should see:
- ✅ The calculated result (read-only)
- ✅ The calculation formula in human-readable format
- ✅ All dependencies with their current values
- ✅ Edit/Add buttons for each dependency to fix or input data
- ✅ Clear warnings when dependencies are missing data
- ✅ Links to navigate to dependency fields

### Impact
- **Affects:** ALL computed fields in the system
- **User Confusion:** Users don't understand why they can "enter data" for calculated fields
- **Data Integrity:** Risk of users attempting to manually override calculated values
- **Workflow Efficiency:** Users cannot quickly identify and fix missing dependency data

---

## Solution Design

### Approach: Enhanced Modal with Merged Tab View

**Core Principle:** Use the same modal (`dataCollectionModal`) but render different content based on field type.

### Tab Structure

#### For Computed Fields (when "View Data" is clicked):

**Tab 1: "Current Entry"** (Enhanced - Merged Calculation View)
- **Section 1: Computed Result**
  - Large, prominent display of calculated value
  - Status badge (Complete/Pending/Error)
  - Unit display
  - Last calculated timestamp

- **Section 2: Calculation Formula**
  - Human-readable formula (e.g., "Male Employees + Female Employees")
  - Variable mapping (A, B, C, etc.)
  - Mathematical notation

- **Section 3: Dependencies Breakdown**
  - Table showing each dependency:
    - Variable name (A, B, C)
    - Field name
    - Current value with unit
    - Status indicator (✓ Available, ⚠ Pending, ✗ Missing)
    - **[📝 Edit]** button to open dependency modal

- **Section 4: Missing Data Warning** (conditional)
  - Highlighted warning box
  - "⚠️ Cannot calculate - X dependencies need data"
  - Links to open dependency modals

**Tab 2: "Historical Data"**
- Historical computed values
- Export buttons (CSV/Excel)

**Tab 3: "Field Info"**
- Field metadata, framework info, description

#### For Raw Input Fields (No Changes):
- **Tab 1:** Current Entry (input form)
- **Tab 2:** Historical Data
- **Tab 3:** Field Info

---

## Visual Mockups

### Complete Data State
```
┌───────────────────────────────────────────────────────────────┐
│ View Computed Field: Total Employee Count    [Auto-saved] [×] │
├───────────────────────────────────────────────────────────────┤
│ [Current Entry] [Historical Data] [Field Info]                │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📊 Computed Result                                      │ │
│ │                                                         │ │
│ │    150 employees                       [✓ Complete]    │ │
│ │    Last calculated: 2025-01-12 10:30 AM               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📐 Calculation Formula                                  │ │
│ │                                                         │ │
│ │    Male Employees + Female Employees                   │ │
│ │    (Variable A)      (Variable B)                      │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🔗 Dependencies                                         │ │
│ │                                                         │ │
│ │ ┌────────┬──────────────────┬───────┬────────┬────────┐│ │
│ │ │Variable│ Field Name       │ Value │ Status │ Action ││ │
│ │ ├────────┼──────────────────┼───────┼────────┼────────┤│ │
│ │ │   A    │ Male Employees   │ 85    │   ✓    │[📝Edit]││ │
│ │ │   B    │Female Employees  │ 65    │   ✓    │[📝Edit]││ │
│ │ └────────┴──────────────────┴───────┴────────┴────────┘│ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│                                              [Close] [Export] │
└───────────────────────────────────────────────────────────────┘
```

### Missing Dependencies State
```
┌───────────────────────────────────────────────────────────────┐
│ View Computed Field: Total Employee Count    [Auto-saved] [×] │
├───────────────────────────────────────────────────────────────┤
│ [Current Entry] [Historical Data] [Field Info]                │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ⚠️ Cannot Calculate - Missing Data                      │ │
│ │                                                         │ │
│ │ This field requires data from 2 dependencies:          │ │
│ │ • Male Employees - No data for selected date           │ │
│ │ • Female Employees - No data for selected date         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📐 Calculation Formula                                  │ │
│ │    Male Employees + Female Employees                   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🔗 Dependencies                                         │ │
│ │                                                         │ │
│ │ ┌────────┬──────────────────┬───────┬────────┬────────┐│ │
│ │ │Variable│ Field Name       │ Value │ Status │ Action ││ │
│ │ ├────────┼──────────────────┼───────┼────────┼────────┤│ │
│ │ │   A    │ Male Employees   │  N/A  │   ✗    │[📝Add] ││ │
│ │ │   B    │Female Employees  │  N/A  │   ✗    │[📝Add] ││ │
│ │ └────────┴──────────────────┴───────┴────────┴────────┘│ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│                                                        [Close] │
└───────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### 1. Frontend Changes

#### 1.1 Modal Opening Logic Enhancement
**File:** `app/templates/user_v2/dashboard.html` (lines 992-1087)

**Changes:**
```javascript
// Update: Open modal when clicking "Enter Data" or "View Data" buttons
document.querySelectorAll('.open-data-modal').forEach(button => {
    button.addEventListener('click', async function() {
        const fieldId = this.dataset.fieldId;
        const fieldName = this.dataset.fieldName;
        const fieldType = this.dataset.fieldType; // 'computed' or 'raw_input'

        // Store field type globally
        window.currentFieldType = fieldType;
        window.currentFieldId = fieldId;

        // Update modal title based on field type
        const modalTitle = fieldType === 'computed' ? 'View Computed Field' : 'Enter Data';
        document.getElementById('dataCollectionModalLabel').innerHTML =
            `${modalTitle}: <span id="modalFieldName">${fieldName}</span>`;

        // Show/hide tabs based on field type
        configureTabs(fieldType);

        // Load appropriate content for Current Entry tab
        if (fieldType === 'computed') {
            await loadComputedFieldView(fieldId, entityId, reportingDate);
        } else {
            // Existing raw input logic
            loadRawInputView(fieldId, entityId, reportingDate);
        }

        modal.show();
    });
});

function configureTabs(fieldType) {
    // For computed fields: hide dimensional inputs, show read-only view
    // For raw fields: show input form
    const entryTab = document.getElementById('tab-entry');

    if (fieldType === 'computed') {
        entryTab.textContent = 'Calculation & Dependencies';
    } else {
        entryTab.textContent = 'Current Entry';
    }
}
```

#### 1.2 New Computed Field View Component
**File:** `app/static/js/user_v2/computed_field_view.js` (NEW)

**Purpose:** Renders computed field calculation details with dependencies

**Key Methods:**
- `load(fieldId, entityId, reportingDate)` - Load and render computed field view
- `render(data)` - Render complete view with all sections
- `renderComputedResult(result)` - Section 1: Result display
- `renderMissingDataWarning(missingDeps)` - Section 2: Warning (conditional)
- `renderFormula(formula, variableMapping)` - Section 3: Formula display
- `renderDependencies(dependencies)` - Section 4: Dependencies table
- `attachEditHandlers()` - Attach click handlers to Edit/Add buttons
- `openDependencyModal(fieldId, fieldName, fieldType)` - Open dependency field modal

**Component Structure:**
```javascript
class ComputedFieldView {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentFieldId = null;
        this.currentEntityId = null;
        this.currentDate = null;
    }

    async load(fieldId, entityId, reportingDate) {
        // Fetch data from API
        // Render complete view
    }

    render(data) {
        // Combine all sections
        const html = `
            <div class="computed-field-view">
                ${this.renderComputedResult(data.result)}
                ${this.renderMissingDataWarning(data.missing_dependencies)}
                ${this.renderFormula(data.formula, data.variable_mapping)}
                ${this.renderDependencies(data.dependencies)}
            </div>
        `;
        this.container.innerHTML = html;
        this.attachEditHandlers();
    }

    renderComputedResult(result) {
        // Display calculated value with status badge
    }

    renderMissingDataWarning(missingDeps) {
        // Show warning if dependencies missing
    }

    renderFormula(formula, variableMapping) {
        // Display formula with variable mapping
    }

    renderDependencies(dependencies) {
        // Render dependencies table with edit buttons
    }

    attachEditHandlers() {
        // Attach click handlers to Edit/Add buttons
        this.container.querySelectorAll('.btn-edit-dependency').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const fieldId = e.currentTarget.dataset.fieldId;
                const fieldName = e.currentTarget.dataset.fieldName;
                this.openDependencyModal(fieldId, fieldName, 'raw_input');
            });
        });
    }

    openDependencyModal(fieldId, fieldName, fieldType) {
        // Close current modal
        // Open dependency field modal
    }
}

// Initialize globally
window.computedFieldView = null;
document.addEventListener('DOMContentLoaded', function() {
    window.computedFieldView = new ComputedFieldView('entry-tab');
});
```

**Full implementation includes:**
- Loading states and error handling
- Format helpers (formatValue, formatDate, formatStatus)
- Status icons and badges
- HTML escaping for security
- Event handler management

#### 1.3 CSS Styling
**File:** `app/static/css/user_v2/computed_field_view.css` (NEW)

**Sections:**
- `.computed-field-view` - Main container
- `.result-section` - Computed result display with gradient background
- `.missing-data-warning` - Warning box styling (red theme)
- `.formula-section` - Formula display with code styling
- `.dependencies-section` - Dependencies table
- `.dependencies-table` - Table styling with hover effects
- Button styles for Edit/Add actions
- Loading and error states
- Dark mode support for all sections
- Responsive design utilities

**Key Features:**
- Color-coded status indicators
- Green gradient for successful calculations
- Red gradient for warnings
- Clean, professional table design
- Accessible hover states
- Material Icons integration

#### 1.4 Modal Footer Enhancement
**File:** `app/templates/user_v2/dashboard.html` (lines 499-502)

**Change:** Hide "Save Data" button for computed fields, show "Export" button instead

```html
<!-- Modal Footer -->
<div class="modal-footer">
    <button type="button" class="btn btn-secondary btn-cancel" data-bs-dismiss="modal">Cancel</button>
    <!-- Show for raw input fields only -->
    <button type="button" class="btn btn-primary btn-submit" id="submitDataBtn" style="display: none;">
        Save Data
    </button>
    <!-- Show for computed fields only -->
    <button type="button" class="btn btn-success btn-export" id="exportDataBtn" style="display: none;">
        <span class="material-icons text-sm mr-1">download</span>
        Export History
    </button>
</div>
```

**JavaScript to toggle buttons:**
```javascript
// Show/hide footer buttons based on field type
const submitBtn = document.getElementById('submitDataBtn');
const exportBtn = document.getElementById('exportDataBtn');

if (window.currentFieldType === 'computed') {
    submitBtn.style.display = 'none';
    exportBtn.style.display = 'inline-flex';
} else {
    submitBtn.style.display = 'inline-flex';
    exportBtn.style.display = 'none';
}
```

---

### 2. Backend Changes

#### 2.1 New API Endpoint: Get Computed Field Details with Dependencies
**File:** `app/routes/user_v2/field_api.py`

**Endpoint:** `GET /api/user/v2/computed-field-details/<field_id>`

**Query Parameters:**
- `entity_id` (required): Entity ID
- `reporting_date` (required): Reporting date (YYYY-MM-DD)

**Response Structure:**
```json
{
    "success": true,
    "field_id": "abc-123",
    "field_name": "Total Employee Count",
    "result": {
        "value": 150,
        "unit": "employees",
        "status": "complete",
        "calculated_at": "2025-01-12T10:30:00"
    },
    "formula": "A + B",
    "variable_mapping": {
        "A": {"field_id": "def-456", "field_name": "Male Employees"},
        "B": {"field_id": "ghi-789", "field_name": "Female Employees"}
    },
    "dependencies": [
        {
            "field_id": "def-456",
            "field_name": "Male Employees",
            "variable": "A",
            "value": 85,
            "unit": "employees",
            "status": "available",
            "reporting_date": "2025-01-31"
        },
        {
            "field_id": "ghi-789",
            "field_name": "Female Employees",
            "variable": "B",
            "value": 65,
            "unit": "employees",
            "status": "available",
            "reporting_date": "2025-01-31"
        }
    ],
    "missing_dependencies": []
}
```

**Status Values:**
- **Result Status:** `complete`, `partial`, `no_data`, `failed`
- **Dependency Status:** `available`, `missing`, `pending`

**Implementation Logic:**
1. Validate field is computed
2. Check active assignment for entity
3. Fetch ESGData for computed result
4. Iterate through variable mappings to get dependencies
5. For each dependency:
   - Fetch ESGData for same reporting date
   - Determine status (available/missing)
   - Build dependency info object
6. Track missing dependencies
7. Return comprehensive response

**Error Handling:**
- 400: Missing required parameters or invalid date format
- 404: Field not found or not assigned to entity
- 400: Field is not a computed field
- 500: Server error with stack trace logging

---

### 3. Integration Steps

#### Step 1: Add New JS and CSS Files
1. Create `app/static/js/user_v2/computed_field_view.js`
2. Create `app/static/css/user_v2/computed_field_view.css`
3. Add script and link tags to `dashboard.html`:

```html
<!-- Add after line 1617 -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/user_v2/computed_field_view.css') }}">
<script src="{{ url_for('static', filename='js/user_v2/computed_field_view.js') }}"></script>
```

#### Step 2: Update Modal Opening Logic
In `dashboard.html` (lines 992-1087), update the `.open-data-modal` click handler to:
1. Detect field type from `data-field-type` attribute
2. Store globally in `window.currentFieldType`
3. Call appropriate loading function:
   - Computed: `window.computedFieldView.load()`
   - Raw: Existing logic

#### Step 3: Update Modal Footer Logic
Add logic to show/hide buttons based on `window.currentFieldType`:
- Computed: Hide "Save Data", show "Export"
- Raw: Show "Save Data", hide "Export"

#### Step 4: Register New API Endpoint
In `app/routes/user_v2/__init__.py`, ensure the field_api blueprint is registered (should already be done).

#### Step 5: Test in Development
1. Start Flask dev server: `python3 run.py`
2. Login as user with computed fields
3. Test all scenarios (complete data, missing data, editing dependencies)

---

### 4. Test Cases

#### Test Case 1: Computed Field Modal Opens with Calculation View
**Preconditions:**
- User is logged in
- Entity has at least one computed field assigned
- Computed field has complete dependency data

**Steps:**
1. Navigate to user dashboard
2. Find a computed field card (has "Computed" badge)
3. Click "View Data" button

**Expected Results:**
- ✅ Modal opens with title "View Computed Field: [Field Name]"
- ✅ "Current Entry" tab shows:
  - Computed result section with value and status badge
  - Formula section with readable formula
  - Dependencies table with all dependencies listed
  - All dependencies show "Available" status with values
  - Each dependency has an "Edit" button
- ✅ No input form is shown
- ✅ "Save Data" button is hidden
- ✅ "Export" button is visible in footer

---

#### Test Case 2: Computed Field with Missing Dependencies
**Preconditions:**
- User is logged in
- Entity has a computed field assigned
- At least one dependency is missing data for selected date

**Steps:**
1. Navigate to user dashboard
2. Find computed field with missing data
3. Click "View Data"

**Expected Results:**
- ✅ Modal opens
- ✅ Warning box appears: "Cannot Calculate - Missing Data"
- ✅ Warning lists which dependencies are missing
- ✅ Computed result section shows "No Calculated Value"
- ✅ Dependencies table shows missing dependencies with "Missing" status
- ✅ Missing dependencies have "Add Data" buttons instead of "Edit"

---

#### Test Case 3: Edit Dependency from Computed Field Modal
**Preconditions:**
- User is logged in
- Computed field modal is open
- At least one dependency has data

**Steps:**
1. Open computed field modal (View Data)
2. In dependencies table, click "Edit" button for a dependency
3. Make changes in the opened dependency modal
4. Save changes
5. Close dependency modal

**Expected Results:**
- ✅ Current modal closes
- ✅ Dependency modal opens showing dependency field's input form
- ✅ Can edit dependency data
- ✅ After saving, user returns to dashboard
- ✅ (Optional enhancement) Re-opening computed field shows updated dependency value

---

#### Test Case 4: Add Data for Missing Dependency
**Preconditions:**
- Computed field has missing dependency
- Computed field modal is open showing warning

**Steps:**
1. Open computed field modal with missing data
2. Click "Add Data" button for missing dependency
3. Enter data in opened modal
4. Save data
5. Re-open computed field modal

**Expected Results:**
- ✅ Dependency modal opens
- ✅ Can enter data for dependency
- ✅ After saving, computed field recalculates
- ✅ Re-opening computed field shows:
  - Updated dependency status to "Available"
  - Dependency value populated
  - Computed result updated (if all deps complete)
  - Warning removed (if all deps complete)

---

#### Test Case 5: Raw Input Field Still Works
**Preconditions:**
- User is logged in
- Entity has raw input fields assigned

**Steps:**
1. Navigate to dashboard
2. Find a raw input field (has "Raw Input" badge)
3. Click "Enter Data"

**Expected Results:**
- ✅ Modal opens with title "Enter Data: [Field Name]"
- ✅ Current Entry tab shows input form (not calculation view)
- ✅ Date selector, value input, dimensional grid (if applicable) visible
- ✅ "Save Data" button visible
- ✅ "Export" button hidden
- ✅ No "Calculation Details" content shown

---

#### Test Case 6: Historical Data Tab Works for Both Types
**Preconditions:**
- Both computed and raw fields have historical data

**Steps:**
1. Open computed field modal
2. Click "Historical Data" tab
3. Verify historical computed values shown
4. Close modal
5. Open raw input field modal
6. Click "Historical Data" tab
7. Verify historical raw values shown

**Expected Results:**
- ✅ Both field types show historical data correctly
- ✅ Computed fields show calculated values
- ✅ Raw fields show raw input values
- ✅ Export buttons work for both

---

#### Test Case 7: Field Info Tab Shows Formula for Computed Fields
**Preconditions:**
- Computed field modal is open

**Steps:**
1. Open computed field modal
2. Click "Field Info" tab

**Expected Results:**
- ✅ Field metadata shown
- ✅ "Calculation Formula" section visible
- ✅ Formula displayed
- ✅ Dependencies listed with variable mappings

---

#### Test Case 8: Multiple Levels of Dependencies
**Preconditions:**
- Computed field A depends on computed field B
- Computed field B depends on raw fields C and D

**Steps:**
1. Open computed field A modal
2. Check dependencies list

**Expected Results:**
- ✅ Shows direct dependencies (field B)
- ✅ Field B shows as "computed" type
- ✅ Clicking "Edit" on field B opens field B's computed modal
- ✅ (Future enhancement) Could show full dependency tree

---

#### Test Case 9: Dark Mode Support
**Steps:**
1. Toggle dark mode
2. Open computed field modal
3. Verify all sections are readable

**Expected Results:**
- ✅ All text is readable in dark mode
- ✅ Color scheme matches dark theme
- ✅ Status badges are visible
- ✅ Tables and sections have proper contrast

---

#### Test Case 10: Responsive Design
**Steps:**
1. Open computed field modal on mobile viewport (375px)
2. Verify layout
3. Test on tablet (768px)
4. Test on desktop (1920px)

**Expected Results:**
- ✅ Modal is responsive at all breakpoints
- ✅ Dependencies table scrolls horizontally if needed on mobile
- ✅ Buttons stack properly on small screens
- ✅ Text is readable at all sizes

---

### 5. Success Criteria

✅ **Computed fields do NOT show input form when "View Data" is clicked**
✅ **Computed fields show calculation details with formula and dependencies**
✅ **Each dependency has an edit/add button that opens the dependency's modal**
✅ **Missing dependencies show clear warnings with actionable buttons**
✅ **Raw input fields continue to work as before (no regression)**
✅ **All tabs work correctly for both field types**
✅ **Modal footer buttons adapt based on field type**
✅ **Dark mode is fully supported**
✅ **Responsive design works on all screen sizes**
✅ **All 10 test cases pass**

---

### 6. Future Enhancements (Out of Scope)

1. **Nested Dependency Tree Visualization**: Show full tree when computed fields depend on other computed fields
2. **Inline Dependency Editing**: Edit dependency values without closing current modal (modal stacking)
3. **Real-time Recalculation**: Auto-update computed value when dependency is edited
4. **Calculation History**: Show how computed value changed over time with dependency changes
5. **Dependency Graph**: Visual graph showing relationships between fields using D3.js or similar
6. **Formula Builder**: Visual formula builder in admin panel
7. **What-if Analysis**: Allow users to see how changing a dependency affects computed values
8. **Batch Dependency Updates**: Update multiple dependencies at once

---

## Code Files to Create/Modify

### New Files
1. `app/static/js/user_v2/computed_field_view.js` - ComputedFieldView component (~450 lines)
2. `app/static/css/user_v2/computed_field_view.css` - Styling for computed field view (~400 lines)

### Modified Files
1. `app/templates/user_v2/dashboard.html`:
   - Lines 992-1087: Update modal opening logic
   - Lines 499-502: Update modal footer
   - After line 1617: Add new script/link tags

2. `app/routes/user_v2/field_api.py`:
   - Add new endpoint: `get_computed_field_details()` (~150 lines)

3. `app/routes/user_v2/__init__.py`:
   - Verify field_api blueprint is registered

---

## Estimated Effort

**Development Time:**
- Frontend Component: 4-6 hours
- CSS Styling: 2-3 hours
- Backend API: 2-3 hours
- Integration: 1-2 hours
- Testing: 3-4 hours
- **Total: 12-18 hours**

**Complexity Breakdown:**
- JavaScript Component: Medium (state management, event handling)
- CSS Styling: Low-Medium (mostly standard patterns)
- Backend Logic: Medium (dependency resolution, status calculation)
- Testing: Medium (multiple scenarios, edge cases)

---

## Dependencies

**Technical Dependencies:**
- Bootstrap 5 (for modal)
- Material Icons (for icons)
- Existing ESGData and FrameworkDataField models
- Existing VariableMapping model
- Existing DataPointAssignment model

**Functional Dependencies:**
- Must maintain backward compatibility with raw input fields
- Must not break existing historical data tab
- Must not break existing field info tab
- Must work with existing auto-save handler

---

## Risk Assessment

**Low Risk:**
- ✅ Uses existing modal structure (no breaking changes)
- ✅ Additive changes (new component, new endpoint)
- ✅ No database schema changes required
- ✅ Clear separation between computed and raw field logic

**Medium Risk:**
- ⚠️ Modal interaction complexity (opening dependency modals from computed modal)
- ⚠️ State management (tracking current field type, ID)

**Mitigation:**
- Comprehensive testing of modal navigation flows
- Clear global state variables with documentation
- Fallback error handling for edge cases

---

## Rollback Plan

If issues are found after deployment:

1. **Immediate:** Add feature flag to disable computed field view
   ```javascript
   const ENABLE_COMPUTED_FIELD_VIEW = false; // Toggle to disable
   ```

2. **Quick Fix:** Revert to old behavior (show input form for all fields)
   - Comment out field type check
   - Always load raw input view

3. **Full Rollback:** Remove new files and revert dashboard.html changes
   - Keep backend API (won't hurt if unused)
   - Remove JS/CSS file includes
   - Revert modal opening logic

---

## Monitoring & Metrics

**Success Metrics:**
1. **User Engagement:** Track clicks on "View Data" for computed fields
2. **Dependency Navigation:** Track clicks on Edit/Add buttons in dependencies table
3. **Modal Completion:** Track users closing modal after viewing calculation details
4. **Error Rate:** Monitor API errors for new endpoint

**User Feedback Questions:**
1. Is it clear how the computed value is calculated?
2. Is it easy to navigate to dependency fields?
3. Do you find the warning messages helpful?
4. Would you like any additional information in the calculation view?

---

## Documentation Updates Needed

1. **User Guide:**
   - How to view computed field details
   - Understanding calculation formulas
   - Editing dependency data
   - Troubleshooting missing dependencies

2. **Admin Guide:**
   - How computed fields appear to users
   - Setting up dependencies
   - Best practices for computed field assignment

3. **Developer Documentation:**
   - ComputedFieldView component API
   - New backend endpoint documentation
   - Testing guide for computed fields

---

## Sign-off

**Prepared By:** Claude Code (AI Agent)
**Date:** 2025-11-12
**Review Status:** Awaiting implementation
**Approved By:** [Pending]

---

## Notes

- This enhancement was discussed and designed collaboratively with the product owner
- The merged tab approach (combining result, formula, and dependencies) was chosen for better UX
- Future enhancements list is extensive and can be prioritized based on user feedback
- Implementation can be done incrementally (frontend first, then backend, then integration)
