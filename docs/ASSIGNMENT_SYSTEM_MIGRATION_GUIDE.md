# Assignment System Migration Guide

## Overview

This guide provides technical information for developers working with the Enhanced Assignment Management System (Feature Cycle 001). It covers database schema changes, API updates, and migration procedures.

## Table of Contents

1. [Database Schema Changes](#database-schema-changes)
2. [API Changes](#api-changes)
3. [Service Layer Updates](#service-layer-updates)
4. [Migration Procedures](#migration-procedures)
5. [Development Guidelines](#development-guidelines)

---

## Database Schema Changes

### DataPointAssignment Model Updates

The `DataPointAssignment` model has been enhanced with assignment versioning capabilities:

```python
# New columns added to DataPointAssignment
data_series_id = db.Column(db.String(36), nullable=False, index=True)  # UUID for assignment series
series_version = db.Column(db.Integer, nullable=False, default=1)      # Version number
series_status = db.Column(db.Enum('active', 'inactive', 'deprecated'), default='active')  # Status
```

### Schema Migration

**For Development**:
```bash
# Remove existing database and recreate with new schema
rm -f instance/esg_data.db
python3 run.py
# App will auto-create tables with new schema via db.create_all()
```

**For Production**:
```sql
-- Add new columns to existing DataPointAssignment table
ALTER TABLE data_point_assignment 
ADD COLUMN data_series_id VARCHAR(36) NOT NULL DEFAULT '';

ALTER TABLE data_point_assignment 
ADD COLUMN series_version INTEGER NOT NULL DEFAULT 1;

ALTER TABLE data_point_assignment 
ADD COLUMN series_status VARCHAR(20) NOT NULL DEFAULT 'active';

-- Create index on data_series_id for performance
CREATE INDEX idx_data_point_assignment_series_id 
ON data_point_assignment(data_series_id);

-- Update existing records to have proper data_series_id values
-- This should be done with a migration script that generates UUIDs
```

### Backward Compatibility

The system maintains backward compatibility through:
- **Dual ID Support**: Both `field_id` and `assignment_id` are supported in APIs
- **Default Values**: Existing assignments get default versioning values
- **Legacy Routes**: Existing API endpoints continue to work

---

## API Changes

### New Endpoints

#### Assignment History API
```python
# New blueprint: admin_assignment_history
GET /admin/assignment-history/                     # Main page
GET /admin/assignment-history/api/timeline         # Timeline data
GET /admin/assignment-history/api/data-series      # Data series info
GET /admin/assignment-history/api/assignments      # Assignment details
```

#### Bulk Operations API
```python
# New blueprint: admin_bulk_operations
POST /admin/bulk-operations/create-assignments     # Bulk create
POST /admin/bulk-operations/update-frequencies     # Bulk update
POST /admin/bulk-operations/copy-template          # Copy template
GET  /admin/bulk-operations/export                 # Export CSV
POST /admin/bulk-operations/import                 # Import CSV
GET  /admin/bulk-operations/templates              # Template info
GET  /admin/bulk-operations/download-template      # Download template
GET  /admin/bulk-operations/progress/<op_id>       # Progress tracking
```

#### Admin API Extensions
```python
# Added to existing admin.py
GET /admin/get_topics                              # Topics hierarchy
GET /admin/get_assignments_summary                 # Assignment statistics
GET /admin/bulk-operations                         # Bulk operations page
```

### Updated Response Formats

#### Assignment Response with Versioning
```json
{
  "assignment_id": "uuid",
  "field_id": "uuid", 
  "data_series_id": "uuid",
  "series_version": 1,
  "series_status": "active",
  "entity_id": 123,
  "frequency": "Annual",
  "unit": "kg",
  "assigned_topic_id": "uuid",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

#### Timeline Response Format
```json
{
  "success": true,
  "timeline": [
    {
      "date": "2025-01-15",
      "assignments": [
        {
          "assignment_id": "uuid",
          "field_name": "Field Name",
          "entity_name": "Entity Name", 
          "version": 1,
          "status": "active",
          "assigned_by": "User Name"
        }
      ]
    }
  ],
  "total_count": 150,
  "page": 1,
  "per_page": 50
}
```

---

## Service Layer Updates

### Assignment Versioning Service

**Location**: `app/services/assignment_versioning.py`

**Key Methods**:
```python
class AssignmentVersioningService:
    def create_assignment(self, field_id, entity_id, **config)
    def update_assignment(self, assignment_id, changes, reason=None)
    def get_assignment_history(self, data_series_id)
    def resolve_assignment(self, assignment_reference)  # < 50ms cached
    def get_active_version(self, data_series_id)
```

**Usage Examples**:
```python
from app.services.assignment_versioning import AssignmentVersioningService

service = AssignmentVersioningService()

# Create new assignment
assignment = service.create_assignment(
    field_id="field-uuid",
    entity_id=123,
    frequency="Annual",
    unit="kg"
)

# Update existing assignment (creates new version)
updated = service.update_assignment(
    assignment_id="assignment-uuid",
    changes={"frequency": "Quarterly"},
    reason="Regulatory requirement change"
)

# Get assignment history
history = service.get_assignment_history(data_series_id="series-uuid")
```

### Import/Export Operations

**Location**: Frontend implementation in `app/static/js/admin/assign_data_points_redesigned.js`

**Key Features**:
- **Export Assignments**: Download current assignment configurations as CSV
- **Import Assignments**: Upload CSV files to update assignment configurations
- **Real-time Validation**: Immediate feedback on import/export operations
- **UI Integration**: Seamlessly integrated with the assignment interface

**Usage**:
- Use the Export/Import buttons in the admin assignment interface
- Export downloads CSV with current configurations
- Import accepts CSV files with Field ID, Frequency, and Unit columns

---

## Migration Procedures

### Code Migration Steps

#### 1. Database Schema Update
```python
# For production environments, run schema migration
# Development: delete database and restart app

# Update model imports
from app.models.data_assignment import DataPointAssignment

# Check for new fields in model
assignment = DataPointAssignment.query.first()
print(f"Series ID: {assignment.data_series_id}")
print(f"Version: {assignment.series_version}")
print(f"Status: {assignment.series_status}")
```

#### 2. Update Existing Code

**Before** (Legacy):
```python
# Old assignment creation
assignment = DataPointAssignment(
    field_id=field_id,
    entity_id=entity_id,
    frequency=frequency
)
db.session.add(assignment)
db.session.commit()
```

**After** (With Versioning):
```python
# New assignment creation using service
from app.services.assignment_versioning import AssignmentVersioningService

service = AssignmentVersioningService()
assignment = service.create_assignment(
    field_id=field_id,
    entity_id=entity_id,
    frequency=frequency
)
```

#### 3. Update Frontend References

**Template Updates**:
```html
<!-- Add new navigation links -->
<li><a href="{{ url_for('admin.bulk_operations') }}">Bulk Operations</a></li>
<li><a href="{{ url_for('assignment_history.assignment_history') }}">Assignment History</a></li>
```

**JavaScript API Calls**:
```javascript
// Use new bulk operations APIs
fetch('/admin/bulk-operations/create-assignments', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        assignments: assignmentsData,
        validate_only: false
    })
})
.then(response => response.json())
.then(data => handleBulkCreateResult(data));
```

### Data Migration

#### Existing Assignment Versioning
```python
# Migration script to add versioning to existing assignments
from app.models.data_assignment import DataPointAssignment
import uuid

assignments = DataPointAssignment.query.all()
for assignment in assignments:
    if not assignment.data_series_id:
        assignment.data_series_id = str(uuid.uuid4())
        assignment.series_version = 1
        assignment.series_status = 'active'

db.session.commit()
```

#### Company Fiscal Year Migration
```python
# If companies need FY configuration
from app.models.company import Company

companies = Company.query.all()
for company in companies:
    if not hasattr(company, 'fiscal_year_start_month'):
        company.fiscal_year_start_month = 1  # January default
        company.fiscal_year_end_month = 12   # December default

db.session.commit()
```

---

## Development Guidelines

### Working with Assignment Versioning

#### Creating Assignments
Always use the `AssignmentVersioningService` for assignment operations:
```python
# Good
service = AssignmentVersioningService()
assignment = service.create_assignment(field_id, entity_id, **config)

# Avoid direct model creation for versioned operations
# assignment = DataPointAssignment(...)  # Don't do this for new assignments
```

#### Updating Assignments
```python
# Updates create new versions automatically
service = AssignmentVersioningService()
updated_assignment = service.update_assignment(
    assignment_id=assignment.id,
    changes={'frequency': 'Quarterly'},
    reason='Regulatory change'
)
```

#### Querying Assignments
```python
# Get active assignments only
active_assignments = DataPointAssignment.query.filter_by(
    series_status='active'
).all()

# Get specific version
assignment = service.resolve_assignment(assignment_id)  # Cached, < 50ms

# Get full history
history = service.get_assignment_history(data_series_id)
```

### Multi-Tenant Considerations

#### Always Respect Tenant Context
```python
# Good - uses tenant middleware
@admin_bp.route('/my-endpoint')
@admin_or_super_admin_required
def my_endpoint():
    tenant = get_current_tenant()
    assignments = DataPointAssignment.query.filter_by(
        company_id=tenant.id
    ).all()
    return jsonify(assignments)
```

#### SUPER_ADMIN Impersonation
```python
# Check for impersonation in templates
{% if current_user.role == 'SUPER_ADMIN' and not g.tenant %}
    <div class="alert">Please select a company to manage</div>
{% endif %}

# In routes, impersonation is enforced by decorators
@admin_or_super_admin_required  # Handles impersonation requirement
def admin_endpoint():
    # Admin logic here
    pass
```

### Performance Considerations

#### Assignment Resolution Caching
```python
# Use resolve_assignment for frequently accessed assignments
assignment = service.resolve_assignment(assignment_id)  # Cached

# Batch operations for multiple assignments
assignments = service.resolve_assignments_batch([id1, id2, id3])
```

#### Bulk Operations Limits
```python
# Respect batch size limits
MAX_BULK_CREATE = 1000
MAX_BULK_UPDATE = 500
MAX_TEMPLATE_TARGETS = 100

if len(assignments) > MAX_BULK_CREATE:
    raise ValueError(f"Bulk create limited to {MAX_BULK_CREATE} assignments")
```

### Testing Guidelines

#### Unit Testing Assignment Versioning
```python
def test_assignment_versioning():
    service = AssignmentVersioningService()
    
    # Create assignment
    assignment = service.create_assignment(field_id, entity_id, frequency="Annual")
    assert assignment.series_version == 1
    assert assignment.series_status == 'active'
    
    # Update assignment
    updated = service.update_assignment(
        assignment.id, 
        {'frequency': 'Quarterly'},
        reason='Test update'
    )
    assert updated.series_version == 2
    assert updated.data_series_id == assignment.data_series_id
```

#### Integration Testing Import/Export Operations
```python
def test_import_export_functionality():
    # Test frontend import/export through UI testing
    # The import/export functionality is now implemented in JavaScript
    # and should be tested through browser automation or UI tests

    # Example of testing the assignment interface:
    # 1. Configure some assignments through the UI
    # 2. Click Export button to download CSV
    # 3. Modify CSV file
    # 4. Click Import button to upload modified CSV
    # 5. Verify configurations were updated
    pass
```

---

## Troubleshooting

### Common Issues

#### 1. Schema Migration Errors
```bash
# If you see column not found errors:
rm instance/esg_data.db  # Development only
python3 run.py  # Recreates with new schema
```

#### 2. Impersonation Issues
```python
# Check SUPER_ADMIN access
if current_user.role == 'SUPER_ADMIN' and not g.tenant:
    # Redirect to impersonation selection
    return redirect(url_for('superadmin.dashboard'))
```

#### 3. Assignment Resolution Performance
```python
# If assignment resolution is slow:
# Check that caching is enabled
service = AssignmentVersioningService()
service.clear_cache()  # Reset cache if needed
```

#### 4. Bulk Operation Failures
```python
# Check validation errors in bulk operations
try:
    result = service.bulk_create_assignments(data, validate_only=True)
    if result['errors']:
        # Handle validation errors before actual creation
        process_validation_errors(result['errors'])
except Exception as e:
    logger.error(f"Bulk operation failed: {str(e)}")
```

### Debugging Tips

1. **Enable Detailed Logging**:
   ```python
   import logging
   logging.getLogger('app.services.assignment_versioning').setLevel(logging.DEBUG)
   ```

2. **Check Database State**:
   ```python
   # Verify assignment versioning data
   assignment = DataPointAssignment.query.first()
   print(f"ID: {assignment.id}, Series: {assignment.data_series_id}, Version: {assignment.series_version}")
   ```

3. **Test API Endpoints**:
   ```bash
   # Test new endpoints
   curl -X GET "http://localhost:8000/admin/get_topics" -H "Cookie: session=..."
   curl -X GET "http://localhost:8000/admin/assignment-history/api/timeline" -H "Cookie: session=..."
   ```

---

## Summary

The Enhanced Assignment Management System introduces:

- **Assignment versioning** with complete audit trails
- **Bulk operations** for efficient assignment management  
- **Assignment history** with timeline visualization
- **SUPER_ADMIN impersonation** for secure multi-tenant access

Key migration considerations:
- Database schema updates with new versioning columns
- Service layer integration for assignment operations
- Frontend updates for new functionality
- Multi-tenant security through impersonation requirements

This system maintains backward compatibility while providing powerful new capabilities for assignment lifecycle management.