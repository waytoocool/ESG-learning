# Visual Test Reference Guide
## Computed Field Dependency Management - What to Look For

This guide provides visual descriptions of what testers should observe during manual testing.

---

## TC-001: Auto-Cascade Selection - Visual Checklist

### BEFORE Selection:
```
Left Panel (Topic Tree):
┌─────────────────────────────────────────┐
│ GRI 401: Employment 2016                │
│   ▶ Total rate of employee turnover 🧮(2) │  ← Look for purple badge
│   ▶ Total rate of new employee hires 🧮(2) │
│   ▶ Number of new employee hires         │
│   ▶ Number of employee turnover          │
└─────────────────────────────────────────┘

Right Panel (Selected):
┌─────────────────────────────────────────┐
│ 0 selected                               │
│ [Empty State Message]                    │
└─────────────────────────────────────────┘
```

### AFTER Clicking + on "Total rate of employee turnover":
```
Left Panel:
┌─────────────────────────────────────────┐
│ GRI 401: Employment 2016                │
│   ✓ Total rate of employee turnover 🧮(2) │ ← Button changes to checkmark
│   ✓ Number of new employee hires         │ ← Auto-selected (dependency)
│   ✓ Number of employee turnover          │ ← Auto-selected (dependency)
└─────────────────────────────────────────┘

Right Panel:
┌─────────────────────────────────────────┐
│ 3 selected                               │ ← Counter shows 3
├─────────────────────────────────────────┤
│ 🧮 Total rate of employee turnover      │ ← Computed field (parent)
│   ├─ Number of new employee hires       │ ← Dependency (auto-added)
│   └─ Number of employee turnover        │ ← Dependency (auto-added)
└─────────────────────────────────────────┘

Toast Notification (top-right):
┌─────────────────────────────────────────┐
│ ✓ Dependencies Auto-Added                │
│   Added 'Total rate of employee         │
│   turnover' and 2 dependencies          │
└─────────────────────────────────────────┘
```

### Console Output (F12):
```
[DependencyManager] Loading dependency data...
[DependencyManager] Loaded dependencies for 8 computed fields
[DependencyManager] Initialized successfully
[SelectDataPointsPanel] Add button clicked for field: field_123
[DependencyManager] Auto-adding 2 dependencies for field_123
[DependencyManager] Successfully added 2 dependency fields
[AppState] Added selected data point: Total rate of employee turnover
[AppState] Added selected data point: Number of new employee hires
[AppState] Added selected data point: Number of employee turnover
```

---

## TC-008: Visual Indicators - Badge Examples

### Topic Tree View:
```
┌────────────────────────────────────────────────────┐
│ GRI 401: Employment 2016                          │
│                                                    │
│   Regular Field:                                   │
│   ▶ Number of new employee hires                  │ ← No badge (regular field)
│                                                    │
│   Computed Field:                                  │
│   ▶ Total rate of employee turnover 🧮(2)         │ ← Purple badge + icon + count
│      ↑                                  ↑    ↑     │
│      │                                  │    │     │
│   Field name                      Badge Icon Count │
└────────────────────────────────────────────────────┘

Badge Details:
- Color: Purple/gradient background
- Icon: Calculator (🧮 or fa-calculator)
- Count: (2) or (X) showing number of dependencies
- Tooltip (hover): "Computed field with 2 dependencies"
```

### Flat List View:
```
┌────────────────────────────────────────────────────┐
│ All Fields                                         │
│                                                    │
│ GRI 401: Employment 2016 (15 fields) [+ Add All]  │
│   ├─ Number of new employee hires              [+]│ ← No badge
│   ├─ Number of employee turnover               [+]│ ← No badge
│   ├─ Total rate of employee turnover 🧮(2)     [+]│ ← Badge visible
│   └─ Total rate of new employee hires 🧮(2)    [+]│ ← Badge visible
└────────────────────────────────────────────────────┘
```

