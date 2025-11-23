# Phase 9.2: UI Components Deep Dive - Requirements & Specs

**Date**: 2025-09-30
**Status**: Ready for Testing
**Total Tests**: 38 tests
**Estimated Time**: 3-4 hours
**Priority**: HIGH (Core UI)

---

## Context & Background

### Purpose
Phase 9.2 validates the UI component layer - the toolbar buttons, selection panel, and all user-facing interactive elements. These are the primary components users interact with daily.

### Scope
This phase combines two critical UI testing areas:
- **Phase 3**: CoreUI & Toolbar Tests (18 tests) - Toolbar buttons, counters, enable/disable logic
- **Phase 4**: Selection Panel Tests (20 tests) - Framework selection, search, view toggles

### Why This Phase is Critical
- UI components are the user's primary interaction points
- Toolbar state management drives user workflows
- Selection panel is the core data entry interface
- Bugs here directly impact user experience and productivity

### Previous Testing
Phase 9.1 validated the foundation layer (events, state, services). Phase 9.2 builds on that foundation to test the UI layer that users see and interact with.

**Already Tested in Round 6**:
- ✅ Toolbar button visibility
- ✅ Selection counter display
- ✅ Framework selection
- ✅ Topic tree rendering
- ✅ Checkbox selection
- ✅ "Add All" button functionality

**Still Untested (91% of UI layer)**:
- ❌ Button enable/disable logic
- ❌ Button state transitions
- ❌ Search functionality (2+ char trigger, results, highlighting)
- ❌ View toggles (Topic Tree ↔ Flat List ↔ Search Results)
- ❌ Flat list rendering with 50+ fields
- ❌ Topic expand/collapse
- ❌ Already-selected and disabled field indicators

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
3. Phase 9.1 bugs fixed (foundation layer stable)
4. Test data seeded (frameworks with 50+ fields, entities, users)
5. Browser: Chrome (latest stable)

---

## Phase 3: CoreUI & Toolbar Tests (18 Tests)

### Focus Areas
- Toolbar button visibility and accessibility
- Selection counter accuracy
- Button enable/disable state logic
- Button click event handling

### Test Cases

#### T3.1: Toolbar Button Visibility ✅ (DONE in Round 6)
**Status**: COMPLETE
**Objective**: Verify all toolbar buttons are visible and correctly labeled

**Expected Results**:
- "Assign to Entities" button visible
- "Configure" button visible
- "Save All" button visible
- "Import" button visible
- "Export" button visible
- "History" button visible
- "Deselect All" button visible

---

#### T3.2: Selection Counter Display ✅ (DONE in Round 6)
**Status**: COMPLETE
**Objective**: Verify selection counter shows correct count

**Expected Results**:
- Counter displays current selection count
- Updates in real-time as selections change
- Format: "X selected" or similar

---

#### T3.3: "Assign to Entities" Button Enable/Disable Logic
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify button is only enabled when data points are selected

**Test Steps**:
1. Load page (19 existing assignments should be loaded)
2. Check button state with existing selections
3. Deselect all
4. Check button state with 0 selections
5. Select 1 data point
6. Check button state with 1 selection
7. Select 3 more data points
8. Check button state with multiple selections

**Expected Results**:
- ✅ Button **ENABLED** when count > 0
- ✅ Button **DISABLED** when count = 0
- ✅ Visual indication of disabled state (grayed out, cursor change)
- ✅ Tooltip or message explains why disabled

**Failure Indicators**:
- ❌ Button enabled with 0 selections
- ❌ Button disabled with selections
- ❌ Button state doesn't update in real-time

---

#### T3.4: "Configure" Button Enable/Disable Logic
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify button is only enabled when data points are selected

**Test Steps**:
1. Check button state with 0 selections
2. Select 1 data point
3. Check button state
4. Select 5 data points
5. Check button state

**Expected Results**:
- ✅ Button **ENABLED** when count > 0
- ✅ Button **DISABLED** when count = 0
- ✅ Visual indication of disabled state

**Failure Indicators**:
- ❌ Button clickable with no selections
- ❌ Button state incorrect

---

#### T3.5: "Save All" Button Enable/Disable Logic
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify button is only enabled when there are changes to save

**Test Steps**:
1. Load page with existing assignments (no changes)
2. Check button state (should be disabled - no changes)
3. Select a new data point
4. Check button state (should be enabled - has changes)
5. Configure a data point
6. Check button state (should be enabled - has changes)
7. Save changes
8. Check button state (should be disabled - no pending changes)

