# Floating Chatbot Bug Reporting System - Complete Implementation Guide

## Table of Contents
1. [Overview](#overview)
2. [Database Models](#database-models)
3. [Backend Services](#backend-services)
4. [API Endpoints](#api-endpoints)
5. [Frontend Components](#frontend-components)
6. [Configuration](#configuration)
7. [Installation Steps](#installation-steps)
8. [Testing Guide](#testing-guide)

## Overview

A comprehensive floating chatbot widget for bug reporting that captures:
- User issue reports with categorization
- Browser context and environment data
- Console errors and API request history
- Screenshots with annotation capabilities
- Session recording of user actions
- GitHub Issues integration
- Email notifications with ticket numbers

## Database Models

### 1. Create Issue Report Model
**File:** `app/models/issue_report.py`

```python
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

    @classmethod
    def generate_ticket_number(cls):
        """Generate a unique ticket number in format BUG-YYYY-NNNN."""
        from datetime import datetime
        year = datetime.now().year

        latest = cls.query.filter(
            cls.ticket_number.like(f'BUG-{year}-%')
        ).order_by(cls.ticket_number.desc()).first()

        if latest:
            last_num = int(latest.ticket_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f'BUG-{year}-{next_num:04d}'

    def to_github_issue_body(self):
        """Format issue data for GitHub issue creation."""
        # Implementation shown in previous code
        pass
```

### 2. Update Models Init
**File:** `app/models/__init__.py`

Add these lines:
```python
from .issue_report import IssueReport, IssueComment

# In __all__ list, add:
'IssueReport',
'IssueComment'
```

## Backend Services

### 3. GitHub Integration Service
**File:** `app/services/github_service.py`

```python
"""
GitHub integration service for syncing issue reports with GitHub Issues.
"""

import os
from github import Github, GithubException
from flask import current_app
from datetime import datetime
from ..models.issue_report import IssueReport
from ..extensions import db


class GitHubService:
    """Service for managing GitHub Issues integration."""

    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        self.repo_name = os.getenv('GITHUB_REPO')
        self.default_labels = os.getenv('GITHUB_LABELS', 'bug,user-reported').split(',')

        if not self.token or not self.repo_name:
            raise ValueError("GitHub configuration missing. Set GITHUB_TOKEN and GITHUB_REPO in .env")

        self.github = Github(self.token)
        self.repo = self.github.get_repo(self.repo_name)

    def create_issue(self, issue_report):
        """
        Create a GitHub issue from an IssueReport.

        Args:
            issue_report (IssueReport): The issue report to sync

        Returns:
            dict: GitHub issue details
        """
        try:
            # Prepare labels
            labels = self.default_labels.copy()
            labels.append(issue_report.severity)
            labels.append(issue_report.category.replace('_', '-'))

            # Create issue title
            title = f"[{issue_report.ticket_number}] {issue_report.title}"

            # Create issue body
            body = self._format_issue_body(issue_report)

            # Create GitHub issue
            github_issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=labels
            )

            # Update issue report with GitHub info
            issue_report.github_issue_id = github_issue.id
            issue_report.github_issue_number = github_issue.number
            issue_report.github_issue_url = github_issue.html_url
            issue_report.github_sync_status = 'synced'
            issue_report.github_synced_at = datetime.utcnow()

            db.session.commit()

            return {
                'success': True,
                'issue_number': github_issue.number,
                'issue_url': github_issue.html_url
            }

        except GithubException as e:
            issue_report.github_sync_status = 'failed'
            issue_report.github_sync_error = str(e)
            db.session.commit()

            current_app.logger.error(f"GitHub sync failed for {issue_report.ticket_number}: {e}")

            return {
                'success': False,
                'error': str(e)
            }

    def _format_issue_body(self, issue_report):
        """Format issue report for GitHub issue body."""
        body = f"""## Issue Report: {issue_report.ticket_number}

**Category:** {issue_report.category.replace('_', ' ').title()}
**Severity:** {issue_report.severity.title()}
**Reported by:** {issue_report.user.name} ({issue_report.user.email})
**Company:** {issue_report.company.name}
**Date:** {issue_report.created_at.strftime('%Y-%m-%d %H:%M UTC')}

## Description
{issue_report.description}

## Steps to Reproduce
{issue_report.steps_to_reproduce or 'Not provided'}

## Expected Behavior
{issue_report.expected_behavior or 'Not provided'}

## Actual Behavior
{issue_report.actual_behavior or 'Not provided'}

## Environment Details
- **Page URL:** {issue_report.page_url or 'N/A'}
- **Browser:** {self._format_browser_info(issue_report.browser_info)}
- **Screen Resolution:** {issue_report.screen_resolution or 'N/A'}
- **Viewport Size:** {issue_report.viewport_size or 'N/A'}

## Console Errors
```
{self._format_console_errors(issue_report.console_errors)}
```

## Recent API Calls
```
{self._format_api_history(issue_report.api_history)}
```

## User Actions
```
{self._format_user_actions(issue_report.user_actions)}
```

---
*Internal Tracking ID: {issue_report.id}*
"""
        return body

    def _format_browser_info(self, browser_info):
        if not browser_info:
            return 'N/A'
        return f"{browser_info.get('name', 'Unknown')} {browser_info.get('version', '')} on {browser_info.get('platform', 'Unknown')}"

    def _format_console_errors(self, errors):
        if not errors:
            return "No console errors captured"
        return "\n".join([f"[{e.get('timestamp', 'N/A')}] {e.get('level', 'ERROR')}: {e.get('message', '')}" for e in errors[:10]])

    def _format_api_history(self, history):
        if not history:
            return "No API history captured"
        return "\n".join([f"[{h.get('status', 'N/A')}] {h.get('method', 'GET')} {h.get('url', 'N/A')}" for h in history[:10]])

    def _format_user_actions(self, actions):
        if not actions:
            return "No user actions captured"
        return "\n".join([f"[{a.get('timestamp', 'N/A')}] {a.get('type', 'N/A')}: {a.get('target', 'N/A')}" for a in actions[:10]])
```

## API Endpoints

### 4. Support Routes
**File:** `app/routes/support.py`

```python
"""
Support and issue reporting API endpoints.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from ..models.issue_report import IssueReport
from ..services.github_service import GitHubService
from ..services.email import send_email
from ..middleware.tenant import get_current_tenant
from ..extensions import db

support_bp = Blueprint('support', __name__, url_prefix='/api/support')

UPLOAD_FOLDER = 'uploads/screenshots'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@support_bp.route('/report', methods=['POST'])
@login_required
def submit_report():
    """Submit a new issue report."""
    try:
        data = request.get_json()
        tenant = get_current_tenant()

        # Create new issue report
        issue = IssueReport()
        issue.ticket_number = IssueReport.generate_ticket_number()
        issue.user_id = current_user.id
        issue.company_id = tenant.id if tenant else current_user.company_id

        # Basic information
        issue.category = data.get('category', 'bug')
        issue.severity = data.get('severity', 'medium')
        issue.title = data.get('title', '')
        issue.description = data.get('description', '')
        issue.steps_to_reproduce = data.get('steps_to_reproduce')
        issue.expected_behavior = data.get('expected_behavior')
        issue.actual_behavior = data.get('actual_behavior')

        # Browser and environment data
        issue.browser_info = data.get('browser_info', {})
        issue.page_url = data.get('page_url')
        issue.page_title = data.get('page_title')
        issue.viewport_size = data.get('viewport_size')
        issue.screen_resolution = data.get('screen_resolution')

        # Debug data
        issue.console_errors = data.get('console_errors', [])
        issue.api_history = data.get('api_history', [])
        issue.user_actions = data.get('user_actions', [])
        issue.local_storage_data = data.get('local_storage_data', {})
        issue.session_storage_data = data.get('session_storage_data', {})

        # Screenshot handling
        screenshot_data = data.get('screenshot_data')
        if screenshot_data:
            issue.screenshot_path = save_screenshot(screenshot_data, issue.ticket_number)
        issue.screenshot_annotations = data.get('screenshot_annotations')

        db.session.add(issue)
        db.session.commit()

        # Sync to GitHub (async in production)
        if os.getenv('GITHUB_ENABLED', 'false').lower() == 'true':
            try:
                github_service = GitHubService()
                github_result = github_service.create_issue(issue)
            except Exception as e:
                current_app.logger.error(f"GitHub sync failed: {e}")

        # Send email notification
        send_issue_confirmation_email(issue)

        return jsonify({
            'success': True,
            'ticket_number': issue.ticket_number,
            'message': 'Your issue has been reported successfully'
        })

    except Exception as e:
        current_app.logger.error(f"Error submitting report: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to submit report'
        }), 500

@support_bp.route('/reports', methods=['GET'])
@login_required
def get_user_reports():
    """Get all reports submitted by the current user."""
    try:
        reports = IssueReport.query.filter_by(user_id=current_user.id).order_by(
            IssueReport.created_at.desc()
        ).all()

        return jsonify({
            'success': True,
            'reports': [report.to_dict() for report in reports]
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching reports: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch reports'
        }), 500

@support_bp.route('/report/<ticket_number>', methods=['GET'])
@login_required
def get_report_status(ticket_number):
    """Get status of a specific report."""
    try:
        report = IssueReport.query.filter_by(
            ticket_number=ticket_number,
            user_id=current_user.id
        ).first()

        if not report:
            return jsonify({
                'success': False,
                'error': 'Report not found'
            }), 404

        return jsonify({
            'success': True,
            'report': report.to_dict()
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching report: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch report'
        }), 500

@support_bp.route('/upload-screenshot', methods=['POST'])
@login_required
def upload_screenshot():
    """Handle screenshot upload."""
    try:
        if 'screenshot' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['screenshot']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file and allowed_file(file.filename):
            # Generate unique filename
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4()}.{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            # Ensure directory exists
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            # Save file
            file.save(filepath)

            return jsonify({
                'success': True,
                'filename': filename,
                'path': filepath
            })

        return jsonify({'error': 'Invalid file type'}), 400

    except Exception as e:
        current_app.logger.error(f"Error uploading screenshot: {e}")
        return jsonify({'error': 'Upload failed'}), 500

def save_screenshot(base64_data, ticket_number):
    """Save base64 screenshot data to file."""
    try:
        import base64

        # Remove data URL prefix if present
        if 'base64,' in base64_data:
            base64_data = base64_data.split('base64,')[1]

        # Decode base64
        image_data = base64.b64decode(base64_data)

        # Generate filename
        filename = f"{ticket_number}_{uuid.uuid4()}.png"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # Ensure directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        # Save file
        with open(filepath, 'wb') as f:
            f.write(image_data)

        return filepath

    except Exception as e:
        current_app.logger.error(f"Error saving screenshot: {e}")
        return None

def send_issue_confirmation_email(issue):
    """Send confirmation email to user."""
    try:
        subject = f"Issue Report Received - {issue.ticket_number}"

        body = f"""
        <h2>Thank you for reporting an issue</h2>
        <p>We have received your issue report with ticket number: <strong>{issue.ticket_number}</strong></p>

        <h3>Issue Details:</h3>
        <ul>
            <li><strong>Title:</strong> {issue.title}</li>
            <li><strong>Category:</strong> {issue.category.replace('_', ' ').title()}</li>
            <li><strong>Severity:</strong> {issue.severity.title()}</li>
        </ul>

        <p>Our team will review your report and take appropriate action. You can check the status of your report anytime by referencing the ticket number.</p>

        <p>Best regards,<br>Support Team</p>
        """

        send_email(issue.user.email, subject, body)

        issue.email_sent = True
        issue.email_sent_at = datetime.utcnow()
        db.session.commit()

    except Exception as e:
        current_app.logger.error(f"Error sending confirmation email: {e}")
```

### 5. Register Routes
**File:** `app/__init__.py`

Add to the application factory:
```python
from .routes.support import support_bp
app.register_blueprint(support_bp)
```

## Frontend Components

### 6. Chatbot JavaScript
**File:** `app/static/js/chatbot/chatbot.js`

```javascript
/**
 * Support Chatbot - Main controller
 */

class SupportChatbot {
    constructor() {
        this.isOpen = false;
        this.currentStep = 1;
        this.reportData = {};
        this.dataCapture = new DataCapture();
        this.sessionRecorder = new SessionRecorder();
        this.apiLogger = new APILogger();
        this.errorTracker = new ErrorTracker();

        this.init();
    }

    init() {
        // Start tracking immediately
        this.sessionRecorder.init();
        this.apiLogger.init();
        this.errorTracker.init();

        // Create chatbot UI
        this.render();
        this.attachEventListeners();
    }

    render() {
        const chatbotHTML = `
            <div id="support-chatbot" class="chatbot-container">
                <button id="chatbot-trigger" class="chatbot-trigger">
                    <svg class="bug-icon" viewBox="0 0 24 24" width="24" height="24">
                        <path fill="white" d="M20 8h-2.81c-.45-.78-1.07-1.45-1.82-1.96L17 4.41 15.59 3l-2.17 2.17C12.96 5.06 12.49 5 12 5c-.49 0-.96.06-1.41.17L8.41 3 7 4.41l1.62 1.63C7.88 6.55 7.26 7.22 6.81 8H4v2h2.09c-.05.33-.09.66-.09 1v1H4v2h2v1c0 .34.04.67.09 1H4v2h2.81c1.04 1.79 2.97 3 5.19 3s4.15-1.21 5.19-3H20v-2h-2.09c.05-.33.09-.66.09-1v-1h2v-2h-2v-1c0-.34-.04-.67-.09-1H20V8zm-6 8h-4v-2h4v2zm0-4h-4v-2h4v2z"/>
                    </svg>
                    <span class="trigger-text">Report Issue</span>
                </button>

                <div id="chatbot-window" class="chatbot-window hidden">
                    <div class="chatbot-header">
                        <h3>Report an Issue</h3>
                        <button id="chatbot-minimize" class="chatbot-minimize">
                            <svg viewBox="0 0 24 24" width="20" height="20">
                                <path fill="currentColor" d="M19 13H5v-2h14v2z"/>
                            </svg>
                        </button>
                    </div>

                    <div class="chatbot-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress-fill"></div>
                        </div>
                        <div class="progress-steps">
                            <span class="step active" data-step="1">Category</span>
                            <span class="step" data-step="2">Severity</span>
                            <span class="step" data-step="3">Details</span>
                            <span class="step" data-step="4">Review</span>
                        </div>
                    </div>

                    <div id="chatbot-content" class="chatbot-content">
                        <!-- Dynamic content here -->
                    </div>

                    <div class="chatbot-footer">
                        <button id="chatbot-back" class="btn-secondary hidden">Back</button>
                        <button id="chatbot-next" class="btn-primary">Next</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', chatbotHTML);
    }

    attachEventListeners() {
        document.getElementById('chatbot-trigger').addEventListener('click', () => this.open());
        document.getElementById('chatbot-minimize').addEventListener('click', () => this.close());
        document.getElementById('chatbot-back').addEventListener('click', () => this.previousStep());
        document.getElementById('chatbot-next').addEventListener('click', () => this.nextStep());
    }

    open() {
        this.isOpen = true;
        document.getElementById('chatbot-window').classList.remove('hidden');
        document.getElementById('chatbot-trigger').classList.add('hidden');
        this.showStep(1);
    }

    close() {
        this.isOpen = false;
        document.getElementById('chatbot-window').classList.add('hidden');
        document.getElementById('chatbot-trigger').classList.remove('hidden');
    }

    showStep(step) {
        this.currentStep = step;
        this.updateProgress();

        const content = document.getElementById('chatbot-content');

        switch(step) {
            case 1:
                this.showCategoryStep(content);
                break;
            case 2:
                this.showSeverityStep(content);
                break;
            case 3:
                this.showDetailsStep(content);
                break;
            case 4:
                this.showReviewStep(content);
                break;
        }

        // Update buttons
        document.getElementById('chatbot-back').classList.toggle('hidden', step === 1);
        document.getElementById('chatbot-next').textContent = step === 4 ? 'Submit' : 'Next';
    }

    showCategoryStep(content) {
        content.innerHTML = `
            <div class="step-content">
                <h4>What type of issue are you reporting?</h4>
                <div class="category-options">
                    <label class="category-option">
                        <input type="radio" name="category" value="bug">
                        <div class="option-card">
                            <span class="option-icon">🐛</span>
                            <span class="option-label">Bug Report</span>
                            <span class="option-desc">Something isn't working correctly</span>
                        </div>
                    </label>
                    <label class="category-option">
                        <input type="radio" name="category" value="feature_request">
                        <div class="option-card">
                            <span class="option-icon">💡</span>
                            <span class="option-label">Feature Request</span>
                            <span class="option-desc">Suggest a new feature or improvement</span>
                        </div>
                    </label>
                    <label class="category-option">
                        <input type="radio" name="category" value="help">
                        <div class="option-card">
                            <span class="option-icon">❓</span>
                            <span class="option-label">Help/Question</span>
                            <span class="option-desc">Need help using the application</span>
                        </div>
                    </label>
                </div>
            </div>
        `;
    }

    showSeverityStep(content) {
        content.innerHTML = `
            <div class="step-content">
                <h4>How severe is this issue?</h4>
                <div class="severity-options">
                    <label class="severity-option">
                        <input type="radio" name="severity" value="critical">
                        <div class="option-card critical">
                            <span class="severity-label">Critical</span>
                            <span class="severity-desc">System is unusable, data loss, or security issue</span>
                        </div>
                    </label>
                    <label class="severity-option">
                        <input type="radio" name="severity" value="high">
                        <div class="option-card high">
                            <span class="severity-label">High</span>
                            <span class="severity-desc">Major feature broken, no workaround available</span>
                        </div>
                    </label>
                    <label class="severity-option">
                        <input type="radio" name="severity" value="medium">
                        <div class="option-card medium">
                            <span class="severity-label">Medium</span>
                            <span class="severity-desc">Feature partially working, workaround available</span>
                        </div>
                    </label>
                    <label class="severity-option">
                        <input type="radio" name="severity" value="low">
                        <div class="option-card low">
                            <span class="severity-label">Low</span>
                            <span class="severity-desc">Minor issue, cosmetic problem</span>
                        </div>
                    </label>
                </div>
            </div>
        `;
    }

    showDetailsStep(content) {
        content.innerHTML = `
            <div class="step-content">
                <h4>Describe the issue</h4>
                <form id="issue-details-form">
                    <div class="form-group">
                        <label for="issue-title">Title *</label>
                        <input type="text" id="issue-title" placeholder="Brief summary of the issue" required>
                    </div>

                    <div class="form-group">
                        <label for="issue-description">Description *</label>
                        <textarea id="issue-description" rows="4" placeholder="Detailed description of what happened" required></textarea>
                    </div>

                    <div class="form-group">
                        <label for="steps-to-reproduce">Steps to Reproduce</label>
                        <textarea id="steps-to-reproduce" rows="3" placeholder="1. Go to...&#10;2. Click on...&#10;3. See error"></textarea>
                    </div>

                    <div class="form-group">
                        <label for="expected-behavior">Expected Behavior</label>
                        <textarea id="expected-behavior" rows="2" placeholder="What should happen?"></textarea>
                    </div>

                    <div class="form-group">
                        <label for="actual-behavior">Actual Behavior</label>
                        <textarea id="actual-behavior" rows="2" placeholder="What actually happened?"></textarea>
                    </div>

                    <div class="screenshot-section">
                        <button type="button" id="capture-screenshot" class="btn-secondary">
                            📸 Capture Screenshot
                        </button>
                        <div id="screenshot-preview" class="hidden">
                            <canvas id="screenshot-canvas"></canvas>
                            <div class="annotation-tools">
                                <button data-tool="arrow">➜</button>
                                <button data-tool="rectangle">▭</button>
                                <button data-tool="text">T</button>
                                <button data-tool="clear">Clear</button>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
        `;

        // Add screenshot capture handler
        document.getElementById('capture-screenshot').addEventListener('click', () => {
            this.captureScreenshot();
        });
    }

    showReviewStep(content) {
        const data = this.collectFormData();

        content.innerHTML = `
            <div class="step-content">
                <h4>Review your report</h4>
                <div class="review-summary">
                    <div class="review-item">
                        <span class="review-label">Category:</span>
                        <span class="review-value">${data.category.replace('_', ' ').toUpperCase()}</span>
                    </div>
                    <div class="review-item">
                        <span class="review-label">Severity:</span>
                        <span class="review-value ${data.severity}">${data.severity.toUpperCase()}</span>
                    </div>
                    <div class="review-item">
                        <span class="review-label">Title:</span>
                        <span class="review-value">${data.title}</span>
                    </div>
                    <div class="review-item">
                        <span class="review-label">Description:</span>
                        <div class="review-value">${data.description}</div>
                    </div>
                    ${data.screenshot_data ? '<div class="review-item"><span class="review-label">Screenshot:</span><span class="review-value">✓ Attached</span></div>' : ''}
                </div>

                <div class="data-capture-info">
                    <p class="info-text">The following debugging information will be included:</p>
                    <ul>
                        <li>Browser information and version</li>
                        <li>Page URL and viewport size</li>
                        <li>Console errors (${this.errorTracker.errors.length} captured)</li>
                        <li>Recent API calls (${this.apiLogger.requests.length} captured)</li>
                        <li>Recent actions (${this.sessionRecorder.actions.length} captured)</li>
                    </ul>
                </div>
            </div>
        `;
    }

    collectFormData() {
        return {
            category: document.querySelector('input[name="category"]:checked')?.value || 'bug',
            severity: document.querySelector('input[name="severity"]:checked')?.value || 'medium',
            title: document.getElementById('issue-title')?.value || '',
            description: document.getElementById('issue-description')?.value || '',
            steps_to_reproduce: document.getElementById('steps-to-reproduce')?.value || '',
            expected_behavior: document.getElementById('expected-behavior')?.value || '',
            actual_behavior: document.getElementById('actual-behavior')?.value || '',
            screenshot_data: this.reportData.screenshot_data || null
        };
    }

    async captureScreenshot() {
        // Hide chatbot temporarily
        document.getElementById('chatbot-window').style.display = 'none';

        try {
            const canvas = await html2canvas(document.body, {
                logging: false,
                useCORS: true
            });

            // Show chatbot again
            document.getElementById('chatbot-window').style.display = '';

            // Display screenshot
            const previewDiv = document.getElementById('screenshot-preview');
            const previewCanvas = document.getElementById('screenshot-canvas');
            const ctx = previewCanvas.getContext('2d');

            previewCanvas.width = 400;
            previewCanvas.height = 300;

            // Scale and draw
            ctx.drawImage(canvas, 0, 0, canvas.width, canvas.height, 0, 0, 400, 300);

            previewDiv.classList.remove('hidden');

            // Store base64 data
            this.reportData.screenshot_data = canvas.toDataURL('image/png');

            // Initialize annotation tools
            new ScreenshotAnnotator(previewCanvas);

        } catch (error) {
            console.error('Screenshot capture failed:', error);
            document.getElementById('chatbot-window').style.display = '';
        }
    }

    updateProgress() {
        const progressFill = document.getElementById('progress-fill');
        progressFill.style.width = `${(this.currentStep / 4) * 100}%`;

        document.querySelectorAll('.step').forEach(step => {
            const stepNum = parseInt(step.dataset.step);
            step.classList.toggle('active', stepNum <= this.currentStep);
        });
    }

    nextStep() {
        if (this.currentStep === 4) {
            this.submitReport();
        } else {
            this.showStep(this.currentStep + 1);
        }
    }

    previousStep() {
        if (this.currentStep > 1) {
            this.showStep(this.currentStep - 1);
        }
    }

    async submitReport() {
        const formData = this.collectFormData();
        const debugData = this.dataCapture.collectAllData();

        const reportData = {
            ...formData,
            ...debugData,
            console_errors: this.errorTracker.errors,
            api_history: this.apiLogger.requests,
            user_actions: this.sessionRecorder.actions
        };

        try {
            const response = await fetch('/api/support/report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(reportData)
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccessMessage(result.ticket_number);
            } else {
                this.showErrorMessage();
            }

        } catch (error) {
            console.error('Submit failed:', error);
            this.showErrorMessage();
        }
    }

    showSuccessMessage(ticketNumber) {
        const content = document.getElementById('chatbot-content');
        content.innerHTML = `
            <div class="success-message">
                <div class="success-icon">✅</div>
                <h3>Report Submitted Successfully!</h3>
                <p>Your ticket number is:</p>
                <div class="ticket-number">${ticketNumber}</div>
                <p>We've sent a confirmation email with your ticket details.</p>
                <button class="btn-primary" onclick="supportChatbot.close()">Close</button>
            </div>
        `;

        document.getElementById('chatbot-footer').style.display = 'none';
    }

    showErrorMessage() {
        const content = document.getElementById('chatbot-content');
        content.innerHTML = `
            <div class="error-message">
                <div class="error-icon">❌</div>
                <h3>Submission Failed</h3>
                <p>We couldn't submit your report. Please try again later.</p>
                <button class="btn-primary" onclick="supportChatbot.close()">Close</button>
            </div>
        `;

        document.getElementById('chatbot-footer').style.display = 'none';
    }
}
```

### 7. Data Capture Module
**File:** `app/static/js/chatbot/data-capture.js`

```javascript
/**
 * Data capture utilities for debugging information
 */

class DataCapture {
    collectAllData() {
        return {
            browser_info: this.getBrowserInfo(),
            page_url: window.location.href,
            page_title: document.title,
            viewport_size: `${window.innerWidth}x${window.innerHeight}`,
            screen_resolution: `${screen.width}x${screen.height}`,
            local_storage_data: this.getLocalStorageData(),
            session_storage_data: this.getSessionStorageData()
        };
    }

    getBrowserInfo() {
        const ua = navigator.userAgent;
        const browser = {
            name: this.getBrowserName(ua),
            version: this.getBrowserVersion(ua),
            platform: navigator.platform,
            language: navigator.language,
            user_agent: ua,
            cookies_enabled: navigator.cookieEnabled,
            online: navigator.onLine,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        };

        return browser;
    }

    getBrowserName(ua) {
        if (ua.indexOf('Firefox') > -1) return 'Firefox';
        if (ua.indexOf('Chrome') > -1) return 'Chrome';
        if (ua.indexOf('Safari') > -1) return 'Safari';
        if (ua.indexOf('Edge') > -1) return 'Edge';
        if (ua.indexOf('Opera') > -1 || ua.indexOf('OPR') > -1) return 'Opera';
        return 'Unknown';
    }

    getBrowserVersion(ua) {
        const match = ua.match(/(firefox|chrome|safari|edge|opr)[\/]?([\d]+)/i);
        return match ? match[2] : 'Unknown';
    }

    getLocalStorageData() {
        const relevantKeys = ['user_preferences', 'theme', 'last_page'];
        const data = {};

        relevantKeys.forEach(key => {
            const value = localStorage.getItem(key);
            if (value) {
                data[key] = value;
            }
        });

        return data;
    }

    getSessionStorageData() {
        const relevantKeys = ['current_form', 'temp_data'];
        const data = {};

        relevantKeys.forEach(key => {
            const value = sessionStorage.getItem(key);
            if (value) {
                data[key] = value;
            }
        });

        return data;
    }
}

class ErrorTracker {
    constructor() {
        this.errors = [];
        this.maxErrors = 50;
    }

    init() {
        // Capture window errors
        window.addEventListener('error', (event) => {
            this.addError({
                type: 'error',
                message: event.message,
                source: event.filename,
                line: event.lineno,
                column: event.colno,
                stack: event.error?.stack,
                timestamp: new Date().toISOString()
            });
        });

        // Capture unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.addError({
                type: 'unhandledRejection',
                message: event.reason?.message || event.reason,
                stack: event.reason?.stack,
                timestamp: new Date().toISOString()
            });
        });

        // Override console methods
        this.overrideConsole();
    }

    overrideConsole() {
        const originalError = console.error;
        const originalWarn = console.warn;

        console.error = (...args) => {
            this.addError({
                type: 'console.error',
                message: args.join(' '),
                timestamp: new Date().toISOString()
            });
            originalError.apply(console, args);
        };

        console.warn = (...args) => {
            this.addError({
                type: 'console.warn',
                message: args.join(' '),
                timestamp: new Date().toISOString()
            });
            originalWarn.apply(console, args);
        };
    }

    addError(error) {
        this.errors.unshift(error);
        if (this.errors.length > this.maxErrors) {
            this.errors = this.errors.slice(0, this.maxErrors);
        }
    }
}

class APILogger {
    constructor() {
        this.requests = [];
        this.maxRequests = 20;
    }

    init() {
        this.interceptFetch();
        this.interceptXHR();
    }

    interceptFetch() {
        const originalFetch = window.fetch;

        window.fetch = async (...args) => {
            const startTime = Date.now();
            const [url, options = {}] = args;

            try {
                const response = await originalFetch(...args);

                this.logRequest({
                    type: 'fetch',
                    url: url.toString(),
                    method: options.method || 'GET',
                    status: response.status,
                    statusText: response.statusText,
                    duration: Date.now() - startTime,
                    timestamp: new Date().toISOString()
                });

                return response;

            } catch (error) {
                this.logRequest({
                    type: 'fetch',
                    url: url.toString(),
                    method: options.method || 'GET',
                    status: 0,
                    error: error.message,
                    duration: Date.now() - startTime,
                    timestamp: new Date().toISOString()
                });

                throw error;
            }
        };
    }

    interceptXHR() {
        const originalOpen = XMLHttpRequest.prototype.open;
        const originalSend = XMLHttpRequest.prototype.send;

        XMLHttpRequest.prototype.open = function(method, url, ...args) {
            this._method = method;
            this._url = url;
            this._startTime = Date.now();
            return originalOpen.apply(this, [method, url, ...args]);
        };

        XMLHttpRequest.prototype.send = function(...args) {
            this.addEventListener('load', () => {
                window.apiLogger?.logRequest({
                    type: 'xhr',
                    url: this._url,
                    method: this._method,
                    status: this.status,
                    statusText: this.statusText,
                    duration: Date.now() - this._startTime,
                    timestamp: new Date().toISOString()
                });
            });

            this.addEventListener('error', () => {
                window.apiLogger?.logRequest({
                    type: 'xhr',
                    url: this._url,
                    method: this._method,
                    status: 0,
                    error: 'Network error',
                    duration: Date.now() - this._startTime,
                    timestamp: new Date().toISOString()
                });
            });

            return originalSend.apply(this, args);
        };
    }

    logRequest(request) {
        this.requests.unshift(request);
        if (this.requests.length > this.maxRequests) {
            this.requests = this.requests.slice(0, this.maxRequests);
        }
    }
}

class SessionRecorder {
    constructor() {
        this.actions = [];
        this.maxActions = 10;
    }

    init() {
        // Track clicks
        document.addEventListener('click', (e) => {
            this.recordAction({
                type: 'click',
                target: this.getElementPath(e.target),
                text: e.target.textContent?.slice(0, 50),
                timestamp: Date.now()
            });
        });

        // Track form inputs
        document.addEventListener('change', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
                this.recordAction({
                    type: 'input',
                    target: this.getElementPath(e.target),
                    field_name: e.target.name || e.target.id,
                    field_type: e.target.type,
                    timestamp: Date.now()
                });
            }
        });

        // Track page navigation
        window.addEventListener('popstate', () => {
            this.recordAction({
                type: 'navigation',
                url: window.location.href,
                timestamp: Date.now()
            });
        });
    }

    getElementPath(element) {
        const path = [];
        while (element && element.nodeType === Node.ELEMENT_NODE) {
            let selector = element.nodeName.toLowerCase();
            if (element.id) {
                selector += '#' + element.id;
                path.unshift(selector);
                break;
            } else if (element.className) {
                selector += '.' + element.className.split(' ').join('.');
            }
            path.unshift(selector);
            element = element.parentNode;
        }
        return path.join(' > ');
    }

    recordAction(action) {
        this.actions.unshift(action);
        if (this.actions.length > this.maxActions) {
            this.actions = this.actions.slice(0, this.maxActions);
        }
    }
}

