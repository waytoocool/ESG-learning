# Phase 1: Backend Infrastructure - Requirements & Specifications

**Phase:** Backend Development
**Start Date:** 2025-01-05
**Duration:** 2 days
**Dependencies:** None
**Risk Level:** Low

## Phase Objectives

Implement the backend infrastructure for the bug reporting system, including database models, GitHub integration, API endpoints, and email notifications.

## Deliverables

1. Database models for storing issue reports
2. GitHub integration service
3. RESTful API endpoints for issue submission
4. Email confirmation system
5. Unit tests for all components

## Detailed Requirements

### 1. Database Models (`app/models/issue_report.py`)

#### 1.1 IssueReport Model

**Fields:**
```python
# Primary fields
- id: UUID (primary key)
- ticket_number: STRING(20) UNIQUE - Format: BUG-YYYY-NNNN

# Categorization
- category: ENUM('bug', 'feature_request', 'help', 'other')
- severity: ENUM('critical', 'high', 'medium', 'low')
- status: ENUM('new', 'in_review', 'assigned', 'in_progress', 'resolved', 'closed')

# Issue details
- title: STRING(255) REQUIRED
- description: TEXT REQUIRED
- steps_to_reproduce: TEXT OPTIONAL
- expected_behavior: TEXT OPTIONAL
- actual_behavior: TEXT OPTIONAL

# User context
- user_id: INTEGER FK(user.id) REQUIRED
- company_id: INTEGER FK(company.id) REQUIRED

# Browser & environment
- browser_info: JSON
- page_url: STRING(500)
- page_title: STRING(255)
- viewport_size: STRING(50)
- screen_resolution: STRING(50)

# Debug data
- console_errors: JSON (array of error objects)
- api_history: JSON (array of API call objects)
- user_actions: JSON (array of user action objects)
- local_storage_data: JSON
- session_storage_data: JSON

# Screenshots
- screenshot_path: STRING(500)
- screenshot_annotations: JSON
- attachments: JSON (array of file paths)

# GitHub integration
- github_issue_id: INTEGER
- github_issue_url: STRING(500)
- github_issue_number: INTEGER
- github_sync_status: ENUM('pending', 'synced', 'failed')
- github_sync_error: TEXT
- github_synced_at: DATETIME

# Timestamps
- created_at: DATETIME
- updated_at: DATETIME
- resolved_at: DATETIME

# Internal management
- internal_notes: TEXT
- assigned_to: STRING(100)
- resolution_notes: TEXT

# Email tracking
- email_sent: BOOLEAN
- email_sent_at: DATETIME
```

**Methods:**
```python
@classmethod
generate_ticket_number() -> str
    # Generate unique BUG-YYYY-NNNN format

to_dict() -> dict
    # Convert to JSON for API responses

to_github_issue_body() -> str
    # Format for GitHub issue creation
```

**Indexes:**
```sql
idx_ticket_number (ticket_number)
idx_user (user_id)
idx_company (company_id)
idx_status (status)
idx_severity (severity)
idx_category (category)
idx_created (created_at)
idx_github (github_issue_number)
```

#### 1.2 IssueComment Model

**Fields:**
```python
- id: UUID (primary key)
- issue_id: UUID FK(issue_reports.id)
- user_id: INTEGER FK(user.id)
- company_id: INTEGER FK(company.id)
- comment: TEXT REQUIRED
- is_internal: BOOLEAN (default: False)
- created_at: DATETIME
- updated_at: DATETIME
```

### 2. GitHub Integration Service (`app/services/github_service.py`)

#### 2.1 GitHubService Class

**Configuration:**
```python
__init__():
    - Load GITHUB_TOKEN from environment
    - Load GITHUB_REPO from environment
    - Load GITHUB_LABELS from environment
    - Initialize GitHub client
    - Connect to repository
```

**Methods:**
```python
create_issue(issue_report: IssueReport) -> dict:
    """
    Create a GitHub issue from an IssueReport.

    Args:
        issue_report: The issue report to sync

    Returns:
        {
            'success': bool,
            'issue_number': int,
            'issue_url': str,
            'error': str (if failed)
        }
    """
    - Format issue title: [ticket_number] title
    - Format issue body with all details
    - Apply labels based on category and severity
    - Create GitHub issue
    - Update issue_report with GitHub details
    - Commit to database
    - Handle errors gracefully

_format_issue_body(issue_report: IssueReport) -> str:
    """Format comprehensive issue body for GitHub"""
    - Include all issue details
    - Format browser information
    - Format console errors
    - Format API history
    - Format user actions
    - Add internal tracking ID

_format_browser_info(browser_info: dict) -> str:
    """Format browser info for display"""

_format_console_errors(errors: list) -> str:
    """Format console errors (limit to 10 most recent)"""

_format_api_history(history: list) -> str:
    """Format API call history (limit to 10 most recent)"""

_format_user_actions(actions: list) -> str:
    """Format user action history (limit to 10 most recent)"""
```

