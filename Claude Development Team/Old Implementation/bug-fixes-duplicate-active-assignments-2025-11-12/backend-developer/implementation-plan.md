# Implementation Plan: Fix Duplicate Active Assignments

## Phase 1: Database Cleanup (Immediate)

### Step 1.1: Create Cleanup Script

**File**: `app/utils/fix_duplicate_active_assignments.py`

```python
"""
Cleanup script to fix duplicate active assignments
Run this before implementing the database constraint
"""
from app import db
from app.models.data_assignment import DataPointAssignment
from sqlalchemy import text
from datetime import datetime

def find_duplicate_active_assignments():
    """Find all field-entity-company combinations with multiple active assignments"""
    query = text("""
        SELECT field_id, entity_id, company_id,
               COUNT(*) as active_count,
               GROUP_CONCAT(id || ':' || series_version ORDER BY series_version DESC) as versions
        FROM data_point_assignments
        WHERE series_status = 'active'
        GROUP BY field_id, entity_id, company_id
        HAVING COUNT(*) > 1
    """)

    results = db.session.execute(query).fetchall()
    return results

def fix_duplicates(dry_run=True):
    """
    Fix duplicate active assignments by keeping only the highest version active

    Args:
        dry_run: If True, only print what would be done without making changes
    """
    duplicates = find_duplicate_active_assignments()

    if not duplicates:
        print("✅ No duplicate active assignments found")
        return {"fixed": 0, "errors": 0}

    print(f"🔍 Found {len(duplicates)} field-entity-company combinations with duplicate actives")

    fixed_count = 0
    error_count = 0

    for dup in duplicates:
        field_id, entity_id, company_id, active_count, versions_str = dup
        versions = versions_str.split(',')

        # Parse version strings (format: "id:version")
        parsed_versions = []
        for v in versions:
            assign_id, version_num = v.split(':')
            parsed_versions.append({
                'id': assign_id,
                'version': int(version_num)
            })

        # Sort by version desc, keep highest
        parsed_versions.sort(key=lambda x: x['version'], reverse=True)
        highest_version = parsed_versions[0]
        others_to_supersede = parsed_versions[1:]

        print(f"\n📝 Field: {field_id}, Entity: {entity_id}, Company: {company_id}")
        print(f"   Active count: {active_count}")
        print(f"   Keep active: v{highest_version['version']} ({highest_version['id']})")
        print(f"   Supersede: {[f\"v{x['version']} ({x['id']})\" for x in others_to_supersede]}")

        if dry_run:
            print("   [DRY RUN] Would supersede these assignments")
            fixed_count += len(others_to_supersede)
            continue

        # Actually fix it
        try:
            for assignment_data in others_to_supersede:
                assignment = DataPointAssignment.query.get(assignment_data['id'])
                if assignment:
                    old_status = assignment.series_status
                    assignment.series_status = 'superseded'
                    print(f"   ✓ Superseded: {assignment_data['id']} (v{assignment_data['version']}): {old_status} → superseded")
                    fixed_count += 1

            db.session.commit()
            print(f"   ✅ Successfully fixed {len(others_to_supersede)} duplicate(s)")

        except Exception as e:
            db.session.rollback()
            print(f"   ❌ Error fixing duplicates: {str(e)}")
            error_count += 1

    return {"fixed": fixed_count, "errors": error_count}

if __name__ == "__main__":
    import sys

    # Check for --execute flag
    execute = '--execute' in sys.argv

    if not execute:
        print("="*80)
        print("DRY RUN MODE - No changes will be made")
        print("Add --execute flag to actually fix the duplicates")
        print("="*80)
        print()

    results = fix_duplicates(dry_run=not execute)

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Fixed: {results['fixed']}")
    print(f"Errors: {results['errors']}")
    print("="*80)

    if not execute:
        print("\n💡 To apply these changes, run: python -m app.utils.fix_duplicate_active_assignments --execute")
```

### Step 1.2: Run Cleanup (Dry Run First)

```bash
# Dry run to see what would be fixed
python -c "from app.utils.fix_duplicate_active_assignments import fix_duplicates; fix_duplicates(dry_run=True)"

# Actually execute
python -c "from app.utils.fix_duplicate_active_assignments import fix_duplicates; fix_duplicates(dry_run=False)"
```

---

## Phase 2: Add Database Constraint

### Step 2.1: Create Migration Script

**File**: `app/utils/add_unique_active_constraint.py`

```python
"""Add unique constraint for single active assignment per field-entity-company"""
from app import db
from sqlalchemy import text

def add_unique_active_constraint():
    """
    Add a unique partial index to enforce single active assignment
    SQLite 3.8.0+ supports partial indexes
    """
    try:
        # Check if index already exists
        check_query = text("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_single_active_assignment'
        """)
        existing = db.session.execute(check_query).fetchone()

        if existing:
            print("✅ Index 'idx_single_active_assignment' already exists")
            return True

        # Create the unique partial index
        create_index_query = text("""
            CREATE UNIQUE INDEX idx_single_active_assignment
            ON data_point_assignments(field_id, entity_id, company_id)
            WHERE series_status = 'active'
        """)

        db.session.execute(create_index_query)
        db.session.commit()

        print("✅ Successfully created unique index 'idx_single_active_assignment'")
        return True

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating index: {str(e)}")
        return False

def remove_unique_active_constraint():
    """Remove the constraint (for rollback if needed)"""
    try:
        drop_query = text("DROP INDEX IF EXISTS idx_single_active_assignment")
        db.session.execute(drop_query)
        db.session.commit()
        print("✅ Successfully removed index 'idx_single_active_constraint'")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error removing index: {str(e)}")
        return False

if __name__ == "__main__":
    import sys

    if '--remove' in sys.argv:
        remove_unique_active_constraint()
    else:
        add_unique_active_constraint()
```

