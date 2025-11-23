# Phase 9.1: Foundation & Services Validation - Requirements & Specs

**Date**: 2025-09-30
**Status**: Ready for Testing
**Total Tests**: 24 tests
**Estimated Time**: 2-3 hours
**Priority**: HIGH (Foundation layer)

---

## Context & Background

### Purpose
Phase 9.1 validates the foundational layer of the modular refactoring - the event system, state management, and services layer. These are critical infrastructure components that all other modules depend on.

### Scope
This phase combines two critical testing areas:
- **Phase 1**: Foundation Tests (12 tests) - Event system, state management, initialization
- **Phase 2**: Services Layer Tests (12 tests) - API calls, framework loading, error handling

### Why This Phase is Critical
- Foundation layer must be rock-solid for all other features to work
- Event system is the communication backbone between modules
- State management ensures data consistency across the application
- Services layer handles all backend communication
- Bugs here cascade to all other modules

### Previous Testing (Phase 9.0)
In Round 1-6 testing, we validated:
- ✅ Page load (no errors)
- ✅ Global objects verification (AppEvents, AppState exist)
- ✅ Initial data load (frameworks, entities)
- ✅ Basic event system functionality

**Still Untested (91% of foundation layer)**:
- ❌ Event registration/emission/cleanup
- ❌ State management operations
- ❌ API error handling
- ❌ Service layer robustness

---

## Test Environment

### Test Pages
- **NEW Page (Under Test)**: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points
- **OLD Page (Baseline)**: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-redesigned

### Test Credentials
```
Company: test-company-alpha
Admin User: alice@alpha.com / admin123
```

### Prerequisites
1. Flask application running on http://127-0-0-1.nip.io:8000/
2. MCP server running (`npm run mcp:start`)
3. Test data seeded (frameworks, entities, users)
4. Browser: Chrome (latest stable)

---

## Phase 1: Foundation Tests (12 Tests)

### Focus Areas
- Event system functionality (AppEvents)
- State management (AppState)
- Module initialization
- Data persistence

### Test Cases

#### T1.1: Page Load Validation ✅ (DONE in Round 6)
**Status**: COMPLETE
**Objective**: Verify page loads without errors
**Steps**:
1. Navigate to NEW page
2. Check console for errors
3. Verify no network failures

**Expected Results**:
- Page loads successfully
- No JavaScript errors
- HTTP 200 responses

---

#### T1.2: Global Objects Verification ✅ (DONE in Round 6)
**Status**: COMPLETE
**Objective**: Verify AppEvents and AppState are initialized
**Steps**:
1. Open browser console
2. Check `window.AppEvents`
3. Check `window.AppState`

**Expected Results**:
- `AppEvents` exists and has methods: `on()`, `emit()`, `off()`
- `AppState` exists and has state properties

---

#### T1.3: Initial Data Load ✅ (DONE in Round 6)
**Status**: COMPLETE
**Objective**: Verify frameworks and entities load on page init
**Steps**:
1. Load NEW page
2. Check framework dropdown populated
3. Verify entities load

**Expected Results**:
- Framework dropdown shows all frameworks
- Entities available for assignment

---

#### T1.4: Event System Functionality ✅ (DONE in Round 6)
**Status**: COMPLETE (Basic validation only)
**Objective**: Verify event system works for basic operations
**Steps**:
1. Select a framework
2. Check console for event logs
3. Verify event propagation

**Expected Results**:
- Events logged in console
- No event propagation errors

---

#### T1.5: AppEvents.on() Registration
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify event listeners register correctly

**Test Steps**:
1. Open NEW page
2. Open browser console
3. Execute test code:
```javascript
// Test event registration
let testEventFired = false;
AppEvents.on('test:event', () => {
  testEventFired = true;
  console.log('✅ Test event received');
});

// Trigger event
AppEvents.emit('test:event');

// Check result
console.log('Event fired:', testEventFired);
```

