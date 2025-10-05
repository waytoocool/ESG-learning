import os
import logging
from werkzeug.security import generate_password_hash
from sqlalchemy import text
from app.extensions import db
from app.models import User, Company, Framework, FrameworkDataField, DataPointAssignment, Topic, Entity
import uuid
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

def ensure_super_admin():
    """
    Ensure exactly one SUPER_ADMIN user exists in the system.
    
    This function is idempotent - safe to run multiple times.
    Creates a SUPER_ADMIN user only if none exists.
    
    Environment Variables:
        SUPER_ADMIN_EMAIL: Email for the super admin (default: admin@yourdomain.com)
        SUPER_ADMIN_PASSWORD: Password for the super admin (default: changeme)
        SUPER_ADMIN_USERNAME: Username for the super admin (default: superadmin)
    
    Returns:
        tuple: (bool: True if a new SUPER_ADMIN was created, User: the super admin user object)
    """
    # Use raw SQL to check for existing SUPER_ADMIN to avoid schema caching issues
    try:
        super_admin_user = User.query.filter_by(role='SUPER_ADMIN').first()
        
        if super_admin_user:
            print("[seed-data] 🔁 SUPER_ADMIN already exists")
            logger.info(f"SUPER_ADMIN already exists: {super_admin_user.email}")
            return False, super_admin_user
    except Exception as e:
        logger.error(f"Database schema check for SUPER_ADMIN failed: {str(e)}")
        print(f"[seed-data] ⚠️  Database schema check failed: {str(e)}")
        raise
    
    # Get environment variables with safe defaults
    admin_email = os.getenv("SUPER_ADMIN_EMAIL", "admin@yourdomain.com").lower().strip()
    admin_password = os.getenv("SUPER_ADMIN_PASSWORD", "changeme")
    admin_name = os.getenv("SUPER_ADMIN_USERNAME", "superadmin")
    
    # Log warning about default credentials in production
    if admin_email == "admin@yourdomain.com" or admin_password == "changeme":
        logger.warning("Using default SUPER_ADMIN credentials. Please set SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD environment variables in production!")
        print("[seed-data] ⚠️  WARNING: Using default credentials. Set SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD env vars!")
    
    # Create SUPER_ADMIN user
    try:
        new_super_admin = User(
            name=admin_name,
            email=admin_email,
            role="SUPER_ADMIN",
            company_id=None, # Super admin is not tied to a specific company
            is_active=True,
            is_email_verified=True
        )
        new_super_admin.set_password(admin_password)
        db.session.add(new_super_admin)
        db.session.commit()
        
        print(f"[seed-data] ✅ SUPER_ADMIN created: {admin_email}")
        logger.info(f"SUPER_ADMIN user created successfully: {admin_email}")
        return True, new_super_admin
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create SUPER_ADMIN user: {str(e)}")
        print(f"[seed-data] ❌ Failed to create SUPER_ADMIN: {str(e)}")
        raise