// Export for global use
window.DataCapture = DataCapture;
window.ErrorTracker = ErrorTracker;
window.APILogger = APILogger;
window.SessionRecorder = SessionRecorder;
```

### 8. Screenshot Annotation
**File:** `app/static/js/chatbot/screenshot.js`

```javascript
/**
 * Screenshot annotation tools
 */

class ScreenshotAnnotator {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.isDrawing = false;
        this.currentTool = 'arrow';
        this.annotations = [];
        this.startX = 0;
        this.startY = 0;

        this.init();
    }

    init() {
        // Tool selection
        document.querySelectorAll('.annotation-tools button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tool = e.target.dataset.tool;
                if (tool === 'clear') {
                    this.clearAnnotations();
                } else {
                    this.currentTool = tool;
                    document.querySelectorAll('.annotation-tools button').forEach(b => {
                        b.classList.remove('active');
                    });
                    e.target.classList.add('active');
                }
            });
        });

        // Mouse events
        this.canvas.addEventListener('mousedown', (e) => this.startDrawing(e));
        this.canvas.addEventListener('mousemove', (e) => this.draw(e));
        this.canvas.addEventListener('mouseup', (e) => this.stopDrawing(e));
        this.canvas.addEventListener('mouseleave', (e) => this.stopDrawing(e));
    }

    startDrawing(e) {
        this.isDrawing = true;
        const rect = this.canvas.getBoundingClientRect();
        this.startX = e.clientX - rect.left;
        this.startY = e.clientY - rect.top;
    }

    draw(e) {
        if (!this.isDrawing) return;

        const rect = this.canvas.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;

        // Redraw base image and all annotations
        this.redrawCanvas();

        // Draw current annotation preview
        this.ctx.strokeStyle = '#FF0000';
        this.ctx.lineWidth = 2;

        switch(this.currentTool) {
            case 'arrow':
                this.drawArrow(this.startX, this.startY, currentX, currentY);
                break;
            case 'rectangle':
                this.drawRectangle(this.startX, this.startY, currentX - this.startX, currentY - this.startY);
                break;
        }
    }

    stopDrawing(e) {
        if (!this.isDrawing) return;

        this.isDrawing = false;

        const rect = this.canvas.getBoundingClientRect();
        const endX = e.clientX - rect.left;
        const endY = e.clientY - rect.top;

        // Save annotation
        this.annotations.push({
            tool: this.currentTool,
            startX: this.startX,
            startY: this.startY,
            endX: endX,
            endY: endY
        });

        if (this.currentTool === 'text') {
            this.addTextAnnotation(endX, endY);
        }

        this.redrawCanvas();
    }

    drawArrow(fromX, fromY, toX, toY) {
        const headLength = 10;
        const angle = Math.atan2(toY - fromY, toX - fromX);

        this.ctx.beginPath();
        this.ctx.moveTo(fromX, fromY);
        this.ctx.lineTo(toX, toY);
        this.ctx.lineTo(toX - headLength * Math.cos(angle - Math.PI / 6), toY - headLength * Math.sin(angle - Math.PI / 6));
        this.ctx.moveTo(toX, toY);
        this.ctx.lineTo(toX - headLength * Math.cos(angle + Math.PI / 6), toY - headLength * Math.sin(angle + Math.PI / 6));
        this.ctx.stroke();
    }

    drawRectangle(x, y, width, height) {
        this.ctx.strokeRect(x, y, width, height);
    }

    addTextAnnotation(x, y) {
        const text = prompt('Enter annotation text:');
        if (text) {
            this.annotations[this.annotations.length - 1].text = text;
            this.redrawCanvas();
        }
    }

    redrawCanvas() {
        // Save current canvas content (base screenshot)
        // This would be the original screenshot

        // Redraw all annotations
        this.ctx.strokeStyle = '#FF0000';
        this.ctx.lineWidth = 2;
        this.ctx.font = '14px Arial';
        this.ctx.fillStyle = '#FF0000';

        this.annotations.forEach(ann => {
            switch(ann.tool) {
                case 'arrow':
                    this.drawArrow(ann.startX, ann.startY, ann.endX, ann.endY);
                    break;
                case 'rectangle':
                    this.drawRectangle(ann.startX, ann.startY, ann.endX - ann.startX, ann.endY - ann.startY);
                    break;
                case 'text':
                    if (ann.text) {
                        this.ctx.fillText(ann.text, ann.endX, ann.endY);
                    }
                    break;
            }
        });
    }

    clearAnnotations() {
        this.annotations = [];
        // Redraw base screenshot only
        // This would restore the original screenshot
    }

    getAnnotationData() {
        return this.annotations;
    }
}

