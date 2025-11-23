from ..extensions import db
import uuid
from datetime import datetime, UTC
from sqlalchemy import Enum, event
from .mixins import TenantScopedQueryMixin, TenantScopedModelMixin

class DataPointAssignment(db.Model, TenantScopedQueryMixin, TenantScopedModelMixin):
    """Data Point Assignment model with FY and frequency configuration."""
    
    __tablename__ = 'data_point_assignments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    field_id = db.Column(db.String(36), db.ForeignKey('framework_data_fields.field_id'), nullable=False)
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)
    # Add company_id for tenant isolation - temporarily nullable until T-3 seed data
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    # Removed value_type - now comes from FrameworkDataField.value_type
    unit = db.Column(db.String(10), nullable=True)  # Can override field's default_unit

    # Data Collection Frequency
    frequency = db.Column(Enum('Monthly', 'Quarterly', 'Annual', name='frequency_type'),
                         nullable=False, default='Annual')

    # Validation Configuration
    attachment_required = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment="Whether supporting documents are required for this assignment"
    )
    
    # Material Topic Assignment
    assigned_topic_id = db.Column(db.String(36), db.ForeignKey('topics.topic_id'), nullable=True)
    
    # Phase 1: Assignment versioning and data series support
    data_series_id = db.Column(db.String(36), nullable=True, index=True)  # Groups related assignments
    series_version = db.Column(db.Integer, default=1, nullable=False)  # Version within series
    series_status = db.Column(Enum('active', 'inactive', 'superseded', 'legacy', name='series_status_type'),
                             nullable=False, default='active')
    
    # Metadata
    assigned_date = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Update relationships
    field = db.relationship('FrameworkDataField', backref='assignments')
    entity = db.relationship('Entity', backref='data_assignments')
    assigned_by_user = db.relationship('User', backref='assigned_data_points')
    company = db.relationship('Company', backref='data_point_assignments')
    assigned_topic = db.relationship('Topic', backref='data_point_assignments')
    
    # Phase 4: Enhanced indexes for better query performance (< 50ms target)
    __table_args__ = (
        db.Index('idx_assignment_field_entity', 'field_id', 'entity_id'),
        db.Index('idx_assignment_company', 'company_id'),  # Index for tenant filtering
        db.Index('idx_assignment_topic', 'assigned_topic_id'),  # Index for topic filtering
        db.Index('idx_assignment_series', 'data_series_id', 'series_version'),  # Index for versioning
        db.Index('idx_assignment_status', 'series_status'),  # Index for status filtering
        # Phase 4: Additional performance indexes for assignment resolution
        db.Index('idx_assignment_active_lookup', 'field_id', 'entity_id', 'series_status'),  # Fast active assignment lookup
        db.Index('idx_assignment_company_active', 'company_id', 'series_status'),  # Company-filtered active assignments
        db.Index('idx_assignment_field_company_active', 'field_id', 'company_id', 'series_status'),  # Fast field+company lookup
    )

    def __init__(self, field_id, entity_id, frequency, assigned_by, company_id=None, unit=None, assigned_topic_id=None, data_series_id=None, series_version=1, attachment_required=False):
        self.field_id = field_id
        self.entity_id = entity_id
        self.company_id = company_id
        self.unit = unit
        self.frequency = frequency
        self.assigned_by = assigned_by
        self.assigned_topic_id = assigned_topic_id
        self.data_series_id = data_series_id or str(uuid.uuid4())  # Auto-generate if not provided
        self.series_version = series_version
        self.series_status = 'active'  # FIX: Set default series_status to avoid validation errors
        self.attachment_required = attachment_required

    @property
    def value_type(self):
        """Get value_type from the associated field."""
        return self.field.value_type if self.field else 'TEXT'

    @property 
    def effective_unit(self):
        """Get the effective unit - either assignment override or field default."""
        return self.unit or (self.field.default_unit if self.field else None)
    
    @property
    def effective_topic(self):
        """Get the effective topic - either assigned material topic or framework topic fallback."""
        if self.assigned_topic:
            return self.assigned_topic
        elif self.field and self.field.topic:
            return self.field.topic
        else:
            return None
    
    @property
    def effective_topic_name(self):
        """Get the effective topic name for display purposes."""
        effective_topic = self.effective_topic
        return effective_topic.name if effective_topic else 'Unassigned'
    
    @property
    def effective_topic_path(self):
        """Get the full hierarchical path of the effective topic."""
        effective_topic = self.effective_topic
        return effective_topic.get_full_path() if effective_topic else 'Unassigned'

    def get_valid_reporting_dates(self, fy_year=None, target_date=None):
        """
        Generate list of valid reporting dates based on frequency and company's FY configuration.
        
        Enhanced in Phase 2 to support:
        - Automatic FY detection from target date
        - Multiple FY support for indefinite assignments
        - Better company FY integration
        
        Args:
            fy_year (int, optional): The fiscal year (based on the year containing FY end date)
            target_date (date, optional): Date to determine FY year from (defaults to today)
        
        Returns:
            List[date]: List of valid reporting dates for the fiscal year
        """
        if not self.company:
            # Return empty list instead of raising exception for defensive programming
            return []
        
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta
        
        # Auto-detect FY year if not provided
        if fy_year is None:
            if target_date is None:
                target_date = date.today()
            
            # Use company FY configuration to determine FY year
            fy_end_month = self.company.fy_end_month
            fy_end_day = self.company.fy_end_day
            
            # Check if target_date is before or after FY end for current calendar year
            try:
                import calendar
                max_day = calendar.monthrange(target_date.year, fy_end_month)[1]
                actual_end_day = min(fy_end_day, max_day)
                fy_end_current_year = date(target_date.year, fy_end_month, actual_end_day)
                
                if target_date <= fy_end_current_year:
                    fy_year = target_date.year
                else:
                    fy_year = target_date.year + 1
            except Exception:
                # Fallback to simple year-based calculation
                fy_year = target_date.year
        
        valid_dates = []
        
        # Get FY start and end dates from company configuration
        fy_start = self.company.get_fy_start_date(fy_year)
        fy_end = self.company.get_fy_end_date(fy_year)
        
        if self.frequency == 'Annual':
            # Only FY end date
            valid_dates.append(fy_end)
            
        elif self.frequency == 'Quarterly':
            # Generate quarterly dates
            current_date = fy_start
            while current_date <= fy_end:
                # Last day of quarter
                quarter_end = (current_date + relativedelta(months=3)) - timedelta(days=1)
                if quarter_end <= fy_end:
                    valid_dates.append(quarter_end)
                current_date = current_date + relativedelta(months=3)
                    
        elif self.frequency == 'Monthly':
            # Generate monthly dates
            current_date = fy_start
            while current_date <= fy_end:
                # Last day of month
                month_end = (current_date + relativedelta(months=1)) - timedelta(days=1)
                if month_end <= fy_end:
                    valid_dates.append(month_end)
                current_date = current_date + relativedelta(months=1)
        
        return valid_dates
    
    def is_valid_reporting_date(self, reporting_date, fy_year=None):
        """
        Check if a given date is valid for this assignment.
        
        Enhanced in Phase 2 to auto-detect FY year from the reporting date.
        
        Args:
            reporting_date (date): The date to validate
            fy_year (int, optional): The fiscal year to check against (auto-detected if not provided)
            
        Returns:
            bool: True if the date is valid for reporting
        """
        try:
            valid_dates = self.get_valid_reporting_dates(fy_year, reporting_date)
            return reporting_date in valid_dates
        except Exception:
            # If validation fails, be permissive (return True)
            return True
    
    def get_fy_display(self, fy_year):
        """
        Get human-readable FY display for the specified fiscal year.
        
        Args:
            fy_year (int): The fiscal year (based on the year containing FY end date)
            
        Returns:
            str: Human-readable fiscal year display (e.g., "Apr 2024 - Mar 2025")
        """
        if not self.company:
            return f"FY {fy_year} (No Company Configuration)"
        
        return self.company.get_fy_display(fy_year)
    
    # Phase 2: Assignment versioning methods
    def create_new_version(self, changes, reason, created_by):
        """
        Create a new version of this assignment using the versioning service.
        
        Args:
            changes (dict): Changes to apply to the new version
            reason (str): Reason for creating new version
            created_by (int): User ID creating the version
            
        Returns:
            dict: Result from versioning service
        """
        from ..services.assignment_versioning import AssignmentVersioningService
        
        return AssignmentVersioningService.create_assignment_version(
            self.id, changes, reason, created_by
        )
    
    def supersede(self, reason=None):
        """
        Mark this assignment as superseded.
        
        Args:
            reason (str): Optional reason for superseding
            
        Returns:
            dict: Result from versioning service
        """
        from ..services.assignment_versioning import AssignmentVersioningService
        
        return AssignmentVersioningService.supersede_assignment(self.id, reason)
    
    def get_data_series_versions(self):
        """
        Get all versions in this assignment's data series.
        
        Returns:
            List[DataPointAssignment]: All versions ordered by version number (newest first)
        """
        if not self.data_series_id:
            return [self]  # This assignment only
            
        from ..services.assignment_versioning import AssignmentVersioningService
        
        return AssignmentVersioningService.get_assignment_history(
            data_series_id=self.data_series_id
        )
    
    @staticmethod
    def get_active_for_date(field_id, entity_id, target_date=None):
        """
        Get active assignment for a specific field+entity on a given date.
        
        Args:
            field_id (str): Framework data field ID
            entity_id (int): Entity ID
            target_date (date): Target date (defaults to today)
            
        Returns:
            DataPointAssignment: Active assignment or None
        """
        from ..services.assignment_versioning import AssignmentVersioningService
        
        return AssignmentVersioningService.get_active_assignment(
            field_id, entity_id, target_date
        )
    
    def is_latest_version(self):
        """
        Check if this assignment is the latest version in its data series.
        
        Returns:
            bool: True if this is the latest version
        """
        if not self.data_series_id:
            return True  # Single assignment is always latest
            
        latest_version = DataPointAssignment.query.filter_by(
            data_series_id=self.data_series_id
        ).order_by(DataPointAssignment.series_version.desc()).first()
        
        return latest_version.id == self.id if latest_version else True
    
    def get_data_entry_count(self):
        """
        Get count of ESG data entries associated with this assignment.
        
        Returns:
            int: Number of data entries
        """
        from ..models.esg_data import ESGData
        
        # Count entries linked to this assignment directly
        direct_count = ESGData.query.filter_by(assignment_id=self.id).count()
        
        # Also count entries linked by field+entity (legacy pattern)
        legacy_count = ESGData.query.filter(
            ESGData.field_id == self.field_id,
            ESGData.entity_id == self.entity_id,
            ESGData.assignment_id.is_(None)  # Only count unlinked entries
        ).count()
        
        return direct_count + legacy_count
    
    @property
    def version_display(self):
        """Get display string for version info."""
        if not self.data_series_id:
            return "v1 (original)"
        return f"v{self.series_version}"
    
    @property  
    def status_display(self):
        """Get human-readable status display."""
        status_map = {
            'active': 'Active',
            'superseded': 'Superseded', 
            'legacy': 'Legacy'
        }
        return status_map.get(self.series_status, self.series_status.title())

    def validate_data_integrity(self):
        """
        Validate data integrity for series_status field.

        Returns:
            dict: {'is_valid': bool, 'error': str}
        """
        # Basic validation for series_status
        valid_statuses = ['active', 'inactive', 'superseded', 'legacy']
        if self.series_status not in valid_statuses:
            return {
                'is_valid': False,
                'error': f"Assignment {self.id} has invalid series_status='{self.series_status}'"
            }

        return {'is_valid': True}

    @classmethod
    def validate_single_active_per_field_entity(cls, field_id, entity_id, company_id):
        """
        Validate that only one assignment per field+entity has series_status='active'.

        Returns:
            dict: {'is_valid': bool, 'error': str, 'active_count': int}
        """
        active_count = cls.query.filter(
            cls.field_id == field_id,
            cls.entity_id == entity_id,
            cls.company_id == company_id,
            cls.series_status == 'active'
        ).count()

        if active_count > 1:
            return {
                'is_valid': False,
                'error': f"Multiple active assignments found for field {field_id}, entity {entity_id}: {active_count}",
                'active_count': active_count
            }

        return {'is_valid': True, 'active_count': active_count}

    def __repr__(self):
        version_info = f" v{self.series_version}" if self.data_series_id else ""
        return f'<DataPointAssignment {self.field_id}:{self.entity_id}{version_info}>'