**Expected Results**:
- ✅ Event listener registers without error
- ✅ Event fires when emitted
- ✅ Callback executes
- ✅ Console shows "✅ Test event received"
- ✅ `testEventFired` is `true`

**Failure Indicators**:
- ❌ Error: "AppEvents.on is not a function"
- ❌ Event doesn't fire
- ❌ Callback doesn't execute
- ❌ `testEventFired` remains `false`

---

#### T1.6: AppEvents.emit() Propagation
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify events propagate to multiple listeners

**Test Steps**:
1. Open NEW page
2. Execute test code:
```javascript
// Register multiple listeners
let listener1Fired = false;
let listener2Fired = false;
let listener3Fired = false;

AppEvents.on('test:multi', () => { listener1Fired = true; });
AppEvents.on('test:multi', () => { listener2Fired = true; });
AppEvents.on('test:multi', () => { listener3Fired = true; });

// Emit event
AppEvents.emit('test:multi');

// Check all fired
console.log('Listener 1:', listener1Fired);
console.log('Listener 2:', listener2Fired);
console.log('Listener 3:', listener3Fired);
```

**Expected Results**:
- ✅ All three listeners fire
- ✅ All flags set to `true`
- ✅ No errors in console

**Failure Indicators**:
- ❌ Only first listener fires
- ❌ Listeners fire out of order
- ❌ Some listeners skipped

---

#### T1.7: AppEvents.off() Cleanup
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify event listeners can be removed

**Test Steps**:
1. Open NEW page
2. Execute test code:
```javascript
// Create listener function
let callCount = 0;
function testListener() {
  callCount++;
  console.log('Listener called, count:', callCount);
}

// Register
AppEvents.on('test:cleanup', testListener);

// Emit once
AppEvents.emit('test:cleanup');
console.log('After first emit:', callCount); // Should be 1

// Remove listener
AppEvents.off('test:cleanup', testListener);

// Emit again
AppEvents.emit('test:cleanup');
console.log('After second emit:', callCount); // Should still be 1
```

**Expected Results**:
- ✅ Listener fires before removal (count = 1)
- ✅ Listener removed successfully
- ✅ Listener does NOT fire after removal (count stays 1)
- ✅ No errors

**Failure Indicators**:
- ❌ Listener still fires after `off()` call
- ❌ Error: "AppEvents.off is not a function"
- ❌ Count increments to 2

---

#### T1.8: AppState.addSelectedDataPoint() Validation
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify state correctly adds selected data points

**Test Steps**:
1. Open NEW page
2. Execute test code:
```javascript
// Check initial state
console.log('Initial selected count:', AppState.selectedDataPoints.size);

// Add a test data point
AppState.addSelectedDataPoint({
  field_id: 'test-field-1',
  field_name: 'Test Field 1',
  topic_name: 'Test Topic'
});

// Check state updated
console.log('After add count:', AppState.selectedDataPoints.size);
console.log('Data point exists:', AppState.selectedDataPoints.has('test-field-1'));
```

**Expected Results**:
- ✅ Size increments by 1
- ✅ Data point stored in Map
- ✅ Data point retrievable by field_id
- ✅ No duplicates if added twice

**Failure Indicators**:
- ❌ Size doesn't increment
- ❌ Data point not found
- ❌ Duplicate entries created

---

#### T1.9: AppState.removeSelectedDataPoint() Validation
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify state correctly removes data points

**Test Steps**:
1. Open NEW page
2. Add then remove a data point:
```javascript
// Add
AppState.addSelectedDataPoint({
  field_id: 'test-remove-1',
  field_name: 'Test Remove',
  topic_name: 'Test'
});
console.log('After add:', AppState.selectedDataPoints.size);

// Remove
AppState.removeSelectedDataPoint('test-remove-1');
console.log('After remove:', AppState.selectedDataPoints.size);
console.log('Still exists?:', AppState.selectedDataPoints.has('test-remove-1'));
```

