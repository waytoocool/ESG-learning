from app import create_app
from app.extensions import db
from app.models import Dimension, DimensionValue
import os

# Set up a dummy environment for the app context
os.environ['FLASK_CONFIG'] = 'development' # Or 'testing', 'production' as appropriate
os.environ['TENANT_ID'] = 'your_company_id_here' # Replace with an actual company ID if needed for tenant-scoping

app = create_app()

with app.app_context():
    try:
        # Define your new dimension data
        dimension_name = "Test Dimension"
        dimension_description = "A dimension created via script for testing."
        # IMPORTANT: Replace 'your_company_id_here' with the actual company_id
        # If you're testing with a specific tenant, ensure this matches.
        # For super admin created dimensions, company_id can be None or a specific ID.
        # For tenant-scoped dimensions, it must be the tenant's company_id.
        target_company_id = os.environ.get('TENANT_ID') # Or set a specific ID like 1, 2, etc.

        # Check if dimension already exists to prevent duplicates
        existing_dimension = Dimension.query.filter_by(name=dimension_name, company_id=target_company_id).first()
        if existing_dimension:
            print(f"Dimension '{dimension_name}' already exists for company_id {target_company_id}. Skipping creation.")
        else:
            # Create the dimension
            new_dimension = Dimension(
                name=dimension_name,
                description=dimension_description,
                company_id=target_company_id,
                is_system_default=False # Set to True if it's a system default dimension
            )
            db.session.add(new_dimension)
            db.session.flush() # Flush to get the dimension_id

            # Define dimension values
            dimension_values_data = [
                {"value": "Option A", "display_name": "First Option"},
                {"value": "Option B", "display_name": "Second Option"},
                {"value": "Option C", "display_name": "Third Option"}
            ]

            # Create dimension values
            for i, val_data in enumerate(dimension_values_data):
                new_value = DimensionValue(
                    dimension_id=new_dimension.dimension_id,
                    value=val_data["value"],
                    display_name=val_data["display_name"],
                    display_order=i + 1,
                    company_id=target_company_id # Must match the dimension's company_id
                )
                db.session.add(new_value)

            db.session.commit()
            print(f"Dimension '{dimension_name}' and its values created successfully for company_id {target_company_id}!")

    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")
    finally:
        db.session.close()