# Automatic validation hooks
@event.listens_for(DataPointAssignment, 'before_insert')
@event.listens_for(DataPointAssignment, 'before_update')
def validate_assignment_integrity(mapper, connection, target):
    """
    Automatically validate data integrity before saves.
    Prevents inconsistent series_status values.
    """
    validation = target.validate_data_integrity()
    if not validation['is_valid']:
        raise ValueError(f"Data integrity violation: {validation['error']}")


# Global context flag for versioning operations
_versioning_context = {}

def set_versioning_context(field_id: str, entity_id: int, company_id: int):
    """Set versioning context to bypass validation for this field+entity+company combination."""
    context_key = f"{field_id}_{entity_id}_{company_id}"
    _versioning_context[context_key] = True

def clear_versioning_context(field_id: str, entity_id: int, company_id: int):
    """Clear versioning context for this field+entity+company combination."""
    context_key = f"{field_id}_{entity_id}_{company_id}"
    _versioning_context.pop(context_key, None)

@event.listens_for(DataPointAssignment, 'before_insert')
def validate_single_active_assignment(mapper, connection, target):
    """
    Ensure only one active assignment exists per field+entity+company.
    Only validates for new active assignments.

    NOTE: During versioning operations, this validation is bypassed using a context flag.
    """
    if target.series_status == 'active':
        # Check if we're in a versioning context for this field+entity+company combination
        context_key = f"{target.field_id}_{target.entity_id}_{target.company_id}"
        if _versioning_context.get(context_key, False):
            # We're in a versioning operation, skip validation
            return

        # Check if there are other active assignments
        from sqlalchemy import text

        query = text("""
        SELECT COUNT(*) FROM data_point_assignments
        WHERE field_id = :field_id AND entity_id = :entity_id AND company_id = :company_id
        AND series_status = 'active' AND id != :assignment_id
        """)

        # DEBUG: Log the parameters being passed
        # FIX: Use -1 instead of empty string for new assignments (target.id is None before insert)
        # This prevents SQL type mismatch error when comparing integer id column with string value
        params = {
            'field_id': target.field_id,
            'entity_id': target.entity_id,
            'company_id': target.company_id,
            'assignment_id': target.id if target.id is not None else -1
        }
        print(f"[DEBUG validate_single_active_assignment] Query parameters: {params}")
        print(f"[DEBUG validate_single_active_assignment] Parameter types: field_id={type(target.field_id)}, entity_id={type(target.entity_id)}, company_id={type(target.company_id)}, assignment_id={type(target.id)}")

        try:
            result = connection.execute(query, params).fetchone()
        except Exception as e:
            print(f"[DEBUG validate_single_active_assignment] SQLAlchemy execute error: {e}")
            print(f"[DEBUG validate_single_active_assignment] Query: {query}")
            print(f"[DEBUG validate_single_active_assignment] Params: {params}")
            raise

        active_count = result[0] if result else 0

        if active_count > 0:
            raise ValueError(
                f"Cannot create active assignment: {active_count} active assignment(s) already exist "
                f"for field {target.field_id}, entity {target.entity_id}, company {target.company_id}"
            )