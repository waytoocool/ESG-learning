# Enhancement #4: Bulk Excel Upload for Overdue Data Submission

**Date Created:** 2025-11-14
**Status:** Planning Complete - Ready for Implementation
**Priority:** High
**Complexity:** High
**Type:** New Feature

---

## Problem Statement

### Current Behavior

Users must submit ESG data one field at a time using the modal popup interface. This creates inefficiencies when:

1. **Multiple overdue items accumulate** - Users have 15-20 pending data points to submit
2. **Batch data collection** - Organizations collect data in spreadsheets and must manually transcribe each value
3. **Quarterly/Annual reporting cycles** - End-of-period spikes require submitting large volumes of data
4. **Data entry from external sources** - Users have data in Excel/CSV from other systems
5. **Dimensional data entry** - Fields with multiple dimension combinations require many individual submissions

### Business Impact

- ⏰ **Time-consuming:** 2-3 minutes per field × 20 fields = 40-60 minutes of repetitive data entry
- ❌ **Error-prone:** Manual transcription from spreadsheets increases mistakes
- 😓 **User frustration:** Repetitive modal popups feel tedious
- 📊 **Delayed reporting:** Users postpone data submission due to effort required
- 🔄 **Inefficient workflow:** Cannot leverage existing Excel-based data collection processes

### Expected Behavior

Users should be able to:
- ✅ Download a pre-filled Excel template with pending/overdue assignments
- ✅ Fill in values offline in Excel (familiar tool)
- ✅ Upload the completed Excel file for validation
- ✅ Review all entries before submission
- ✅ Optionally attach supporting documents to submitted data
- ✅ Submit 20+ data points in under 5 minutes

---

## Solution Design

### Overview

Implement a **5-step bulk upload workflow** that allows users to submit multiple data points via Excel upload while maintaining data integrity, validation, and audit trail.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BULK UPLOAD ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│   User Clicks   │
│ "Bulk Upload"   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: Template Generation (Backend)                              │
├─────────────────────────────────────────────────────────────────────┤
│ • Query DataPointAssignments (filtered by status)                  │
│ • Join with FrameworkDataFields, Entities, Dimensions              │
│ • Calculate valid reporting dates                                  │
│ • Generate Excel with pre-filled metadata                          │
│ • Include hidden columns (Field_ID, Entity_ID, Assignment_ID)      │
│ • Add "Instructions" sheet with validation rules                   │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: User Fills Excel (Offline)                                 │
├─────────────────────────────────────────────────────────────────────┤
│ • User edits only "Value" and "Notes" columns                      │
│ • All other columns are protected/read-only                        │
│ • Dimension rows pre-expanded (one per combination)                │
│ • Saves file locally                                                │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: File Upload & Parsing (Backend)                            │
├─────────────────────────────────────────────────────────────────────┤
│ • Accept .xlsx, .xls, .csv (max 5MB)                               │
│ • Parse using pandas/openpyxl                                       │
│ • Extract data rows (skip instructions sheet)                      │
│ • Read hidden columns for IDs                                       │
│ • Build row dictionaries for validation                            │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: Validation (DataValidationService)                         │
├─────────────────────────────────────────────────────────────────────┤
│ For EACH row:                                                       │
│   ✓ Field assignment exists and is active                          │
│   ✓ Reporting date is valid for assignment                         │
│   ✓ Data type matches (use unified validation)                     │
│   ✓ Dimension values are valid                                     │
│   ✓ Check for existing data (overwrite detection)                  │
│   ✓ Business rules (negative values, ranges, etc.)                 │
│                                                                     │
│ If ANY row fails → REJECT entire upload                            │
│ Return: valid_rows, invalid_rows, overwrite_rows, warnings         │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: Preview & Confirm (Frontend)                               │
├─────────────────────────────────────────────────────────────────────┤
│ • Show validation summary (errors/warnings only)                   │
│ • Display overwrite warnings with old vs new values                │
│ • Allow user to cancel or proceed                                  │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 6: Optional Attachments (Frontend)                            │
├─────────────────────────────────────────────────────────────────────┤
│ • List all validated data entries                                  │
│ • Provide file upload per entry                                    │
│ • Users can skip or attach files                                   │
│ • Backend deduplicates identical files (by hash)                   │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 7: Data Submission (Backend Transaction)                      │
├─────────────────────────────────────────────────────────────────────┤
│ BEGIN TRANSACTION                                                   │
│   • Generate batch_id (UUID)                                        │
│   • Create BulkUploadLog record                                     │
│   For EACH valid row:                                               │
│     • Create or Update ESGData                                      │
│     • Create ESGDataAuditLog (type: Excel Upload/Update)            │
│     • Link ESGDataAttachment if file provided                       │
│   • Update assignment statuses                                      │
│ COMMIT                                                              │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 8: Success Confirmation                                       │
├─────────────────────────────────────────────────────────────────────┤
│ • Display success message with statistics                          │
│ • Update dashboard counts (overdue → complete)                     │
│ • Return to dashboard                                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Technical Specification

### 1. Database Changes

#### 1.1 New Table: BulkUploadLog

```python
class BulkUploadLog(db.Model, TenantScopedModelMixin):
    """Tracks bulk upload operations for audit and monitoring."""

    __tablename__ = 'bulk_upload_logs'

    upload_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # File information
    filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)  # Bytes

    # Upload statistics
    total_rows = db.Column(db.Integer, nullable=False)
    new_entries = db.Column(db.Integer, nullable=False)
    updated_entries = db.Column(db.Integer, nullable=False)
    failed_rows = db.Column(db.Integer, default=0)

    # Attachment statistics
    attachments_uploaded = db.Column(db.Integer, default=0)
    total_attachment_size = db.Column(db.Integer, default=0)  # Bytes

    # Metadata
    upload_date = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    status = db.Column(db.Enum('Success', 'Partial', 'Failed', name='upload_status'),
                      nullable=False, default='Success')

    # Relationships
    company = db.relationship('Company')
    user = db.relationship('User', backref='bulk_uploads')

    # Indexes
    __table_args__ = (
        db.Index('idx_bulk_upload_company', 'company_id'),
        db.Index('idx_bulk_upload_user', 'uploaded_by'),
        db.Index('idx_bulk_upload_date', 'upload_date'),
    )
```

#### 1.2 Enhanced: ESGDataAuditLog

**Add new enum values:**
```python
change_type = db.Column(db.Enum(
    'Create',
    'Update',
    'Delete',
    'On-demand Computation',
    'Smart Computation',
    'CSV Upload',
    'Admin Recompute',
    'Admin Bulk Recompute',
    'Excel Upload',              # NEW: Bulk upload new entry
    'Excel Upload Update',       # NEW: Bulk upload overwrite
    name='change_type'
))
```

**Add metadata column:**
```python
metadata = db.Column(db.JSON, nullable=True)
# Example: {
#     "source": "bulk_upload",
#     "filename": "Pending_Assignments_2025-11-14.xlsx",
#     "row_number": 5,
#     "batch_id": "batch-abc-123",
#     "has_attachment": true,
#     "has_notes": true,
#     "previous_submission_date": "2024-04-05T10:30:00Z"  # For updates
# }
```

#### 1.3 Enhanced: ESGDataAttachment

**Add file hash column for deduplication:**
```python
file_hash = db.Column(db.String(64), nullable=True, index=True)  # SHA256 hash
```

#### 1.4 Enhanced: ESGData (Optional - Enhancement #2 prerequisite)

If Enhancement #2 (Comments/Notes) is not yet implemented:
```python
notes = db.Column(db.Text, nullable=True)  # User notes/comments
```

---

### 2. Backend Implementation

#### 2.1 New Service: DataValidationService

**File:** `app/services/user_v2/data_validation_service.py`

**Purpose:** Unified validation logic for both modal and bulk upload

**Key Methods:**
```python
class DataValidationService:
    @staticmethod
    def validate_data_entry(field_id, entity_id, reporting_date, value,
                           dimensions=None, notes=None) -> Dict[str, Any]

    @staticmethod
    def validate_bulk_upload(rows: List[Dict]) -> Dict[str, Any]

    @staticmethod
    def _validate_reporting_date(reporting_date, assignment) -> Dict

    @staticmethod
    def _validate_data_type(value, value_type) -> Dict

    @staticmethod
    def _validate_dimensions(dimensions, field_id) -> Dict

    @staticmethod
    def _validate_business_rules(value, field, assignment) -> Dict
```

**Validation Rules:**

1. **Field Assignment Validation:**
   - Field must be assigned to entity
   - Assignment must have status 'active'
   - Series version must be latest

2. **Reporting Date Validation:**
   - Date must be in assignment's valid reporting dates
   - Use `assignment.get_valid_reporting_dates()` method

3. **Data Type Validation:**
   - INTEGER: Parse as int, reject decimals
   - DECIMAL/NUMBER: Parse with Decimal, allow formatting (commas)
   - PERCENTAGE: Accept both 15 and 0.15, normalize to decimal
   - CURRENCY: Strip $, commas, parse as decimal
   - BOOLEAN: Accept TRUE/FALSE, YES/NO, 1/0
   - DATE: Parse YYYY-MM-DD format
   - TEXT: Accept as-is

4. **Dimension Validation:**
   - Required dimensions must be present
   - Dimension values must match defined DimensionValue options
   - Warn on unknown dimensions (ignore them)

5. **Business Rules:**
   - Warn on negative values (except variance fields)
   - Warn on very large values (> 1 billion)
   - Can be extended with custom rules per field

#### 2.2 New Blueprint: BulkUploadAPI

**File:** `app/routes/user_v2/bulk_upload_api.py`

**Routes:**

