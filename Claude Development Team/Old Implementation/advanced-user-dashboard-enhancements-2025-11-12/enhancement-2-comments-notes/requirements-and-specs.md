# Enhancement #2: Comments/Notes Functionality for Data Entries

**Date Created:** 2025-11-12
**Status:** Planning Complete - Ready for Implementation
**Priority:** High
**Complexity:** Low-Medium

---

## Problem Statement

### Current Behavior
Users can enter data values but have no way to add explanatory notes or comments to provide context about:
- Why a value is unusual or different from expected
- Data source or methodology used
- Known data quality issues
- Clarifications for reviewers/admins
- Justifications for variance analysis

### Expected Behavior
Users should be able to add optional notes/comments when entering data that:
- ✅ Are saved with the ESGData entry
- ✅ Are visible to all users who can access that data (entity-level visibility)
- ✅ Appear in historical data views
- ✅ Are included in data exports
- ✅ Work for both raw input and computed fields
- ✅ Support dimensional data (notes per dimension combination)

### Business Value
- **Audit Trail:** Provides context for auditors and reviewers
- **Data Quality:** Helps explain anomalies and variances
- **Collaboration:** Enables communication between data entry users and admins
- **Transparency:** Documents methodology and assumptions
- **Compliance:** Meets regulatory requirements for data justification

---

## Solution Design

### Approach: Simple Notes Field (MVP)

