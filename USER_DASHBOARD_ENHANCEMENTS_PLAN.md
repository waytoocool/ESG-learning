# User Dashboard Enhancements Implementation Plan

## Overview
Comprehensive plan to enhance the User Dashboard with modal-based data collection, dimensional data support, entity management, and contextual computation information.

## Key Features to Implement

### 1. Modal Dialog for Data Collection
- Replace inline table editing with a comprehensive modal dialog
- Support both raw and computed field display
- Include file upload capabilities for evidence/attachments
- Show historical data for context

### 2. Dimensional Data Collection
- Display all dimension combinations as separate input fields
- Automatically calculate and display totals
- Support framework-defined dimensions (no dynamic add/remove)
- Validate against defined dimension values

### 3. Entity Management
- Display current entity name prominently
- Add entity switcher for users with multi-entity access
- Maintain entity context across sessions

### 4. Computation Context Modals
- Show formulas and calculation methods for computed fields
- Display dependencies and their current values
- Provide calculation breakdown for transparency

### 5. Historical Data Display
- Show previous submissions in the dialog
- Display trends and changes over time
- Separate views for raw vs computed fields

## Technical Architecture

### Data Model Enhancement - Enhanced JSON Storage

We will use the existing `dimension_values` JSON column in the ESGData model with an enhanced structure to support comprehensive dimensional data collection:

```python
# ESGData model - Enhanced JSON structure
dimension_values = db.Column(db.JSON)  # Existing column

# Enhanced JSON structure for dimensional data:
{
    "version": 2,  # Schema version for future migrations
    "dimensions": ["gender", "age"],  # Active dimensions for this field
    "breakdowns": [
        {
            "dimensions": {"gender": "Male", "age": "<30"},
            "raw_value": 100,
            "notes": "Q1 2024 headcount"
        },
        {
            "dimensions": {"gender": "Male", "age": "30-50"},
            "raw_value": 150,
            "notes": null
        },
        {
            "dimensions": {"gender": "Female", "age": "<30"},
            "raw_value": 120,
            "notes": null
        },
        # ... all dimension combinations
    ],
    "totals": {
        "overall": 500,  # Grand total
        "by_dimension": {
            "gender": {
                "Male": 250,
                "Female": 215,
                "Other": 35
            },
            "age": {
                "<30": 165,
                "30-50": 230,
                ">50": 105
            }
        }
    },
    "metadata": {
        "last_updated": "2024-01-31T10:30:00Z",
        "completed_combinations": 6,
        "total_combinations": 6,
        "is_complete": true
    }
}
```

### Benefits of This Approach:
- ✅ **Backward Compatible**: Existing code continues to work
- ✅ **Single Source of Truth**: All dimensional data in one record
- ✅ **Efficient Storage**: No need for multiple database rows
- ✅ **Fast Retrieval**: Single query gets all dimensional data
- ✅ **Flexible Schema**: Can evolve without database migrations
- ✅ **Version Control**: Schema versioning allows future enhancements

### Project Structure - Separated New Implementation

```
app/
├── routes/
│   ├── user.py                          # EXISTING - DO NOT MODIFY
│   └── user_v2/                         # NEW FOLDER - All new implementation
│       ├── __init__.py                  # Blueprint registration
│       ├── dashboard.py                 # New dashboard routes
│       ├── data_collection_api.py       # Data collection endpoints
│       ├── entity_api.py                # Entity management endpoints
│       ├── computation_api.py           # Computation details endpoints
│       ├── preferences_api.py           # User preferences endpoints
│       └── feedback_api.py              # Feedback collection endpoints
│
├── services/
│   ├── user_v2/                         # NEW FOLDER - Business logic
│       ├── __init__.py
│       ├── dimensional_data_service.py  # Dimensional data processing
│       ├── entity_service.py            # Entity management logic
│       ├── computation_service.py       # Computation calculations
│       ├── aggregation_service.py       # Total calculations
│       ├── validation_service.py        # Data validation
│       └── historical_data_service.py   # Historical data queries
│
├── static/
│   ├── css/user_v2/                     # NEW FOLDER - Styles
│   │   ├── dashboard.css                # New dashboard styles
│   │   ├── data_collection_modal.css    # Modal styles
│   │   ├── entity_switcher.css          # Entity selection styles
│   │   ├── computation_context.css      # Computation tooltip styles
│   │   └── dimensional_grid.css         # Dimension matrix styles
│   │
│   └── js/user_v2/                      # NEW FOLDER - JavaScript
│       ├── dashboard.js                 # New dashboard controller
│       ├── data_collection_modal.js     # Modal logic
│       ├── dimensional_data_handler.js  # Dimension input handling
│       ├── entity_manager.js            # Entity switching logic
│       ├── computation_tooltips.js      # Computation display
│       ├── api_client.js                # API communication layer
│       └── utils.js                     # Utility functions
│
├── templates/
│   ├── user/                            # EXISTING - DO NOT MODIFY
│   │   └── dashboard.html               # Current dashboard
│   │
│   └── user_v2/                         # NEW FOLDER - Templates
│       ├── dashboard.html               # New dashboard template
│       ├── modals/
│       │   ├── data_collection.html    # Main collection modal
│       │   ├── computation_details.html # Computation info modal
│       │   └── feedback.html            # Feedback modal
│       └── components/
│           ├── entity_switcher.html     # Entity selector
│           ├── dimensional_grid.html    # Dimension input grid
│           └── progress_tracker.html    # Progress component
│
└── models/
    └── user_feedback.py                 # NEW MODEL for feedback
```

