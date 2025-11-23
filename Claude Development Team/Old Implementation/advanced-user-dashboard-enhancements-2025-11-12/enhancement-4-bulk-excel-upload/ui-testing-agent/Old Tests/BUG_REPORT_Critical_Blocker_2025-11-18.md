# BUG REPORT: Critical Blocker - Bulk Upload Template Download

**Bug ID:** BUG-ENH4-001
**Date Reported:** 2025-11-18
**Reported By:** UI Testing Agent
**Severity:** 🔴 **CRITICAL (P0)**
**Status:** NEW
**Priority:** IMMEDIATE FIX REQUIRED

---

## Bug Summary

Template download for bulk upload feature fails with Python AttributeError: `'User' object has no attribute 'entities'`. This is a **complete feature blocker** - no functionality works.

---

## Impact Assessment

### Business Impact
- ⛔ **Feature Unusable:** 100% of bulk upload functionality is blocked
- 📉 **User Experience:** Users cannot submit bulk data, defeating the purpose of the feature
- ⏱️ **Time Savings:** Expected 90% time reduction (from 40-60 min to <5 min) NOT achieved
- 🚫 **ROI:** Zero return on development investment until fixed

### Technical Impact
- **Affected Users:** All USER role users attempting bulk upload
- **Affected Companies:** All tenant companies (test-company-alpha, test-company-beta, test-company-gamma)
- **Affected Workflows:** Template download, file upload, validation, submission (all blocked)
- **Data Integrity:** No impact (feature fails before any database operations)

---

## Bug Details

### Error Information

**Error Message (User-Facing):**
```
Template Download Failed

Failed to generate template
```

**Error Log (Backend):**
```python
[2025-11-18 19:54:35,415] ERROR in bulk_upload_api:
Template generation failed: 'User' object has no attribute 'entities'

127.0.0.1 - - [18/Nov/2025 19:54:35]
"[35m[1mPOST /api/user/v2/bulk-upload/template HTTP/1.1[0m" 500 -
```

**HTTP Response:**
- **Status Code:** 500 Internal Server Error
- **Endpoint:** `POST /api/user/v2/bulk-upload/template`
- **Request Body:** `{"filter": "pending"}`

---

## Root Cause

### Code Analysis

**Problematic Code:**
```python
# File: app/services/user_v2/bulk_upload/template_service.py
# Line: 95

@staticmethod
def _get_assignments(user, filter_type: str):
    """Get assignments based on filter type."""
    from ....models.data_assignment import DataPointAssignment
    from ....models.esg_data import ESGData
    from datetime import date

    today = date.today()

    # Base query - active assignments for user's entities
    base_query = DataPointAssignment.query.filter(
        DataPointAssignment.entity_id.in_([e.id for e in user.entities]),  # ❌ BUG HERE
        DataPointAssignment.series_status == 'active'
    )
```

**Issue:** The code assumes `user.entities` exists as a collection (list/query) but the User model only has `entity_id` (singular integer).

### User Model Structure

```python
# File: app/models/user.py

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=True)  # ✅ SINGULAR
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)

    # No 'entities' relationship defined
    # User has ONE entity, not multiple
```

---

## Steps to Reproduce

### Environment
- **Application URL:** http://test-company-alpha.127-0-0-1.nip.io:8000/
- **User:** bob@alpha.com / user123
- **Role:** USER
- **Entity:** Alpha Factory Manufacturing (ID: 3)

### Reproduction Steps

1. Login as USER (bob@alpha.com)
2. Navigate to `/user/v2/dashboard`
3. Click "Bulk Upload Data" button (purple button in filters area)
4. Modal opens with "Select Template Type" (Step 1)
5. Select any filter:
   - Overdue Only
   - Pending Only ← (tested, but all fail)
   - Overdue + Pending
6. Click "Download Template" button

### Expected Behavior
- Loading indicator appears
- Excel file downloads: `Template_pending_YYYYMMDD_HHMMSS.xlsx`
- File contains:
  - "Data Entry" sheet with rows for user's pending assignments
  - "Instructions" sheet
  - Hidden columns: Field_ID, Entity_ID, Assignment_ID
