# Phase 1: Backend Developer Implementation Report

**Project:** User Dashboard Enhancements - Modal Infrastructure
**Phase:** Phase 1 - Core Modal Infrastructure
**Date:** 2025-01-04
**Developer:** Backend Developer Agent (Claude)
**Status:** ✅ Complete

---

## Executive Summary

Phase 1 implementation is complete. All backend service layers, API endpoints, dashboard routes, and HTML template structure have been implemented according to specifications. The system is ready for Phase 2 (JavaScript/frontend logic implementation).

### Deliverables Status

| Component | Status | Files Created |
|-----------|--------|---------------|
| Service Layer | ✅ Complete | 3 services + __init__ |
| API Endpoints | ✅ Complete | 3 API blueprints |
| Dashboard Route | ✅ Complete | Updated dashboard.py |
| Template Structure | ✅ Complete | dashboard.html |
| Blueprint Registration | ✅ Complete | Updated routes/__init__.py |

---

## 1. Service Layer Implementation

### 1.1 Entity Service (`app/services/user_v2/entity_service.py`)

**Purpose:** Manage entity access, switching, and hierarchical relationships for users.

#### Key Methods

##### `get_user_entities(user_id: int) -> List[Entity]`
- Returns all entities accessible by the user
- ADMIN users: All entities in their company
- USER users: Only their assigned entity
- Implements proper tenant isolation

```python
# Example usage
entities = EntityService.get_user_entities(current_user.id)
# Returns: [Entity(id=1, name='Facility Alpha-1'), Entity(id=2, name='Facility Alpha-2')]
```

##### `get_current_entity(user_id: int) -> Optional[Entity]`
- Retrieves the user's currently selected entity
- Returns None if user has no entity assigned

##### `switch_entity(user_id: int, entity_id: int) -> Dict[str, Any]`
- Switches admin user's current entity context
- Validates entity access and company membership
- Updates user.entity_id in database
- Returns success/error response

**Response Format:**
```json
{
  "success": true,
  "message": "Switched to entity: Facility Alpha-2",
  "entity": {
    "id": 2,
    "name": "Facility Alpha-2",
    "type": "facility",
    "parent_id": null
  }
}
```

##### `get_entity_hierarchy(entity_id: int) -> Dict[str, Any]`
- Returns full hierarchical path from root to entity
- Useful for breadcrumb navigation

**Response Format:**
```json
{
  "entity_id": 3,
  "path": [
    {"id": 1, "name": "Company", "type": "company"},
    {"id": 2, "name": "Region A", "type": "region"},
    {"id": 3, "name": "Facility A1", "type": "facility"}
  ],
  "level": 3
}
```

##### `get_entity_assignment_count(entity_id: int) -> Dict[str, int]`
- Returns counts of data point assignments
- Separates raw vs computed fields

**Response Format:**
```json
{
  "total": 25,
  "raw": 20,
  "computed": 5
}
```

---

### 1.2 Field Service (`app/services/user_v2/field_service.py`)

**Purpose:** Manage field details, metadata, dimensions, and validation.

#### Key Methods

##### `get_field_details(field_id: str, entity_id: int) -> Dict[str, Any]`
- Comprehensive field information retrieval
- Includes dimensions, validation rules, assignment info
- Returns dependencies for computed fields

**Response Format:**
```json
{
  "success": true,
  "field_id": "abc-123",
  "field_name": "Employee Count",
  "field_code": "employee_count",
  "field_type": "raw_input",
  "data_type": "number",
  "unit_category": "count",
  "default_unit": "employees",
  "description": "Total number of employees",
  "dimensions": [
    {
      "dimension_id": "dim-1",
      "name": "Gender",
      "is_required": true,
      "values": [
        {
          "value_id": "v1",
          "value": "Male",
          "display_name": "Male",
          "effective_display_name": "Male"
        }
      ]
    }
  ],
  "validation_rules": {
    "required": true,
    "data_type": "number",
    "frequency": "Monthly",
    "valid_reporting_dates": ["2024-01-31", "2024-02-29", ...]
  },
  "assignment": {
    "assignment_id": "assign-1",
    "frequency": "Monthly",
    "unit": "employees",
    "data_series_id": "series-1",
    "series_version": 1,
    "series_status": "active",
    "topic_name": "Employee Metrics",
    "topic_path": "Social > Employment > Employee Metrics"
  },
  "dependencies": [],
  "formula_expression": null,
  "constant_multiplier": null
}
```