### Backend Route Separation Strategy

```python
# app/__init__.py - Modified to register new blueprint conditionally
def create_app():
    # ... existing code ...

    # Register existing user routes
    from app.routes.user import user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    # Register new v2 routes (parallel implementation)
    from app.routes.user_v2 import user_v2_bp
    app.register_blueprint(user_v2_bp, url_prefix='/user/v2')

    # ... rest of initialization ...
```

```python
# app/routes/user_v2/__init__.py - New blueprint initialization
from flask import Blueprint

user_v2_bp = Blueprint('user_v2', __name__)

# Import all route modules
from . import dashboard
from . import data_collection_api
from . import entity_api
from . import computation_api
from . import preferences_api
from . import feedback_api
```

```python
# app/routes/user_v2/dashboard.py - New dashboard route
from flask import render_template, request, current_app
from flask_login import login_required, current_user
from . import user_v2_bp

@user_v2_bp.route('/dashboard')
@login_required
def dashboard():
    """New dashboard with modal-based data entry."""
    # Check if user has opted into new interface
    if not current_user.use_new_data_entry:
        # Redirect to old dashboard if not opted in
        return redirect(url_for('user.dashboard'))

    # New dashboard logic here
    return render_template('user_v2/dashboard.html', ...)
```

## Implementation Phases

### Phase 0: Parallel Implementation Setup (Week 1)

#### 0.1 Feature Toggle Infrastructure
- Add `use_new_data_entry` preference to User model
- Create user preference API endpoint `/api/user/preferences`
- Implement toggle switch in dashboard header
- Store preference in session and database

#### 0.2 Dual Interface Support
- Keep existing inline editing completely functional
- Add conditional rendering based on user preference
- Create A/B testing framework for metrics collection
- Implement fallback mechanism for any failures

#### 0.3 Feedback Collection System
- Add feedback widget to new interface
- Create feedback API endpoint `/api/user/feedback`
- Implement feedback storage and categorization
- Set up feedback dashboard for admins

#### 0.4 Usage Analytics Setup
- Track interface selection metrics
- Monitor time spent on each interface
- Log completion rates for both interfaces
- Create comparative analytics dashboard

```python
# User model enhancement
class User(db.Model):
    # ... existing fields ...
    use_new_data_entry = db.Column(db.Boolean, default=False)
    interface_feedback = db.relationship('UserFeedback', backref='user')

# New feedback model
class UserFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    interface_version = db.Column(db.String(20))  # 'legacy' or 'modal'
    feedback_type = db.Column(db.String(50))  # 'bug', 'suggestion', 'praise'
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
```

#### UI Toggle Component
```html
<!-- Dashboard header toggle -->
<div class="interface-toggle">
    <label class="switch">
        <input type="checkbox" id="newInterfaceToggle"
               {% if current_user.use_new_data_entry %}checked{% endif %}>
        <span class="slider"></span>
    </label>
    <span>Try New Interface (Beta)</span>
    <button class="btn-feedback" onclick="openFeedbackModal()">
        <i class="fas fa-comment"></i> Feedback
    </button>
</div>
```

#### 0.5 Monitoring & Rollback Strategy
- Set up real-time error monitoring for new interface
- Create automated alerts for critical failures
- Implement instant rollback mechanism per user
- Track performance metrics (load times, response times)
- Create comparison dashboard for old vs new metrics

