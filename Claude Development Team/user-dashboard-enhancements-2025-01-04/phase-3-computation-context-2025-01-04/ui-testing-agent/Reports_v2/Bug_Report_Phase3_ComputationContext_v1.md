# Bug Report: Phase 3 Computation Context Feature
**Version:** v1
**Date:** 2025-10-04
**Tester:** UI Testing Agent
**Environment:** Test Company Alpha (http://test-company-alpha.127-0-0-1.nip.io:8000/)
**User:** bob@alpha.com (USER role)
**Entity:** Alpha Factory (ID: 3)

---

## Executive Summary

**CRITICAL BLOCKER IDENTIFIED**: The Phase 3 Computation Context feature fails completely due to an assignment resolution issue in the multi-tenant environment. While the UI, API routes, and service layer are correctly implemented, the `resolve_assignment()` function returns `None` when called through HTTP requests with tenant middleware active, causing all Formula button clicks to fail with HTTP 404 errors.

**Impact:** Phase 3 feature is 100% non-functional in production-like environment (web browser with authenticated session).

---

## Test Environment Details

### Database Status (Verified)
- 12 computed fields created across 3 test companies
- 33 variable mappings created
- 20 data point assignments created
- 48 historical ESG data records created (12 months × 4 fields for Test Company Alpha)

### Computed Fields for Test Company Alpha (company_id=2)
1. **Total Energy Consumption** (ID: 06437e92-8778-40a5-b81b-dcf6c8d8579e) - Formula: `A + B`
2. **Energy Efficiency Ratio** - Formula: `A / B`
3. **Average Resource Consumption** - Formula: `(A + B) / C`
4. **Complex Sustainability Index** - Formula: `(A + B) * C / D`

All 4 fields have active assignments for Entity 3 (Alpha Factory).

---

## Critical Bug: Assignment Resolution Failure

### Bug Classification
- **Severity:** CRITICAL - Blocks entire Phase 3 feature
- **Priority:** P0 - Must fix before deployment
- **Type:** Backend Logic Error - Tenant Scoping Issue

### Symptom
When clicking the "Formula" button for any computed field, the API call fails with:
```
HTTP 404: NOT FOUND
{
  "error": "No assignment found for this field",
  "success": false
}
```

### Root Cause Analysis

#### Evidence Chain

**1. UI Layer** ✅ Working Correctly
- Computed fields display in dashboard (8 fields shown)
- "Formula" buttons render next to each computed field
- Button click triggers JavaScript handler correctly
- API request sent to: `/user/v2/api/computation-context/06437e92-8778-40a5-b81b-dcf6c8d8579e?entity_id=3&reporting_date=2025-10-04`

**2. API Route Registration** ✅ Working Correctly
- Blueprint `computation_context_api_bp` properly imported
- Route `/user/v2/api/computation-context/<field_id>` registered in app
- Verified with Flask route inspection:
  ```
  /user/v2/api/computation-context/<field_id> -> computation_context_api.get_computation_context
  ```

**3. Authentication & Authorization** ✅ Working Correctly
Flask logs confirm:
```
[2025-10-04 23:38:32,126] DEBUG in auth: Access granted: User 3 (role: USER) accessing get_computation_context for tenant 2
```

**4. Service Layer** ✅ Works in Isolation
Direct Python test (WITHOUT web request context):
```python
result = ComputationContextService.get_computation_context(field_id, entity_id, reporting_date)
# Returns: {'success': True, 'field': {...}, 'formula': 'High Coverage Framework Field 1  +  High Coverage Framework Field 10', ...}
```

**5. Database** ✅ Assignments Exist
```python
assignments = DataPointAssignment.query.filter_by(field_id='06437e92-8778-40a5-b81b-dcf6c8d8579e').all()
# Returns: 2 assignments
#   - Entity 2, Status: active
#   - Entity 3, Status: active
```

**6. Critical Failure Point** ❌ `resolve_assignment()` in Web Context

When called through HTTP request WITH tenant middleware:
```
resolve_assignment(field_id='06437e92-8778-40a5-b81b-dcf6c8d8579e', entity_id=3, reporting_date=date(2025,10,4))
# Returns: None
```

When called in Python shell WITHOUT request context:
```python
resolve_assignment(field_id='06437e92-8778-40a5-b81b-dcf6c8d8579e', entity_id=3, reporting_date=date(2025,10,4))
# Returns: <DataPointAssignment object>
```

### Technical Deep Dive

#### Code Path to Failure

1. **API Handler** (`app/routes/user_v2/computation_context_api.py:56-137`)
   ```python
   @computation_context_api_bp.route('/computation-context/<field_id>', methods=['GET'])
   @login_required
   @tenant_required_for('USER', 'ADMIN')
   def get_computation_context(field_id):
       context = ComputationContextService.get_computation_context(field_id, entity_id, reporting_date)
       if not context.get('success', True):  # ← This evaluates to True
           return jsonify(context), 404        # ← Returns 404
   ```

2. **Service Method** (`app/services/user_v2/computation_context_service.py:66-71`)
   ```python
   # Get assignment for this field
   assignment = resolve_assignment(field_id, entity_id, reporting_date)
   if not assignment:  # ← assignment is None!
       return {
           'success': False,
           'error': 'No assignment found for this field'  # ← This error is returned
       }
   ```

3. **Assignment Resolution** (`app/services/assignment_versioning.py`)
   - The `resolve_assignment()` function uses tenant-scoped queries
   - In web request context, tenant middleware filters queries to current tenant
   - Query returns empty result despite assignment existing in database
   - **Hypothesis:** Tenant scoping logic has a bug when resolving assignments for computed fields

#### Suspect Code Areas

1. **Tenant Middleware** (`app/middleware/tenant.py`)
   - May be over-filtering queries for computed field assignments
   - Could be blocking cross-entity or cross-field-type queries

2. **Assignment Resolution Service** (`app/services/assignment_versioning.py`)
   - `AssignmentResolutionService.resolve_assignment()` method
   - May not properly handle company_id in tenant-scoped context
   - Cache may be using incorrect tenant-scoping keys

3. **Data Point Assignment Model** (`app/models/data_assignment.py`)
   - Model may have tenant scoping mixins that interfere with resolution
   - Relationship mappings may not work correctly in multi-tenant context

---

## Test Results Summary

### Phase 3 Features Tested (15 Total)

| # | Test Item | Status | Notes |
|---|-----------|--------|-------|
| 1 | Computed Field Display | ✅ PASS | 8 computed fields visible in dashboard |
| 2 | "Formula" Button Visibility | ✅ PASS | Buttons render next to all computed fields |
| 3 | Modal Opening | ❌ FAIL | Modal never opens due to API 404 error |
| 4 | Formula Display | ❌ BLOCKED | Cannot test - modal doesn't open |
| 5 | Dependency Tree | ❌ BLOCKED | Cannot test - modal doesn't open |
| 6 | Historical Trend Chart | ❌ BLOCKED | Cannot test - modal doesn't open |
| 7 | Modal Closing | ❌ BLOCKED | Cannot test - modal doesn't open |
| 8 | Calculation Steps | ❌ BLOCKED | Cannot test - modal doesn't open |
| 9 | Trend Analysis | ❌ BLOCKED | Cannot test - modal doesn't open |
| 10 | Status Badges | ❌ BLOCKED | Cannot test - modal doesn't open |
| 11 | Responsive Design | ❌ BLOCKED | Cannot test - modal doesn't open |
| 12 | Multiple Fields | ❌ BLOCKED | All fields fail with same error |
| 13 | API Response Structure | ❌ FAIL | Returns 404 instead of 200 with context data |
| 14 | Missing Dependencies | ❌ BLOCKED | Cannot test error states |
| 15 | Error Handling | ⚠️ PARTIAL | Error is caught but user sees no feedback |

**Pass Rate: 2/15 (13.3%)**
**Blocked: 11/15 (73.3%)**
**Failed: 2/15 (13.3%)**

---

## Evidence & Screenshots

### Screenshot 1: Dashboard Initial State
**File:** `screenshots/01-dashboard-initial-state.png`
**Shows:**
- User Dashboard V2 loaded successfully
- 28 total fields displayed (20 raw + 8 computed)
- Computed fields table with "Formula" buttons visible
- Current date: 2025-10-04
- Entity: Alpha Factory

### Screenshot 2: Formula Button 404 Error
**File:** `screenshots/02-formula-button-404-error.png`
**Shows:**
- Same dashboard state (no visual change after button click)
- No modal opened
- No error message shown to user
- Console shows: `Error loading computation context: Error: HTTP 404: NOT FOUND`

### Screenshot 3: Browser Console Errors
**File:** `screenshots/03-browser-console-errors.png`
**Shows:**
- JavaScript error from computation_context_handler.js
- Failed fetch request to `/user/v2/api/computation-context/...`
- HTTP 404 status code

---

## Network Request Details

### Failed API Call
```
Request:
GET /user/v2/api/computation-context/06437e92-8778-40a5-b81b-dcf6c8d8579e?entity_id=3&reporting_date=2025-10-04
Host: test-company-alpha.127-0-0-1.nip.io:8000
Cookie: session=<authenticated_session>

Response:
HTTP/1.1 404 NOT FOUND
Content-Type: application/json

{
  "error": "No assignment found for this field",
  "success": false
}
```

### Flask Server Logs
```
[2025-10-04 23:38:32,126] DEBUG in auth: Access granted: User 3 (role: USER) accessing get_computation_context for tenant 2
127.0.0.1 - - [04/Oct/2025 23:38:32] "[33mGET /user/v2/api/computation-context/06437e92-8778-40a5-b81b-dcf6c8d8579e?entity_id=3&reporting_date=2025-10-04 HTTP/1.1[0m" 404 -
```

**Note:** Auth passed ✅ but assignment resolution failed ❌

---

## Browser Console Errors

```javascript
[ERROR] Failed to load resource: the server responded with a status of 404 (NOT FOUND)
@ http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/api/computation-context/06437e92-8778-40a5-b81b-dcf6c8d8579e?entity_id=3&reporting_date=2025-10-04:0

[ERROR] Error loading computation context: Error: HTTP 404: NOT FOUND
    at ComputationContextHandler.loadComputationContext (http://test-company-alpha.127-0-0-1.nip.io:8000/static/js/user_v2/computation_context_handler.js?v=1759588442:40:23)
@ http://test-company-alpha.127-0-0-1.nip.io:8000/static/js/user_v2/computation_context_handler.js?v=1759588442:51
```

---

## User Experience Impact

### Current Behavior
1. User clicks "Formula" button
2. No visible feedback (no loading state, no error message)
3. Button appears to do nothing
4. No modal opens
5. Silent failure - user has no idea what went wrong

### Expected Behavior
1. User clicks "Formula" button
2. Loading indicator appears
3. Modal opens with computation context
4. Formula, dependencies, trend chart all visible
5. User can explore calculation details

### UX Severity
- **Confusing:** User gets zero feedback
- **Frustrating:** Feature appears broken with no explanation
- **Blocking:** Cannot access ANY computation context for ANY field

---

## Recommended Fix Priority

### Immediate Actions (P0 - Must Fix)
1. **Debug `resolve_assignment()` in tenant context**
   - Add detailed logging to assignment resolution
   - Check tenant filtering logic in DataPointAssignment queries
   - Verify company_id propagation through query chain

2. **Fix tenant scoping for computed field assignments**
   - Ensure assignments are correctly scoped to company_id=2
   - Verify entity relationships respect tenant boundaries
   - Test assignment resolution with/without tenant middleware

3. **Add user-facing error handling**
   - Show toast notification when API fails
   - Display helpful error message in modal
   - Log errors for debugging

### Testing Requirements Before Deployment
- ✅ Verify `resolve_assignment()` works in web request context
- ✅ Test all 4 computed fields open modal successfully
- ✅ Verify formula, dependencies, trend chart render
- ✅ Test across all 3 test companies
- ✅ Test with different user roles (USER, ADMIN)
- ✅ Test error scenarios (missing data, invalid field ID)

---

## Additional Observations

### Positive Findings
- Phase 1 & 2 features still working correctly
- Database seeding script worked perfectly
- UI components are well-structured and ready
- API route architecture is correct
- Service layer logic is sound (when tested in isolation)

### Technical Debt Identified
1. **Silent Failures:** No error feedback to users
2. **Logging Gaps:** Assignment resolution not logging failures
3. **Test Coverage:** Missing integration tests for tenant-scoped assignment resolution
4. **Documentation:** No documentation of tenant scoping requirements for assignment resolution

---

## Conclusion

Phase 3 Computation Context feature is **completely blocked** by a critical backend bug in the assignment resolution system. The feature cannot proceed to user testing until the `resolve_assignment()` function correctly handles multi-tenant queries in HTTP request contexts.

**Estimated Fix Effort:** 2-4 hours (debug tenant scoping + fix + test)
**Risk Level:** HIGH - Core multi-tenant functionality may have systemic issues
**Blocker Status:** CRITICAL - Blocks all Phase 3 functionality

---

## Attachments
- `screenshots/01-dashboard-initial-state.png` - Dashboard with computed fields
- `screenshots/02-formula-button-404-error.png` - Failed API call state
- `screenshots/03-browser-console-errors.png` - JavaScript errors

## Test Artifacts
- Test Date: 2025-10-04 23:38 UTC
- Browser: Playwright (Chromium-based)
- Resolution: 1280x720 (default viewport)
- Network: localhost (127-0-0-1.nip.io subdomain routing)

---

**Report Generated By:** UI Testing Agent
**Report Format:** Comprehensive Bug Report
**Next Steps:** Backend developer to investigate tenant scoping in assignment resolution service
