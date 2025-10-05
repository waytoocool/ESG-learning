#!/usr/bin/env python3
"""
Seed Dimensional Test Data
Creates dimensions, dimension values, and field-dimension associations for testing Phase 2.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.dimension import Dimension, DimensionValue, FieldDimension
from app.models.framework import FrameworkDataField
from app.models.company import Company

def seed_dimensional_data():
    """Seed dimensional test data for all companies."""

    print("🚀 Starting dimensional test data seeding...")

    # Get all companies
    companies = Company.query.all()
    print(f"📊 Found {len(companies)} companies")

    for company in companies:
        print(f"\n🏢 Seeding dimensions for: {company.name} (ID: {company.id})")

        # Create dimensions for this company
        dimensions_data = [
            {
                'name': 'Gender',
                'description': 'Gender breakdown for workforce data',
                'values': [
                    {'value': 'Male', 'display_name': 'Male', 'order': 1},
                    {'value': 'Female', 'display_name': 'Female', 'order': 2},
                    {'value': 'Other', 'display_name': 'Other', 'order': 3},
                ]
            },
            {
                'name': 'Age Group',
                'description': 'Age group breakdown',
                'values': [
                    {'value': '<30', 'display_name': 'Under 30', 'order': 1},
                    {'value': '30-50', 'display_name': '30-50 years', 'order': 2},
                    {'value': '>50', 'display_name': 'Over 50', 'order': 3},
                ]
            },
            {
                'name': 'Department',
                'description': 'Department breakdown',
                'values': [
                    {'value': 'IT', 'display_name': 'Information Technology', 'order': 1},
                    {'value': 'Finance', 'display_name': 'Finance', 'order': 2},
                    {'value': 'Operations', 'display_name': 'Operations', 'order': 3},
                    {'value': 'HR', 'display_name': 'Human Resources', 'order': 4},
                ]
            },
        ]

        created_dimensions = {}

        for dim_data in dimensions_data:
            # Check if dimension already exists
            existing_dim = Dimension.query.filter_by(
                name=dim_data['name'],
                company_id=company.id
            ).first()

            if existing_dim:
                print(f"  ⚠️  Dimension '{dim_data['name']}' already exists, skipping...")
                created_dimensions[dim_data['name']] = existing_dim
                continue

            # Create dimension
            dimension = Dimension(
                name=dim_data['name'],
                company_id=company.id,
                description=dim_data['description'],
                is_system_default=False
            )
            db.session.add(dimension)
            db.session.flush()  # Get the dimension_id

            print(f"  ✅ Created dimension: {dim_data['name']}")

            # Create dimension values
            for val_data in dim_data['values']:
                dim_value = DimensionValue(
                    dimension_id=dimension.dimension_id,
                    value=val_data['value'],
                    company_id=company.id,
                    display_name=val_data['display_name'],
                    display_order=val_data['order']
                )
                db.session.add(dim_value)
                print(f"    ➕ Added value: {val_data['display_name']}")

            created_dimensions[dim_data['name']] = dimension

        db.session.commit()

        # Associate dimensions with fields
        print(f"\n  🔗 Associating dimensions with fields...")

        # Get some fields for this company
        fields = FrameworkDataField.query.filter_by(company_id=company.id).limit(10).all()

        if len(fields) >= 3:
            # Field 1: 1D (Gender only)
            field1 = fields[0]
            if not FieldDimension.query.filter_by(field_id=field1.field_id, dimension_id=created_dimensions['Gender'].dimension_id).first():
                fd1 = FieldDimension(
                    field_id=field1.field_id,
                    dimension_id=created_dimensions['Gender'].dimension_id,
                    company_id=company.id,
                    is_required=True
                )
                db.session.add(fd1)
                print(f"  ✅ {field1.field_name} → Gender (1D)")

            # Field 2: 2D (Gender x Age)
            field2 = fields[1]
            if not FieldDimension.query.filter_by(field_id=field2.field_id, dimension_id=created_dimensions['Gender'].dimension_id).first():
                fd2_gender = FieldDimension(
                    field_id=field2.field_id,
                    dimension_id=created_dimensions['Gender'].dimension_id,
                    company_id=company.id,
                    is_required=True
                )
                db.session.add(fd2_gender)

                fd2_age = FieldDimension(
                    field_id=field2.field_id,
                    dimension_id=created_dimensions['Age Group'].dimension_id,
                    company_id=company.id,
                    is_required=True
                )
                db.session.add(fd2_age)
                print(f"  ✅ {field2.field_name} → Gender x Age Group (2D)")

            # Field 3: 3D (Gender x Age x Department)
            field3 = fields[2]
            if not FieldDimension.query.filter_by(field_id=field3.field_id, dimension_id=created_dimensions['Gender'].dimension_id).first():
                fd3_gender = FieldDimension(
                    field_id=field3.field_id,
                    dimension_id=created_dimensions['Gender'].dimension_id,
                    company_id=company.id,
                    is_required=True
                )
                db.session.add(fd3_gender)

                fd3_age = FieldDimension(
                    field_id=field3.field_id,
                    dimension_id=created_dimensions['Age Group'].dimension_id,
                    company_id=company.id,
                    is_required=True
                )
                db.session.add(fd3_age)

                fd3_dept = FieldDimension(
                    field_id=field3.field_id,
                    dimension_id=created_dimensions['Department'].dimension_id,
                    company_id=company.id,
                    is_required=True
                )
                db.session.add(fd3_dept)
                print(f"  ✅ {field3.field_name} → Gender x Age Group x Department (3D)")

            db.session.commit()
        else:
            print(f"  ⚠️  Not enough fields to associate dimensions")

    # Print summary
    print("\n" + "="*60)
    print("📊 DIMENSIONAL DATA SEEDING COMPLETE")
    print("="*60)

    total_dimensions = Dimension.query.count()
    total_values = DimensionValue.query.count()
    total_associations = FieldDimension.query.count()

    print(f"✅ Total Dimensions: {total_dimensions}")
    print(f"✅ Total Dimension Values: {total_values}")
    print(f"✅ Total Field-Dimension Associations: {total_associations}")
    print("\n🎉 Dimensional test data seeding completed successfully!")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        try:
            seed_dimensional_data()
        except Exception as e:
            print(f"\n❌ Error during seeding: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