**Core Principle:** Add a single `notes` text field to ESGData model and expose it in the data entry modal.

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│          ESGData Model Enhancement              │
├─────────────────────────────────────────────────┤
│ • Add `notes` column (TEXT, nullable)           │
│ • Indexed for search performance                │
│ • Visible to all users with ESGData access      │
│ • Inherits tenant isolation automatically       │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│          Data Entry UI Enhancement              │
├─────────────────────────────────────────────────┤
│ • Add Notes/Comments textarea in modal          │
│ • Character limit: 1000 characters              │
│ • Live character counter                        │
│ • Optional field (not required)                 │
│ • Works for raw input and computed fields       │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│          Display & Export Enhancement           │
├─────────────────────────────────────────────────┤
│ • Show notes in historical data tab             │
│ • Include notes in CSV/Excel exports            │
│ • Display notes in computed field view          │
│ • Show notes indicator on field cards           │
└─────────────────────────────────────────────────┘
```

### Data Model Changes

**ESGData Model:** Add `notes` column
```python
notes = db.Column(db.Text, nullable=True)  # Up to 65,535 characters
```

**Visibility Rules:**
- Notes visibility = ESGData visibility
- All users assigned to the same entity can see notes
- Admins can see notes for all entities they manage
- SUPER_ADMIN can see all notes (through impersonation)
- No separate permissions needed (inherits from ESGData)

---

## Visual Mockups

### Raw Input Field - Data Entry Modal with Notes

```
┌───────────────────────────────────────────────────────────────┐
│ Enter Data: Male Employees                       [Auto-save] [×]│
├───────────────────────────────────────────────────────────────┤
│ [Current Entry] [Historical Data] [Field Info]                │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ Smart Date Selector:                                          │
│ [Jan 2025 ▼] [Feb 2025] [Mar 2025] ... [Dec 2025]            │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Value                                                   │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ 85                                                  │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📝 Notes / Comments (Optional)                          │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ Includes 5 new hires from acquisition of Company   │ │ │
│ │ │ XYZ on Jan 15, 2025. Previous month variance of   │ │ │
│ │ │ +6.2% is explained by this one-time event.        │ │ │
│ │ │                                                     │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ │ <span class="char-counter">142 / 1000 characters</span>│ │
│ │                                                         │ │
│ │ <small class="help-text">                              │ │
│ │   💡 Add context about unusual values, data sources,  │ │
│ │   methodology, or any clarifications for reviewers    │ │
│ │ </small>                                               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ File Attachments                                        │ │
│ │ [Upload area...]                                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│                                              [Cancel] [Save Data]│
└───────────────────────────────────────────────────────────────┘
```

---

### Computed Field - View with Notes

```
┌───────────────────────────────────────────────────────────────┐
│ View Computed Field: Total Employees              [Auto-save] [×]│
├───────────────────────────────────────────────────────────────┤
│ [Calculation & Dependencies] [Historical] [Info]              │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ 📊 Computed Result                                            │
│    150 employees                          [✓ Complete]       │
│    Last calculated: 2025-01-12 10:30 AM                      │
│                                                               │
│ 📐 Calculation Formula                                        │
│    Male Employees + Female Employees                          │
│                                                               │
│ 🔗 Dependencies                                               │
│ ┌─────────┬──────────────────┬───────┬────────┬────────────┐│
│ │Variable │ Field Name       │ Value │ Status │ Action     ││
│ ├─────────┼──────────────────┼───────┼────────┼────────────┤│
│ │   A     │ Male Employees   │ 85    │   ✓    │[📝 Edit]   ││
│ │         │ 💬 "Includes 5 new hires..."        │View Notes ││
│ │   B     │Female Employees  │ 65    │   ✓    │[📝 Edit]   ││
│ └─────────┴──────────────────┴───────┴────────┴────────────┘│
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📝 Notes for This Calculation (Optional)                │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ Total headcount is higher than Q4 2024 due to      │ │ │
│ │ │ acquisition. Growth is expected to stabilize.      │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ │ 87 / 1000 characters                                    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│                                                  [Close] [Save]│
└───────────────────────────────────────────────────────────────┘
```

---

### Historical Data Tab with Notes

```
┌───────────────────────────────────────────────────────────────┐
│ Enter Data: Male Employees                              [×]  │
├───────────────────────────────────────────────────────────────┤
│ [Current Entry] [Historical Data] [Field Info]                │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ Historical Submissions (Showing 10 of 24)     [CSV] [Excel]  │
│                                                               │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ Reporting Date │ Value │ Notes               │ Submitted  ││
│ ├────────────────┼───────┼─────────────────────┼────────────┤│
│ │ 2025-01-31     │  85   │ 💬 Includes 5 new..│ 2 days ago ││
│ │ 2024-12-31     │  80   │ 💬 End of year...  │ 1 month ago││
│ │ 2024-11-30     │  78   │ -                  │ 2 months   ││
│ │ 2024-10-31     │  79   │ 💬 One termination │ 3 months   ││
│ └────────────────┴───────┴─────────────────────┴────────────┘│
│                                                               │
│ Click on 💬 icon or note text to view full note              │
│                                                               │
│                                         [Load More ↓]         │
└───────────────────────────────────────────────────────────────┘
```

---

### Dimensional Data with Notes

For dimensional data, each dimension combination can have its own notes:

```
┌───────────────────────────────────────────────────────────────┐
│ Enter Data: Employees by Gender and Age                 [×]  │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ Dimensional Data Entry (Gender × Age)                        │
│                                                               │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ Gender │ Age    │ Value │ Notes                           ││
│ ├────────┼────────┼───────┼─────────────────────────────────┤│
│ │ Male   │ <30    │  25   │ ┌────────────────────────────┐ ││
│ │        │        │       │ │ High turnover in this      │ ││
│ │        │        │       │ │ segment noted              │ ││
│ │        │        │       │ └────────────────────────────┘ ││
│ │ Male   │ 30-50  │  45   │ [Add notes...]                 ││
│ │ Male   │ >50    │  15   │ [Add notes...]                 ││
│ │ Female │ <30    │  22   │ [Add notes...]                 ││
│ │ Female │ 30-50  │  30   │ [Add notes...]                 ││
│ │ Female │ >50    │  13   │ [Add notes...]                 ││
│ ├────────┴────────┼───────┼─────────────────────────────────┤│
│ │ TOTAL          │  150  │ [Overall notes...]             ││
│ └────────────────┴───────┴─────────────────────────────────┘│
│                                                               │
│                                              [Cancel] [Save]  │
└───────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Database Schema Changes

#### 1.1 Update ESGData Model
**File:** `app/models/esg_data.py`

**Add column:**
```python
# After line 27 (unit column)
# Phase 2 Enhancement: Notes/Comments for data context
notes = db.Column(db.Text, nullable=True)  # Supports up to 65,535 characters
```

**Update `__init__` method:**
```python
# Line 72-81: Update constructor
def __init__(self, entity_id, field_id, raw_value, reporting_date, company_id=None,
             calculated_value=None, unit=None, dimension_values=None, assignment_id=None, notes=None):
    self.entity_id = entity_id
    self.field_id = field_id
    self.company_id = company_id
    self.assignment_id = assignment_id
    self.raw_value = raw_value
    self.calculated_value = calculated_value
    self.reporting_date = reporting_date
    self.dimension_values = dimension_values or {}
    self.unit = unit
    self.notes = notes  # NEW
```

**Add helper methods:**
```python
# Add after line 137 (after matches_dimension_filter method)

def has_notes(self):
    """Check if this data entry has notes.

    Returns:
        bool: True if notes exist and are not empty
    """
    return bool(self.notes and self.notes.strip())

def get_notes_preview(self, max_length=50):
    """Get a preview of notes (first N characters).

    Args:
        max_length (int): Maximum length of preview

    Returns:
        str: Preview of notes with ellipsis if truncated
    """
    if not self.has_notes():
        return ""

    notes_text = self.notes.strip()
    if len(notes_text) <= max_length:
        return notes_text

    return notes_text[:max_length] + "..."
```