#### 0.6 Feature Flags Configuration
```python
# config.py enhancement
class Config:
    # Feature flags
    FEATURE_NEW_DATA_ENTRY_ENABLED = True  # Global kill switch
    FEATURE_NEW_DATA_ENTRY_DEFAULT = False  # Default for new users
    FEATURE_NEW_DATA_ENTRY_PERCENTAGE = 10  # Gradual rollout percentage

    # A/B testing configuration
    AB_TEST_ENABLED = True
    AB_TEST_SAMPLE_SIZE = 100  # Minimum users per variant
```

#### 0.7 URL Routing Strategy

**Access Patterns:**
- Old Interface: `/user/dashboard` (existing)
- New Interface: `/user/v2/dashboard` (new)
- Toggle switches between URLs, not templates

```python
# app/routes/user.py - Modified to handle toggle
@user_bp.route('/dashboard')
def dashboard():
    """Existing dashboard - check if user prefers new interface."""
    if current_app.config['FEATURE_NEW_DATA_ENTRY_ENABLED'] and current_user.use_new_data_entry:
        # Redirect to new dashboard
        return redirect(url_for('user_v2.dashboard'))

    # Continue with existing dashboard
    return render_template('user/dashboard.html', ...)

# app/routes/user_v2/preferences_api.py - Toggle endpoint
@user_v2_bp.route('/api/toggle-interface', methods=['POST'])
@login_required
def toggle_interface():
    """Toggle between old and new interface."""
    new_preference = request.json.get('useNewInterface')
    current_user.use_new_data_entry = new_preference
    db.session.commit()

    # Log the switch for analytics
    log_interface_switch(current_user.id, new_preference)

    # Return appropriate redirect URL
    if new_preference:
        redirect_url = url_for('user_v2.dashboard')
    else:
        redirect_url = url_for('user.dashboard')

    return jsonify({
        'success': True,
        'redirect': redirect_url
    })
```

**JavaScript for Toggle:**
```javascript
// app/static/js/user_v2/utils.js
function toggleInterface(useNew) {
    fetch('/user/v2/api/toggle-interface', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({useNewInterface: useNew})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.redirect;
        }
    });
}
```

### Phase 1: Core Modal Infrastructure (Week 2-3)

#### 1.1 Backend API Development
- Create `/api/user/data-collection` endpoint
- Add `/api/user/entities` for entity listing
- Implement `/api/user/field-details/{field_id}` for field metadata
- Add `/api/user/historical-data/{field_id}` for history

#### 1.2 Modal Dialog Implementation
- Create responsive modal component
- Implement tabbed interface (Current Entry | Historical Data | Computation Details)
- Add file upload area with drag-and-drop
- Include save/cancel with confirmation

#### 1.3 Entity Display & Switching
- Add entity name to page header
- Create entity switcher dropdown
- Store selected entity in session
- Update all queries to use selected entity

### Phase 2: Dimensional Data Support (Week 3-4)

#### 2.1 Dimensional Input Fields
- Generate input grid based on field dimensions
- Create dimension combination matrix
- Implement real-time total calculation
- Add validation for dimension values

#### 2.2 Data Storage Enhancement
- Extend ESGData model for dimensional storage
- Create aggregation service for totals
- Implement dimension-aware queries
- Add validation for completeness

#### 2.3 UI Enhancements
- Color-code dimension groups
- Add expand/collapse for dimension sections
- Implement smart defaults based on patterns
- Add copy from previous period feature

### Phase 3: Computation Context (Week 4-5)

#### 3.1 Formula Display System
- Parse and display formulas clearly
- Show dependency tree visualization
- Highlight current values in formula
- Add step-by-step calculation display

#### 3.2 Contextual Help Modals
- Create floating tooltip system
- Implement info icons for computed fields
- Add calculation history view
- Show impact analysis for changes

#### 3.3 Historical Data Integration
- Display time series for each field
- Show comparison with previous periods
- Add trend indicators
- Implement data quality scores

### Phase 4: Advanced Features (Week 5-6)

#### 4.1 Smart Data Entry
- Auto-save draft functionality
- Keyboard shortcuts for navigation
- Bulk paste from Excel
- Smart number formatting

#### 4.2 Validation & Quality
- Real-time validation feedback
- Cross-field dependency checks
- Completeness indicators
- Data quality warnings

