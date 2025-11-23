"""
Cleanup script to fix duplicate active assignments
Run this before implementing the database constraint
"""
from app import create_app, db
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

    print(f"🔍 Found {len(duplicates)} field-entity-company combinations with duplicate actives\n")

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

        print(f"📝 Field: {field_id[:8]}..., Entity: {entity_id}, Company: {company_id}")
        print(f"   Active count: {active_count}")
        print(f"   Keep active: v{highest_version['version']} ({highest_version['id'][:8]}...)")
        supersede_list = [f"v{x['version']} ({x['id'][:8]}...)" for x in others_to_supersede]
        print(f"   Supersede: {supersede_list}")

        if dry_run:
            print(f"   [DRY RUN] Would supersede {len(others_to_supersede)} assignment(s)\n")
            fixed_count += len(others_to_supersede)
            continue

        # Actually fix it
        try:
            for assignment_data in others_to_supersede:
                assignment = DataPointAssignment.query.get(assignment_data['id'])
                if assignment:
                    old_status = assignment.series_status
                    assignment.series_status = 'superseded'
                    print(f"   ✓ Superseded: {assignment_data['id'][:8]}... (v{assignment_data['version']}): {old_status} → superseded")
                    fixed_count += 1

            db.session.commit()
            print(f"   ✅ Successfully fixed {len(others_to_supersede)} duplicate(s)\n")

        except Exception as e:
            db.session.rollback()
            print(f"   ❌ Error fixing duplicates: {str(e)}\n")
            error_count += 1

    return {"fixed": fixed_count, "errors": error_count}

if __name__ == "__main__":
    import sys

    # Create Flask app context
    app = create_app()
    with app.app_context():
        # Check for --execute flag
        execute = '--execute' in sys.argv

        if not execute:
            print("="*80)
            print("DRY RUN MODE - No changes will be made")
            print("Add --execute flag to actually fix the duplicates")
            print("="*80)
            print()

        results = fix_duplicates(dry_run=not execute)

        print("="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Fixed: {results['fixed']}")
        print(f"Errors: {results['errors']}")
        print("="*80)

        if not execute and results['fixed'] > 0:
            print("\n💡 To apply these changes, run: python app/utils/fix_duplicate_active_assignments.py --execute")
