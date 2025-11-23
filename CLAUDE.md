# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
python3 run.py                    # Start Flask dev server on http://127-0-0-1.nip.io:8000/
```

### Dependencies
```bash
pip install -r requirements.txt  # Install Python dependencies
npm install                      # Install Node.js dependencies (for E2E tests)
```

## Architecture Overview

### Core Framework
- **Flask** web application with SQLAlchemy ORM
- **Multi-tenant architecture** with company-based data isolation via tenant middleware
- **Role-based access control** with USER, ADMIN, and SUPER_ADMIN roles
- **Session-based authentication** with Flask-Login
- **SQLite database** (configurable via DATABASE_URL environment variable)

### Application Structure
```
app/
├── __init__.py           # Application factory with blueprints and initialization
├── config.py            # Configuration classes (Dev/Prod/Test)
├── extensions.py        # Flask extensions (db, login_manager, mail)
├── models/              # SQLAlchemy models with multi-tenant support
│   ├── company.py      # Company/tenant details
│   ├── user.py         # User model with role-based access
│   ├── entity.py       # Entity model for data collection
│   ├── esg_data.py     # Core ESG data model
│   ├── framework.py    # ESG framework model
│   ├── data_assignment.py  # Data point assignment model
│   ├── dimension.py    # Dimensional data model
│   ├── audit_log.py    # Audit trail and logging model
│   ├── sync_operation.py  # Synchronization operations model
│   ├── system_config.py  # System configuration model
│   └── mixins.py       # Shared model mixins
├── routes/              # Blueprint-based route handlers
│   ├── auth.py         # Authentication routes
│   ├── admin.py        # Admin dashboard and data management
│   ├── admin_assignment_history.py  # Assignment history and versioning
│   ├── admin_assignments_api.py    # Assignment API endpoints
│   ├── admin_frameworks_api.py     # Framework management API
│   ├── superadmin.py   # Super admin company management
│   └── user.py         # User dashboard and data entry
├── services/           # Business logic and services
│   ├── assignment_versioning.py  # Assignment lifecycle management
│   ├── frameworks_service.py  # Framework management service
│   ├── analytics_service.py  # Analytics and reporting
│   ├── email.py        # Email notification service
│   ├── initial_data.py # Initial data setup service
│   └── [other services] # Additional business logic services
├── middleware/         # Custom middleware (tenant isolation)
│   └── tenant.py       # Multi-tenant middleware
├── decorators/         # Custom decorators (role-based auth)
│   └── auth.py         # Authentication decorators
├── templates/          # Jinja2 templates
│   ├── admin/          # Admin interface templates
│   ├── superadmin/     # Super admin templates
│   └── user/           # User interface templates
├── static/             # CSS, JavaScript, and assets
│   ├── css/            # Stylesheets (admin/, common/, superadmin/, user/)
│   └── js/             # JavaScript files (admin/, common/, user/)
└── utils/              # Utility functions and helpers
    ├── helpers.py      # General helper functions
    ├── field_import_templates.py  # Import template utilities
    └── unit_conversions.py  # Unit conversion utilities
```



### Key Models and Data Flow
- **Company**: Multi-tenant isolation unit - all data scoped to companies
- **User**: Belongs to a company, has role (USER/ADMIN/SUPER_ADMIN)
- **Entity**: Data collection entities within a company (e.g., facilities, departments)
- **Framework**: ESG reporting frameworks (GRI, TCFD, SASB, etc.) with data points and topics
- **ESGData**: Core data entries with audit trails, file attachments, and versioning
- **DataPointAssignment**: Admin-controlled assignments of framework data points to entities with versioning
- **Dimension**: Support for dimensional data (geographical, temporal, operational breakdowns)
- **AuditLog**: Comprehensive audit trail for all data changes and system actions
- **SyncOperation**: Data synchronization operations and status tracking
- **SystemConfig**: System-wide configuration and settings

## UI Views and User Roles

### 1. 🔑 SUPER_ADMIN (Global Access)
**Login URL**: `http://127-0-0-1.nip.io:8000/login`
- **Credentials**: admin@yourdomain.com / changeme
- **Key Features**:
  - **Impersonation System**: Must impersonate company admins to access company-specific features
  - **Company Management**: Create, manage, and monitor all companies
  - **System Administration**: Global framework management, system health monitoring
  - **Cross-Tenant Access**: Can access any company's data through impersonation
- **Important Links**:
  - Dashboard: `http://127-0-0-1.nip.io:8000/superadmin/dashboard`
  - All Users (has impersonation feature): `http://127-0-0-1.nip.io:8000/superadmin/users`
  - Framework Sync: `http://127-0-0-1.nip.io:8000/superadmin/framework-sync`