```python
bulk_upload_bp = Blueprint('user_v2_bulk_upload', __name__,
                           url_prefix='/api/user/v2/bulk-upload')

@bulk_upload_bp.route('/template', methods=['POST'])
@login_required
@tenant_required_for('USER')
def download_template():
    """
    Generate Excel template with assignments based on filter.

    Request Body:
        {
            "filter": "overdue" | "pending" | "overdue_and_pending"
        }

    Returns:
        Excel file download with:
        - "Data Entry" sheet with assignments
        - "Instructions" sheet with validation rules
        - Hidden columns: Field_ID, Entity_ID, Assignment_ID
    """
    pass

@bulk_upload_bp.route('/upload', methods=['POST'])
@login_required
@tenant_required_for('USER')
def upload_file():
    """
    Accept Excel file upload and parse.

    Request: multipart/form-data with 'file' field

    Returns:
        {
            "success": true,
            "upload_id": "temp-abc-123",  # Temporary session ID
            "total_rows": 23,
            "parsed_rows": [...],  # Row data for validation
            "filename": "uploaded_file.xlsx"
        }
    """
    pass

@bulk_upload_bp.route('/validate', methods=['POST'])
@login_required
@tenant_required_for('USER')
def validate_upload():
    """
    Validate parsed rows from upload.

    Request Body:
        {
            "upload_id": "temp-abc-123",
            "rows": [...]
        }

    Returns:
        {
            "success": true/false,
            "valid": true/false,  # All rows valid?
            "total_rows": 23,
            "valid_count": 20,
            "invalid_count": 3,
            "warning_count": 5,
            "invalid_rows": [
                {
                    "row_number": 8,
                    "field_name": "Energy Consumption",
                    "errors": ["Invalid DECIMAL format: 'ABCD'"]
                }
            ],
            "warning_rows": [...],
            "overwrite_rows": [
                {
                    "row_number": 5,
                    "field_name": "Total Employees",
                    "old_value": 20,
                    "new_value": 25,
                    "submitted_date": "2024-04-05T10:30:00Z"
                }
            ]
        }
    """
    pass

@bulk_upload_bp.route('/submit', methods=['POST'])
@login_required
@tenant_required_for('USER')
def submit_upload():
    """
    Submit validated data and create ESGData entries.

    Request Body:
        {
            "upload_id": "temp-abc-123",
            "rows": [...],  # Validated rows
            "attachments": {
                "data_id_1": {file_data},
                "data_id_2": {file_data}
            }
        }

    Returns:
        {
            "success": true,
            "batch_id": "batch-abc-123",
            "new_entries": 20,
            "updated_entries": 3,
            "total": 23,
            "attachments_uploaded": 2
        }
    """
    pass

@bulk_upload_bp.route('/cancel', methods=['POST'])
@login_required
@tenant_required_for('USER')
def cancel_upload():
    """
    Cancel an in-progress upload.

    Request Body:
        {"upload_id": "temp-abc-123"}

    Returns:
        {"success": true}
    """
    pass
```

#### 2.3 Excel Template Generation Logic

**Function:** `generate_template(user, filter_type)`

**Process:**

1. Query assignments based on filter:
```python
if filter_type == 'overdue':
    # Get assignments with past due dates and no data
    assignments = get_overdue_assignments(user.entity_id)
elif filter_type == 'pending':
    # Get assignments with no submitted data (not overdue)
    assignments = get_pending_assignments(user.entity_id)
else:  # overdue_and_pending
    assignments = get_overdue_and_pending_assignments(user.entity_id)
```

2. Expand dimensional assignments:
```python
for assignment in assignments:
    field = assignment.field

    if field.has_dimensions():
        # Get all dimension combinations
        dimensions = get_dimension_combinations(field.field_id)

        for dim_combo in dimensions:
            rows.append({
                'Field_Name': field.field_name,
                'Entity': assignment.entity.name,
                'Rep_Date': assignment.get_next_reporting_date(),
                'Dimension_Gender': dim_combo.get('gender', ''),
                'Dimension_Age': dim_combo.get('age', ''),
                # ... other dimension columns
                'Value': '',
                'Unit': assignment.field.default_unit,
                'Notes': '',
                'Status': 'PENDING',
                # Hidden columns
                'Field_ID': field.field_id,
                'Entity_ID': assignment.entity_id,
                'Assignment_ID': assignment.id
            })
    else:
        # Non-dimensional field
        rows.append({
            'Field_Name': field.field_name,
            'Entity': assignment.entity.name,
            'Rep_Date': assignment.get_next_reporting_date(),
            'Value': '',
            'Unit': assignment.field.default_unit,
            'Notes': '',
            'Status': 'PENDING',
            # Hidden columns
            'Field_ID': field.field_id,
            'Entity_ID': assignment.entity_id,
            'Assignment_ID': assignment.id
        })
```

3. Create Excel with pandas/openpyxl:
```python
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Protection

# Create DataFrame
df = pd.DataFrame(rows)

# Write to Excel
with pd.ExcelWriter('template.xlsx', engine='openpyxl') as writer:
    # Data Entry sheet
    df.to_excel(writer, sheet_name='Data Entry', index=False)

    # Instructions sheet
    instructions = create_instructions_sheet()
    instructions.to_excel(writer, sheet_name='Instructions', index=False)

# Post-process with openpyxl for formatting
wb = load_workbook('template.xlsx')
ws = wb['Data Entry']

# Hide ID columns (move to end and hide)
ws.column_dimensions['AA'].hidden = True  # Field_ID
ws.column_dimensions['AB'].hidden = True  # Entity_ID
ws.column_dimensions['AC'].hidden = True  # Assignment_ID

# Protect read-only columns
gray_fill = PatternFill(start_color='E0E0E0', fill_type='solid')
for col in ['A', 'B', 'C', 'D', 'E', 'G', 'H']:  # All except Value (F) and Notes (I)
    for cell in ws[col]:
        cell.fill = gray_fill
        cell.protection = Protection(locked=True)

# Allow editing only Value and Notes columns
ws.protection.sheet = True
ws.protection.password = None  # No password, just UI protection

wb.save('template.xlsx')
```

#### 2.4 File Upload & Parsing Logic

**Function:** `parse_uploaded_file(file)`

**Process:**

1. Validate file:
```python
# Check file extension
allowed_extensions = ['.xlsx', '.xls', '.csv']
if not file.filename.endswith(tuple(allowed_extensions)):
    raise ValidationError("Invalid file format")

# Check file size
if file.size > 5 * 1024 * 1024:  # 5MB
    raise ValidationError("File exceeds 5MB limit")
```

2. Parse with pandas:
```python
import pandas as pd

if file.filename.endswith('.csv'):
    df = pd.read_csv(file)
else:
    df = pd.read_excel(file, sheet_name='Data Entry')

# Extract rows
rows = []
for idx, row in df.iterrows():
    # Build dimension dict
    dimensions = {}
    for col in df.columns:
        if col.startswith('Dimension_'):
            dim_name = col.replace('Dimension_', '').lower()
            if pd.notna(row[col]) and row[col] != '':
                dimensions[dim_name] = str(row[col])

    rows.append({
        'row_number': idx + 2,  # Excel row number
        'field_id': row['Field_ID'],
        'field_name': row['Field_Name'],
        'entity_id': int(row['Entity_ID']),
        'reporting_date': pd.to_datetime(row['Rep_Date']).date(),
        'value': row['Value'],
        'dimensions': dimensions if dimensions else None,
        'notes': row.get('Notes'),
        'assignment_id': row['Assignment_ID']
    })

return rows
```

#### 2.5 Validation Logic

**Function:** `validate_bulk_upload(rows, current_user)`

**Process:**

1. Check for dimension version changes:
```python
for row in rows:
    assignment = DataPointAssignment.query.get(row['assignment_id'])

    # Check if dimensions changed since template download
    current_dimensions = get_field_dimensions(row['field_id'])
    if has_dimension_changes(current_dimensions, row['dimensions']):
        errors.append({
            'row_number': row['row_number'],
            'field_name': row['field_name'],
            'error': 'Field dimensions have changed. Please download a new template.'
        })
        continue
```

2. Use DataValidationService:
```python
from ...services.user_v2.data_validation_service import DataValidationService

validation_result = DataValidationService.validate_bulk_upload(rows)

# REJECT entire upload if any errors
if not validation_result['valid']:
    return {
        'success': False,
        'errors': validation_result['invalid_rows']
    }
```

3. Check for overwrites:
```python
overwrite_rows = []
for row in validation_result['valid_rows']:
    existing = ESGData.query.filter_by(
        field_id=row['field_id'],
        entity_id=row['entity_id'],
        reporting_date=row['reporting_date'],
        is_draft=False
    ).first()

    if existing:
        overwrite_rows.append({
            'row_number': row['row_number'],
            'field_name': row['field_name'],
            'old_value': existing.raw_value,
            'new_value': row['parsed_value'],
            'submitted_date': existing.created_at.isoformat()
        })
```

#### 2.6 Data Submission Logic

**Function:** `submit_bulk_upload(validated_rows, attachments, current_user)`

**Process:**

1. Begin transaction:
```python
from sqlalchemy import exc

try:
    # Generate batch ID
    batch_id = str(uuid4())

    # Create upload log
    upload_log = BulkUploadLog(
        upload_id=batch_id,
        company_id=current_user.company_id,
        uploaded_by=current_user.id,
        filename=filename,
        file_size=file_size,
        total_rows=len(validated_rows)
    )
    db.session.add(upload_log)
```

2. Process each row:
```python
    new_count = 0
    update_count = 0

    for row in validated_rows:
        # Check for existing entry
        existing = ESGData.query.filter_by(
            field_id=row['field_id'],
            entity_id=row['entity_id'],
            reporting_date=row['reporting_date'],
            is_draft=False
        ).first()

        if existing:
            # UPDATE scenario
            audit_log = ESGDataAuditLog(
                data_id=existing.data_id,
                change_type='Excel Upload Update',
                old_value=float(existing.raw_value) if existing.raw_value else None,
                new_value=float(row['parsed_value']),
                changed_by=current_user.id,
                metadata={
                    'source': 'bulk_upload',
                    'filename': filename,
                    'row_number': row['row_number'],
                    'batch_id': batch_id,
                    'previous_submission_date': existing.created_at.isoformat(),
                    'has_notes': bool(row.get('notes'))
                }
            )
            db.session.add(audit_log)

            existing.raw_value = str(row['parsed_value'])
            existing.dimension_values = row.get('dimensions')
            existing.notes = row.get('notes')
            existing.updated_at = datetime.now(UTC)

            update_count += 1

        else:
            # CREATE scenario
            new_entry = ESGData(
                entity_id=row['entity_id'],
                field_id=row['field_id'],
                company_id=current_user.company_id,
                assignment_id=row['assignment_id'],
                raw_value=str(row['parsed_value']),
                reporting_date=row['reporting_date'],
                dimension_values=row.get('dimensions'),
                notes=row.get('notes'),
                is_draft=False
            )
            db.session.add(new_entry)
            db.session.flush()  # Get data_id

            audit_log = ESGDataAuditLog(
                data_id=new_entry.data_id,
                change_type='Excel Upload',
                old_value=None,
                new_value=float(row['parsed_value']),
                changed_by=current_user.id,
                metadata={
                    'source': 'bulk_upload',
                    'filename': filename,
                    'row_number': row['row_number'],
                    'batch_id': batch_id,
                    'has_notes': bool(row.get('notes'))
                }
            )
            db.session.add(audit_log)

            new_count += 1

            # Handle attachment if provided
            if row['field_id'] in attachments:
                file_data = attachments[row['field_id']]

                # Calculate file hash for deduplication
                file_hash = hashlib.sha256(file_data.read()).hexdigest()
                file_data.seek(0)

                # Check for existing file with same hash
                existing_attachment = ESGDataAttachment.query.filter_by(
                    file_hash=file_hash,
                    uploaded_by=current_user.id
                ).first()

                if existing_attachment:
                    # Reuse existing file path
                    file_path = existing_attachment.file_path
                else:
                    # Save new file
                    file_path = save_uploaded_file(file_data)

                # Create attachment record (always create new, even if file reused)
                attachment = ESGDataAttachment(
                    data_id=new_entry.data_id,
                    filename=file_data.filename,
                    file_path=file_path,
                    file_size=len(file_data.read()),
                    mime_type=file_data.content_type,
                    uploaded_by=current_user.id,
                    file_hash=file_hash
                )
                db.session.add(attachment)
```

