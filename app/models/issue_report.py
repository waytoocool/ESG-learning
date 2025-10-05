"""
Issue Report model for bug tracking and support system.
Stores user-reported issues with comprehensive debugging information.
"""

from ..extensions import db
import uuid
from datetime import datetime, UTC
from sqlalchemy import Text, JSON, Enum
from .mixins import TenantScopedQueryMixin, TenantScopedModelMixin


class IssueReport(db.Model, TenantScopedQueryMixin, TenantScopedModelMixin):
    """Model for storing user-reported issues and bug reports."""

    __tablename__ = 'issue_reports'

    # Primary fields
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)  # e.g., "BUG-2025-0001"

    # Issue categorization
    category = db.Column(Enum('bug', 'feature_request', 'help', 'other', name='issue_category_type'),
                         nullable=False, default='bug')
    severity = db.Column(Enum('critical', 'high', 'medium', 'low', name='severity_type'),
                         nullable=False, default='medium')
    status = db.Column(Enum('new', 'in_review', 'assigned', 'in_progress', 'resolved', 'closed', name='issue_status_type'),
                      nullable=False, default='new')

    # Issue details
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(Text, nullable=False)
    steps_to_reproduce = db.Column(Text, nullable=True)
    expected_behavior = db.Column(Text, nullable=True)
    actual_behavior = db.Column(Text, nullable=True)

    # User and company context
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    # Browser and environment information
    browser_info = db.Column(JSON, nullable=True)  # {name, version, platform, user_agent, language, etc.}
    page_url = db.Column(db.String(500), nullable=True)
    page_title = db.Column(db.String(255), nullable=True)
    viewport_size = db.Column(db.String(50), nullable=True)  # e.g., "1920x1080"
    screen_resolution = db.Column(db.String(50), nullable=True)  # e.g., "2560x1440"

    # Error and debugging data
    console_errors = db.Column(JSON, nullable=True)  # Array of console error messages
    api_history = db.Column(JSON, nullable=True)  # Last 20 API requests/responses
    user_actions = db.Column(JSON, nullable=True)  # Last 10 user actions (clicks, inputs, etc.)
    local_storage_data = db.Column(JSON, nullable=True)  # Relevant localStorage data
    session_storage_data = db.Column(JSON, nullable=True)  # Relevant sessionStorage data

    # Screenshot and attachments
    screenshot_path = db.Column(db.String(500), nullable=True)
    screenshot_annotations = db.Column(JSON, nullable=True)  # Annotation data for screenshot
    attachments = db.Column(JSON, nullable=True)  # List of additional file paths

    # GitHub integration
    github_issue_id = db.Column(db.Integer, nullable=True)
    github_issue_url = db.Column(db.String(500), nullable=True)
    github_issue_number = db.Column(db.Integer, nullable=True)
    github_sync_status = db.Column(Enum('pending', 'synced', 'failed', name='sync_status_type'),
                                   nullable=False, default='pending')
    github_sync_error = db.Column(Text, nullable=True)
    github_synced_at = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    resolved_at = db.Column(db.DateTime, nullable=True)

    # Internal notes (for admin/developer use)
    internal_notes = db.Column(Text, nullable=True)
    assigned_to = db.Column(db.String(100), nullable=True)  # Developer/team assigned to fix
    resolution_notes = db.Column(Text, nullable=True)

    # Email notification tracking
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref='issue_reports', foreign_keys=[user_id])
    company = db.relationship('Company', backref='issue_reports', foreign_keys=[company_id])

    # Indexes for better query performance
    __table_args__ = (
        db.Index('idx_issue_ticket_number', 'ticket_number'),
        db.Index('idx_issue_user', 'user_id'),
        db.Index('idx_issue_company', 'company_id'),
        db.Index('idx_issue_status', 'status'),
        db.Index('idx_issue_severity', 'severity'),
        db.Index('idx_issue_category', 'category'),
        db.Index('idx_issue_created', 'created_at'),
        db.Index('idx_issue_github', 'github_issue_number'),
    )

    @classmethod
    def generate_ticket_number(cls):
        """Generate a unique ticket number in format BUG-YYYY-NNNN."""
        from datetime import datetime
        year = datetime.now().year

        # Get the latest ticket number for the current year
        latest = cls.query.filter(
            cls.ticket_number.like(f'BUG-{year}-%')
        ).order_by(cls.ticket_number.desc()).first()

        if latest:
            # Extract the sequence number and increment
            last_num = int(latest.ticket_number.split('-')[-1])
            next_num = last_num + 1
        else:
            # First ticket of the year
            next_num = 1

        return f'BUG-{year}-{next_num:04d}'

    def to_dict(self):
        """Convert issue report to dictionary for API responses."""
        return {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'category': self.category,
            'severity': self.severity,
            'status': self.status,
            'title': self.title,
            'description': self.description,
            'user_name': self.user.name if self.user else None,
            'user_email': self.user.email if self.user else None,
            'page_url': self.page_url,
            'github_issue_url': self.github_issue_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

    def to_github_issue_body(self):
        """Format issue data for GitHub issue creation."""
        body = f"""## Issue Report: {self.ticket_number}

**Category:** {self.category.replace('_', ' ').title()}
**Severity:** {self.severity.title()}
**Reported by:** {self.user.name if self.user else 'Unknown'} ({self.user.email if self.user else 'N/A'})
**Company:** {self.company.name if self.company else 'N/A'}
**Date:** {self.created_at.strftime('%Y-%m-%d %H:%M UTC')}

## Description
{self.description}

## Steps to Reproduce
{self.steps_to_reproduce if self.steps_to_reproduce else 'Not provided'}

## Expected Behavior
{self.expected_behavior if self.expected_behavior else 'Not provided'}

## Actual Behavior
{self.actual_behavior if self.actual_behavior else 'Not provided'}

## Environment Details
- **Page URL:** {self.page_url if self.page_url else 'N/A'}
- **Browser:** {self.browser_info.get('name', 'Unknown')} {self.browser_info.get('version', '')} if self.browser_info else 'N/A'
- **Platform:** {self.browser_info.get('platform', 'Unknown') if self.browser_info else 'N/A'}
- **Screen Resolution:** {self.screen_resolution if self.screen_resolution else 'N/A'}
- **Viewport Size:** {self.viewport_size if self.viewport_size else 'N/A'}

## Console Errors
```
{self._format_console_errors()}
```

## Recent API Calls
```
{self._format_api_history()}
```

## Internal Tracking
- Ticket Number: {self.ticket_number}
- Issue ID: {self.id}
"""
        return body

    def _format_console_errors(self):
        """Format console errors for display."""
        if not self.console_errors:
            return "No console errors captured"

        errors = []
        for error in self.console_errors[:10]:  # Limit to 10 most recent
            errors.append(f"[{error.get('timestamp', 'N/A')}] {error.get('level', 'ERROR')}: {error.get('message', '')}")

        return "\n".join(errors)

    def _format_api_history(self):
        """Format API history for display."""
        if not self.api_history:
            return "No API history captured"

        calls = []
        for call in self.api_history[:10]:  # Limit to 10 most recent
            status = call.get('status', 'N/A')
            method = call.get('method', 'GET')
            url = call.get('url', 'N/A')
            calls.append(f"[{status}] {method} {url}")

        return "\n".join(calls)

    def __repr__(self):
        return f'<IssueReport {self.ticket_number}: {self.title[:50]}>'


class IssueComment(db.Model, TenantScopedQueryMixin, TenantScopedModelMixin):
    """Model for storing comments on issue reports."""

    __tablename__ = 'issue_comments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issue_id = db.Column(db.String(36), db.ForeignKey('issue_reports.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    comment = db.Column(Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=False)  # Internal notes not visible to reporter

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    issue = db.relationship('IssueReport', backref='comments', foreign_keys=[issue_id])
    user = db.relationship('User', backref='issue_comments', foreign_keys=[user_id])
    company = db.relationship('Company', backref='issue_comments', foreign_keys=[company_id])

    def __repr__(self):
        return f'<IssueComment {self.id} on {self.issue_id}>'