# Quick Test Guide - Computed Field Dependency Auto-Management

**Feature:** Computed Field Dependency Auto-Management
**Date:** 2025-11-10
**Status:** Ready for Testing

## Quick Start Testing

### Prerequisites
1. Start the Flask application: `python3 run.py`
2. Access test company: `http://test-company-alpha.127-0-0-1.nip.io:8000/`
3. Login as admin: alice@alpha.com / admin123
4. Navigate to: Admin Dashboard → Assign Data Points

### Test 1: Auto-Cascade Selection (30 seconds)

**Goal:** Verify dependencies are automatically added when selecting computed field

1. Click on "GRI" framework tab
2. Find "Total rate of employee turnover" in topic tree
3. **Look for:** Purple badge with calculator icon 🧮 (2)
4. Click the "+" button to add this field
5. **Expected Results:**
   - ✅ Success notification appears: "Added 'Total rate of employee turnover' and 2 dependencies"
   - ✅ Selected panel shows 3 fields total (1 computed + 2 raw)
   - ✅ Computed field has purple left border
   - ✅ Dependency fields have blue left border with arrow

**Pass Criteria:** All 4 checkmarks above

### Test 2: Visual Indicators (15 seconds)

**Goal:** Verify computed fields are visually distinct

1. Look at any computed field in the topic tree
2. **Expected Visual Elements:**
   - ✅ Purple gradient badge with calculator icon
   - ✅ Dependency count shown in badge: (2)
   - ✅ Badge has hover effect (slight lift)
   - ✅ Field has purple left border

**Pass Criteria:** All visual elements present

### Test 3: Deletion Protection (45 seconds)

**Goal:** Verify warning when removing dependency field

1. Select "Total rate of employee turnover" (auto-adds 2 dependencies)
2. In selected panel, find one dependency field (e.g., "Total employees")
3. Click the remove button (trash icon) on the dependency
4. **Expected:**
   - ✅ Warning modal appears
   - ✅ Modal title: "Cannot Remove Dependency"
   - ✅ Modal shows "Total rate of employee turnover" as affected
   - ✅ Two options: Cancel or Confirm
5. Click **Cancel**
6. **Expected:** Field remains in selected panel
7. Try again and click **Confirm**
8. **Expected:** Both dependency and computed field removed

**Pass Criteria:** All modal elements correct, removal behavior correct

### Test 4: Already Selected Dependencies (30 seconds)

**Goal:** Verify smart handling of existing selections

1. Clear all selections (remove all fields)
2. Manually select "Total employees" field
3. Then select "Total rate of employee turnover"
4. **Expected:**
   - ✅ Only 1 new dependency auto-added (Total employee turnover)
   - ✅ Notification mentions "1 dependency already selected"
   - ✅ Selected panel shows 3 fields (not duplicates)

**Pass Criteria:** No duplicate fields, correct notification

## Browser Console Checks

Open browser developer tools (F12) and check console:

### Expected Log Messages (Success)
```
[DependencyManager] Loading dependency data...
[DependencyManager] Loaded dependencies for X computed fields
[DependencyManager] Initialized successfully
[AppMain] DependencyManager initialized
```

### Expected Log Messages (When Selecting Computed Field)
```
[DependencyManager] Auto-adding 2 dependencies for <field-id>
[AppState] Added data point: <dependency-1>
[AppState] Added data point: <dependency-2>
```

### Red Flags (Errors to Watch For)
```
❌ Failed to load dependency tree
❌ DependencyManager not available
❌ Cannot read property 'getDependencies' of undefined
```

## API Endpoint Tests (Optional - Advanced)

Use browser developer tools → Network tab:

### Check Dependency Tree Load
1. Navigate to Assign Data Points page
2. Look for network request: `GET /admin/api/assignments/dependency-tree`
3. **Expected Response:**
   - Status: 200 OK
   - Response time: < 500ms
   - Response contains: `{"success": true, "dependency_tree": [...], "total_computed_fields": X}`

### Check Dependency Data
1. Select a computed field
2. Look for any API calls in network tab
3. **Expected:** No additional API calls (data loaded from cache)

