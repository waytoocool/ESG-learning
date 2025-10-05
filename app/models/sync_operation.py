"""
Multi-tenant synchronization models for T-8 implementation.

This module contains models for tracking and managing cross-tenant
synchronization operations including framework sync, tenant templates,
and data migration operations.
"""

from ..extensions import db
from datetime import datetime
import json
import uuid


class SyncOperation(db.Model):
    """
    Base model for tracking all synchronization operations.
    
    This model provides a unified tracking system for all types of
    multi-tenant synchronization operations including framework sync,
    tenant cloning, and data migrations.
    """
    
    __tablename__ = 'sync_operations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    operation_type = db.Column(db.Enum('FRAMEWORK_SYNC', 'TENANT_CLONE', 'DATA_MIGRATION', 'TEMPLATE_CREATION', name='sync_operation_type'), nullable=False)
    source_id = db.Column(db.String(36), nullable=True)  # Source framework/tenant ID
    target_ids = db.Column(db.JSON, nullable=True)  # List of target IDs
    parameters = db.Column(db.JSON, nullable=True)  # Operation-specific parameters
    status = db.Column(db.Enum('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='sync_status'), default='QUEUED')
    progress_percentage = db.Column(db.Integer, default=0)
    initiated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    log_data = db.Column(db.JSON, nullable=True)  # Detailed operation logs
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    initiated_by_user = db.relationship('User', backref='sync_operations')
    
    def __init__(self, operation_type, initiated_by, source_id=None, target_ids=None, parameters=None):
        self.operation_type = operation_type
        self.initiated_by = initiated_by
        self.source_id = source_id
        self.target_ids = target_ids or []
        self.parameters = parameters or {}
        self.log_data = []
    
    def add_log_entry(self, level, message, details=None):
        """Add a log entry to the operation."""
        if not self.log_data:
            self.log_data = []
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,  # INFO, WARNING, ERROR
            'message': message,
            'details': details or {}
        }
        self.log_data.append(log_entry)
    
    def start_operation(self):
        """Mark operation as started."""
        self.status = 'RUNNING'
        self.started_at = datetime.utcnow()
        self.add_log_entry('INFO', 'Operation started')
    
    def complete_operation(self, success=True, error_message=None):
        """Mark operation as completed."""
        self.status = 'COMPLETED' if success else 'FAILED'
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100 if success else self.progress_percentage
        
        if error_message:
            self.error_message = error_message
            self.add_log_entry('ERROR', error_message)
        else:
            self.add_log_entry('INFO', 'Operation completed successfully')
    
    def update_progress(self, percentage, message=None):
        """Update operation progress."""
        self.progress_percentage = min(max(percentage, 0), 100)
        if message:
            self.add_log_entry('INFO', message, {'progress': percentage})
    
    def get_duration(self):
        """Get operation duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return 0
    
    def __repr__(self):
        return f'<SyncOperation {self.id}: {self.operation_type} - {self.status}>'


class FrameworkSyncJob(db.Model):
    """
    Specialized model for framework synchronization operations.
    
    This model tracks framework synchronization jobs, including
    which frameworks are being synced to which tenants and
    handles conflict resolution.
    """
    
    __tablename__ = 'framework_sync_jobs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sync_operation_id = db.Column(db.String(36), db.ForeignKey('sync_operations.id'), nullable=False)
    framework_id = db.Column(db.String(36), db.ForeignKey('frameworks.framework_id'), nullable=False)
    source_company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)  # None for global frameworks
    target_company_ids = db.Column(db.JSON, nullable=False)  # List of target company IDs
    sync_options = db.Column(db.JSON, nullable=True)  # Sync configuration options
    conflict_resolution = db.Column(db.Enum('SKIP', 'OVERWRITE', 'MERGE', 'MANUAL', name='conflict_resolution'), default='SKIP')
    conflicts_detected = db.Column(db.JSON, nullable=True)  # List of detected conflicts
    
    # Relationships
    sync_operation = db.relationship('SyncOperation', backref='framework_sync_jobs')
    framework = db.relationship('Framework', backref='sync_jobs')
    source_company = db.relationship('Company', foreign_keys=[source_company_id], backref='outgoing_framework_syncs')
    
    def __init__(self, sync_operation_id, framework_id, target_company_ids, 
                 source_company_id=None, sync_options=None, conflict_resolution='SKIP'):
        self.sync_operation_id = sync_operation_id
        self.framework_id = framework_id
        self.source_company_id = source_company_id
        self.target_company_ids = target_company_ids
        self.sync_options = sync_options or {}
        self.conflict_resolution = conflict_resolution
        self.conflicts_detected = []
    
    def add_conflict(self, company_id, conflict_type, details):
        """Add a detected conflict."""
        if not self.conflicts_detected:
            self.conflicts_detected = []
        
        conflict = {
            'company_id': company_id,
            'conflict_type': conflict_type,  # 'FRAMEWORK_EXISTS', 'FIELD_CONFLICT', etc.
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.conflicts_detected.append(conflict)
    
    def get_target_companies(self):
        """Get Company objects for target companies."""
        from .company import Company
        return Company.query.filter(Company.id.in_(self.target_company_ids)).all()
    
    def __repr__(self):
        return f'<FrameworkSyncJob {self.id}: Framework {self.framework_id} to {len(self.target_company_ids)} tenants>'


class TenantTemplate(db.Model):
    """
    Model for storing tenant templates.
    
    Templates allow rapid provisioning of new tenants based on
    successful existing configurations including frameworks,
    data points, entity structures, and other settings.
    """
    
    __tablename__ = 'tenant_templates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    industry = db.Column(db.String(50), nullable=True)
    source_company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)  # None for built-in templates
    template_data = db.Column(db.JSON, nullable=False)  # Serialized template structure
    is_public = db.Column(db.Boolean, default=False)  # Available to all super admins
    is_builtin = db.Column(db.Boolean, default=False)  # System-provided template
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usage_count = db.Column(db.Integer, default=0)
    
    # Relationships
    source_company = db.relationship('Company', backref='created_templates')
    created_by_user = db.relationship('User', backref='created_templates')
    
    def __init__(self, name, template_data, created_by, description=None, 
                 industry=None, source_company_id=None, is_public=False):
        self.name = name
        self.description = description
        self.industry = industry
        self.source_company_id = source_company_id
        self.template_data = template_data
        self.is_public = is_public
        self.created_by = created_by
    
    def increment_usage(self):
        """Increment the usage counter."""
        self.usage_count += 1
    
    def get_template_summary(self):
        """Get a summary of what's included in the template."""
        data = self.template_data or {}
        return {
            'frameworks': len(data.get('frameworks', [])),
            'data_points': len(data.get('data_points', [])),
            'entities': len(data.get('entities', [])),
            'assignments': len(data.get('assignments', [])),
            'users': len(data.get('users', [])),
            'settings': len(data.get('settings', {}))
        }
    
    def validate_template_data(self):
        """Validate template data structure."""
        required_keys = ['frameworks', 'data_points', 'entities']
        data = self.template_data or {}
        
        for key in required_keys:
            if key not in data:
                return False, f"Missing required section: {key}"
        
        return True, "Template data is valid"
    
    @classmethod
    def get_public_templates(cls):
        """Get all public templates."""
        return cls.query.filter_by(is_public=True).all()
    
    @classmethod
    def get_builtin_templates(cls):
        """Get all built-in system templates."""
        return cls.query.filter_by(is_builtin=True).all()
    
    def __repr__(self):
        return f'<TenantTemplate {self.name}: {self.industry or "Generic"}>'


class DataMigrationJob(db.Model):
    """
    Model for tracking data migration operations.
    
    This model handles large-scale data movement operations
    including tenant mergers, data exports/imports, and
    archival operations.
    """
    
    __tablename__ = 'data_migration_jobs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sync_operation_id = db.Column(db.String(36), db.ForeignKey('sync_operations.id'), nullable=False)
    migration_type = db.Column(db.Enum('EXPORT', 'IMPORT', 'MERGE', 'ARCHIVE', name='migration_type'), nullable=False)
    source_company_ids = db.Column(db.JSON, nullable=True)  # Source companies for export/merge
    target_company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)  # Target for import/merge
    migration_options = db.Column(db.JSON, nullable=True)  # Migration configuration
    data_selection = db.Column(db.JSON, nullable=True)  # What data to migrate
    validation_results = db.Column(db.JSON, nullable=True)  # Pre-migration validation
    
    # Relationships
    sync_operation = db.relationship('SyncOperation', backref='data_migration_jobs')
    target_company = db.relationship('Company', backref='incoming_migrations')
    
    def __init__(self, sync_operation_id, migration_type, target_company_id=None, 
                 source_company_ids=None, migration_options=None, data_selection=None):
        self.sync_operation_id = sync_operation_id
        self.migration_type = migration_type
        self.target_company_id = target_company_id
        self.source_company_ids = source_company_ids or []
        self.migration_options = migration_options or {}
        self.data_selection = data_selection or {}
        self.validation_results = {}
    
    def add_validation_result(self, category, result, details=None):
        """Add validation result."""
        if not self.validation_results:
            self.validation_results = {}
        
        self.validation_results[category] = {
            'result': result,  # 'PASS', 'FAIL', 'WARNING'
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_source_companies(self):
        """Get Company objects for source companies."""
        from .company import Company
        if self.source_company_ids:
            return Company.query.filter(Company.id.in_(self.source_company_ids)).all()
        return []
    
    def __repr__(self):
        return f'<DataMigrationJob {self.id}: {self.migration_type}>' 