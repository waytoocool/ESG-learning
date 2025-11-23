"""
Migration script to add Enhancement #4 bulk upload support columns.

Adds:
1. metadata column to esg_data_audit_log
2. file_hash column to esg_data_attachments
3. New enum values to change_type in esg_data_audit_log
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database(db_path='instance/esg_data.db'):
    """Add bulk upload support columns to existing database."""

    print(f"Starting migration for: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Add change_metadata column to esg_data_audit_log
        print("Adding change_metadata column to esg_data_audit_log...")
        try:
            cursor.execute("""
                ALTER TABLE esg_data_audit_log
                ADD COLUMN change_metadata TEXT
            """)
            print("✓ change_metadata column added")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("⊘ change_metadata column already exists")
            else:
                raise

        # 2. Add file_hash column to esg_data_attachments
        print("Adding file_hash column to esg_data_attachments...")
        try:
            cursor.execute("""
                ALTER TABLE esg_data_attachments
                ADD COLUMN file_hash VARCHAR(64)
            """)
            print("✓ file_hash column added")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("⊘ file_hash column already exists")
            else:
                raise

        # 3. Create index on file_hash
        print("Creating index on file_hash...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_attachment_file_hash
                ON esg_data_attachments(file_hash)
            """)
            print("✓ Index created on file_hash")
        except Exception as e:
            print(f"⚠ Index creation warning: {e}")

        # 4. Note about enum values
        print("\nNote: New enum values ('Excel Upload', 'Excel Upload Update') will be")
        print("available for future inserts. Existing enum constraint will accept them.")
        print("SQLite allows new enum values without schema changes.")

        conn.commit()
        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    # Check if custom path provided
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'instance/esg_data.db'

    # Verify file exists
    if not Path(db_path).exists():
        print(f"❌ Database file not found: {db_path}")
        sys.exit(1)

    migrate_database(db_path)