#### 4.3 Performance Optimization
- Lazy loading for historical data
- Client-side caching
- Optimized dimension queries
- Batch save operations

### Phase 5: OCR Integration (Future Enhancement)

#### 5.1 Document Upload Enhancement
- Support PDF, JPG, PNG formats
- Create document preview interface
- Implement document storage service
- Add document versioning

#### 5.2 OCR Processing (Phase 2)
- Integrate OCR service (Tesseract/Cloud service)
- Create extraction review interface
- Map extracted values to fields
- Add confidence scoring

## UI/UX Mockup Descriptions

### 1. Main Dashboard View
```
┌─────────────────────────────────────────────────────────────┐
│ 🏢 Test Company Alpha > Facility Alpha-1 > Dashboard    [↓] │
├─────────────────────────────────────────────────────────────┤
│ Selected Date: January 2024  [Select Date] [Upload CSV]      │
├─────────────────────────────────────────────────────────────┤
│ Progress: 45/100 fields complete (45%)  ████░░░░░░          │
├─────────────────────────────────────────────────────────────┤
│ Field Name          | Status    | Value      | Actions       │
│ Employee Count      | Complete  | 500        | [Edit] [ℹ]    │
│ Energy Usage (calc) | Computed  | 1,234 kWh  | [View] [ℹ]    │
│ Gender Distribution | Partial   | 3/6 dims   | [Edit] [ℹ]    │
└─────────────────────────────────────────────────────────────┘
```

### 2. Data Collection Modal
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Enter Data: Employee Count - Facility Alpha-1        [X] │
├─────────────────────────────────────────────────────────────┤
│ [Current Entry] [Historical Data] [Field Info]              │
├─────────────────────────────────────────────────────────────┤
│ Reporting Period: January 2024                              │
│                                                              │
│ ▼ Dimensional Breakdown                                     │
│ ┌─────────────────────────────────────────────────────┐    │
│ │         Gender →  │  Male  │ Female │ Other │ Total │    │
│ │ Age ↓            │        │        │       │       │    │
│ ├──────────────────┼────────┼────────┼───────┼───────┤    │
│ │ < 30            │ [ 50 ] │ [ 45 ] │ [ 5 ] │  100  │    │
│ │ 30-50           │ [ 120] │ [ 100] │ [ 10] │  230  │    │
│ │ > 50            │ [ 80 ] │ [ 70 ] │ [ 20] │  170  │    │
│ ├──────────────────┼────────┼────────┼───────┼───────┤    │
│ │ Total           │  250   │  215   │  35   │  500  │    │
│ └─────────────────────────────────────────────────────┘    │
│                                                              │
│ 📎 Supporting Documents                                      │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ Drop files here or click to browse                   │    │
│ │ Accepted: PDF, JPG, PNG, XLSX (max 20MB)            │    │
│ └─────────────────────────────────────────────────────┘    │
│                                                              │
│ Notes: [                                               ]    │
│                                                              │
│ [Save Draft] [Cancel]                    [Submit Data]      │
└─────────────────────────────────────────────────────────────┘
```

### 3. Computation Context Modal
```
┌─────────────────────────────────────────────────────────────┐
│ 🧮 Calculation Details: Total Energy Consumption        [X] │
├─────────────────────────────────────────────────────────────┤
│ Formula:                                                     │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ Electricity_Usage + Gas_Usage * 0.293 + Other_Energy│    │
│ └─────────────────────────────────────────────────────┘    │
│                                                              │
│ Current Values:                                              │
│ • Electricity_Usage = 850 kWh ✓                             │
│ • Gas_Usage = 1,300 therms ✓                               │
│ • Other_Energy = 0 kWh (no data)                           │
│                                                              │
│ Calculation:                                                 │
│ = 850 + (1,300 × 0.293) + 0                                │
│ = 850 + 380.9 + 0                                          │
│ = 1,230.9 kWh                                              │
│                                                              │
│ Historical Trend:                                            │
│ ┌─────────────────────────────────────────────────────┐    │
│ │     📈 [Line chart showing 12-month trend]          │    │
│ └─────────────────────────────────────────────────────┘    │
│                                                              │
│                                              [Close]        │
└─────────────────────────────────────────────────────────────┘
```

## Backend Services Implementation

### Service Layer Architecture

```python
# app/services/user_v2/dimensional_data_service.py
class DimensionalDataService:
    """Service for handling dimensional data operations."""

    @staticmethod
    def prepare_dimension_matrix(field_id, entity_id):
        """Generate empty dimension matrix for a field."""
        field = FrameworkDataField.query.get(field_id)
        dimensions = FieldDimension.query.filter_by(field_id=field_id).all()

        # Generate all combinations
        dimension_values = {}
        for dim in dimensions:
            dimension_values[dim.dimension.name] = [
                v.value for v in dim.dimension.get_ordered_values()
            ]

        # Create matrix structure
        return generate_combinations(dimension_values)

    @staticmethod
    def calculate_totals(dimensional_data):
        """Calculate totals across all dimensions."""
        overall_total = sum(d['raw_value'] for d in dimensional_data if d['raw_value'])

        # Calculate per-dimension totals
        by_dimension = {}
        for dim_name in get_dimension_names(dimensional_data):
            by_dimension[dim_name] = calculate_dimension_totals(dimensional_data, dim_name)

        return {
            'overall': overall_total,
            'by_dimension': by_dimension
        }

    @staticmethod
    def validate_dimensional_data(field_id, dimensional_data):
        """Validate dimensional data completeness and accuracy."""
        # Check all required combinations are present
        # Validate value types and ranges
        # Ensure totals match
        pass