---

## Phase 3: Enhanced Validation & Logging

### Step 3.1: Add Validation Helper

**File**: `app/services/assignment_versioning.py` (add new function)

```python
def validate_no_duplicate_actives(field_id, entity_id, company_id):
    """
    Validate that no duplicate active assignments exist

    Raises:
        ValueError: If duplicate active assignments are detected
    """
    active_count = DataPointAssignment.query.filter(
        and_(
            DataPointAssignment.field_id == field_id,
            DataPointAssignment.entity_id == entity_id,
            DataPointAssignment.company_id == company_id,
            DataPointAssignment.series_status == 'active'
        )
    ).count()

    if active_count > 1:
        current_app.logger.error(
            f"DUPLICATE ACTIVE ASSIGNMENTS DETECTED: "
            f"field={field_id}, entity={entity_id}, company={company_id}, count={active_count}"
        )
        raise ValueError(
            f"Data integrity error: {active_count} active assignments found for same field-entity-company. "
            f"Expected 1. Please contact support."
        )

    return active_count
```

### Step 3.2: Enhanced Logging in Versioning

**Location**: `app/services/assignment_versioning.py:98-170`

Add detailed logging around status transitions:

```python
# Before supersede (line 101)
current_app.logger.info(
    f"[VERSIONING-START] Assignment {assignment_id}: "
    f"field={current_assignment.field_id}, entity={current_assignment.entity_id}, "
    f"current_status={current_assignment.series_status}, current_version={current_assignment.series_version}"
)

# After supersede flush (line 110)
current_app.logger.info(
    f"[VERSIONING-PHASE1-COMPLETE] Assignment {assignment_id}: "
    f"status changed to 'superseded', flushed to database"
)

# After new version created (line 164)
current_app.logger.info(
    f"[VERSIONING-PHASE2-COMPLETE] New assignment {new_assignment.id}: "
    f"version={new_assignment.series_version}, status={new_assignment.series_status}, "
    f"old_assignment={assignment_id} now superseded"
)
```

### Step 3.3: Add Validation in configure_fields

**Location**: `app/routes/admin_assignDataPoints_Additional.py:131`

Before processing active assignments:

```python
# Process active assignments with versioning
for assignment in active_assignments:
    try:
        # ADDED: Validate no duplicates before versioning
        from ..services.assignment_versioning import validate_no_duplicate_actives
        validate_no_duplicate_actives(
            assignment.field_id,
            assignment.entity_id,
            assignment.company_id
        )

        # Existing versioning code...
        version_result = AssignmentVersioningService.create_assignment_version(...)
```

---

## Implementation Checklist

### Phase 1: Cleanup
- [ ] Create `fix_duplicate_active_assignments.py`
- [ ] Run dry-run to identify duplicates
- [ ] Review dry-run output
- [ ] Execute cleanup script
- [ ] Verify no duplicates remain
- [ ] Document cleanup results

### Phase 2: Database Constraint
- [ ] Create `add_unique_active_constraint.py`
- [ ] Run constraint creation
- [ ] Test constraint with manual duplicate attempt
- [ ] Verify constraint blocks duplicates
- [ ] Document constraint behavior

### Phase 3: Code Enhancements
- [ ] Add `validate_no_duplicate_actives()` function
- [ ] Add enhanced logging to versioning service
- [ ] Add validation to configure_fields endpoint
- [ ] Update error messages for user clarity
- [ ] Test all changes

### Phase 4: Testing
- [ ] Re-run Phase 1.1: Rapid configuration changes
- [ ] Run Phase 1.2: Frequency changes
- [ ] Run Phase 1.3: Configuration with existing data
- [ ] Verify no duplicates created
- [ ] Check logs for proper status transitions
- [ ] Document test results

---

## Rollback Plan

If issues are discovered:

1. **Rollback Database Constraint**
   ```bash
   python -m app.utils.add_unique_active_constraint --remove
   ```

2. **Rollback Code Changes**
   - Remove validation calls from configure_fields
   - Remove enhanced logging
   - Keep cleanup script for reference

3. **Restore Original State**
   - Backup database before cleanup
   - If needed, restore from backup

---

## Success Metrics

- ✅ Zero duplicate active assignments in database
- ✅ Database constraint prevents future duplicates
- ✅ All edge case tests pass
- ✅ No errors in production logs
- ✅ User experience unaffected

---

## Notes

- Test on development database first
- Backup production database before applying
- Monitor logs closely after deployment
- Be prepared to rollback if issues arise
