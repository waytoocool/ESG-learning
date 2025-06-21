from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
import mimetypes
import os

# Load environment variables FIRST before importing any config
load_dotenv()

from app.services.initial_data import create_initial_data
from app.extensions import db, login_manager, mail, migrate
from .config import DevelopmentConfig
from .utils.helpers import init_url_versioning, init_caching

def create_app(config_object=DevelopmentConfig):
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config_object)

    # Initialize utility helpers
    init_url_versioning(app)
    init_caching(app)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # Initialize ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Initialize Redis
    from .services.redis import init_redis
    init_redis(app)

    # Register multi-tenant middleware
    from .middleware.tenant import load_tenant
    app.before_request(load_tenant)
    
    # Register impersonation status check
    from .routes.superadmin import check_impersonation_status
    app.before_request(check_impersonation_status)

    # Register routes
    from .routes import blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    # Initialize database tables
    with app.app_context():
        # Import models for migration compatibility
        from .models import User, Entity, Framework, DataPoint, ESGData, Company
        
        # Check if this is a test environment that wants to skip migrations
        if app.config.get('SKIP_MIGRATIONS', False):
            db.create_all()
            app.logger.info("Test mode - forcing db.create_all()")
            print("[app-init] 🧪 Test mode - creating all tables")
        else:
            # Check if migrations exist - if so, assume alembic manages the schema
            migrations_dir = os.path.join(os.path.dirname(app.root_path), 'migrations', 'versions')
            if os.path.exists(migrations_dir) and os.listdir(migrations_dir):
                app.logger.info("Migrations detected - skipping db.create_all()")
                print("[app-init] 🔧 Using Alembic migrations for schema management")
            else:
                # Only create tables if no migrations exist (for development/testing)
                db.create_all()
                app.logger.info("No migrations found - using db.create_all()")
        
        # T-3 Seed data: Ensure SUPER_ADMIN user exists (skip in test mode and during migrations)
        if not app.config.get('SKIP_MIGRATIONS', False) and not os.environ.get('FLASK_MIGRATE_RUNNING'):
            try:
                create_initial_data()
            except Exception as e:
                # Log error but don't crash the app startup
                app.logger.error(f"Failed to create initial data: {str(e)}")
                print(f"[app-init] ⚠️  Failed to create initial data: {str(e)}")
        else:
            if app.config.get('SKIP_MIGRATIONS', False):
                print("[app-init] 🧪 Test mode - skipping initial data seeding")
            else:
                print("[app-init] 🔄 Migration mode - skipping initial data seeding")

    # Register MIME types
    for ext, mime_type in app.config['MIMETYPES'].items():
        mimetypes.add_type(mime_type, ext)

    # Register CLI commands
    register_cli_commands(app)

    return app


def register_cli_commands(app):
    """Register custom CLI commands for the Flask app."""
    
    @app.cli.command("seed-data")
    def seed_data_command():
        """Seed default SUPER_ADMIN user and essential data."""
        print("🌱 Running manual seed data command...")
        try:
            result = create_initial_data()
            if result['success']:
                print(f"✅ Seed data command completed successfully!")
                if result['super_admin_created']:
                    print("   └── New SUPER_ADMIN user created")
                else:
                    print("   └── SUPER_ADMIN user already existed")
                print(f"   └── Final state: {result['state']}")
            else:
                print("❌ Seed data command failed")
        except Exception as e:
            print(f"❌ Seed data command failed: {str(e)}")
            raise
    
    @app.cli.command("verify-seed")
    def verify_seed_command():
        """Verify the current seed data state."""
        print("🔍 Verifying seed data state...")
        try:
            from app.services.initial_data import verify_seed_state
            state = verify_seed_state()
            
            print("✅ Seed state verification completed:")
            print(f"   └── SUPER_ADMIN users: {state['super_admin_count']}")
            print(f"   └── Total users: {state['total_user_count']}")
            print(f"   └── Companies: {state['company_count']}")
            
            # Validate expected state
            if state['super_admin_count'] == 0:
                print("⚠️  WARNING: No SUPER_ADMIN users found!")
            elif state['super_admin_count'] > 1:
                print(f"⚠️  WARNING: Multiple SUPER_ADMIN users found ({state['super_admin_count']})!")
            else:
                print("✅ Seed state is healthy")
                
        except Exception as e:
            print(f"❌ Seed verification failed: {str(e)}")
            raise
