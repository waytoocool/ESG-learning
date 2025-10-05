from datetime import datetime, UTC
from ..extensions import db

class UserFeedback(db.Model):
    """Model for collecting user feedback on interface versions."""

    __tablename__ = 'user_feedback'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    interface_version = db.Column(db.String(20), nullable=False)  # 'legacy' or 'modal'
    feedback_type = db.Column(db.String(50))  # 'bug', 'suggestion', 'praise', 'other'
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    user = db.relationship('User', backref='interface_feedback')

    def __repr__(self):
        return f'<UserFeedback {self.id} - {self.user_id} - {self.interface_version}>'

    def to_dict(self):
        """Convert feedback to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'interface_version': self.interface_version,
            'feedback_type': self.feedback_type,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
