# Phase 6: Popups & Modals Extraction - Requirements & Specifications

**Date**: September 30, 2025
**Phase**: 6 of 10
**Status**: 🔄 IN PROGRESS
**Target Completion**: September 30, 2025

---

## Executive Summary

Phase 6 focuses on extracting and modularizing all modal dialogs and popup functionality from the monolithic `assign_data_points_redesigned.js` file into a dedicated `PopupsModule.js`. This phase also includes comprehensive documentation and rigorous testing.

### Goals
1. ✅ Extract all modal and dialog functionality into `PopupsModule.js`
2. ✅ Consolidate popup logic from multiple source files
3. ✅ Implement event-driven modal management
4. ✅ Create comprehensive testing suite with Playwright
5. ✅ Generate complete phase documentation

### Progress Target
- **Current Progress**: ~60% modularized (after Phase 5)
- **Target Progress**: ~75% modularized (after Phase 6)
- **Lines to Extract**: ~900 lines

---

## Phase 6 Scope

### Source Files to Consolidate

1. **From `assign_data_points_redesigned.js`** (~600 lines):
   - Configuration modal logic
   - Entity assignment modal
   - Field information dialogs
   - Modal state management
   - Form validation logic

2. **From `assign_data_point_ConfirmationDialog.js`** (~359 lines):
   - Confirmation dialog component
   - Dialog utilities
   - Action confirmation patterns

3. **From `assign_data_points_import.js`** (modal portions ~100 lines):
   - Import modal UI
   - Export modal UI
   - File upload dialogs

---

## Module Architecture

### PopupsModule.js Structure

```javascript
// app/static/js/admin/assign_data_points/PopupsModule.js
(function() {
    'use strict';

    const PopupsModule = {
        // Module state
        state: {
            activeModal: null,
            modalStack: [],
            modalData: {}
        },

        // DOM element references
        elements: {
            configurationModal: null,
            entityAssignmentModal: null,
            fieldInformationModal: null,
            importModal: null,
            exportModal: null,
            confirmationDialog: null
        },

        // Initialization
        init() {
            this.cacheElements();
            this.bindEvents();
            console.log('[PopupsModule] Popups module initialized successfully');
        },

        // Configuration Modal (~200 lines)
        showConfigurationModal(dataPoints) { },
        populateConfigurationForm(dataPoints) { },
        handleConfigurationSave() { },
        validateConfigurationForm() { },

        // Entity Assignment Modal (~200 lines)
        showEntityAssignmentModal(dataPoints) { },
        renderEntityTree() { },
        handleEntitySelection() { },
        saveEntityAssignments() { },

        // Field Information Modal (~100 lines)
        showFieldInformation(fieldId) { },
        loadFieldDetails(fieldId) { },
        displayCalculationMethodology() { },

        // Import/Export Modals (~200 lines)
        showImportModal() { },
        showExportModal() { },
        handleFileUpload() { },
        validateImportData() { },
        generateExportConfig() { },

        // Confirmation Dialog (~150 lines)
        showConfirmationDialog(options) { },
        showSuccessDialog(message) { },
        showErrorDialog(message) { },
        showWarningDialog(message) { },

        // Modal Management (~50 lines)
        openModal(modalType, data) { },
        closeModal(modalType) { },
        closeAllModals() { },
        isModalOpen() { },
        getActiveModal() { }
    };

    // Export to global scope
    window.PopupsModule = PopupsModule;

})();
```

---

## Detailed Requirements

### 1. Configuration Modal

**Purpose**: Allow bulk configuration of selected data points

**Features Required**:
- ✅ Display list of selected data points
- ✅ Form fields:
  - Data collection frequency (Monthly/Quarterly/Annual)
  - Unit override selector
  - Reporting period configuration
  - FY-based date validation
  - Custom instructions field
- ✅ Form validation before save
- ✅ Preview changes before applying
- ✅ Batch save to all selected items
- ✅ Success/error feedback

**Events to Emit**:
- `configuration-modal-opened`
- `configuration-modal-closed`
- `configuration-saved`
- `configuration-validation-error`

**Events to Listen**:
- `toolbar-configure-clicked`
- `configure-datapoint` (individual configuration)

**API Integration**:
```javascript
// Save configuration
POST /admin/api/assignments/configure
Body: {
    dataPointIds: [],
    configuration: {
        frequency: "monthly",
        unitOverride: "kg CO2e",
        reportingPeriod: {...}
    }
}
```

---

### 2. Entity Assignment Modal

**Purpose**: Assign data points to entities/facilities

**Features Required**:
- ✅ Hierarchical entity tree display
- ✅ Parent/child entity relationships
- ✅ Checkbox selection with:
  - Individual entity selection
  - Parent selection auto-selects children
  - "Select All" / "Deselect All" options