3. Finalize and commit:
```python
    # Update upload log
    upload_log.new_entries = new_count
    upload_log.updated_entries = update_count
    upload_log.attachments_uploaded = len(attachments)
    upload_log.status = 'Success'

    db.session.commit()

    return {
        'success': True,
        'batch_id': batch_id,
        'new_entries': new_count,
        'updated_entries': update_count
    }

except exc.SQLAlchemyError as e:
    db.session.rollback()
    upload_log.status = 'Failed'
    db.session.commit()
    raise e
```

---

### 3. Frontend Implementation

#### 3.1 New UI Components

**File:** `app/static/js/user_v2/bulk_upload_handler.js`

**Components:**

1. **BulkUploadModal**
   - Multi-step wizard UI
   - Step 1: Template download with filter selection
   - Step 2: File upload with drag-drop
   - Step 3: Validation preview (errors/warnings only)
   - Step 4: Attachment upload (optional)
   - Step 5: Confirmation and submission

2. **TemplateDownloadPanel**
   - Radio buttons for filter selection
   - Download button
   - Progress indicator

3. **FileUploadPanel**
   - Drag-drop zone
   - File format/size validation
   - Upload progress bar

4. **ValidationPreviewPanel**
   - Error list (expandable)
   - Warning list (expandable)
   - Overwrite warnings (highlighted)

5. **AttachmentUploadPanel**
   - List of validated entries
   - File upload per entry
   - Skip all option
   - File deduplication hint

6. **ConfirmationPanel**
   - Summary statistics
   - Impact preview
   - Final submit button

#### 3.2 Template Integration

**File:** `app/templates/user_v2/dashboard.html`

**Add button in dashboard header:**
```html
<div class="quick-actions">
    <button id="bulkUploadBtn" class="btn btn-primary">
        <i class="bi bi-cloud-upload"></i> Bulk Upload Data
    </button>
</div>
```

**Add modal HTML:**
```html
<!-- Bulk Upload Modal -->
<div id="bulkUploadModal" class="modal fade" tabindex="-1">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Bulk Upload Data</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <!-- Multi-step wizard content -->
                <div id="bulkUploadWizard">
                    <!-- Steps will be dynamically rendered -->
                </div>
            </div>
        </div>
    </div>
</div>
```

#### 3.3 JavaScript Flow

```javascript
class BulkUploadHandler {
    constructor() {
        this.currentStep = 1;
        this.uploadId = null;
        this.validatedRows = null;
        this.attachments = {};
    }

    async step1_downloadTemplate(filter) {
        const response = await fetch('/api/user/v2/bulk-upload/template', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({filter: filter})
        });

        const blob = await response.blob();
        this.downloadFile(blob, `Template_${filter}_${Date.now()}.xlsx`);

        this.moveToStep(2);
    }

    async step2_uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/user/v2/bulk-upload/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            this.uploadId = result.upload_id;
            this.validateUpload(result.parsed_rows);
        }
    }

    async validateUpload(rows) {
        const response = await fetch('/api/user/v2/bulk-upload/validate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                upload_id: this.uploadId,
                rows: rows
            })
        });

        const result = await response.json();

        if (!result.valid) {
            this.showValidationErrors(result.invalid_rows);
        } else {
            this.validatedRows = result;
            this.moveToStep(3);
        }
    }

    async step3_showPreview(validationResult) {
        // Show only errors and warnings
        this.renderErrorsAndWarnings(validationResult);
        this.moveToStep(4);
    }

    async step4_collectAttachments() {
        // Show list of validated entries with upload options
        this.renderAttachmentUpload(this.validatedRows.valid_rows);
    }

    async step5_submit() {
        const response = await fetch('/api/user/v2/bulk-upload/submit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                upload_id: this.uploadId,
                rows: this.validatedRows.valid_rows,
                attachments: this.attachments
            })
        });

        const result = await response.json();

        if (result.success) {
            this.showSuccess(result);
            this.closeModal();
            this.refreshDashboard();
        }
    }

    moveToStep(stepNum) {
        this.currentStep = stepNum;
        this.renderStep(stepNum);
    }
}
```

---

### 4. Configuration & Limits

#### File Size Limits

```python
# app/config.py

# Bulk upload specific limits
BULK_UPLOAD_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB for Excel file
BULK_UPLOAD_MAX_ATTACHMENT_SIZE = 20 * 1024 * 1024  # 20MB per attachment
BULK_UPLOAD_MAX_TOTAL_SIZE = 200 * 1024 * 1024  # 200MB total per batch
BULK_UPLOAD_MAX_ROWS = 1000  # Maximum rows per upload

# Allowed file formats
BULK_UPLOAD_ALLOWED_FORMATS = ['.xlsx', '.xls', '.csv']
```

#### Session Management

```python
# Store upload state in Redis (if available) or session
BULK_UPLOAD_SESSION_TIMEOUT = 30 * 60  # 30 minutes
```

---

## UI Mockups & Flow Diagrams