#### 1.2 Database Migration

**Create migration script:** `app/utils/add_notes_column.py`

```python
"""
Migration script to add notes column to esg_data table.
Run this script to update existing database.
"""

from app import create_app
from app.extensions import db
from sqlalchemy import text

def migrate_add_notes_column():
    """Add notes column to esg_data table."""

    app = create_app()
    with app.app_context():
        try:
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('esg_data')]

            if 'notes' in columns:
                print("✅ Column 'notes' already exists in esg_data table")
                return

            # Add notes column
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE esg_data
                    ADD COLUMN notes TEXT NULL
                """))
                conn.commit()

            print("✅ Successfully added 'notes' column to esg_data table")

        except Exception as e:
            print(f"❌ Error adding notes column: {str(e)}")
            raise

if __name__ == '__main__':
    migrate_add_notes_column()
```

**Run migration:**
```bash
python3 app/utils/add_notes_column.py
```

---

### Phase 2: Frontend UI Changes

#### 2.1 Add Notes Field to Data Entry Modal
**File:** `app/templates/user_v2/dashboard.html`

**Location:** After the value input field (around line 464, before file attachments)

```html
<!-- Add after dataValue input, before file attachments section -->

<!-- Notes/Comments Section -->
<div class="mb-3" id="notesSection">
    <label for="fieldNotes" class="form-label">
        <span class="material-icons text-sm align-middle">comment</span>
        Notes / Comments <span class="text-muted">(Optional)</span>
    </label>
    <textarea
        class="form-control"
        id="fieldNotes"
        rows="4"
        maxlength="1000"
        placeholder="Add context about unusual values, data sources, methodology, or clarifications for reviewers..."
    ></textarea>
    <div class="d-flex justify-content-between align-items-center mt-1">
        <small class="form-text text-muted">
            <span class="material-icons text-xs align-middle">info</span>
            Provide context to help reviewers understand this data entry
        </small>
        <small class="char-counter text-muted">
            <span id="notesCharCount">0</span> / 1000 characters
        </small>
    </div>
</div>
```

**Add character counter JavaScript:**

```javascript
// Add in Phase 4 section (around line 1630)

// Notes character counter
document.addEventListener('DOMContentLoaded', function() {
    const notesField = document.getElementById('fieldNotes');
    const charCount = document.getElementById('notesCharCount');

    if (notesField && charCount) {
        notesField.addEventListener('input', function() {
            const length = this.value.length;
            charCount.textContent = length;

            // Change color when approaching limit
            if (length > 900) {
                charCount.classList.add('text-danger');
            } else if (length > 750) {
                charCount.classList.add('text-warning');
                charCount.classList.remove('text-danger');
            } else {
                charCount.classList.remove('text-warning', 'text-danger');
            }
        });
    }
});
```

**Add CSS styling:**

```css
/* Add to the <style> section in dashboard.html */

/* Notes section styling */
#notesSection {
    background: #f8fafc;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #e2e8f0;
}

#notesSection label {
    font-weight: 600;
    color: #1e293b;
    display: flex;
    align-items: center;
    gap: 0.375rem;
}

#fieldNotes {
    resize: vertical;
    min-height: 80px;
    font-size: 0.875rem;
    line-height: 1.5;
}

#fieldNotes:focus {
    border-color: #3f6212;
    box-shadow: 0 0 0 3px rgba(63, 98, 18, 0.1);
}

.char-counter {
    font-size: 0.75rem;
    font-weight: 500;
}

/* Dark mode */
.dark #notesSection {
    background: #1e293b;
    border-color: #475569;
}

.dark #notesSection label {
    color: #e2e8f0;
}

.dark #fieldNotes {
    background: #0f172a;
    border-color: #334155;
    color: #e2e8f0;
}
```

#### 2.2 Update Modal Opening Logic to Load Existing Notes

**File:** `app/templates/user_v2/dashboard.html` (around line 1466)

**Add note loading when modal opens:**