**Expected Results**:
- ✅ Button **DISABLED** on initial load (no changes)
- ✅ Button **ENABLED** when new selections made
- ✅ Button **ENABLED** when configurations changed
- ✅ Button **DISABLED** after successful save
- ✅ Visual indication of state

**Failure Indicators**:
- ❌ Button always enabled
- ❌ Button never enabled
- ❌ State doesn't update after save

---

#### T3.6: "Import" Button Accessibility
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify import button is always accessible

**Test Steps**:
1. Check button is visible
2. Check button is clickable
3. Click button and verify modal/action occurs

**Expected Results**:
- ✅ Button always enabled (import doesn't require selections)
- ✅ Button clickable
- ✅ Clicking opens import modal or triggers import flow

**Failure Indicators**:
- ❌ Button disabled
- ❌ Button not visible
- ❌ Click doesn't trigger action

---

#### T3.7: "Export" Button Accessibility
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify export button works with or without selections

**Test Steps**:
1. Check button with 0 selections
2. Check button with selections
3. Click and verify export action

**Expected Results**:
- ✅ Button enabled regardless of selection count
- ✅ Exports all assignments (if 0 selected) OR selected assignments
- ✅ Clicking triggers export action

**Failure Indicators**:
- ❌ Button incorrectly disabled
- ❌ Export doesn't work

---

#### T3.8: "History" Button Accessibility
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify history button is always accessible

**Test Steps**:
1. Check button is visible and enabled
2. Click button
3. Verify history view/modal opens

**Expected Results**:
- ✅ Button always enabled (history is always viewable)
- ✅ Clicking opens history timeline/modal
- ✅ History data loads (from Phase 9.1 fixed endpoint)

**Failure Indicators**:
- ❌ Button disabled
- ❌ Click doesn't open history
- ❌ History endpoint errors

---

#### T3.9: "Deselect All" Button Functionality
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify button clears all selections

**Test Steps**:
1. Select 5 data points manually
2. Check selection counter (should show 5)
3. Click "Deselect All" button
4. Check selection counter (should show 0)
5. Check selected items panel (should be empty)
6. Check checkboxes in selection panel (should all be unchecked)

**Expected Results**:
- ✅ Button clears all selections
- ✅ Counter resets to 0
- ✅ Selected items panel empties
- ✅ All checkboxes unchecked
- ✅ AppState.selectedDataPoints.size = 0

**Failure Indicators**:
- ❌ Selections not cleared
- ❌ Counter doesn't update
- ❌ Some selections remain

---

#### T3.10: Counter Updates in Real-Time
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify counter updates immediately as selections change

**Test Steps**:
1. Note current count
2. Check one checkbox → Counter should increment by 1
3. Check another checkbox → Counter should increment by 1
4. Uncheck first checkbox → Counter should decrement by 1
5. Click "Add All" in a topic → Counter should increment by topic field count
6. Deselect All → Counter should go to 0

**Expected Results**:
- ✅ Counter updates instantly (<100ms)
- ✅ No delay or flicker
- ✅ Accurate count at all times
- ✅ Events fire correctly (state-selectedDataPoints-changed)

**Failure Indicators**:
- ❌ Counter lags behind selections
- ❌ Counter shows incorrect count
- ❌ Counter doesn't update

---

#### T3.11: Button States with 0 Selections
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify button states when nothing is selected

**Test Steps**:
1. Deselect all
2. Check each button's state

**Expected Results**:
| Button | State with 0 Selections |
|--------|-------------------------|
| Assign to Entities | DISABLED |
| Configure | DISABLED |
| Save All | DISABLED |
| Import | ENABLED |
| Export | ENABLED |
| History | ENABLED |
| Deselect All | ENABLED (or hidden) |

**Failure Indicators**:
- ❌ Any incorrect button state

---

#### T3.12: Button States with 1 Selection
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify button states with single selection

**Test Steps**:
1. Select exactly 1 data point
2. Check each button's state

**Expected Results**:
| Button | State with 1 Selection |
|--------|------------------------|
| Assign to Entities | ENABLED |
| Configure | ENABLED |
| Save All | ENABLED (if unsaved) |
| Import | ENABLED |
| Export | ENABLED |
| History | ENABLED |
| Deselect All | ENABLED |

---

#### T3.13: Button States with Multiple Selections
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify button states with 5+ selections

**Test Steps**:
1. Select 5 data points
2. Check each button's state

**Expected Results**:
- All buttons behave correctly with bulk selections
- Performance remains good (no lag)

---

#### T3.14: Button Click Event Propagation
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify button clicks trigger correct events

**Test Steps**:
1. Open browser console
2. Click each toolbar button
3. Check console for event logs

**Expected Results**:
- ✅ Each button click logs an event
- ✅ Events have correct names (e.g., "toolbar:assignToEntities")
- ✅ Events fire before action occurs
- ✅ Action occurs after event fires

**Failure Indicators**:
- ❌ No events logged
- ❌ Events fire after action
- ❌ Incorrect event names

---

#### T3.15: Toolbar Responsive Design
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify toolbar works at different viewport widths

**Test Steps**:
1. Test at 1920px width (desktop)
2. Test at 1366px width (laptop)
3. Test at 1024px width (tablet)
4. Check button wrapping, spacing, visibility

**Expected Results**:
- ✅ Buttons visible at all widths
- ✅ No button overlap
- ✅ Appropriate wrapping/scrolling
- ✅ Readable labels

**Failure Indicators**:
- ❌ Buttons hidden or cut off
- ❌ Layout broken at smaller widths

---

#### T3.16: Toolbar Keyboard Navigation
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify toolbar is keyboard accessible

**Test Steps**:
1. Tab to toolbar
2. Tab through each button
3. Press Enter/Space on focused button
4. Verify action occurs

**Expected Results**:
- ✅ All buttons reachable via Tab
- ✅ Focus indicator visible
- ✅ Enter/Space triggers button action
- ✅ Logical tab order

**Failure Indicators**:
- ❌ Buttons not tabbable
- ❌ No focus indicator
- ❌ Enter doesn't work

---

#### T3.17: Button Tooltips
**Status**: PENDING
**Priority**: LOW
**Objective**: Verify buttons have helpful tooltips

**Test Steps**:
1. Hover over each button
2. Check for tooltip appearance
3. Read tooltip text

**Expected Results**:
- ✅ Tooltip appears within 500ms
- ✅ Tooltip describes button action
- ✅ Tooltip disappears on mouse out

**Failure Indicators**:
- ❌ No tooltips
- ❌ Tooltips unclear or incorrect

---

#### T3.18: Loading States During Operations
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify buttons show loading state during async operations

**Test Steps**:
1. Click "Save All" button
2. Observe button during save operation
3. Check for loading indicator (spinner, disabled state, text change)

**Expected Results**:
- ✅ Button shows loading state during save
- ✅ Button disabled during save (prevents double-click)
- ✅ Loading indicator visible
- ✅ Button returns to normal state after save completes

**Failure Indicators**:
- ❌ No loading indication
- ❌ Button can be clicked multiple times
- ❌ Button stays in loading state

---

## Phase 4: Selection Panel Tests (20 Tests)

### Focus Areas
- Framework dropdown functionality
- Topic tree rendering and interaction
- Search functionality
- View mode toggles (Topic Tree / Flat List / Search Results)
- Checkbox selection mechanics
- "Add All" buttons
- Field status indicators

### Test Cases

#### T4.1: Framework Selection ✅ (DONE in Round 6)
**Status**: COMPLETE
**Objective**: Verify framework dropdown works correctly

---

#### T4.2: Topic Tree Rendering ✅ (DONE in Round 6)
**Status**: COMPLETE
**Objective**: Verify topics render in tree structure

---

#### T4.3: Checkbox Selection ✅ (DONE in Round 6)
**Status**: COMPLETE
**Objective**: Verify individual checkbox selection works

---

#### T4.4: "Add All" Button Functionality ✅ (DONE in Round 6)
**Status**: COMPLETE
**Objective**: Verify "Add All" buttons work (fixed in NEW page)

---

#### T4.5: Search Input with 2+ Characters
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify search activates after typing 2+ characters

**Test Steps**:
1. Select a framework (e.g., GRI with 50+ fields)
2. Click search input box
3. Type "e" (1 character) → Check search doesn't activate
4. Type "em" (2 characters) → Check search activates
5. Check search results appear

**Expected Results**:
- ✅ Search doesn't trigger with 1 character
- ✅ Search triggers with 2+ characters
- ✅ Search results filter fields matching query
- ✅ View switches to "Search Results" mode

**Failure Indicators**:
- ❌ Search triggers with 1 character
- ❌ Search doesn't trigger with 2+ characters
- ❌ No results shown

---

#### T4.6: Search Results Highlighting
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify search terms are highlighted in results

**Test Steps**:
1. Search for "emissions"
2. Check if "emissions" is highlighted in field names
3. Check if highlighting is case-insensitive

**Expected Results**:
- ✅ Search term highlighted in results (bold, color, background)
- ✅ Highlighting case-insensitive
- ✅ Multiple occurrences highlighted

**Failure Indicators**:
- ❌ No highlighting
- ❌ Highlighting broken or ugly

---

#### T4.7: Search Clear Button
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify search can be cleared to return to tree view

**Test Steps**:
1. Perform a search (search for "energy")
2. Check for clear/X button in search input
3. Click clear button
4. Check view returns to Topic Tree

**Expected Results**:
- ✅ Clear button appears when search active
- ✅ Clicking clear resets search
- ✅ View returns to Topic Tree
- ✅ All fields visible again

**Failure Indicators**:
- ❌ No clear button
- ❌ Clear doesn't reset search
- ❌ View doesn't reset

---

#### T4.8: View Toggle: Topic Tree → Flat List
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify user can switch from tree view to flat list view

**Test Steps**:
1. Check view toggle control exists (tabs or buttons)
2. Current view should be "Topic Tree"
3. Click "Flat List" view toggle
4. Check all fields displayed in flat list format (no nesting)

**Expected Results**:
- ✅ View toggle control visible and labeled
- ✅ Clicking "Flat List" switches view
- ✅ All fields displayed without topic grouping
- ✅ Fields include topic name in display (for context)

**Failure Indicators**:
- ❌ No view toggle
- ❌ View doesn't switch
- ❌ Flat list broken or incomplete

---

#### T4.9: View Toggle: Topic Tree → Search Results
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify search automatically switches to Search Results view

**Test Steps**:
1. Start in Topic Tree view
2. Type search query "carbon"
3. Check view automatically switches to Search Results

**Expected Results**:
- ✅ View auto-switches to Search Results
- ✅ Only matching fields shown
- ✅ View label updates to indicate search mode

---

#### T4.10: View Toggle: Flat List → Topic Tree
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify user can switch back from flat list to tree

**Test Steps**:
1. Switch to Flat List view
2. Click "Topic Tree" view toggle
3. Check topics render with nested fields

**Expected Results**:
- ✅ View switches back to Topic Tree
- ✅ Fields grouped by topics
- ✅ Topic expand/collapse works
- ✅ Selections preserved across view changes

---

#### T4.11: Flat List Rendering with 50+ Fields
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify flat list handles large field counts

**Test Steps**:
1. Select GRI framework (has 100+ fields)
2. Switch to Flat List view
3. Check rendering performance
4. Scroll through entire list
5. Check for lag or freezing

**Expected Results**:
- ✅ All fields render (count matches framework field count)
- ✅ No lag or freezing
- ✅ Smooth scrolling
- ✅ Fields load within 2 seconds

**Failure Indicators**:
- ❌ Fields missing
- ❌ Page freezes or lags
- ❌ Slow rendering (>5 seconds)

---

#### T4.12: Flat List "Add" Buttons
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify each field has an "Add" button in flat list view

**Test Steps**:
1. Switch to Flat List view
2. Check each field has "Add" or "Select" button
3. Click "Add" button on a field
4. Verify field added to selections

**Expected Results**:
- ✅ Each field has action button
- ✅ Button adds field to selections
- ✅ Button changes to "Remove" or disables after adding
- ✅ Selection counter increments

**Failure Indicators**:
- ❌ Buttons missing
- ❌ Buttons don't work
- ❌ Duplicate additions possible

---

#### T4.13: Framework Filter in Flat List
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify flat list can filter by framework

**Test Steps**:
1. Switch to Flat List view
2. Check for framework filter dropdown
3. Select "GRI" from filter
4. Check only GRI fields shown

**Expected Results**:
- ✅ Framework filter available
- ✅ Filtering works correctly
- ✅ Field count updates

**Failure Indicators**:
- ❌ No filter option
- ❌ Filter doesn't work

---

#### T4.14: Topic Expand/Collapse All
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify topic tree can expand/collapse all at once

**Test Steps**:
1. Check for "Expand All" / "Collapse All" controls
2. Click "Collapse All" → All topics should collapse
3. Click "Expand All" → All topics should expand

**Expected Results**:
- ✅ Controls available and labeled
- ✅ Collapse All hides all fields
- ✅ Expand All shows all fields
- ✅ Fast operation (<1 second)

**Failure Indicators**:
- ❌ No expand/collapse controls
- ❌ Slow operation
- ❌ Doesn't work with large datasets

---

#### T4.15: Nested Sub-Topic Rendering
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify multi-level topic nesting renders correctly

**Test Steps**:
1. Find a framework with nested topics (e.g., GRI has multi-level topics)
2. Check topics render with proper indentation
3. Expand parent topic → Sub-topics should appear indented
4. Collapse parent → Sub-topics should hide

**Expected Results**:
- ✅ Multi-level nesting supported
- ✅ Visual indentation shows hierarchy
- ✅ Collapse/expand works recursively

**Failure Indicators**:
- ❌ Flat structure (no nesting)
- ❌ Broken hierarchy
- ❌ Collapse doesn't work recursively

---

#### T4.16: Data Point Checkbox States
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify checkboxes show correct checked/unchecked states

**Test Steps**:
1. Load page with existing selections
2. Check already-selected fields have checked checkboxes
3. Unselect a field → Checkbox should uncheck
4. Select a new field → Checkbox should check

**Expected Results**:
- ✅ Checkboxes reflect selection state
- ✅ State persists across view changes
- ✅ State accurate after page refresh

---

#### T4.17: Already-Selected Field Indicators
**Status**: PENDING
**Priority**: HIGH
**Objective**: Verify fields show visual indicator if already selected

**Test Steps**:
1. Load page with 19 existing selections
2. Find one of the pre-selected fields in selection panel
3. Check for visual indicator (background color, icon, badge)

**Expected Results**:
- ✅ Already-selected fields visually distinct
- ✅ Indicator clear and obvious
- ✅ Doesn't interfere with interaction

**Failure Indicators**:
- ❌ No visual indicator
- ❌ Can't tell which fields are selected
- ❌ Indicator confusing

---

#### T4.18: Disabled Field Indicators
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify fields that can't be selected show disabled state

**Test Steps**:
1. Check if any fields are disabled (e.g., already assigned to different entity, deprecated fields)
2. Try to select a disabled field
3. Check for visual indicator (grayed out, cursor change, disabled checkbox)

**Expected Results**:
- ✅ Disabled fields visually distinct
- ✅ Can't select disabled fields
- ✅ Tooltip explains why disabled

**Failure Indicators**:
- ❌ Disabled fields look selectable
- ❌ Can select disabled fields (shouldn't be possible)

---

#### T4.19: Empty State Messaging
**Status**: PENDING
**Priority**: LOW
**Objective**: Verify empty state shown when no fields match filter/search

**Test Steps**:
1. Search for gibberish text "zzzzzzz"
2. Check for empty state message
3. Clear search
4. Select framework with no fields (if any)
5. Check for empty state message

**Expected Results**:
- ✅ Empty state message appears
- ✅ Message helpful ("No results found", "Try different search")
- ✅ Suggests action (clear search, select different framework)

**Failure Indicators**:
- ❌ Blank screen
- ❌ No guidance for user

---

#### T4.20: Loading State During Framework Switch
**Status**: PENDING
**Priority**: MEDIUM
**Objective**: Verify loading indicator when switching frameworks

**Test Steps**:
1. Select GRI framework (large dataset)
2. Immediately switch to SASB framework
3. Check for loading indicator during field load

**Expected Results**:
- ✅ Loading indicator appears during load
- ✅ Selection panel disabled during load
- ✅ Indicator disappears when load complete
- ✅ Load completes within 2 seconds

**Failure Indicators**:
- ❌ No loading indicator
- ❌ Can interact during load (causes bugs)
- ❌ Slow loading (>5 seconds)

---

## Success Criteria for Phase 9.2

**Phase 9.2 is COMPLETE when:**
- ✅ All 38 tests executed (18 toolbar + 20 selection panel)
- ✅ Zero P0 (critical) bugs found
- ✅ All P1 (high) bugs fixed
- ✅ P2/P3 bugs documented for later
- ✅ ui-testing-agent approves phase
- ✅ Test report generated with evidence

**Key Validation Points:**
- Toolbar buttons work correctly (enable/disable, click events)
- Selection panel fully functional (search, views, checkboxes)
- UI responsive and performant
- Keyboard accessible
- Ready for Phase 9.3 (Selected Items Panel)

---

## Test Deliverables

### Required Outputs
1. **Test Execution Report**: Pass/Fail for all 38 tests
2. **Bug Report**: Any issues found with priority (P0-P3)
3. **Screenshots/Evidence**: Button states, search results, view modes
4. **Recommendation**: PROCEED to Phase 9.3 / FIX BUGS FIRST

### Bug Priority Definitions
- **P0 (Critical)**: Blocks core UI functionality, must fix immediately
- **P1 (High)**: Major UI issue, fix before Phase 9 completion
- **P2 (Medium)**: Minor UI issue, can defer to post-launch
- **P3 (Low)**: Cosmetic, backlog for future

---

## Next Steps After Phase 9.2

**If all tests pass:**
→ Proceed to Phase 9.3 (Selected Items & Bulk Operations - 15 tests)

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