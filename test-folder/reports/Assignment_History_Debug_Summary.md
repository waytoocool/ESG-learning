# Assignment History Debug Summary

**Date:** October 2, 2025
**Tester:** UI Testing Agent
**Test Field:** Complete Framework Field 1
**Issue:** Inactive assignments not showing faded styling in Version 2

---

## Quick Summary

The assignment history modal is not displaying faded styling for inactive assignments within active versions due to a **property name mismatch** between the backend API and frontend JavaScript.

- **Backend sends:** `status`
- **Frontend expects:** `series_status`
- **Result:** Conditional styling check fails, `.superseded` class is not applied

---

## Test Results

### ✅ What Works

1. **Active Count Display** - Correctly shows "1 Active" in summary
2. **Superseded Versions** - Version 1 displays both cards with faded styling correctly
3. **CSS Rule** - `.assignment-card.superseded { opacity: 0.7; }` exists and functions
4. **Frontend Logic** - JavaScript correctly checks `series_status === 'inactive'` on line 1402

### ❌ What Doesn't Work

1. **Version 2 Display** - Both Alpha HQ and Alpha Factory cards show normal styling
2. **Property Access** - `assignment.series_status` is `undefined` due to backend sending `assignment.status`
3. **Visual Feedback** - Users cannot distinguish active from inactive assignments

---

## Technical Details

### Backend API Response
**File:** `/app/routes/admin_assignment_history.py`
**Line:** 194

```python
'status': assignment.series_status,  # ❌ Wrong property name
```

### Frontend JavaScript Check
**File:** `/app/static/js/admin/assign_data_points/PopupsModule.js`
**Line:** 1402-1403

```javascript
const isAssignmentInactive = assignment.series_status === 'inactive';  // ❌ Undefined
const cardClass = isAssignmentInactive ? 'superseded' : (isActive ? '' : 'superseded');
```

---

## The Fix

### Recommended Solution: Update Backend

**File:** `/app/routes/admin_assignment_history.py`
**Line:** 194

```python
# Change FROM:
'status': assignment.series_status,

# Change TO:
'series_status': assignment.series_status,
```

**Why this fix:**
- Aligns with frontend expectations
- More descriptive property name
- Consistent with other parts of the codebase
- Lower risk of breaking changes

---

## Evidence

### DOM Inspection Results

**Version 2 Cards (Broken):**
```
Card 1 (Alpha HQ):     classList: ["assignment-card"]           ❌
Card 2 (Alpha Factory): classList: ["assignment-card"]           ❌
```

**Version 1 Cards (Working):**
```
Card 1 (Alpha HQ):     classList: ["assignment-card", "superseded"] ✓
Card 2 (Alpha Factory): classList: ["assignment-card", "superseded"] ✓
```

### Screenshots

1. **assignment-history-version2-display.png** - Main view showing both cards without fading
2. **version2-both-assignments-no-fade.png** - Close-up of the styling issue

All screenshots saved in: `/test-folder/screenshots/`

---

## Test Environment

- **URL:** `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2`
- **User:** alice@alpha.com (ADMIN)
- **Company:** Test Company Alpha
- **Browser:** Chromium (Playwright MCP)

---

## Database State

**Version 2 Expected State:**
- Entity 2 (Alpha HQ): `series_status='active'` → Normal display ✓
- Entity 3 (Alpha Factory): `series_status='inactive'` → Should be faded ❌

**Summary Stats:**
- Total: 4 assignments
- Active: 1
- Superseded: 3

---

## Impact Assessment

### Severity: Medium

**User Impact:**
- Users cannot visually distinguish active from inactive assignments in active versions
- Risk of confusion about which assignments are currently in effect
- Manual checking required to verify assignment status

**Business Logic:**
- Data is correctly tracked in database
- Summary counts are accurate
- Only visual presentation is affected

### Workaround

Users can check the active count (shows "1 Active" correctly) but must manually determine which specific assignment is active.

---

## Related Files

1. **Backend:**
   - `/app/routes/admin_assignment_history.py` (line 194)

2. **Frontend:**
   - `/app/static/js/admin/assign_data_points/PopupsModule.js` (lines 1402-1403)

3. **CSS:**
   - CSS rule exists and works correctly

---

## Next Steps

1. Apply the recommended backend fix (change `'status'` to `'series_status'`)
2. Test the assignment history modal after the fix
3. Verify faded styling appears for Alpha Factory in Version 2
4. Close this bug report

---

## Testing Checklist

After fix is applied:
- [ ] Version 2 shows Alpha HQ with normal styling
- [ ] Version 2 shows Alpha Factory with faded styling (opacity: 0.7)
- [ ] Active count still shows "1 Active"
- [ ] Version 1 assignments remain faded
- [ ] No JavaScript console errors
