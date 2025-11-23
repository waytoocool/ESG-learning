# Phase 9.6: Integration & Performance Testing
## Requirements & Specifications

**Date**: 2025-10-01
**Phase**: 9.6 of 8 (Phase 9.0-9.8)
**Total Tests**: 18 tests (8 integration + 10 performance)
**Estimated Time**: 3-4 hours
**Priority**: HIGH (End-to-end validation)

---

## Overview

### Purpose

Phase 9.6 focuses on **integration and performance testing** of the NEW modular assign-data-points page. While previous phases validated individual features, this phase ensures:
1. **End-to-end workflows** work correctly across multiple modules
2. **Performance metrics** meet or exceed targets
3. **Cross-module communication** functions properly
4. **System remains responsive** under realistic usage conditions

### Context from Previous Phases

**Phase 9.0** (Rounds 1-6): ✅ Core functionality validated (20 tests)
**Phase 9.5**: ✅ Versioning, History, Import/Export validated (19 tests executed)
**Progress So Far**: 39 tests completed, 0 P0/P1 bugs remaining

---

## Test Environment

### Test URL
```
http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2
```

**IMPORTANT**: Use the NEW modular page (`-v2`), NOT the old page (`_redesigned`)

### Test Credentials
```
Company: test-company-alpha
Admin: alice@alpha.com / admin123
User: bob@alpha.com / user123
```

### Browser
- **Primary**: Chrome (latest stable)
- **Note**: Cross-browser testing in Phase 9.7

---

## Test Scope

### Part 1: Full Workflow Tests (8 tests)

**Focus**: End-to-end user journeys that span multiple modules

**Why This Matters**: Individual features may work, but integration bugs can break complete workflows. These tests ensure the entire system works together seamlessly.

---

#### Workflow Test 1: Complete Assignment Creation Flow

**Test ID**: T9.6-W1
**Priority**: P0 (Critical workflow)

**Workflow Steps**:
1. Select framework from dropdown (e.g., "GRI Standards")
2. Expand topic tree and select 3-5 data point fields
3. Click "Assign to Entities"
4. Select 2 entities from entity tree (e.g., "Alpha HQ", "Alpha Factory")
5. Click "Configure" for one selected field
6. Set frequency (Quarterly), unit (tons), FY dates
7. Click "Save All" to persist assignments
8. Verify success message displays
9. Refresh page and verify assignments persist

**Expected Results**:
- All steps complete without errors
- Selection counter updates correctly (step 2)
- Toolbar buttons enable/disable appropriately (steps 2, 3, 6)
- Configuration modal opens and saves (steps 5-6)
- Assignments saved to database (step 7)
- Data persists after page refresh (step 9)

**Success Criteria**: Complete workflow finishes in < 60 seconds, all data saved correctly

---

#### Workflow Test 2: CSV Import End-to-End

**Test ID**: T9.6-W2
**Priority**: P1 (Major feature)

**Workflow Steps**:
1. Click "Import" button
2. Upload valid CSV file with 10-20 assignment records
3. Review import preview modal
   - Verify record count matches CSV
   - Check for warnings/errors
4. Click "Confirm Import"
5. Wait for import progress indicator
6. Verify import success message
7. Check that imported assignments appear in selected items panel
8. Query database to confirm records saved

**Expected Results**:
- Import modal displays preview correctly
- Record count accurate (e.g., "20 records found")
- Progress indicator shows during import
- Success message: "Imported 20 assignments successfully"
- Assignments visible in UI
- Database contains all imported records

**Success Criteria**: Import 20 records in < 5 seconds, 100% data integrity

---

#### Workflow Test 3: Export-Modify-Reimport Cycle

**Test ID**: T9.6-W3
**Priority**: P1 (Data integrity)

**Workflow Steps**:
1. Export all current assignments to CSV
2. Open exported CSV file
3. Modify 2-3 records (change frequency, entity, or unit)
4. Save modified CSV
5. Re-import the modified CSV
6. Verify import preview shows changes
7. Confirm import
8. Verify changes reflected in UI
9. Check Assignment History shows update events

**Expected Results**:
- Export produces valid CSV with all assignments
- Modifications preserved in CSV
- Import detects changes (may show as updates or new versions)
- UI reflects updated data
- History timeline shows modification events

**Success Criteria**: Round-trip data integrity maintained, no data loss

---

#### Workflow Test 4: View History and Version Information