## Visual Design Checklist

### Computed Field Badge
- [ ] Purple gradient background (#667eea to #764ba2)
- [ ] White text
- [ ] Calculator icon visible
- [ ] Dependency count in parentheses
- [ ] Rounded corners (12px)
- [ ] Slight shadow effect
- [ ] Hover effect (lifts slightly)

### Field Items
- [ ] Computed fields: Purple left border (3px solid #8b5cf6)
- [ ] Computed fields: Light purple background gradient
- [ ] Dependency fields (in selected panel): Blue left border (3px solid #3b82f6)
- [ ] Dependency fields: Blue arrow indicator (↳)

### Warning Modal
- [ ] Red heading with warning icon
- [ ] List of affected computed fields
- [ ] Red background on field list
- [ ] Clear Cancel/Confirm buttons
- [ ] Proper modal overlay (darkened background)

## Performance Benchmarks

| Operation | Target | How to Measure |
|-----------|--------|----------------|
| Dependency tree load | < 500ms | Network tab, dependency-tree request |
| Auto-cascade selection | < 100ms | Time between click and notification |
| Modal display | < 50ms | Time between remove click and modal |
| UI update after selection | < 200ms | Time to see fields in selected panel |

## Common Issues & Solutions

### Issue: Purple badges not showing
**Solution:**
1. Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)
2. Check browser console for CSS errors
3. Verify `assign_data_points_redesigned.css` loaded

### Issue: Auto-cascade not working
**Solution:**
1. Check browser console for DependencyManager errors
2. Verify logged in as admin (not regular user)
3. Reload page to re-initialize DependencyManager

### Issue: Warning modal not appearing
**Solution:**
1. Verify field is actually a dependency (has purple or blue border)
2. Check that computed field using it is also selected
3. Check browser console for JavaScript errors

### Issue: "Already selected" instead of auto-add
**Explanation:** This is correct behavior! It means dependencies were already selected manually.

## Test Data Reference

### Existing Computed Fields in GRI Framework

1. **Total rate of employee turnover**
   - Formula: A / B
   - Dependencies:
     - Total number of employee turnover
     - Total number of employees
   - Expected auto-add count: 2

2. **Total rate of new employee hires**
   - Formula: A / B
   - Dependencies:
     - Total number of new employee hires
     - Total number of employees
   - Expected auto-add count: 2

## Acceptance Criteria

Feature is considered **PASSING** if:

✅ Auto-cascade adds correct number of dependencies
✅ Purple badges visible on all computed fields
✅ Deletion warning appears for dependency fields
✅ Warning lists correct affected computed fields
✅ Cancelling removal keeps fields selected
✅ Confirming removal removes both dependency and computed fields
✅ No duplicate fields in selected panel
✅ Console shows no errors during normal operation
✅ Visual styling matches design specifications
✅ Performance targets met (< 500ms load, < 100ms operations)

## Bug Reporting Template

If you find issues, report using this format:

```
**Bug Title:** [Brief description]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happened]

**Browser Console Errors:**
[Paste any red error messages]

**Screenshots:**
[Attach if relevant]

**Environment:**
- Browser: [Chrome/Firefox/Safari]
- Version: [Browser version]
- User Role: [Admin/User]
- Company: [test-company-alpha]
```

## Success Report Template

If all tests pass, report using this format:

```
**Test Date:** [Date]
**Tester:** [Your name]
**Browser:** [Browser and version]

**Test Results:**
✅ Test 1: Auto-Cascade Selection - PASS
✅ Test 2: Visual Indicators - PASS
✅ Test 3: Deletion Protection - PASS
✅ Test 4: Already Selected Dependencies - PASS

**Performance:**
- Dependency tree load: [X]ms
- Auto-cascade: [X]ms
- Modal display: [X]ms

**Notes:**
[Any additional observations]

**Recommendation:**
[ ] Ready for production
[ ] Needs minor fixes
[ ] Needs major fixes
```

---

**Total Testing Time:** ~5 minutes
**Recommended Tests:** 1-4 (Core functionality)
**Optional Tests:** API endpoint tests, performance benchmarks

**Happy Testing! 🧮**