# app/services/user_v2/aggregation_service.py
class AggregationService:
    """Service for data aggregation and calculations."""

    @staticmethod
    def aggregate_by_dimension(esg_data_list, dimension_name):
        """Aggregate data by specific dimension."""
        aggregated = {}
        for data in esg_data_list:
            if data.dimension_values:
                dim_data = json.loads(data.dimension_values)
                for breakdown in dim_data.get('breakdowns', []):
                    dim_value = breakdown['dimensions'].get(dimension_name)
                    if dim_value:
                        aggregated[dim_value] = aggregated.get(dim_value, 0) + breakdown['raw_value']
        return aggregated

    @staticmethod
    def calculate_cross_entity_totals(field_id, entities, reporting_date):
        """Calculate totals across multiple entities."""
        total = 0
        for entity in entities:
            data = ESGData.query.filter_by(
                field_id=field_id,
                entity_id=entity.id,
                reporting_date=reporting_date
            ).first()
            if data and data.raw_value:
                total += float(data.raw_value)
        return total

# app/services/user_v2/validation_service.py
class ValidationService:
    """Service for data validation."""

    @staticmethod
    def validate_dimension_combination(field_id, dimensions):
        """Validate that dimension combination is valid for field."""
        field_dimensions = FieldDimension.query.filter_by(field_id=field_id).all()

        # Check all required dimensions are present
        for fd in field_dimensions:
            if fd.is_required and fd.dimension.name not in dimensions:
                return False, f"Missing required dimension: {fd.dimension.name}"

        # Validate dimension values
        for dim_name, dim_value in dimensions.items():
            if not validate_dimension_value(dim_name, dim_value):
                return False, f"Invalid value for dimension {dim_name}: {dim_value}"

        return True, None
```

## API Endpoints Design

### 1. Data Collection Endpoints

```python
# Get field details with dimensions
GET /api/user/field-details/{field_id}
Response: {
    "field_id": "123",
    "field_name": "Employee Count",
    "type": "raw_input",
    "dimensions": [
        {
            "dimension_id": "gender",
            "name": "Gender",
            "values": ["Male", "Female", "Other"]
        },
        {
            "dimension_id": "age",
            "name": "Age Group",
            "values": ["<30", "30-50", ">50"]
        }
    ],
    "validation_rules": {...}
}

# Submit dimensional data
POST /api/user/submit-dimensional-data
Body: {
    "field_id": "123",
    "entity_id": 1,
    "reporting_date": "2024-01-31",
    "dimensional_data": [
        {"dimensions": {"gender": "Male", "age": "<30"}, "value": 50},
        {"dimensions": {"gender": "Male", "age": "30-50"}, "value": 120},
        // ... other combinations
    ],
    "total": 500,
    "attachments": ["file_id_1", "file_id_2"],
    "notes": "January headcount data"
}

# Get historical data
GET /api/user/historical-data/{field_id}?entity_id=1&months=12
Response: {
    "data": [
        {
            "date": "2024-01-31",
            "value": 500,
            "dimensional_breakdown": [...],
            "status": "submitted"
        },
        // ... previous months
    ]
}
```

### 2. Entity Management Endpoints

```python
# Get user's accessible entities
GET /api/user/entities
Response: {
    "entities": [
        {"id": 1, "name": "Facility Alpha-1", "type": "facility"},
        {"id": 2, "name": "Facility Alpha-2", "type": "facility"}
    ],
    "current_entity_id": 1
}

