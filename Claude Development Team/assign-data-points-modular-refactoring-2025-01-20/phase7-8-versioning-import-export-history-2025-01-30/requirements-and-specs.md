# Phase 7 & 8: Versioning, Import/Export, and History Implementation

**Project**: Assign Data Points Modular Refactoring
**Phase**: 7 & 8 Combined
**Date Started**: 2025-01-30
**Status**: In Progress

---

## Executive Summary

This document outlines the requirements and specifications for implementing Phase 7 (Versioning Module) and Phase 8 (Import/Export & History Modules) of the Assign Data Points modular refactoring project. These phases represent the final feature modules before legacy code removal, adding sophisticated versioning, bulk operations, and historical tracking capabilities.

---

## Phase 7: Versioning Module

### Objectives

1. Extract all assignment versioning logic into a dedicated `VersioningModule.js`
2. Implement data series management with version tracking
3. Provide assignment resolution based on fiscal year and date
4. Enable version lifecycle management (active, superseded, draft)
5. Integrate versioning with existing modules through event system

### Key Concepts

#### Version Terminology
- **data_series_id**: UUID identifying a unique assignment series (same field-entity combination)
- **series_version**: Incremental version number within a series (1, 2, 3...)
- **series_status**: Status of version (`active`, `superseded`, `draft`)
- **Assignment Resolution**: Logic to find the correct version for a given date
- **FY Integration**: Fiscal year-based version validation and constraints

#### Version Lifecycle
```
Draft Version → Active Version → Superseded Version
     ↓               ↓                    ↓
  Editing        In Use              Historical
```

### Functional Requirements

#### FR7.1: Version Creation
- **ID**: FR7.1
- **Description**: System shall create new assignment versions with proper series tracking
- **Acceptance Criteria**:
  - New assignments automatically create version 1 with new data_series_id
  - Modifications to existing assignments create new versions with incremented series_version
  - Previous active version automatically marked as superseded
  - Version metadata includes: created_by, created_at, fiscal_year
- **Priority**: High

#### FR7.2: Assignment Resolution
- **ID**: FR7.2
- **Description**: System shall resolve the appropriate assignment version for a given date
- **Acceptance Criteria**:
  - Given field_id, entity_id, and date, return active version
  - Apply fiscal year constraints to resolution
  - Handle overlapping assignment scenarios
  - Cache resolution results for performance
  - Return null if no valid assignment exists for date
- **Priority**: High

#### FR7.3: Version Status Management
- **ID**: FR7.3
- **Description**: System shall manage version status transitions
- **Acceptance Criteria**:
  - Support status transitions: draft → active, active → superseded
  - Prevent invalid transitions (e.g., superseded → active)
  - Update related versions when status changes
  - Emit events on status changes
  - Validate only one active version per series at a time
- **Priority**: High

#### FR7.4: FY Validation
- **ID**: FR7.4
- **Description**: System shall validate assignments against fiscal year configuration
- **Acceptance Criteria**:
  - Check assignment dates against company fiscal year
  - Warn when data entry attempts occur outside FY range
  - Support FY-based version filtering
  - Handle FY rollovers correctly
- **Priority**: Medium

#### FR7.5: Version Conflict Detection
- **ID**: FR7.5
- **Description**: System shall detect and handle version conflicts
- **Acceptance Criteria**:
  - Identify overlapping date ranges for same field-entity
  - Provide conflict resolution UI
  - Allow force supersede with confirmation
  - Log conflict resolutions for audit
- **Priority**: Medium

### Technical Specifications

#### Module Structure
```javascript
// VersioningModule.js (~600 lines)
window.VersioningModule = {
    // Initialization
    init() { },

    // Version Creation
    createAssignmentVersion(assignmentData) { },
    supersedePreviousVersion(seriesId, currentVersion) { },

    // Resolution
    resolveActiveAssignment(fieldId, entityId, date) { },
    getVersionForDate(seriesId, date) { },

    // Status Management
    updateVersionStatus(versionId, newStatus) { },
    validateVersionTransition(currentStatus, newStatus) { },

    // FY Integration
    checkFYCompatibility(assignmentData) { },
    validateDateInFY(date, fiscalYear) { },

    // Conflict Handling
    detectVersionConflicts(assignmentData) { },
    handleVersionConflict(conflictData) { },

    // Cache Management
    cacheResolution(key, value) { },
    invalidateCache(seriesId) { },

    // Utilities
    generateSeriesId() { },
    getNextVersionNumber(seriesId) { }
};
```