def _create_sample_frameworks_and_data(company_id):
    """
    Creates sample frameworks, data fields, and assignments for a given company.
    """
    if Framework.query.filter_by(company_id=company_id).first():
        print(f"[seed-data] 🔁 Sample frameworks already exist for company {company_id}. Skipping.")
        return

    print(f"[seed-data] 🚀 Creating sample frameworks and data for company {company_id}...")

    # --- 1. Create Sample Frameworks ---
    frameworks_to_create = [
        {"name": "Custom ESG Framework", "description": "A custom framework tailored for specific reporting needs."},
        {"name": "GRI Standards 2021", "description": "Global Reporting Initiative Universal Standards 2021."},
        {"name": "SASB Standards", "description": "Sustainability Accounting Standards Board industry-specific standards."},
    ]

    created_frameworks = []
    for fw_data in frameworks_to_create:
        framework = Framework(
            framework_id=str(uuid.uuid4()),
            framework_name=fw_data["name"],
            description=fw_data["description"],
            company_id=company_id
        )
        db.session.add(framework)
        created_frameworks.append(framework)
    db.session.flush() # Flush to get framework_ids

    # --- 2. Create Sample Topics and Data Fields ---
    sample_topics_and_fields = {
        "Custom ESG Framework": [
            {"topic_name": "Energy Management", "fields": [
                {"name": "Electricity Consumption", "code": "ELEC_CONS", "type": "NUMBER", "unit": "kWh"},
                {"name": "Renewable Energy Used", "code": "RENEW_ENERGY", "type": "NUMBER", "unit": "kWh"},
            ]},
            {"topic_name": "Water Usage", "fields": [
                {"name": "Total Water Withdrawal", "code": "WATER_WITHDRAW", "type": "NUMBER", "unit": "m3"},
            ]},
        ],
        "GRI Standards 2021": [
            {"topic_name": "GRI 305: Emissions", "fields": [
                {"name": "GHG Emissions Scope 1", "code": "GRI_GHG_S1", "type": "NUMBER", "unit": "tonnes CO2e"},
                {"name": "GHG Emissions Scope 2", "code": "GRI_GHG_S2", "type": "NUMBER", "unit": "tonnes CO2e"},
            ]},
            {"topic_name": "GRI 403: Occupational Health and Safety", "fields": [
                {"name": "Number of Fatalities", "code": "GRI_FATALITIES", "type": "NUMBER", "unit": "count"},
            ]},
        ],
        "SASB Standards": [
            {"topic_name": "GHG Emissions (SASB)", "fields": [
                {"name": "Total GHG Emissions", "code": "SASB_TOTAL_GHG", "type": "NUMBER", "unit": "tonnes CO2e"},
            ]},
            {"topic_name": "Water Management (SASB)", "fields": [
                {"name": "Water Recycled", "code": "SASB_WATER_RECYCLED", "type": "NUMBER", "unit": "m3"},
            ]},
        ],
    }

    created_fields = []
    for framework in created_frameworks:
        if framework.framework_name in sample_topics_and_fields:
            for topic_data in sample_topics_and_fields[framework.framework_name]:
                topic = Topic(
                    name=topic_data["topic_name"],
                    framework_id=framework.framework_id,
                    parent_id=None,
                    company_id=company_id,
                    description=f"Topic for {topic_data['topic_name']}"
                )
                db.session.add(topic)
                db.session.flush() # Flush to get topic_id

                for field_data in topic_data["fields"]:
                    field = FrameworkDataField(
                        field_id=str(uuid.uuid4()),
                        framework_id=framework.framework_id,
                        company_id=company_id,
                        field_name=field_data["name"],
                        field_code=field_data["code"],
                        description=f"Description for {field_data["name"]}",
                        unit_category=field_data["unit"].split(' ')[0] if field_data["unit"] else None, # Simple guess
                        default_unit=field_data["unit"],
                        value_type="NUMBER" if field_data["type"] == "Numeric" else field_data["type"],
                        topic_id=topic.topic_id,
                        is_computed=False
                    )
                    db.session.add(field)
                    created_fields.append(field)
    db.session.flush() # Flush to get field_ids

    # --- 3. Create a Sample Entity ---
    sample_entity = Entity.query.filter_by(company_id=company_id, name="Sample Location").first()
    if not sample_entity:
        sample_entity = Entity(
            name="Sample Location",
            entity_type="Office",
            company_id=company_id
        )
        db.session.add(sample_entity)
    db.session.flush() # Flush to get entity_id

    # --- 4. Create Random DataPointAssignments for coverage demo ---
    # Assign about 70% of fields to the sample entity
    import random
    assigned_count = 0
    for field in created_fields:
        if random.random() < 0.7: # 70% chance to assign
            assignment = DataPointAssignment(
                field_id=field.field_id,
                entity_id=sample_entity.id,
                frequency="Annual",
                assigned_by=User.query.filter_by(role='SUPER_ADMIN').first().id,
                company_id=company_id
            )
            db.session.add(assignment)
            assigned_count += 1
    db.session.commit()

    print(f"[seed-data] ✅ Created {len(created_frameworks)} frameworks, {len(created_fields)} fields, and {assigned_count} assignments.")