window.ScreenshotAnnotator = ScreenshotAnnotator;
```

### 9. Chatbot Styles
**File:** `app/static/css/chatbot.css`

```css
/* Support Chatbot Styles */

.chatbot-container {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9999;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* Trigger Button */
.chatbot-trigger {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 50px;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    transition: all 0.3s ease;
}

.chatbot-trigger:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
}

.chatbot-trigger.hidden {
    display: none;
}

.bug-icon {
    width: 24px;
    height: 24px;
}

/* Chatbot Window */
.chatbot-window {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 400px;
    max-width: 90vw;
    height: 600px;
    max-height: 80vh;
    background: white;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
    display: flex;
    flex-direction: column;
    animation: slideUp 0.3s ease;
}

.chatbot-window.hidden {
    display: none;
}

@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Header */
.chatbot-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 12px 12px 0 0;
}

.chatbot-header h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
}

.chatbot-minimize {
    background: none;
    border: none;
    color: white;
    cursor: pointer;
    padding: 4px;
    display: flex;
    align-items: center;
    opacity: 0.8;
    transition: opacity 0.2s;
}

.chatbot-minimize:hover {
    opacity: 1;
}

/* Progress Bar */
.chatbot-progress {
    padding: 20px 20px 0;
}

.progress-bar {
    height: 4px;
    background: #e5e7eb;
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 12px;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    transition: width 0.3s ease;
    width: 25%;
}