- ✅ Search/filter entities
- ✅ Show already-assigned entities
- ✅ Batch assignment to multiple entities
- ✅ Assignment versioning integration

**Events to Emit**:
- `entity-assignment-modal-opened`
- `entity-assignment-modal-closed`
- `entities-assigned`
- `entity-selection-changed`

**Events to Listen**:
- `toolbar-assign-clicked`
- `assign-to-entities` (from context menu)

**API Integration**:
```javascript
// Save entity assignments
POST /admin/api/assignments/assign-entities
Body: {
    dataPointIds: [],
    entityIds: [],
    configuration: {...}
}
```

---

### 3. Field Information Modal

**Purpose**: Display detailed information about a data point/field

**Features Required**:
- ✅ Field name and description
- ✅ Framework origin
- ✅ Topic hierarchy
- ✅ Calculation methodology
- ✅ Unit information and conversions
- ✅ Data quality requirements
- ✅ Reporting standards
- ✅ Historical data (if available)
- ✅ Related fields suggestions

**Events to Emit**:
- `field-info-modal-opened`
- `field-info-modal-closed`
- `field-info-loaded`

**Events to Listen**:
- `show-field-info` (from info icon clicks)

**API Integration**:
```javascript
// Get field details
GET /admin/api/frameworks/field/{fieldId}/details
```

---

### 4. Import Modal

**Purpose**: Import assignments from CSV/Excel

**Features Required**:
- ✅ Drag-and-drop file upload
- ✅ File format validation
- ✅ CSV/Excel parsing
- ✅ Import preview with data table
- ✅ Row-level validation
- ✅ Error highlighting
- ✅ Downloadable error report
- ✅ Mapping configuration
- ✅ Progress indicator during import
- ✅ Success/failure summary

**Events to Emit**:
- `import-modal-opened`
- `import-modal-closed`
- `import-started`
- `import-progress`
- `import-completed`
- `import-validation-error`

**Events to Listen**:
- `toolbar-import-clicked`

**API Integration**:
```javascript
// Import assignments
POST /admin/api/assignments/import
Body: FormData with file
```

---

### 5. Export Modal

**Purpose**: Export assignments to CSV/Excel

**Features Required**:
- ✅ Export format selection (CSV/Excel)
- ✅ Filter options:
  - By framework
  - By entity
  - By topic
  - By date range
- ✅ Column selection
- ✅ Include/exclude inactive assignments
- ✅ Template download option
- ✅ Progress indicator
- ✅ File download trigger

**Events to Emit**:
- `export-modal-opened`
- `export-modal-closed`
- `export-started`
- `export-completed`
- `export-downloaded`

**Events to Listen**:
- `toolbar-export-clicked`

**API Integration**:
```javascript
// Export assignments
POST /admin/api/assignments/export
Body: {
    format: "csv",
    filters: {...},
    columns: [...]
}
```

---

### 6. Confirmation Dialog

**Purpose**: Generic confirmation/alert dialogs

**Dialog Types**:

1. **Confirmation Dialog**:
   ```javascript
   PopupsModule.showConfirmationDialog({
       title: "Confirm Action",
       message: "Are you sure?",
       confirmText: "Yes, continue",
       cancelText: "Cancel",
       onConfirm: () => { /* action */ },
       onCancel: () => { /* cleanup */ },
       type: "warning" // success, error, warning, info
   });
   ```

2. **Success Dialog**:
   ```javascript
   PopupsModule.showSuccessDialog("Operation completed successfully!");
   ```

3. **Error Dialog**:
   ```javascript
   PopupsModule.showErrorDialog("An error occurred: " + errorMessage);
   ```

4. **Warning Dialog**:
   ```javascript
   PopupsModule.showWarningDialog("This action cannot be undone.");
   ```

**Events to Emit**:
- `confirmation-dialog-opened`
- `confirmation-dialog-closed`
- `confirmation-confirmed`
- `confirmation-cancelled`

---

## Event Flow Examples

### Configuration Flow

```
User clicks "Configure Selected" in toolbar
  ↓
CoreUI emits 'toolbar-configure-clicked'
  ↓
PopupsModule listens and receives event
  ↓
PopupsModule.showConfigurationModal(selectedDataPoints)
  ↓
Modal displays with form pre-populated
  ↓
User fills form and clicks Save
  ↓
PopupsModule.handleConfigurationSave()
  ↓
Validate form → If valid, call API
  ↓
ServicesModule.callAPI('/api/assignments/configure', data)
  ↓
API success → Update AppState
  ↓
AppState.setConfiguration() → emits 'configuration-saved'
  ↓
SelectedDataPointsPanel listens → updates status indicators
CoreUI listens → shows success message
PopupsModule.closeModal('configuration')
```

### Entity Assignment Flow

