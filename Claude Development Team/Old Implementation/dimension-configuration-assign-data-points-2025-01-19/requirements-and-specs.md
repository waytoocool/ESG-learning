# Dimension Configuration in Assign Data Points - Requirements & Specifications

**Feature Name:** Dimension Configuration in Assign Data Points Page
**Start Date:** 2025-01-19
**Feature Owner:** Backend Developer
**Status:** Planning

---

## Executive Summary

Enable administrators to configure field dimensions directly from the Assign Data Points page, eliminating the need to navigate to the Frameworks page for dimension management. This feature provides a unified workflow for data point assignment configuration while maintaining strict tenant isolation and data integrity for computed fields.

---

## Business Requirements

### Primary Goal
Provide a convenient, single-page workflow for administrators to:
1. Assign data points to entities
2. Configure frequency, units, and material topics
3. **Manage field dimensions** (NEW)

All within the Assign Data Points interface.

### Key Stakeholders
- **Admins:** Primary users who assign and configure data points
- **Users:** Benefit from consistent dimensional data collection
- **Super Admins:** Manage cross-tenant dimension isolation

---

## Functional Requirements

### FR-1: Dimension Indicator Display
**Priority:** HIGH
**Description:** Display dimension indicators on field cards in the Selected Data Points panel

**Acceptance Criteria:**
- Show dimension name badges for fields with assigned dimensions
- Badges appear below field metadata (frequency, framework, topic)
- No indicator shown when field has no dimensions (clean display)
- Dimension badges use consistent styling with existing UI

**Visual Example:**
```
┌─────────────────────────────────────────────────┐
│ [✓] Total Employees                             │
│     Annual · GRI 2-7 · Social                   │
│     Gender, Age Group, Department         [⚙️] [ℹ️] [🗑️] │
│     ▸ 3 entities assigned                       │
└─────────────────────────────────────────────────┘
```

---

### FR-2: Manage Dimensions Button
**Priority:** HIGH
**Description:** Add a "Manage Dimensions" action button to each field card

**Acceptance Criteria:**
- Button appears alongside existing action buttons (Configure, Info, Remove)
- Icon: `fas fa-sliders-h`
- Button color changes when field has dimensions assigned:
  - **Gray/default:** No dimensions assigned
  - **Blue/accent:** Dimensions assigned
- Click opens Dimension Management Modal for that specific field
- No field selection required (button works independently)
- Button state updates immediately after dimension changes

---

### FR-3: Dimension Management Modal (Shared Component)
**Priority:** HIGH
**Description:** Create a reusable dimension management modal that works across Frameworks and Assign Data Points pages

**Acceptance Criteria:**

**Modal Structure:**
```
┌──────────────────────────────────────────────────────┐
│ Manage Dimensions: [Field Name]              [✕]   │
├──────────────────────────────────────────────────────┤
│ Currently Assigned Dimensions                        │
│ ┌──────────────────────────────────────────────┐   │
│ │ ✓ Gender                           [Remove] │   │
│ │   Values: Male, Female, Other               │   │
│ │                                              │   │
│ │ ✓ Age Group                        [Remove] │   │
│ │   Values: <30, 30-50, >50                   │   │
│ └──────────────────────────────────────────────┘   │
│                                                      │
│ ──────────────────────────────────────────────────  │
│                                                      │
│ Available Dimensions                                 │
│ ┌──────────────────────────────────────────────┐   │
│ │ ☐ Department                          [Add] │   │
│ │   Values: IT, Finance, HR, Operations       │   │
│ │                                              │   │
│ │ ☐ Region                              [Add] │   │
│ │   Values: North, South, East, West          │   │
│ └──────────────────────────────────────────────┘   │
│                                                      │
│ [+ Create New Dimension]                            │
│                                                      │
├──────────────────────────────────────────────────────┤
│                          [Cancel]  [Save Changes]   │
└──────────────────────────────────────────────────────┘
```

**Modal Sections:**
1. **Header:** Shows field name being configured
2. **Assigned Dimensions:** List of currently assigned dimensions with Remove button
3. **Available Dimensions:** List of company dimensions not yet assigned with Add button
4. **Create New Dimension:** Inline dimension creation flow
5. **Footer:** Cancel and Save Changes buttons