def verify_seed_state():
    """
    Verify the expected state after seeding.
    
    Returns:
        dict: State information including user and company counts
    """
    
    # Use raw SQL to avoid schema caching issues
    super_admin_count = db.session.query(User).filter_by(role='SUPER_ADMIN').count()
    total_user_count = db.session.query(User).count()
    company_count = db.session.query(Company).count()
    framework_count = db.session.query(Framework).count()
    field_count = db.session.query(FrameworkDataField).count()
    assignment_count = db.session.query(DataPointAssignment).count()
    
    state = {
        'super_admin_count': super_admin_count,
        'total_user_count': total_user_count,
        'company_count': company_count,
        'framework_count': framework_count,
        'field_count': field_count,
        'assignment_count': assignment_count
    }
    
    print(f"[seed-data] 📊 Current state: {super_admin_count} SUPER_ADMIN(s), {total_user_count} total users, {company_count} companies, {framework_count} frameworks, {field_count} fields, {assignment_count} assignments.")
    logger.info(f"Seed state verification: {state}")
    
    return state


def create_initial_data():
    """
    Main seed data function for multi-tenant ESG DataVault.
    
    This function ensures the system has the minimum required data:
    1. Exactly one SUPER_ADMIN user
    2. Sample companies, frameworks, and data points for demonstration.
    
    This is idempotent and safe to run multiple times.
    """
    print("[seed-data] 🚀 Starting initial data seeding...")
    logger.info("Starting initial data seeding process")
    
    try:
        # Ensure SUPER_ADMIN exists
        super_admin_created, super_admin_user = ensure_super_admin()
        
        # Ensure a default company exists for seeding tenant-scoped data
        default_company = Company.query.filter_by(name="Default Seed Company").first()
        if not default_company:
            default_company = Company(
                name="Default Seed Company",
                slug="default-seed-company"
            )
            db.session.add(default_company)
            db.session.commit()
            print(f"[seed-data] ✅ Default Seed Company created: {default_company.name}")
            logger.info(f"Default Seed Company created: {default_company.name}")
        
        # Set the Default Seed Company as the global framework provider
        if not default_company.is_global_framework_provider:
            default_company.set_as_global_provider()
            db.session.commit()
            print(f"[seed-data] ✅ Default Seed Company set as global framework provider")
            logger.info(f"Default Seed Company set as global framework provider")
        
        # Update super admin's company_id if it's not set (for tenant-scoped operations)
        if not super_admin_user.company_id:
            super_admin_user.company_id = default_company.id
            db.session.add(super_admin_user)
            db.session.commit()
            print(f"[seed-data] ✅ SUPER_ADMIN {super_admin_user.email} assigned to Default Seed Company.")

        # Create sample frameworks and data for the default company
        _create_sample_frameworks_and_data(default_company.id)
        
        # Create test companies and comprehensive test data (if enabled)
        create_test_data = os.getenv("CREATE_TEST_DATA", "true").lower() == "true"
        if create_test_data:
            _create_test_companies_and_users()
        else:
            print("[seed-data] ⏭️ Test data creation disabled (set CREATE_TEST_DATA=true to enable)")

        # NEW: Backfill entity assignments for any existing users without an entity
        _backfill_user_entity_assignments()
        
        # Verify final state
        state = verify_seed_state()
        
        # Validate expected state (optional, but good for debugging seeding issues)
        if state['super_admin_count'] != 1:
            raise ValueError(f"Expected exactly 1 SUPER_ADMIN, found {state['super_admin_count']}")
        
        if state['company_count'] < 1: # At least one company should exist now
            raise ValueError(f"Expected at least 1 company, found {state['company_count']}")

        if state['framework_count'] < 3: # Expected at least 3 sample frameworks
            raise ValueError(f"Expected at least 3 frameworks, found {state['framework_count']}")

        if state['field_count'] < 5: # Expected a reasonable number of fields
            raise ValueError(f"Expected at least 5 fields, found {state['field_count']}")

        if state['assignment_count'] < 3: # Expected a reasonable number of assignments
            raise ValueError(f"Expected at least 3 assignments, found {state['assignment_count']}")
        
        print("[seed-data] 🎉 Initial data seeding completed successfully!")
        logger.info("Initial data seeding completed successfully")
        
        return {
            'success': True,
            'super_admin_created': super_admin_created,
            'test_data_created': create_test_data,
            'state': state
        }
        
    except Exception as e:
        logger.error(f"Initial data seeding failed: {str(e)}")
        print(f"[seed-data] ❌ Seeding failed: {str(e)}")
        raise


