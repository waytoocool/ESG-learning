#!/usr/bin/env python3
"""
Seed Computed Fields for Phase 3 Testing
Creates computed fields with formulas, dependencies, and assignments for testing Phase 3 computation context features.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.framework import FrameworkDataField, Framework, FieldVariableMapping
from app.models.company import Company
from app.models.entity import Entity
from app.models.data_assignment import DataPointAssignment
from app.models.esg_data import ESGData

def seed_computed_fields():
    """Seed computed fields for all companies."""

    print("🚀 Starting computed fields seeding...")

    # Get all companies
    companies = Company.query.all()
    print(f"📊 Found {len(companies)} companies")

    for company in companies:
        print(f"\n🏢 Processing company: {company.name} (ID: {company.id})")

        # Get or create a framework for this company
        framework = Framework.query.filter_by(
            company_id=company.id,
            framework_name='High Coverage Framework'
        ).first()

        if not framework:
            print(f"  ⚠️  No 'High Coverage Framework' found for {company.name}, skipping...")
            continue

        # Get some raw fields to use as dependencies
        raw_fields = FrameworkDataField.query.filter_by(
            framework_id=framework.framework_id,
            is_computed=False
        ).limit(5).all()

        if len(raw_fields) < 2:
            print(f"  ⚠️  Not enough raw fields for {company.name}, skipping...")
            continue

        print(f"  ✅ Found {len(raw_fields)} raw fields to use as dependencies")

        # Create computed fields using simple variable names (A-Z)
        computed_fields_data = [
            {
                'name': 'Total Energy Consumption',
                'code': 'COMPUTED_TOTAL_ENERGY',
                'description': 'Sum of all energy consumption sources',
                'formula': 'A + B',
                'variable_mappings': [
                    {'variable': 'A', 'source_field_id': raw_fields[0].field_id},
                    {'variable': 'B', 'source_field_id': raw_fields[1].field_id}
                ],
                'unit': 'kWh'
            },
            {
                'name': 'Energy Efficiency Ratio',
                'code': 'COMPUTED_ENERGY_EFFICIENCY',
                'description': 'Energy consumption per unit output',
                'formula': 'A / B',
                'variable_mappings': [
                    {'variable': 'A', 'source_field_id': raw_fields[0].field_id},
                    {'variable': 'B', 'source_field_id': raw_fields[1].field_id}
                ],
                'unit': 'kWh/unit'
            },
            {
                'name': 'Average Resource Consumption',
                'code': 'COMPUTED_AVG_RESOURCE',
                'description': 'Average of multiple resource consumption metrics',
                'formula': '(A + B) / C',
                'variable_mappings': [
                    {'variable': 'A', 'source_field_id': raw_fields[0].field_id},
                    {'variable': 'B', 'source_field_id': raw_fields[1].field_id},
                    {'variable': 'C', 'source_field_id': raw_fields[2].field_id}
                ],
                'unit': 'units',
                'coefficient': 2  # Since we're dividing by C instead of literal 2
            }
        ]

        # Add a field with more complex formula if we have enough raw fields
        if len(raw_fields) >= 4:
            computed_fields_data.append({
                'name': 'Complex Sustainability Index',
                'code': 'COMPUTED_SUSTAINABILITY_INDEX',
                'description': 'Complex calculation involving multiple factors',
                'formula': '(A + B) * C / D',
                'variable_mappings': [
                    {'variable': 'A', 'source_field_id': raw_fields[0].field_id},
                    {'variable': 'B', 'source_field_id': raw_fields[1].field_id},
                    {'variable': 'C', 'source_field_id': raw_fields[2].field_id},
                    {'variable': 'D', 'source_field_id': raw_fields[3].field_id}
                ],
                'unit': 'index'
            })

        created_computed_fields = []

        for cf_data in computed_fields_data:
            # Check if computed field already exists
            existing_field = FrameworkDataField.query.filter_by(
                framework_id=framework.framework_id,
                field_code=cf_data['code']
            ).first()

            if existing_field:
                print(f"  ⚠️  Computed field '{cf_data['name']}' already exists, skipping...")
                created_computed_fields.append(existing_field)
                continue

            # Create computed field
            computed_field = FrameworkDataField(
                framework_id=framework.framework_id,
                field_name=cf_data['name'],
                field_code=cf_data['code'],
                description=cf_data['description'],
                value_type='NUMBER',
                is_computed=True,
                formula_expression=cf_data['formula'],
                default_unit=cf_data['unit'],
                company_id=company.id
            )
            db.session.add(computed_field)
            db.session.flush()  # Get the field_id

            print(f"  ✅ Created computed field: {cf_data['name']}")

            # Create variable mappings
            for mapping_data in cf_data['variable_mappings']:
                mapping = FieldVariableMapping(
                    computed_field_id=computed_field.field_id,
                    variable_name=mapping_data['variable'],
                    raw_field_id=mapping_data['source_field_id']
                )
                db.session.add(mapping)

            print(f"    ➕ Added {len(cf_data['variable_mappings'])} variable mappings")

            created_computed_fields.append(computed_field)

        db.session.commit()

        # Assign computed fields to entities
        print(f"\n  🔗 Assigning computed fields to entities...")

        entities = Entity.query.filter_by(company_id=company.id).all()

        for entity in entities:
            for computed_field in created_computed_fields:
                # Check if assignment already exists
                existing_assignment = DataPointAssignment.query.filter_by(
                    field_id=computed_field.field_id,
                    entity_id=entity.id
                ).first()

                if existing_assignment:
                    continue

                # Create assignment
                assignment = DataPointAssignment(
                    field_id=computed_field.field_id,
                    entity_id=entity.id,
                    frequency='Annual',  # Default frequency
                    assigned_by=1,  # System assignment (use admin user ID 1)
                    company_id=company.id
                )
                db.session.add(assignment)

            print(f"    ✅ Assigned {len(created_computed_fields)} computed fields to {entity.name}")

        db.session.commit()

        # Create some historical data for computed fields (for trend testing)
        print(f"\n  📈 Creating historical ESG data for trend testing...")

        from datetime import date, timedelta

        # Create data for the first entity
        if entities:
            test_entity = entities[0]

            for computed_field in created_computed_fields:
                # Create data for the last 12 months
                for months_ago in range(12, 0, -1):
                    reporting_date = date.today() - timedelta(days=months_ago * 30)

                    # Check if data already exists
                    existing_data = ESGData.query.filter_by(
                        field_id=computed_field.field_id,
                        entity_id=test_entity.id,
                        reporting_date=reporting_date
                    ).first()

                    if existing_data:
                        continue

                    # Create some sample calculated values (increasing trend)
                    base_value = 1000
                    trend_value = base_value + (12 - months_ago) * 50  # Increasing trend

                    esg_data = ESGData(
                        entity_id=test_entity.id,
                        field_id=computed_field.field_id,
                        raw_value=str(trend_value),
                        reporting_date=reporting_date,
                        company_id=company.id,
                        calculated_value=trend_value
                    )
                    db.session.add(esg_data)

                print(f"    ✅ Created 12 months of historical data for {computed_field.field_name}")

            db.session.commit()

    # Print summary
    print("\n" + "="*60)
    print("📊 COMPUTED FIELDS SEEDING COMPLETE")
    print("="*60)

    total_computed_fields = FrameworkDataField.query.filter_by(is_computed=True).count()
    total_mappings = FieldVariableMapping.query.count()
    total_assignments = DataPointAssignment.query.join(
        FrameworkDataField,
        DataPointAssignment.field_id == FrameworkDataField.field_id
    ).filter(FrameworkDataField.is_computed == True).count()

    print(f"✅ Total Computed Fields: {total_computed_fields}")
    print(f"✅ Total Variable Mappings: {total_mappings}")
    print(f"✅ Total Computed Field Assignments: {total_assignments}")
    print("\n🎉 Computed fields seeding completed successfully!")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        try:
            seed_computed_fields()
        except Exception as e:
            print(f"\n❌ Error during seeding: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