#### API Endpoints Used
```
POST   /admin/api/assignments/version/create
PUT    /admin/api/assignments/version/{id}/supersede
POST   /admin/api/assignments/resolve
GET    /admin/api/assignments/series/{seriesId}/versions
PUT    /admin/api/assignments/version/{id}/status
```

#### Events Emitted
```javascript
'version-created'         // New version created
'version-superseded'      // Version marked as superseded
'version-activated'       // Version activated
'resolution-changed'      // Resolution result changed
'version-conflict'        // Conflict detected
'fy-validation-warning'   // FY validation issue
```

#### Events Listened
```javascript
'assignment-saved'        // To create new version
'assignment-deleted'      // To supersede version
'fy-config-changed'       // To revalidate versions
'state-configuration-changed'  // To trigger version update
```

### Non-Functional Requirements

#### NFR7.1: Performance
- Version resolution must complete in < 100ms
- Cache hit rate should be > 90%
- Support up to 10,000 versions per company

#### NFR7.2: Data Integrity
- No orphaned versions
- Series consistency maintained
- Atomic version transitions

#### NFR7.3: Auditability
- All version changes logged
- Creator and timestamp tracked
- Conflict resolutions recorded

---

## Phase 8: Import/Export & History Modules

### Objectives

1. Extract import/export functionality into `ImportExportModule.js`
2. Extract history visualization into `HistoryModule.js`
3. Consolidate functionality from `assign_data_points_import.js`
4. Consolidate functionality from `assignment_history.js`
5. Provide comprehensive bulk operations and historical tracking

### Module 1: ImportExportModule.js

#### Objectives
- Consolidate all import/export functionality
- Support CSV/Excel file formats
- Provide validation and error reporting
- Enable template downloads

#### Functional Requirements

##### FR8.1: CSV Import
- **ID**: FR8.1
- **Description**: System shall support importing assignments from CSV files
- **Acceptance Criteria**:
  - Parse CSV files with standard format
  - Validate all rows before import
  - Show preview with validation results
  - Support bulk creation of assignments
  - Provide detailed error reporting
  - Allow partial imports (skip errors)
- **Priority**: High

##### FR8.2: Import Validation
- **ID**: FR8.2
- **Description**: System shall validate import data comprehensively
- **Acceptance Criteria**:
  - Validate field existence
  - Validate entity existence
  - Validate configuration data types
  - Check for duplicate entries
  - Validate fiscal year compatibility
  - Highlight invalid rows in preview
- **Priority**: High

##### FR8.3: Export Functionality
- **ID**: FR8.3
- **Description**: System shall export assignments to CSV format
- **Acceptance Criteria**:
  - Export all assignments or filtered subset
  - Include all configuration details
  - Support entity hierarchy in export
  - Generate valid CSV format
  - Provide filename with timestamp
- **Priority**: High

##### FR8.4: Template Download
- **ID**: FR8.4
- **Description**: System shall provide downloadable import templates
- **Acceptance Criteria**:
  - Template includes all required columns
  - Sample data included for reference
  - Instructions in header comments
  - Current framework fields included
- **Priority**: Medium

#### Technical Specifications

##### Module Structure
```javascript
// ImportExportModule.js (~500 lines)
window.ImportExportModule = {
    // Initialization
    init() { },

    // Import
    handleImportFile(file) { },
    parseCSVFile(file) { },
    validateImportData(rows) { },
    processImportRows(validRows) { },
    showImportPreview(data, errors) { },

    // Export
    generateExportCSV(assignments) { },
    downloadCSV(csvContent, filename) { },
    filterAssignmentsForExport() { },

    // Template
    downloadAssignmentTemplate() { },
    generateTemplateCSV() { },

    // Utilities
    parseCSVLine(line) { },
    formatCSVValue(value) { },
    validateRow(row, rowIndex) { }
};
```

##### CSV Format Specification
```csv
Field ID,Field Name,Entity ID,Entity Name,Frequency,Start Date,End Date,Required,Unit Override,Notes
GRI-302-1,Energy Consumption,1,Headquarters,Monthly,2024-01-01,2024-12-31,true,kWh,Main facility tracking
```

