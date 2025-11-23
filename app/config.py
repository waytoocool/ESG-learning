import os
from datetime import timedelta

class Config:
    # Application Settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecretkey')
    
    # Database Configuration - single source of truth from environment
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session Configuration for cross-subdomain support (needed for impersonation)
    SESSION_COOKIE_DOMAIN = os.environ.get('SESSION_COOKIE_DOMAIN', None)  # Set to .nip.io for dev, .yourdomain.com for prod
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'  # True for HTTPS
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # Mail Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    # Login Manager Configuration
    LOGIN_VIEW = 'auth.login'

    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_ENABLED = os.environ.get('REDIS_ENABLED', 'False').lower() == 'true'

    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB max file size
    ALLOWED_EXTENSIONS = {
        # Documents
        'pdf', 'doc', 'docx', 'txt', 'rtf',
        # Spreadsheets  
        'xls', 'xlsx', 'csv', 'ods',
        # Images
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff',
        # Archives
        'zip', 'rar', '7z',
        # Presentations
        'ppt', 'pptx'
    }
    
    # Ensure upload directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Enhancement #4: Bulk Excel Upload Configuration
    BULK_UPLOAD_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB for Excel file
    BULK_UPLOAD_MAX_ATTACHMENT_SIZE = 20 * 1024 * 1024  # 20MB per attachment (reuses MAX_CONTENT_LENGTH)
    BULK_UPLOAD_MAX_TOTAL_SIZE = 200 * 1024 * 1024  # 200MB total per batch
    BULK_UPLOAD_MAX_ROWS = 1000  # Maximum rows per upload
    BULK_UPLOAD_ALLOWED_FORMATS = {'.xlsx', '.xls', '.csv'}  # Allowed file formats
    BULK_UPLOAD_SESSION_TIMEOUT = 30 * 60  # 30 minutes session timeout

    # Phase 0: Feature Flags for User Dashboard Enhancements
    # Global kill switch - can disable new interface entirely
    FEATURE_NEW_DATA_ENTRY_ENABLED = os.environ.get('FEATURE_NEW_DATA_ENTRY_ENABLED', 'True').lower() == 'true'
    # Default preference for new users
    FEATURE_NEW_DATA_ENTRY_DEFAULT = os.environ.get('FEATURE_NEW_DATA_ENTRY_DEFAULT', 'False').lower() == 'true'
    # Percentage-based gradual rollout (0-100)
    FEATURE_NEW_DATA_ENTRY_PERCENTAGE = int(os.environ.get('FEATURE_NEW_DATA_ENTRY_PERCENTAGE', '10'))
    # A/B testing configuration
    AB_TEST_ENABLED = os.environ.get('AB_TEST_ENABLED', 'False').lower() == 'true'
    AB_TEST_SAMPLE_SIZE = int(os.environ.get('AB_TEST_SAMPLE_SIZE', '100'))

    # Add MIME types configuration
    MIMETYPES = {
        '.js': 'application/javascript',
        '.mjs': 'application/javascript',
        '.css': 'text/css',
        '.html': 'text/html',
        '.txt': 'text/plain',
        '.json': 'application/json'
    }

class DevelopmentConfig(Config):
    DEBUG = True
    
    # Dynamic session cookie domain handling
    # If SESSION_COOKIE_DOMAIN is explicitly set in env, use that
    # Otherwise, detect if we're running under nip.io and set accordingly
    raw_domain = os.environ.get("SESSION_COOKIE_DOMAIN")
    if raw_domain is not None:
        SESSION_COOKIE_DOMAIN = raw_domain
    else:
        # Get host from environment or request
        host = os.getenv("FLASK_RUN_HOST", "")
        # For nip.io domains, make cookie valid for all subdomains
        SESSION_COOKIE_DOMAIN = ".127-0-0-1.nip.io" if host.endswith(".nip.io") else None
    
    # Ensure session cookie settings are correct for development
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # Allow redirects while maintaining security

class ProductionConfig(Config):
    DEBUG = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/var/www/uploads')
    REDIS_ENABLED = os.environ.get('REDIS_ENABLED', 'True').lower() == 'true'
    SESSION_COOKIE_SECURE = True  # HTTPS required in production

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_uploads')
