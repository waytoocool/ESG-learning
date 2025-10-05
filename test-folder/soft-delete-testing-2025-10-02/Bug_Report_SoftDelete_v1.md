# Bug Report: Soft Delete Not Implemented

**Bug ID**: SOFT-DELETE-001
**Date Reported**: October 2, 2025
**Reported By**: UI Testing Agent
**Priority**: P0 (Critical)
**Severity**: High
**Status**: Open
**Environment**: test-company-alpha, assign-data-points-v2 page

---

## Summary

The delete button on the assign-data-points-v2 page performs a HARD DELETE instead of a SOFT DELETE. Items are completely removed from the UI state rather than being marked as inactive, making them unrecoverable and preventing the "Show Inactive" toggle from functioning correctly.

---

## Steps to Reproduce

1. Navigate to `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2`
2. Log in as admin (alice@alpha.com / admin123)
3. Wait for page to load existing assignments (e.g., 20 data points)
4. Locate any data point in the "Selected Data Points" panel
5. Click the delete button (red trash icon) on the data point
6. Observe the behavior

**Expected Result**:
- Item should be marked as inactive (`is_active: false`)
- Item should remain in the list with visual indicators (reduced opacity, badge, etc.)
- Counter should update to show "19 active, 1 inactive" or similar
- "Show Inactive" button should toggle visibility of the inactive item

**Actual Result**:
- Item is completely removed from the UI
- Item count decreases from 20 to 19
- No inactive items are created
- "Show Inactive" button has no effect (no inactive items to show)
- Item is unrecoverable without page refresh

---

## Impact

**User Impact**:
- **Data Loss Risk**: Accidental deletion cannot be undone
- **No Recovery**: Users must refresh page or re-import data to recover
- **Audit Trail Missing**: No record of deleted/deactivated items
- **Workflow Disruption**: Cannot temporarily deactivate items

**Business Impact**:
- **Compliance Issue**: No audit trail for data changes
- **Data Integrity**: Risk of permanent data loss
- **User Trust**: Users may lose confidence in the system
- **Support Burden**: Increased support requests for data recovery

---

## Root Cause

**File**: `/app/static/js/admin/assign_data_points/SelectedDataPointsPanel.js`
**Method**: `removeItem(fieldId)`
**Lines**: 243-260

### Current Implementation (INCORRECT):

```javascript
removeItem(fieldId) {
    console.log('[SelectedDataPointsPanel] Removing item:', fieldId);

    if (!this.selectedItems.has(fieldId)) {
        console.log('[SelectedDataPointsPanel] Item not found for removal:', fieldId);
        return;
    }

    this.selectedItems.delete(fieldId);  // ❌ HARD DELETE - completely removes from Map

    // Update display
    this.updateDisplay();

    AppEvents.emit('selected-panel-item-removed', {
        fieldId: fieldId,
        count: this.selectedItems.size
    });

    AppEvents.emit('datapoint-removed', { fieldId: fieldId });
    AppEvents.emit('selected-panel-count-changed', { count: this.selectedItems.size });
}
```

### Issue Analysis:

1. **Line 251**: `this.selectedItems.delete(fieldId)` - Completely removes item from Map
2. **Missing**: No `is_active` flag handling
3. **Missing**: No filter logic in `updateDisplay()` to show/hide inactive items
4. **Missing**: No visual styling for inactive items

---

## Proposed Fix

### Solution 1: Modify removeItem() to Mark as Inactive

```javascript
removeItem(fieldId) {
    console.log('[SelectedDataPointsPanel] Marking item as inactive:', fieldId);

    if (!this.selectedItems.has(fieldId)) {
        console.log('[SelectedDataPointsPanel] Item not found:', fieldId);
        return;
    }

    // Get the item and mark it as inactive (SOFT DELETE)
    const item = this.selectedItems.get(fieldId);
    item.is_active = false;
    item.deleted_at = new Date().toISOString();

    // Keep item in Map, but marked as inactive
    this.selectedItems.set(fieldId, item);

    // Update display (will filter based on showInactive state)
    this.updateDisplay();

    // Emit events
    AppEvents.emit('selected-panel-item-deactivated', {
        fieldId: fieldId,
        activeCount: this.getActiveCount(),
        totalCount: this.selectedItems.size
    });

    AppEvents.emit('datapoint-deactivated', { fieldId: fieldId });
    AppEvents.emit('selected-panel-count-changed', { count: this.getActiveCount() });
}

// Helper method to count active items
getActiveCount() {
    return Array.from(this.selectedItems.values())
        .filter(item => item.is_active !== false).length;
}
```

### Solution 2: Update Display Logic to Filter Inactive Items

Modify the rendering methods to respect `showInactive` state:

```javascript
updateDisplay() {
    console.log('[SelectedDataPointsPanel] Updating display...');

    // Filter items based on showInactive state
    const itemsToDisplay = Array.from(this.selectedItems.entries())
        .filter(([fieldId, item]) => {
            // Show all items if showInactive is true
            if (this.showInactive) return true;
            // Otherwise, only show active items
            return item.is_active !== false;
        });

    // Update count display
    const activeCount = this.getActiveCount();
    const totalCount = this.selectedItems.size;
    const inactiveCount = totalCount - activeCount;

    this.updateCount(activeCount, inactiveCount);

    // Render items...
    this.renderItems(itemsToDisplay);

    // Update empty state...
    this.updateEmptyState(itemsToDisplay.length === 0);
}
```

### Solution 3: Add Visual Indicators for Inactive Items