# Legacy function maintained for backwards compatibility
# TODO: Remove in a future version after T4 refactoring
def create_initial_data_legacy(db, Entity, User):
    """
    Legacy initial data creation function.
    
    This function is deprecated in favor of create_initial_data().
    Maintained for backwards compatibility during the transition to multi-tenant architecture.
    
    Args:
        db: Database session (deprecated, using app context instead)
        Entity: Entity model (no longer used in T3)
        User: User model (no longer used directly, imported in functions)
    """
    logger.warning("create_initial_data_legacy called - this function is deprecated")
    print("[seed-data] ⚠️  Using legacy function - please migrate to create_initial_data()")
    
    # Delegate to the new function
    return create_initial_data()

def _create_test_companies_and_users():
    """
    Create test companies and users for development/testing.
    This creates a comprehensive set of test data including multiple companies,
    admin users, regular users, and entities for each company.
    """
    print("[seed-data] 🧪 Creating test companies and users...")
    
    # Check if test companies already exist
    if Company.query.filter(Company.name.like('Test Company%')).first():
        print("[seed-data] 🔁 Test companies already exist. Skipping.")
        return
    
    test_companies_data = [
        {
            "name": "Test Company Alpha",
            "slug": "test-company-alpha",
            "admin": {
                "name": "Alice Admin",
                "email": "alice@alpha.com",
                "password": "admin123"
            },
            "users": [
                {"name": "Bob User", "email": "bob@alpha.com", "password": "user123", "role": "USER"},
                {"name": "Carol Manager", "email": "carol@alpha.com", "password": "manager123", "role": "ADMIN"}
            ],
            "entities": [
                {"name": "Alpha HQ", "entity_type": "Office"},
                {"name": "Alpha Factory", "entity_type": "Manufacturing"}
            ]
        },
        {
            "name": "Test Company Beta",
            "slug": "test-company-beta", 
            "admin": {
                "name": "David Admin",
                "email": "david@beta.com",
                "password": "admin123"
            },
            "users": [
                {"name": "Eve User", "email": "eve@beta.com", "password": "user123", "role": "USER"},
                {"name": "Frank Analyst", "email": "frank@beta.com", "password": "analyst123", "role": "USER"}
            ],
            "entities": [
                {"name": "Beta Main Office", "entity_type": "Office"},
                {"name": "Beta Warehouse", "entity_type": "Warehouse"}
            ]
        },
        {
            "name": "Test Company Gamma",
            "slug": "test-company-gamma",
            "admin": {
                "name": "Grace Admin", 
                "email": "grace@gamma.com",
                "password": "admin123"
            },
            "users": [
                {"name": "Henry User", "email": "henry@gamma.com", "password": "user123", "role": "USER"}
            ],
            "entities": [
                {"name": "Gamma Campus", "entity_type": "Campus"}
            ]
        }
    ]
    
    created_companies = []
    
    for company_data in test_companies_data:
        # Create company
        company = Company(
            name=company_data["name"],
            slug=company_data["slug"]
        )
        db.session.add(company)
        db.session.flush()  # Get company ID
        
        # Create admin user
        admin_data = company_data["admin"]
        admin_user = User(
            name=admin_data["name"],
            email=admin_data["email"],
            role="ADMIN",
            company_id=company.id,
            is_active=True,
            is_email_verified=True
        )
        admin_user.set_password(admin_data["password"])
        db.session.add(admin_user)
        
        # Create regular users and keep references for later entity assignment
        regular_users: list[User] = []
        for user_data in company_data["users"]:
            user = User(
                name=user_data["name"],
                email=user_data["email"],
                role=user_data["role"],
                company_id=company.id,
                is_active=True,
                is_email_verified=True
            )
            user.set_password(user_data["password"])
            db.session.add(user)
            regular_users.append(user)
        
        # Create entities with proper hierarchy
        created_entities = []
        for i, entity_data in enumerate(company_data["entities"]):
            # First entity is always root (parent_id = None)
            # Subsequent entities are children of the first entity
            parent_id = None if i == 0 else created_entities[0].id
            
            entity = Entity(
                name=entity_data["name"],
                entity_type=entity_data["entity_type"],
                company_id=company.id,
                parent_id=parent_id
            )
            db.session.add(entity)
            db.session.flush()  # Get entity ID for potential parent reference
            created_entities.append(entity)
        
        # ----------------------------------------------------
        # Assign entities to users (admin -> root, users -> child)
        # ----------------------------------------------------
        if created_entities:
            root_entity_id = created_entities[0].id
            admin_user.entity_id = root_entity_id
            db.session.add(admin_user)
            
            # Determine child entity (if any)
            child_entity_id = created_entities[1].id if len(created_entities) > 1 else root_entity_id
            for user_obj in regular_users:
                # If the user is an ADMIN, assign the root entity; otherwise assign the child entity
                if user_obj.role == "ADMIN":
                    user_obj.entity_id = root_entity_id
                else:
                    user_obj.entity_id = child_entity_id
                db.session.add(user_obj)
        
        created_companies.append(company)
        db.session.flush()
    
    db.session.commit()
    
    print(f"[seed-data] ✅ Created {len(created_companies)} test companies with users and entities")
    
    # Create comprehensive frameworks for each test company
    for company in created_companies:
        _create_comprehensive_test_frameworks(company.id)