```javascript
// In the .open-data-modal click handler
document.querySelectorAll('.open-data-modal').forEach(button => {
    button.addEventListener('click', async function() {
        const fieldId = this.dataset.fieldId;
        const fieldName = this.dataset.fieldName;
        const fieldType = this.dataset.fieldType;
        const entityId = {{ current_entity.id if current_entity else 'null' }};
        const reportingDate = document.getElementById('selectedDate')?.value || new Date().toISOString().split('T')[0];

        // ... existing modal setup code ...

        // Load existing notes if data exists
        await loadExistingNotes(fieldId, entityId, reportingDate);

        modal.show();
    });
});

// Add new function to load existing notes
async function loadExistingNotes(fieldId, entityId, reportingDate) {
    try {
        const response = await fetch(
            `/api/user/v2/field-data/${fieldId}?entity_id=${entityId}&reporting_date=${reportingDate}`
        );

        if (response.ok) {
            const data = await response.json();
            const notesField = document.getElementById('fieldNotes');

            if (data.success && data.notes && notesField) {
                notesField.value = data.notes;
                // Trigger character counter update
                const event = new Event('input');
                notesField.dispatchEvent(event);
            }
        }
    } catch (error) {
        console.error('Error loading existing notes:', error);
    }
}
```

#### 2.3 Update Submit Logic to Include Notes

**File:** `app/templates/user_v2/dashboard.html` (around line 1540)

**Update submit-simple-data call:**

```javascript
// In submitDataBtn click handler (line ~1540)
const response = await fetch('/user/v2/api/submit-simple-data', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        field_id: fieldId,
        entity_id: entityId,
        reporting_date: reportingDate,
        raw_value: dataValue,
        notes: document.getElementById('fieldNotes')?.value || null  // ADD THIS
    })
});
```

---

### Phase 3: Backend API Changes

#### 3.1 Update Submit Simple Data API
**File:** `app/routes/user_v2/dimensional_data_api.py`

**Update submit_simple_data function (line 61-142):**

