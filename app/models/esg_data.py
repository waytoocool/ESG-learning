from ..extensions import db
import uuid
from datetime import datetime, UTC, date
from typing import Optional, Dict, Any
from .mixins import TenantScopedQueryMixin, TenantScopedModelMixin

class ESGData(db.Model, TenantScopedQueryMixin, TenantScopedModelMixin):
    """ESG Data model for storing actual metric values.
    
    Phase 2.5: Enhanced with dimensional support for complex data breakdowns.
    Data can now be categorized by multiple dimensions (gender, age, department, etc.).
    """
    
    __tablename__ = 'esg_data'
    
    data_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)
    field_id = db.Column(db.String(36), db.ForeignKey('framework_data_fields.field_id'), nullable=False)
    # Add company_id for tenant isolation - temporarily nullable until T-3 seed data
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    # Phase 1: Assignment relationship for versioning support
    assignment_id = db.Column(db.String(36), db.ForeignKey('data_point_assignments.id'), nullable=True, index=True)
    raw_value = db.Column(db.String(255), nullable=True)  # String to accommodate both numeric and text values
    calculated_value = db.Column(db.Float, nullable=True)
    # Phase 4.1: unit column for storing user-selected units (overrides field default_unit)
    unit = db.Column(db.String(20), nullable=True)
    
    # Phase 2.5: Dimensional data support
    dimension_values = db.Column(db.JSON, nullable=True)  # {"gender": "Male", "age": "<30", "department": "IT"}

    # Phase 4: Draft support for auto-save functionality
    is_draft = db.Column(db.Boolean, default=False, nullable=False)  # Flag to mark draft entries
    draft_metadata = db.Column(db.JSON, nullable=True)  # Store additional draft metadata

    # Enhancement #2: Notes/Comments functionality for data context
    notes = db.Column(db.Text, nullable=True)  # User notes/comments for data entry

    # Validation Engine: Review workflow fields
    review_status = db.Column(
        db.Enum('draft', 'submitted', 'pending_review',
                'approved', 'rejected', 'needs_revision',
                name='review_status_type'),
        default='draft',
        nullable=False,
        index=True,
        comment="Current review status of the data submission"
    )

    submitted_at = db.Column(
        db.DateTime,
        nullable=True,
        comment="Timestamp when data was submitted for review"
    )

    # Validation Engine: Validation results storage
    validation_results = db.Column(
        db.JSON,
        nullable=True,
        comment="Automated validation check results and warnings"
    )

    reporting_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Updated relationships
    entity = db.relationship('Entity', 
                           back_populates='esg_data',
                           lazy='joined')
    field = db.relationship('FrameworkDataField', 
                          back_populates='esg_data',
                          lazy='joined')  # Performance optimization for frequent access
    audit_logs = db.relationship('ESGDataAuditLog', 
                               back_populates='esg_data',
                               cascade='all, delete-orphan')
    company = db.relationship('Company', backref='esg_data')
    
    # Phase 1: Assignment relationship for versioning support
    assignment = db.relationship('DataPointAssignment', backref='esg_data_entries')

    # Add new relationship for attachments
    attachments = db.relationship('ESGDataAttachment', 
                                back_populates='esg_data',
                                cascade='all, delete-orphan')

    # Add indexes for better query performance
    __table_args__ = (
        # Uniqueness constraint: Prevent duplicate entries for same field/entity/date/company
        # Note: is_draft is NOT included to allow multiple draft versions
        db.UniqueConstraint(
            'field_id',
            'entity_id',
            'reporting_date',
            'company_id',
            name='uq_esg_single_entry_per_date'
        ),
        db.Index('idx_esg_entity_date', 'entity_id', 'reporting_date'),
        db.Index('idx_esg_field_date', 'field_id', 'reporting_date'),
        db.Index('idx_esg_company', 'company_id'),  # Index for tenant filtering
        db.Index('idx_esg_assignment', 'assignment_id'),  # Index for assignment relationship
        # Phase 2.5: Add index for dimensional queries
        db.Index('idx_esg_dimensions', 'field_id', 'reporting_date', 'dimension_values'),
        # Phase 4: Add index for draft queries
        db.Index('idx_esg_draft_lookup', 'field_id', 'entity_id', 'reporting_date', 'is_draft'),
        # Validation Engine: Add index for review status queries
        db.Index('idx_esg_review_status', 'review_status', 'company_id'),
        db.Index('idx_esg_review_pending', 'review_status', 'submitted_at'),
    )

    def __init__(self, entity_id, field_id, raw_value, reporting_date, company_id=None, calculated_value=None, unit=None, dimension_values=None, assignment_id=None, notes=None):
        self.entity_id = entity_id
        self.field_id = field_id
        self.company_id = company_id
        self.assignment_id = assignment_id  # Phase 1: Support for assignment relationship
        self.raw_value = raw_value
        self.calculated_value = calculated_value
        self.reporting_date = reporting_date
        self.dimension_values = dimension_values or {}
        self.unit = unit  # Phase 1: Support for user-selected units
        self.notes = notes  # Enhancement #2: Support for notes/comments

    @property
    def effective_unit(self):
        """Get the effective unit for this data entry.
        
        Returns user-selected unit if available, otherwise field's default_unit.
        """
        return self.unit or (self.field.default_unit if self.field else None)

    @property 
    def value_type(self):
        """Get the value type from the associated field."""
        return self.field.value_type if self.field else 'TEXT'

    def convert_to_default_unit(self):
        """Phase 1: No conversion needed since unit comes from field definition."""
        # This is a placeholder for future unit conversion logic
        # For now, units are consistent since they come from field.default_unit
        pass

    # Phase 2.5: Dimensional data helper methods
    def get_dimension_value(self, dimension_name):
        """Get the value for a specific dimension."""
        return (self.dimension_values or {}).get(dimension_name)

    def set_dimension_value(self, dimension_name, value):
        """Set the value for a specific dimension."""
        if not self.dimension_values:
            self.dimension_values = {}
        self.dimension_values[dimension_name] = value

    def has_dimensions(self):
        """Check if this data entry has any dimensional breakdowns."""
        return bool(self.dimension_values)

    def matches_dimension_filter(self, dimension_filter):
        """Check if this data entry matches the given dimension filter.
        
        Args:
            dimension_filter (dict): Filter like {"gender": "Male", "age": "<30"}
        
        Returns:
            bool: True if all dimensions in filter match this entry
        """
        if not dimension_filter:
            return True
        
        if not self.dimension_values:
            return False
        
        for dim_name, dim_value in dimension_filter.items():
            if self.dimension_values.get(dim_name) != dim_value:
                return False
        
        return True

    def get_dimension_key(self):
        """Get a string key representing the dimensional breakdown.

        Returns:
            str: Sorted dimension key like "age:<30,gender:Male"
        """
        if not self.dimension_values:
            return ""

        sorted_items = sorted(self.dimension_values.items())
        return ",".join([f"{k}:{v}" for k, v in sorted_items])

    # Enhancement #2: Notes helper methods
    def has_notes(self):
        """Check if this data entry has notes.

        Returns:
            bool: True if notes exist and are not empty
        """
        return bool(self.notes and self.notes.strip())

    def get_notes_preview(self, max_length=50):
        """Get a preview of notes (first N characters).

        Args:
            max_length (int): Maximum length of preview

        Returns:
            str: Preview of notes with ellipsis if truncated
        """
        if not self.has_notes():
            return ""

        notes_text = self.notes.strip()
        if len(notes_text) <= max_length:
            return notes_text

        return notes_text[:max_length] + "..."

    # Phase 4: Assignment resolution methods for dual compatibility
    def resolve_assignment(self) -> Optional['DataPointAssignment']:
        """Resolve the assignment for this data entry.
        
        Returns the assignment based on either direct assignment_id or
        field_id + entity_id + reporting_date resolution.
        
        Returns:
            DataPointAssignment: Resolved assignment or None
        """
        from ..services.assignment_versioning import resolve_assignment_for_data
        
        return resolve_assignment_for_data(
            self.field_id,
            self.entity_id, 
            self.reporting_date,
            self.assignment_id
        )
    
    @property
    def resolved_assignment(self) -> Optional['DataPointAssignment']:
        """Property for accessing the resolved assignment."""
        if not hasattr(self, '_resolved_assignment'):
            self._resolved_assignment = self.resolve_assignment()
        return self._resolved_assignment
    
    def get_assignment_frequency(self) -> Optional[str]:
        """Get the frequency from the resolved assignment.
        
        Returns:
            str: Assignment frequency (Monthly/Quarterly/Annual) or None
        """
        assignment = self.resolved_assignment
        return assignment.frequency if assignment else None
    
    def get_assignment_series_info(self) -> Dict[str, Any]:
        """Get data series information for this data entry.
        
        Returns:
            Dict containing series information
        """
        assignment = self.resolved_assignment
        if not assignment:
            return {'has_assignment': False}
        
        return {
            'has_assignment': True,
            'assignment_id': assignment.id,
            'data_series_id': assignment.data_series_id,
            'series_version': assignment.series_version,
            'series_status': assignment.series_status,
            'is_latest_version': assignment.is_latest_version(),
            'frequency': assignment.frequency
        }
    
    def is_assignment_compatible(self) -> bool:
        """Check if this data entry is compatible with its resolved assignment.
        
        Returns:
            bool: True if compatible, False if there are issues
        """
        assignment = self.resolved_assignment
        if not assignment:
            return False  # No assignment found
        
        # Check if reporting date is valid for assignment
        try:
            return assignment.is_valid_reporting_date(self.reporting_date)
        except Exception:
            return False
    
    @classmethod
    def find_by_assignment(cls, assignment_id: str, entity_id: Optional[int] = None, reporting_date: Optional[date] = None):
        """Find ESG data entries by assignment ID with optional filters.
        
        Args:
            assignment_id: Assignment ID to search for
            entity_id: Optional entity ID filter
            reporting_date: Optional reporting date filter
            
        Returns:
            Query: Filtered query for ESG data entries
        """
        query = cls.query.filter(cls.assignment_id == assignment_id)
        
        if entity_id:
            query = query.filter(cls.entity_id == entity_id)
        
        if reporting_date:
            query = query.filter(cls.reporting_date == reporting_date)
        
        return query
    
    @classmethod
    def find_by_field_entity_date(cls, field_id: str, entity_id: int, reporting_date: date):
        """Find ESG data entry by field + entity + date (legacy pattern).
        
        Args:
            field_id: Framework data field ID
            entity_id: Entity ID
            reporting_date: Reporting date
            
        Returns:
            ESGData: Data entry or None
        """
        return cls.query.filter(
            cls.field_id == field_id,
            cls.entity_id == entity_id,
            cls.reporting_date == reporting_date
        ).first()
    
    @classmethod
    def resolve_data_for_assignment(cls, field_id: str, entity_id: int, reporting_date: date):
        """Resolve ESG data using assignment resolution logic.
        
        This method uses the assignment resolution service to find the appropriate
        assignment and then looks for data entries that match.
        
        Args:
            field_id: Framework data field ID
            entity_id: Entity ID
            reporting_date: Reporting date
            
        Returns:
            ESGData: Data entry or None
        """
        from ..services.assignment_versioning import resolve_assignment
        
        # First try to resolve the assignment
        assignment = resolve_assignment(field_id, entity_id, reporting_date)
        if not assignment:
            return None
        
        # Look for data linked directly to this assignment
        direct_data = cls.query.filter(
            cls.assignment_id == assignment.id,
            cls.reporting_date == reporting_date
        ).first()
        
        if direct_data:
            return direct_data
        
        # Fallback to field+entity+date pattern (legacy)
        return cls.find_by_field_entity_date(field_id, entity_id, reporting_date)

    def __repr__(self):
        unit_str = f" {self.effective_unit}" if self.effective_unit else ""
        dim_str = f" {self.get_dimension_key()}" if self.has_dimensions() else ""
        return f'<ESGData {self.field_id}: {self.raw_value}{unit_str}{dim_str}>'