def _create_comprehensive_test_frameworks(company_id):
    """
    Create comprehensive test frameworks with varied coverage for a company.
    Based on the test_frameworks_api.py setup_framework_data fixture.
    """
    print(f"[seed-data] 🔧 Creating comprehensive test frameworks for company {company_id}...")
    
    # Get admin user for assignments
    admin_user = User.query.filter_by(company_id=company_id, role="ADMIN").first()
    if not admin_user:
        print(f"[seed-data] ⚠️ No admin user found for company {company_id}, skipping frameworks")
        return
    
    # Get an entity for assignments
    entity = Entity.query.filter_by(company_id=company_id).first()
    if not entity:
        print(f"[seed-data] ⚠️ No entity found for company {company_id}, skipping frameworks")
        return
    
    frameworks_data = [
        {
            "name": "High Coverage Framework",
            "description": "Framework with high data coverage for testing",
            "topic": "Energy Management",
            "field_count": 10,
            "coverage_ratio": 0.8  # 80% coverage
        },
        {
            "name": "Low Coverage Framework", 
            "description": "Framework with low data coverage for testing",
            "topic": "Water Management",
            "field_count": 10,
            "coverage_ratio": 0.2  # 20% coverage
        },
        {
            "name": "New Framework",
            "description": "Recently created framework with no coverage",
            "topic": "Waste Management",
            "field_count": 5,
            "coverage_ratio": 0.0  # 0% coverage
        },
        {
            "name": "Complete Framework",
            "description": "Framework with complete data coverage",
            "topic": "Emissions Tracking",
            "field_count": 6,
            "coverage_ratio": 1.0  # 100% coverage
        },
        {
            "name": "Searchable Test Framework",
            "description": "Framework specifically for search functionality testing",
            "topic": "Social Impact",
            "field_count": 8,
            "coverage_ratio": 0.5  # 50% coverage
        }
    ]
    
    for fw_data in frameworks_data:
        # Create framework
        framework = Framework(
            framework_id=str(uuid.uuid4()),
            framework_name=fw_data["name"],
            description=fw_data["description"],
            company_id=company_id
        )
        db.session.add(framework)
        db.session.flush()
        
        # Create topic
        topic = Topic(
            name=fw_data["topic"],
            framework_id=framework.framework_id,
            company_id=company_id,
            description=f"Topic for {fw_data['topic']}"
        )
        db.session.add(topic)
        db.session.flush()
        
        # Create fields
        fields = []
        for i in range(fw_data["field_count"]):
            field = FrameworkDataField(
                field_id=str(uuid.uuid4()),
                framework_id=framework.framework_id,
                company_id=company_id,
                field_name=f"{fw_data['name']} Field {i+1}",
                field_code=f"{fw_data['name'].upper().replace(' ', '_')}_F{i+1}",
                description=f"Test field {i+1} for {fw_data['name']}",
                unit_category="energy" if "energy" in fw_data["topic"].lower() else "count",
                default_unit="kWh" if "energy" in fw_data["topic"].lower() else "units",
                value_type="NUMBER",
                topic_id=topic.topic_id,
                is_computed=False
            )
            db.session.add(field)
            fields.append(field)
        
        db.session.flush()
        
        # Create assignments based on coverage ratio
        coverage_count = int(fw_data["field_count"] * fw_data["coverage_ratio"])
        for i in range(coverage_count):
            assignment = DataPointAssignment(
                field_id=fields[i].field_id,
                entity_id=entity.id,
                frequency="Annual",
                assigned_by=admin_user.id,
                company_id=company_id
            )
            db.session.add(assignment)
    
    db.session.commit()
    print(f"[seed-data] ✅ Created {len(frameworks_data)} comprehensive test frameworks for company {company_id}")

