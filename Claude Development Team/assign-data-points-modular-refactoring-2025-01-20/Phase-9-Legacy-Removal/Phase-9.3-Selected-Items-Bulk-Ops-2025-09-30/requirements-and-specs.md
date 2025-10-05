# Phase 9.3: Selected Items & Bulk Operations - Testing Plan

**Date**: 2025-09-30
**Phase**: 9.3 - Selected Items Panel & Bulk Operations
**Parent**: Phase 9 Comprehensive Testing
**Status**: Ready for Execution
**Total Tests**: 15 tests
**Estimated Time**: 2 hours
**Priority**: HIGH (Core functionality)

---

## Context & Background

### Purpose

Phase 9.3 focuses on testing the **Selected Data Points Panel** and **bulk operations** functionality. This panel displays all currently selected data points and provides controls for managing selections (remove individual items, deselect all, view configurations/assignments).

### Why This Phase Matters

The Selected Items Panel is a **critical user-facing component** that:
- Shows users what data points they've selected
- Provides feedback on configuration/assignment status
- Enables bulk removal operations
- Displays grouping by topic for better organization
- Serves as the primary interface for managing large selections

**Risk Level**: 🟡 **MEDIUM-HIGH**
- Users rely on this panel to verify their selections before saving
- Bulk operations can affect many data points at once
- State synchronization between selection panel and selected items panel must be perfect
- Status indicators must be accurate for users to make informed decisions

### Prerequisites

**Must Be Complete Before Starting**:
- ✅ Phase 9.1: Foundation & Services (COMPLETE)
- ✅ Phase 9.2: UI Components (COMPLETE)

**Why Prerequisites Matter**:
- Phase 9.1 validated AppState management (selection add/remove)
- Phase 9.2 validated toolbar buttons and selection mechanisms
- Phase 9.3 builds on these foundations to test the "right panel" where selections are displayed

### Test Environment

**Test Page:**
- **URL**: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2
- **Login**: alice@alpha.com / admin123

**Browser**: Chrome (primary)

**Key UI Components**:
- **Left Panel**: Framework/topic selection (tested in Phase 9.2)
- **Right Panel**: Selected data points panel (THIS PHASE)
- **Toolbar**: Action buttons and counter (tested in Phase 9.2)

---

## Test Coverage

### Phase 5: Selected Panel Tests (15 tests)

**Focus**: Item display, removal, bulk operations, status indicators

#### Tests Previously Completed (Round 6)

| Test ID | Test Name | Status | Notes |
|---------|-----------|--------|-------|
| T5.1 | Selected items display | ✅ DONE Round 6 | Re-verify in this phase |
| T5.2 | Field names correct | ✅ DONE Round 6 | Re-verify in this phase |
| T5.3 | Topic grouping | ✅ DONE Round 6 | Re-verify in this phase |

#### Tests Pending Execution

| Test ID | Test Name | Priority | Complexity |
|---------|-----------|----------|------------|
| T5.4 | Remove individual item | P0 | Medium |
| T5.5 | Remove item updates counter | P1 | Low |
| T5.6 | Remove item updates AppState | P0 | Medium |
| T5.7 | Bulk remove (select multiple, remove all) | P1 | High |
| T5.8 | "Deselect All" clears all items | P0 | Medium |
| T5.9 | "Deselect All" resets counter to 0 | P1 | Low |
| T5.10 | Configuration status indicators | P1 | Medium |
| T5.11 | Entity assignment indicators | P1 | Medium |
| T5.12 | Inactive toggle show/hide | P2 | Low |
| T5.13 | Empty state message when no selections | P2 | Low |
| T5.14 | Scroll behavior with 50+ items | P2 | Medium |
| T5.15 | Item hover effects | P3 | Low |

**Total**: 15 tests (3 re-verify, 12 new)

---

## Detailed Test Specifications

### Group 1: Basic Display (Re-verification - 3 tests)

#### T5.1: Selected Items Display ✅ (Re-verify)
**Priority**: P0
**Status**: Previously passing in Round 6, re-verify still works