### 2. 👨‍💼 ADMIN (Company Management)
**Login URL**: `http://{company-slug}.127-0-0-1.nip.io:8000/login`
- **Access Pattern**: Must use company-specific tenant URL
- **Key Features**:
  - **Data Hierarchy**: Manage entities, facilities, and organizational structure
  - **Framework Management**: Assign and configure ESG frameworks for the company
  - **Data Point Assignment**: Control which data points are assigned to which entities
  - **Assignment History**: Track changes and versioning of assignments
  - **Bulk Operations**: Import/export assignments, bulk updates
- **Important Links** (for test-company-alpha):
  - Admin Dashboard: `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/`
  - Data Hierarchy: `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/data-hierarchy`
  - Frameworks: `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/frameworks`
  - Assign Data Points: `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points`

### 3. 👤 USER (Data Entry)
**Login URL**: `http://{company-slug}.127-0-0-1.nip.io:8000/login`
- **Access Pattern**: Must use company-specific tenant URL
- **Key Features**:
  - **Data Dashboard**: View assigned data points and submission status
  - **Data Entry**: Submit ESG data for assigned data points
  - **File Attachments**: Upload supporting documents
  - **Data Review**: Review and validate submitted data
- **Important Links** (for test-company-alpha):
  - User Dashboard: `http://test-company-alpha.127-0-0-1.nip.io:8000/user/dashboard`
  - Data Entry: `http://test-company-alpha.127-0-0-1.nip.io:8000/user/dashboard` (main interface)

### 🔗 Quick Access Links

**IMPORTANT**: Users and admins must access the application through their company-specific tenant URLs. Direct login is only available for SUPER_ADMIN.

#### Test Company Alpha (test-company-alpha)
- **Admin Access**: `http://test-company-alpha.127-0-0-1.nip.io:8000/`
- **User Access**: `http://test-company-alpha.127-0-0-1.nip.io:8000/`
- **Admin Credentials**: alice@alpha.com / admin123, carol@alpha.com / manager123
- **User Credentials**: bob@alpha.com / user123

#### Test Company Beta (test-company-beta)
- **Admin Access**: `http://test-company-beta.127-0-0-1.nip.io:8000/`
- **User Access**: `http://test-company-beta.127-0-0-1.nip.io:8000/`
- **Admin Credentials**: david@beta.com / admin123
- **User Credentials**: eve@beta.com / user123, frank@beta.com / analyst123

#### Test Company Gamma (test-company-gamma)
- **Admin Access**: `http://test-company-gamma.127-0-0-1.nip.io:8000/`
- **User Access**: `http://test-company-gamma.127-0-0-1.nip.io:8000/`
- **Admin Credentials**: grace@gamma.com / admin123
- **User Credentials**: henry@gamma.com / user123

### 🔗 Access Instructions
1. **SUPER_ADMIN**: Login at main domain, then use impersonation to access company contexts
2. **Company Users/Admins**: Must use their company's tenant URL for direct access
3. **Tenant URL Format**: `http://{company-slug}.127-0-0-1.nip.io:8000/`
4. **Multi-Tenant Isolation**: Users can only access data within their company's tenant context

The SUPER_ADMIN can impersonate any company admin for cross-tenant management.

### Multi-Tenant Architecture
- **Tenant Middleware** (`app/middleware/tenant.py`): Automatically filters all queries by current user's company
- **Automatic Scoping**: All database operations are automatically scoped to the current tenant
- **Data Isolation**: Companies cannot access each other's data
- **SUPER_ADMIN Exception**: Only SUPER_ADMIN users can cross tenant boundaries

## Environment Configuration
### Required Environment Variables
```bash
DATABASE_URL=sqlite:///instance/esg_data.db  # Database connection
SECRET_KEY=your-secret-key                   # Flask secret key
MAIL_USERNAME=your-gmail@gmail.com           # Email service
MAIL_PASSWORD=your-app-password              # Gmail app password
```

### Optional Environment Variables
```bash
SUPER_ADMIN_EMAIL=admin@yourdomain.com       # Super admin email
SUPER_ADMIN_PASSWORD=changeme                # Super admin password
SUPER_ADMIN_USERNAME=superadmin              # Super admin username
REDIS_URL=redis://localhost:6379/0           # Redis for caching
REDIS_ENABLED=true                           # Enable Redis caching
SESSION_COOKIE_DOMAIN=.nip.io               # Cross-subdomain sessions
```
- IMPORTANT do not change the super admin email and password. If you are having trouble in authentication then reset the email and password to these default variables