##### API Endpoints
```
POST   /admin/api/assignments/import
GET    /admin/api/assignments/export
GET    /admin/api/assignments/template
POST   /admin/api/assignments/validate-import
```

##### Events
```javascript
// Emitted
'import-completed'           // Import finished
'export-generated'          // Export ready
'import-validation-error'   // Validation failed
'import-preview-ready'      // Preview data ready

// Listened
'toolbar-import-clicked'    // Import button clicked
'toolbar-export-clicked'    // Export button clicked
```

### Module 2: HistoryModule.js

#### Objectives
- Consolidate history visualization from `assignment_history.js`
- Provide timeline view of assignment changes
- Enable version comparison
- Support historical filtering and search

#### Functional Requirements

##### FR8.5: History Timeline
- **ID**: FR8.5
- **Description**: System shall display assignment history in timeline format
- **Acceptance Criteria**:
  - Chronological display of all versions
  - Visual indicators for version types (created, updated, deleted)
  - User attribution for each change
  - Date/time stamps
  - Clickable timeline items for details
- **Priority**: High

##### FR8.6: History Filtering
- **ID**: FR8.6
- **Description**: System shall support filtering historical data
- **Acceptance Criteria**:
  - Filter by date range
  - Filter by user
  - Filter by entity
  - Filter by framework
  - Filter by change type
  - Multiple filters combinable
- **Priority**: Medium

##### FR8.7: Version Comparison
- **ID**: FR8.7
- **Description**: System shall allow comparing two versions
- **Acceptance Criteria**:
  - Select any two versions to compare
  - Highlight differences (added, removed, changed)
  - Side-by-side or unified diff view
  - Export comparison results
- **Priority**: Medium

##### FR8.8: Version Restoration
- **ID**: FR8.8
- **Description**: System shall allow restoring previous versions
- **Acceptance Criteria**:
  - View any historical version
  - Option to restore as new version
  - Confirmation before restoration
  - Audit log of restoration
- **Priority**: Low

#### Technical Specifications

##### Module Structure
```javascript
// HistoryModule.js (~500 lines)
window.HistoryModule = {
    // Initialization
    init() { },

    // Timeline
    loadAssignmentHistory(filters) { },
    renderHistoryTimeline(historyData) { },
    createTimelineItem(versionData) { },

    // Filtering
    filterHistoryByDate(startDate, endDate) { },
    filterHistoryByUser(userId) { },
    filterHistoryByEntity(entityId) { },
    applyMultipleFilters(filterObj) { },

    // Comparison
    compareVersions(version1Id, version2Id) { },
    displayVersionDiff(diffData) { },
    highlightChanges(oldValue, newValue) { },

    // Details
    showHistoryDetails(versionId) { },
    loadVersionData(versionId) { },

    // Search
    searchHistory(query) { },

    // Utilities
    formatTimestamp(timestamp) { },
    getChangeIcon(changeType) { }
};
```

##### API Endpoints
```
GET    /admin/api/assignments/history
GET    /admin/api/assignments/history/{assignmentId}
GET    /admin/api/assignments/version/{id}
POST   /admin/api/assignments/version/{id}/restore
GET    /admin/api/assignments/compare/{v1}/{v2}
```

##### Events
```javascript
// Emitted
'history-filter-changed'    // Filter updated
'version-selected'          // Version clicked
'history-loaded'            // History data loaded
'comparison-requested'      // Compare initiated

// Listened
'version-created'           // From VersioningModule
'version-superseded'        // From VersioningModule
'assignment-deleted'        // From any module
```

### Non-Functional Requirements

#### NFR8.1: Performance
- Import processing: < 5 seconds for 1000 rows
- Export generation: < 3 seconds for all data
- History timeline load: < 2 seconds

#### NFR8.2: Usability
- Clear error messages during import
- Progress indicators for bulk operations
- Intuitive timeline navigation
- Responsive diff visualization

#### NFR8.3: Data Integrity
- Import transactions atomic
- No partial imports on failure
- Export data matches database
- Version comparison accurate

---

## Integration Requirements

### Module Dependencies
```
Phase 7 & 8 Module Dependencies:

VersioningModule.js
    ↓ depends on
    ServicesModule.js (API calls)
    AppState (state management)
    AppEvents (event system)

ImportExportModule.js
    ↓ depends on
    ServicesModule.js (API calls)
    VersioningModule.js (version creation)
    PopupsModule.js (modal display)
    AppEvents (event system)

HistoryModule.js
    ↓ depends on
    ServicesModule.js (API calls)
    VersioningModule.js (version data)
    AppEvents (event system)
```