##### `get_assigned_fields_for_entity(entity_id: int, include_computed: bool) -> List[Dict]`
- Returns all assigned fields for an entity
- Includes hierarchical entity assignments (parent entities)
- Optional computed field filtering

**Response Format:**
```json
[
  {
    "field_id": "abc-123",
    "field_name": "Employee Count",
    "field_code": "employee_count",
    "is_computed": false,
    "value_type": "NUMBER",
    "unit_category": "count",
    "default_unit": "employees",
    "assignment_id": "assign-1",
    "frequency": "Monthly",
    "entity_id": 1,
    "topic_name": "Employee Metrics"
  }
]
```

##### `validate_field_value(field_id: str, value: Any, dimension_values: Optional[Dict]) -> Dict`
- Validates field values against type and dimension requirements
- Returns validation result with error messages

**Response Format:**
```json
{
  "valid": true
}
// or
{
  "valid": false,
  "error": "Required dimension 'Gender' is missing"
}
```

---

### 1.3 Historical Data Service (`app/services/user_v2/historical_data_service.py`)

**Purpose:** Query and retrieve historical ESG data submissions.

#### Key Methods

##### `get_historical_data(field_id, entity_id, start_date, end_date, limit) -> Dict`
- Returns historical data submissions with attachments
- Supports date range filtering
- Includes dimension values and metadata

**Response Format:**
```json
{
  "success": true,
  "field_id": "abc-123",
  "field_name": "Employee Count",
  "entity_id": 1,
  "total_count": 12,
  "data": [
    {
      "id": "data-1",
      "reporting_date": "2024-01-31",
      "raw_value": "500",
      "calculated_value": null,
      "unit": "employees",
      "dimension_values": {"gender": "Male", "age": "<30"},
      "status": "submitted",
      "created_at": "2024-02-01T10:00:00Z",
      "updated_at": "2024-02-01T10:00:00Z",
      "attachments": [
        {
          "id": "att-1",
          "filename": "employee_report.pdf",
          "file_size": 1024000,
          "mime_type": "application/pdf",
          "uploaded_at": "2024-02-01T10:05:00Z"
        }
      ]
    }
  ],
  "is_computed": false
}
```

##### `get_data_summary(field_id: str, entity_id: int) -> Dict`
- Summary statistics for numerical fields
- Date range information
- Total submission count

**Response Format:**
```json
{
  "success": true,
  "field_id": "abc-123",
  "entity_id": 1,
  "total_submissions": 12,
  "date_range": {
    "earliest": "2023-01-31",
    "latest": "2024-12-31"
  },
  "statistics": {
    "min": 450,
    "max": 550,
    "average": 500,
    "count": 12
  }
}
```

##### `get_data_by_date_range(entity_id, start_date, end_date, field_ids) -> Dict`
- All data for entity within date range
- Optional field filtering
- Organized by date and field

##### `check_data_completeness(entity_id: int, reporting_date: date) -> Dict`
- Completeness check for specific date
- Lists missing fields
- Calculates completeness percentage

**Response Format:**
```json
{
  "success": true,
  "entity_id": 1,
  "reporting_date": "2024-01-31",
  "total_fields": 25,
  "submitted_count": 20,
  "missing_count": 5,
  "completeness_percentage": 80.0,
  "missing_fields": [
    {
      "field_id": "field-1",
      "field_name": "Water Consumption",
      "is_computed": false
    }
  ]
}
```

---

## 2. API Endpoint Implementation

### 2.1 Entity API (`app/routes/user_v2/entity_api.py`)

**Blueprint Prefix:** `/api/user/v2`

#### Endpoints

##### `GET /api/user/v2/entities`
- **Auth:** @tenant_required_for('USER')
- **Purpose:** Get all accessible entities
- **Response:** List of entities with assignment counts

**Example Request:**
```bash
curl -X GET http://test-company-alpha.127-0-0-1.nip.io:8000/api/user/v2/entities \
  -H "Cookie: session=..."
```

**Example Response:**
```json
{
  "success": true,
  "entities": [
    {
      "id": 1,
      "name": "Facility Alpha-1",
      "type": "facility",
      "is_current": true,
      "parent_id": null,
      "assignment_count": 15
    },
    {
      "id": 2,
      "name": "Facility Alpha-2",
      "type": "facility",
      "is_current": false,
      "parent_id": null,
      "assignment_count": 12
    }
  ],
  "current_entity_id": 1
}
```

##### `POST /api/user/v2/switch-entity`
- **Auth:** @tenant_required_for('ADMIN')
- **Purpose:** Switch current entity (admin only)
- **Request Body:** `{"entity_id": 2}`

