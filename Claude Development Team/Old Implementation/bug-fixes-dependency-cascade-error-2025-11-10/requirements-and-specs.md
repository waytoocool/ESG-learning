# Bug Fix: Dependency Cascade Selection Error

## Bug Overview
- **Bug ID/Issue**: TypeError in DependencyManager.fetchFieldData()
- **Date Reported**: 2025-11-10
- **Severity**: High (blocks key functionality)
- **Affected Components**: DependencyManager.js, SelectDataPointsPanel.js
- **Affected Tenants**: All companies
- **Reporter**: User testing auto-cascade feature

## Bug Description
When a computed field is selected in the Assign Data Points interface, the system should automatically add its dependency fields. However, this auto-cascade feature is failing with a JavaScript error:

**Error**: `TypeError: Cannot read properties of undefined (reading 'find')`
**Location**: `DependencyManager.js:254`
**Function**: `fetchFieldData()`

The error occurs because `AppState.availableDataPoints` is undefined. The DependencyManager is attempting to fetch dependency field data from a non-existent property in AppState.

## Expected Behavior
1. User selects a computed field (e.g., "Total rate of employee turnover")
2. System automatically identifies the field's 2 dependencies
3. System fetches complete field data for those dependencies
4. System adds the dependencies to the selected data points
5. User sees notification: "Added 'Total rate of employee turnover' and 2 dependencies"

## Actual Behavior
1. User selects a computed field
2. System throws TypeError at line 254 of DependencyManager.js
3. Auto-cascade fails completely
4. Dependencies are not added
5. No notification is shown

## Reproduction Steps
1. Login to test-company-alpha as admin (alice@alpha.com / admin123)
2. Navigate to `/admin/assign-data-points`
3. Select "All Frameworks" or a specific framework
4. Search for "Total rate of employee turnover" computed field
5. Click the "+" button to add it
6. Open browser console to see the error

## Fix Requirements
- [ ] Fix the `fetchFieldData()` method to retrieve dependency data correctly
- [ ] Use SelectDataPointsPanel.flatListData or topicsData as data source
- [ ] Add defensive checks to handle missing data gracefully
- [ ] Ensure field data includes all required properties (id, field_id, name, etc.)
- [ ] Must maintain tenant isolation
- [ ] Must not break existing functionality
- [ ] Must be tested across all user roles

## Success Criteria
- Computed field selection triggers auto-cascade without errors
- Dependency fields are automatically added to selection
- Success notification displays correct field count
- Feature works in both topic tree and flat list views
- Feature works when no framework is selected (all frameworks)
- Feature works when a specific framework is selected