- Modal remains on Step 1 with success message

### Actual Behavior
- ❌ Alert dialog appears: "Template Download Failed - Failed to generate template"
- ❌ No file downloads
- ❌ HTTP 500 error logged
- ❌ Modal incorrectly advances to Step 2 (Upload File)
- ❌ Backend logs show AttributeError

### Reproducibility
**100% reproducible** - fails every time, all filter types, all users

---

## Proposed Fix

### Solution #1: Single Entity Per User (Recommended)

**Current Application Behavior:** Users have exactly ONE entity assigned via `entity_id`.

```python
# File: app/services/user_v2/bulk_upload/template_service.py
# Line: 94-97

# BEFORE (BUGGY):
base_query = DataPointAssignment.query.filter(
    DataPointAssignment.entity_id.in_([e.id for e in user.entities]),
    DataPointAssignment.series_status == 'active'
)

# AFTER (FIXED):
base_query = DataPointAssignment.query.filter(
    DataPointAssignment.entity_id == user.entity_id,
    DataPointAssignment.series_status == 'active'
)
```

**Additional Safety Check:**
```python
# Add validation at the start of _get_assignments():
if not user.entity_id:
    raise ValueError("User has no entity assigned")
```

### Solution #2: Multi-Entity Support (Future Enhancement)

If users should support multiple entities:

1. **Update User Model:**
```python
# app/models/user.py

class User(db.Model, UserMixin):
    # ... existing fields ...

    # Add many-to-many relationship
    entity_assignments = db.relationship(
        'UserEntityAccess',
        back_populates='user',
        lazy='dynamic'
    )

    @property
    def entities(self):
        """Get all entities user has access to."""
        return [access.entity for access in self.entity_assignments]
```

2. **Create UserEntityAccess Model:**
```python
class UserEntityAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'))
    access_level = db.Column(db.String(50))
```

**Note:** This is out of scope for the current bug fix. Recommend Solution #1.

---

## Testing Strategy

### Unit Tests Needed

```python
# tests/services/test_template_service.py

def test_generate_template_with_valid_user():
    """Test template generation with user having entity_id."""
    user = User(id=3, entity_id=5, email='test@alpha.com')

    # Should not raise AttributeError
    template = TemplateGenerationService.generate_template(user, 'pending')
    assert template is not None

def test_generate_template_without_entity():
    """Test template generation with user having no entity."""
    user = User(id=3, entity_id=None, email='test@alpha.com')

    # Should raise ValueError with clear message
    with pytest.raises(ValueError, match="User has no entity assigned"):
        TemplateGenerationService.generate_template(user, 'pending')

def test_get_assignments_filters():
    """Test each filter type."""
    user = User(id=3, entity_id=5)

    # Test overdue
    assignments = TemplateGenerationService._get_assignments(user, 'overdue')
    assert all(a.is_overdue() for a in assignments)

    # Test pending
    assignments = TemplateGenerationService._get_assignments(user, 'pending')
    assert all(not a.is_overdue() for a in assignments)

    # Test combined
    assignments = TemplateGenerationService._get_assignments(user, 'overdue_and_pending')
    assert len(assignments) > 0
```

### Integration Tests Needed

```python
# tests/integration/test_bulk_upload_api.py

def test_download_template_pending(client, auth_user):
    """Test template download endpoint with pending filter."""
    response = client.post(
        '/api/user/v2/bulk-upload/template',
        json={'filter': 'pending'},
        headers=auth_user
    )

    assert response.status_code == 200
    assert response.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    assert 'Template_pending_' in response.headers['Content-Disposition']

def test_download_template_no_entity(client, auth_user_no_entity):
    """Test template download fails gracefully for user without entity."""
    response = client.post(
        '/api/user/v2/bulk-upload/template',
        json={'filter': 'pending'},
        headers=auth_user_no_entity
    )

    assert response.status_code == 404
    assert 'No entity assigned' in response.json['error']
```