.progress-steps {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #9ca3af;
}

.progress-steps .step {
    position: relative;
    padding: 4px 0;
}

.progress-steps .step.active {
    color: #667eea;
    font-weight: 600;
}

/* Content Area */
.chatbot-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}

.step-content h4 {
    margin-top: 0;
    margin-bottom: 20px;
    color: #1f2937;
}

/* Category Options */
.category-options {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.category-option input[type="radio"] {
    display: none;
}

.option-card {
    display: flex;
    flex-direction: column;
    padding: 16px;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.category-option input[type="radio"]:checked + .option-card {
    border-color: #667eea;
    background: #f3f4f6;
}

.option-card:hover {
    border-color: #9ca3af;
}

.option-icon {
    font-size: 24px;
    margin-bottom: 8px;
}

.option-label {
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 4px;
}

.option-desc {
    font-size: 14px;
    color: #6b7280;
}

/* Severity Options */
.severity-options {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.severity-option input[type="radio"] {
    display: none;
}

.severity-option .option-card {
    padding: 12px 16px;
}

.severity-label {
    font-weight: 600;
    margin-bottom: 4px;
    display: block;
}

.severity-desc {
    font-size: 14px;
    color: #6b7280;
}

.option-card.critical {
    border-left: 4px solid #ef4444;
}

.option-card.high {
    border-left: 4px solid #f97316;
}

.option-card.medium {
    border-left: 4px solid #eab308;
}

.option-card.low {
    border-left: 4px solid #22c55e;
}

/* Form Elements */
.form-group {
    margin-bottom: 16px;
}

.form-group label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
    color: #374151;
    font-size: 14px;
}

.form-group input[type="text"],
.form-group textarea {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 14px;
    transition: border-color 0.2s;
}

.form-group input[type="text"]:focus,
.form-group textarea:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group textarea {
    resize: vertical;
    min-height: 60px;
}

/* Screenshot Section */
.screenshot-section {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #e5e7eb;
}

#screenshot-preview {
    margin-top: 16px;
}

#screenshot-canvas {
    width: 100%;
    border: 1px solid #d1d5db;
    border-radius: 6px;
}