**Behavior:**
- Modal is context-aware (receives `fieldId` and `fieldName` as parameters)
- Works in both Frameworks page and Assign Data Points page
- Loads current field dimensions on open
- Loads available company dimensions (tenant-scoped)
- Add/Remove actions save immediately (no pending state)
- Modal can be closed anytime - changes already persisted
- Shows loading states during API calls
- Shows success/error notifications

---

### FR-4: Dimension Badge Tooltip
**Priority:** MEDIUM
**Description:** Show dimension values in a tooltip when hovering over dimension badges

**Acceptance Criteria:**
- Hover over dimension badge shows tooltip
- Tooltip displays: `"[Dimension Name]: [Value1], [Value2], [Value3]"`
- Example: `"Gender: Male, Female, Other, Prefer not to say"`
- Tooltip appears after 500ms hover
- Tooltip disappears on mouse leave
- Uses consistent tooltip styling with existing system

---

### FR-5: Create New Dimension Inline
**Priority:** MEDIUM
**Description:** Allow admins to create new dimensions directly from the Dimension Management Modal

**Acceptance Criteria:**
- "Create New Dimension" button visible in modal footer
- Click opens inline dimension creation form
- Form fields:
  - Dimension Name (required)
  - Description (optional)
  - Dimension Values (minimum 2 required)
- Validation:
  - Dimension name must be unique within company
  - At least 2 values required
- Save creates dimension and automatically assigns it to the current field
- Cancel returns to dimension selection view
- Shows success message on creation
- New dimension appears in "Assigned Dimensions" section

---

### FR-6: Toolbar Quick Access (Optional)
**Priority:** LOW
**Description:** Add "Manage Dimensions" button to main toolbar for quick access

**Acceptance Criteria:**
- Button only enabled when exactly 1 field is selected
- Tooltip when disabled: "Select a single field to manage dimensions"
- Click opens Dimension Management Modal for selected field
- Button placement: between "Assign Entities" and "Save All"
- Follows same styling as other toolbar buttons

---

## Non-Functional Requirements

### NFR-1: Multi-Tenant Isolation
**Priority:** CRITICAL
**Description:** Ensure complete tenant isolation for dimension configurations

**Requirements:**
- All dimension queries must be tenant-scoped (filtered by `company_id`)
- Dimension assignments in Company A must NOT affect Company B
- Same global field can have different dimensions in different companies
- `FieldDimension` junction table uses `company_id` for isolation
- API endpoints validate tenant context before operations
- Comprehensive testing for cross-tenant isolation

**Test Coverage:**
- Cross-tenant dimension assignment test
- Cross-tenant dimension visibility test
- Cross-tenant dimension modification test

---

### NFR-2: Computed Field Dimension Validation
**Priority:** CRITICAL
**Description:** Enforce dimension consistency for computed fields and their dependencies

**Business Rule:**
> **When assigning dimensions to a computed field, all dependencies (raw fields) MUST have AT LEAST the same dimensions. Dependencies can have MORE dimensions but CANNOT have FEWER.**

**Rationale:**
You cannot compute dimensional aggregations if the source data lacks those dimensions.

**Example:**
```
Computed Field: "Energy Intensity" = Total_Energy / Total_Employees
Assigned Dimensions: [Gender, Department]

Dependency 1: "Total Energy"
Required Dimensions: [Gender, Department] (minimum)
Allowed Dimensions: [Gender, Department, Region] ✅
Invalid Dimensions: [Department] ❌ (missing Gender)

Dependency 2: "Total Employees"
Required Dimensions: [Gender, Department] (minimum)
Allowed Dimensions: [Gender, Department] ✅
```

**Validation Requirements:**

1. **Pre-assignment Validation:**
   - Before assigning dimensions to a computed field, validate all dependencies
   - If any dependency has fewer dimensions, **block the operation**
   - Show clear error message indicating which dependency needs which dimensions

2. **Error Message Format:**
   ```
   ❌ Cannot assign dimensions to "Energy Intensity"

   The following dependencies are missing required dimensions:

   • Total Energy (missing: Gender)
     Current: [Department]
     Required: [Gender, Department]

   Please add the missing dimensions to dependencies first.
   ```

3. **Dependency Modification Protection:**
   - When removing dimensions from a raw field, check if it's used by computed fields
   - If removal would violate computed field requirements, **block the operation**
   - Show warning listing affected computed fields

4. **API-Level Validation:**
   - Validation enforced at API level (cannot bypass via direct DB access)
   - Returns 400 Bad Request with detailed error message
   - Frontend displays error in modal

