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
    - Global framework provider designation for framework classification
    - Timestamps for audit trail
    """
    
    __tablename__ = 'company'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(60), unique=True, nullable=False)  # Used in sub-domain routing
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_global_framework_provider = db.Column(db.Boolean, default=False, nullable=False)
    
    # Fiscal Year Configuration
    fy_end_month = db.Column(db.Integer, nullable=False, default=3)  # March = 3 (default for Apr-Mar FY)
    fy_end_day = db.Column(db.Integer, nullable=False, default=31)   # Last day of March
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships - intentionally minimal to avoid circular dependencies
    # Users will have a company_id foreign key pointing to this model
    # Other tenant-scoped models will reference this via company_id
    
    def __init__(self, name, slug, is_active=True, is_global_framework_provider=False, fy_end_month=3, fy_end_day=31):
        """
        Initialize a new Company.
        
        Args:
            name (str): Display name of the company
            slug (str): URL-safe identifier for subdomain routing
            is_active (bool): Whether the company is active (default: True)
            is_global_framework_provider (bool): Whether this company provides global frameworks (default: False)
            fy_end_month (int): Fiscal year end month (1-12, default: 3 for March)
            fy_end_day (int): Fiscal year end day (1-31, default: 31)
        """
        self.name = name
        self.slug = slug.lower()  # Ensure slug is lowercase for consistency
        self.is_active = is_active
        self.is_global_framework_provider = is_global_framework_provider
        self.fy_end_month = fy_end_month
        self.fy_end_day = fy_end_day
    
    def deactivate(self):
        """Deactivate the company (soft delete)."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self):
        """Activate the company."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def set_as_global_provider(self):
        """
        Set this company as the global framework provider.
        Ensures only one company can be the global provider at a time.
        """
        # First, remove global provider status from any existing provider
        existing_provider = Company.query.filter_by(is_global_framework_provider=True).first()
        if existing_provider and existing_provider.id != self.id:
            existing_provider.is_global_framework_provider = False
            existing_provider.updated_at = datetime.utcnow()
        
        # Set this company as the global provider
        self.is_global_framework_provider = True
        self.updated_at = datetime.utcnow()
    
    def remove_global_provider_status(self):
        """Remove global framework provider status from this company."""
        self.is_global_framework_provider = False
        self.updated_at = datetime.utcnow()
    
    @staticmethod
    def get_global_provider():
        """
        Get the company designated as the global framework provider.
        
        Returns:
            Company: The global framework provider company, or None if not set
        """
        return Company.query.filter_by(
            is_global_framework_provider=True,
            is_active=True
        ).first()
    
    @staticmethod
    def get_global_provider_id():
        """
        Get the ID of the global framework provider company.
        
        Returns:
            int: The company ID of the global provider, or None if not set
        """
        provider = Company.get_global_provider()
        return provider.id if provider else None
    
    @staticmethod
    def set_global_provider(company_id):
        """
        Set a specific company as the global framework provider.
        
        Args:
            company_id (int): The ID of the company to set as global provider
            
        Returns:
            bool: True if successful, False if company not found
        """
        company = Company.query.get(company_id)
        if company and company.is_active:
            company.set_as_global_provider()
            db.session.commit()
            return True
        return False
    
    def get_fy_start_month(self):
        """
        Calculate fiscal year start month based on fiscal year end month.
        
        Returns:
            int: Fiscal year start month (1-12)
        """
        return (self.fy_end_month % 12) + 1
    
    def get_fy_start_date(self, fy_year):
        """
        Get fiscal year start date for a given fiscal year.
        
        Args:
            fy_year (int): The fiscal year (based on the year containing FY end date)
            
        Returns:
            date: The fiscal year start date
        """
        from datetime import date
        start_month = self.get_fy_start_month()
        
        # If FY end is in March (3), FY start is April (4) of previous year
        # If FY end is in December (12), FY start is January (1) of same year
        if start_month > self.fy_end_month:
            start_year = fy_year - 1
        else:
            start_year = fy_year
        
        return date(start_year, start_month, 1)
    
    def get_fy_end_date(self, fy_year):
        """
        Get fiscal year end date for a given fiscal year.
        
        Args:
            fy_year (int): The fiscal year (based on the year containing FY end date)
            
        Returns:
            date: The fiscal year end date
        """
        from datetime import date
        import calendar
        
        # Validate day exists in the month (e.g., Feb 31 doesn't exist)
        max_day = calendar.monthrange(fy_year, self.fy_end_month)[1]
        actual_day = min(self.fy_end_day, max_day)
        
        return date(fy_year, self.fy_end_month, actual_day)
    
    def validate_fy_configuration(self):
        """
        Validate fiscal year configuration fields.
        
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        if not (1 <= self.fy_end_month <= 12):
            return False, f"fy_end_month must be between 1 and 12, got {self.fy_end_month}"
        
        if not (1 <= self.fy_end_day <= 31):
            return False, f"fy_end_day must be between 1 and 31, got {self.fy_end_day}"
        
        # Check if day is valid for the month (using current year as example)
        import calendar
        from datetime import datetime
        current_year = datetime.now().year
        max_day = calendar.monthrange(current_year, self.fy_end_month)[1]
        
        if self.fy_end_day > max_day:
            return False, f"Day {self.fy_end_day} is invalid for month {self.fy_end_month}"
        
        return True, ""
    
    def get_fy_display(self, fy_year):
        """
        Get human-readable fiscal year display for a given FY year.
        
        Args:
            fy_year (int): The fiscal year (based on the year containing FY end date)
            
        Returns:
            str: Human-readable fiscal year display (e.g., "Apr 2024 - Mar 2025")
        """
        month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        fy_start = self.get_fy_start_date(fy_year)
        fy_end = self.get_fy_end_date(fy_year)
        
        return f"{month_names[fy_start.month]} {fy_start.year} - {month_names[fy_end.month]} {fy_end.year}"
    
    def __repr__(self):
        global_status = " (Global Provider)" if self.is_global_framework_provider else ""
        return f'<Company {self.slug}: {self.name}{global_status}>'
    
    def __str__(self):
        return self.name 