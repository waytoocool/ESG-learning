# Enhancement #1: Computed Field Modal - Requirements & Specifications

**Date Created:** 2025-11-15
**Status:** In Progress - Implementation Started
**Priority:** High
**Complexity:** Medium
**Estimated Effort:** 12-18 hours

---

## Executive Summary

This enhancement fixes a critical UX bug where computed fields incorrectly show data input forms instead of calculation details. The solution provides a read-only view showing the calculated result, formula, dependencies, and actionable buttons to edit dependency data.

---

## Problem Statement

### Current Behavior (Bug)

Computed fields (e.g., "Total rate of new employee hires") currently show the same data input modal as raw input fields when users click "View Data". This is incorrect because:

1. **Computed fields should NOT allow manual data entry** - values are calculated from dependencies
2. Users see input forms, date selectors, and file upload options for read-only fields
3. No visibility into how the value is calculated or which fields it depends on
4. Users cannot easily navigate to dependency fields to fix incorrect data

### Expected Behavior

When clicking "View Data" on a computed field, users should see:
- ✅ The calculated result (read-only)
- ✅ The calculation formula in human-readable format
- ✅ All dependencies with their current values
- ✅ Edit/Add buttons for each dependency to fix or input data
- ✅ Clear warnings when dependencies are missing data
- ✅ No input form for the computed field itself

### Impact

- **Affects:** ALL computed fields in the system
- **User Confusion:** Users don't understand why they can "enter data" for calculated fields
- **Data Integrity:** Risk of users attempting to manually override calculated values
- **Workflow Efficiency:** Users cannot quickly identify and fix missing dependency data

---

## Solution Design

### Approach: Enhanced Modal with Dual View

**Core Principle:** Use the same modal (`dataCollectionModal`) but render different content based on field type.

### Tab Structure

#### For Computed Fields:

**Tab 1: "Calculation & Dependencies"**
- Section 1: Computed Result (value, status, timestamp)
- Section 2: Calculation Formula (human-readable)
- Section 3: Dependencies Breakdown (table with edit buttons)
- Section 4: Missing Data Warning (conditional)

**Tab 2: "Historical Data"**
- Historical computed values
- Export buttons (CSV/Excel)

**Tab 3: "Field Info"**
- Field metadata, framework info, description

#### For Raw Input Fields (No Changes):
- Tab 1: Current Entry (input form)
- Tab 2: Historical Data
- Tab 3: Field Info

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│          Frontend: Modal Opening Logic                  │
├─────────────────────────────────────────────────────────┤
│ • Detect field type (computed vs raw)                   │
│ • Store globally: window.currentFieldType               │
│ • Call appropriate loading function                     │
│ • Configure tabs and footer buttons                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│          Frontend: ComputedFieldView Component           │
├─────────────────────────────────────────────────────────┤
│ • Load computed field details via API                   │
│ • Render calculation result section                     │
│ • Render formula with variable mapping                  │
│ • Render dependencies table with status                 │
│ • Attach edit handlers for dependencies                 │
│ • Show warnings for missing dependencies                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│          Backend: Computed Field Details API             │
├─────────────────────────────────────────────────────────┤
│ • GET /api/user/v2/computed-field-details/<field_id>    │
│ • Validate field is computed                            │
│ • Fetch ESGData for computed result                     │
│ • Iterate through variable mappings                     │
│ • Fetch dependency values                               │
│ • Determine status (complete/partial/no_data)           │
│ • Return comprehensive response                         │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Backend API ✅

**File:** `app/routes/user_v2/field_api.py`

**New Endpoint:** `GET /api/user/v2/computed-field-details/<field_id>`