### Event Flow Integration
```
User imports CSV
    ↓
ImportExportModule.handleImportFile()
    ↓
ImportExportModule.validateImportData()
    ↓ (emit) 'import-preview-ready'
    ↓
User confirms import
    ↓
ImportExportModule.processImportRows()
    ↓ (for each row)
    ↓
VersioningModule.createAssignmentVersion()
    ↓ (emit) 'version-created'
    ↓
HistoryModule (listens) → updates timeline
    ↓ (emit) 'import-completed'
    ↓
Show success message
```

### Template Integration

#### Script Loading Order (Updated)
```html
<!-- Phase 1-6 modules -->
<script src="{{ url_for('static', filename='js/admin/assign_data_points/main.js') }}"></script>
<script src="{{ url_for('static', filename='js/admin/assign_data_points/ServicesModule.js') }}"></script>
<script src="{{ url_for('static', filename='js/admin/assign_data_points/CoreUI.js') }}"></script>
<script src="{{ url_for('static', filename='js/admin/assign_data_points/SelectDataPointsPanel.js') }}"></script>
<script src="{{ url_for('static', filename='js/admin/assign_data_points/SelectedDataPointsPanel.js') }}"></script>
<script src="{{ url_for('static', filename='js/admin/assign_data_points/PopupsModule.js') }}"></script>

<!-- Phase 7 & 8 modules -->
<script src="{{ url_for('static', filename='js/admin/assign_data_points/VersioningModule.js') }}"></script>
<script src="{{ url_for('static', filename='js/admin/assign_data_points/ImportExportModule.js') }}"></script>
<script src="{{ url_for('static', filename='js/admin/assign_data_points/HistoryModule.js') }}"></script>

<!-- Initialize all modules -->
<script>
    document.addEventListener('DOMContentLoaded', () => {
        // Phase 7 & 8 initialization
        VersioningModule.init();
        ImportExportModule.init();
        HistoryModule.init();
    });
</script>
```

---

## Testing Requirements

### Phase 7 Testing

#### Test Suite 7.1: Version Creation
- [ ] Create new assignment → version 1 created
- [ ] Modify assignment → version 2 created, version 1 superseded
- [ ] Concurrent modifications → proper version sequencing
- [ ] Series ID consistency maintained
- [ ] Version metadata populated correctly

#### Test Suite 7.2: Assignment Resolution
- [ ] Resolve assignment for current date → returns active version
- [ ] Resolve for historical date → returns appropriate version
- [ ] Resolve with no active version → returns null
- [ ] FY-based resolution → respects fiscal year boundaries
- [ ] Cache performance → subsequent calls faster

#### Test Suite 7.3: Version Status
- [ ] Status indicators display correctly
- [ ] Active/superseded/draft states accurate
- [ ] Status transitions validated
- [ ] Only one active version per series
- [ ] Status changes emit events

#### Test Suite 7.4: Conflict Handling
- [ ] Overlapping assignments detected
- [ ] Conflict warning displayed
- [ ] Force supersede option works
- [ ] Conflict resolution logged

### Phase 8 Testing

#### Test Suite 8.1: CSV Import
- [ ] Valid CSV imports successfully
- [ ] Invalid rows highlighted
- [ ] Preview shows correct data
- [ ] Partial import works
- [ ] Error report downloadable
- [ ] Large files (1000+ rows) handled

#### Test Suite 8.2: Import Validation
- [ ] Invalid field ID rejected
- [ ] Invalid entity ID rejected
- [ ] Invalid date format rejected
- [ ] Duplicate entries detected
- [ ] Required fields validated
- [ ] Data types validated

#### Test Suite 8.3: Export
- [ ] Full export generates correctly
- [ ] Filtered export works
- [ ] CSV format valid
- [ ] All data included
- [ ] Filename has timestamp
- [ ] Download triggers properly

#### Test Suite 8.4: History Timeline
- [ ] Timeline displays chronologically
- [ ] All versions shown
- [ ] User attribution correct
- [ ] Timestamps accurate
- [ ] Timeline interactive
- [ ] Details load on click

#### Test Suite 8.5: History Filtering
- [ ] Date range filter works
- [ ] User filter works
- [ ] Entity filter works
- [ ] Multiple filters combine correctly
- [ ] Clear filters restores all data