**Example Request:**
```bash
curl -X POST http://test-company-alpha.127-0-0-1.nip.io:8000/api/user/v2/switch-entity \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"entity_id": 2}'
```

##### `GET /api/user/v2/entity-hierarchy/<entity_id>`
- **Auth:** @tenant_required_for('USER')
- **Purpose:** Get hierarchical path for entity
- **Response:** Full entity hierarchy

##### `GET /api/user/v2/entity-stats/<entity_id>`
- **Auth:** @tenant_required_for('USER')
- **Purpose:** Get assignment statistics for entity
- **Response:** Assignment counts (total, raw, computed)

---

### 2.2 Field API (`app/routes/user_v2/field_api.py`)

**Blueprint Prefix:** `/api/user/v2`

#### Endpoints

##### `GET /api/user/v2/field-details/<field_id>`
- **Auth:** @tenant_required_for('USER')
- **Query Params:** `entity_id` (optional, defaults to current user's entity)
- **Purpose:** Get comprehensive field details

**Example Request:**
```bash
curl -X GET "http://test-company-alpha.127-0-0-1.nip.io:8000/api/user/v2/field-details/abc-123?entity_id=1" \
  -H "Cookie: session=..."
```

##### `GET /api/user/v2/assigned-fields`
- **Auth:** @tenant_required_for('USER')
- **Query Params:**
  - `include_computed` (optional, default: true)
  - `entity_id` (optional, defaults to current user's entity)
- **Purpose:** Get all assigned fields for entity

**Example Request:**
```bash
curl -X GET "http://test-company-alpha.127-0-0-1.nip.io:8000/api/user/v2/assigned-fields?include_computed=true&entity_id=1" \
  -H "Cookie: session=..."
```

**Example Response:**
```json
{
  "success": true,
  "entity_id": 1,
  "fields": [
    {
      "field_id": "abc-123",
      "field_name": "Employee Count",
      "is_computed": false,
      "value_type": "NUMBER",
      "frequency": "Monthly",
      "assignment_id": "assign-1"
    }
  ],
  "total_count": 15
}
```

##### `POST /api/user/v2/validate-value`
- **Auth:** @tenant_required_for('USER')
- **Request Body:** `{"field_id": "abc-123", "value": 500, "dimension_values": {...}}`
- **Purpose:** Validate field value

**Example Request:**
```bash
curl -X POST http://test-company-alpha.127-0-0-1.nip.io:8000/api/user/v2/validate-value \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{
    "field_id": "abc-123",
    "value": 500,
    "dimension_values": {"gender": "Male", "age": "<30"}
  }'
```

---

### 2.3 Data API (`app/routes/user_v2/data_api.py`)

**Blueprint Prefix:** `/api/user/v2`

#### Endpoints

##### `GET /api/user/v2/historical-data/<field_id>`
- **Auth:** @tenant_required_for('USER')
- **Query Params:**
  - `entity_id` (optional)
  - `start_date` (optional, YYYY-MM-DD)
  - `end_date` (optional, YYYY-MM-DD)
  - `limit` (optional, default: 50)
- **Purpose:** Get historical data submissions

**Example Request:**
```bash
curl -X GET "http://test-company-alpha.127-0-0-1.nip.io:8000/api/user/v2/historical-data/abc-123?start_date=2024-01-01&end_date=2024-12-31&limit=50" \
  -H "Cookie: session=..."
```

##### `GET /api/user/v2/data-summary/<field_id>`
- **Auth:** @tenant_required_for('USER')
- **Query Params:** `entity_id` (optional)
- **Purpose:** Get summary statistics

##### `GET /api/user/v2/data-by-date-range`
- **Auth:** @tenant_required_for('USER')
- **Query Params:**
  - `entity_id` (optional)
  - `start_date` (required, YYYY-MM-DD)
  - `end_date` (required, YYYY-MM-DD)
  - `field_ids` (optional, comma-separated)
- **Purpose:** Get all data within date range

**Example Request:**
```bash
curl -X GET "http://test-company-alpha.127-0-0-1.nip.io:8000/api/user/v2/data-by-date-range?start_date=2024-01-01&end_date=2024-12-31&field_ids=abc-123,def-456" \
  -H "Cookie: session=..."
```

##### `GET /api/user/v2/data-completeness`
- **Auth:** @tenant_required_for('USER')
- **Query Params:**
  - `entity_id` (optional)
  - `reporting_date` (required, YYYY-MM-DD)
- **Purpose:** Check data completeness for date

**Example Request:**
```bash
curl -X GET "http://test-company-alpha.127-0-0-1.nip.io:8000/api/user/v2/data-completeness?reporting_date=2024-01-31&entity_id=1" \
  -H "Cookie: session=..."
```

---

## 3. Dashboard Route Implementation

### 3.1 Updated Dashboard Route (`app/routes/user_v2/dashboard.py`)

**Route:** `/user/v2/dashboard`
**Methods:** GET
**Auth:** @login_required, @tenant_required_for('USER')

#### Implementation Details

**Key Features:**
1. ✅ Checks if user has opted into new interface (redirects if not)
2. ✅ Validates user has entity assigned
3. ✅ Loads accessible entities (for entity switcher)
4. ✅ Retrieves assigned fields using FieldService
5. ✅ Separates raw input fields from computed fields
6. ✅ Determines field status (empty/partial/complete) based on today's data
7. ✅ Passes comprehensive context to template

**Context Data Structure:**
```python
{
    'user_name': 'Alice Admin',
    'user_role': 'ADMIN',
    'current_entity': {
        'id': 1,
        'name': 'Facility Alpha-1',
        'type': 'facility'
    },
    'entities': [
        {'id': 1, 'name': 'Facility Alpha-1', 'type': 'facility', 'is_current': True},
        {'id': 2, 'name': 'Facility Alpha-2', 'type': 'facility', 'is_current': False}
    ],
    'raw_input_fields': [
        {
            'field_id': 'abc-123',
            'field_name': 'Employee Count',
            'field_code': 'employee_count',
            'is_computed': False,
            'value_type': 'NUMBER',
            'unit_category': 'count',
            'default_unit': 'employees',
            'assignment_id': 'assign-1',
            'frequency': 'Monthly',
            'entity_id': 1,
            'topic_name': 'Employee Metrics',
            'status': 'complete'  # Added by dashboard route
        }
    ],
    'computed_fields': [...],
    'total_fields': 25,
    'raw_count': 20,
    'computed_count': 5,
    'selected_date': '2025-01-04'
}
```

---

## 4. Template Structure Implementation

### 4.1 Dashboard Template (`app/templates/user_v2/dashboard.html`)

**Template Features:**

#### Header Section
- ✅ User welcome message
- ✅ Entity switcher dropdown (visible for admins with multiple entities)
- ✅ Current entity display (for non-admins or single-entity admins)
- ✅ Legacy view toggle button

#### Statistics Cards
- ✅ Total fields count
- ✅ Raw input fields count
- ✅ Computed fields count
- ✅ Date selector

#### Data Points Tables
- ✅ Separate tables for raw input and computed fields
- ✅ Columns: Field Name, Topic, Frequency, Unit, Status, Actions
- ✅ Status badges (complete/partial/empty)
- ✅ Action buttons ("Enter Data" / "View Details")

#### Modal Dialog Structure
- ✅ Modal overlay with backdrop
- ✅ Modal header with field name and entity name
- ✅ Tab navigation (Current Entry, Historical Data, Field Info)
- ✅ Current Entry tab with form fields:
  - Reporting date input
  - Data value input
  - Dimension fields (hidden by default)
  - File upload area with drag-and-drop
- ✅ Historical Data tab (placeholder)
- ✅ Field Info tab (placeholder)
- ✅ Modal footer with action buttons (Cancel, Save Draft, Submit)

#### JavaScript Placeholders (Phase 1)
- ✅ Modal open/close functionality
- ✅ Tab switching logic
- ✅ Entity switcher event handler
- ✅ File upload area interactions
- ✅ Legacy dashboard toggle
- ✅ Console logging for API integration points (Phase 2)

---

## 5. Blueprint Registration

### 5.1 Updated Files

#### `app/routes/user_v2/__init__.py`
```python
# Import and register API blueprints
from .entity_api import entity_api_bp
from .field_api import field_api_bp
from .data_api import data_api_bp

# Export all blueprints for registration in app factory
__all__ = ['user_v2_bp', 'entity_api_bp', 'field_api_bp', 'data_api_bp']
```

#### `app/routes/__init__.py`
```python
from .user_v2 import user_v2_bp, entity_api_bp, field_api_bp, data_api_bp

blueprints = [
    auth_bp,
    admin_bp,
    ...
    user_v2_bp,
    entity_api_bp,  # User V2 Entity API
    field_api_bp,   # User V2 Field API
    data_api_bp,    # User V2 Data API
    superadmin_bp
]
```

---

## 6. Integration Points

### 6.1 Database Models Used

| Model | Usage |
|-------|-------|
| `Entity` | Entity management, hierarchy traversal |
| `User` | User authentication, entity assignment |
| `FrameworkDataField` | Field metadata, validation rules |
| `DataPointAssignment` | Assignment resolution, frequency info |
| `ESGData` | Historical data retrieval, status checks |
| `ESGDataAttachment` | File attachment information |
| `Dimension`, `FieldDimension`, `DimensionValue` | Dimensional data support |
| `FieldVariableMapping` | Computed field dependencies |

### 6.2 Authentication & Authorization

All API endpoints implement:
- ✅ `@login_required` - Flask-Login authentication
- ✅ `@tenant_required_for('USER')` or `@tenant_required_for('ADMIN')` - Tenant isolation
- ✅ Entity access validation
- ✅ Company membership verification

### 6.3 Error Handling

All service methods and API endpoints include:
- ✅ Try-catch exception handling
- ✅ Validation of required parameters
- ✅ Proper HTTP status codes (200, 400, 403, 404, 500)
- ✅ JSON error responses with descriptive messages

---

## 7. Testing Notes

### 7.1 Manual Testing Checklist

**Service Layer:**
- [ ] Test entity access for USER vs ADMIN roles
- [ ] Verify entity switching updates database
- [ ] Check hierarchical entity queries
- [ ] Validate field details retrieval with dimensions
- [ ] Test historical data date range filtering
- [ ] Verify data completeness calculations

**API Endpoints:**
- [ ] Test all endpoints with authentication
- [ ] Verify tenant isolation (cross-tenant access blocked)
- [ ] Test query parameter validation
- [ ] Check JSON response formats
- [ ] Verify error responses

**Dashboard:**
- [ ] Test dashboard loading for USER and ADMIN
- [ ] Verify entity switcher visibility and functionality
- [ ] Check field categorization (raw vs computed)
- [ ] Test modal opening/closing
- [ ] Verify tab switching
- [ ] Test legacy dashboard toggle

### 7.2 Test Scenarios

**Scenario 1: Admin User with Multiple Entities**
1. Login as alice@alpha.com (ADMIN)
2. Access /user/v2/dashboard
3. Verify entity switcher shows 2+ entities
4. Switch entity using dropdown
5. Verify assigned fields update

**Scenario 2: Regular User**
1. Login as bob@alpha.com (USER)
2. Access /user/v2/dashboard
3. Verify entity switcher NOT visible
4. Verify correct entity name displayed
5. Check assigned fields load correctly

**Scenario 3: API Endpoint Testing**
1. Call GET /api/user/v2/entities
2. Verify entities list returned
3. Call GET /api/user/v2/field-details/{field_id}
4. Verify dimensions, validation rules included
5. Call GET /api/user/v2/historical-data/{field_id}
6. Verify historical data with attachments returned

---

## 8. Known Limitations (Phase 1)

### 8.1 JavaScript Functionality
- ❌ Modal tabs are functional but API calls not implemented
- ❌ File upload accepts files but doesn't upload
- ❌ Data submission form doesn't call API
- ❌ Historical data tab doesn't fetch data
- ❌ Field info tab doesn't fetch metadata
- ❌ Entity switcher logs to console but doesn't call API

**Note:** These are intentional - Phase 2 will implement all JavaScript/AJAX functionality.

### 8.2 Features Not Implemented
- ❌ Data validation on frontend
- ❌ Dimension picker UI logic
- ❌ File preview thumbnails
- ❌ Unsaved changes warning
- ❌ Loading states and spinners
- ❌ Real-time field status updates

---

## 9. Files Created/Modified

### Created Files

**Services:**
- `/app/services/user_v2/__init__.py`
- `/app/services/user_v2/entity_service.py`
- `/app/services/user_v2/field_service.py`
- `/app/services/user_v2/historical_data_service.py`

**API Routes:**
- `/app/routes/user_v2/entity_api.py`
- `/app/routes/user_v2/field_api.py`
- `/app/routes/user_v2/data_api.py`

**Templates:**
- `/app/templates/user_v2/dashboard.html`

### Modified Files

**Routes:**
- `/app/routes/user_v2/__init__.py` - Added API blueprint imports
- `/app/routes/user_v2/dashboard.py` - Full dashboard implementation
- `/app/routes/__init__.py` - Registered new API blueprints

---

## 10. Next Steps (Phase 2)

### 10.1 Frontend JavaScript Implementation
1. Implement modal data loading via API calls
2. Add form submission logic with validation
3. Implement file upload with progress indicators
4. Add historical data table rendering
5. Implement field info tab with metadata display
6. Add dimension picker UI logic
7. Implement unsaved changes warning
8. Add loading states and error handling

### 10.2 User Experience Enhancements
1. Add date picker restrictions based on assignment frequency
2. Implement real-time field status updates
3. Add keyboard navigation (ESC, Tab, Enter)
4. Implement accessibility features (ARIA labels, focus management)
5. Add mobile-responsive enhancements
6. Implement file preview thumbnails

### 10.3 Data Submission
1. Implement data entry form submission
2. Add dimension value selection UI
3. Implement save draft functionality
4. Add validation feedback
5. Implement computed field recalculation triggers

---

## 11. Code Quality & Standards

### 11.1 Code Organization
- ✅ Clear separation of concerns (services, routes, templates)
- ✅ Consistent naming conventions
- ✅ Comprehensive docstrings for all methods
- ✅ Type hints for function parameters and returns
- ✅ Proper error handling with try-catch blocks

### 11.2 Security
- ✅ Authentication required for all endpoints
- ✅ Tenant isolation enforced
- ✅ SQL injection prevention (using SQLAlchemy ORM)
- ✅ CSRF protection via Flask sessions
- ✅ Access control validation (admin-only endpoints)

### 11.3 Performance Considerations
- ✅ Database queries optimized with joins
- ✅ Limited query results with `limit` parameter
- ✅ Eager loading of relationships where appropriate
- ✅ Indexed fields used in queries (entity_id, field_id)

---

## 12. Conclusion

Phase 1 implementation is complete and ready for Phase 2 (JavaScript/frontend logic). All backend services, API endpoints, and HTML template structure are in place. The system provides:

1. ✅ Complete service layer for entity, field, and data management
2. ✅ RESTful API endpoints with proper authentication
3. ✅ Dashboard route with comprehensive data loading
4. ✅ HTML template with modal structure and basic interactivity
5. ✅ Proper blueprint registration and integration

The implementation follows best practices for:
- Code organization and separation of concerns
- Security and authentication
- Error handling and validation
- Database query optimization
- Tenant isolation and data access control

**Status:** Ready for Phase 2 implementation by UI Developer Agent.

---

## Appendix A: API Endpoint Summary

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/api/user/v2/entities` | USER | List accessible entities |
| POST | `/api/user/v2/switch-entity` | ADMIN | Switch current entity |
| GET | `/api/user/v2/entity-hierarchy/<id>` | USER | Get entity hierarchy |
| GET | `/api/user/v2/entity-stats/<id>` | USER | Get entity statistics |
| GET | `/api/user/v2/field-details/<id>` | USER | Get field details |
| GET | `/api/user/v2/assigned-fields` | USER | List assigned fields |
| POST | `/api/user/v2/validate-value` | USER | Validate field value |
| GET | `/api/user/v2/historical-data/<id>` | USER | Get historical data |
| GET | `/api/user/v2/data-summary/<id>` | USER | Get data summary |
| GET | `/api/user/v2/data-by-date-range` | USER | Get data by date range |
| GET | `/api/user/v2/data-completeness` | USER | Check completeness |

---

## Appendix B: Database Query Examples

### Example 1: Get Assigned Fields with Hierarchy
```python
# Get entity and its parent entities for hierarchical assignments
entity = Entity.query.get(entity_id)
entity_ids = [entity_id]
current_entity = entity
while current_entity and current_entity.parent_id:
    entity_ids.append(current_entity.parent_id)
    current_entity = current_entity.parent

# Get active assignments for these entities
assignments = DataPointAssignment.query.filter(
    DataPointAssignment.entity_id.in_(entity_ids),
    DataPointAssignment.series_status == 'active'
).all()
```

### Example 2: Get Historical Data with Date Filtering
```python
query = ESGData.query.filter_by(
    field_id=field_id,
    entity_id=entity_id
).filter(
    ESGData.raw_value.isnot(None) | ESGData.calculated_value.isnot(None)
)

if start_date:
    query = query.filter(ESGData.reporting_date >= start_date)
if end_date:
    query = query.filter(ESGData.reporting_date <= end_date)

entries = query.order_by(ESGData.reporting_date.desc()).limit(limit).all()
```

---

**Report Generated:** 2025-01-04
**Backend Developer:** Claude (Anthropic)
**Phase Status:** ✅ Complete
