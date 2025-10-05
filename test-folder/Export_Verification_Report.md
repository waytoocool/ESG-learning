# Export Functionality Verification Report
**Date**: 2025-10-01
**Test URL**: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2
**Tester**: UI Testing Agent

## Test Summary

**Status**: FAILED - Critical Bug Found
**Issue**: Export endpoint returns HTTP 500 Internal Server Error

## Test Details

### 1. URL Structure Verification
- **Expected URL**: `/admin/api/assignments/export`
- **Actual URL Called**: `/admin/api/assignments/export` ✅
- **Status Code**: 500 (INTERNAL SERVER ERROR) ❌

### 2. Network Analysis

From browser console and network tab:
```
[ERROR] Failed to load resource: the server responded with a status of 500 (INTERNAL SERVER ERROR)
[ERROR] [ServicesModule] API call failed: /api/assignments/export Error: HTTP 500: INTERNAL SERVER ERROR
[ERROR] [ImportExportModule] Export error: Error: HTTP 500: INTERNAL SERVER ERROR
```

Network requests show:
- URL: `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/api/assignments/export`
- Method: GET
- Status: 500 INTERNAL SERVER ERROR
- Called twice (button clicked twice in test)

### 3. Root Cause Analysis

**File**: `/app/routes/admin_assignments_api.py`
**Lines**: 861-862

```python
'start_date': assignment.fy_start_date.isoformat() if assignment.fy_start_date else '',
'end_date': assignment.fy_end_date.isoformat() if assignment.fy_end_date else '',
```

**Problem**: The code attempts to access `assignment.fy_start_date` and `assignment.fy_end_date` as direct model attributes, but these fields do not exist in the `DataPointAssignment` model.

**Evidence**: Search of `data_assignment.py` shows these are computed values from methods, not model fields:
```python
fy_start = self.company.get_fy_start_date(fy_year)  # line 150
fy_end = self.company.get_fy_end_date(fy_year)      # line 151
```

### 4. Impact Assessment

- **Severity**: CRITICAL - Blocks core functionality
- **User Impact**: Admins cannot export assignment data
- **Workaround**: None available
- **Data Integrity**: Not affected (read-only operation)

## Recommended Fix

The export endpoint should either:
1. Remove the fiscal year date fields from the export (if not required)
2. Calculate them dynamically using the company's fiscal year methods
3. Add them as computed properties to the model

Suggested code fix for lines 861-862:
```python
# Option 1: Remove if not needed
# 'start_date': '',
# 'end_date': '',

# Option 2: Calculate dynamically (requires FY year context)
# 'start_date': assignment.company.get_fy_start_date(current_fy_year).isoformat() if assignment.company else '',
# 'end_date': assignment.company.get_fy_end_date(current_fy_year).isoformat() if assignment.company else '',

# Option 3: Use empty strings as placeholder
'start_date': '',
'end_date': '',
```

## Test Evidence

Screenshot saved: `.playwright-mcp/export-500-error.png`

## Testing Context

- **Login**: alice@alpha.com (ADMIN role)
- **Company**: Test Company Alpha
- **Assignments Present**: 17 active assignments loaded
- **Hard Refresh**: Performed to ensure latest JavaScript
- **Browser**: Playwright automated browser

## Conclusion

The URL prefix fix from the previous change was successful - the correct URL `/admin/api/assignments/export` is being called. However, a backend bug in the export endpoint prevents it from functioning. This is a regression or incomplete implementation issue that must be fixed before the export functionality can be used.
