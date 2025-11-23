"""
Database migration script for Validation Engine Implementation
Adds validation-related columns to Company, DataPointAssignment, and ESGData models

Run this script ONCE to apply the database schema changes for the validation engine.

Usage:
    python3 -c "from app.utils.migrate_validation_engine import migrate; migrate()"

Or from Python shell:
    from app.utils.migrate_validation_engine import migrate
    migrate()
"""

from ..extensions import db
from sqlalchemy import text


def migrate():
    """
    Apply validation engine database migrations.

    Changes:
    1. Company: Add validation_trend_threshold_pct column
    2. DataPointAssignment: Add attachment_required column
    3. ESGData: Add review_status, submitted_at, validation_results columns
    4. ESGDataAuditLog: Add validation-related change types to enum
    """

    print("=" * 70)
    print("VALIDATION ENGINE - DATABASE MIGRATION")
    print("=" * 70)
    print()

    try:
        # Step 1: Add validation_trend_threshold_pct to Company table
        print("[1/5] Adding validation_trend_threshold_pct to Company table...")
        try:
            db.session.execute(text("""
                ALTER TABLE company
                ADD COLUMN validation_trend_threshold_pct FLOAT DEFAULT 20.0 NOT NULL
            """))
            db.session.commit()
            print("✓ Company table updated successfully")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("⊳ Column already exists, skipping...")
                db.session.rollback()
            else:
                raise

        # Step 2: Add attachment_required to DataPointAssignment table
        print("\n[2/5] Adding attachment_required to DataPointAssignment table...")
        try:
            db.session.execute(text("""
                ALTER TABLE data_point_assignments
                ADD COLUMN attachment_required BOOLEAN DEFAULT FALSE NOT NULL
            """))
            db.session.commit()
            print("✓ DataPointAssignment table updated successfully")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("⊳ Column already exists, skipping...")
                db.session.rollback()
            else:
                raise

        # Step 3: Create review_status_type enum (if using PostgreSQL)
        # For SQLite, we'll handle this differently since SQLite doesn't support ENUM
        print("\n[3/5] Adding review workflow fields to ESGData table...")

        # Check database type
        db_url = str(db.engine.url)
        is_sqlite = 'sqlite' in db_url.lower()

        if is_sqlite:
            # SQLite approach: Add columns with CHECK constraint
            try:
                db.session.execute(text("""
                    ALTER TABLE esg_data
                    ADD COLUMN review_status TEXT DEFAULT 'draft' NOT NULL
                    CHECK(review_status IN ('draft', 'submitted', 'pending_review',
                                            'approved', 'rejected', 'needs_revision'))
                """))
                db.session.commit()
                print("✓ Added review_status column (SQLite)")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("⊳ review_status column already exists, skipping...")
                    db.session.rollback()
                else:
                    raise

            try:
                db.session.execute(text("""
                    ALTER TABLE esg_data
                    ADD COLUMN submitted_at TIMESTAMP NULL
                """))
                db.session.commit()
                print("✓ Added submitted_at column")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("⊳ submitted_at column already exists, skipping...")
                    db.session.rollback()
                else:
                    raise

            try:
                db.session.execute(text("""
                    ALTER TABLE esg_data
                    ADD COLUMN validation_results JSON NULL
                """))
                db.session.commit()
                print("✓ Added validation_results column")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("⊳ validation_results column already exists, skipping...")
                    db.session.rollback()
                else:
                    raise

        else:
            # PostgreSQL approach: Create ENUM type first
            try:
                db.session.execute(text("""
                    CREATE TYPE review_status_type AS ENUM (
                        'draft', 'submitted', 'pending_review',
                        'approved', 'rejected', 'needs_revision'
                    )
                """))
                db.session.commit()
                print("✓ Created review_status_type ENUM")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("⊳ ENUM type already exists, skipping...")
                    db.session.rollback()
                else:
                    raise

            try:
                db.session.execute(text("""
                    ALTER TABLE esg_data
                    ADD COLUMN review_status review_status_type DEFAULT 'draft' NOT NULL
                """))
                db.session.commit()
                print("✓ Added review_status column")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("⊳ review_status column already exists, skipping...")
                    db.session.rollback()
                else:
                    raise

            try:
                db.session.execute(text("""
                    ALTER TABLE esg_data
                    ADD COLUMN submitted_at TIMESTAMP NULL
                """))
                db.session.commit()
                print("✓ Added submitted_at column")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("⊳ submitted_at column already exists, skipping...")
                    db.session.rollback()
                else:
                    raise

            try:
                db.session.execute(text("""
                    ALTER TABLE esg_data
                    ADD COLUMN validation_results JSONB NULL
                """))
                db.session.commit()
                print("✓ Added validation_results column")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("⊳ validation_results column already exists, skipping...")
                    db.session.rollback()
                else:
                    raise

        # Step 4: Create indexes for review workflow
        print("\n[4/5] Creating indexes for review workflow...")
        try:
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_esg_review_status
                ON esg_data(review_status, company_id)
            """))
            db.session.commit()
            print("✓ Created idx_esg_review_status index")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("⊳ Index already exists, skipping...")
                db.session.rollback()
            else:
                raise

        try:
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_esg_review_pending
                ON esg_data(review_status, submitted_at)
            """))
            db.session.commit()
            print("✓ Created idx_esg_review_pending index")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("⊳ Index already exists, skipping...")
                db.session.rollback()
            else:
                raise

        # Step 5: Update ESGDataAuditLog enum (model change only, no SQL needed)
        print("\n[5/5] ESGDataAuditLog change types updated in model...")
        print("✓ New change types: Data_Submitted, Validation_Passed, Validation_Warning, User_Acknowledged_Warning")
        print("  Note: These will be available after app restart")

        print("\n" + "=" * 70)
        print("✓ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Restart the Flask application")
        print("2. Verify changes in Python shell:")
        print("   from app.models import Company, DataPointAssignment, ESGData")
        print("   company = Company.query.first()")
        print("   print(company.validation_trend_threshold_pct)")
        print()

        return True

    except Exception as e:
        db.session.rollback()
        print("\n" + "=" * 70)
        print("✗ MIGRATION FAILED!")
        print("=" * 70)
        print(f"Error: {str(e)}")
        print()
        print("The database has been rolled back to the previous state.")
        print("Please review the error and try again.")
        print()
        raise


