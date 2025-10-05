# Reactivation Version Bug - Test Report

**Test Date**: October 2, 2025
**Bug ID**: REACTIVATION-VERSION-BUG-001
**Status**: CONFIRMED
**Severity**: HIGH

---

## Quick Links

- **Bug Report**: [Bug_Report_Reactivation_Version_Toolbar.md](./Bug_Report_Reactivation_Version_Toolbar.md)
- **Testing Summary**: [Testing_Summary_Reactivation_Bug_v1.md](./Testing_Summary_Reactivation_Bug_v1.md)
- **Screenshots**: [screenshots/](./screenshots/)

---

## Overview

This directory contains complete documentation for the reactivation version bug discovered in the assign-data-points-v2 page. The bug causes the system to create v1 assignments when reactivating fields that already have higher version numbers (v2, v3, v4, v5, etc.).

---

## Bug Summary

**Issue**: When reactivating an inactive field using the checkbox + toolbar "Assign Entity" workflow, the system incorrectly assigns version 1 instead of the latest existing version.

**Example**:
- Field has versions: v1, v2, v3, v4, v5 (all inactive)
- User reactivates field for "Alpha Factory" entity
- Expected: v5 or v6
- Actual: v1 ❌

**Impact**: Version history fragmentation, data integrity issues, audit trail confusion

---

## Documentation Structure

```
reactivation-version-bug-v2-2025-10-02/
├── README.md (this file)
├── Bug_Report_Reactivation_Version_Toolbar.md
│   └── Comprehensive bug report with technical details
├── Testing_Summary_Reactivation_Bug_v1.md
│   └── Executive summary of testing process
└── screenshots/
    ├── 1-phase1-assignment-history-before-delete-v5-highest.png
    ├── 2-phase2-field-inactive-no-assignments.png
    ├── 3-phase3-field-checkbox-selected.png
    ├── 4-phase3-assign-entity-modal-opened.png
    ├── 5-phase3-entity-selected-alpha-factory.png
    ├── 6-phase3-field-reactivated-with-entity.png
    ├── 7-BUG-CONFIRMED-v1-active-instead-of-v5.png
    └── 8-filtered-view-showing-v1-active-v5-exists.png
```

---

## Key Findings

1. **Bug Confirmed**: Successfully reproduced on first attempt
2. **Root Cause**: Backend missing version selection logic in entity assignment API
3. **Severity**: HIGH - affects data integrity and version tracking
4. **Impact**: All fields with multiple versions are affected

---

## Test Details

### Test Environment
- URL: http://test-company-alpha.127-0-0-1.nip.io:8000/
- User: alice@alpha.com (ADMIN)
- Company: Test Company Alpha
- Test Field: "Complete Framework Field 1"
- Highest Version: v5 (Alpha HQ, Inactive)

### Test Results
- Reproduced bug: ✓ YES
- Version created: v1 (INCORRECT)
- Expected version: v5 or v6
- Screenshots: 8 captured
- Documentation: Complete

---

## Recommended Fix

**Backend** (Primary):
```python
# Add version selection logic in assignment API
def determine_version_for_assignment(field_id, entity_id):
    existing = DataPointAssignment.query.filter_by(
        field_id=field_id,
        entity_id=entity_id
    ).order_by(DataPointAssignment.series_version.desc()).first()

    if existing and existing.series_status == 'inactive':
        return existing.series_version  # Reactivate highest
    elif existing:
        return existing.series_version + 1  # Create next
    else:
        return 1  # New assignment
```

**Frontend** (Secondary):
- Display version number in assignment modal
- Show existing version count
- Validate version in success messages

---

## Next Steps

1. **Backend Developer**: Fix version selection logic in `/app/routes/admin_assignments_api.py`
2. **Code Review**: Check similar workflows for same issue
3. **Testing**: Add unit tests for version handling
4. **Regression Test**: Verify fix doesn't break other workflows

---

## Contact

For questions or additional information about this bug report, please contact the development team.

---

**Report Generated**: October 2, 2025
**Testing Agent**: UI Testing Agent
**All Phases**: COMPLETED ✓