**Steps**:
1. Load page with existing 17 assignments
2. Verify selected items panel shows 17 items
3. Select additional data points from left panel
4. Verify new selections appear in right panel immediately

**Expected**:
- All selected items display in right panel
- Items render immediately after selection
- No lag or delay

**Evidence**: Screenshot of selected items panel

---

#### T5.2: Field Names Correct ✅ (Re-verify)
**Priority**: P1
**Status**: Previously passing in Round 6, re-verify no regressions

**Steps**:
1. Load page with existing assignments
2. Inspect field names in selected items panel
3. Verify no "Unnamed Field" or undefined labels

**Expected**:
- All field names display correctly
- No "Unnamed Field" or null/undefined labels
- Names match the data point definitions

**Evidence**: Screenshot showing proper field names

---

#### T5.3: Topic Grouping ✅ (Re-verify)
**Priority**: P1
**Status**: Previously passing in Round 6, re-verify grouping logic

**Steps**:
1. Select data points from multiple topics
2. Verify items grouped by topic in right panel
3. Verify topic headers display correctly

**Expected**:
- Items grouped by parent topic
- Topic headers visible and labeled
- Grouping makes sense and aids usability

**Evidence**: Screenshot showing topic grouping

---

### Group 2: Item Removal Operations (4 tests)

#### T5.4: Remove Individual Item
**Priority**: P0 - CRITICAL
**Complexity**: Medium

**Description**: Test ability to remove a single selected data point

**Steps**:
1. Load page with 17 existing assignments
2. Verify count: "17 data points selected"
3. Click "Remove" (X button) on one specific item
4. Verify item disappears from right panel
5. Check console: `AppState.selectedDataPoints.size` should be 16

**Expected**:
- ✅ Item removes from UI immediately
- ✅ AppState.selectedDataPoints.size decreases by 1
- ✅ Counter updates to "16 data points selected"
- ✅ Checkbox in left panel unchecks
- ✅ No errors in console

**Bug Risk**: 🔴 **HIGH** - This is core removal functionality, bugs here would be critical

**Evidence Required**:
- Screenshot BEFORE removal (17 items)
- Screenshot AFTER removal (16 items)
- Console log showing AppState.size = 16

---

#### T5.5: Remove Item Updates Counter
**Priority**: P1 - HIGH
**Complexity**: Low

**Description**: Verify counter updates in real-time when item removed

**Steps**:
1. Load page with multiple selections (e.g., 17)
2. Note current counter: "17 data points selected"
3. Remove 1 item
4. Verify counter updates to "16 data points selected"
5. Remove 2 more items
6. Verify counter updates to "14 data points selected"

**Expected**:
- Counter updates immediately (< 100ms)
- Counter always accurate
- No stale counter values

**Evidence**: Screenshot showing counter before/after removals

---

#### T5.6: Remove Item Updates AppState
**Priority**: P0 - CRITICAL
**Complexity**: Medium

**Description**: Verify AppState.selectedDataPoints Map stays synchronized

**Steps**:
1. Load page, check `AppState.selectedDataPoints.size` (e.g., 17)
2. Remove 1 item via UI
3. Re-check `AppState.selectedDataPoints.size` (should be 16)
4. Verify removed item's field_id no longer in Map
5. Use console: `AppState.selectedDataPoints.has(removed_field_id)` should be false

**Expected**:
- ✅ AppState.size decrements correctly
- ✅ Removed item no longer in Map
- ✅ Map keys accurate
- ✅ Global state synchronized with UI

**Bug Risk**: 🔴 **HIGH** - State desync would break entire system

**Evidence Required**:
- Console log of AppState.size before/after
- Console log showing `has(field_id)` returns false

---

#### T5.7: Bulk Remove (Select Multiple, Remove All)
**Priority**: P1 - HIGH
**Complexity**: High

**Description**: Test bulk removal of multiple selected items