**Test ID**: T9.6-W4
**Priority**: P1 (History feature)

**Workflow Steps**:
1. Click info (i) button on a data point with history
2. Modal opens to Field Details tab
3. Click "Assignment History" tab
4. Verify timeline displays with version entries
5. Check version numbers display (Version 8, Version 7, etc.)
6. Check dates display correctly
7. Verify statistics accurate (Total, Active, Superseded counts)
8. Click on a history entry to view details
9. Verify change description shows what was modified

**Expected Results**:
- Modal opens smoothly (< 200ms)
- Assignment History tab loads (< 500ms)
- Timeline renders all history entries
- Version numbers, dates, statistics all correct
- Detail view shows change information

**Success Criteria**: History loads in < 1 second, all data accurate

**Note**: Version comparison and rollback deferred to future enhancements

---

#### Workflow Test 5: Cross-Module Selection Triggering

**Test ID**: T9.6-W5
**Priority**: P0 (Core interaction)

**Workflow Steps**:
1. Start with 0 selections (use "Deselect All" if needed)
2. Select 1 data point checkbox
3. **Verify**: Selection counter updates to "1 field selected"
4. **Verify**: Toolbar buttons update state:
   - "Assign to Entities" enabled
   - "Configure" enabled
   - "Save All" enabled
5. Select 2 more data points (total 3)
6. **Verify**: Counter updates to "3 fields selected"
7. Deselect 1 field (back to 2)
8. **Verify**: Counter updates to "2 fields selected"
9. Click "Deselect All"
10. **Verify**: Counter resets to "0 fields selected"
11. **Verify**: Toolbar buttons disable

**Expected Results**:
- Counter updates in real-time on every selection change
- Toolbar buttons enable when selections > 0
- Toolbar buttons disable when selections = 0
- AppState synchronized across modules

**Success Criteria**: UI updates in < 50ms per selection, no state desync

---

#### Workflow Test 6: Configuration Triggering Versioning

**Test ID**: T9.6-W6
**Priority**: P1 (Version management)

**Workflow Steps**:
1. Select an existing data point assignment (one that already has a version)
2. Click "Configure" button
3. Open configuration modal
4. Change a setting (e.g., Frequency from Quarterly → Monthly)
5. Save configuration
6. Open info (i) modal for that field
7. Go to Assignment History tab
8. **Verify**: New version created
9. **Verify**: Previous version status changed to SUPERSEDED
10. **Verify**: New version shows updated frequency

**Expected Results**:
- Configuration change triggers version creation
- Version number increments (e.g., Version 7 → Version 8)
- Old version marked SUPERSEDED
- New version marked ACTIVE
- History timeline shows both versions

**Success Criteria**: Versioning system captures all configuration changes

---

#### Workflow Test 7: State Synchronization Across Modules

**Test ID**: T9.6-W7
**Priority**: P0 (System integrity)

**Workflow Steps**:
1. Use browser DevTools console to inspect `window.AppState`
2. Select 3 data points via Selection Panel
3. **Verify**: `AppState.getSelectedDataPoints()` returns 3 items
4. Open Configuration modal (via Configure button)
5. **Verify**: PopupsModule shows selected items
6. Add entity assignment via entity modal
7. **Verify**: AppState updated with entity info
8. Click "Save All"
9. **Verify**: All modules receive `save-completed` event
10. **Verify**: State cleared/updated appropriately

**Expected Results**:
- AppState maintains single source of truth
- All modules read from AppState
- Event system propagates changes
- No stale state after operations

**Success Criteria**: Zero state desynchronization issues

---

#### Workflow Test 8: Error Recovery Flow

**Test ID**: T9.6-W8
**Priority**: P1 (Resilience)

**Workflow Steps**:
1. Open browser DevTools Network tab
2. Set network throttling to "Offline"
3. Select some data points
4. Click "Save All"
5. **Verify**: Error message displays (e.g., "Network error, please try again")
6. **Verify**: User can retry or cancel
7. Set network back to "Online"
8. Click "Retry" or "Save All" again
9. **Verify**: Save succeeds
10. **Verify**: Data saved correctly

**Expected Results**:
- System detects network failure gracefully
- User-friendly error message shown
- Retry mechanism available
- Operation succeeds after network restored
- No data loss or corruption

**Success Criteria**: Graceful error handling, successful recovery

---

### Part 2: Performance Tests (10 tests)

