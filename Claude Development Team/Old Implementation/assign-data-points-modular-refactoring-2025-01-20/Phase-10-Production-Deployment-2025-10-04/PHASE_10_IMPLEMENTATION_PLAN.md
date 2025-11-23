# Phase 10: Production Deployment - Implementation Plan

**Date**: 2025-10-04
**Status**: IN PROGRESS
**Purpose**: Deploy NEW modular page to production URL

---

## Overview

Phase 10 marks the final step of the modular refactoring project: making the NEW modular page the default production page while safely preserving the OLD legacy page as backup.

### Key Changes

1. **Route Update**: `/assign-data-points-v2` → `/assign-data-points` (production URL)
2. **Backup OLD Route**: `/assign_data_points_redesigned` → backup (preserved, not removed)
3. **File Preservation**: Keep `assignment_history.js` (still referenced)

---

## Current State

### Routes
- **OLD** (Legacy): `/admin/assign_data_points_redesigned` → `assign_data_points_redesigned.html`
- **NEW** (Modular): `/admin/assign-data-points-v2` → `assign_data_points_v2.html`

### Files to Backup (NOT Remove)
- `app/static/js/admin/assign_data_points_redesigned.js` (4,973 lines)
- `app/static/js/admin/assign_data_points_import.js` (385 lines)
- `app/static/js/admin/assign_data_point_ConfirmationDialog.js` (359 lines)
- ~~`app/static/js/admin/assignment_history.js`~~ **KEEP - Still referenced**

---

## Implementation Steps

### Step 1: Update Main Production Route ✅

**File**: `app/routes/admin_assign_data_points.py`

**Change**:
```python
# BEFORE
@admin_assign_data_points_bp.route('/assign-data-points-v2', methods=['GET'])
def assign_data_points_v2():
    ...

# AFTER
@admin_assign_data_points_bp.route('/assign-data-points', methods=['GET'])
def assign_data_points():  # Renamed from assign_data_points_v2
    ...
```

**Impact**:
- Production URL becomes: `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points`
- NEW modular page is now the default

---

### Step 2: Preserve OLD Route as Backup ✅

**File**: `app/routes/admin.py`

**Change**:
```python
# BEFORE
@admin_bp.route('/assign_data_points_redesigned', methods=['GET'])
def assign_data_points_redesigned():
    ...

# AFTER
@admin_bp.route('/assign_data_points_redesigned_backup', methods=['GET'])
def assign_data_points_redesigned_backup():
    """BACKUP: Original legacy page preserved for emergency rollback"""
    ...
```

**Impact**:
- OLD page still accessible at: `/admin/assign_data_points_redesigned_backup`
- Can rollback if critical issues found
- OLD template and JS files preserved

---

### Step 3: Backup JavaScript Files ✅

**Files to Rename** (add `.backup` extension):

```bash
# Static JS files
mv assign_data_points_redesigned.js → assign_data_points_redesigned.js.backup
mv assign_data_points_import.js → assign_data_points_import.js.backup
mv assign_data_point_ConfirmationDialog.js → assign_data_point_ConfirmationDialog.js.backup
```

**Files to KEEP** (still referenced):
- `assignment_history.js` - **NO CHANGES**

**CSS Files** (backup):
```bash
# Static CSS files
mv assign_data_points_redesigned.css → assign_data_points_redesigned.css.backup
```

---

### Step 4: Update Template References (if needed)

**Check**: `app/templates/admin/assign_data_points_redesigned.html`

Ensure OLD template references the backup JS files if still loading them:
```html
<!-- Update script tags to .backup files if needed -->
<script src="{{ url_for('static', filename='js/admin/assign_data_points_redesigned.js.backup') }}"></script>
```

---

## Rollback Plan

If critical issues found in production:

### Quick Rollback (5 minutes)
1. Revert route in `admin_assign_data_points.py`:
   ```python
   @admin_assign_data_points_bp.route('/assign-data-points-v2', methods=['GET'])
   ```
2. Point main route back to OLD:
   ```python
   # In admin.py, restore original route:
   @admin_bp.route('/assign_data_points_redesigned', methods=['GET'])
   ```

### Full Rollback (10 minutes)
1. Restore all `.backup` files (remove `.backup` extension)
2. Revert all route changes
3. Restart application

---

## Testing Checklist

After deployment, verify:

### Functional Testing
- [ ] Navigate to `/admin/assign-data-points` (should show NEW modular page)
- [ ] All modules initialize correctly (check console logs)
- [ ] Framework selection works
- [ ] Data point selection works
- [ ] Entity assignment modal works
- [ ] Configuration modal works
- [ ] Export functionality works
- [ ] Import functionality works
- [ ] Assignment History tab works

### Backup Route Testing
- [ ] Navigate to `/admin/assign_data_points_redesigned_backup` (should show OLD page)
- [ ] OLD page still functional
- [ ] OLD page JS files load from `.backup` files

### Production URLs
- [ ] Main production URL: `/admin/assign-data-points` → NEW modular page ✓
- [ ] Backup URL: `/admin/assign_data_points_redesigned_backup` → OLD legacy page ✓

---

## Success Criteria

Phase 10 is **COMPLETE** when:
- ✅ NEW modular page is at production URL `/admin/assign-data-points`
- ✅ OLD legacy page preserved as backup
- ✅ All files backed up (not removed)
- ✅ `assignment_history.js` kept intact
- ✅ All functionality verified working
- ✅ Rollback plan tested and ready

---

## Files Modified

### Routes
1. `/app/routes/admin_assign_data_points.py` - Main route update
2. `/app/routes/admin.py` - Backup route rename

### Static Files (Renamed to .backup)
1. `/app/static/js/admin/assign_data_points_redesigned.js.backup`
2. `/app/static/js/admin/assign_data_points_import.js.backup`
3. `/app/static/js/admin/assign_data_point_ConfirmationDialog.js.backup`
4. `/app/static/css/admin/assign_data_points_redesigned.css.backup`

### Static Files (KEPT - No Changes)
- `/app/static/js/admin/assignment_history.js` ✓

### Templates (Updated if needed)
- `/app/templates/admin/assign_data_points_redesigned.html` - Update script references to .backup files

---

## Post-Deployment Monitoring

### Week 1
- Monitor error logs for any NEW page issues
- Collect user feedback
- Track performance metrics
- Compare usage: NEW vs OLD backup

### Week 2
- Analyze data integrity
- Verify all features working as expected
- Plan for OLD page deprecation (if all good)

### Month 1
- If no issues, plan to remove OLD backup route
- Archive backup files to documentation folder
- Update user documentation

---

**Status**: Ready for implementation
**Risk Level**: LOW (OLD page preserved as backup)
**Rollback Time**: < 10 minutes