```
User clicks "Assign to Entities" in toolbar
  ↓
CoreUI emits 'toolbar-assign-clicked'
  ↓
PopupsModule listens and opens entity assignment modal
  ↓
Modal loads entity tree via ServicesModule.loadEntities()
  ↓
User selects entities (parent/child logic handled)
  ↓
User clicks Save
  ↓
PopupsModule.saveEntityAssignments()
  ↓
VersioningModule.createAssignmentVersion() for each assignment
  ↓
ServicesModule.callAPI('/api/assignments/assign-entities', data)
  ↓
API success → AppEvents.emit('entities-assigned')
  ↓
SelectedDataPointsPanel updates assignment status
CoreUI shows success notification
PopupsModule.closeModal('entityAssignment')
```

---

## Testing Requirements

### 1. Unit Tests (Per Modal Type)

**Configuration Modal**:
- [ ] Opens correctly with selected data points
- [ ] Form validation catches empty required fields
- [ ] Unit override selector populates correctly
- [ ] Frequency selection shows appropriate sub-options
- [ ] Save button disabled until form valid
- [ ] API call made with correct payload
- [ ] Success/error handling works

**Entity Assignment Modal**:
- [ ] Entity tree renders with hierarchy
- [ ] Parent selection auto-selects children
- [ ] Deselecting child shows partial parent selection
- [ ] "Select All" selects all entities
- [ ] Search filters entity list
- [ ] Save creates proper assignments
- [ ] Already-assigned entities indicated

**Field Information Modal**:
- [ ] Opens with correct field ID
- [ ] Displays all field details
- [ ] Calculation methodology formatted correctly
- [ ] Related fields shown
- [ ] Close button works

**Import Modal**:
- [ ] File upload accepts CSV/Excel
- [ ] Rejects invalid file types
- [ ] Preview displays data correctly
- [ ] Validation errors highlighted
- [ ] Error report downloadable
- [ ] Import progress shown
- [ ] Success summary accurate

**Export Modal**:
- [ ] Format selection works
- [ ] Filters apply correctly
- [ ] Column selection updates preview
- [ ] Template download works
- [ ] Export generates file
- [ ] File downloads correctly

**Confirmation Dialog**:
- [ ] Shows correct message/title
- [ ] Confirm button triggers callback
- [ ] Cancel button triggers cancel callback
- [ ] ESC key closes dialog
- [ ] Click outside closes dialog
- [ ] Type styling (success/error/warning) applies

---

### 2. Integration Tests

**Modal Interactions**:
- [ ] Opening modal from different triggers works
- [ ] Modal closes and cleans up properly
- [ ] Multiple modals don't interfere (modal stack)
- [ ] Modal data persists during session
- [ ] Events propagate correctly

**Cross-Module Communication**:
- [ ] Configuration saved updates SelectedDataPointsPanel
- [ ] Entity assignment updates AppState
- [ ] Import completion reloads data
- [ ] Export uses current filter state

**State Synchronization**:
- [ ] Modal changes reflect in AppState
- [ ] AppState changes trigger modal updates
- [ ] No stale data in modals

---

### 3. Visual Tests with Playwright

**Viewport Tests**:
- [ ] Desktop (1920x1080)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

**Modal Display**:
- [ ] Modals centered correctly
- [ ] Backdrop darkens background
- [ ] Close button visible
- [ ] Scrolling works for long content
- [ ] Responsive on small screens

**Form Elements**:
- [ ] All inputs accessible
- [ ] Dropdowns functional
- [ ] Checkboxes toggle correctly
- [ ] Radio buttons exclusive
- [ ] Date pickers work

**Accessibility**:
- [ ] Keyboard navigation works (Tab, Shift+Tab)
- [ ] ESC key closes modal
- [ ] Enter key submits form
- [ ] Focus trapped in modal
- [ ] ARIA labels present
- [ ] Screen reader compatible

---

### 4. Performance Tests

**Modal Load Time**:
- [ ] Configuration modal < 200ms
- [ ] Entity assignment modal < 500ms (with tree)
- [ ] Field info modal < 300ms
- [ ] Import preview < 1s (for 1000 rows)

**Memory Usage**:
- [ ] No memory leaks on open/close cycles
- [ ] Event listeners cleaned up
- [ ] Large datasets handled efficiently

---

## Success Criteria

### Functional Requirements
- [ ] All 6 modal types fully functional
- [ ] All modals can open/close correctly
- [ ] Form validation works on all modals
- [ ] API integration successful for all modals
- [ ] Event system communication working
- [ ] No JavaScript console errors

### Code Quality
- [ ] PopupsModule.js ~900 lines
- [ ] Clear method organization
- [ ] Consistent naming conventions
- [ ] Comprehensive error handling
- [ ] Console logging for debugging

### Testing Coverage
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Visual tests passing (Playwright)
- [ ] Accessibility tests passing
- [ ] Performance benchmarks met

