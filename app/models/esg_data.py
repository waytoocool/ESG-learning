from ..extensions import db
import uuid
from datetime import datetime, UTC

class ESGData(db.Model):
    """ESG Data model for storing actual metric values."""
    
    __tablename__ = 'esg_data'
    
    data_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_point_id = db.Column(db.String(36), db.ForeignKey('data_point.id'), nullable=False)
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)
    field_id = db.Column(db.String(36), db.ForeignKey('framework_data_fields.field_id'), nullable=False)
    raw_value = db.Column(db.String(255), nullable=True)  # String to accommodate both numeric and text values
    calculated_value = db.Column(db.Float, nullable=True)
    reporting_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Simplified relationships
    entity = db.relationship('Entity', 
                           back_populates='esg_data',
                           lazy='joined')
    field = db.relationship('FrameworkDataField', 
                          back_populates='esg_data',
                          lazy='joined')  # Performance optimization for frequent access
    audit_logs = db.relationship('ESGDataAuditLog', 
                               back_populates='esg_data',
                               cascade='all, delete-orphan')
    data_point = db.relationship('DataPoint', back_populates='esg_data')

    # Add new relationship for attachments
    attachments = db.relationship('ESGDataAttachment', 
                                back_populates='esg_data',
                                cascade='all, delete-orphan')

    # Add indexes for better query performance
    __table_args__ = (
        db.Index('idx_esg_entity_date', 'entity_id', 'reporting_date'),
        db.Index('idx_esg_field_date', 'field_id', 'reporting_date'),
    )

    def __init__(self, entity_id, field_id, data_point_id, raw_value, reporting_date, calculated_value=None):
        self.entity_id = entity_id
        self.field_id = field_id
        self.data_point_id = data_point_id
        self.raw_value = raw_value
        self.calculated_value = calculated_value
        self.reporting_date = reporting_date

    def __repr__(self):
        return f'<ESGData {self.field_id}: {self.raw_value}>'


class ESGDataAuditLog(db.Model):
    """Audit log for tracking changes to ESG data."""
    
    __tablename__ = 'esg_data_audit_log'
    
    log_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_id = db.Column(db.String(36), db.ForeignKey('esg_data.data_id'), nullable=False)
    change_type = db.Column(db.Enum('Create', 'Update', 'Delete', 'On-demand Computation', 'Smart Computation', 'CSV Upload', 'Admin Recompute', 'Admin Bulk Recompute', name='change_type'), nullable=False)
    old_value = db.Column(db.Float, nullable=True)
    new_value = db.Column(db.Float, nullable=True)
    changed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    change_date = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    # Relationship with User
    user = db.relationship('User', backref='audit_logs')

    # Updated relationship
    esg_data = db.relationship('ESGData', back_populates='audit_logs')

    def __init__(self, data_id, change_type, changed_by, old_value=None, new_value=None):
        self.data_id = data_id
        self.change_type = change_type
        self.old_value = old_value
        self.new_value = new_value
        self.changed_by = changed_by

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

    # Relationships
    esg_data = db.relationship('ESGData', back_populates='attachments')
    user = db.relationship('User', backref='uploaded_attachments')

    def __repr__(self):
        return f'<ESGDataAttachment {self.filename}>'
