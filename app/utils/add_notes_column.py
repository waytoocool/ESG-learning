"""
Migration script to add notes column to esg_data table.

Enhancement #2: Comments/Notes Functionality for Data Entries
Date: 2025-11-14
Run this script to update existing database.

Usage:
    python3 app/utils/add_notes_column.py
"""

from app import create_app
from app.extensions import db
from sqlalchemy import text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_add_notes_column():
    """Add notes column to esg_data table."""

    app = create_app()
    with app.app_context():
        try:
            # Check if column already exists
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('esg_data')]

            if 'notes' in columns:
                logger.info("✅ Column 'notes' already exists in esg_data table")
                return

            logger.info("Adding 'notes' column to esg_data table...")

            # Add notes column
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE esg_data
                    ADD COLUMN notes TEXT NULL
                """))
                conn.commit()

            logger.info("✅ Successfully added 'notes' column to esg_data table")
            logger.info("   - Column type: TEXT (supports up to 65,535 characters)")
            logger.info("   - Nullable: Yes (optional field)")
            logger.info("   - Default: NULL")

        except Exception as e:
            logger.error(f"❌ Error adding notes column: {str(e)}")
            raise


if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("Enhancement #2: Adding Notes Column to ESGData")
    logger.info("=" * 70)
    migrate_add_notes_column()
    logger.info("=" * 70)
    logger.info("Migration completed successfully!")
    logger.info("=" * 70)