**Test Coverage:**
- Valid computed field dimension assignment (all deps have required dims)
- Invalid computed field dimension assignment (dep missing required dim)
- Dimension removal from dependency blocked (computed field requires it)
- Dimension removal from dependency allowed (no computed fields require it)

---

### NFR-3: Performance
**Priority:** HIGH
**Description:** Maintain fast response times for dimension operations

**Requirements:**
- Dimension modal opens in < 300ms
- Dimension assignment/removal completes in < 500ms
- Dimension badge rendering in < 100ms per field
- No blocking UI operations
- Optimistic UI updates with rollback on error

---

### NFR-4: User Experience
**Priority:** HIGH
**Description:** Ensure intuitive and consistent user experience

**Requirements:**
- Clear visual feedback for all actions
- Loading states for async operations
- Success/error notifications
- Consistent styling with existing UI
- Responsive design (works on all screen sizes)
- Accessibility compliance (ARIA labels, keyboard navigation)

---

## Technical Architecture

### Components

#### 1. Backend (Existing - No Changes Required)
**Endpoints:**
- `GET /admin/dimensions` - List company dimensions
- `POST /admin/dimensions` - Create new dimension
- `GET /admin/fields/<field_id>/dimensions` - Get field dimensions
- `POST /admin/fields/<field_id>/dimensions` - Assign dimension to field
- `DELETE /admin/fields/<field_id>/dimensions/<dimension_id>` - Remove dimension

**Models:**
- `Dimension` - Dimension definitions (tenant-scoped)
- `DimensionValue` - Values within dimensions
- `FieldDimension` - Junction table linking fields to dimensions (tenant-scoped)

#### 2. Frontend Components (New)

**Shared Component:**
- `DimensionManagerShared.js` - Reusable dimension management modal

**Assign Data Points Integration:**
- `DimensionConfigModule.js` - Dimension configuration module for assign data points

**Frameworks Refactoring:**
- Refactor `frameworks-dimensions.js` to use `DimensionManagerShared.js`

---

## Implementation Phases

### Phase 1: Shared Dimension Component
**Goal:** Create reusable dimension management infrastructure

**Deliverables:**
1. `DimensionManagerShared.js` - Shared modal component
2. Dimension modal HTML template
3. CSS styling for dimension UI
4. Dimension validation service for computed fields
5. Unit tests for shared component

**Timeline:** 2 days

---

### Phase 2: Integration with Assign Data Points
**Goal:** Integrate dimension management into assign data points workflow

**Deliverables:**
1. `DimensionConfigModule.js` - Integration module
2. Dimension badge component
3. Dimension tooltip component
4. "Manage Dimensions" button in field cards
5. Optional toolbar button
6. Integration tests

**Timeline:** 1.5 days

---

### Phase 3: Testing & Validation
**Goal:** Comprehensive testing of all features and edge cases

**Deliverables:**
1. Tenant isolation tests
2. Computed field validation tests
3. UI/UX testing with `@ui-testing-agent`
4. Performance testing
5. Accessibility testing

**Timeline:** 1.5 days

**Total Timeline:** 5 days

---

## Test Cases

### Test Suite 1: Core Functionality

#### TC-1.1: Display Dimension Badges
**Given:** Field "Total Employees" has dimensions [Gender, Age Group]
**When:** Field card is rendered in Selected Data Points panel
**Then:**
- Dimension badges "Gender" and "Age Group" are visible
- Badges appear below field metadata
- Badges use correct styling

#### TC-1.2: No Dimension Indicator
**Given:** Field "Revenue" has no dimensions
**When:** Field card is rendered
**Then:**
- No dimension badges shown
- Field card displays cleanly without empty space

#### TC-1.3: Open Dimension Modal
**Given:** Field "Total Employees" in Selected Data Points panel
**When:** User clicks "Manage Dimensions" button
**Then:**
- Dimension Management Modal opens
- Modal title shows "Manage Dimensions: Total Employees"
- Currently assigned dimensions are listed
- Available dimensions are listed

#### TC-1.4: Assign Dimension to Field
**Given:** Dimension Management Modal is open for "Total Employees"
**And:** "Department" dimension is available but not assigned
**When:** User clicks "Add" next to "Department"
**Then:**
- "Department" moves to "Assigned Dimensions" section
- API call succeeds (immediate save)
- Success notification appears
- Modal reflects updated state