```python
@user_v2_bp.route('/api/submit-simple-data', methods=['POST'])
@login_required
@tenant_required_for('USER')
def submit_simple_data():
    """
    Submit simple (non-dimensional) data for a field.

    Request Body:
        {
            "field_id": "field-uuid",
            "entity_id": 1,
            "reporting_date": "2024-01-31",
            "raw_value": "100",
            "notes": "Optional notes",  # NOW SUPPORTED
            "attachments": []
        }

    Returns:
        JSON with success status
    """
    try:
        data = request.get_json()

        # Validate required fields
        field_id = data.get('field_id')
        entity_id = data.get('entity_id')
        reporting_date = data.get('reporting_date')
        raw_value = data.get('raw_value')
        notes = data.get('notes')  # ADD THIS

        if not all([field_id, entity_id, reporting_date]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: field_id, entity_id, reporting_date'
            }), 400

        # Convert reporting_date string to date object
        reporting_date_obj = datetime.strptime(reporting_date, '%Y-%m-%d').date()

        # Find or create ESGData entry
        esg_data = ESGData.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date_obj,
            company_id=current_user.company_id,
            is_draft=False  # Only get non-draft entries
        ).first()

        if esg_data:
            # Update existing entry
            esg_data.raw_value = str(raw_value) if raw_value else None
            esg_data.notes = notes  # ADD THIS
            esg_data.updated_at = datetime.utcnow()
        else:
            # Create new entry
            esg_data = ESGData(
                field_id=field_id,
                entity_id=entity_id,
                reporting_date=reporting_date_obj,
                raw_value=str(raw_value) if raw_value else None,
                notes=notes,  # ADD THIS
                company_id=current_user.company_id
            )
            db.session.add(esg_data)

        # Commit to database
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Data saved successfully',
            'data_id': esg_data.data_id
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid date format: {str(e)}'
        }), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting simple data: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

#### 3.2 Update Dimensional Data API
**File:** `app/routes/user_v2/dimensional_data_api.py`

**Update submit_dimensional_data function (line 145-onwards):**

The dimensional data service already handles notes through the `breakdowns` array. Each breakdown can have notes. Just ensure the service saves them:

**File:** `app/services/user_v2/dimensional_data_service.py`

Verify that notes are being saved in the `save_dimensional_data` method. If not, update it to include notes.

#### 3.3 Create New API Endpoint to Fetch Existing Data with Notes
**File:** `app/routes/user_v2/field_api.py`

**Add new endpoint:**

```python
@field_api_bp.route('/field-data/<field_id>', methods=['GET'])
@login_required
@tenant_required_for('USER')
def get_field_data(field_id):
    """
    Get existing data for a field including notes.

    Query Parameters:
        entity_id (required): Entity ID
        reporting_date (required): Reporting date (YYYY-MM-DD)

    Response:
        {
            "success": true,
            "field_id": "abc-123",
            "entity_id": 1,
            "reporting_date": "2025-01-31",
            "raw_value": "85",
            "calculated_value": null,
            "notes": "Includes 5 new hires from acquisition...",
            "has_notes": true,
            "unit": "employees",
            "dimension_values": {},
            "created_at": "2025-01-12T10:30:00",
            "updated_at": "2025-01-12T14:20:00"
        }
    """
    try:
        from ...models.esg_data import ESGData
        from datetime import datetime

        # Get parameters
        entity_id = request.args.get('entity_id', type=int)
        reporting_date_str = request.args.get('reporting_date')

        if not entity_id or not reporting_date_str:
            return jsonify({
                'success': False,
                'error': 'entity_id and reporting_date are required'
            }), 400

        # Parse date
        try:
            reporting_date = datetime.strptime(reporting_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }), 400

        # Find data entry
        esg_data = ESGData.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date,
            company_id=current_user.company_id,
            is_draft=False
        ).first()

        if not esg_data:
            return jsonify({
                'success': False,
                'error': 'No data found for this field and date'
            }), 404

        return jsonify({
            'success': True,
            'field_id': esg_data.field_id,
            'entity_id': esg_data.entity_id,
            'reporting_date': esg_data.reporting_date.isoformat(),
            'raw_value': esg_data.raw_value,
            'calculated_value': esg_data.calculated_value,
            'notes': esg_data.notes,
            'has_notes': esg_data.has_notes(),
            'unit': esg_data.effective_unit,
            'dimension_values': esg_data.dimension_values,
            'created_at': esg_data.created_at.isoformat() if esg_data.created_at else None,
            'updated_at': esg_data.updated_at.isoformat() if esg_data.updated_at else None
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

#### 3.4 Update Historical Data API to Include Notes
**File:** `app/routes/user_v2/field_api.py` (line 479-617)

**Update get_field_history endpoint:**

```python
# In the history list building (line ~585-593)
history.append({
    'reporting_date': entry.reporting_date.isoformat(),
    'value': value,
    'unit': entry.unit or field.default_unit,
    'has_dimensions': has_dimensions,
    'dimension_values': entry.dimension_values if has_dimensions else None,
    'notes': entry.notes,  # ADD THIS
    'has_notes': entry.has_notes(),  # ADD THIS
    'created_at': entry.created_at.isoformat() if entry.created_at else None,
    'updated_at': entry.updated_at.isoformat() if entry.updated_at else None
})
```

#### 3.5 Update Draft Service to Include Notes
**File:** `app/services/user_v2/draft_service.py`

Ensure draft save/restore handles notes field:

```python
# In save_draft method
draft_data = {
    'value': value,
    'notes': notes,  # Ensure this is included
    'dimension_values': dimension_values,
    # ... other fields
}

# In restore_draft method
return {
    'value': draft_metadata.get('value'),
    'notes': draft_metadata.get('notes'),  # Ensure this is returned
    'dimension_values': draft_metadata.get('dimension_values'),
    # ... other fields
}
```

---

### Phase 4: Display Enhancements

#### 4.1 Show Notes in Historical Data Tab
**File:** `app/templates/user_v2/dashboard.html` (around line 1242)

**Update renderHistoryTable function:**

```javascript
function renderHistoryTable(history, totalCount, hasMore, fieldId) {
    const historyContent = document.getElementById('historicalDataContent');

    if (history.length === 0) {
        historyContent.innerHTML = '<p class="text-muted">No historical data available for this field.</p>';
        return;
    }

    let html = '<div class="historical-data">';

    // Header with export buttons
    html += '<div class="d-flex justify-content-between align-items-center mb-3">';
    html += `<h5 class="mb-0">Historical Submissions (Showing ${history.length} of ${totalCount})</h5>`;
    html += '<div class="export-buttons">';
    html += `<button class="btn btn-sm btn-outline-success me-2" onclick="exportFieldHistory('${fieldId}', 'csv')" title="Export to CSV">`;
    html += '<i class="bi bi-download"></i> CSV</button>';
    html += `<button class="btn btn-sm btn-outline-success" onclick="exportFieldHistory('${fieldId}', 'excel')" title="Export to Excel">`;
    html += '<i class="bi bi-file-earmark-excel"></i> Excel</button>';
    html += '</div>';
    html += '</div>';

    html += '<table class="table table-sm table-striped">';
    html += '<thead><tr><th>Reporting Date</th><th>Value</th><th>Notes</th><th>Submitted On</th></tr></thead>';  // ADD Notes column
    html += '<tbody>';

    history.forEach(entry => {
        const submittedDate = entry.created_at ? new Date(entry.created_at).toLocaleDateString() : 'N/A';
        const valueDisplay = entry.value !== null ? `${entry.value} ${entry.unit || ''}` : 'N/A';

        // ADD notes display
        const notesDisplay = entry.has_notes
            ? `<span class="notes-indicator" title="${escapeHtml(entry.notes)}">💬 ${truncateText(entry.notes, 30)}</span>`
            : '<span class="text-muted">-</span>';

        html += '<tr>';
        html += `<td>${entry.reporting_date}</td>`;
        html += `<td>${valueDisplay}${entry.has_dimensions ? ' <span class="badge badge-info">Dimensional</span>' : ''}</td>`;
        html += `<td>${notesDisplay}</td>`;  // ADD THIS
        html += `<td>${submittedDate}</td>`;
        html += '</tr>';
    });

    html += '</tbody></table>';

    // Load more button...
    if (hasMore) {
        html += '<div class="text-center mt-3">';
        html += `<button class="btn btn-sm btn-outline-primary load-more-btn" onclick="loadMoreHistory('${fieldId}')">`;
        html += 'Load More <i class="bi bi-arrow-down"></i></button>';
        html += '</div>';
    }

    html += '</div>';
    historyContent.innerHTML = html;
}

// Helper function to truncate text
function truncateText(text, maxLength) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
```

**Add CSS for notes indicator:**

```css
/* Add to dashboard.html styles */
.notes-indicator {
    cursor: help;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    background: #eff6ff;
    border-radius: 0.25rem;
    font-size: 0.875rem;
    color: #1e40af;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.notes-indicator:hover {
    background: #dbeafe;
}

.dark .notes-indicator {
    background: #1e3a5f;
    color: #93c5fd;
}

.dark .notes-indicator:hover {
    background: #1e40af;
}
```

#### 4.2 Show Notes in Computed Field Dependency View

When showing dependencies in computed field view, include notes preview:

**File:** Enhancement #1 implementation - `app/static/js/user_v2/computed_field_view.js`

**Update renderDependencyRow:**

```javascript
renderDependencyRow(dep) {
    const statusIcon = this.getStatusIcon(dep.status);
    const valueDisplay = dep.value !== null ?
        `${this.formatValue(dep.value)} ${dep.unit || ''}` : 'N/A';

    // ADD notes preview
    const notesPreview = dep.notes
        ? `<div class="dependency-notes"><small>💬 ${this.escapeHtml(dep.notes.substring(0, 50))}${dep.notes.length > 50 ? '...' : ''}</small></div>`
        : '';

    const actionButton = dep.status === 'available' ?
        `<button class="btn-edit-dependency" data-field-id="${dep.field_id}" data-field-name="${this.escapeHtml(dep.field_name)}">
            <span class="material-icons text-sm">edit</span> Edit
        </button>` :
        `<button class="btn-add-dependency" data-field-id="${dep.field_id}" data-field-name="${this.escapeHtml(dep.field_name)}">
            <span class="material-icons text-sm">add</span> Add Data
        </button>`;

    return `
        <tr class="dependency-row status-${dep.status}">
            <td class="variable-cell">${this.escapeHtml(dep.variable)}</td>
            <td class="field-name-cell">
                ${this.escapeHtml(dep.field_name)}
                ${notesPreview}
            </td>
            <td class="value-cell">${valueDisplay}</td>
            <td class="status-cell">${statusIcon} ${this.formatStatus(dep.status)}</td>
            <td class="action-cell">${actionButton}</td>
        </tr>
    `;
}
```

**Update backend API to include notes:**

**File:** `app/routes/user_v2/field_api.py` - in get_computed_field_details endpoint

```python
# When building dependency_info (around line ~250)
dependency_info = {
    'field_id': dep_field.field_id,
    'field_name': dep_field.field_name,
    'variable': mapping.variable_name,
    'value': dep_data.raw_value if dep_data else None,
    'notes': dep_data.notes if dep_data else None,  # ADD THIS
    'unit': dep_field.default_unit,
    'status': dep_status,
    'reporting_date': reporting_date.isoformat()
}
```

#### 4.3 Update Export Functionality to Include Notes

**File:** `app/routes/user_v2/export_api.py` (if exists, otherwise create it)

Ensure CSV and Excel exports include notes column:

```python
# In export function
headers = ['Reporting Date', 'Value', 'Unit', 'Notes', 'Submitted On']  # ADD Notes
# When building rows
row = [
    entry.reporting_date.isoformat(),
    entry.raw_value or entry.calculated_value,
    entry.effective_unit,
    entry.notes or '',  # ADD THIS
    entry.created_at.isoformat() if entry.created_at else ''
]
```

---

### Phase 5: Computed Fields Notes Support

#### 5.1 Enable Notes for Computed Fields

**File:** `app/templates/user_v2/dashboard.html`

When loading computed field view, show notes section but make it clear it's for explaining the calculation, not the inputs:

```html
<!-- In computed field view (after dependencies table) -->
<div class="mb-3" id="computedNotesSection">
    <label for="computedFieldNotes" class="form-label">
        <span class="material-icons text-sm align-middle">comment</span>
        Notes for This Calculation <span class="text-muted">(Optional)</span>
    </label>
    <textarea
        class="form-control"
        id="computedFieldNotes"
        rows="3"
        maxlength="1000"
        placeholder="Add notes explaining unusual calculated values, known issues, or context about this computation..."
    ></textarea>
    <small class="form-text text-muted">
        These notes explain the computed result. To add notes about input values, edit the dependency fields.
    </small>
</div>
```

#### 5.2 Save Computed Field Notes

Create API endpoint to save notes for computed fields:

**File:** `app/routes/user_v2/field_api.py`

```python
@field_api_bp.route('/save-computed-notes/<field_id>', methods=['POST'])
@login_required
@tenant_required_for('USER')
def save_computed_notes(field_id):
    """
    Save notes for a computed field result.

    Request Body:
        {
            "entity_id": 1,
            "reporting_date": "2025-01-31",
            "notes": "Total is higher due to acquisition..."
        }

    Response:
        {
            "success": true,
            "message": "Notes saved successfully"
        }
    """
    try:
        from ...models.esg_data import ESGData
        from datetime import datetime

        data = request.get_json()
        entity_id = data.get('entity_id')
        reporting_date_str = data.get('reporting_date')
        notes = data.get('notes')

        if not all([entity_id, reporting_date_str]):
            return jsonify({
                'success': False,
                'error': 'entity_id and reporting_date are required'
            }), 400

        # Parse date
        reporting_date = datetime.strptime(reporting_date_str, '%Y-%m-%d').date()

        # Find or create ESGData entry for computed field
        esg_data = ESGData.query.filter_by(
            field_id=field_id,
            entity_id=entity_id,
            reporting_date=reporting_date,
            company_id=current_user.company_id
        ).first()

        if not esg_data:
            # Create entry with just notes (calculated_value will be set by computation service)
            esg_data = ESGData(
                field_id=field_id,
                entity_id=entity_id,
                reporting_date=reporting_date,
                raw_value=None,
                notes=notes,
                company_id=current_user.company_id
            )
            db.session.add(esg_data)
        else:
            esg_data.notes = notes
            esg_data.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Notes saved successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

---

## Test Cases

### Test Case 1: Add Notes to Raw Input Field
**Preconditions:**
- User is logged in
- User has raw input field assigned

**Steps:**
1. Navigate to user dashboard
2. Click "Enter Data" on a raw input field
3. Enter value: "85"
4. Enter notes: "Includes 5 new hires from acquisition"
5. Click "Save Data"

**Expected Results:**
- ✅ Notes field is visible in modal
- ✅ Character counter shows "42 / 1000 characters"
- ✅ Data saves successfully
- ✅ Success message displayed

---

### Test Case 2: View Existing Notes in Historical Data
**Preconditions:**
- Field has historical data with notes

**Steps:**
1. Open field modal
2. Click "Historical Data" tab
3. View entries with notes

**Expected Results:**
- ✅ Historical data table shows notes column
- ✅ Entries with notes show 💬 icon
- ✅ Notes are truncated with "..." if > 30 characters
- ✅ Hovering over notes shows full text in tooltip

---

### Test Case 3: Add Notes to Computed Field
**Preconditions:**
- User has computed field assigned
- Computed field has calculated value

**Steps:**
1. Open computed field modal (View Data)
2. View calculation and dependencies
3. Enter notes: "Higher than expected due to data quality issue"
4. Save notes

**Expected Results:**
- ✅ Notes field is visible and editable
- ✅ Help text explains these notes are for the calculation
- ✅ Notes save successfully
- ✅ Re-opening modal shows saved notes

---

### Test Case 4: Edit Existing Notes
**Preconditions:**
- Data entry exists with notes

**Steps:**
1. Open field modal with existing data
2. Verify existing notes are loaded
3. Modify notes
4. Save

**Expected Results:**
- ✅ Existing notes pre-populate the field
- ✅ Character counter shows correct initial count
- ✅ Modified notes save successfully
- ✅ Old notes are replaced (not appended)

---

### Test Case 5: Notes Character Limit
**Steps:**
1. Open data entry modal
2. Type exactly 1000 characters in notes
3. Try to type more

**Expected Results:**
- ✅ Cannot type beyond 1000 characters
- ✅ Character counter shows "1000 / 1000"
- ✅ Counter turns red when approaching limit (> 900)

---

### Test Case 6: Notes in Dimensional Data
**Preconditions:**
- Field has dimensional data (e.g., Gender × Age)

**Steps:**
1. Open dimensional field modal
2. Enter value for Male, <30: 25
3. Enter notes for that cell: "High turnover in this segment"
4. Save

**Expected Results:**
- ✅ Each dimension cell can have its own notes
- ✅ Notes save independently per dimension combination
- ✅ Historical data shows dimensional notes correctly

---

### Test Case 7: Export with Notes
**Steps:**
1. Open historical data tab
2. Click "CSV" export button
3. Open downloaded CSV

**Expected Results:**
- ✅ CSV includes "Notes" column
- ✅ All notes are present in export
- ✅ Notes with commas/quotes are properly escaped
- ✅ Empty notes show as blank cells

---

### Test Case 8: Auto-Save Includes Notes
**Steps:**
1. Open data entry modal
2. Enter value
3. Enter notes
4. Wait for auto-save (don't click Save)
5. Close modal
6. Re-open modal

**Expected Results:**
- ✅ Auto-save includes notes in draft
- ✅ Re-opening modal shows both value and notes
- ✅ Draft restoration includes notes

---

### Test Case 9: Notes Visibility Across Users
**Preconditions:**
- User A and User B both assigned to same entity

**Steps:**
1. User A enters data with notes
2. User B logs in
3. User B opens same field modal
4. User B views historical data

**Expected Results:**
- ✅ User B can see User A's notes
- ✅ Notes are visible to all users in entity
- ✅ Admin can see notes for all entities

---

### Test Case 10: Clear Notes
**Steps:**
1. Open modal with existing notes
2. Delete all text from notes field
3. Save

**Expected Results:**
- ✅ Notes are cleared (set to NULL)
- ✅ Historical data shows "-" for notes
- ✅ Notes indicator doesn't appear

---

## Success Criteria

✅ **Database schema updated with notes column**
✅ **Notes field visible in data entry modal for all field types**
✅ **Character counter works correctly with limit enforcement**
✅ **Notes save successfully with data submissions**
✅ **Existing notes load when opening modal**
✅ **Historical data displays notes with truncation and tooltips**
✅ **Exports include notes column**
✅ **Auto-save includes notes in drafts**
✅ **Computed fields support notes (editable)**
✅ **Dimensional data supports notes per dimension**
✅ **Notes visibility follows ESGData visibility rules**
✅ **Dark mode support for notes UI**
✅ **All 10 test cases pass**

---

## Rollback Plan

If issues are found after deployment:

1. **Quick Fix:** Hide notes UI (keep database column)
   ```javascript
   document.getElementById('notesSection').style.display = 'none';
   ```

2. **Data Rollback:** Not needed (notes column is nullable, doesn't break existing functionality)

3. **Full Rollback:**
   - Remove notes field from UI
   - Remove notes from API responses
   - Keep database column (safe to ignore)

---

## Future Enhancements (Out of Scope)

1. **Rich Text Editor:** Support formatting (bold, italics, lists) in notes
2. **@Mentions:** Tag other users in notes with notifications
3. **Note History:** Track changes to notes over time
4. **Note Templates:** Common note templates for frequent scenarios
5. **Search Notes:** Full-text search across all notes
6. **Note Categories:** Tag notes (e.g., "Data Quality", "Methodology", "Variance Explanation")
7. **Attachments to Notes:** Link files to specific notes
8. **AI Suggestions:** Auto-suggest notes based on data variance

---

## Estimated Effort

**Development Time:**
- Database Migration: 0.5 hours
- Frontend UI: 3-4 hours
- Backend API Updates: 2-3 hours
- Display Enhancements: 2-3 hours
- Testing: 2-3 hours
- **Total: 9-13.5 hours**

**Complexity:** Low-Medium
- Database: Simple column addition
- Frontend: Standard form field
- Backend: Minor API updates
- No complex logic or dependencies

---

## Dependencies

**Technical:**
- ESGData model
- Bootstrap 5 (modal, forms)
- Existing data entry infrastructure
- Auto-save handler (Phase 4)

**Functional:**
- Must work with both raw and computed fields
- Must work with dimensional data
- Must integrate with existing historical data views
- Must integrate with export functionality

---

## Sign-off

**Prepared By:** Claude Code (AI Agent)
**Date:** 2025-11-12
**Review Status:** Awaiting implementation
**Approved By:** [Pending]

---

## Notes

- This is a foundational feature that enables future collaboration enhancements
- The simple notes approach allows for easy extension to threaded comments later
- Notes visibility follows existing ESGData permissions (no new permission system needed)
- Implementation can be done incrementally (DB → UI → Display)
