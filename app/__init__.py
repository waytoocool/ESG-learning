from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
import mimetypes
import os
import click

# Load environment variables FIRST before importing any config
load_dotenv()

from app.services.initial_data import create_initial_data
from app.extensions import db, login_manager, mail
from .config import DevelopmentConfig
from .utils.helpers import init_url_versioning, init_caching, init_dynamic_session_cookie_domain

def create_app(config_object=DevelopmentConfig):
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config_object)

    # Initialize utility helpers
    init_url_versioning(app)
    init_caching(app)
    init_dynamic_session_cookie_domain(app)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

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
        from .models import User, Entity, Framework, ESGData, Company
        
        # Create all database tables
        db.create_all()
        app.logger.info("Database tables created successfully")
        print("[app-init] 🔧 Database tables created using db.create_all()")
        
        # T-3 Seed data: Ensure SUPER_ADMIN user exists (skip in test mode)
        if not app.config.get('SKIP_MIGRATIONS', False):
            try:
                create_initial_data()
            except Exception as e:
                # Log error but don't crash the app startup
                app.logger.error(f"Failed to create initial data: {str(e)}")
                print(f"[app-init] ⚠️  Failed to create initial data: {str(e)}")
        else:
            print("[app-init] 🧪 Test mode - skipping initial data seeding")

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
    
    @app.cli.command("manage-superadmin")
    @click.option('--action', type=click.Choice(['list', 'change-email', 'reset-password']), required=True, help='Action to perform')
    @click.option('--new-email', help='New email for change-email action')
    @click.option('--new-password', help='New password for reset-password action')
    def manage_superadmin_command(action, new_email, new_password):
        """Manage SUPER_ADMIN user safely."""
        from app.models.user import User
        from app.extensions import db
        
        try:
            if action == 'list':
                super_admins = User.query.filter_by(role='SUPER_ADMIN').all()
                print(f"📋 Found {len(super_admins)} SUPER_ADMIN user(s):")
                for i, user in enumerate(super_admins, 1):
                    print(f"   {i}. ID: {user.id}, Email: {user.email}, Name: {user.name}")
                    print(f"      Company: {user.company.name if user.company else 'None'}")
                    print(f"      Active: {user.is_active}")
                    
            elif action == 'change-email':
                if not new_email:
                    print("❌ --new-email is required for change-email action")
                    return
                    
                super_admin = User.query.filter_by(role='SUPER_ADMIN').first()
                if not super_admin:
                    print("❌ No SUPER_ADMIN user found")
                    return
                    
                old_email = super_admin.email
                super_admin.email = new_email
                db.session.commit()
                print(f"✅ SUPER_ADMIN email changed from {old_email} to {new_email}")
                
            elif action == 'reset-password':
                if not new_password:
                    print("❌ --new-password is required for reset-password action")
                    return
                    
                super_admin = User.query.filter_by(role='SUPER_ADMIN').first()
                if not super_admin:
                    print("❌ No SUPER_ADMIN user found")
                    return
                    
                super_admin.set_password(new_password)
                db.session.commit()
                print(f"✅ SUPER_ADMIN password reset for {super_admin.email}")
                
        except Exception as e:
            print(f"❌ SUPER_ADMIN management failed: {str(e)}")
            raise