#### TC-1.5: Remove Dimension from Field
**Given:** Dimension Management Modal is open for "Total Employees"
**And:** "Gender" dimension is assigned
**When:** User clicks "Remove" next to "Gender"
**Then:**
- "Gender" moves to "Available Dimensions" section
- API call succeeds (immediate save)
- Success notification appears
- Modal reflects updated state

#### TC-1.6: Dimension Badge Tooltip
**Given:** Field "Total Employees" has dimension "Gender" with values [Male, Female, Other]
**When:** User hovers over "Gender" badge
**Then:**
- Tooltip appears after 500ms
- Tooltip shows: "Gender: Male, Female, Other"
- Tooltip disappears on mouse leave

#### TC-1.7: Create New Dimension Inline
**Given:** Dimension Management Modal is open
**When:** User clicks "Create New Dimension"
**And:** Fills form with Name: "Employment Type", Values: ["Full-time", "Part-time", "Contract"]
**And:** Clicks "Save"
**Then:**
- New dimension is created for current company
- Dimension is automatically assigned to current field
- Dimension appears in "Assigned Dimensions" section
- Success notification appears

---

### Test Suite 2: Multi-Tenant Isolation (CRITICAL)

#### TC-2.1: Cross-Tenant Dimension Visibility
**Given:** User is admin for Company Alpha
**And:** Company Alpha has dimension "Gender"
**And:** Company Beta has dimension "Region"
**When:** User opens Dimension Management Modal
**Then:**
- "Gender" appears in available dimensions
- "Region" does NOT appear in available dimensions
- Only Company Alpha dimensions are visible

#### TC-2.2: Cross-Tenant Dimension Assignment
**Given:** User is admin for Company Alpha
**And:** Field "Total Employees" is global (shared across companies)
**When:** User assigns "Gender" dimension to "Total Employees" in Company Alpha
**Then:**
- "Gender" is assigned to field in Company Alpha context only
- Company Beta's view of "Total Employees" is unchanged
- `field_dimensions` table shows entry with `company_id = Company Alpha ID`

#### TC-2.3: Cross-Tenant Dimension Modification
**Given:** Company Alpha has assigned "Gender" to "Total Employees"
**And:** Company Beta has assigned "Department" to "Total Employees"
**When:** User in Company Alpha removes "Gender" dimension
**Then:**
- "Gender" is removed from Company Alpha's field configuration
- Company Beta's "Department" assignment remains unchanged
- No cross-tenant impact

---

### Test Suite 3: Computed Field Validation (CRITICAL)

#### TC-3.1: Valid Computed Field Dimension Assignment
**Given:** Computed field "Energy Intensity" with formula: `Total_Energy / Total_Employees`
**And:** Dependency "Total Energy" has dimensions: [Gender, Department, Region]
**And:** Dependency "Total Employees" has dimensions: [Gender, Department]
**When:** User assigns dimensions [Gender, Department] to "Energy Intensity"
**Then:**
- Assignment succeeds
- No validation errors
- Success notification appears

#### TC-3.2: Invalid Computed Field - Missing Dimension in Dependency
**Given:** Computed field "Energy Intensity" with formula: `Total_Energy / Total_Employees`
**And:** Dependency "Total Energy" has dimensions: [Department] (missing Gender)
**And:** Dependency "Total Employees" has dimensions: [Gender, Department]
**When:** User attempts to assign dimensions [Gender, Department] to "Energy Intensity"
**Then:**
- Operation is blocked (API returns 400 error)
- Error modal appears with message:
  ```
  ❌ Cannot assign dimensions to "Energy Intensity"

  The following dependencies are missing required dimensions:

  • Total Energy (missing: Gender)
    Current: [Department]
    Required: [Gender, Department]

  Please add the missing dimensions to dependencies first.
  ```
- No changes are saved

#### TC-3.3: Invalid Computed Field - Multiple Missing Dimensions
**Given:** Computed field "Efficiency Ratio" with 3 dependencies
**And:** Dependency 1 missing "Gender"
**And:** Dependency 2 missing "Gender" and "Region"
**And:** Dependency 3 has all required dimensions
**When:** User attempts to assign [Gender, Department, Region]
**Then:**
- Operation blocked
- Error lists all dependencies with missing dimensions
- Clear guidance on what needs to be added

