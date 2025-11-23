# Visual Reference Guide: Collapsible Dependency Grouping Feature
**Feature:** Collapsible Dependency Grouping
**Date:** 2025-11-10
**Purpose:** Quick reference for QA team to identify correct vs incorrect rendering

---

## Quick Identification Guide

### ✅ CORRECT: Feature Working (What You Should See)

```
┌─────────────────────────────────────────────────────────────┐
│ Selected Data Points (3)                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ ▼ ☐  🧮 Total rate of new employee hires     (2) │   │ ← Purple border
│  │      Field Code: GRI-401-1-a                       │   │
│  │      Configuration: ✓ Configured                   │   │
│  │      Entities: ✓ 3 entities assigned              │   │
│  ├────────────────────────────────────────────────────┤   │
│  │    ➘ ☐  Number of new hires                      │   │ ← Blue border
│  │         Field Code: GRI-401-1-a-1                  │   │
│  │         Configuration: ✓ Configured                │   │
│  │                                                     │   │
│  │    ➘ ☐  Total number of employees                │   │ ← Blue border
│  │         Field Code: GRI-401-1-a-2                  │   │
│  │         Configuration: ✓ Configured                │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Legend:
▼ = Toggle button (can click to collapse)
☐ = Checkbox
🧮 = Calculator icon (computed field indicator)
(2) = Dependency count badge
➘ = Dependency arrow indicator
Purple border = Computed field
Blue border = Dependency field
```

### ❌ INCORRECT: Feature Broken (Old Behavior)

```
┌─────────────────────────────────────────────────────────────┐
│ Selected Data Points (3)                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ ☐  Total rate of new employee hires               │   │ ← No purple border
│  │    Field Code: GRI-401-1-a                         │   │   No toggle button
│  │    Configuration: ✓ Configured                     │   │   No badge
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ ☐  Number of new hires                            │   │ ← Not grouped
│  │    Field Code: GRI-401-1-a-1                       │   │   Flat list
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ ☐  Total number of employees                      │   │ ← Not grouped
│  │    Field Code: GRI-401-1-a-2                       │   │   Flat list
│  └────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Problems:
❌ No toggle button
❌ No purple border
❌ No calculator icon
❌ No dependency count badge
❌ No arrow indicator
❌ No blue border
❌ No grouping (flat list)
```

---

## Visual Element Checklist

### 1. Toggle Button (Chevron)