### Documentation
- [ ] Module API documented
- [ ] Event contracts documented
- [ ] Usage examples provided
- [ ] Testing guide complete
- [ ] Phase 6 completion report created

---

## Implementation Steps

### Step 1: Extract Modal HTML Structure
- [ ] Review existing modal HTML in template
- [ ] Ensure all modals have consistent structure
- [ ] Add data attributes for module binding

### Step 2: Create PopupsModule.js Base
- [ ] Set up module skeleton
- [ ] Implement init() and cacheElements()
- [ ] Create modal open/close base methods
- [ ] Add modal stack management

### Step 3: Extract Configuration Modal
- [ ] Copy logic from redesigned.js
- [ ] Refactor to use AppEvents/AppState
- [ ] Implement form validation
- [ ] Connect API integration

### Step 4: Extract Entity Assignment Modal
- [ ] Copy entity tree logic
- [ ] Implement parent/child selection
- [ ] Add search/filter functionality
- [ ] Connect versioning system

### Step 5: Extract Field Information Modal
- [ ] Copy field info display logic
- [ ] Format calculation methodology
- [ ] Add related fields suggestions

### Step 6: Extract Import/Export Modals
- [ ] Move import logic from import.js
- [ ] Implement file upload handling
- [ ] Create export configuration UI
- [ ] Add progress indicators

### Step 7: Extract Confirmation Dialog
- [ ] Consolidate from ConfirmationDialog.js
- [ ] Create generic dialog method
- [ ] Add dialog type variants
- [ ] Implement promise-based pattern

### Step 8: Testing
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Run Playwright visual tests
- [ ] Performance profiling

### Step 9: Documentation
- [ ] Document module API
- [ ] Create usage examples
- [ ] Write testing guide
- [ ] Generate completion report

---

## Risk Assessment

### High Risk
- **Modal Interference**: Multiple modals open simultaneously
  - *Mitigation*: Implement modal stack with proper z-index management

- **Form Validation Complexity**: Different validation rules per modal
  - *Mitigation*: Create reusable validation utilities

### Medium Risk
- **Import File Size**: Large CSV files may cause performance issues
  - *Mitigation*: Implement chunked file reading, pagination in preview

- **Entity Tree Performance**: Large organization hierarchies
  - *Mitigation*: Virtual scrolling, lazy loading of sub-trees

### Low Risk
- **Browser Compatibility**: Modal API differences
  - *Mitigation*: Use polyfills, test across browsers

---

## Timeline

| Task | Duration | Status |
|------|----------|--------|
| Phase 6 setup | 1 hour | ✅ DONE |
| Extract configuration modal | 2 hours | ⏳ PENDING |
| Extract entity assignment modal | 2 hours | ⏳ PENDING |
| Extract field info modal | 1 hour | ⏳ PENDING |
| Extract import/export modals | 2 hours | ⏳ PENDING |
| Extract confirmation dialog | 1 hour | ⏳ PENDING |
| Testing (unit + integration) | 3 hours | ⏳ PENDING |
| Playwright visual testing | 2 hours | ⏳ PENDING |
| Documentation | 2 hours | ⏳ PENDING |
| **Total Estimated Time** | **16 hours** | |

---

## Dependencies

### Required Modules (Already Complete)
- ✅ main.js (Event system)
- ✅ ServicesModule.js (API calls)
- ✅ CoreUI.js (Toolbar events)
- ✅ VersioningModule.js (Assignment versioning)
- ✅ SelectDataPointsPanel.js (Data point selection)
- ✅ SelectedDataPointsPanel.js (Status updates)

### External Dependencies
- ✅ Flask backend APIs
- ✅ AppState global state
- ✅ AppEvents event system
- ✅ Playwright for testing

---

## Deliverables

1. **Code**:
   - [ ] PopupsModule.js (~900 lines)
   - [ ] Updated template with modal bindings
   - [ ] Test files

2. **Documentation**:
   - [ ] This requirements document
   - [ ] API documentation
   - [ ] Testing guide
   - [ ] Completion report

3. **Testing**:
   - [ ] Unit test suite
   - [ ] Integration test suite
   - [ ] Playwright test scripts
   - [ ] Test results report

---

## Next Phase Preview

**Phase 7: Extract Versioning Logic**

After completing Phase 6, we'll move to Phase 7 which focuses on:
- Extract VersioningModule.js (if not already complete)
- Assignment lifecycle management
- Version resolution logic
- FY-based validation
- Cache management

**Progress Target**: ~85% modularized

---

**Document Status**: ✅ COMPLETE
**Ready for Implementation**: YES
**Approval Required**: NO (Internal refactoring)

---

*Generated: September 30, 2025*
*Author: Claude Development Team*
*Phase: 6 of 10*