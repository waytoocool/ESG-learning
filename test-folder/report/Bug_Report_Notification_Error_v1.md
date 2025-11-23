# Bug Report: JavaScript Error in Dependency Auto-Add Notification

**Bug ID:** BUG-001
**Date Reported:** 2025-11-10
**Reported By:** UI Testing Agent
**Severity:** Minor
**Priority:** Medium
**Status:** New
**Environment:** Test Company Alpha - Admin Interface

---

## Summary

A JavaScript TypeError occurs when the DependencyManager module attempts to display a notification to users after automatically adding dependencies for a computed field. This prevents users from receiving confirmation feedback about the automatic dependency selection.

---

## Environment Details

- **URL:** http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points
- **User Role:** ADMIN
- **Browser:** Playwright (Chrome-based)
- **Affected File:** `/static/js/admin/assign_data_points/DependencyManager.js`
- **Version:** v1762748475

---

## Steps to Reproduce

1. Login as admin user (alice@alpha.com)
2. Navigate to `/admin/assign-data-points`
3. Expand all topics to view data points
4. Locate a computed field (e.g., "Total rate of new employee hires..." in GRI 401 topic)
5. Click the "+" button to add the computed field to selection
6. Open browser developer console

---

## Expected Behavior

When a computed field is selected and its dependencies are automatically added:
1. Dependencies should be added to the selection (this works)
2. A notification should be displayed to the user informing them that dependencies were automatically added
3. The notification should indicate how many dependencies were added
4. No JavaScript errors should appear in the console

---

## Actual Behavior

1. Dependencies are correctly added to the selection ✅
2. No notification is displayed to the user ❌
3. JavaScript TypeError appears in browser console ❌

**Console Error:**
```javascript
TypeError: PopupManager.showNotification is not a function
    at Object.showAutoAddNotification (http://test-company-alpha.127-0-0-1.nip.io:8000/static/js/admin/assign_data_points/DependencyManager.js?v=1762748475:300:30)
    at Object.handleFieldSelection (http://test-company-alpha.127-0-0-1.nip.io:8000/static/js/admin/assign_data_points/DependencyManager.js?v=1762748475:200:22)
```

---

## Impact Analysis

### User Impact
- **Severity:** Low
- **Functional Impact:** None - core functionality works correctly
- **User Experience Impact:** Moderate - users miss confirmation feedback
- **Frequency:** Occurs every time a computed field is selected

### System Impact
- Does not cause system failure
- Does not prevent feature from working
- Does not corrupt data
- Does not affect performance

### Business Impact
- Users may be confused about whether dependencies were added
- Reduces transparency of automatic operations
- May lead to user uncertainty about system behavior

---

## Root Cause Analysis

The error occurs because `DependencyManager.js` attempts to call `PopupManager.showNotification()` but this method either:
1. Does not exist in the PopupManager module
2. Has a different name
3. Has not been properly exported/exposed

**Code Location:** `DependencyManager.js` line 300 in `showAutoAddNotification()` function

**Probable Cause:** Method name mismatch or API change in PopupManager module

---

## Technical Details

### Call Stack
```
TypeError: PopupManager.showNotification is not a function
    at Object.showAutoAddNotification
        (DependencyManager.js:300:30)
    at Object.handleFieldSelection
        (DependencyManager.js:200:22)
```

### Affected Module
- **Module:** DependencyManager
- **Function:** `showAutoAddNotification()`
- **Line:** 300

### Dependencies
- **Required Module:** PopupManager
- **Expected Method:** `showNotification()`
- **Status:** Method not found

---

## Evidence

### Console Log Excerpt
```
[LOG] [DependencyManager] Auto-adding 2 dependencies for 0f944ca1-4052-45c8-8e9e-3fbcf84ba44c
[LOG] [AppEvents] state-dataPoint-added: {field_id: b27c0050-82cd-46ff-aad6-b4c9156539e8...}
[LOG] [AppEvents] state-dataPoint-added: {field_id: 43267341-4891-40d9-970c-8d003aab8302...}
TypeError: PopupManager.showNotification is not a function
    at Object.showAutoAddNotification...
```

### Successful Operations (Before Error)
- Dependency loading: ✅ Success
- Field selection: ✅ Success
- Dependency addition: ✅ Success
- State updates: ✅ Success
- UI rendering: ✅ Success
- **Only notification fails:** ❌ Error

---

## Suggested Fix

### Option 1: Correct Method Name (Recommended)
Review the PopupManager module and identify the correct method name for showing notifications. Update the call in DependencyManager.js accordingly.

**Example:**
```javascript
// Current (broken):
PopupManager.showNotification(message);

// Possible fix:
PopupManager.show(message);
// OR
window.PopupManager.showNotification(message);
// OR
PopupManager.showMessage(message);
```

### Option 2: Add Missing Method
If the PopupManager module doesn't have a showNotification method, add it to maintain the expected API.

### Option 3: Use Global Popup System
Check if there's a global popup/notification system available and use that instead.

---

## Recommended Testing After Fix

1. **Functional Test:**
   - Select a computed field
   - Verify notification appears
   - Verify notification message is clear and helpful
   - Verify no console errors

2. **Content Test:**
   - Check notification shows correct dependency count
   - Check notification indicates which field's dependencies were added
   - Check notification is dismissible

3. **Regression Test:**
   - Verify core dependency auto-add still works
   - Verify multiple computed fields work correctly
   - Verify UI updates correctly

---

## Workaround

**For Users:**
No workaround needed. Users can verify dependencies were added by:
1. Checking the selection count in the header (increases by dependency count + 1)
2. Viewing the Selected Data Points panel
3. Seeing the newly added items in the list

**For Developers:**
Temporarily comment out the notification call to eliminate the error, or catch the error silently until the fix is implemented.

---

## Related Issues

- None currently identified
- This appears to be an isolated issue with the notification system integration

---

## Additional Notes

- The PopupManager module itself initializes successfully: `✅ Global PopupManager initialized`
- Other parts of the application may use PopupManager successfully
- This may indicate a scope or timing issue with how DependencyManager accesses PopupManager
- Consider adding error handling around notification calls to prevent console errors from user-facing features

---

## Attachments

- See Testing Summary document for full context
- Console logs available in Testing_Summary_Computed_Field_Dependencies_v1.md
- Screenshots showing successful dependency addition despite error

---

**Report Status:** Ready for Development Review
**Next Steps:** Assign to frontend developer for investigation and fix