### CSS Classes to Verify (in Inspector):
```html
<span class="computed-badge"
      title="Computed field with 2 dependencies">
    <i class="fas fa-calculator"></i>
    <small>(2)</small>
</span>
```

---

## TC-004: Collapsible Grouping - Visual States

### IDEAL BEHAVIOR (Grouping Working):

#### Expanded State:
```
Right Panel (Selected):
┌────────────────────────────────────────────────────┐
│ 3 selected                                         │
├────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────┐  │
│ │ ▼ [✓] 🧮 Total rate of employee turnover  [⚙][x]│ ← Toggle down
│ │          Field Code: GRI-401-1-a                 │
│ │          Configuration: ✓ Configured             │
│ │          Entities: ✓ 3 entities assigned         │
│ │                                                  │
│ │    ↳ [✓] Number of new employee hires      [x]│ ← Dependency
│ │          Field Code: GRI-401-1-b                 │
│ │                                                  │
│ │    ↳ [✓] Number of employee turnover       [x]│ ← Dependency
│ │          Field Code: GRI-401-1-c                 │
│ └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

#### Collapsed State:
```
Right Panel (Selected):
┌────────────────────────────────────────────────────┐
│ 3 selected                                         │
├────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────┐  │
│ │ ▶ [✓] 🧮 Total rate of employee turnover  [⚙][x]│ ← Toggle right
│ │          Field Code: GRI-401-1-a                 │
│ │          Configuration: ✓ Configured             │
│ │          Entities: ✓ 3 entities assigned         │
│ │          [2 dependencies hidden]                 │ ← Collapsed indicator
│ └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

### DEGRADED BEHAVIOR (Fallback - ACCEPTABLE):

```
Right Panel (Selected):
┌────────────────────────────────────────────────────┐
│ 3 selected                                         │
├────────────────────────────────────────────────────┤
│ [✓] 🧮 Total rate of employee turnover      [⚙][x]│ ← No toggle button
│     Field Code: GRI-401-1-a                        │
│                                                    │
│ [✓] Number of new employee hires            [⚙][x]│ ← Flat list
│     Field Code: GRI-401-1-b                        │
│                                                    │
│ [✓] Number of employee turnover             [⚙][x]│ ← Flat list
│     Field Code: GRI-401-1-c                        │
└────────────────────────────────────────────────────┘

Console Output:
[SelectedDataPointsPanel] Generating flat HTML...
[SelectedDataPointsPanel] DependencyManager not ready, using flat list
```

### DOM Elements to Check (in Inspector):

**If Grouping Working:**
```javascript
// In Console:
document.querySelector('.computed-field-group')
// Expected: <div class="computed-field-group" data-field-id="...">

document.querySelector('.dependency-toggle-btn')
// Expected: <button class="dependency-toggle-btn" data-field-id="...">

document.querySelector('.computed-field-dependencies')
// Expected: <div class="computed-field-dependencies collapsed" ...>
```

**If Degraded (Fallback):**
```javascript
// In Console:
window.DependencyManager.isReady()
// Expected: false (or undefined)

document.querySelector('.computed-field-group')
// Expected: null (grouping not rendered)
```

---

## RT-001: Regression Testing - Visual Verification

### Regular Field Selection (NO Auto-Cascade):

#### BEFORE:
```
Left Panel:
┌─────────────────────────────────────────┐
│ GRI 401: Employment 2016                │
│   ▶ Number of new employee hires        │ ← Regular field (no badge)
│   ▶ Number of employee turnover         │ ← Regular field (no badge)
└─────────────────────────────────────────┘

Right Panel:
┌─────────────────────────────────────────┐
│ 0 selected                               │
└─────────────────────────────────────────┘
```