**Expected Results**:
- ✅ Size decrements by 1
- ✅ Data point removed from Map
- ✅ `has()` returns false after removal

**Failure Indicators**:
- ❌ Size doesn't decrement
- ❌ Data point still exists
- ❌ Error thrown

---

#### T1.10: AppState.setConfiguration() Validation
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify configuration state updates

**Test Steps**:
1. Open NEW page
2. Set configuration:
```javascript
// Set config for a field
AppState.setConfiguration('test-field-config', {
  fiscal_year_start: '2024-01',
  frequency: 'Annual',
  unit: 'tonnes'
});

// Retrieve config
const config = AppState.getConfiguration('test-field-config');
console.log('Retrieved config:', config);
```

**Expected Results**:
- ✅ Configuration stored
- ✅ Configuration retrievable
- ✅ All properties preserved

**Failure Indicators**:
- ❌ Configuration not stored
- ❌ Properties missing or corrupted
- ❌ Error thrown

---

#### T1.11: Map-Based State Management
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify state uses Map for efficient lookups

**Test Steps**:
1. Open NEW page
2. Check data structure:
```javascript
// Check type
console.log('Selected data points is Map:', AppState.selectedDataPoints instanceof Map);
console.log('Configuration is Map:', AppState.configurations instanceof Map);

// Test Map methods
AppState.selectedDataPoints.forEach((value, key) => {
  console.log('Key:', key, 'Value:', value);
});
```

**Expected Results**:
- ✅ `selectedDataPoints` is a Map
- ✅ `configurations` is a Map
- ✅ Map methods work (forEach, has, get, set)

**Failure Indicators**:
- ❌ Using plain objects instead of Map
- ❌ Map methods not available
- ❌ Poor performance with large datasets

---

#### T1.12: State Persistence Across Operations
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify state persists during complex operations

**Test Steps**:
1. Open NEW page
2. Perform sequence:
```javascript
// Add 3 data points
for (let i = 1; i <= 3; i++) {
  AppState.addSelectedDataPoint({
    field_id: `persist-test-${i}`,
    field_name: `Persist Test ${i}`,
    topic_name: 'Persist Topic'
  });
}

// Emit some events (simulate other operations)
AppEvents.emit('selection:changed');
AppEvents.emit('toolbar:update');

// Check state still intact
console.log('Count after events:', AppState.selectedDataPoints.size);
console.log('All 3 exist:',
  AppState.selectedDataPoints.has('persist-test-1') &&
  AppState.selectedDataPoints.has('persist-test-2') &&
  AppState.selectedDataPoints.has('persist-test-3')
);
```

**Expected Results**:
- ✅ State persists across events
- ✅ Count remains 3
- ✅ All data points retrievable
- ✅ No data loss

**Failure Indicators**:
- ❌ State resets or clears
- ❌ Data points lost
- ❌ Count changes unexpectedly

---

## Phase 2: Services Layer Tests (12 Tests)

### Focus Areas
- API call infrastructure
- Framework data loading
- Error handling and retries
- Loading states

### Test Cases

#### T2.1: ServicesModule.apiCall() Basic Functionality
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify API wrapper works for basic calls

**Test Steps**:
1. Open NEW page
2. Execute test API call:
```javascript
// Test API call
ServicesModule.apiCall('/admin/frameworks', 'GET')
  .then(response => {
    console.log('✅ API call successful:', response);
    console.log('Frameworks count:', response.length);
  })
  .catch(error => {
    console.error('❌ API call failed:', error);
  });
```

**Expected Results**:
- ✅ Promise resolves successfully
- ✅ Response contains framework data
- ✅ No errors thrown

**Failure Indicators**:
- ❌ Promise rejects
- ❌ Error: "ServicesModule is not defined"
- ❌ Network error

---

#### T2.2: ServicesModule.loadFrameworkFields() Validation
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify framework fields load correctly