#### TC-3.4: Dimension Removal Protection - Computed Field Requires It
**Given:** Raw field "Total Energy" has dimensions [Gender, Department]
**And:** Computed field "Energy Intensity" requires [Gender, Department] from "Total Energy"
**When:** User attempts to remove "Gender" from "Total Energy"
**Then:**
- Operation blocked (API returns 400 error)
- Warning message appears:
  ```
  ⚠️ Cannot remove "Gender" dimension

  This dimension is required by the following computed fields:

  • Energy Intensity (requires: Gender, Department)

  Please remove the computed field dimensions first, or add "Gender" to its other dependencies.
  ```
- No changes are saved

#### TC-3.5: Dimension Removal Allowed - No Computed Fields
**Given:** Raw field "Total Employees" has dimensions [Gender, Department, Region]
**And:** No computed fields depend on "Total Employees" requiring "Region"
**When:** User removes "Region" from "Total Employees"
**Then:**
- Removal succeeds
- Success notification appears
- Badge updates to show only [Gender, Department]

---

### Test Suite 4: User Experience

#### TC-4.1: Button Color Change
**Given:** Field "Total Employees" initially has no dimensions
**When:** User assigns "Gender" dimension
**Then:**
- "Manage Dimensions" button changes from gray to blue
- Button reflects assigned state immediately

#### TC-4.2: Real-time Badge Update
**Given:** Dimension Management Modal is open
**When:** User assigns "Department" dimension
**Then:**
- Field card badge updates in real-time (without closing modal)
- "Department" badge appears in field card

#### TC-4.3: Loading States
**Given:** User clicks "Add" to assign dimension
**When:** API call is in progress
**Then:**
- Loading spinner appears on "Add" button
- Button is disabled during request
- Other actions are disabled

#### TC-4.4: Error Handling
**Given:** API returns 500 error during dimension assignment
**When:** Error occurs
**Then:**
- Error notification appears with clear message
- Operation rolls back to previous state
- User can retry action

---

### Test Suite 5: Performance

#### TC-5.1: Modal Open Performance
**Given:** Field with 3 assigned dimensions
**When:** User clicks "Manage Dimensions"
**Then:**
- Modal opens in < 300ms
- All data loads and renders

#### TC-5.2: Dimension Assignment Performance
**Given:** User clicks "Add" for dimension
**When:** API call completes
**Then:**
- Response time < 500ms
- UI updates immediately

#### TC-5.3: Badge Rendering Performance
**Given:** Selected Data Points panel with 20 fields
**And:** Each field has 2-3 dimensions
**When:** Panel renders
**Then:**
- All badges render in < 2 seconds total
- No UI lag or blocking

---

## Success Criteria

1. ✅ Dimension badges display correctly for all fields
2. ✅ "Manage Dimensions" button functions on all field cards
3. ✅ Dimension Management Modal opens and operates correctly
4. ✅ Dimension assignment/removal saves immediately
5. ✅ Dimension tooltips show correct values
6. ✅ Multi-tenant isolation is complete (zero cross-tenant leakage)
7. ✅ Computed field validation enforces dimension consistency
8. ✅ All test cases pass (100% success rate)
9. ✅ Performance targets met (< 500ms for all operations)
10. ✅ UI/UX is intuitive and consistent with existing design

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing frameworks page | HIGH | Extract shared component carefully, maintain backward compatibility |
| Computed field validation too strict | MEDIUM | Provide clear error messages with actionable guidance |
| Cross-tenant data leakage | CRITICAL | Comprehensive tenant isolation testing, API-level validation |
| Performance degradation with many dimensions | MEDIUM | Optimize queries, implement caching, lazy loading |
| User confusion about dimension inheritance | LOW | Clear UI indicators, tooltips, help text |

---

## Future Enhancements (Out of Scope)

1. Bulk dimension assignment (assign same dimensions to multiple fields)
2. Dimension templates (pre-defined dimension sets)
3. Dimension usage analytics (which dimensions are most used)
4. Dimension value auto-complete during data entry
5. Dimension-based data export filtering

---

## Approval

**Requirements Approved By:** _______________ Date: _______________
**Technical Review By:** _______________ Date: _______________
**Ready for Implementation:** ☐ Yes  ☐ No

---

**Next Steps:**
1. Review and approve requirements
2. Begin Phase 1: Shared Dimension Component
3. Conduct code review after each phase
4. UI testing with `@ui-testing-agent`
5. Production deployment after all tests pass
