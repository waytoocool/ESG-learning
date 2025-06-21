import os
import logging
from werkzeug.security import generate_password_hash
from sqlalchemy import text

# Set up logging
logger = logging.getLogger(__name__)

def ensure_super_admin():
    """
    Ensure exactly one SUPER_ADMIN user exists in the system.
    
    This function is idempotent - safe to run multiple times.
    Creates a SUPER_ADMIN user only if none exists.
    
    Environment Variables:
        SUPER_ADMIN_EMAIL: Email for the super admin (default: admin@example.com)
        SUPER_ADMIN_PASSWORD: Password for the super admin (default: changeme)
        SUPER_ADMIN_USERNAME: Username for the super admin (default: superadmin)
    
    Returns:
        bool: True if a new SUPER_ADMIN was created, False if one already existed
    """
    from app.extensions import db
    
    # Use raw SQL to check for existing SUPER_ADMIN to avoid schema caching issues
    try:
        result = db.session.execute(text("SELECT COUNT(*) FROM user WHERE role = 'SUPER_ADMIN'"))
        super_admin_count = result.fetchone()[0]
        
        if super_admin_count > 0:
            print("[seed-data] 🔁 SUPER_ADMIN already exists")
            logger.info(f"SUPER_ADMIN already exists (count: {super_admin_count})")
            return False
    except Exception as e:
        logger.error(f"Raw SQL check for SUPER_ADMIN failed: {str(e)}")
        # If raw SQL fails, the schema might not be ready yet
        print(f"[seed-data] ⚠️  Database schema check failed: {str(e)}")
        raise
    
    # Get environment variables with safe defaults
    admin_email = os.getenv("SUPER_ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("SUPER_ADMIN_PASSWORD", "changeme")
    admin_username = os.getenv("SUPER_ADMIN_USERNAME", "superadmin")
    
    # Log warning about default credentials in production
    if admin_email == "admin@example.com" or admin_password == "changeme":
        logger.warning("Using default SUPER_ADMIN credentials. Please set SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD environment variables in production!")
        print("[seed-data] ⚠️  WARNING: Using default credentials. Set SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD env vars!")
    
    # Create SUPER_ADMIN user using raw SQL to avoid schema issues
    try:
        # Hash the password manually
        hashed_password = generate_password_hash(admin_password, method='pbkdf2:sha256')
        
        # Insert using raw SQL with proper parameterization
        insert_sql = text("""
        INSERT INTO user (username, email, password, role, company_id, is_active, is_email_verified)
        VALUES (:username, :email, :password, 'SUPER_ADMIN', NULL, 1, 1)
        """)
        
        db.session.execute(insert_sql, {
            'username': admin_username,
            'email': admin_email,
            'password': hashed_password
        })
        db.session.commit()
        
        print(f"[seed-data] ✅ SUPER_ADMIN created: {admin_email}")
        logger.info(f"SUPER_ADMIN user created successfully: {admin_email}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create SUPER_ADMIN user with raw SQL: {str(e)}")
        print(f"[seed-data] ❌ Failed to create SUPER_ADMIN: {str(e)}")
        raise


def verify_seed_state():
    """
    Verify the expected state after seeding.
    
    Returns:
        dict: State information including user and company counts
    """
    from app.extensions import db
    
    try:
        # Use raw SQL to avoid schema caching issues
        super_admin_result = db.session.execute(text("SELECT COUNT(*) FROM user WHERE role = 'SUPER_ADMIN'"))
        super_admin_count = super_admin_result.fetchone()[0]
        
        total_users_result = db.session.execute(text("SELECT COUNT(*) FROM user"))
        total_user_count = total_users_result.fetchone()[0]
        
        company_result = db.session.execute(text("SELECT COUNT(*) FROM company"))
        company_count = company_result.fetchone()[0]
        
    except Exception as e:
        logger.warning(f"Raw SQL verification failed, using fallback values: {str(e)}")
        # Fallback to safe defaults if raw SQL fails
        super_admin_count = 0
        total_user_count = 0
        company_count = 0
    
    state = {
        'super_admin_count': super_admin_count,
        'total_user_count': total_user_count,
        'company_count': company_count
    }
    
    print(f"[seed-data] 📊 Current state: {super_admin_count} SUPER_ADMIN(s), {total_user_count} total users, {company_count} companies")
    logger.info(f"Seed state verification: {state}")
    
    return state


def create_initial_data():
    """
    Main seed data function for multi-tenant ESG DataVault.
    
    This function ensures the system has the minimum required data:
    1. Exactly one SUPER_ADMIN user
    2. No companies (companies are created by SUPER_ADMIN through the interface)
    
    This is idempotent and safe to run multiple times.
    """
    print("[seed-data] 🚀 Starting initial data seeding...")
    logger.info("Starting initial data seeding process")
    
    try:
        # Ensure SUPER_ADMIN exists
        super_admin_created = ensure_super_admin()
        
        # Verify final state
        state = verify_seed_state()
        
        # Validate expected state
        if state['super_admin_count'] != 1:
            raise ValueError(f"Expected exactly 1 SUPER_ADMIN, found {state['super_admin_count']}")
        
        if state['company_count'] != 0:
            logger.info(f"Found {state['company_count']} existing companies (this is expected if data already exists)")
        
        print("[seed-data] 🎉 Initial data seeding completed successfully!")
        logger.info("Initial data seeding completed successfully")
        
        return {
            'success': True,
            'super_admin_created': super_admin_created,
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