#### AFTER Clicking + on "Number of new employee hires":
```
Left Panel:
┌─────────────────────────────────────────┐
│ GRI 401: Employment 2016                │
│   ✓ Number of new employee hires        │ ← Only this field selected
│   ▶ Number of employee turnover         │ ← NOT auto-selected
└─────────────────────────────────────────┘

Right Panel:
┌─────────────────────────────────────────┐
│ 1 selected                               │ ← Counter shows 1 (not 3)
├─────────────────────────────────────────┤
│ [✓] Number of new employee hires   [⚙][x]│ ← Only 1 field
└─────────────────────────────────────────┘

Console Output (NO auto-cascade logs):
[SelectDataPointsPanel] Add button clicked for field: field_456
[AppState] Added selected data point: Number of new employee hires
(No DependencyManager auto-add logs)
```

### Remove Regular Field (NO Warning):

#### Clicking [x] on regular field:
```
┌─────────────────────────────────────────┐
│ 1 selected                               │
├─────────────────────────────────────────┤
│ [✓] Number of new employee hires   [⚙][X]│ ← Click X
└─────────────────────────────────────────┘
                ↓
        (Field removed immediately)
                ↓
┌─────────────────────────────────────────┐
│ 0 selected                               │
│ [Empty State Message]                    │
└─────────────────────────────────────────┘

NO WARNING MODAL APPEARS ← Important!
```

---

## Console Verification Checklist

### ✅ PASS Indicators:
```
✓ [DependencyManager] Initialized successfully
✓ [SelectDataPointsPanel] Auto-loading topic tree on initialization...
✓ [SelectedDataPointsPanel] Initialized successfully
✓ [DependencyManager] Auto-adding X dependencies for [field-id]
✓ No red errors in console
```

### ❌ FAIL Indicators:
```
✗ Uncaught TypeError: Cannot read property 'get' of undefined
✗ [DependencyManager] Failed to load dependencies
✗ 404 Not Found: /admin/api/assignments/dependency-tree
✗ DependencyManager is not defined
✗ AppState is not defined
```

### ⚠️ WARNING Indicators (May be acceptable):
```
⚠ [SelectedDataPointsPanel] DependencyManager not ready, using flat list
⚠ [Warning] Missing framework data for field X
⚠ [Info] Using fallback rendering for grouping
```

---

## Screenshot Checklist

When taking screenshots, ensure:

1. **Full Page Context** - Include URL bar, panels, toolbar
2. **Console Visible** - F12 open, Console tab active
3. **Highlights** - Use browser's inspect tool to highlight elements
4. **State Indicators** - Capture counters, badges, buttons
5. **Tooltips** - Hover and capture tooltip text if relevant
6. **Timing** - Capture notifications before they disappear

### Critical Screenshots:
- [ ] Initial page load (before any action)
- [ ] Computed field with purple badge (close-up)
- [ ] After clicking + on computed field (showing auto-cascade)
- [ ] Selected panel showing 3 fields
- [ ] Console logs showing auto-add messages
- [ ] Collapsed dependency group
- [ ] Expanded dependency group
- [ ] Regular field selection (no cascade)
- [ ] Final state after all tests

---

## Quick Reference: What Makes Each Test PASS

### TC-001 PASS:
- ✅ Counter shows "3 selected"
- ✅ Console shows auto-add logs
- ✅ Success notification appears
- ✅ 3 fields visible in selected panel

### TC-008 PASS:
- ✅ Purple badge visible on computed fields
- ✅ Calculator icon present
- ✅ Dependency count shown (e.g., "(2)")
- ✅ Tooltip displays correctly

### TC-004 PASS (Ideal):
- ✅ Toggle button (▶/▼) visible
- ✅ Dependencies grouped under parent
- ✅ Toggle works (collapse/expand)
- ✅ Icon changes correctly

### TC-004 PASS (Degraded - ACCEPTABLE):
- ✅ All fields visible in flat list
- ✅ No toggle button (flat layout)
- ✅ Console shows "DependencyManager not ready"
- ✅ All fields still accessible

### RT-001 PASS:
- ✅ Regular fields add one at a time
- ✅ Counter increments by 1
- ✅ No auto-cascade occurs
- ✅ Remove works without warning

---

**Visual Reference Version:** 1.0
**Last Updated:** 2025-11-10
**For Use With:** P0_Test_Execution_Results.md
