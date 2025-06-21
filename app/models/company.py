from ..extensions import db
from datetime import datetime


class Company(db.Model):
    """
    Company model for multi-tenant architecture.
    
    This model represents tenant companies in the ESG DataVault system.
    Each company is identified by a unique slug used for subdomain routing
    (e.g., 'acme' for acme.localhost). 
    
    The multi-tenant architecture uses application-level tenant isolation
    where all tenant-scoped data is filtered by company_id in the application layer.
    Super admins operate at the system level and can manage multiple companies.
    
    Key features:
    - Unique slug for subdomain-based tenant identification
    - Active/inactive status for tenant management
    - Timestamps for audit trail
    """
    
    __tablename__ = 'company'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(60), unique=True, nullable=False)  # Used in sub-domain routing
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships - intentionally minimal to avoid circular dependencies
    # Users will have a company_id foreign key pointing to this model
    # Other tenant-scoped models will reference this via company_id
    
    def __init__(self, name, slug, is_active=True):
        """
        Initialize a new Company.
        
        Args:
            name (str): Display name of the company
            slug (str): URL-safe identifier for subdomain routing
            is_active (bool): Whether the company is active (default: True)
        """
        self.name = name
        self.slug = slug.lower()  # Ensure slug is lowercase for consistency
        self.is_active = is_active
    
    def deactivate(self):
        """Deactivate the company (soft delete)."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self):
        """Activate the company."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Company {self.slug}: {self.name}>'
    
    def __str__(self):
        return self.name 