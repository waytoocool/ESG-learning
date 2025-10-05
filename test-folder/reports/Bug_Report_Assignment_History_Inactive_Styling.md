# Bug Report: Assignment History - Inactive Assignments Missing Faded Styling

**Date:** October 2, 2025
**Reporter:** UI Testing Agent
**Severity:** Medium
**Component:** Assignment History Modal
**Affected Page:** `/admin/assign-data-points-v2`

---

## Summary

In the Assignment History modal, inactive assignments within active versions are not displaying the faded styling (`.superseded` CSS class). This makes it impossible for users to visually distinguish between active and inactive assignments within the same version.

## Environment

- **URL:** `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2`
- **User:** alice@alpha.com (ADMIN)
- **Test Field:** Complete Framework Field 1
- **Browser:** Chromium (Playwright)

---

## Expected Behavior

**Version 2** should display:
- **Alpha HQ** assignment: Normal appearance (series_status='active')
- **Alpha Factory** assignment: Faded appearance with opacity 0.7 (series_status='inactive')

The summary should show "1 Active" assignment, and one of the two displayed assignments should appear faded.

---

## Actual Behavior

**Version 2** displays:
- **Both assignments** appear with normal styling (no fading)
- Summary correctly shows "1 Active"
- Neither assignment has the `.superseded` CSS class applied

**Screenshot Evidence:**

![Version 2 Display Issue](../screenshots/assignment-history-version2-display.png)

*Both Alpha HQ and Alpha Factory assignments appear with identical styling, despite one being inactive*

---

## Technical Analysis

### DOM Investigation Results

**Version 2 Assignment Cards:**
```
Card 1 (Alpha HQ):
- classList: ["assignment-card"]
- Entity: Alpha HQ
- Status: Should be 'active'
- Has .superseded class: NO ❌

Card 2 (Alpha Factory):
- classList: ["assignment-card"]
- Entity: Alpha Factory
- Status: Should be 'inactive'
- Has .superseded class: NO ❌
```

**Version 1 Assignment Cards (Working Correctly):**
```
Card 1 (Alpha HQ):
- classList: ["assignment-card", "superseded"]
- Entity: Alpha HQ
- Has .superseded class: YES ✓
- Computed opacity: 0.7

Card 2 (Alpha Factory):
- classList: ["assignment-card", "superseded"]
- Entity: Alpha Factory
- Has .superseded class: YES ✓
- Computed opacity: 0.7
```

### CSS Rule Verification

The CSS rule exists and works correctly:
```css
.assignment-card.superseded {
    opacity: 0.7;
}
```

This rule is successfully applied to Version 1 cards but is missing from Version 2 cards.

---

## Root Cause

**IDENTIFIED: Property Name Mismatch Between Backend and Frontend**

The issue is a **data contract mismatch** between the backend API and frontend JavaScript:

**Backend API** (`/app/routes/admin_assignment_history.py`, line 194):
```python
'status': assignment.series_status,  # ❌ Sends as 'status'
```

**Frontend JavaScript** (`/app/static/js/admin/assign_data_points/PopupsModule.js`, line 1402):
```javascript
const isAssignmentInactive = assignment.series_status === 'inactive';  // ❌ Looks for 'series_status'
```

The backend sends the assignment status as `status`, but the frontend JavaScript is trying to read `series_status`. This causes the conditional check to always be `undefined`, resulting in the `.superseded` class never being applied to individual inactive assignments.

### Database vs UI Mismatch

**Database State (Expected):**
- Version 2, Entity 2 (Alpha HQ): `series_status='active'`
- Version 2, Entity 3 (Alpha Factory): `series_status='inactive'`

**UI State (Actual):**
- Version 2, Entity 2 (Alpha HQ): No `.superseded` class
- Version 2, Entity 3 (Alpha Factory): No `.superseded` class ❌

---

## Steps to Reproduce

1. Navigate to `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2`
2. Login as `alice@alpha.com / admin123`
3. Search for "Complete Framework Field 1"
4. Click the info icon (ℹ️) on the field
5. Switch to the "Assignment History" tab
6. Observe Version 2 assignments

**Result:** Both assignments appear with identical styling

---

## Impact

### User Impact
- **Confusion:** Users cannot visually distinguish between active and inactive assignments within a version
- **Data Accuracy:** Risk of users assuming all displayed assignments are active
- **Workflow Disruption:** Users may need to check each assignment's status individually

### Severity Justification
- **Medium:** The functionality is broken but has a workaround (manual checking)
- Data is correctly counted (summary shows "1 Active")
- Visual presentation is misleading but doesn't prevent system use

---

## Recommended Fix

**OPTION 1: Fix Backend (Recommended)**

Update the backend API response to use consistent property naming:

**File:** `/app/routes/admin_assignment_history.py`, line 194

**Change:**
```python
# FROM:
'status': assignment.series_status,

# TO:
'series_status': assignment.series_status,
```

This aligns the backend response with what the frontend expects.

---

**OPTION 2: Fix Frontend**

Update the frontend JavaScript to match the backend property name:

**File:** `/app/static/js/admin/assign_data_points/PopupsModule.js`, line 1402

**Change:**
```javascript
// FROM:
const isAssignmentInactive = assignment.series_status === 'inactive';

// TO:
const isAssignmentInactive = assignment.status === 'inactive';
```

---

**RECOMMENDATION:**

Choose **Option 1 (Backend Fix)** because:
1. The property name `series_status` is more descriptive and consistent with the database model
2. The frontend logic is already correctly written with good naming conventions
3. Other parts of the response already use `series_status` terminology (line 201: `'is_active': assignment.series_status == 'active'`)
4. Less risk of breaking other parts that may already be using `series_status`

---

## Additional Notes

### Console Errors Observed
```
Uncaught TypeError: Cannot read properties of null (reading 'children')
    at children (bootstrap.bundle.min.js:5:9306)
```
This error occurs when switching to the Assignment History tab but may be unrelated to the styling issue.

### Related Files
- CSS: Assignment styling rules are correctly defined
- JavaScript: Issue is in the rendering/DOM manipulation logic
- Backend API: Appears to be returning correct `series_status` values

---

## Test Data Reference

**Complete Framework Field 1:**
- Version 2 created: 02/10/2025, 06:05:57
- Version 1 created: 02/10/2025, 06:03:45
- Total assignments: 4 (across both versions)
- Active assignments: 1
- Superseded assignments: 3

---

## Screenshots

1. **assignment-history-version2-display.png** - Shows both assignments without fading
2. **version2-both-assignments-no-fade.png** - Detailed view of the styling issue

All screenshots saved in: `/test-folder/screenshots/`