**Steps**:
1. Load page with 17 selections
2. If bulk selection UI exists:
   - Select 5 items in selected panel
   - Click "Remove Selected" or equivalent bulk action
3. If no bulk UI:
   - Remove items one by one (5 items)
4. Verify all 5 items removed
5. Verify counter updates to "12 data points selected"
6. Verify `AppState.selectedDataPoints.size` = 12

**Expected**:
- All selected items removed
- Counter accurate
- AppState synchronized
- Operation completes quickly (< 1 second for 5 items)

**Evidence**:
- Screenshot before bulk remove
- Screenshot after bulk remove
- Console log of AppState.size

---

### Group 3: Deselect All (2 tests)

#### T5.8: "Deselect All" Clears All Items
**Priority**: P0 - CRITICAL
**Complexity**: Medium

**Description**: Verify "Deselect All" button clears entire selected panel

**Note**: This was tested in Phase 9.2, but testing again from the perspective of the Selected Items Panel

**Steps**:
1. Load page with 17 selections
2. Verify selected items panel shows 17 items
3. Click "Deselect All" button (in toolbar)
4. Verify selected items panel is now empty or shows "No selections" message
5. Check `AppState.selectedDataPoints.size` === 0

**Expected**:
- ✅ Selected items panel clears completely
- ✅ Empty state message displays
- ✅ AppState.size === 0
- ✅ All checkboxes in left panel unchecked

**Bug Risk**: 🟡 **MEDIUM** - Already tested in Phase 9.2, but different perspective

**Evidence**:
- Screenshot of full panel (17 items)
- Screenshot of empty panel after Deselect All
- Console log of AppState.size = 0

---

#### T5.9: "Deselect All" Resets Counter to 0
**Priority**: P1 - HIGH
**Complexity**: Low

**Description**: Verify counter displays "0 data points selected" after Deselect All

**Note**: This was tested in Phase 9.2, re-verify here for completeness

**Steps**:
1. Load page with 17 selections
2. Verify counter: "17 data points selected"
3. Click "Deselect All"
4. Verify counter: "0 data points selected"

**Expected**:
- Counter resets to 0
- Text reads "0 data points selected" (not "0 data point selected" - grammar check)

**Evidence**: Screenshot of counter showing "0 data points selected"

---

### Group 4: Status Indicators (2 tests)

#### T5.10: Configuration Status Indicators
**Priority**: P1 - HIGH
**Complexity**: Medium

**Description**: Verify selected items show configuration status (configured vs pending)

**Steps**:
1. Load page with existing assignments (some configured, some not)
2. Inspect selected items panel
3. Look for visual indicators showing configuration status:
   - "Configured" badge/icon
   - "Pending Configuration" badge/icon
   - Different styling for configured vs unconfigured
4. Select new data point (should show "Pending")
5. Verify status indicator correct

**Expected**:
- ✅ Status indicators visible
- ✅ Configured items clearly marked
- ✅ Pending items clearly marked
- ✅ Easy to distinguish at a glance

**If Feature Doesn't Exist**: Document as "Feature Not Implemented" (not a bug, but note for future)

**Evidence**: Screenshot showing configured vs pending items

---

#### T5.11: Entity Assignment Indicators
**Priority**: P1 - HIGH
**Complexity**: Medium

**Description**: Verify selected items show entity assignment status

**Steps**:
1. Load page with existing assignments (some assigned to entities, some not)
2. Inspect selected items panel
3. Look for indicators showing:
   - "Assigned to 3 entities" or similar
   - "Not Assigned" or similar
   - Entity names or count
4. Verify accuracy by comparing to database or expected state

**Expected**:
- ✅ Assignment status visible
- ✅ Entity count or names displayed
- ✅ Unassigned items clearly marked
- ✅ Accurate information

**If Feature Doesn't Exist**: Document as "Feature Not Implemented" (not a bug)

**Evidence**: Screenshot showing entity assignment indicators

---

### Group 5: UI/UX Features (4 tests)

#### T5.12: Inactive Toggle Show/Hide
**Priority**: P2 - MEDIUM
**Complexity**: Low

