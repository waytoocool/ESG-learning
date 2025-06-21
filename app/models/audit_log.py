from ..extensions import db
from datetime import datetime
import json


class AuditLog(db.Model):
    """
    Audit log for tracking administrative actions.
    
    This model tracks all significant actions performed by administrators,
    particularly SUPER_ADMIN actions that affect the system globally.
    """
    
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # e.g., 'CREATE_COMPANY', 'DELETE_USER'
    entity_type = db.Column(db.String(50), nullable=True)  # e.g., 'Company', 'User'
    entity_id = db.Column(db.Integer, nullable=True)  # ID of the affected entity
    payload = db.Column(db.Text, nullable=True)  # JSON serialized request data
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4/IPv6 address
    user_agent = db.Column(db.String(500), nullable=True)  # Browser/client info
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='admin_audit_logs')
    
    def __init__(self, user_id, action, entity_type=None, entity_id=None, 
                 payload=None, ip_address=None, user_agent=None):
        """
        Initialize a new audit log entry.
        
        Args:
            user_id (int): ID of the user performing the action
            action (str): Action being performed (e.g., 'CREATE_COMPANY')
            entity_type (str, optional): Type of entity being affected
            entity_id (int, optional): ID of the affected entity
            payload (dict, optional): Additional data about the action
            ip_address (str, optional): IP address of the client
            user_agent (str, optional): User agent string
        """
        self.user_id = user_id
        self.action = action
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.payload = json.dumps(payload) if payload else None
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    def get_payload_json(self):
        """Get payload as parsed JSON object."""
        if self.payload:
            try:
                return json.loads(self.payload)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.action} by User {self.user_id}>'
    
    @classmethod
    def log_action(cls, user_id, action, entity_type=None, entity_id=None, 
                   payload=None, ip_address=None, user_agent=None):
        """
        Convenience method to create and save an audit log entry.
        
        Args:
            user_id (int): ID of the user performing the action
            action (str): Action being performed
            entity_type (str, optional): Type of entity being affected
            entity_id (int, optional): ID of the affected entity
            payload (dict, optional): Additional data about the action
            ip_address (str, optional): IP address of the client
            user_agent (str, optional): User agent string
            
        Returns:
            AuditLog: The created audit log entry
        """
        audit_entry = cls(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(audit_entry)
        # Note: Caller is responsible for committing the transaction
        
        return audit_entry 