### Manual Testing Checklist

After fix is deployed:

- [ ] Test with bob@alpha.com (has entity_id=3)
- [ ] Test "Pending Only" filter
- [ ] Test "Overdue Only" filter
- [ ] Test "Overdue + Pending" filter
- [ ] Verify Excel file downloads successfully
- [ ] Verify Excel contains correct data
- [ ] Verify modal remains on Step 1 after download
- [ ] Test with user having no entity_id (should show clear error)
- [ ] Test upload workflow with downloaded template
- [ ] Complete full TC-TG-001 through TC-DS-001 critical path

---

## Code Review Findings

### Similar Issues Found

Checked other bulk upload service files for same pattern:

**validation_service.py:**
```python
# Line: No usage of user.entities found ✅ SAFE
```

**submission_service.py:**
```python
# Line: No usage of user.entities found ✅ SAFE
```

**upload_service.py:**
```python
# Line: No usage of user.entities found ✅ SAFE
```

**Conclusion:** Bug is isolated to `template_service.py` only.

### Related Code Patterns

**Correct Usage Examples:**
```python
# app/routes/user_v2/dashboard.py:38
if not current_user.entity_id:
    current_app.logger.warning(f'User {current_user.id} has no entity assigned')

# app/routes/user_v2/dashboard.py:77
all_fields = FieldService.get_assigned_fields_for_entity(
    entity_id=current_entity.id,  # Using entity_id correctly
    include_computed=True
)
```

---

## Fix Verification

### Definition of Done

- [ ] Code updated in `template_service.py` line 95
- [ ] Null check added for `user.entity_id`
- [ ] Unit tests added and passing
- [ ] Integration tests added and passing
- [ ] Manual test with bob@alpha.com successful
- [ ] All three filter types working
- [ ] Excel file downloads correctly
- [ ] Modal state correct (stays on Step 1)
- [ ] Error messages improved
- [ ] Code reviewed by second developer
- [ ] Deployed to test environment
- [ ] Full test suite (90 test cases) executed
- [ ] All critical path tests passing

---

## Timeline

**Estimated Fix Time:**
- Code change: 15 minutes
- Unit tests: 1 hour
- Integration tests: 1 hour
- Manual testing: 1 hour
- Code review: 30 minutes
- **Total: ~3.5 hours**

**Priority:** 🔴 **URGENT** - Block deployment until fixed

---

## Additional Context

### Feature Background
Enhancement #4 was designed to reduce data entry time by 90% (from 40-60 minutes to <5 minutes) by allowing bulk upload of ESG data via Excel templates. This is a high-value feature for users with many assignments.

### Why This Wasn't Caught

1. **No Unit Tests:** Template service wasn't tested with actual User objects
2. **No Integration Tests:** API endpoint not tested end-to-end
3. **Assumption Error:** Developer assumed users have multiple entities
4. **No Pre-Deployment Testing:** Feature pushed without UI testing

### Prevention Measures

1. Add pre-commit hooks requiring unit tests for new services
2. Add integration tests to CI/CD pipeline
3. Require UI testing before merging features
4. Add test coverage requirements (minimum 80%)
5. Document User model relationships clearly

---

## Screenshots

### Evidence of Bug

**Modal Opened (Before Error):**
![Modal Opened](.playwright-mcp/enhancement4-test-2025-11-18/05-TC-TG-001-modal-opened.png)

**Error State (After Failure):**
![Error State](.playwright-mcp/enhancement4-test-2025-11-18/07-TC-TG-001-CRITICAL-FAIL-moved-to-step2.png)

---

## Related Documentation

- **Feature Spec:** `requirements-and-specs.md`
- **Testing Guide:** `TESTING_GUIDE.md`
- **Test Report:** `TEST_EXECUTION_REPORT_2025-11-18.md`
- **User Model:** `app/models/user.py`
- **Buggy Code:** `app/services/user_v2/bulk_upload/template_service.py`

---

**Report Created:** 2025-11-18
**Last Updated:** 2025-11-18
**Next Review:** After fix is deployed