## Testing Strategy

All new and ongoing testing is now consolidated under the Visual Testing with Playwright MCP workflow or Chrome DevTools MCP .

### Visual Testing with for ui-testing-agent to use Playwright MCP Tools
- **Primary Test Suite**: All core and regression tests are implemented as Playwright MCP visual/UI tests.
- **UI Testing Sub-Agent**: Use `@ui-testing-agent` for comprehensive post-implementation and pre-merge validation. ui-testing-agent is supposed to only use Playwright MCP.
- **On-Demand Validation**: UI testing agent should be invoked after each feature implementation and before merges.
- **MCP Server Requirement**: Refer to MCP documentations
- **For Browser error** if we get error "Browse already in use" then force close the browser

### Visual Testing with for non sub agent to use Chrome DevTools MCP
- **Primary Test Suite**: Use Chrome DevTools MCP for all the tests non related to ui-testing-agent. If there are any issues with Chrome DevTools then fall back to use Playwright MCP if it is not in use.
- **MCP Server Requirement**: Refer to MCP documentation for more details.

### MCP Servers Configuration
For detailed information about MCP server setup, configuration, and usage, see **[MCP_SERVERS_CONFIG.md](./MCP_SERVERS_CONFIG.md)**. This includes:
- **Playwright MCP**: Automated browser testing and UI validation. Supports both Chrome and Firefox.
- **Chrome DevTools MCP**: Browser debugging, performance profiling, and DevTools integration
- Quick start guides, troubleshooting, and best practices. Supports Chrome.


## Claude Development Team Documentation Structure/ New Feature Documentaion

### Overview
The Claude Development Team follows a structured documentation approach with a product-manager-agent coordinating with specialized sub-agents (backend-developer, ui-testing-agent).

### Documentation Hierarchy
For development documentaion
```
Claude Development Team/{feature-name}-{feature-start-date-YYYY-MM-DD}/
├── Main requirements-and-specs.md                    # The first file to be created, mother of the full developement cycle, requirements & specs
├── Parent Folder or {feature-cycle}-{}{feature-cycle-start-date-YYYY-MM-DD}/
│   ├── requirements-and-specs.md                    # The requirements & specs of the phase or the specific feature cycle
│   ├── backend-developer/                          # Backend developer implementation notes & reports
│   │   ├── backend-developer-report.md
│   │   ├── other files created by backend developer...
│   ├── backend-reviewer/                           # Backend reviewer validation & findings
│   │   ├── backend-reviewer-report.md
│   │   ├── other files created by backend reviewer...
│   ├── ui-testing-agent/                           # UI testing results & screenshots add version numbers of the test based on the previous tests
│   │   ├── Reports_v{version-number}/
│   │   │   ├── Testing_Summary_{feature-name}_Phase{number}_v{version-number}.md
│   │   │   └── screenshots/
│   │   │       ├── desktop-*.png
│   │   └── test-{YYYY-MM-DD}-{feature-name}/
│   └── DEVELOPMENT_LOG_TEMPLATE.md                 # Depricated
```
Include final completion documentaion

## Development Notes

### Assignment System Database Changes
- **DataPointAssignment Model**: Enhanced with data_series_id, series_version, series_status for versioning
- **Assignment Versioning**: New versioning system tracks assignment lifecycle and changes
- **Company Fiscal Year**: Centralized FY configuration in Company model
- **Backward Compatibility**: Dual support for field_id and assignment_id references

### Database Schema
- Uses `db.create_all()` for table creation (no migrations)
- Schema changes require manual database recreation in development
- Production deployments should use proper migration strategy
- **Assignment Versioning Schema**: data_series_id (UUID), series_version (Integer), series_status (Enum)

### Multi-Tenant Considerations
- All models except User and Company should inherit from tenant-aware base classes
- Always test data isolation between different companies
- Be careful with raw SQL queries - they bypass tenant filtering
- **SUPER_ADMIN Access**: Must use impersonation for company-specific operations
- **Assignment Operations**: All bulk operations respect tenant boundaries
- **Cross-Tenant Prevention**: Assignment history and bulk operations enforce strict tenant isolation

### Framework Management
- Frameworks are global but assignments are company-specific
- Admins can only assign data points within their company
- SUPER_ADMIN can manage global framework definitions

### File Uploads
- Configured for 20MB max file size
- Multiple format support (documents, spreadsheets, images, archives)
- Upload directory: `uploads/` (configurable via `UPLOAD_FOLDER`)
- go to user, and impersonate as admin
