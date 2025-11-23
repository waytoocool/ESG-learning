# Bug Report: Bug #2 - Entity Selection Not Working

**Date:** 2025-09-30
**Priority:** 🔴 **P0 - CRITICAL BLOCKER**
**Status:** ❌ **NOT FIXED** (claimed fixed in Round 2, but still broken)
**Affects:** Phase 9.4 - Entity Assignment Modal

---

## Bug Summary

Entity selection in the "Assign Entities" modal is completely broken. Users cannot select entities, making entity assignment functionality impossible.

---

## Steps to Reproduce

1. Navigate to: `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2`
2. Login as: `alice@alpha.com / admin123`
3. Page loads with 17 pre-selected data points
4. Click "🏢 Assign Entities" button
5. Entity assignment modal opens (Bug #1 is fixed ✅)
6. Click on any entity card (e.g., "Alpha Factory")
7. **OBSERVE:** Counter still shows "Selected Entities (0)"
8. **OBSERVE:** No visual feedback on entity card (no highlight/border)
9. **OBSERVE:** Entity selection state not updating

---

## Expected Behavior

When user clicks on an entity card:
1. Entity should be added to selected state
2. Counter should update: "Selected Entities (1)"
3. Entity card should have visual feedback (highlight, border, checkmark)
4. Clicking again should deselect (toggle behavior)
5. Multiple entities can be selected
6. Counter updates accordingly: "Selected Entities (2)", "Selected Entities (3)", etc.

---

## Actual Behavior

When user clicks on an entity card:
1. ❌ Nothing happens
2. ❌ Counter stays at "Selected Entities (0)"
3. ❌ No visual feedback
4. ❌ Entity state not tracked
5. ❌ `PopupsModule.selectedEntities` is **undefined**

---

## Technical Evidence

### JavaScript State Inspection

Evaluated in browser console:
```javascript
{
  selectedEntities: "undefined",  // ❌ State variable is undefined
  entityCardsFound: 49,           // Entity cards exist in DOM
  popupsModuleExists: true        // Module is loaded
}
```

**Root Cause:** `PopupsModule.selectedEntities` is never initialized. The state variable is completely undefined.

---

## Impact

**Business Impact:**
- 🔴 **Users cannot assign data points to entities**
- 🔴 **Entity assignment workflow is completely broken**
- 🔴 **No workaround available - feature is non-functional**

**Technical Impact:**
- Blocks Phase 9.4 approval
- Blocks Phase 9.5 (depends on Phase 9.4)
- Blocks T6.7 test (Entity Assignment SAVE)
- Cannot proceed with modal testing

---

## Root Cause Analysis

### Why It's Broken

**Primary Issue:** State initialization missing

The `PopupsModule.selectedEntities` variable is never initialized when the entity modal opens. It remains `undefined` throughout the modal lifecycle.

**Possible Secondary Issues:**
1. **Click handlers not attached:** Entity cards may not have event listeners
2. **Event delegation broken:** If using event delegation, selector may be incorrect
3. **Handler function missing:** The function that updates `selectedEntities` may not exist
4. **Module initialization order:** PopupsModule may initialize before DOM is ready

---

## Required Fix

The bug-fixer MUST implement the following:

### 1. Initialize Selection State
```javascript
// In openEntityAssignmentModal() or similar function
this.selectedEntities = new Set(); // or []
```

### 2. Attach Click Handlers
```javascript
// Attach click handlers to entity cards
document.querySelectorAll('.entity-card').forEach(card => {
    card.addEventListener('click', (e) => {
        const entityId = card.dataset.entityId;
        this.toggleEntitySelection(entityId);
    });
});
```

### 3. Toggle Selection Function
```javascript
toggleEntitySelection(entityId) {
    if (this.selectedEntities.has(entityId)) {
        this.selectedEntities.delete(entityId);
        // Remove visual feedback
    } else {
        this.selectedEntities.add(entityId);
        // Add visual feedback
    }
    this.updateEntityCounter();
}
```

### 4. Update Counter Display
```javascript
updateEntityCounter() {
    const counter = document.querySelector('#selected-entities-counter');
    const count = this.selectedEntities.size;
    counter.textContent = `Selected Entities (${count})`;
}
```

### 5. Visual Feedback
```javascript
// Add/remove 'selected' class on entity cards
card.classList.toggle('selected');
```

---

## Test Criteria for Fix Verification

The fix is ONLY complete when ALL of the following work:

1. ✅ Click on entity card → Counter updates to "Selected Entities (1)"
2. ✅ Click on second entity → Counter updates to "Selected Entities (2)"
3. ✅ Click on first entity again → Counter updates to "Selected Entities (1)" (deselection)
4. ✅ Entity cards show visual feedback when selected (highlight/border)
5. ✅ `PopupsModule.selectedEntities` is properly initialized (Set or Array)
6. ✅ No console errors

---

## Previous Fix Attempts

### Round 2 (Failed)
- **Claimed:** "Fixed entity selection click handlers"
- **Reality:** Bug was NOT actually fixed
- **Issue:** State initialization was missing, not just click handlers

---

## Files to Check

Based on console logs, the bug is likely in:
- `app/static/js/admin/assign_data_points/popups.js`
- Specifically in the `openEntityAssignmentModal()` function
- And/or the entity card click handler attachment logic

---

## Verification Steps for Bug-Fixer

**Before submitting fix:**

1. Open page: `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2`
2. Login as: `alice@alpha.com / admin123`
3. Click "Assign Entities" button
4. Click "Alpha Factory" entity
5. **VERIFY:** Counter shows "Selected Entities (1)"
6. Click "Alpha HQ" entity
7. **VERIFY:** Counter shows "Selected Entities (2)"
8. Click "Alpha Factory" again
9. **VERIFY:** Counter shows "Selected Entities (1)"
10. Open browser console
11. Type: `window.PopupsModule.selectedEntities`
12. **VERIFY:** Shows Set or Array with selected entity IDs

**If all steps pass, then notify ui-testing-agent for Round 4 verification.**

---

## Screenshots

**Evidence of Bug:**
- `screenshots/03-bug2-still-broken-entity-selection-failed.png`
  - Shows counter at "Selected Entities (0)" after clicking entity
  - No visual feedback on clicked entity

---

## Priority Justification

**Why P0:**
- Blocks entire entity assignment feature
- No workaround available
- Prevents users from completing core workflow
- Blocks Phase 9.4 approval
- Blocks Phase 9.5
- Critical business functionality impacted

---

## Next Actions

1. **Bug-fixer:** Implement fix following "Required Fix" section above
2. **Bug-fixer:** Test locally using "Verification Steps" section
3. **Bug-fixer:** Notify ui-testing-agent when ready for Round 4
4. **ui-testing-agent:** Run Round 4 verification focused on Bug #2
5. **If Round 4 passes:** Approve Phase 9.4 and proceed
6. **If Round 4 fails:** Return to step 1

---

**Status:** 🔴 **OPEN - CRITICAL**
**Assigned To:** bug-fixer
**Blocks:** Phase 9.4 Approval, Phase 9.5

---

**Report Created:** 2025-09-30
**Last Updated:** 2025-09-30
**Reporter:** ui-testing-agent