**Location:** Far left of computed field
**Appearance:**
- → (right arrow) when COLLAPSED
- ↓ (down arrow) when EXPANDED
**Color:** Purple (#8b5cf6)
**Behavior:** Click to toggle expand/collapse

**Visual Check:**
```
✅ CORRECT:  ▼ ☐ 🧮 Total rate of new employee hires
❌ WRONG:       ☐    Total rate of new employee hires
```

---

### 2. Purple Border (Computed Field Indicator)

**Location:** Left side of computed field card
**Appearance:** 3-4px solid line
**Color:** #8b5cf6 (purple/violet)

**Visual Check:**
```
✅ CORRECT:
┌─────────────────────┐
│ ▼ ☐ 🧮 Field Name   │ ← Purple left border
│    Details...       │
└─────────────────────┘

❌ WRONG:
┌─────────────────────┐
│ ☐ Field Name        │ ← No colored border
│    Details...       │
└─────────────────────┘
```

---

### 3. Calculator Icon

**Location:** Inside field name, before text
**Appearance:** 🧮 or calculator symbol
**Color:** Purple (#8b5cf6)

**Visual Check:**
```
✅ CORRECT: 🧮 Total rate of new employee hires
❌ WRONG:      Total rate of new employee hires
```

---

### 4. Dependency Count Badge

**Location:** End of field name
**Appearance:** Small rounded badge with number
**Background Color:** Blue (#3b82f6)
**Text Color:** White
**Content:** Number in parentheses, e.g., (2), (5)

**Visual Check:**
```
✅ CORRECT: Total rate of new employee hires (2)
                                             ↑↑↑
                                        Blue badge

❌ WRONG:   Total rate of new employee hires
                                   (no badge)
```

---

### 5. Dependencies Listed Below

**Location:** Indented below computed field
**Appearance:** Nested under parent, slight indent
**Behavior:** Hidden when collapsed, shown when expanded

**Visual Check:**
```
✅ CORRECT (EXPANDED):
┌──────────────────────┐
│ ▼ 🧮 Computed Field  │
├──────────────────────┤
│   ➘ Dependency 1    │ ← Visible
│   ➘ Dependency 2    │ ← Visible
└──────────────────────┘

✅ CORRECT (COLLAPSED):
┌──────────────────────┐
│ ► 🧮 Computed Field  │
└──────────────────────┘
(Dependencies hidden)

❌ WRONG (FLAT LIST):
┌──────────────────────┐
│ ☐ Computed Field     │
└──────────────────────┘
┌──────────────────────┐
│ ☐ Dependency 1       │ ← Not grouped
└──────────────────────┘
┌──────────────────────┐
│ ☐ Dependency 2       │ ← Not grouped
└──────────────────────┘
```

---

### 6. Arrow Indicator (Dependencies)

**Location:** Left side of dependency field name
**Appearance:** ➘ or "arrow-turn-down-right" icon
**Color:** Gray/muted
**Purpose:** Shows this is a child/dependency field

**Visual Check:**
```
✅ CORRECT:  ➘ ☐ Number of new hires
❌ WRONG:       ☐ Number of new hires
```

---

### 7. Blue Border (Dependency Indicator)

**Location:** Left side of dependency card
**Appearance:** 2-3px solid line, slightly thinner than computed field border
**Color:** #3b82f6 (blue)

**Visual Check:**
```
✅ CORRECT:
  ┌─────────────────┐
  │ ➘ ☐ Dependency  │ ← Blue left border
  │    Details...   │
  └─────────────────┘

❌ WRONG:
  ┌─────────────────┐
  │ ☐ Dependency    │ ← No colored border
  │    Details...   │
  └─────────────────┘
```

---

## Color Reference

### Hex Codes (for DevTools verification)

| Element | Color | Hex Code |
|---------|-------|----------|
| Computed field border | Purple | #8b5cf6 |
| Computed field toggle button | Purple | #8b5cf6 |
| Calculator icon | Purple | #8b5cf6 |
| Dependency border | Blue | #3b82f6 |
| Dependency count badge bg | Blue | #3b82f6 |
| Dependency count badge text | White | #ffffff |
| Arrow indicator | Gray | #6b7280 |

### RGB Values (for comparison)

| Element | RGB |
|---------|-----|
| Purple | rgb(139, 92, 246) |
| Blue | rgb(59, 130, 246) |
| White | rgb(255, 255, 255) |
| Gray | rgb(107, 116, 128) |

---

## Console Messages Reference

### ✅ Success Messages (What You Should See)

```javascript
[DependencyManager] Initializing...
[DependencyManager] Loading dependency data...
[DependencyManager] Loaded dependencies for 5 computed fields
[DependencyManager] Initialized successfully

[SelectedDataPointsPanel] Initializing SelectedDataPointsPanel module...
[SelectedDataPointsPanel] Generating flat HTML with dependency grouping...
[SelectedDataPointsPanel] DOM elements cached

[DependencyManager] Auto-adding 2 dependencies for 401
```

### ❌ Error Messages (What You Should NOT See)

```javascript
// OLD BUG (SHOULD NOT APPEAR):
❌ Uncaught TypeError: Cannot read property 'dependencyMap' of undefined
❌ state is not defined
❌ getDependencyMap is not a function

// IF THESE APPEAR, THE BUG IS NOT FIXED!
```

---

## Browser DevTools Inspection Guide

### Inspect Computed Field Element

1. Right-click computed field → Inspect Element
2. Look for these CSS classes:

```html
<!-- ✅ CORRECT: -->
<div class="topic-group-item selected-point-item is-computed"
     data-field-id="401">
  <button class="dependency-toggle-btn" data-field-id="401">
    <i class="fas fa-chevron-down"></i>
  </button>
  ...
</div>

<!-- ❌ WRONG: -->
<div class="topic-group-item selected-point-item"
     data-field-id="401">
  <!-- No is-computed class, no toggle button -->
  ...
</div>
```

### Inspect Computed Styles

1. Select computed field element
2. Go to "Computed" tab in DevTools
3. Verify:

```
border-left-color: rgb(139, 92, 246) ← Purple #8b5cf6
border-left-width: 4px
border-left-style: solid
```

### Inspect Dependency Element

```html
<!-- ✅ CORRECT: -->
<div class="topic-group-item selected-point-item is-dependency"
     data-field-id="402"
     data-parent-id="401">
  <div class="dependency-indicator">
    <i class="fas fa-arrow-turn-down-right"></i>
  </div>
  ...
</div>

<!-- ❌ WRONG: -->
<div class="topic-group-item selected-point-item"
     data-field-id="402">
  <!-- No is-dependency class, no indicator -->
  ...
</div>
```

---

## Animation/Interaction Reference

### Toggle Button Animation

**Collapsed State:**
```
► (right chevron)
```

**Click to expand:**
```
► → ▼ (rotates 90° clockwise)
```

**Expanded State:**
```
▼ (down chevron)
```

**Click to collapse:**
```
▼ → ► (rotates 90° counter-clockwise)
```

**Timing:** 0.3s smooth transition

---

## Common Issues and How to Identify

### Issue 1: No Visual Elements Appear

**Symptoms:**
- No toggle button
- No purple border
- No calculator icon
- Flat list layout

**Root Cause:** JavaScript error, API not working

**Check:**
1. Open console
2. Look for error: "Cannot read property 'dependencyMap' of undefined"
3. This means the bug fix did NOT work

---

### Issue 2: Elements Appear But Don't Function

**Symptoms:**
- Visual elements present
- Toggle button doesn't work
- No expand/collapse

**Root Cause:** Event listener not attached

**Check:**
1. Click toggle button
2. Check console for errors
3. Verify `setupDependencyToggleListeners()` is called

---

### Issue 3: Incorrect Styling

**Symptoms:**
- Wrong colors
- Missing borders
- Incorrect layout

**Root Cause:** CSS not loaded or conflicting styles

**Check:**
1. Inspect element in DevTools
2. Check if CSS classes are applied
3. Look for CSS file load errors in Network tab

---

## Quick Diagnosis Flow Chart

```
Start: Select a computed field
  ↓
Does it appear in right panel?
  ├─ NO → Check console for JS errors
  │       → Check if field is actually computed (has dependencies)
  └─ YES → Continue
      ↓
  Is there a toggle button (chevron)?
    ├─ NO → ❌ FEATURE BROKEN
    │       → Check console for API errors
    │       → Bug NOT fixed
    └─ YES → Continue
        ↓
    Is there a purple left border?
      ├─ NO → ⚠️  CSS not loading
      │       → Check browser DevTools Styles tab
      └─ YES → Continue
          ↓
      Is there a dependency count badge?
        ├─ NO → ⚠️  Partial rendering issue
        │       → Check console for warnings
        └─ YES → Continue
            ↓
        Click toggle button. Do dependencies collapse?
          ├─ NO → ⚠️  Event listener issue
          │       → Check console for errors
          └─ YES → ✅ FEATURE WORKING!
                   → Take screenshots
                   → Mark test as PASS
```

---

## Screenshot Naming Convention

When capturing screenshots, use these file names:

### Success Screenshots
```
✅ computed-field-expanded.png
✅ computed-field-collapsed.png
✅ multiple-computed-fields.png
✅ console-success-messages.png
✅ devtools-css-verification.png
```

### Failure Screenshots
```
❌ bug-no-toggle-button.png
❌ bug-no-purple-border.png
❌ bug-flat-list-layout.png
❌ bug-console-errors.png
```

---

## Testing Shortcuts

### Fastest Test (30 seconds)
1. Login
2. Go to assign data points
3. Select computed field
4. Check: Toggle button? Purple border? Badge?
5. Result: PASS or FAIL

### Thorough Test (5 minutes)
1. All visual elements present?
2. Toggle works?
3. Multiple fields work?
4. Console has no errors?
5. Styling correct?
6. Result: PASS or FAIL with notes

---

## Support Contact

If you encounter issues during testing:

1. **Take Screenshots**: Capture everything (page + console)
2. **Export Console Log**: Right-click console → Save as...
3. **Note Browser Details**: Chrome/Firefox version, OS
4. **Document Steps**: Exact steps to reproduce
5. **Create Bug Report**: Use template in manual test script

---

**End of Visual Reference Guide**

Use this guide to quickly identify whether the collapsible dependency grouping feature is working correctly or not.

