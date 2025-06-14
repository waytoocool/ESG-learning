import os
from datetime import timedelta

class Config:
    # Application Settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecretkey')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///./esg_data.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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

class ProductionConfig(Config):
    DEBUG = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/var/www/uploads')
    REDIS_ENABLED = os.environ.get('REDIS_ENABLED', 'True').lower() == 'true'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_uploads')