**Query Parameters:**
- `entity_id` (required)
- `reporting_date` (required)

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
        }
    ],
    "missing_dependencies": []
}
```

### Phase 2: Frontend Component ✅

**File:** `app/static/js/user_v2/computed_field_view.js` (NEW)

**Key Methods:**
- `load(fieldId, entityId, reportingDate)` - Load and render view
- `render(data)` - Render complete view
- `renderComputedResult(result)` - Result display
- `renderFormula(formula, variableMapping)` - Formula display
- `renderDependencies(dependencies)` - Dependencies table
- `attachEditHandlers()` - Attach click handlers
- `openDependencyModal(fieldId, fieldName)` - Open dependency modal

### Phase 3: CSS Styling ✅

**File:** `app/static/css/user_v2/computed_field_view.css` (NEW)

**Sections:**
- `.computed-field-view` - Main container
- `.result-section` - Computed result with gradient
- `.missing-data-warning` - Warning box (red theme)
- `.formula-section` - Formula display
- `.dependencies-section` - Dependencies table
- Dark mode support

### Phase 4: Integration ✅

**File:** `app/templates/user_v2/dashboard.html`

**Updates:**
1. Add script/CSS includes
2. Update modal opening logic to detect field type
3. Update modal footer to show/hide buttons
4. Configure tabs based on field type

---

## Test Cases

### TC1: Computed Field Modal Opens with Calculation View
**Expected:**
- Modal opens with "View Computed Field" title
- Shows computed result, formula, dependencies
- No input form shown
- "Save Data" hidden, "Export" visible

### TC2: Computed Field with Missing Dependencies
**Expected:**
- Warning box: "Cannot Calculate - Missing Data"
- Dependencies show "Missing" status
- "Add Data" buttons instead of "Edit"

### TC3: Edit Dependency from Computed Field Modal
**Expected:**
- Current modal closes
- Dependency modal opens with input form
- Can edit dependency data

### TC4: Raw Input Field Still Works
**Expected:**
- Modal shows input form (not calculation view)
- "Save Data" visible, "Export" hidden

### TC5: Historical Data Tab Works for Both Types
**Expected:**
- Both field types show historical data correctly
- Export buttons work

### TC6: Field Info Tab Shows Formula for Computed Fields
**Expected:**
- Field metadata shown
- "Calculation Formula" section visible

### TC7: Multiple Levels of Dependencies
**Expected:**
- Shows direct dependencies
- Computed dependencies show as "computed" type

### TC8: Dark Mode Support
**Expected:**
- All text readable in dark mode
- Proper color scheme

### TC9: Responsive Design
**Expected:**
- Modal responsive at all breakpoints
- Tables scroll horizontally on mobile

### TC10: Notes Integration
**Expected:**
- Notes field works for computed fields
- Notes display in dependencies view

---

## Success Criteria

✅ Computed fields do NOT show input form
✅ Computed fields show calculation details
✅ Each dependency has edit/add button
✅ Missing dependencies show warnings
✅ Raw input fields continue to work
✅ All tabs work for both field types
✅ Modal footer adapts based on field type
✅ Dark mode fully supported
✅ Responsive design works
✅ All 10 test cases pass

---

## Files to Create/Modify

### New Files (3)
1. `app/static/js/user_v2/computed_field_view.js` (~450 lines)
2. `app/static/css/user_v2/computed_field_view.css` (~400 lines)
3. Backend endpoint in `app/routes/user_v2/field_api.py` (~150 lines)

### Modified Files (2)
1. `app/templates/user_v2/dashboard.html` (modal logic, script includes)
2. `app/routes/user_v2/__init__.py` (verify blueprint registration)

---

## Risk Assessment

**Low Risk:**
- ✅ Uses existing modal structure (no breaking changes)
- ✅ Additive changes (new component, new endpoint)
- ✅ No database schema changes required
- ✅ Clear separation between computed and raw field logic

**Medium Risk:**
- ⚠️ Modal interaction complexity (opening dependency modals)
- ⚠️ State management (tracking field type, ID)

**Mitigation:**
- Comprehensive testing of modal navigation
- Clear global state variables
- Fallback error handling

---

## Rollback Plan

1. **Feature Flag:** Add toggle to disable computed field view
2. **Quick Fix:** Revert to old behavior (show input form for all fields)
3. **Full Rollback:** Remove new files and revert dashboard changes

---

**Prepared By:** Claude Code (AI Agent)
**Date:** 2025-11-15
**Status:** Implementation In Progress