**Test Steps**:
1. Open NEW page
2. Select a framework from dropdown
3. Check console logs:
```javascript
// Should see logs like:
// "Loading fields for framework: GRI"
// "Loaded X fields"
```
4. Verify fields render in selection panel

**Expected Results**:
- ✅ Fields load when framework selected
- ✅ Field count matches database
- ✅ Fields render with topics
- ✅ Loading indicator shows during fetch

**Failure Indicators**:
- ❌ No fields load
- ❌ Error in console
- ❌ Infinite loading state

---

#### T2.3: ServicesModule.loadExistingDataPointsWithInactive() Validation
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify existing assignments load (including inactive)

**Test Steps**:
1. Open NEW page with existing assignments
2. Check console for load message
3. Verify existing assignments show in "Selected Items" panel

**Expected Results**:
- ✅ Existing assignments load on init
- ✅ Active assignments visible
- ✅ Inactive assignments hidden by default (toggle to show)
- ✅ Assignment metadata present (entities, FY, etc.)

**Failure Indicators**:
- ❌ No existing assignments load
- ❌ Inactive assignments always shown
- ❌ Metadata missing

---

#### T2.4: API Error Handling (Network Failures)
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify graceful handling of network errors

**Test Steps**:
1. Open NEW page
2. Simulate network error:
   - Open DevTools → Network tab
   - Set throttling to "Offline"
   - Try to select a framework
3. Check error handling

**Expected Results**:
- ✅ Error message displayed to user
- ✅ No console errors breaking the page
- ✅ User can retry operation
- ✅ Page remains functional

**Failure Indicators**:
- ❌ Page crashes or freezes
- ❌ No error message shown
- ❌ Unhandled promise rejection

---

#### T2.5: API Timeout Handling
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify handling of slow/timeout requests

**Test Steps**:
1. Open NEW page
2. Simulate slow network:
   - DevTools → Network → Throttling: "Slow 3G"
3. Try to load a large framework (e.g., GRI with 100+ fields)
4. Check timeout handling

**Expected Results**:
- ✅ Request eventually completes or times out gracefully
- ✅ Loading indicator shows progress
- ✅ User can cancel slow request
- ✅ Timeout message if exceeds threshold

**Failure Indicators**:
- ❌ Request hangs indefinitely
- ❌ No timeout mechanism
- ❌ Page becomes unresponsive

---

#### T2.6: Framework List Loading
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify framework dropdown populates correctly

**Test Steps**:
1. Open NEW page
2. Check framework dropdown
3. Verify all frameworks present

**Expected Results**:
- ✅ Dropdown shows all frameworks (GRI, SASB, TCFD, etc.)
- ✅ Framework names display correctly
- ✅ Frameworks sorted alphabetically or by priority
- ✅ No duplicate entries

**Failure Indicators**:
- ❌ Dropdown empty
- ❌ Missing frameworks
- ❌ Duplicate frameworks

---

#### T2.7: Framework Fields Loading
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify fields load when framework selected

**Test Steps**:
1. Open NEW page
2. Select "GRI" framework
3. Wait for fields to load
4. Count fields in selection panel

**Expected Results**:
- ✅ Fields load within 2 seconds
- ✅ All fields from selected framework present
- ✅ Fields organized by topics
- ✅ No duplicate fields

**Failure Indicators**:
- ❌ Fields don't load
- ❌ Only partial fields load
- ❌ Wrong framework's fields shown

---

#### T2.8: Entity List Loading
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify entities available for assignment

**Test Steps**:
1. Open NEW page
2. Select some data points
3. Click "Assign to Entities"
4. Check entity modal/panel

**Expected Results**:
- ✅ All company entities listed
- ✅ Entity hierarchy/tree structure (if applicable)
- ✅ Entity names correct
- ✅ No duplicate entities

**Failure Indicators**:
- ❌ No entities shown
- ❌ Entities from other companies visible (tenant isolation broken)
- ❌ Entity tree broken

---

#### T2.9: Search API Integration
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify search functionality works with backend

