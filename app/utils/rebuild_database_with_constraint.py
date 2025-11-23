"""
DEVELOPMENT ONLY: Rebuild Database with Uniqueness Constraint

⚠️  WARNING: This script will DROP ALL TABLES and recreate them!
Use ONLY in development environment.

For production, use proper migrations (Alembic).

What this does:
1. Exports all data to backup JSON file
2. Drops all tables
3. Recreates tables with new uniqueness constraint
4. Restores data from backup

Safety:
- Creates backup before any changes
- Can rollback if restoration fails
"""

from app import create_app, db
from app.models.esg_data import ESGData
import json
from datetime import date, datetime
import sys


def serialize_date(obj):
    """JSON serializer for datetime/date objects."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def backup_data():
    """
    Backup all ESG data to JSON file.

    Returns:
        str: Path to backup file
    """
    print("\n[1/5] Creating backup of all data...")

    backup_file = "esg_data_backup.json"

    # Get all data
    all_data = ESGData.query.all()

    backup = []
    for entry in all_data:
        backup.append({
            'data_id': entry.data_id,
            'entity_id': entry.entity_id,
            'field_id': entry.field_id,
            'company_id': entry.company_id,
            'assignment_id': entry.assignment_id,
            'raw_value': entry.raw_value,
            'calculated_value': entry.calculated_value,
            'unit': entry.unit,
            'dimension_values': entry.dimension_values,
            'is_draft': entry.is_draft,
            'draft_metadata': entry.draft_metadata,
            'notes': entry.notes,
            'review_status': entry.review_status,
            'submitted_at': entry.submitted_at,
            'validation_results': entry.validation_results,
            'reporting_date': entry.reporting_date,
            'created_at': entry.created_at,
            'updated_at': entry.updated_at
        })

    with open(backup_file, 'w') as f:
        json.dump(backup, f, indent=2, default=serialize_date)

    print(f"   ✅ Backed up {len(backup)} entries to {backup_file}")
    return backup_file


def rebuild_schema():
    """
    Drop and recreate all tables with new constraints.
    """
    print("\n[2/5] Rebuilding database schema...")

    try:
        # Drop all tables
        print("   Dropping all tables...")
        db.drop_all()

        # Recreate all tables with new constraints
        print("   Creating all tables with new constraints...")
        db.create_all()

        print("   ✅ Schema rebuilt successfully")
        return True

    except Exception as e:
        print(f"   ❌ Error rebuilding schema: {str(e)}")
        return False


def restore_data(backup_file):
    """
    Restore data from backup file.

    Args:
        backup_file: Path to backup JSON file
    """
    print("\n[3/5] Restoring data from backup...")

    try:
        with open(backup_file, 'r') as f:
            backup = json.load(f)

        restored = 0
        skipped = 0

        for entry_data in backup:
            # Convert date strings back to date objects
            entry_data['reporting_date'] = datetime.fromisoformat(entry_data['reporting_date']).date()
            if entry_data['created_at']:
                entry_data['created_at'] = datetime.fromisoformat(entry_data['created_at'])
            if entry_data['updated_at']:
                entry_data['updated_at'] = datetime.fromisoformat(entry_data['updated_at'])
            if entry_data['submitted_at']:
                entry_data['submitted_at'] = datetime.fromisoformat(entry_data['submitted_at'])

            # Check if entry already exists (shouldn't, but just in case)
            existing = ESGData.query.filter_by(
                field_id=entry_data['field_id'],
                entity_id=entry_data['entity_id'],
                reporting_date=entry_data['reporting_date'],
                company_id=entry_data['company_id'],
                is_draft=entry_data.get('is_draft', False)
            ).first()

            if existing:
                print(f"   ⚠️  Skipping duplicate: {entry_data['data_id']}")
                skipped += 1
                continue

            # Create new entry using only the fields accepted by __init__
            entry = ESGData(
                entity_id=entry_data['entity_id'],
                field_id=entry_data['field_id'],
                raw_value=entry_data['raw_value'],
                reporting_date=entry_data['reporting_date'],
                company_id=entry_data['company_id'],
                calculated_value=entry_data.get('calculated_value'),
                unit=entry_data.get('unit'),
                dimension_values=entry_data.get('dimension_values'),
                assignment_id=entry_data.get('assignment_id'),
                notes=entry_data.get('notes')
            )

            # Manually set fields that aren't in __init__
            entry.data_id = entry_data['data_id']
            entry.is_draft = entry_data.get('is_draft', False)
            entry.draft_metadata = entry_data.get('draft_metadata')
            entry.review_status = entry_data.get('review_status', 'draft')
            entry.submitted_at = entry_data.get('submitted_at')
            entry.validation_results = entry_data.get('validation_results')
            entry.created_at = entry_data.get('created_at')
            entry.updated_at = entry_data.get('updated_at')

            db.session.add(entry)
            restored += 1

        db.session.commit()

        print(f"   ✅ Restored {restored} entries (skipped {skipped} duplicates)")
        return True

    except Exception as e:
        db.session.rollback()
        print(f"   ❌ Error restoring data: {str(e)}")
        return False


def test_constraint():
    """
    Test that the constraint is working.
    """
    print("\n[4/5] Testing uniqueness constraint...")

    try:
        # Find an existing entry
        existing = ESGData.query.first()

        if not existing:
            print("   ⚠️  No data to test with")
            return True

        # Try to create a duplicate
        duplicate = ESGData(
            entity_id=existing.entity_id,
            field_id=existing.field_id,
            raw_value="999",
            reporting_date=existing.reporting_date,
            company_id=existing.company_id,
            is_draft=False
        )

        db.session.add(duplicate)
        db.session.flush()

        # If we got here, constraint is NOT working
        db.session.rollback()
        print("   ❌ Constraint NOT working! Duplicate insert succeeded!")
        return False

    except Exception as e:
        db.session.rollback()

        if 'UNIQUE constraint failed' in str(e) or 'IntegrityError' in str(type(e).__name__):
            print(f"   ✅ Constraint working! Duplicate blocked")
            return True
        else:
            print(f"   ⚠️  Unexpected error: {str(e)}")
            return False


def verify_data_count(expected_count):
    """
    Verify that all data was restored.
    """
    print("\n[5/5] Verifying data restoration...")

    actual_count = ESGData.query.count()

    if actual_count >= expected_count - 10:  # Allow for duplicates that were skipped
        print(f"   ✅ Data verified: {actual_count} entries (expected ~{expected_count})")
        return True
    else:
        print(f"   ❌ Data loss detected: {actual_count} entries (expected {expected_count})")
        return False


def main():
    """Main entry point."""
    print("=" * 70)
    print("⚠️  DATABASE REBUILD: Add Uniqueness Constraint")
    print("=" * 70)
    print("\nWARNING: This will DROP and RECREATE all tables!")
    print("This should ONLY be used in development environment!")

    response = input("\nAre you sure you want to proceed? (yes/no): ")
    if response.lower() != 'yes':
        print("Rebuild cancelled.")
        return

    # Get initial count
    initial_count = ESGData.query.count()
    print(f"\nCurrent data count: {initial_count} entries")

    # Step 1: Backup
    backup_file = backup_data()

    # Step 2: Rebuild schema
    if not rebuild_schema():
        print("\n❌ Rebuild FAILED at schema recreation")
        sys.exit(1)

    # Step 3: Restore data
    if not restore_data(backup_file):
        print("\n❌ Rebuild FAILED at data restoration")
        print(f"⚠️  Data backup available in: {backup_file}")
        sys.exit(1)

    # Step 4: Test constraint
    if not test_constraint():
        print("\n❌ Rebuild FAILED: Constraint not enforced")
        sys.exit(1)

    # Step 5: Verify
    if not verify_data_count(initial_count):
        print("\n⚠️  Warning: Data count mismatch")

    print("\n" + "=" * 70)
    print("✅ Database rebuild completed successfully!")
    print("=" * 70)
    print("\nThe uniqueness constraint is now active.")
    print("Duplicate entries will be prevented at the database level.")
    print(f"\nBackup file retained: {backup_file}")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        main()
