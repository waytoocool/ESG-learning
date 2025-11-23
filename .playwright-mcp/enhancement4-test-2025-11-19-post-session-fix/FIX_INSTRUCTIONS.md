# Quick Fix Instructions - P0 Blocker

**Issue:** ESGData constructor doesn't accept is_draft parameter
**Impact:** Data submission fails with 500 error
**Fix Time:** 10 minutes

---

## Files to Modify (7 changes across 3 files)

### File 1: submission_service.py

**Location:** `app/services/user_v2/bulk_upload/submission_service.py`

**Line 100:**
```python
# BEFORE:
new_entry = ESGData(
    entity_id=row['entity_id'],
    field_id=row['field_id'],
    company_id=current_user.company_id,
    assignment_id=row['assignment_id'],
    raw_value=str(row['parsed_value']),
    reporting_date=row['reporting_date'],
    dimension_values=row.get('dimensions'),
    notes=row.get('notes'),
    is_draft=False  # ← REMOVE THIS LINE
)

# AFTER:
new_entry = ESGData(
    entity_id=row['entity_id'],
    field_id=row['field_id'],
    company_id=current_user.company_id,
    assignment_id=row['assignment_id'],
    raw_value=str(row['parsed_value']),
    reporting_date=row['reporting_date'],
    dimension_values=row.get('dimensions'),
    notes=row.get('notes')
)
```

---

### File 2: validation_service.py

**Location:** `app/services/user_v2/bulk_upload/validation_service.py`

**Line 59:**
```python
# BEFORE:
existing = ESGData.query.filter_by(
    field_id=row['field_id'],
    entity_id=row['entity_id'],
    reporting_date=row['reporting_date'],
    is_draft=False  # ← REMOVE THIS LINE
).first()

# AFTER:
existing = ESGData.query.filter_by(
    field_id=row['field_id'],
    entity_id=row['entity_id'],
    reporting_date=row['reporting_date']
).filter(ESGData.is_draft == False).first()
```

**Note:** For query filters, use `.filter(ESGData.is_draft == False)` instead of `filter_by(is_draft=False)` as this is more explicit and works with boolean column comparisons.

---

### File 3: template_service.py

**Location:** `app/services/user_v2/bulk_upload/template_service.py`

There are **5 occurrences** in this file. Search for `is_draft=False` and apply the same fix pattern:

#### Location 1 (around line 72):
```python
# BEFORE:
existing = ESGData.query.filter_by(
    # ... filters ...
    is_draft=False  # ← REMOVE
).first()

# AFTER:
existing = ESGData.query.filter_by(
    # ... filters ...
).filter(ESGData.is_draft == False).first()
```

#### Location 2 (around line 82):
```python
# BEFORE:
.filter_by(is_draft=False)  # ← REMOVE

# AFTER:
.filter(ESGData.is_draft == False)
```

#### Location 3 (around line 98):
```python
# BEFORE:
.filter_by(is_draft=False)  # ← REMOVE

# AFTER:
.filter(ESGData.is_draft == False)
```

#### Location 4 (around line 174):
```python
# BEFORE:
.filter_by(is_draft=False)  # ← REMOVE

# AFTER:
.filter(ESGData.is_draft == False)
```

#### Location 5 (around line 191):
```python
# BEFORE:
.filter_by(is_draft=False)  # ← REMOVE

# AFTER:
.filter(ESGData.is_draft == False)
```

---

## Quick Find & Replace Strategy

### For submission_service.py (line 100):
**Find:**
```python
    notes=row.get('notes'),
    is_draft=False
)
```

**Replace with:**
```python
    notes=row.get('notes')
)
```

### For all query filters (validation_service.py and template_service.py):
**Find:**
```python
is_draft=False
```

**In filter_by() context, replace with:**
Add `.filter(ESGData.is_draft == False)` after the filter_by() call

---

## Verification After Fix

### Test Command:
```bash
cd "/Users/prateekgoyal/Desktop/Prateek/ESG DataVault Development/Claude/sakshi-learning"
python3 .playwright-mcp/enhancement4-test-2025-11-19-post-session-fix/test-scripts/session_fix_verification.py
```

### Expected Output:
```
✅ SESSION FIX VERIFIED - ALL CHECKS PASSED
   - Submission succeeded without 'No validated rows' error
   - 3 entries found in database
   - Session persistence fix is working correctly

🎉 READY TO PROCEED TO COMPREHENSIVE TESTING
```

### Database Check:
```bash
cd "/Users/prateekgoyal/Desktop/Prateek/ESG DataVault Development/Claude/sakshi-learning"
python3 -c "
import sqlite3
conn = sqlite3.connect('instance/esg_data.db')
cursor = conn.cursor()
cursor.execute(\"SELECT COUNT(*) FROM esg_data WHERE notes LIKE '%SESSION-FIX-TEST%'\")
count = cursor.fetchone()[0]
print(f'Test entries in database: {count}')
print('Expected: 3')
print('Status: PASS' if count == 3 else 'Status: FAIL')
conn.close()
"
```

---

## Why This Works

**Original Problem:**
- ESGData.__init__() doesn't have is_draft parameter
- Code tries to pass is_draft=False to constructor
- Python raises TypeError

**The Fix:**
- For object creation: Remove is_draft parameter, rely on column default
- For queries: Use .filter() instead of filter_by() for boolean comparisons

**Column Default:**
```python
# From esg_data.py line 33:
is_draft = db.Column(db.Boolean, default=False, nullable=False)
```

When you create ESGData without specifying is_draft, SQLAlchemy automatically uses the column default (False).

**Existing Pattern:**
This matches how draft_service.py creates ESGData objects:
```python
# draft_service.py lines 119-132
new_draft = ESGData(...)  # No is_draft parameter
new_draft.is_draft = True  # Set as attribute after creation
```

---

## Rollback Plan (if fix causes issues)

If the fix causes unexpected problems, you can rollback by:

1. Reverting the 3 files to previous state
2. OR applying Option 2 fix instead:

**Option 2: Add is_draft to ESGData.__init__**

File: `app/models/esg_data.py`

Line 75, change:
```python
# BEFORE:
def __init__(self, entity_id, field_id, raw_value, reporting_date,
             company_id=None, calculated_value=None, unit=None,
             dimension_values=None, assignment_id=None, notes=None):

# AFTER:
def __init__(self, entity_id, field_id, raw_value, reporting_date,
             company_id=None, calculated_value=None, unit=None,
             dimension_values=None, assignment_id=None, notes=None,
             is_draft=False):  # ADD THIS
```

Line 86, add:
```python
self.is_draft = is_draft  # ADD THIS LINE
```

This makes the original code work, but Option 1 (removing the parameter) is cleaner.

---

## Summary Checklist

- [ ] File 1: submission_service.py - Remove is_draft from line 100
- [ ] File 2: validation_service.py - Fix filter on line 59
- [ ] File 3: template_service.py - Fix 5 filter occurrences
- [ ] Run verification test script
- [ ] Check database for 3 test entries
- [ ] Confirm no errors in submission response
- [ ] Proceed to comprehensive testing

**Estimated Time:** 10 minutes
**Risk Level:** Low (simple parameter removal)
**Rollback:** Easy (revert 3 files or apply Option 2)

---

**Created:** 2025-11-19
**Status:** Ready to apply
**Tested:** No (awaiting fix application)