def _backfill_user_entity_assignments():
    """
    Assign an entity to every user whose `entity_id` is NULL.
    Logic:
        • For each company, find the root entity (parent_id is None).
        • The root entity is assigned to any ADMIN users missing an entity.
        • A direct child of the root (if any) is assigned to USER-role users; if no child exists, fall back to root.
    This keeps the hierarchy consistent with newly-seeded data while ensuring no orphaned users remain.
    """
    print("[seed-data] 🔄 Backfilling entity assignments for existing users…")

    companies = Company.query.all()
    total_updated = 0

    for company in companies:
        root_entity = Entity.query.filter_by(company_id=company.id, parent_id=None).first()
        if not root_entity:
            # No entities at all for this company; skip.
            continue

        # Prefer the first child entity (if present) for regular users
        child_entity = Entity.query.filter_by(company_id=company.id, parent_id=root_entity.id).first()
        if not child_entity:
            child_entity = root_entity

        # Backfill admins
        admins_to_update = User.query.filter_by(company_id=company.id, role="ADMIN", entity_id=None).all()
        for admin in admins_to_update:
            admin.entity_id = root_entity.id
            db.session.add(admin)
            total_updated += 1

        # Backfill regular users
        users_to_update = User.query.filter(User.company_id==company.id, User.role=="USER", User.entity_id==None).all()
        for user in users_to_update:
            user.entity_id = child_entity.id
            db.session.add(user)
            total_updated += 1

    if total_updated:
        db.session.commit()
        print(f"[seed-data] ✅ Backfilled entity assignments for {total_updated} user(s).")
    else:
        print("[seed-data] ✅ All users already have an entity. No backfill needed.")