**Description**: Test toggle to show/hide inactive assignments

**Steps**:
1. Look for "Show Inactive" or similar toggle in selected panel
2. If toggle exists:
   - Enable "Show Inactive"
   - Verify inactive items appear with visual distinction
   - Disable "Show Inactive"
   - Verify inactive items hidden
3. If toggle doesn't exist:
   - Document as "Feature Not Implemented"

**Expected** (if feature exists):
- Toggle controls visibility of inactive items
- Inactive items visually distinct (greyed out, different icon)
- Toggle state persists during session

**Evidence**: Screenshot with toggle ON, screenshot with toggle OFF

---

#### T5.13: Empty State Message When No Selections
**Priority**: P2 - MEDIUM
**Complexity**: Low

**Description**: Verify empty state messaging when no items selected

**Steps**:
1. Load page
2. If no pre-existing selections, panel should already be empty
3. If pre-existing selections, click "Deselect All"
4. Verify empty state message displays
5. Check message text (e.g., "No data points selected", "Select data points from the left panel")

**Expected**:
- ✅ Empty state message displays
- ✅ Message helpful and clear
- ✅ Message guides user to action (select from left panel)
- ✅ No awkward empty panel

**Evidence**: Screenshot of empty state

---

#### T5.14: Scroll Behavior with 50+ Items
**Priority**: P2 - MEDIUM
**Complexity**: Medium

**Description**: Test panel scrolling with large number of selections

**Steps**:
1. Select 50+ data points (use "Add All" on multiple topics)
2. Verify selected panel displays all items
3. Test scrolling:
   - Scroll bar appears
   - Smooth scrolling (no lag)
   - All items accessible
4. Test performance:
   - No freezing or lag
   - Remove item from middle of list (should work smoothly)

**Expected**:
- ✅ Panel handles 50+ items without performance issues
- ✅ Scroll bar functional
- ✅ All items accessible via scroll
- ✅ Operations (remove, etc.) still responsive

**Evidence**: Screenshot showing 50+ items with scroll bar

---

#### T5.15: Item Hover Effects
**Priority**: P3 - LOW
**Complexity**: Low

**Description**: Verify hover effects on selected items for better UX

**Steps**:
1. Load page with selections
2. Hover mouse over individual items in selected panel
3. Observe visual feedback:
   - Background color change
   - Border highlight
   - Remove button visibility change
4. Verify hover effects enhance usability

**Expected**:
- ✅ Hover effects present
- ✅ Visual feedback clear
- ✅ Hover effects consistent across items
- ✅ Enhances UX without being distracting

**Can Defer**: This is cosmetic, low priority

**Evidence**: Screenshot showing hover effect

---

## Success Criteria

Phase 9.3 is COMPLETE and can proceed to Phase 9.4 when:

### Critical Requirements (Must Pass)
- ✅ All P0 tests passed (T5.4, T5.6, T5.8)
- ✅ All P1 tests passed (T5.2, T5.3, T5.5, T5.7, T5.9, T5.10, T5.11)
- ✅ Zero P0 bugs found (or all fixed)
- ✅ Zero P1 bugs found (or all fixed and verified)

### Quality Requirements
- ✅ Item removal working correctly (individual and bulk)
- ✅ AppState stays synchronized with UI
- ✅ Counter always accurate
- ✅ Status indicators accurate (if implemented)
- ✅ No performance issues with large selections

### Documentation Requirements
- ✅ Test execution report created
- ✅ All tests documented as PASS/FAIL
- ✅ Screenshots for evidence
- ✅ Any bugs documented with priority and reproduction steps

---

## Test Execution Strategy

### Order of Execution

**Phase 1: Re-verification (15 minutes)**
1. T5.1: Selected items display
2. T5.2: Field names correct
3. T5.3: Topic grouping

**Phase 2: Critical Removal Operations (45 minutes)**
4. T5.4: Remove individual item
5. T5.6: Remove item updates AppState
6. T5.5: Remove item updates counter
7. T5.7: Bulk remove