#### Test Suite 8.6: Version Comparison
- [ ] Select two versions
- [ ] Diff highlights changes
- [ ] Added/removed/changed identified
- [ ] Side-by-side view works
- [ ] Export comparison works

### UI Testing with Playwright MCP

All testing will be conducted using the Playwright MCP visual testing approach:

```bash
# Start MCP server
npm run mcp:start

# Run UI testing agent for Phase 7 & 8
# Agent will test all UI components, interactions, and visual regressions
```

#### Visual Test Scenarios
1. **Version indicators** in data point list
2. **Import modal** with preview and validation
3. **Export dialog** with filter options
4. **History timeline** visualization
5. **Version comparison** diff view
6. **Conflict warnings** and resolution UI
7. **FY validation** messages
8. **Progress indicators** during bulk operations

---

## Success Criteria

### Phase 7 Success Criteria
- [ ] VersioningModule.js created and functional (~600 lines)
- [ ] All versioning logic extracted from legacy code
- [ ] Version creation/resolution working correctly
- [ ] FY validation integrated
- [ ] Conflict detection operational
- [ ] All Phase 7 tests passing
- [ ] No console errors
- [ ] Performance metrics met

### Phase 8 Success Criteria
- [ ] ImportExportModule.js created and functional (~500 lines)
- [ ] HistoryModule.js created and functional (~500 lines)
- [ ] Import functionality consolidated
- [ ] Export functionality working
- [ ] History timeline displaying correctly
- [ ] Version comparison operational
- [ ] All Phase 8 tests passing
- [ ] No console errors
- [ ] Performance metrics met

### Combined Success Criteria
- [ ] All modules integrated successfully
- [ ] Event communication working across modules
- [ ] No functionality regressions
- [ ] Documentation complete
- [ ] UI testing agent validation passed
- [ ] Ready for Phase 9 (legacy code removal)

---

## Risk Assessment

### High Risk Items
1. **Version Resolution Complexity**: Complex logic with date ranges and FY constraints
   - **Mitigation**: Extensive unit testing, cache validation

2. **Import Data Validation**: Many validation rules, potential for missed edge cases
   - **Mitigation**: Comprehensive validation suite, user feedback

3. **History Performance**: Large datasets could slow timeline rendering
   - **Mitigation**: Pagination, lazy loading, efficient queries

### Medium Risk Items
1. **Cache Invalidation**: Stale resolution cache could cause incorrect versions
   - **Mitigation**: Clear cache strategy, event-driven invalidation

2. **CSV Parsing**: Various file encodings and formats
   - **Mitigation**: Robust parsing library, format validation

3. **Version Conflicts**: Complex conflict scenarios
   - **Mitigation**: Clear UI feedback, audit logging

---

## Timeline

### Phase 7: Versioning Module
- **Day 1**: Create VersioningModule.js structure and core functions
- **Day 2**: Implement resolution logic and FY validation
- **Day 3**: Integration and testing

### Phase 8: Import/Export & History
- **Day 4**: Create ImportExportModule.js with import functionality
- **Day 5**: Add export and template generation
- **Day 6**: Create HistoryModule.js with timeline
- **Day 7**: Add filtering and comparison features
- **Day 8**: Integration and comprehensive testing

### Total Estimated Time: 8 days

---

## Next Steps

1. ✅ Create documentation structure
2. ⏳ Create VersioningModule.js
3. ⏳ Integrate and test Phase 7
4. ⏳ Create ImportExportModule.js
5. ⏳ Create HistoryModule.js
6. ⏳ Integrate and test Phase 8
7. ⏳ Run comprehensive UI testing with Playwright MCP
8. ⏳ Document results and prepare for Phase 9

---

## References

- Main Requirements: `Main Requirement & Specs-ASSIGN_DATA_POINTS_MODULAR_REFACTORING_PLAN.md`
- Existing Versioning Service: `app/services/assignment_versioning.py`
- Legacy Import Code: `app/static/js/admin/assign_data_points_import.js`
- Legacy History Code: `app/static/js/admin/assignment_history.js`
- Testing Guide: UI Testing with Playwright MCP (documented in main plan)

---

**Document Version**: 1.0
**Last Updated**: 2025-01-30
**Author**: Claude Development Team
**Status**: Ready for Implementation