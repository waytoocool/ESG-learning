"""Add unique constraint for single active assignment per field-entity-company"""
from app import create_app, db
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
        print("✅ Successfully removed index 'idx_single_active_assignment'")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error removing index: {str(e)}")
        return False

if __name__ == "__main__":
    import sys

    # Create Flask app context
    app = create_app()
    with app.app_context():
        if '--remove' in sys.argv:
            remove_unique_active_constraint()
        else:
            add_unique_active_constraint()