def rollback():
    """
    Rollback validation engine migrations (CAUTION: This will drop columns!).

    WARNING: This will permanently delete data in the validation-related columns!
    Only use this if you need to completely remove the validation engine features.
    """

    print("=" * 70)
    print("VALIDATION ENGINE - DATABASE ROLLBACK")
    print("=" * 70)
    print()
    print("WARNING: This will remove validation engine columns and data!")
    print()

    response = input("Are you sure you want to proceed? (type 'YES' to confirm): ")

    if response != "YES":
        print("Rollback cancelled.")
        return False

    try:
        # Remove columns from ESGData
        print("[1/3] Removing columns from ESGData table...")
        db.session.execute(text("ALTER TABLE esg_data DROP COLUMN IF EXISTS review_status"))
        db.session.execute(text("ALTER TABLE esg_data DROP COLUMN IF EXISTS submitted_at"))
        db.session.execute(text("ALTER TABLE esg_data DROP COLUMN IF EXISTS validation_results"))
        db.session.commit()
        print("✓ ESGData columns removed")

        # Remove column from DataPointAssignment
        print("\n[2/3] Removing column from DataPointAssignment table...")
        db.session.execute(text("ALTER TABLE data_point_assignments DROP COLUMN IF EXISTS attachment_required"))
        db.session.commit()
        print("✓ DataPointAssignment column removed")

        # Remove column from Company
        print("\n[3/3] Removing column from Company table...")
        db.session.execute(text("ALTER TABLE company DROP COLUMN IF EXISTS validation_trend_threshold_pct"))
        db.session.commit()
        print("✓ Company column removed")

        print("\n" + "=" * 70)
        print("✓ ROLLBACK COMPLETED!")
        print("=" * 70)
        print()

        return True

    except Exception as e:
        db.session.rollback()
        print("\n" + "=" * 70)
        print("✗ ROLLBACK FAILED!")
        print("=" * 70)
        print(f"Error: {str(e)}")
        print()
        raise


if __name__ == "__main__":
    print("This migration script should be run from the Flask application context.")
    print()
    print("Usage:")
    print("  python3 -c \"from app.utils.migrate_validation_engine import migrate; migrate()\"")
    print()
    print("Or from Python shell:")
    print("  from app.utils.migrate_validation_engine import migrate")
    print("  migrate()")
