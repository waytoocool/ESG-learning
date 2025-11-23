"""
Data Cleanup Script: Remove Duplicate ESG Data Entries

This script identifies and removes duplicate ESG data entries where multiple
rows exist for the same (field_id, entity_id, reporting_date, company_id).

Strategy:
- For each duplicate group, keep the MOST RECENT entry (by updated_at)
- Delete older entries
- Preserve change history in audit log before deletion
- Report all changes for verification

Safety Features:
- Dry run mode to preview changes
- Audit trail preservation
- Detailed logging
- Transaction rollback on errors
"""

from app import create_app, db
from app.models.esg_data import ESGData, ESGDataAuditLog
from flask_login import current_user
from datetime import datetime, UTC
from sqlalchemy import func
import sys

def find_duplicates():
    """
    Find all duplicate ESG data entries.

    Returns:
        List of tuples: (field_id, entity_id, reporting_date, company_id, count)
    """
    print("\n[1/5] Scanning for duplicate entries...")

    duplicates = db.session.query(
        ESGData.field_id,
        ESGData.entity_id,
        ESGData.reporting_date,
        ESGData.company_id,
        func.count(ESGData.data_id).label('count')
    ).group_by(
        ESGData.field_id,
        ESGData.entity_id,
        ESGData.reporting_date,
        ESGData.company_id
    ).having(
        func.count(ESGData.data_id) > 1
    ).all()

    print(f"   Found {len(duplicates)} groups with duplicates")
    return duplicates


def get_entries_for_duplicate_group(field_id, entity_id, reporting_date, company_id):
    """
    Get all entries for a duplicate group, ordered by updated_at DESC.

    Returns:
        List of ESGData entries (most recent first)
    """
    return ESGData.query.filter_by(
        field_id=field_id,
        entity_id=entity_id,
        reporting_date=reporting_date,
        company_id=company_id
    ).order_by(
        ESGData.updated_at.desc()
    ).all()


def create_deletion_audit_log(entry, reason="Duplicate Entry Cleanup"):
    """
    Create audit log entry before deleting a duplicate.

    Args:
        entry: ESGData entry being deleted
        reason: Reason for deletion
    """
    audit_log = ESGDataAuditLog(
        data_id=entry.data_id,
        change_type='Delete',
        old_value=float(entry.raw_value) if entry.raw_value else None,
        new_value=None,
        changed_by=1,  # System user ID (adjust as needed)
        change_metadata={
            'reason': reason,
            'cleanup_script': True,
            'field_id': entry.field_id,
            'entity_id': entry.entity_id,
            'reporting_date': entry.reporting_date.isoformat(),
            'original_created_at': entry.created_at.isoformat() if entry.created_at else None,
            'original_updated_at': entry.updated_at.isoformat() if entry.updated_at else None,
            'notes': entry.notes,
            'dimension_values': entry.dimension_values
        }
    )
    db.session.add(audit_log)


def cleanup_duplicates(dry_run=True):
    """
    Remove duplicate ESG data entries, keeping the most recent one.

    Args:
        dry_run: If True, only report what would be deleted without actual deletion

    Returns:
        Dict with cleanup statistics
    """
    stats = {
        'duplicate_groups': 0,
        'entries_kept': 0,
        'entries_deleted': 0,
        'errors': 0
    }

    try:
        # Find all duplicate groups
        duplicates = find_duplicates()
        stats['duplicate_groups'] = len(duplicates)

        if not duplicates:
            print("\n✅ No duplicates found! Database is clean.")
            return stats

        print(f"\n[2/5] Processing {len(duplicates)} duplicate groups...")
        print(f"   Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (will delete duplicates)'}")

        for idx, (field_id, entity_id, reporting_date, company_id, count) in enumerate(duplicates, 1):
            print(f"\n   [{idx}/{len(duplicates)}] Processing group:")
            print(f"      Field ID: {field_id}")
            print(f"      Entity ID: {entity_id}")
            print(f"      Reporting Date: {reporting_date}")
            print(f"      Company ID: {company_id}")
            print(f"      Duplicate count: {count}")

            # Get all entries for this group
            entries = get_entries_for_duplicate_group(
                field_id, entity_id, reporting_date, company_id
            )

            # Keep the first one (most recent by updated_at)
            keep_entry = entries[0]
            delete_entries = entries[1:]

            print(f"      ✅ KEEP: data_id={keep_entry.data_id}, "
                  f"value={keep_entry.raw_value}, "
                  f"updated={keep_entry.updated_at}")

            stats['entries_kept'] += 1

            # Delete the rest
            for entry in delete_entries:
                print(f"      ❌ DELETE: data_id={entry.data_id}, "
                      f"value={entry.raw_value}, "
                      f"updated={entry.updated_at}")

                if not dry_run:
                    # Create audit log before deletion
                    create_deletion_audit_log(entry)

                    # Delete the entry
                    db.session.delete(entry)

                stats['entries_deleted'] += 1

        if not dry_run:
            print("\n[3/5] Committing changes to database...")
            db.session.commit()
            print("   ✅ Changes committed successfully")
        else:
            print("\n[3/5] Skipping commit (DRY RUN mode)")

        # Print summary
        print("\n[4/5] Cleanup Summary:")
        print(f"   Duplicate groups found: {stats['duplicate_groups']}")
        print(f"   Entries kept: {stats['entries_kept']}")
        print(f"   Entries deleted: {stats['entries_deleted']}")
        print(f"   Total entries processed: {stats['entries_kept'] + stats['entries_deleted']}")

        if dry_run:
            print("\n⚠️  This was a DRY RUN - no changes were made")
            print("   Run with --live flag to actually remove duplicates")
        else:
            print("\n✅ Cleanup completed successfully!")

        return stats

    except Exception as e:
        print(f"\n❌ Error during cleanup: {str(e)}")
        db.session.rollback()
        stats['errors'] += 1
        raise


def verify_cleanup():
    """
    Verify that no duplicates remain after cleanup.

    Returns:
        Boolean: True if no duplicates exist
    """
    print("\n[5/5] Verifying cleanup...")

    remaining_duplicates = find_duplicates()

    if not remaining_duplicates:
        print("   ✅ Verification passed! No duplicates found.")
        return True
    else:
        print(f"   ⚠️  WARNING: {len(remaining_duplicates)} duplicate groups still exist!")
        return False


def main():
    """Main entry point for the cleanup script."""
    print("=" * 70)
    print("ESG Data Duplicate Cleanup Script")
    print("=" * 70)

    # Check command line arguments
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == '--live':
        dry_run = False
        print("\n⚠️  LIVE MODE: Changes will be permanent!")
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() != 'yes':
            print("Cleanup cancelled.")
            return

    # Run cleanup
    stats = cleanup_duplicates(dry_run=dry_run)

    # Verify if live mode
    if not dry_run:
        verify_cleanup()

    print("\n" + "=" * 70)
    print("Cleanup script completed")
    print("=" * 70)


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        main()