**Error Handling:**
- Catch GithubException
- Log errors
- Update sync_status to 'failed'
- Store error message
- Return failure response
- Don't crash the application

### 3. API Endpoints (`app/routes/support.py`)

#### 3.1 Blueprint Configuration
```python
Blueprint: support_bp
URL Prefix: /api/support
Authentication: @login_required on all endpoints
```

#### 3.2 POST /api/support/report

**Request Body:**
```json
{
  "category": "bug|feature_request|help|other",
  "severity": "critical|high|medium|low",
  "title": "string (required)",
  "description": "string (required)",
  "steps_to_reproduce": "string (optional)",
  "expected_behavior": "string (optional)",
  "actual_behavior": "string (optional)",
  "browser_info": {
    "name": "Chrome",
    "version": "120.0",
    "platform": "macOS",
    "user_agent": "...",
    "language": "en-US"
  },
  "page_url": "http://...",
  "page_title": "Page Title",
  "viewport_size": "1920x1080",
  "screen_resolution": "2560x1440",
  "console_errors": [...],
  "api_history": [...],
  "user_actions": [...],
  "local_storage_data": {...},
  "session_storage_data": {...},
  "screenshot_data": "base64_string",
  "screenshot_annotations": [...]
}
```

**Response:**
```json
{
  "success": true,
  "ticket_number": "BUG-2025-0001",
  "message": "Your issue has been reported successfully"
}
```

**Logic:**
1. Validate request data
2. Get current user and tenant
3. Create IssueReport record
4. Generate unique ticket number
5. Save screenshot if provided
6. Commit to database
7. Sync to GitHub (async in production)
8. Send confirmation email
9. Return success response

#### 3.3 GET /api/support/reports

**Query Parameters:**
- page: int (default: 1)
- per_page: int (default: 20, max: 100)
- status: string (filter by status)

**Response:**
```json
{
  "success": true,
  "reports": [
    {
      "id": "uuid",
      "ticket_number": "BUG-2025-0001",
      "category": "bug",
      "severity": "high",
      "status": "new",
      "title": "Export button not working",
      "created_at": "2025-01-05T14:30:00Z",
      "github_issue_url": "https://github.com/..."
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "pages": 3
  }
}
```

#### 3.4 GET /api/support/report/<ticket_number>

**Response:**
```json
{
  "success": true,
  "report": {
    "id": "uuid",
    "ticket_number": "BUG-2025-0001",
    "category": "bug",
    "severity": "high",
    "status": "in_progress",
    "title": "...",
    "description": "...",
    "user_name": "John Doe",
    "created_at": "2025-01-05T14:30:00Z",
    "updated_at": "2025-01-06T10:15:00Z",
    "github_issue_url": "https://github.com/..."
  }
}
```

#### 3.5 POST /api/support/upload-screenshot

**Request:**
- Multipart form data
- File field: 'screenshot'
- Allowed extensions: png, jpg, jpeg, gif
- Max size: 10MB

**Response:**
```json
{
  "success": true,
  "filename": "uuid.png",
  "path": "uploads/screenshots/uuid.png"
}
```

### 4. Email Service (`app/services/email.py`)

#### 4.1 Email Template (`app/templates/emails/issue_confirmation.html`)

**Content:**
```html
<html>
<head>
    <style>
        /* Professional email styling */
    </style>
</head>
<body>
    <h2>Thank you for reporting an issue</h2>
    <p>We have received your issue report.</p>

    <div class="ticket-box">
        <strong>Ticket Number:</strong> {{ ticket_number }}
    </div>

    <h3>Issue Details:</h3>
    <ul>
        <li><strong>Title:</strong> {{ title }}</li>
        <li><strong>Category:</strong> {{ category }}</li>
        <li><strong>Severity:</strong> {{ severity }}</li>
    </ul>

    <p>Our team will review your report and take appropriate action.</p>

    <p>Best regards,<br>Support Team</p>
</body>
</html>
```

#### 4.2 Email Function

```python
def send_issue_confirmation_email(issue: IssueReport):
    """
    Send confirmation email to user.

    Args:
        issue: The issue report that was created
    """
    - Format email subject
    - Render HTML template
    - Send via existing email service
    - Update issue.email_sent = True
    - Update issue.email_sent_at
    - Commit to database
    - Handle errors gracefully
```

### 5. File Upload Handling

**Directory Structure:**
```
uploads/
└── screenshots/
    ├── BUG-2025-0001_uuid.png
    ├── BUG-2025-0002_uuid.png
    └── ...
```