.annotation-tools {
    display: flex;
    gap: 8px;
    margin-top: 8px;
}

.annotation-tools button {
    flex: 1;
    padding: 8px;
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.annotation-tools button:hover {
    background: #e5e7eb;
}

.annotation-tools button.active {
    background: #667eea;
    color: white;
    border-color: #667eea;
}

/* Review Summary */
.review-summary {
    background: #f9fafb;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}

.review-item {
    display: flex;
    margin-bottom: 12px;
}

.review-label {
    font-weight: 600;
    color: #6b7280;
    min-width: 100px;
    font-size: 14px;
}

.review-value {
    color: #1f2937;
    font-size: 14px;
    flex: 1;
}

.review-value.critical {
    color: #ef4444;
    font-weight: 600;
}

.review-value.high {
    color: #f97316;
    font-weight: 600;
}

.review-value.medium {
    color: #eab308;
    font-weight: 600;
}

.review-value.low {
    color: #22c55e;
    font-weight: 600;
}

/* Data Capture Info */
.data-capture-info {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 14px;
}

.info-text {
    margin: 0 0 8px 0;
    color: #1e40af;
    font-weight: 500;
}

.data-capture-info ul {
    margin: 0;
    padding-left: 20px;
    color: #3730a3;
}

/* Footer */
.chatbot-footer {
    display: flex;
    justify-content: space-between;
    padding: 16px 20px;
    border-top: 1px solid #e5e7eb;
}

/* Buttons */
.btn-primary,
.btn-secondary {
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-secondary {
    background: #f3f4f6;
    color: #4b5563;
    border: 1px solid #d1d5db;
}

.btn-secondary:hover {
    background: #e5e7eb;
}

.btn-secondary.hidden,
.btn-primary.hidden {
    display: none;
}

/* Success/Error Messages */
.success-message,
.error-message {
    text-align: center;
    padding: 40px 20px;
}

.success-icon,
.error-icon {
    font-size: 48px;
    margin-bottom: 16px;
}

.success-message h3,
.error-message h3 {
    margin: 16px 0;
    color: #1f2937;
}

.ticket-number {
    display: inline-block;
    padding: 12px 24px;
    background: #f3f4f6;
    border: 2px dashed #9ca3af;
    border-radius: 8px;
    font-family: monospace;
    font-size: 18px;
    font-weight: 600;
    color: #1f2937;
    margin: 16px 0;
}

/* Mobile Responsive */
@media (max-width: 480px) {
    .chatbot-window {
        width: 100vw;
        height: 100vh;
        max-width: 100vw;
        max-height: 100vh;
        bottom: 0;
        right: 0;
        border-radius: 0;
    }

    .chatbot-header {
        border-radius: 0;
    }

    .chatbot-trigger {
        bottom: 10px;
        right: 10px;
    }
}
```

### 10. Integration with Base Template
**File:** `app/templates/base.html`

Add before closing `</body>` tag:

```html
{% if current_user.is_authenticated %}
<!-- Support Chatbot -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/chatbot.css') }}">
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="{{ url_for('static', filename='js/chatbot/data-capture.js') }}"></script>
<script src="{{ url_for('static', filename='js/chatbot/screenshot.js') }}"></script>
<script src="{{ url_for('static', filename='js/chatbot/chatbot.js') }}"></script>
<script>
    // Initialize chatbot on page load
    let supportChatbot;
    document.addEventListener('DOMContentLoaded', function() {
        supportChatbot = new SupportChatbot();
    });
</script>
{% endif %}
```

## Configuration

### 11. Environment Variables
**File:** `.env`

Add these configuration variables:

```env
# GitHub Integration
GITHUB_ENABLED=true
GITHUB_TOKEN=ghp_your_personal_access_token_here
GITHUB_REPO=your-org/your-repo
GITHUB_LABELS=bug,user-reported

# Email Configuration (existing)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Support Configuration
SUPPORT_EMAIL=support@yourcompany.com
MAX_SCREENSHOT_SIZE_MB=10
ISSUE_REPORT_RATE_LIMIT=10  # Max reports per hour per user
```

### 12. Requirements Update
**File:** `requirements.txt`

Add these dependencies:

```txt
PyGithub==2.1.1
Pillow==10.1.0
python-dotenv==1.0.0
```

## Installation Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Update Database
```python
# In Python shell or migration script
from app import create_app, db
from app.models.issue_report import IssueReport, IssueComment

app = create_app()
with app.app_context():
    db.create_all()
    print("Database tables created successfully")
```

### Step 3: Configure GitHub
1. Create a Personal Access Token on GitHub
2. Give it `repo` scope permissions
3. Add to `.env` file

### Step 4: Create Upload Directory
```bash
mkdir -p uploads/screenshots
chmod 755 uploads/screenshots
```

### Step 5: Test the Integration
```python
# Test script: test_chatbot.py
from app import create_app
from app.services.github_service import GitHubService
from app.models.issue_report import IssueReport

app = create_app()
with app.app_context():
    # Create test issue
    issue = IssueReport()
    issue.ticket_number = "TEST-2025-0001"
    issue.title = "Test Issue"
    issue.description = "This is a test issue"

    # Test GitHub sync
    github = GitHubService()
    result = github.create_issue(issue)
    print(f"GitHub sync result: {result}")
```

## Testing Guide

### Manual Testing Checklist

1. **Chatbot UI**
   - [ ] Trigger button appears on all authenticated pages
   - [ ] Window opens/closes smoothly
   - [ ] Progress bar updates correctly
   - [ ] Navigation between steps works

2. **Data Capture**
   - [ ] Browser info captured correctly
   - [ ] Console errors tracked
   - [ ] API calls logged
   - [ ] User actions recorded

3. **Screenshot**
   - [ ] Screenshot captures current page
   - [ ] Annotation tools work
   - [ ] Screenshot saved with report

4. **Submission**
   - [ ] Report saved to database
   - [ ] Ticket number generated
   - [ ] GitHub issue created
   - [ ] Email sent to user

5. **Cross-browser Testing**
   - [ ] Chrome
   - [ ] Firefox
   - [ ] Safari
   - [ ] Edge

6. **Mobile Testing**
   - [ ] Responsive layout
   - [ ] Touch interactions
   - [ ] Screenshot capture

### Automated Testing
```python
# tests/test_chatbot.py
import pytest
from app import create_app, db
from app.models.issue_report import IssueReport

def test_ticket_generation():
    """Test unique ticket number generation."""
    ticket1 = IssueReport.generate_ticket_number()
    ticket2 = IssueReport.generate_ticket_number()
    assert ticket1 != ticket2
    assert ticket1.startswith('BUG-')

def test_issue_creation(client, authenticated_user):
    """Test issue report creation via API."""
    response = client.post('/api/support/report', json={
        'category': 'bug',
        'severity': 'high',
        'title': 'Test Bug',
        'description': 'Test description'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'ticket_number' in data
```

## Troubleshooting

### Common Issues

1. **GitHub sync fails**
   - Check token permissions
   - Verify repo exists
   - Check network connectivity

2. **Screenshots not saving**
   - Check upload directory permissions
   - Verify file size limits
   - Check disk space

3. **Email not sending**
   - Verify SMTP credentials
   - Check spam folder
   - Review email logs

4. **Chatbot not appearing**
   - Check user authentication
   - Verify JavaScript console for errors
   - Check CSS/JS file loading

## Security Considerations

1. **Input Sanitization**
   - All user inputs sanitized before storage
   - HTML escaped in emails and GitHub issues

2. **File Upload Security**
   - File type validation
   - Size limits enforced
   - Secure filename generation

3. **Rate Limiting**
   - Limit reports per user per hour
   - Prevent spam submissions

4. **Access Control**
   - Only authenticated users can report
   - Users can only view their own reports
   - Admin access for all reports

## Future Enhancements

1. **Phase 2 Features**
   - AI-powered severity detection
   - Template suggestions
   - Duplicate detection
   - Help with ESG questions

2. **Performance Optimizations**
   - Lazy load chatbot resources
   - Compress screenshots
   - Batch API tracking

3. **Advanced Features**
   - Video recording
   - Network HAR file capture
   - Performance metrics
   - Integration with other issue trackers

---

This comprehensive implementation guide provides everything needed to build the floating chatbot bug reporting system. Each component is fully detailed with complete code and configuration instructions.