# Switch entity context
POST /api/user/switch-entity
Body: {"entity_id": 2}
```

### 3. Computation Endpoints

```python
# Get computation details
GET /api/user/computation-details/{field_id}
Response: {
    "formula": "Electricity_Usage + Gas_Usage * 0.293",
    "dependencies": [
        {"field_id": "456", "name": "Electricity_Usage", "current_value": 850},
        {"field_id": "789", "name": "Gas_Usage", "current_value": 1300}
    ],
    "calculation_steps": [...],
    "result": 1230.9
}
```

## Migration Strategy

### Phase 1: Parallel Implementation
- Keep existing inline editing functional
- Add "Try New Interface" toggle
- Collect user feedback
- Monitor usage patterns

### Phase 2: Gradual Rollout
- Make modal default for new users
- Migrate power users first
- Provide training materials
- Keep fallback option

### Phase 3: Full Migration
- Deprecate inline editing
- Remove old code
- Optimize for modal-only flow
- Archive legacy interfaces

## Success Metrics

### Functionality Metrics
- ✓ All dimensional combinations can be entered
- ✓ Totals calculate correctly
- ✓ Entity switching works seamlessly
- ✓ Historical data displays properly
- ✓ Computed fields show formulas clearly

### Performance Metrics
- Modal load time < 500ms
- Data save time < 2s
- Dimension calculation < 100ms
- Entity switch < 1s

### User Experience Metrics
- Reduced data entry time by 30%
- Decreased error rate by 50%
- Improved completion rate to 90%
- User satisfaction score > 4.5/5

## Risk Mitigation

### Technical Risks
- **Risk**: Performance with large dimension matrices
  - **Mitigation**: Implement pagination, lazy loading

- **Risk**: Data consistency across dimensions
  - **Mitigation**: Transaction-based saves, validation

### User Adoption Risks
- **Risk**: Learning curve for new interface
  - **Mitigation**: Interactive tutorials, gradual rollout

- **Risk**: Resistance to change
  - **Mitigation**: Keep old interface available initially

## Dependencies

### Required Before Implementation
- Assignment system must be operational
- Company FY configuration working
- Dimension models properly configured
- User entity relationships established

### External Dependencies
- File storage service for attachments
- OCR service selection (future)
- Browser compatibility testing
- Performance monitoring tools

## Future Enhancements

### 1. Advanced Dimensional Data Storage (Post-MVP)

When reporting and querying requirements become more complex, consider migrating to a separate dimensional table structure:

```python
# Future: Separate dimensional data table for advanced querying
class DimensionalESGData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_esg_data_id = db.Column(db.Integer, db.ForeignKey('esg_data.id'))
    dimension_combination = db.Column(db.JSON)
    raw_value = db.Column(db.Float)
    calculated_value = db.Column(db.Float)
    is_total = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)

    # This would enable:
    # - Complex SQL queries across dimensions
    # - Better performance for large datasets
    # - Granular audit trails
    # - Partial updates to specific dimensions
```

### 2. OCR Integration (Phase 5)
- Document text extraction
- Auto-population of fields
- Confidence scoring
- Manual review interface

### 3. Advanced Analytics
- Cross-entity dimensional comparisons
- Trend analysis across dimensions
- Predictive analytics for missing data
- Anomaly detection in dimensional patterns

### 4. AI-Assisted Data Entry
- Smart suggestions based on historical patterns
- Auto-completion for dimensional data
- Validation recommendations
- Data quality scoring

## Timeline Summary

- **Week 1**: Phase 0 - Parallel implementation setup & feature toggle
- **Week 2-3**: Phase 1 - Core modal infrastructure & entity management
- **Week 3-4**: Phase 2 - Dimensional data support (JSON storage)
- **Week 4-5**: Phase 3 - Computation context & historical data
- **Week 5-6**: Phase 4 - Advanced features & optimization
- **Week 6-7**: Testing, bug fixes, and gradual deployment
- **Future**: Additional enhancements based on user needs

## Next Steps

1. Review and approve this plan
2. Create detailed technical specifications
3. Set up development environment
4. Begin Phase 1 implementation
5. Schedule user testing sessions