**Focus**: Load times, responsiveness, memory usage

**Why This Matters**: The NEW modular page must be as fast or faster than the OLD page. Performance regressions are unacceptable.

**Measurement Tools**:
- Browser DevTools Performance tab
- Network tab for load timing
- Memory profiler for leak detection
- Performance API (`performance.now()`, `performance.getEntriesByType()`)

---

#### Performance Test 1: Page Initial Load Time

**Test ID**: T9.6-P1
**Priority**: P0 (Critical metric)

**Target**: < 3 seconds (Ideal: < 2 seconds)

**Measurement**:
1. Open browser in incognito mode (clear cache)
2. Navigate to page: `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2`
3. Use DevTools Performance tab, record page load
4. Measure from navigation start to `DOMContentLoaded` event
5. Also measure to `load` event (all resources loaded)

**Metrics to Capture**:
- Time to DOMContentLoaded (HTML parsed, DOM ready)
- Time to Load (all CSS, JS, images loaded)
- Time to First Contentful Paint (FCP)
- Time to Largest Contentful Paint (LCP)

**Expected Results**:
- DOMContentLoaded: < 1 second
- Load: < 2 seconds
- FCP: < 1 second
- LCP: < 2.5 seconds

**Success Criteria**: Page fully usable in < 2 seconds

---

#### Performance Test 2: Module Loading Time

**Test ID**: T9.6-P2
**Priority**: P1

**Target**: < 100ms per module

**Measurement**:
1. Check browser console for module initialization logs
2. Logs show: `[ModuleName] Initialization complete`
3. Use `console.time` and `console.timeEnd` if needed
4. Measure time from script execution start to init complete

**Modules to Measure**:
- AppState
- AppEvents
- ServicesModule
- SelectionPanelModule
- SelectedItemsModule
- CoreUIModule
- PopupsModule
- ImportExportModule
- VersioningModule
- HistoryModule

**Expected Results**:
- Each module initializes in < 100ms
- Total initialization: < 500ms
- No module takes > 200ms

**Success Criteria**: All modules load quickly, no bottlenecks

---

#### Performance Test 3: JavaScript Parsing Time

**Test ID**: T9.6-P3
**Priority**: P1

**Target**: < 500ms total

**Measurement**:
1. DevTools Performance tab → Record page load
2. Look for "Evaluate Script" entries
3. Sum up all JavaScript parsing/compilation time
4. Check total bundle size and parse time

**Expected Results**:
- Total JS parse time: < 500ms
- No single file takes > 100ms to parse
- Bundle size reasonable (target: < 500KB total)

**Success Criteria**: JavaScript doesn't block page rendering

---

#### Performance Test 4: Search Response Time

**Test ID**: T9.6-P4
**Priority**: P1

**Target**: < 100ms for 500+ data points

**Measurement**:
1. Ensure framework with 500+ data points loaded
2. Type 3 characters in search box (e.g., "emi")
3. Measure time from keyup event to results displayed
4. Use `console.time` in search function if needed

**Expected Results**:
- Search results appear in < 100ms
- No perceptible lag
- Results accurate and highlighted
- Search handles 1000+ data points without slowdown

**Success Criteria**: Instant search feel, no lag

---

#### Performance Test 5: Selection Response Time

**Test ID**: T9.6-P5
**Priority**: P0

**Target**: < 50ms per selection

**Measurement**:
1. Click a data point checkbox
2. Measure time from click to UI updates (counter, selected panel)
3. Use `performance.mark` and `performance.measure`

**Expected Results**:
- Checkbox toggles instantly (< 20ms)
- Counter updates instantly (< 50ms)
- Selected panel updates instantly (< 50ms)
- No lag even with 50+ selections

**Success Criteria**: Snappy, responsive UI

---

#### Performance Test 6: Modal Open Time

**Test ID**: T9.6-P6
**Priority**: P1

**Target**: < 200ms

**Measurement**:
1. Click "Assign to Entities" button
2. Measure time from click to modal fully visible
3. Repeat for Configuration modal and Field Info modal

**Expected Results**:
- Modal opens in < 200ms
- Animation smooth (60fps)
- No jank or stutter

**Success Criteria**: Modals feel instant

---

#### Performance Test 7: Save Operation Time

**Test ID**: T9.6-P7
**Priority**: P0

**Target**: < 1 second for 10 assignments

