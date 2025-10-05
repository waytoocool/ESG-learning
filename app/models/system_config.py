"""
System Configuration Model - T-9

This model handles system-wide configuration settings that can be managed
by SUPER_ADMIN users through the admin interface.
"""

from flask import current_app
from ..extensions import db
from datetime import datetime
import json
from typing import Any, Dict, Optional


class SystemConfig(db.Model):
    """
    Model for storing system-wide configuration settings.
    
    This allows super admins to configure various aspects of the application
    without requiring code changes or server restarts.
    """
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(20), nullable=False, default='string')  # string, integer, float, boolean, json
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False, default='general')
    is_sensitive = db.Column(db.Boolean, default=False)  # Hide value in UI for passwords, API keys
    is_readonly = db.Column(db.Boolean, default=False)  # Prevent modification through UI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationship
    updated_by_user = db.relationship('User', backref='system_config_updates')
    
    def __init__(self, key: str, value: Any = None, value_type: str = 'string', 
                 description: str = None, category: str = 'general', 
                 is_sensitive: bool = False, is_readonly: bool = False):
        self.key = key
        self.value_type = value_type
        self.description = description
        self.category = category
        self.is_sensitive = is_sensitive
        self.is_readonly = is_readonly
        self.set_value(value)
    
    def set_value(self, value: Any) -> None:
        """Set the configuration value with proper type conversion."""
        if value is None:
            self.value = None
            return
        
        if self.value_type == 'string':
            self.value = str(value)
        elif self.value_type == 'integer':
            self.value = str(int(value))
        elif self.value_type == 'float':
            self.value = str(float(value))
        elif self.value_type == 'boolean':
            self.value = str(bool(value)).lower()
        elif self.value_type == 'json':
            self.value = json.dumps(value) if not isinstance(value, str) else value
        else:
            self.value = str(value)
    
    def get_value(self) -> Any:
        """Get the configuration value with proper type conversion."""
        if self.value is None:
            return None
        
        try:
            if self.value_type == 'string':
                return self.value
            elif self.value_type == 'integer':
                return int(self.value)
            elif self.value_type == 'float':
                return float(self.value)
            elif self.value_type == 'boolean':
                return self.value.lower() in ('true', '1', 'yes', 'on')
            elif self.value_type == 'json':
                return json.loads(self.value)
            else:
                return self.value
        except Exception:
            return None
    
    @classmethod
    def get_config(cls, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        config = cls.query.filter_by(key=key).first()
        return config.get_value() if config else default
    
    @classmethod
    def set_config(cls, key: str, value: Any, user_id: int = None, 
                   value_type: str = None, description: str = None, 
                   category: str = 'general') -> 'SystemConfig':
        """Set a configuration value by key."""
        config = cls.query.filter_by(key=key).first()
        
        if config:
            # Update existing config
            config.set_value(value)
            config.updated_at = datetime.utcnow()
            config.updated_by = user_id
        else:
            # Create new config
            if value_type is None:
                # Auto-detect type
                if isinstance(value, bool):
                    value_type = 'boolean'
                elif isinstance(value, int):
                    value_type = 'integer'
                elif isinstance(value, float):
                    value_type = 'float'
                elif isinstance(value, (dict, list)):
                    value_type = 'json'
                else:
                    value_type = 'string'
            
            config = cls(
                key=key,
                value=value,
                value_type=value_type,
                description=description,
                category=category
            )
            config.set_value(value)
            config.updated_by = user_id
            db.session.add(config)
        
        db.session.commit()
        return config
    
    @classmethod
    def get_by_category(cls, category: str) -> list:
        """Get all configuration values in a category."""
        return cls.query.filter_by(category=category).order_by(cls.key).all()
    
    @classmethod
    def get_all_categories(cls) -> list:
        """Get all configuration categories."""
        categories = db.session.query(cls.category).distinct().all()
        return [cat[0] for cat in categories]
    
    @classmethod
    def initialize_defaults(cls):
        """Initialize default system configuration values."""
        defaults = [
            # Application Settings
            ('app.name', 'ESG DataVault', 'string', 'Application display name', 'application'),
            ('app.version', '1.0.0', 'string', 'Application version', 'application'),
            ('app.maintenance_mode', False, 'boolean', 'Enable maintenance mode', 'application'),
            ('app.registration_enabled', True, 'boolean', 'Allow new user registration', 'application'),
            ('app.max_upload_size', 10485760, 'integer', 'Maximum file upload size in bytes (10MB)', 'application'),
            
            # Email Settings
            ('email.enabled', False, 'boolean', 'Enable email notifications', 'email'),
            ('email.smtp_server', '', 'string', 'SMTP server hostname', 'email'),
            ('email.smtp_port', 587, 'integer', 'SMTP server port', 'email'),
            ('email.use_tls', True, 'boolean', 'Use TLS for email', 'email'),
            ('email.username', '', 'string', 'SMTP username', 'email'),
            ('email.password', '', 'string', 'SMTP password', 'email', True),  # Sensitive
            ('email.from_address', '', 'string', 'Default from email address', 'email'),
            
            # Security Settings
            ('security.session_timeout', 3600, 'integer', 'Session timeout in seconds', 'security'),
            ('security.password_min_length', 8, 'integer', 'Minimum password length', 'security'),
            ('security.require_password_complexity', True, 'boolean', 'Require complex passwords', 'security'),
            ('security.max_login_attempts', 5, 'integer', 'Maximum login attempts before lockout', 'security'),
            ('security.lockout_duration', 900, 'integer', 'Account lockout duration in seconds', 'security'),
            
            # Data Management
            ('data.auto_backup_enabled', True, 'boolean', 'Enable automatic data backups', 'data'),
            ('data.backup_retention_days', 30, 'integer', 'Number of days to retain backups', 'data'),
            ('data.validation_strict_mode', False, 'boolean', 'Enable strict data validation', 'data'),
            ('data.computed_fields_auto_update', True, 'boolean', 'Automatically update computed fields', 'data'),
            
            # Performance
            ('performance.cache_enabled', True, 'boolean', 'Enable application caching', 'performance'),
            ('performance.cache_timeout', 300, 'integer', 'Cache timeout in seconds', 'performance'),
            ('performance.max_concurrent_jobs', 5, 'integer', 'Maximum concurrent background jobs', 'performance'),
            
            # Analytics
            ('analytics.anonymous_usage_stats', True, 'boolean', 'Collect anonymous usage statistics', 'analytics'),
            ('analytics.retention_period_days', 365, 'integer', 'Analytics data retention period', 'analytics'),
            
            # Integration
            ('integration.api_rate_limit', 1000, 'integer', 'API rate limit per hour per user', 'integration'),
            ('integration.webhook_timeout', 30, 'integer', 'Webhook timeout in seconds', 'integration'),
        ]
        
        for key, value, value_type, description, category, *sensitive in defaults:
            is_sensitive = sensitive[0] if sensitive else False
            existing = cls.query.filter_by(key=key).first()
            if not existing:
                config = cls(
                    key=key,
                    value=value,
                    value_type=value_type,
                    description=description,
                    category=category,
                    is_sensitive=is_sensitive
                )
                db.session.add(config)
        
        db.session.commit()
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.get_value() if not self.is_sensitive or include_sensitive else '***',
            'value_type': self.value_type,
            'description': self.description,
            'category': self.category,
            'is_sensitive': self.is_sensitive,
            'is_readonly': self.is_readonly,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<SystemConfig {self.key}: {self.value}>'


class SystemHealth(db.Model):
    """
    Model for tracking system health metrics and status.
    """
    __tablename__ = 'system_health'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False, index=True)
    metric_value = db.Column(db.Text, nullable=True)
    metric_type = db.Column(db.String(20), nullable=False)  # gauge, counter, status
    status = db.Column(db.String(20), nullable=False, default='ok')  # ok, warning, critical
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    @classmethod
    def record_metric(cls, name: str, value: Any, metric_type: str = 'gauge', 
                     status: str = 'ok', details: str = None):
        """Record a system health metric."""
        metric = cls(
            metric_name=name,
            metric_value=str(value),
            metric_type=metric_type,
            status=status,
            details=details
        )
        db.session.add(metric)
        db.session.commit()
        return metric
    
    @classmethod
    def get_latest_metrics(cls, limit: int = 100) -> list:
        """Get the latest system health metrics."""
        return cls.query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_metrics_by_name(cls, name: str, hours: int = 24) -> list:
        """Get metrics by name for the specified time period."""
        cutoff = datetime.utcnow() - datetime.timedelta(hours=hours)
        return cls.query.filter(
            cls.metric_name == name,
            cls.timestamp >= cutoff
        ).order_by(cls.timestamp.desc()).all()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert health metric to dictionary."""
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_type': self.metric_type,
            'status': self.status,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        } 