Update the rendering to add inactive styling:

```javascript
renderItemCard(fieldId, item) {
    const isInactive = item.is_active === false;

    const card = document.createElement('div');
    card.className = 'selected-point-item';
    if (isInactive) {
        card.classList.add('inactive-item');  // Add inactive class
    }

    card.innerHTML = `
        <div class="item-header">
            <h6 class="item-title ${isInactive ? 'text-muted' : ''}">
                ${item.field_name}
                ${isInactive ? '<span class="badge badge-secondary ml-2">INACTIVE</span>' : ''}
            </h6>
        </div>
        <!-- rest of card HTML -->
    `;

    return card;
}
```

### Solution 4: Add CSS for Inactive Items

```css
/* Add to assign_data_points_v2.css or relevant stylesheet */
.selected-point-item.inactive-item {
    opacity: 0.6;
    background-color: #f8f9fa;
    border-left: 3px solid #6c757d;
}

.selected-point-item.inactive-item .item-title {
    text-decoration: line-through;
    color: #6c757d;
}

.selected-point-item.inactive-item .badge {
    background-color: #6c757d;
}
```

---

## Additional Requirements

### 1. Update Toggle Button Handler

```javascript
handleToggleInactive() {
    console.log('[SelectedDataPointsPanel] Toggle Inactive clicked');

    // Toggle the state
    this.showInactive = !this.showInactive;

    // Update button text and icon
    const button = this.elements.toggleInactiveButton;
    if (this.showInactive) {
        button.innerHTML = '<i class="fas fa-eye-slash"></i> Hide Inactive';
        button.classList.add('active');
    } else {
        button.innerHTML = '<i class="fas fa-eye"></i> Show Inactive';
        button.classList.remove('active');
    }

    // Re-render the display with new filter
    this.updateDisplay();

    // Emit event
    const visibleCount = Array.from(this.selectedItems.values())
        .filter(item => this.showInactive || item.is_active !== false).length;

    AppEvents.emit('inactive-toggle-changed', {
        showInactive: this.showInactive,
        visibleItemCount: visibleCount
    });
}
```

### 2. Add Restore Functionality (Optional Enhancement)

```javascript
handleRestoreClick(fieldId) {
    console.log('[SelectedDataPointsPanel] Restore clicked for:', fieldId);

    const item = this.selectedItems.get(fieldId);
    if (!item) return;

    // Restore item to active state
    item.is_active = true;
    delete item.deleted_at;

    this.selectedItems.set(fieldId, item);
    this.updateDisplay();

    AppEvents.emit('datapoint-restored', { fieldId: fieldId });
}
```

---

## Testing Requirements

After implementing the fix, verify:

1. **Soft Delete**:
   - [ ] Click delete button marks item as inactive (not removed)
   - [ ] Item remains in selectedItems Map
   - [ ] Item has `is_active: false` flag
   - [ ] Item has `deleted_at` timestamp

2. **Visual Indicators**:
   - [ ] Inactive items have reduced opacity (0.6)
   - [ ] Inactive items show "INACTIVE" badge
   - [ ] Inactive items have strikethrough or muted text
   - [ ] Inactive items have different background/border

3. **Show/Hide Toggle**:
   - [ ] "Show Inactive" displays all items (active + inactive)
   - [ ] "Hide Inactive" displays only active items
   - [ ] Button text/icon updates correctly
   - [ ] Item count reflects visible items

4. **Data Persistence**:
   - [ ] Inactive state persists after page refresh
   - [ ] Backend API receives `is_active: false` on save
   - [ ] Database records inactive status

5. **Edge Cases**:
   - [ ] All items inactive shows appropriate message
   - [ ] Toggle works with 0 inactive items
   - [ ] Delete last active item works correctly
   - [ ] Restore inactive item works correctly

---

## Related Issues

- **Show Inactive Toggle** (depends on this fix)
- **Inactive Visual Indicators** (depends on this fix)
- **Backend Soft Delete API** (needs verification)
- **Reference Implementation** (may have same issue)

---

## Attachments

**Screenshots**:
1. `page-2025-10-02T09-51-33-153Z.png` - Before delete (20 items)
2. `page-2025-10-02T09-52-12-546Z.png` - After delete (19 items, item removed)
3. `page-2025-10-02T09-52-27-826Z.png` - Show/Hide toggle active

**Test Report**: `Testing_Summary_SoftDelete_v1.md`

**Code Files**:
- `/app/static/js/admin/assign_data_points/SelectedDataPointsPanel.js`
- `/app/static/js/admin/assign_data_points/ServicesModule.js`
- `/app/templates/admin/assign_data_points_v2.html`

---

## Workaround

**Current Workaround for Users**:
1. Do NOT use delete button unless you want permanent removal
2. If accidentally deleted, refresh page to reload from backend
3. Consider using Export before making deletions (as backup)
4. Use Save All frequently to persist changes

**Note**: This workaround is not sustainable and highlights the critical nature of this bug.

---

## Priority Justification

**Why P0 (Critical)**:
- Blocks core functionality (soft delete is expected behavior)
- Data loss risk for users
- No recovery mechanism
- Compliance/audit concerns
- Affects all users of the assign-data-points-v2 page
- Cannot proceed to production without fix

**Estimated Fix Time**: 4-6 hours (including testing)

**Recommended Action**: Implement soft delete before any further feature development on this page.

---

**Status**: Open
**Assigned To**: Backend Developer / UI Developer
**Target Resolution**: Next sprint
**Last Updated**: October 2, 2025