**Test Steps**:
1. Open NEW page
2. Select a framework
3. Type in search box (e.g., "emissions")
4. Check search results

**Expected Results**:
- ✅ Search triggers after 2+ characters
- ✅ Results filtered correctly
- ✅ Highlighting shows matched text
- ✅ Search completes within 500ms

**Failure Indicators**:
- ❌ Search doesn't trigger
- ❌ No results shown
- ❌ Wrong results shown
- ❌ Search too slow (>1s)

---

#### T2.10: Loading State Indicators
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify loading spinners/states show during async operations

**Test Steps**:
1. Open NEW page
2. Watch for loading indicators during:
   - Initial page load
   - Framework selection
   - Field loading
   - Save operations

**Expected Results**:
- ✅ Loading indicator shows during fetch
- ✅ Indicator hides when complete
- ✅ User can see progress
- ✅ No flickering/rapid show-hide

**Failure Indicators**:
- ❌ No loading indicator
- ❌ Indicator never hides
- ❌ Indicator shows after content already loaded

---

#### T2.11: Error Message Display
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify error messages shown to users are helpful

**Test Steps**:
1. Open NEW page
2. Trigger an error (e.g., select framework offline)
3. Read error message

**Expected Results**:
- ✅ Error message displays in UI (not just console)
- ✅ Message is user-friendly (not technical)
- ✅ Message suggests action (e.g., "Try again")
- ✅ Message can be dismissed

**Failure Indicators**:
- ❌ No visible error message
- ❌ Error only in console
- ❌ Error message too technical
- ❌ Can't dismiss message

---

#### T2.12: Retry Mechanisms
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify failed requests can be retried

**Test Steps**:
1. Open NEW page
2. Simulate network error
3. Trigger an API call (framework selection)
4. Check if retry option available

**Expected Results**:
- ✅ Retry button/link shown on failure
- ✅ Clicking retry re-attempts the request
- ✅ Success after retry shows success message
- ✅ Multiple retries supported

**Failure Indicators**:
- ❌ No retry option
- ❌ Retry doesn't work
- ❌ Must refresh page to retry

---

## Success Criteria for Phase 9.1

**Phase 9.1 is COMPLETE when:**
- ✅ All 24 tests executed (12 foundation + 12 services)
- ✅ Zero P0 (critical) bugs found
- ✅ All P1 (high) bugs fixed
- ✅ P2/P3 bugs documented for later
- ✅ ui-testing-agent approves phase
- ✅ Test report generated with evidence

**Key Validation Points:**
- Event system robust and reliable
- State management works correctly
- API layer handles errors gracefully
- Services layer ready for production

---

## Test Deliverables

### Required Outputs
1. **Test Execution Report**: Pass/Fail for all 24 tests
2. **Bug Report**: Any issues found with priority (P0-P3)
3. **Screenshots/Evidence**: Console logs, UI states, error messages
4. **Recommendation**: PROCEED to Phase 9.2 / FIX BUGS FIRST

### Bug Priority Definitions
- **P0 (Critical)**: Blocks core functionality, must fix immediately
- **P1 (High)**: Major issue, fix before Phase 9 completion
- **P2 (Medium)**: Minor issue, can defer to post-launch
- **P3 (Low)**: Cosmetic, backlog for future

---

## Next Steps After Phase 9.1

**If all tests pass:**
→ Proceed to Phase 9.2 (UI Components Deep Dive - 38 tests)

**If critical bugs found:**
→ Invoke bug-fixer, retest, then proceed

**Final Check:**
→ Compare results against main testing plan to ensure coverage complete

---

## Reference Documentation

**Main Spec File**: `../Phase-9-Comprehensive-Testing-Plan.md`
**Test Page**: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points
**Baseline Page**: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-redesigned
**Login**: alice@alpha.com / admin123

---

**Document Version**: 1.0
**Last Updated**: 2025-09-30
**Prepared For**: ui-testing-agent execution