**Measurement**:
1. Select 10 data point fields
2. Assign to 2 entities
3. Click "Save All"
4. Measure from click to success message displayed
5. Check network tab for API call duration

**Expected Results**:
- Save completes in < 1 second
- Success message displays promptly
- UI updates immediately

**Success Criteria**: Users don't perceive delay

---

#### Performance Test 8: Import 100 Rows Performance

**Test ID**: T9.6-P8
**Priority**: P1

**Target**: < 3 seconds

**Measurement**:
1. Prepare CSV file with 100 assignment records
2. Import via Import button
3. Measure from "Confirm Import" click to success message
4. Check console for timing logs

**Expected Results**:
- Import completes in < 3 seconds
- Progress indicator updates smoothly
- No browser freeze

**Success Criteria**: Import feels responsive, even for large datasets

---

#### Performance Test 9: Export 500 Rows Performance

**Test ID**: T9.6-P9
**Priority**: P1

**Target**: < 2 seconds

**Measurement**:
1. Ensure 500+ assignments exist (may need to import test data)
2. Click "Export" button
3. Measure from click to CSV download starts
4. Check file size and generation time

**Expected Results**:
- Export completes in < 2 seconds
- CSV file downloads immediately
- No browser freeze

**Success Criteria**: Export handles large datasets efficiently

---

#### Performance Test 10: Memory Usage & Leak Detection

**Test ID**: T9.6-P10
**Priority**: P1

**Target**: < 50MB initial, < 5MB growth after 100 operations

**Measurement**:
1. Open DevTools Memory tab
2. Take heap snapshot on page load (Snapshot 1)
3. Perform 100 operations:
   - Select 10 fields → Deselect all (repeat 10 times)
   - Open modal → Close modal (repeat 10 times)
   - Perform export (10 times)
4. Force garbage collection
5. Take another heap snapshot (Snapshot 2)
6. Compare memory usage

**Expected Results**:
- Initial memory: < 50MB
- After 100 operations: < 55MB (< 5MB growth)
- No memory leaks in detached DOM nodes
- Event listeners cleaned up properly

**Success Criteria**: No memory leaks, stable memory usage

---

## Success Criteria

### Phase 9.6 is **COMPLETE** when:

**Integration Tests** (8 tests):
- ✅ All 8 end-to-end workflows complete successfully
- ✅ Zero P0 bugs found
- ✅ Zero P1 bugs (or documented as acceptable)
- ✅ Cross-module communication functional
- ✅ Error recovery working

**Performance Tests** (10 tests):
- ✅ All 10 performance targets met or exceeded
- ✅ Page load < 2 seconds
- ✅ Operations responsive (< 100ms)
- ✅ No memory leaks detected
- ✅ Performance equal or better than OLD page

**Overall**:
- ✅ 18/18 tests passed (or 16/18 with documented acceptable failures)
- ✅ System performs well under realistic conditions
- ✅ Ready for browser compatibility testing (Phase 9.7)

---

## Bug Reporting

If bugs found during testing:

**Priority Definitions**:
- **P0 (Critical)**: Blocks core workflow, must fix before Phase 9.7
- **P1 (High)**: Major issue, fix before Phase 9 completion
- **P2 (Medium)**: Minor issue, can defer
- **P3 (Low)**: Cosmetic, backlog

**Bug Report Format**:
1. Test ID where bug found
2. Priority (P0/P1/P2/P3)
3. Steps to reproduce
4. Expected vs actual behavior
5. Screenshots/console logs
6. Impact assessment

---

## Deliverables

**Test Report**: `/ui-testing-agent/Phase_9.6_Test_Report_v1.md`

**Report Structure**:
1. Executive Summary (pass/fail status)
2. Integration Test Results (8 tests)
3. Performance Test Results (10 tests)
4. Performance Comparison (NEW vs OLD page, if data available)
5. Bug List (if any found)
6. Screenshots/Evidence
7. Recommendation (PROCEED / FIX BUGS / BLOCKED)

---

## Reference Documents

- Main spec: `/Phase-9-Comprehensive-Testing-Plan.md`
- Phase 9.5 completion: `/Phase-9.5-Versioning-History-Full-Testing-2025-09-30/PHASE_9.5_COMPLETION_REPORT.md`
- Phase 9.0 results: Previous round testing reports (Rounds 1-6)

---

**Status**: Ready for testing
**Next Phase After 9.6**: Phase 9.7 - Browser Compatibility & Accessibility (28 tests)
