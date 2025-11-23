# Phase 1: Core Modal Infrastructure - Requirements & Specifications

## Overview
Build the foundational modal dialog system and entity management for the new user dashboard interface.

## Requirements

### 1.1 Backend API Development
- [ ] Create `/api/user/v2/field-details/{field_id}` endpoint
  - Return field metadata, dimensions, validation rules
  - Include assignment information
- [ ] Create `/api/user/v2/entities` endpoint
  - List all entities accessible by current user
  - Include current entity selection
- [ ] Create `/api/user/v2/switch-entity` endpoint
  - Switch user's current entity context
  - Update session and database
- [ ] Create `/api/user/v2/historical-data/{field_id}` endpoint
  - Return historical submissions for a field
  - Support date range filtering

### 1.2 Modal Dialog Implementation
- [ ] Create responsive modal component
  - Mobile-first design
  - Accessibility compliance (ARIA labels, keyboard navigation)
- [ ] Implement tabbed interface
  - Tab 1: Current Entry (data input)
  - Tab 2: Historical Data (read-only)
  - Tab 3: Field Info (metadata)
- [ ] Add file upload area
  - Drag-and-drop support
  - Multiple file selection
  - File type validation
  - Preview thumbnails
- [ ] Save/Cancel with confirmation
  - Unsaved changes warning
  - Loading states during save

### 1.3 Entity Display & Switching
- [ ] Add entity name to page header/breadcrumb
- [ ] Create entity switcher dropdown component
  - Display accessible entities
  - Show current selection
  - Quick switch functionality
- [ ] Store selected entity in session
- [ ] Update all queries to use selected entity

### 1.4 Dashboard Data Loading
- [ ] Load assigned data points for selected entity
- [ ] Separate raw input fields from computed fields
- [ ] Display field status (empty/partial/complete)
- [ ] Show progress indicators
- [ ] Implement date selection integration

## Technical Specifications

### API Response Formats

#### Field Details
```json
{
  "field_id": "abc-123",
  "field_name": "Employee Count",
  "field_type": "raw_input",
  "data_type": "integer",
  "unit": "employees",
  "description": "Total number of employees",
  "dimensions": [
    {
      "dimension_id": "dim-1",
      "name": "Gender",
      "values": [
        {"value_id": "v1", "value": "Male", "display_name": "Male"},
        {"value_id": "v2", "value": "Female", "display_name": "Female"}
      ]
    }
  ],
  "validation_rules": {
    "required": true,
    "min_value": 0,
    "max_value": 1000000
  },
  "assignment": {
    "assignment_id": "assign-1",
    "frequency": "Monthly",
    "start_date": "2024-01-01"
  }
}
```

#### Entity List
```json
{
  "entities": [
    {
      "id": 1,
      "name": "Facility Alpha-1",
      "type": "facility",
      "is_current": true
    },
    {
      "id": 2,
      "name": "Facility Alpha-2",
      "type": "facility",
      "is_current": false
    }
  ],
  "current_entity_id": 1
}
```

#### Historical Data
```json
{
  "field_id": "abc-123",
  "entity_id": 1,
  "data": [
    {
      "id": 1,
      "reporting_date": "2024-01-31",
      "raw_value": 500,
      "dimension_values": {...},
      "status": "submitted",
      "created_at": "2024-02-01T10:00:00Z",
      "attachments": [...]
    }
  ]
}
```

### Modal Component Structure

```html
<!-- Data Collection Modal -->
<div class="modal-overlay" id="dataCollectionModal">
  <div class="modal-container">
    <div class="modal-header">
      <h2>Enter Data: [Field Name] - [Entity Name]</h2>
      <button class="modal-close">&times;</button>
    </div>

    <!-- Tab Navigation -->
    <div class="modal-tabs">
      <button class="tab active" data-tab="entry">Current Entry</button>
      <button class="tab" data-tab="history">Historical Data</button>
      <button class="tab" data-tab="info">Field Info</button>
    </div>

    <!-- Tab Content -->
    <div class="modal-body">
      <div class="tab-content active" id="entry-tab">
        <!-- Data input form -->
      </div>
      <div class="tab-content" id="history-tab">
        <!-- Historical data table -->
      </div>
      <div class="tab-content" id="info-tab">
        <!-- Field metadata -->
      </div>
    </div>

    <div class="modal-footer">
      <button class="btn-cancel">Cancel</button>
      <button class="btn-save-draft">Save Draft</button>
      <button class="btn-submit">Submit Data</button>
    </div>
  </div>
</div>
```

### Entity Switcher Component

```html
<!-- Entity Switcher in Header -->
<div class="entity-switcher">
  <label>Current Entity:</label>
  <select id="entitySelect" class="entity-dropdown">
    <option value="1" selected>Facility Alpha-1</option>
    <option value="2">Facility Alpha-2</option>
  </select>
</div>
```

### Service Layer

```python
# app/services/user_v2/entity_service.py
class EntityService:
    @staticmethod
    def get_user_entities(user_id):
        """Get all entities accessible by user."""
        user = User.query.get(user_id)
        if user.role == 'ADMIN':
            # Admins see all company entities
            return Entity.query.filter_by(company_id=user.company_id).all()
        else:
            # Users see only their assigned entity
            return [user.entity] if user.entity else []

    @staticmethod
    def switch_entity(user_id, entity_id):
        """Switch user's current entity."""
        # Validate access
        # Update session
        # Return new entity context
        pass

# app/services/user_v2/field_service.py
class FieldService:
    @staticmethod
    def get_field_details(field_id, entity_id):
        """Get comprehensive field details."""
        field = FrameworkDataField.query.get(field_id)
        dimensions = FieldDimension.query.filter_by(field_id=field_id).all()
        assignment = DataPointAssignment.query.filter_by(
            field_id=field_id,
            entity_id=entity_id
        ).first()

        return {
            'field': field,
            'dimensions': dimensions,
            'assignment': assignment
        }
```

## UI/UX Requirements

### Modal Design
- **Size**: 800px width on desktop, full-screen on mobile
- **Animation**: Fade in/slide up (300ms)
- **Backdrop**: Semi-transparent dark overlay
- **Z-index**: 1000 (above all other elements)
- **Keyboard**: ESC to close, Tab navigation

### Entity Switcher
- **Location**: Top-right of dashboard header
- **Style**: Dropdown select with icon
- **Behavior**: Auto-save on change, reload dashboard

### File Upload
- **Drag Zone**: 200px height, dashed border
- **Accepted**: PDF, JPG, PNG, XLSX, CSV
- **Max Size**: 20MB per file
- **Multiple**: Yes, up to 10 files

## Success Criteria
- ✓ Modal opens and closes smoothly
- ✓ All tabs function correctly
- ✓ File upload accepts valid formats
- ✓ Entity switching updates dashboard
- ✓ Historical data displays correctly
- ✓ API endpoints return proper data
- ✓ Mobile responsive (works on 320px+ screens)
- ✓ Accessibility: keyboard navigation works

## Implementation Tasks
1. Create entity service layer
2. Create field service layer
3. Implement API endpoints
4. Build modal HTML/CSS
5. Implement modal JavaScript logic
6. Create entity switcher component
7. Integrate with dashboard
8. Add file upload handling
9. Test all functionality
10. Fix bugs and polish UI