**Helper Functions:**
```python
allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""

save_screenshot(base64_data: str, ticket_number: str) -> str:
    """
    Save base64 screenshot to file.

    Args:
        base64_data: Base64 encoded image
        ticket_number: Ticket number for filename

    Returns:
        File path where screenshot was saved
    """
```

## Technical Specifications

### Environment Variables
```env
# GitHub Integration
GITHUB_ENABLED=true
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
GITHUB_REPO=owner/repo-name
GITHUB_LABELS=bug,user-reported

# Support Configuration
SUPPORT_EMAIL=support@company.com
MAX_SCREENSHOT_SIZE_MB=10
ISSUE_REPORT_RATE_LIMIT=10
```

### Dependencies
```
PyGithub==2.1.1
Pillow==10.1.0
python-dotenv==1.0.0
```

## Implementation Steps

### Step 1: Database Setup (2 hours)
1. Create `app/models/issue_report.py`
2. Define IssueReport model with all fields
3. Define IssueComment model
4. Update `app/models/__init__.py`
5. Run database migration: `db.create_all()`

### Step 2: GitHub Service (2 hours)
1. Install PyGithub
2. Create `app/services/github_service.py`
3. Implement GitHubService class
4. Test issue creation manually

### Step 3: API Endpoints (3 hours)
1. Create `app/routes/support.py`
2. Implement all endpoints
3. Add validation and error handling
4. Register blueprint in `app/__init__.py`

### Step 4: Email Service (1 hour)
1. Create email template
2. Implement email function
3. Test email sending

### Step 5: Testing (2 hours)
1. Unit tests for models
2. Unit tests for GitHub service
3. Integration tests for API endpoints
4. Manual testing with Postman

## Acceptance Criteria

- [ ] Database tables created successfully
- [ ] IssueReport.generate_ticket_number() creates unique tickets
- [ ] GitHub issue created with correct formatting
- [ ] API POST /report creates issue and returns ticket number
- [ ] API GET /reports returns user's issues
- [ ] API GET /report/<ticket> returns issue details
- [ ] Screenshot upload saves file correctly
- [ ] Email sent on issue submission
- [ ] All tests passing
- [ ] Multi-tenant isolation working (users only see their company's issues)
- [ ] Error handling prevents crashes

## Testing Checklist

### Unit Tests
- [ ] Test ticket number generation
- [ ] Test ticket number uniqueness
- [ ] Test to_dict() serialization
- [ ] Test to_github_issue_body() formatting
- [ ] Test GitHub service issue creation
- [ ] Test GitHub error handling
- [ ] Test screenshot file saving

### Integration Tests
- [ ] Test complete submission flow
- [ ] Test GitHub sync
- [ ] Test email delivery
- [ ] Test file upload
- [ ] Test multi-tenant isolation

### Manual Tests
- [ ] Submit report via Postman
- [ ] Verify database entry
- [ ] Verify GitHub issue created
- [ ] Verify email received
- [ ] Test with different companies
- [ ] Test error scenarios

## Deliverables Checklist

- [ ] `app/models/issue_report.py` - Complete
- [ ] `app/services/github_service.py` - Complete
- [ ] `app/routes/support.py` - Complete
- [ ] `app/templates/emails/issue_confirmation.html` - Complete
- [ ] `app/models/__init__.py` - Updated
- [ ] `app/__init__.py` - Blueprint registered
- [ ] Database migrated
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] Manual testing complete
- [ ] Documentation updated

## Notes for Implementation

1. **GitHub Token Security:**
   - Never commit token to git
   - Use environment variables only
   - Rotate token periodically

2. **Rate Limiting:**
   - GitHub API: 5000 requests/hour
   - Implement queue if needed
   - Handle rate limit errors

3. **Error Recovery:**
   - Save to database even if GitHub fails
   - Retry failed syncs
   - Log all errors

4. **Multi-Tenant:**
   - Always filter by company_id
   - Test cross-company isolation
   - Use existing TenantScopedMixin

5. **Performance:**
   - Index frequently queried fields
   - Optimize GitHub API calls
   - Compress screenshots if large

## Reference Implementation

See `CHATBOT_IMPLEMENTATION_GUIDE.md` sections:
- Database Models (lines 1-400)
- GitHub Integration Service (lines 400-700)
- API Endpoints (lines 700-1200)

## Success Metrics

- All API endpoints functional
- 100% GitHub sync success rate in testing
- Email delivery 100% in testing
- No security vulnerabilities
- Multi-tenant isolation verified
- Performance < 3 seconds for submission

---

**Status:** Ready for Implementation
**Assigned To:** Backend Developer / feature-developer agent
**Review Required:** Yes (code review before Phase 2)