**Phase 3: Deselect All (20 minutes)**
8. T5.8: Deselect All clears all items
9. T5.9: Deselect All resets counter

**Phase 4: Status Indicators (30 minutes)**
10. T5.10: Configuration status indicators
11. T5.11: Entity assignment indicators

**Phase 5: UI/UX Features (30 minutes)**
12. T5.13: Empty state message
13. T5.14: Scroll behavior with 50+ items
14. T5.12: Inactive toggle (if exists)
15. T5.15: Item hover effects (if time permits)

**Total Estimated Time**: 2 hours

---

## Bug Priority Definitions

**P0 (Critical)**: Blocks core functionality, must fix before Phase 9.4
- Example: Individual item removal doesn't work, AppState desync

**P1 (High)**: Major feature broken, fix before Phase 9 completion
- Example: Counter doesn't update, status indicators wrong

**P2 (Medium)**: Minor issue, can defer to post-launch
- Example: Empty state message missing, scroll performance poor

**P3 (Low)**: Cosmetic, backlog for future
- Example: Hover effects missing, styling issues

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| State desync (AppState vs UI) | 🟡 MEDIUM | 🔴 HIGH | Thorough testing of T5.6, check console frequently |
| Bulk operations break | 🟡 MEDIUM | 🟡 MEDIUM | Test T5.7 carefully, try edge cases |
| Performance with large datasets | 🟢 LOW | 🟡 MEDIUM | Test T5.14 with 50+ items |
| Status indicators inaccurate | 🟡 MEDIUM | 🟡 MEDIUM | Validate T5.10, T5.11 against expected data |

**Overall Phase Risk**: 🟡 **MEDIUM**

---

## Deliverables

### Test Report
Create report at: `/Claude Development Team/.../Phase-9.3-Selected-Items-Bulk-Ops-2025-09-30/ui-testing-agent/Phase_9.3_Test_Execution_Report.md`

**Report Must Include**:
1. Executive summary (tests passed/failed, bugs found)
2. Detailed results for all 15 tests
3. Bug report (if any bugs found)
4. Screenshots for evidence
5. Final recommendation (APPROVE or FIX BUGS FIRST)

### Screenshots
Save screenshots in: `ui-testing-agent/screenshots/`

**Required Screenshots**:
- T5.1-T5.3: Re-verification evidence
- T5.4-T5.6: Individual removal before/after
- T5.7: Bulk removal evidence
- T5.8-T5.9: Deselect All evidence
- T5.10-T5.11: Status indicators (if exist)
- T5.13: Empty state
- T5.14: Large dataset scrolling

---

## References

**Main Testing Plan**:
`/Claude Development Team/.../Phase-9-Legacy-Removal/Phase-9-Comprehensive-Testing-Plan.md` (Lines 235-265)

**Phase 9.1 Report** (Foundation validation):
`/Claude Development Team/.../Phase-9.1-Foundation-Services-2025-09-30/Phase-9.1-Completion-Verification.md`

**Phase 9.2 Report** (UI Components validation):
`/Claude Development Team/.../Phase-9.2-UI-Components-2025-09-30/Phase-9.2-Completion-Verification.md`

**Previous Round 6 Testing**:
`/Claude Development Team/.../Phase-9-Legacy-Removal/ui-testing-agent/Reports_v6/Round_6_Comprehensive_Testing_Report.md`

---

## Notes for ui-testing-agent

- Start Flask app if not running: `python3 run.py`
- Use Playwright MCP tools for browser automation
- Take frequent screenshots for evidence
- Check console logs after each operation (AppState.size, errors)
- If a feature doesn't exist (e.g., status indicators), document as "Feature Not Implemented" (not a bug)
- Focus on critical tests first (P0, P1)
- Defer P3 tests if time-constrained

---

**Ready to Begin Testing**: ✅ YES
**Prerequisites Met**: ✅ YES (Phase 9.1 and 9.2 complete)
**Estimated Completion**: 2 hours from start