class ESGDataAuditLog(db.Model):
    """Audit log for tracking changes to ESG data."""

    __tablename__ = 'esg_data_audit_log'

    log_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_id = db.Column(db.String(36), db.ForeignKey('esg_data.data_id'), nullable=False)
    change_type = db.Column(db.Enum(
        'Create',
        'Update',
        'Delete',
        'On-demand Computation',
        'Smart Computation',
        'CSV Upload',
        'Admin Recompute',
        'Admin Bulk Recompute',
        'Excel Upload',              # Enhancement #4: Bulk Excel upload new entry
        'Excel Upload Update',       # Enhancement #4: Bulk Excel upload overwrite
        'Data_Submitted',            # Validation Engine: User submits data for review
        'Validation_Passed',         # Validation Engine: Validation checks passed
        'Validation_Warning',        # Validation Engine: Validation warnings generated
        'User_Acknowledged_Warning', # Validation Engine: User acknowledged warnings with notes
        name='change_type'
    ), nullable=False)
    old_value = db.Column(db.Float, nullable=True)
    new_value = db.Column(db.Float, nullable=True)
    changed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    change_date = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    # Enhancement #4: Additional metadata column for tracking (bulk upload, etc.)
    # Note: Cannot use 'metadata' as it's reserved by SQLAlchemy
    change_metadata = db.Column(db.JSON, nullable=True)
    # Example for bulk upload: {
    #     "source": "bulk_upload",
    #     "filename": "Template_2025-11-14.xlsx",
    #     "row_number": 5,
    #     "batch_id": "batch-abc-123",  # Optional: group related uploads
    #     "has_attachment": true,
    #     "has_notes": true,
    #     "previous_submission_date": "2024-04-05T10:30:00Z"  # For updates
    # }

    # Relationship with User
    user = db.relationship('User', backref='esg_audit_logs')

    # Updated relationship
    esg_data = db.relationship('ESGData', back_populates='audit_logs')

    def __init__(self, data_id, change_type, changed_by, old_value=None, new_value=None, change_metadata=None):
        self.data_id = data_id
        self.change_type = change_type
        self.old_value = old_value
        self.new_value = new_value
        self.changed_by = changed_by
        self.change_metadata = change_metadata

    def __repr__(self):
        return f'<ESGDataAuditLog {self.log_id}>'


class ESGDataAttachment(db.Model):
    """Model for storing ESG data attachments."""

    __tablename__ = 'esg_data_attachments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_id = db.Column(db.String(36), db.ForeignKey('esg_data.data_id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    mime_type = db.Column(db.String(127), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Enhancement #4: File hash for deduplication (SHA256)
    file_hash = db.Column(db.String(64), nullable=True, index=True)

    # Relationships
    esg_data = db.relationship('ESGData', back_populates='attachments')
    user = db.relationship('User', backref='uploaded_attachments')

    def __repr__(self):
        return f'<ESGDataAttachment {self.filename}>'