### Complete User Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: Initiate Bulk Upload                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ 📊 User Dashboard                                                   │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ Summary Statistics                                              ││
│ │ ┌───────────┬───────────┬───────────┬───────────┐              ││
│ │ │ Overdue   │ Pending   │ Complete  │ Total     │              ││
│ │ │    15     │    23     │    142    │    180    │              ││
│ │ └───────────┴───────────┴───────────┴───────────┘              ││
│ │                                                                 ││
│ │ Quick Actions                                                   ││
│ │ ┌─────────────────────────────────────────┐                    ││
│ │ │ 📥 Bulk Upload Data                      │ ← USER CLICKS     ││
│ │ └─────────────────────────────────────────┘                    ││
│ └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘

                              ↓

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: Download Template - Filter Selection                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Bulk Upload - Step 1 of 5: Download Template                       │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                     │
│ Select which assignments to include in your template:              │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ ○ Overdue Only (15 items)                                       ││
│ │   Fields past their due date - needs immediate attention        ││
│ │                                                                  ││
│ │ ● Pending Only (23 items)                        [SELECTED]     ││
│ │   Fields not yet submitted but not overdue                      ││
│ │                                                                  ││
│ │ ○ Overdue + Pending (38 items)                                  ││
│ │   All fields that need data submission                          ││
│ └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ ℹ️  Template will include:                                         │
│ • Field names and descriptions                                     │
│ • Entity assignments                                               │
│ • Pre-calculated reporting dates                                   │
│ • Units and data types                                             │
│ • Dimension columns (if applicable)                                │
│                                                                     │
│ ⚠️  Note: Computed fields are excluded (auto-calculated)           │
│                                                                     │
│ [Cancel] [⬇ Download Template]                                     │
└─────────────────────────────────────────────────────────────────────┘

                              ↓
                    (Excel downloads)
                              ↓

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: User Fills Excel (Offline - User's Computer)               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ 📄 Pending_Assignments_2025-11-14.xlsx                             │
│                                                                     │
│ Sheet: "Data Entry"                                                 │
│ ┌──────────────────────────────────────────────────────────────┐  │
│ │Field_Name│Entity│Rep_Date  │Gender│Age  │Value│Unit│Notes  │  │
│ ├──────────┼──────┼──────────┼──────┼─────┼─────┼────┼───────┤  │
│ │Total Emp │Alpha │2024-03-31│Male  │<30  │     │emp │       │  │
│ │Total Emp │Alpha │2024-03-31│Female│<30  │     │emp │       │  │
│ │Total Emp │Alpha │2024-03-31│Male  │30-50│     │emp │       │  │
│ │Total Emp │Alpha │2024-03-31│Female│30-50│     │emp │       │  │
│ │Energy    │Beta  │2024-06-30│      │     │     │kWh │       │  │
│ │... (18 more rows)                                             │  │
│ └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│ User fills in "Value" column:                                      │
│ ┌──────────────────────────────────────────────────────────────┐  │
│ │Field_Name│Entity│Rep_Date  │Gender│Age  │Value│Unit│Notes  │  │
│ ├──────────┼──────┼──────────┼──────┼─────┼─────┼────┼───────┤  │
│ │Total Emp │Alpha │2024-03-31│Male  │<30  │ 25  │emp │HR data│  │
│ │Total Emp │Alpha │2024-03-31│Female│<30  │ 30  │emp │HR data│  │
│ │Total Emp │Alpha │2024-03-31│Male  │30-50│ 40  │emp │HR data│  │
│ │Total Emp │Alpha │2024-03-31│Female│30-50│ 35  │emp │HR data│  │
│ │Energy    │Beta  │2024-06-30│      │     │5000 │kWh │Q2 mtg │  │
│ └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│ User saves file and returns to dashboard...                        │
└─────────────────────────────────────────────────────────────────────┘

                              ↓

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: Upload File                                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Bulk Upload - Step 2 of 5: Upload File                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │                                                                  ││
│ │         📁 Drag & Drop Excel File Here                          ││
│ │                                                                  ││
│ │              or click to browse                                  ││
│ │                                                                  ││
│ │  Supported: .xlsx, .xls, .csv                                   ││
│ │  Max size: 5MB                                                   ││
│ │                                                                  ││
│ └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ [← Back to Template] [Skip to Manual Entry]                        │
└─────────────────────────────────────────────────────────────────────┘

                  (After file dropped)
                              ↓

┌─────────────────────────────────────────────────────────────────────┐
│ ✓ File Selected: Pending_Assignments_2025-11-14.xlsx (234 KB)      │
│                                                                     │
│ [Remove File] [Upload & Validate →]                                │
└─────────────────────────────────────────────────────────────────────┘

                  (User clicks "Upload & Validate")
                              ↓

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: Server Validation (Backend Processing)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ⏳ Validating Your Upload...                                        │
│                                                                     │
│ ✓ File format validated (.xlsx)                                    │
│ ✓ Reading sheets... (2 sheets found)                               │
│ ✓ Parsing rows... (23 data rows found)                             │
│ ✓ Validating field assignments... (23/23)                          │
│ ✓ Checking reporting dates... (23/23)                              │
│ ✓ Validating data types... (23/23)                                 │
│ ✓ Checking for duplicates... (0 found)                             │
│ ⏳ Detecting dimension changes...                                   │
│ ⏳ Checking for existing data (overwrites)...                       │
│                                                                     │
│ Please wait...                                                      │
└─────────────────────────────────────────────────────────────────────┘

                              ↓
                    (CASE A: SUCCESS)
                              ↓

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 6A: Validation Success - Preview (Errors/Warnings Only)       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Bulk Upload - Step 3 of 5: Review & Confirm                        │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                     │
│ ✅ Validation Successful                                            │
│                                                                     │
│ Summary:                                                            │
│ • 20 new data entries will be created                               │
│ • 3 existing entries will be updated                                │
│ • 23 total rows validated                                           │
│                                                                     │
│ ⚠️  Data that will be OVERWRITTEN (3):              [Show Details]│
│                                                                     │
│ [Details expanded:]                                                 │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ Row 5: Total Employees (Alpha, 2024-Q1, Male <30)               ││
│ │   Current: 20 (submitted 2024-04-05)                            ││
│ │   New: 25                                                        ││
│ │   Change: +5 (+25%)                                              ││
│ ├─────────────────────────────────────────────────────────────────┤│
│ │ Row 10: Energy Consumption (Beta, 2024-Q2)                      ││
│ │   Current: 4800 kWh (submitted 2024-07-12)                      ││
│ │   New: 5000 kWh                                                  ││
│ │   Change: +200 kWh (+4.2%)                                       ││
│ ├─────────────────────────────────────────────────────────────────┤│
│ │ Row 18: Water Usage (Gamma, 2024-Q1)                            ││
│ │   Current: 150 m³ (submitted 2024-04-20)                        ││
│ │   New: 120 m³                                                    ││
│ │   Change: -30 m³ (-20%) ⚠️ Significant decrease                ││
│ └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ ✓ All changes will be logged in audit trail                        │
│                                                                     │
│ [← Back] [Continue to Attachments →]                               │
└─────────────────────────────────────────────────────────────────────┘

                              ↓
                    (CASE B: FAILURE)
                              ↓

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 6B: Validation Failure - Show Errors                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ❌ Upload Failed - Validation Errors                                │
│                                                                     │
│ Found 3 errors in your file. Please fix and re-upload.             │
│                                                                     │
│ Errors:                                                             │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ ❌ Row 8: Energy Consumption (Beta, 2024-06-30)                  ││
│ │    Error: Invalid DECIMAL value "ABCD"                           ││
│ │    Expected: Numeric value                                       ││
│ ├─────────────────────────────────────────────────────────────────┤│
│ │ ❌ Row 12: Water Usage (Gamma, 2024-03-31)                       ││
│ │    Error: Invalid reporting date 2024-03-31                      ││
│ │    Valid dates: 2024-06-30, 2024-09-30, 2024-12-31              ││
│ ├─────────────────────────────────────────────────────────────────┤│
│ │ ❌ Row 15: Waste Generated (Delta, 2024-12-31)                   ││
│ │    Error: Field dimensions changed. Download new template.       ││
│ │    Current dimensions: Type, Location (new), Category            ││
│ └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ ⚠️  NO data has been saved. Fix ALL errors and re-upload.          │
│                                                                     │
│ [Download Error Report (.xlsx)] [← Back to Upload]                 │
└─────────────────────────────────────────────────────────────────────┘

            (User fixes errors and re-uploads entire file)
            (Validation succeeds, continues to Step 7)
                              ↓

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 7: Attach Files (Optional)                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Bulk Upload - Step 4 of 5: Attach Files (Optional)                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                     │
│ You submitted data for 23 fields. Attach supporting documents:     │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ ✅ Total Employees (Alpha, 2024-Q1) - Male <30                  ││
│ │    Value: 25 employees                                           ││
│ │    Note: HR data                                                 ││
│ │                                                                  ││
│ │    📎 Attach File  [No file]                    [Skip]          ││
│ ├─────────────────────────────────────────────────────────────────┤│
│ │ ✅ Total Employees (Alpha, 2024-Q1) - Female <30                ││
│ │    Value: 30 employees                                           ││
│ │    Note: HR data                                                 ││
│ │                                                                  ││
│ │    📎 Attach File  [No file]                    [Skip]          ││
│ │    💡 Same source? Upload the same file for deduplication       ││
│ ├─────────────────────────────────────────────────────────────────┤│
│ │ ✅ Total Employees (Alpha, 2024-Q1) - Male 30-50                ││
│ │    Value: 40 employees                                           ││
│ │    Note: HR data                                                 ││
│ │                                                                  ││
│ │    📎 Attach File  [No file]                    [Skip]          ││
│ ├─────────────────────────────────────────────────────────────────┤│
│ │ ... (20 more fields - collapsed by default)    [Expand All]     ││
│ └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ Files attached: 0 / 23                                              │
│                                                                     │
│ ℹ️  System will auto-deduplicate identical files                   │
│                                                                     │
│ [← Back] [Skip All Attachments] [Continue →]                       │
└─────────────────────────────────────────────────────────────────────┘

            (After user uploads some files)
                              ↓

┌─────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ ✅ Total Employees (Alpha, 2024-Q1) - Male <30                  ││
│ │    📎 Q1_HR_Report.pdf (245 KB) [Remove] ✓                      ││
│ ├─────────────────────────────────────────────────────────────────┤│
│ │ ✅ Total Employees (Alpha, 2024-Q1) - Female <30                ││
│ │    📎 Q1_HR_Report.pdf (245 KB) [Remove] ✓                      ││
│ │    💡 Same file detected - will deduplicate                     ││
│ ├─────────────────────────────────────────────────────────────────┤│
│ │ ✅ Energy Consumption (Beta, 2024-Q2)                           ││
│ │    📎 Q2_Meter_Reading.pdf (180 KB) [Remove] ✓                  ││
│ └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ Files attached: 3 / 23                                              │
│                                                                     │
│ [← Back] [Skip Remaining] [Continue →]                             │
└─────────────────────────────────────────────────────────────────────┘

                              ↓

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 8: Final Confirmation                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Bulk Upload - Step 5 of 5: Final Confirmation                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                     │
│ Ready to submit your bulk data upload:                             │
│                                                                     │
│ 📊 Data Entries:                                                    │
│   • 20 new entries                                                  │
│   • 3 updates (overwrites with audit trail)                        │
│   • 23 total entries                                                │
│                                                                     │
│ 📎 File Attachments:                                                │
│   • 3 files uploaded (2 unique after deduplication)                │
│   • Total size: 425 KB                                              │
│   • Breakdown:                                                      │
│     - Q1_HR_Report.pdf → 2 data entries                            │
│     - Q2_Meter_Reading.pdf → 1 data entry                          │
│                                                                     │
│ 📝 Notes:                                                           │
│   • 23 entries include notes                                        │
│                                                                     │
│ ⚙️  This action will:                                               │
│   ✓ Create 20 new ESGData records                                  │
│   ✓ Update 3 existing ESGData records                              │
│   ✓ Create 3 ESGDataAttachment records (2 physical files)          │
│   ✓ Create 23 audit log entries                                    │
│   ✓ Mark 23 assignments as having data                             │
│                                                                     │
│ ⚠️  Warning: Overwrites cannot be undone (audit trail preserved)   │
│                                                                     │
│ [← Back to Edit] [✓ Confirm & Submit]                              │
└─────────────────────────────────────────────────────────────────────┘

                (User clicks "Confirm & Submit")
                              ↓

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 9: Processing                                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ⏳ Processing Your Submission...                                    │
│                                                                     │
│ ✓ Uploading files... (2/2 uploaded)                                │
│ ✓ Creating data entries... (20/20 created)                         │
│ ✓ Updating existing entries... (3/3 updated)                       │
│ ✓ Linking attachments... (3/3 linked)                              │
│ ✓ Creating audit trail... (26/26 logs created)                     │
│ ✓ Updating assignment statuses...                                  │
│                                                                     │
│ Almost done...                                                      │
└─────────────────────────────────────────────────────────────────────┘

                              ↓

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 10: Success!                                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ✅ Bulk Upload Complete!                                            │
│                                                                     │
│ Successfully submitted 23 data entries                              │
│                                                                     │
│ Summary:                                                            │
│ ✓ 20 new entries created                                            │
│ ✓ 3 existing entries updated                                        │
│ ✓ 2 files uploaded (deduplicated from 3)                           │
│ ✓ 425 KB total storage used                                         │
│                                                                     │
│ Your dashboard statistics updated:                                  │
│ • Overdue: 15 → 0  (-15)                                            │
│ • Pending: 23 → 0  (-23)                                            │
│ • Complete: 142 → 165  (+23)                                        │
│                                                                     │
│ Batch ID: batch-abc-123 (for audit reference)                      │
│                                                                     │
│ [Return to Dashboard]                                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Comprehensive UI Test Cases

### Test Suite Overview

```
Test Categories:
├── 1. Template Generation (10 test cases)
├── 2. File Upload & Parsing (12 test cases)
├── 3. Data Validation (20 test cases)
├── 4. Attachment Upload (8 test cases)
├── 5. Data Submission (10 test cases)
├── 6. Error Handling (15 test cases)
├── 7. Edge Cases (10 test cases)
└── 8. Performance & Load (5 test cases)

Total: 90 test cases
```

---

### 1. Template Generation Test Cases

#### TC-TG-001: Download Template - Overdue Only
**Objective:** Verify template downloads with only overdue assignments

**Preconditions:**
- User logged in as bob@alpha.com
- User has 15 overdue assignments

**Steps:**
1. Navigate to dashboard
2. Click "Bulk Upload Data" button
3. Select "Overdue Only" radio button
4. Click "Download Template"

**Expected Results:**
- Excel file downloads: `Template_overdue_[timestamp].xlsx`
- File contains "Data Entry" sheet with 15 rows (if no dimensions)
- File contains "Instructions" sheet
- Hidden columns present: Field_ID, Entity_ID, Assignment_ID
- All rows have Status = "OVERDUE"
- Reporting dates are in the past

**Test Data:**
- Company: test-company-alpha
- User: bob@alpha.com

---

#### TC-TG-002: Download Template - Pending Only
**Objective:** Verify template downloads with only pending assignments

**Preconditions:**
- User has 23 pending (not overdue) assignments

**Steps:**
1. Click "Bulk Upload Data"
2. Select "Pending Only"
3. Click "Download Template"

**Expected Results:**
- Excel downloads with 23+ rows (more if dimensional)
- All rows have Status = "PENDING"
- Reporting dates are in the future

---

#### TC-TG-003: Download Template - Overdue + Pending
**Objective:** Verify combined filter works

**Preconditions:**
- User has 15 overdue + 23 pending = 38 total

**Steps:**
1. Click "Bulk Upload Data"
2. Select "Overdue + Pending"
3. Download template

**Expected Results:**
- Excel contains 38+ rows
- Mix of "OVERDUE" and "PENDING" statuses

---

#### TC-TG-004: Template with Dimensional Fields
**Objective:** Verify dimensional fields expand into multiple rows

**Preconditions:**
- User has assignment for "Total Employees" field
- Field has dimensions: Gender (Male/Female), Age (<30, 30-50, >50)
- Expected combinations: 2 × 3 = 6 rows

**Steps:**
1. Download template (any filter)
2. Open Excel
3. Locate "Total Employees" field

**Expected Results:**
- 6 rows for "Total Employees":
  - Row 1: Male, <30
  - Row 2: Female, <30
  - Row 3: Male, 30-50
  - Row 4: Female, 30-50
  - Row 5: Male, >50
  - Row 6: Female, >50
- All dimension columns filled
- Same Field_ID for all 6 rows

---

#### TC-TG-005: Template Column Protection
**Objective:** Verify read-only columns are protected

**Steps:**
1. Download template
2. Open in Excel
3. Try to edit "Field_Name" column (cell A2)

**Expected Results:**
- Excel shows "This cell is protected" warning
- Cell cannot be edited
- Only "Value" and "Notes" columns editable

---

#### TC-TG-006: Template Hidden Columns
**Objective:** Verify ID columns are hidden

**Steps:**
1. Download template
2. Check columns AA, AB, AC

**Expected Results:**
- Column AA (Field_ID): Hidden, contains UUID values
- Column AB (Entity_ID): Hidden, contains integer IDs
- Column AC (Assignment_ID): Hidden, contains UUID values

---

#### TC-TG-007: Template Instructions Sheet
**Objective:** Verify instructions sheet is comprehensive

**Steps:**
1. Download template
2. Navigate to "Instructions" sheet

**Expected Results:**
- Sheet exists
- Contains sections:
  - How to Use This Template
  - Dimensional Data explanation
  - Validation Rules
  - Data Type Reference
  - After Upload instructions

---

#### TC-TG-008: Template Empty Case - No Assignments
**Objective:** Verify behavior when user has no pending/overdue assignments

**Preconditions:**
- User has submitted all assignments (nothing pending)

**Steps:**
1. Click "Bulk Upload Data"
2. Select any filter
3. Click "Download Template"

**Expected Results:**
- Error message: "No assignments available for bulk upload"
- OR: Download empty template with headers only
- User sees helpful message

---

#### TC-TG-009: Template with Multiple Entities
**Objective:** Verify template includes all user's accessible entities

**Preconditions:**
- User assigned to multiple entities: Alpha Factory, Beta Office

**Steps:**
1. Download template

**Expected Results:**
- Rows include assignments from both entities
- Entity column shows "Alpha Factory" and "Beta Office"

---

#### TC-TG-010: Template Computed Fields Exclusion
**Objective:** Verify computed fields are NOT in template

**Preconditions:**
- User has assignment for computed field "Total Employee Count"

**Steps:**
1. Download template
2. Search for "Total Employee Count"

**Expected Results:**
- Computed field NOT present in template
- Only raw input fields included

---

### 2. File Upload & Parsing Test Cases

#### TC-UP-001: Upload Valid XLSX File
**Objective:** Verify successful upload of .xlsx file

**Preconditions:**
- Template downloaded and filled with valid data

**Steps:**
1. Click "Bulk Upload Data" → Step 2
2. Drag template.xlsx onto upload zone
3. Click "Upload & Validate"

**Expected Results:**
- File uploads successfully
- Progress bar shows 100%
- Moves to validation step
- Shows "Parsing rows... (23 found)"

---

#### TC-UP-002: Upload Valid CSV File
**Objective:** Verify CSV format support

**Steps:**
1. Save template as CSV (comma-delimited)
2. Upload CSV file

**Expected Results:**
- CSV parsed correctly
- All data extracted
- Moves to validation

---

#### TC-UP-003: Upload Valid XLS File (Legacy Format)
**Objective:** Verify .xls support

**Steps:**
1. Convert template to .xls (Excel 97-2003)
2. Upload file

**Expected Results:**
- File accepted
- Parses correctly

---

#### TC-UP-004: Reject Invalid File Format
**Objective:** Verify only allowed formats accepted

**Steps:**
1. Try uploading .pdf file
2. Try uploading .docx file
3. Try uploading .txt file

**Expected Results:**
- Error: "Invalid file format. Supported: .xlsx, .xls, .csv"
- File not accepted
- User can try again

---

#### TC-UP-005: Reject Oversized File
**Objective:** Verify 5MB file size limit

**Steps:**
1. Create Excel file > 5MB (e.g., 6MB)
2. Try uploading

**Expected Results:**
- Error: "File exceeds 5MB limit"
- File rejected
- Suggestion to reduce file size

---

#### TC-UP-006: Upload File with Modified Columns
**Objective:** Verify system handles column modifications

**Steps:**
1. Download template
2. Delete "Notes" column
3. Upload modified file

**Expected Results:**
- Parsing succeeds
- Missing "Notes" treated as empty
- OR: Error if required column missing

---

#### TC-UP-007: Upload File with Extra Columns
**Objective:** Verify system ignores extra columns

**Steps:**
1. Add column "My_Custom_Field" to template
2. Fill with data
3. Upload

**Expected Results:**
- Upload succeeds
- Extra column ignored
- Warning: "Unknown column 'My_Custom_Field' will be ignored"

---

#### TC-UP-008: Upload File with Missing Hidden Columns
**Objective:** Verify system detects tampered template

**Steps:**
1. Delete hidden columns (Field_ID, Entity_ID, Assignment_ID)
2. Upload

**Expected Results:**
- Error: "Template missing required system columns"
- Upload rejected
- Suggestion to download fresh template

---

#### TC-UP-009: Upload Empty File
**Objective:** Verify handling of empty upload

**Steps:**
1. Create Excel with headers only (no data rows)
2. Upload

**Expected Results:**
- Error: "No data rows found"
- Upload rejected

---

#### TC-UP-010: Drag & Drop Upload
**Objective:** Verify drag-drop functionality

**Steps:**
1. Drag file from desktop to upload zone
2. Release mouse

**Expected Results:**
- File captured
- Upload initiates automatically
- Progress indicator shows

---

#### TC-UP-011: Browse & Upload
**Objective:** Verify file browser upload

**Steps:**
1. Click "Choose File" button
2. Browse to file
3. Select and confirm

**Expected Results:**
- File browser opens
- Selected file name displayed
- Upload initiates

---

#### TC-UP-012: Cancel Upload Mid-Process
**Objective:** Verify upload can be cancelled

**Steps:**
1. Start uploading large file
2. Click "Cancel" during upload

**Expected Results:**
- Upload stops
- File discarded
- Returns to upload screen

---

### 3. Data Validation Test Cases

#### TC-DV-001: Validate All Valid Rows
**Objective:** Verify successful validation of clean data

**Preconditions:**
- Template filled with all valid data (23 rows)

**Steps:**
1. Upload file
2. Wait for validation

**Expected Results:**
- Validation succeeds
- Message: "✅ Validation Successful"
- Shows: "23 total rows validated"
- No errors
- Proceeds to preview step

---

#### TC-DV-002: Reject on Invalid Data Type - Text in Number Field
**Objective:** Verify data type validation for numeric fields

**Test Data:**
- Row 5: Energy Consumption = "ABCD" (should be number)

**Steps:**
1. Fill "Value" with text "ABCD" for numeric field
2. Upload

**Expected Results:**
- Validation fails
- Error: "Row 5: Invalid DECIMAL format: 'ABCD'"
- Expected: Numeric value
- Entire upload rejected

---

#### TC-DV-003: Reject on Invalid Reporting Date
**Objective:** Verify reporting date validation

**Test Data:**
- Field: Quarterly frequency (valid: 03-31, 06-30, 09-30, 12-31)
- Row 8: Rep_Date = 2024-05-15 (invalid)

**Steps:**
1. Change reporting date to invalid value
2. Upload

**Expected Results:**
- Error: "Row 8: Invalid reporting date 2024-05-15"
- Shows valid dates: "2024-03-31, 2024-06-30, ..."
- Upload rejected

---

#### TC-DV-004: Reject on Field Not Assigned
**Objective:** Verify assignment validation

**Test Data:**
- Row 10: Field_ID = "xyz-fake-id" (not assigned to user's entity)

**Steps:**
1. Manually edit Field_ID to invalid value
2. Upload

**Expected Results:**
- Error: "Row 10: Field not assigned to this entity"
- Upload rejected

---

#### TC-DV-005: Reject on Invalid Dimension Value
**Objective:** Verify dimension validation

**Test Data:**
- Field has dimension "Gender" with values: Male, Female
- Row 3: Gender = "Other" (not in allowed values)

**Steps:**
1. Enter invalid dimension value
2. Upload

**Expected Results:**
- Error: "Row 3: Invalid value 'Other' for dimension 'Gender'"
- Shows: "Valid values: Male, Female"
- Upload rejected

---

#### TC-DV-006: Reject on Dimension Version Change
**Objective:** Verify dimension change detection

**Preconditions:**
- User downloads template at 10:00 AM
- Admin adds new dimension option "Location" at 10:30 AM
- User uploads at 11:00 AM

**Steps:**
1. Upload old template with outdated dimensions

**Expected Results:**
- Error: "Row X: Field dimensions changed. Download new template"
- Shows current dimensions
- Upload rejected

---

#### TC-DV-007: Validate Missing Required Dimension
**Objective:** Verify required dimensions are enforced

**Test Data:**
- Field has required dimension "Gender"
- Row 4: Gender column is empty

**Steps:**
1. Leave required dimension empty
2. Upload

**Expected Results:**
- Error: "Row 4: Required dimension 'Gender' is missing"
- Upload rejected

---

#### TC-DV-008: Validate Percentage Format - Both Styles
**Objective:** Verify percentage accepts 15 and 0.15

**Test Data:**
- Row 1: Percentage field = "15" (means 15%)
- Row 2: Percentage field = "0.15" (means 15%)

**Steps:**
1. Enter both formats
2. Upload

**Expected Results:**
- Both accepted
- Normalized to 0.15 internally
- Validation succeeds

---

#### TC-DV-009: Validate Currency Format with Symbols
**Objective:** Verify currency parsing

**Test Data:**
- Row 5: Revenue = "$1,000,000.50"
- Row 6: Revenue = "1000000.50"

**Steps:**
1. Enter both formats
2. Upload

**Expected Results:**
- Both accepted
- Symbols and commas stripped
- Stored as 1000000.50

---

#### TC-DV-010: Validate Boolean - Multiple Formats
**Objective:** Verify boolean accepts various inputs

**Test Data:**
- Row 1: TRUE
- Row 2: FALSE
- Row 3: Yes
- Row 4: No
- Row 5: 1
- Row 6: 0

**Steps:**
1. Enter all formats
2. Upload

**Expected Results:**
- All accepted
- TRUE/Yes/1 → true
- FALSE/No/0 → false

---

#### TC-DV-011: Validate Date Format
**Objective:** Verify date field parsing

**Test Data:**
- Row 1: Date = "2024-12-31" (YYYY-MM-DD)
- Row 2: Date = Excel date serial (45290)

**Steps:**
1. Enter both formats
2. Upload

**Expected Results:**
- Both accepted
- Parsed to date object

---

#### TC-DV-012: Warn on Negative Value
**Objective:** Verify business rule warnings

**Test Data:**
- Row 5: Employee Count = -10 (unusual)

**Steps:**
1. Enter negative value for positive field
2. Upload

**Expected Results:**
- Validation succeeds (warning only)
- Warning: "Row 5: Negative value (-10) - please verify"
- Upload proceeds to preview with warning shown

---

#### TC-DV-013: Warn on Very Large Value
**Objective:** Verify large number warning

**Test Data:**
- Row 8: Energy = 5000000000 (5 billion)

**Steps:**
1. Enter extremely large value
2. Upload

**Expected Results:**
- Warning: "Row 8: Very large value (5,000,000,000) - please verify"
- Proceeds with warning

---

#### TC-DV-014: Detect Overwrite - Show Warning
**Objective:** Verify existing data detection

**Preconditions:**
- Row 5: Total Employees (Alpha, 2024-Q1, Male <30)
- Existing data: 20 (submitted 2024-04-05)
- Template value: 25

**Steps:**
1. Upload template with new value
2. Review validation

**Expected Results:**
- Validation succeeds
- Overwrite warning shown:
  - "Row 5 will overwrite existing data"
  - Current: 20, New: 25, Change: +5 (+25%)
  - Submitted: 2024-04-05
- User can proceed or cancel

---

#### TC-DV-015: Validate Empty Value
**Objective:** Verify required value validation

**Test Data:**
- Row 10: Value column is empty

**Steps:**
1. Leave value blank
2. Upload

**Expected Results:**
- Error: "Row 10: Value is required"
- Upload rejected

---

#### TC-DV-016: Validate Notes Length
**Objective:** Verify notes character limit

**Test Data:**
- Row 3: Notes = 1100 characters (exceeds 1000 limit)

**Steps:**
1. Enter very long notes
2. Upload

**Expected Results:**
- Error: "Row 3: Notes exceed maximum length of 1000 characters"
- Upload rejected

---

#### TC-DV-017: Validate Duplicate Rows
**Objective:** Verify duplicate detection

**Test Data:**
- Row 1 and Row 2 identical:
  - Field: Total Employees
  - Entity: Alpha
  - Date: 2024-Q1
  - Gender: Male
  - Age: <30

**Steps:**
1. Create duplicate rows
2. Upload

**Expected Results:**
- Warning or Error: "Duplicate row detected: Row 2 duplicates Row 1"
- User can proceed or fix

---

#### TC-DV-018: Multiple Errors - Show All
**Objective:** Verify all errors displayed

**Test Data:**
- Row 5: Invalid data type
- Row 8: Invalid date
- Row 12: Field not assigned

**Steps:**
1. Upload file with 3 errors

**Expected Results:**
- Shows all 3 errors
- Each with row number and description
- Upload rejected
- User can download error report

---

#### TC-DV-019: Error + Warning - Reject on Error
**Objective:** Verify errors take precedence

**Test Data:**
- Row 3: Warning (negative value)
- Row 7: Error (invalid type)

**Steps:**
1. Upload mixed file

**Expected Results:**
- Upload rejected due to error
- Both error and warning shown
- Must fix error to proceed

---

#### TC-DV-020: Concurrent Upload Validation
**Objective:** Verify session handling for multiple uploads

**Steps:**
1. User A starts upload (Upload 1)
2. During Upload 1 validation, user A starts another upload (Upload 2)

**Expected Results:**
- Warning: "You have an in-progress upload. Resume or cancel?"
- Options: Resume Upload 1, Cancel Upload 1 and start Upload 2
- Only one upload active per session

---

### 4. Attachment Upload Test Cases

#### TC-AT-001: Attach File to Single Entry
**Objective:** Verify single file attachment

**Steps:**
1. Complete validation successfully
2. On attachment step, attach file to Row 1
3. Click "Continue"

**Expected Results:**
- File uploads
- Shows file name and size
- Proceeds to confirmation

---

#### TC-AT-002: Attach Same File to Multiple Entries
**Objective:** Verify file reuse and deduplication

**Steps:**
1. Attach Q1_Report.pdf to Row 1
2. Attach same Q1_Report.pdf to Row 2
3. Attach same Q1_Report.pdf to Row 3

**Expected Results:**
- All 3 uploads accepted
- Hint shown: "Same file detected - will deduplicate"
- Backend stores 1 file, creates 3 attachment records

---

#### TC-AT-003: Skip All Attachments
**Objective:** Verify attachment is optional

**Steps:**
1. On attachment step, click "Skip All Attachments"

**Expected Results:**
- Proceeds to confirmation
- No attachments uploaded
- Data submission succeeds without files

---

#### TC-AT-004: Attach Different Files
**Objective:** Verify multiple unique attachments

**Steps:**
1. Attach Q1_Report.pdf to Row 1
2. Attach Q2_Meter.pdf to Row 5
3. Attach Annual_Summary.xlsx to Row 10

**Expected Results:**
- All 3 files uploaded
- Shows: "Files attached: 3 / 23"
- Proceeds to confirmation

---

#### TC-AT-005: Remove Attached File
**Objective:** Verify file can be removed

**Steps:**
1. Attach file to Row 1
2. Click "Remove" button

**Expected Results:**
- File removed
- Shows: "No file" again
- Can attach different file

---

#### TC-AT-006: Attach Oversized File
**Objective:** Verify 20MB per file limit

**Steps:**
1. Try attaching 25MB PDF

**Expected Results:**
- Error: "File exceeds 20MB limit"
- File rejected
- Can try different file

---

#### TC-AT-007: Attach Invalid File Type
**Objective:** Verify allowed file types

**Test Data:**
- Allowed: pdf, xlsx, docx, csv, jpg, png, zip
- Not allowed: .exe, .bat, .sh

**Steps:**
1. Try attaching .exe file

**Expected Results:**
- Error: "Invalid file type. Allowed: pdf, xlsx, docx, ..."
- File rejected

---

#### TC-AT-008: Total Upload Size Limit
**Objective:** Verify 200MB batch limit

**Steps:**
1. Attach 15 files, each 15MB = 225MB total
2. Try proceeding

**Expected Results:**
- Error: "Total attachment size exceeds 200MB limit"
- Must remove some files to proceed

---

### 5. Data Submission Test Cases

#### TC-DS-001: Submit New Entries Only
**Objective:** Verify creation of new ESGData records

**Preconditions:**
- 23 rows, all new (no existing data)

**Steps:**
1. Complete all steps
2. Click "Confirm & Submit"

**Expected Results:**
- 23 ESGData records created
- 23 audit logs created (type: "Excel Upload")
- BulkUploadLog created with:
  - new_entries: 23
  - updated_entries: 0
- Success message shown
- Dashboard updated: Pending -23, Complete +23

---

#### TC-DS-002: Submit Updates Only
**Objective:** Verify overwrite of existing data

**Preconditions:**
- All 23 rows have existing data

**Steps:**
1. Upload with new values
2. Confirm overwrites
3. Submit

**Expected Results:**
- 0 new ESGData records
- 23 ESGData records updated
- 23 audit logs created (type: "Excel Upload Update")
- BulkUploadLog:
  - new_entries: 0
  - updated_entries: 23

---

#### TC-DS-003: Submit Mix of New and Updates
**Objective:** Verify mixed submission

**Preconditions:**
- 20 rows new, 3 rows existing

**Steps:**
1. Submit

**Expected Results:**
- 20 ESGData created
- 3 ESGData updated
- 23 audit logs total
- BulkUploadLog:
  - new_entries: 20
  - updated_entries: 3

---

#### TC-DS-004: Submit with Attachments
**Objective:** Verify attachment linking

**Preconditions:**
- 3 files attached (2 unique after deduplication)

**Steps:**
1. Submit

**Expected Results:**
- 3 ESGDataAttachment records created
- 2 physical files saved on disk
- file_hash column populated
- BulkUploadLog.attachments_uploaded: 3

---

#### TC-DS-005: Submit with Notes
**Objective:** Verify notes are saved

**Preconditions:**
- All 23 rows have notes filled

**Steps:**
1. Submit

**Expected Results:**
- All ESGData records have notes populated
- Notes visible in data history

---

#### TC-DS-006: Audit Trail - New Entry
**Objective:** Verify audit log for new data

**Steps:**
1. Submit 1 new entry
2. Query ESGDataAuditLog

**Expected Results:**
```sql
SELECT * FROM esg_data_audit_log WHERE data_id = 'new-entry-id'
```
- change_type: "Excel Upload"
- old_value: NULL
- new_value: 25
- changed_by: current_user.id
- metadata: {
    "source": "bulk_upload",
    "filename": "template.xlsx",
    "row_number": 1,
    "batch_id": "batch-abc-123"
  }

---

#### TC-DS-007: Audit Trail - Update Entry
**Objective:** Verify audit log for overwrite

**Preconditions:**
- Existing: Total Employees = 20

**Steps:**
1. Upload with value 25
2. Submit
3. Query audit log

**Expected Results:**
- change_type: "Excel Upload Update"
- old_value: 20
- new_value: 25
- metadata includes: previous_submission_date

---

#### TC-DS-008: Rollback on Error
**Objective:** Verify transaction rollback on failure

**Steps:**
1. Mock database error during submission
2. Trigger submission

**Expected Results:**
- All changes rolled back
- No ESGData created/updated
- No audit logs created
- BulkUploadLog.status: "Failed"
- Error message shown to user

---

#### TC-DS-009: Dashboard Statistics Update
**Objective:** Verify dashboard reflects changes

**Preconditions:**
- Before: Overdue 15, Pending 23, Complete 142

**Steps:**
1. Submit 38 rows (15 overdue + 23 pending)
2. Return to dashboard

**Expected Results:**
- After: Overdue 0, Pending 0, Complete 180
- Field cards update accordingly
- Submitted fields show "Complete" status

---

#### TC-DS-010: Batch ID Generation
**Objective:** Verify unique batch ID

**Steps:**
1. Submit bulk upload
2. Check BulkUploadLog

**Expected Results:**
- upload_id is valid UUID
- Same batch_id in all audit logs
- Batch ID shown in success message

---

### 6. Error Handling Test Cases

#### TC-EH-001: Network Error During Upload
**Objective:** Verify graceful handling of network failure

**Steps:**
1. Start file upload
2. Disconnect network mid-upload

**Expected Results:**
- Error: "Network error. Please check connection and try again"
- Upload can be retried
- No partial data saved

---

#### TC-EH-002: Session Timeout
**Objective:** Verify session expiry handling

**Steps:**
1. Download template
2. Wait 35 minutes (exceed 30 min timeout)
3. Try uploading

**Expected Results:**
- Error: "Session expired. Please log in again"
- Redirect to login
- Upload lost (must restart)

---

#### TC-EH-003: Database Connection Error
**Objective:** Verify DB error handling

**Steps:**
1. Stop database
2. Try submitting upload

**Expected Results:**
- Error: "System error. Please try again later"
- No data corrupted
- BulkUploadLog.status: "Failed"

---

#### TC-EH-004: Disk Full Error
**Objective:** Verify file upload handling when disk full

**Steps:**
1. Fill server disk to capacity
2. Try uploading attachments

**Expected Results:**
- Error: "Storage error. Please contact support"
- Transaction rolled back
- No partial files saved

---

#### TC-EH-005: Corrupt Excel File
**Objective:** Verify handling of damaged files

**Steps:**
1. Corrupt Excel file (edit with text editor)
2. Try uploading

**Expected Results:**
- Error: "Unable to parse file. File may be corrupt"
- Upload rejected
- Suggestion to download new template

---

#### TC-EH-006: Malicious File Upload
**Objective:** Verify security against malicious uploads

**Steps:**
1. Rename virus.exe to template.xlsx
2. Try uploading

**Expected Results:**
- File type detection prevents execution
- Virus scanner (if enabled) blocks
- Error shown

---

#### TC-EH-007: SQL Injection Attempt
**Objective:** Verify protection against SQL injection

**Test Data:**
- Notes field: "'; DROP TABLE esg_data; --"

**Steps:**
1. Enter malicious SQL in notes
2. Upload

**Expected Results:**
- Input sanitized
- Stored as plain text
- No SQL executed
- Database safe

---

#### TC-EH-008: XSS Attempt in Notes
**Objective:** Verify XSS protection

**Test Data:**
- Notes: "<script>alert('XSS')</script>"

**Steps:**
1. Enter script tag in notes
2. Submit
3. View data in dashboard

**Expected Results:**
- Script not executed
- Displayed as text: `&lt;script&gt;...`
- No JavaScript runs

---

#### TC-EH-009: Concurrent Submission
**Objective:** Verify handling of duplicate submissions

**Steps:**
1. Click "Submit" button
2. Immediately click "Submit" again (double-click)

**Expected Results:**
- First submission processes
- Second submission ignored (button disabled after first click)
- Only one batch created

---

#### TC-EH-010: File Upload Timeout
**Objective:** Verify timeout handling for large files

**Steps:**
1. Start uploading 100MB file on slow connection
2. Wait 5 minutes

**Expected Results:**
- Timeout error after 5 min
- Error: "Upload timeout. Please try again"
- Can retry

---

#### TC-EH-011: Invalid Hidden Column Values
**Objective:** Verify tampering detection

**Steps:**
1. Edit Field_ID to invalid UUID
2. Upload

**Expected Results:**
- Error: "Invalid field ID in row X"
- Upload rejected

---

#### TC-EH-012: Missing Dimension After Template Download
**Objective:** Verify dimension deletion handling

**Preconditions:**
- Template downloaded with dimension "Location"
- Admin deletes "Location" dimension before upload

**Steps:**
1. Upload template with deleted dimension

**Expected Results:**
- Error: "Dimension 'Location' no longer exists. Download new template"
- Upload rejected

---

#### TC-EH-013: Assignment Deactivated Between Download and Upload
**Objective:** Verify assignment status checking

**Preconditions:**
- Assignment active when template downloaded
- Admin deactivates assignment before upload

**Steps:**
1. Upload template with deactivated assignment

**Expected Results:**
- Error: "Assignment no longer active. Download new template"
- Upload rejected

---

#### TC-EH-014: Company/Entity Deleted
**Objective:** Verify data integrity checks

**Preconditions:**
- Admin deletes entity referenced in template

**Steps:**
1. Upload template

**Expected Results:**
- Error: "Entity no longer exists"
- Upload rejected

---

#### TC-EH-015: Browser Crash Recovery
**Objective:** Verify user can resume after crash

**Steps:**
1. Start upload (upload_id created)
2. Close browser (simulate crash)
3. Reopen and try again

**Expected Results:**
- Previous upload session expired
- User can start fresh upload
- No orphaned data

---

### 7. Edge Cases Test Cases

#### TC-EC-001: Maximum Rows - 1000
**Objective:** Verify 1000 row limit

**Steps:**
1. Create template with 1000 rows
2. Upload

**Expected Results:**
- Upload succeeds
- All 1000 rows processed
- Performance acceptable (<30 seconds)

---

#### TC-EC-002: Exceed Maximum Rows
**Objective:** Verify rejection over limit

**Steps:**
1. Create template with 1001 rows
2. Upload

**Expected Results:**
- Error: "Maximum 1000 rows allowed"
- Upload rejected
- Suggestion to split into multiple uploads

---

#### TC-EC-003: Single Row Upload
**Objective:** Verify minimum case works

**Steps:**
1. Upload template with 1 row only

**Expected Results:**
- Upload succeeds
- 1 ESGData created
- Audit log created

---

#### TC-EC-004: All Rows Dimensional
**Objective:** Verify handling of many dimension combinations

**Preconditions:**
- Field has 3 dimensions: Type (5 values), Location (4 values), Category (3 values)
- Total combinations: 5 × 4 × 3 = 60 rows

**Steps:**
1. Download template (expands to 60 rows)
2. Fill all rows
3. Upload

**Expected Results:**
- 60 rows validated
- 60 ESGData created with proper dimension_values
- All combinations saved

---

#### TC-EC-005: Special Characters in Notes
**Objective:** Verify unicode/special character handling

**Test Data:**
- Notes: "Value in €, data from 北京 office 🏢"

**Steps:**
1. Enter special characters in notes
2. Upload

**Expected Results:**
- All characters preserved
- Displayed correctly in dashboard
- No encoding errors

---

#### TC-EC-006: Very Long Field Names
**Objective:** Verify UI handles long text

**Preconditions:**
- Field name: "Total number of new employee hires during the reporting period, by age group, gender, and geographic region (annual turnover rate calculation base)"

**Steps:**
1. Download template (includes long field name)
2. View in Excel and upload UI

**Expected Results:**
- Field name displayed correctly (truncated with tooltip)
- No layout breaks
- Upload succeeds

---

#### TC-EC-007: Leap Year Date Validation
**Objective:** Verify date handling for Feb 29

**Test Data:**
- Reporting date: 2024-02-29 (leap year)

**Steps:**
1. Upload with Feb 29 date

**Expected Results:**
- Date accepted for leap year
- Error for non-leap year (2023-02-29)

---

#### TC-EC-008: Zero Value
**Objective:** Verify zero is valid

**Test Data:**
- Row 5: Employee Count = 0

**Steps:**
1. Enter zero
2. Upload

**Expected Results:**
- Accepted as valid
- Stored as 0 (not NULL)

---

#### TC-EC-009: Decimal Precision
**Objective:** Verify decimal handling

**Test Data:**
- Value: 1.23456789012345

**Steps:**
1. Enter high-precision decimal
2. Upload
3. View saved data

**Expected Results:**
- Precision preserved (up to DB limit)
- No rounding errors

---

#### TC-EC-010: Internationalization - Different Decimal Separators
**Objective:** Verify regional number formats

**Test Data:**
- European format: 1.234,56 (period thousands, comma decimal)
- US format: 1,234.56 (comma thousands, period decimal)

**Steps:**
1. Upload with different formats

**Expected Results:**
- System detects based on locale or rejects ambiguous formats
- Clear error if format unclear
- Recommendation: Use standard format (1234.56)

---

### 8. Performance & Load Test Cases

#### TC-PL-001: Large File Upload Speed
**Objective:** Measure upload time for max size file

**Test Data:**
- Excel file: 5MB (near limit)

**Steps:**
1. Upload 5MB file
2. Measure time

**Expected Results:**
- Upload completes in <10 seconds on standard connection
- Progress indicator updates smoothly

---

#### TC-PL-002: Validation Performance - 1000 Rows
**Objective:** Measure validation speed

**Test Data:**
- 1000 rows, all valid

**Steps:**
1. Upload 1000 rows
2. Measure validation time

**Expected Results:**
- Validation completes in <30 seconds
- UI remains responsive
- Progress updates shown

---

#### TC-PL-003: Submission Performance - 1000 Rows
**Objective:** Measure database insert speed

**Steps:**
1. Submit 1000 valid rows

**Expected Results:**
- Submission completes in <60 seconds
- Transaction commits successfully
- No timeout errors

---

#### TC-PL-004: Concurrent Users - 10 Simultaneous Uploads
**Objective:** Verify system handles multiple users

**Steps:**
1. 10 users upload simultaneously
2. Monitor server resources

**Expected Results:**
- All uploads succeed
- No deadlocks
- Acceptable response times (<30 sec each)

---

#### TC-PL-005: Memory Usage - Large Upload
**Objective:** Verify no memory leaks

**Steps:**
1. Upload 1000 rows repeatedly (5 times)
2. Monitor server memory

**Expected Results:**
- Memory usage stable
- No memory leaks
- Garbage collection works properly

---

## Implementation Checklist

### Phase 1: Backend Foundation (Week 1-2)

- [ ] Database migrations
  - [ ] Create BulkUploadLog table
  - [ ] Add metadata column to ESGDataAuditLog
  - [ ] Add file_hash column to ESGDataAttachment
  - [ ] Add notes column to ESGData (if not exists)
  - [ ] Add new enum values to change_type

- [ ] Core services
  - [ ] Implement DataValidationService
  - [ ] Implement template generation logic
  - [ ] Implement file parsing logic
  - [ ] Implement submission logic with audit trail

- [ ] API endpoints
  - [ ] POST /api/user/v2/bulk-upload/template
  - [ ] POST /api/user/v2/bulk-upload/upload
  - [ ] POST /api/user/v2/bulk-upload/validate
  - [ ] POST /api/user/v2/bulk-upload/submit
  - [ ] POST /api/user/v2/bulk-upload/cancel

### Phase 2: Frontend Implementation (Week 3-4)

- [ ] UI components
  - [ ] BulkUploadModal (wizard)
  - [ ] TemplateDownloadPanel
  - [ ] FileUploadPanel (drag-drop)
  - [ ] ValidationPreviewPanel
  - [ ] AttachmentUploadPanel
  - [ ] ConfirmationPanel

- [ ] JavaScript handlers
  - [ ] BulkUploadHandler class
  - [ ] Step navigation logic
  - [ ] File upload handlers
  - [ ] Validation display
  - [ ] Progress indicators

- [ ] CSS styling
  - [ ] Modal styles
  - [ ] Upload zone styles
  - [ ] Error/warning styles
  - [ ] Progress bars

### Phase 3: Integration & Testing (Week 5-6)

- [ ] Unit tests
  - [ ] DataValidationService tests
  - [ ] Template generation tests
  - [ ] File parsing tests
  - [ ] Submission logic tests

- [ ] Integration tests
  - [ ] End-to-end upload flow
  - [ ] Error handling scenarios
  - [ ] Audit trail verification

- [ ] UI testing (Chrome DevTools MCP)
  - [ ] Execute all 90 test cases
  - [ ] Document results
  - [ ] Fix identified bugs

### Phase 4: Documentation & Deployment (Week 7)

- [ ] User documentation
  - [ ] How-to guide
  - [ ] Video tutorial (optional)
  - [ ] FAQ

- [ ] Admin documentation
  - [ ] Troubleshooting guide
  - [ ] Performance tuning

- [ ] Deployment
  - [ ] Staging environment testing
  - [ ] Production deployment
  - [ ] Monitoring setup

---

## Success Metrics

### User Experience Metrics

- **Time Savings**: Reduce bulk data entry time from 40-60 minutes to <5 minutes
- **Error Rate**: <5% validation errors on first upload attempt
- **User Adoption**: >70% of users with 10+ pending items use bulk upload within 1 month

### Technical Metrics

- **Upload Success Rate**: >95% of uploads complete successfully
- **Performance**: Validation of 100 rows completes in <10 seconds
- **Audit Coverage**: 100% of bulk uploads have complete audit trail

### Business Metrics

- **Data Completion Rate**: Increase from 75% to 90% within 2 months
- **User Satisfaction**: NPS score >8 for bulk upload feature
- **Support Tickets**: <5% of bulk uploads require support assistance

---

## Risks & Mitigation

### Risk 1: Users Upload Wrong Data
**Impact:** High - Could corrupt database with incorrect values
**Probability:** Medium
**Mitigation:**
- Comprehensive validation with clear error messages
- Preview step showing all changes
- Overwrite warnings with old vs new values
- Ability to cancel at any step

### Risk 2: Large Files Cause Performance Issues
**Impact:** Medium - Slow response times
**Probability:** Medium
**Mitigation:**
- 5MB file size limit
- 1000 row maximum
- Async processing for large uploads
- Progress indicators

### Risk 3: Template Structure Changes Break Uploads
**Impact:** High - User frustration, failed uploads
**Probability:** Low
**Mitigation:**
- Version template structure
- Detect dimension changes
- Validate assignment status
- Force fresh template download if outdated

### Risk 4: Attachment Deduplication Fails
**Impact:** Low - Wasted storage
**Probability:** Low
**Mitigation:**
- SHA256 hash verification
- Fallback to saving duplicate if hash fails
- Storage monitoring

---

## Future Enhancements (Out of Scope for v1)

### Phase 2 Features

1. **Batch Rollback**
   - "Undo Last Upload" button (30-min window)
   - Restore overwritten values from audit log

2. **Scheduled Uploads**
   - Upload template now, schedule submission for later
   - Useful for awaiting approvals

3. **Partial Re-upload**
   - Upload only failed rows after validation error
   - Don't require entire file re-upload

4. **Excel Add-in**
   - Native Excel add-in for template generation
   - Direct upload from Excel without browser

5. **API Access**
   - Programmatic bulk upload via REST API
   - For integrations with external systems

6. **Advanced Templates**
   - Formulas in Excel for calculated fields
   - Conditional validation rules

7. **Collaborative Editing**
   - Multiple users can fill same template
   - Merge submissions

8. **Import from Other Formats**
   - Google Sheets import
   - JSON import
   - XML import

---

## Appendix

### A. Excel Template Example Structure

```
Sheet 1: "Data Entry"
┌──────────────┬────────┬────────────┬────────┬──────┬───────┬──────┬───────┬────────┬──────────┬──────────┬──────────────┐
│ Field_Name   │ Entity │ Rep_Date   │ Gender │ Age  │ Value │ Unit │ Notes │ Status │ Field_ID │ Entity_ID│ Assignment_ID│
├──────────────┼────────┼────────────┼────────┼──────┼───────┼──────┼───────┼────────┼──────────┼──────────┼──────────────┤
│ Total Emp    │ Alpha  │ 2024-03-31 │ Male   │ <30  │       │ emp  │       │ PENDING│ abc-123  │ 1        │ assign-1     │
│ Total Emp    │ Alpha  │ 2024-03-31 │ Female │ <30  │       │ emp  │       │ PENDING│ abc-123  │ 1        │ assign-1     │
│ Energy       │ Beta   │ 2024-06-30 │        │      │       │ kWh  │       │ PENDING│ def-456  │ 2        │ assign-2     │
└──────────────┴────────┴────────────┴────────┴──────┴───────┴──────┴───────┴────────┴──────────┴──────────┴──────────────┘
         ↑              ↑              ↑                        ↑      ↑       ↑                    ← Hidden columns →
    Read-only      Read-only      Read-only              Editable  Editable  Read-only

Sheet 2: "Instructions"
─────────────────────────────────────────────────────────────────
HOW TO USE THIS TEMPLATE

1. Fill in the "Value" column (Column F) for each row
2. Optionally add notes in the "Notes" column (Column H)
3. Do NOT modify other columns (marked in gray)
4. Do NOT delete or add rows
5. Save the file and upload it back to the dashboard

DIMENSIONAL DATA

• Some fields have dimension columns (e.g., Gender, Age)
• One row = one dimension combination
• Fill in value for EACH combination

VALIDATION RULES

• Values must match data type:
  - INTEGER: Whole numbers only (e.g., 150)
  - DECIMAL: Numbers with decimals (e.g., 1234.56)
  - PERCENTAGE: Enter as 15 or 0.15 (both accepted)
  - CURRENCY: Can include $ and commas (e.g., $1,000.50)
  - BOOLEAN: TRUE/FALSE, YES/NO, or 1/0
  - TEXT: Any text

• All required fields must have values
• Dates cannot be modified
• Notes limited to 1000 characters

AFTER UPLOAD

• You'll be able to attach files for each field
• Same file can be uploaded multiple times if needed
• All changes will be validated before saving
─────────────────────────────────────────────────────────────────
```

### B. API Request/Response Examples

#### Template Download Request
```http
POST /api/user/v2/bulk-upload/template
Content-Type: application/json

{
  "filter": "pending"
}
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="Template_pending_20251114_143000.xlsx"

[Binary Excel file]
```

#### Upload & Validate Request
```http
POST /api/user/v2/bulk-upload/upload
Content-Type: multipart/form-data

file: [Excel file binary]
```

**Response (Success):**
```json
{
  "success": true,
  "upload_id": "temp-abc-123",
  "total_rows": 23,
  "filename": "template.xlsx",
  "file_size": 245760
}
```

#### Validation Request
```http
POST /api/user/v2/bulk-upload/validate
Content-Type: application/json

{
  "upload_id": "temp-abc-123"
}
```

**Response (With Errors):**
```json
{
  "success": true,
  "valid": false,
  "total_rows": 23,
  "valid_count": 20,
  "invalid_count": 3,
  "warning_count": 2,
  "invalid_rows": [
    {
      "row_number": 8,
      "field_name": "Energy Consumption",
      "errors": ["Invalid DECIMAL format: 'ABCD'"]
    },
    {
      "row_number": 12,
      "field_name": "Water Usage",
      "errors": ["Invalid reporting date 2024-05-15"]
    },
    {
      "row_number": 15,
      "field_name": "Waste Generated",
      "errors": ["Field dimensions changed. Download new template"]
    }
  ],
  "warning_rows": [
    {
      "row_number": 5,
      "field_name": "Total Employees",
      "warnings": ["Negative value (-10) detected - please verify"]
    }
  ],
  "overwrite_rows": [
    {
      "row_number": 3,
      "field_name": "Total Employees",
      "old_value": "20",
      "new_value": "25",
      "submitted_date": "2024-04-05T10:30:00Z"
    }
  ]
}
```

#### Submission Request
```http
POST /api/user/v2/bulk-upload/submit
Content-Type: application/json

{
  "upload_id": "temp-abc-123",
  "attachments": {
    "data-id-1": {
      "filename": "Q1_Report.pdf",
      "data": "[base64 encoded file data]",
      "size": 245760,
      "mime_type": "application/pdf"
    }
  }
}
```

**Response (Success):**
```json
{
  "success": true,
  "batch_id": "batch-def-456",
  "new_entries": 20,
  "updated_entries": 3,
  "total": 23,
  "attachments_uploaded": 1
}
```

---

## Approval & Sign-off

**Prepared By:** Claude (AI Assistant)
**Date:** 2025-11-14
**Version:** 1.0

**Reviewed By:** _________________________
**Date:** __________

**Approved By:** _________________________
**Date:** __________

---

**End of Enhancement #4 Specification**
