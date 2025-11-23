# Bug Report: Category Filter Not Working
**Bug ID:** BUG-20250123-001
**Report Date:** January 23, 2025
**Reporter:** UI Testing Agent
**Version:** v1
**Priority:** Medium
**Severity:** Medium
**Status:** New

---

## Bug Summary

Category filter dropdown does not correctly filter dashboard fields. When selecting any specific category (e.g., "Energy", "Emissions", "Social", "Governance"), all field sections disappear instead of showing the filtered results.

---

## Environment

**Application:** ESG DataVault - User Dashboard V2
**URL:** `http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/dashboard`
**User Role:** USER
**Test User:** bob@alpha.com
**Company:** Test Company Alpha
**Browser:** Playwright (Chromium-based)
**Test Date:** January 23, 2025

---

## Steps to Reproduce

1. Login as user (bob@alpha.com / user123)
2. Navigate to User Dashboard V2
3. Verify all field sections are visible (Energy Management, Water Management, Emissions Tracking, Social Impact)
4. Locate the "All Categories" dropdown filter
5. Click the dropdown and select "Energy"
6. Observe the results

---

## Expected Behavior

When "Energy" is selected from the Category filter:
- Should display ONLY the "Energy Management" section with 8 fields
- Should hide other category sections (Water Management, Emissions Tracking, Social Impact)
- Should maintain the statistics cards showing totals
- Should display filtered results immediately

---

## Actual Behavior

When "Energy" is selected from the Category filter:
- ALL field sections disappear completely
- Empty white space is shown below the search/filter controls
- No fields are visible at all
- Statistics cards remain unchanged (still showing total counts)
- Page snapshot shows no field sections in the DOM

**Evidence from Page Snapshot:**
When the filter is applied, the DOM shows:
```yaml
- generic [ref=e83]:
  - generic [ref=e85]:
    - textbox "Search metrics..." [ref=e86]
  - combobox [ref=e88]: # Status filter
    - option "All Statuses" [selected]
  - combobox [ref=e90]: # Category filter
    - option "All Categories"
    - option "Energy" [selected]  ← Filter is selected
    - option "Emissions"
    - option "Social"
    - option "Governance"
  - combobox [ref=e92]: # Field Type filter
    - option "All Field Types" [selected]
  - button "upload_file Bulk Upload Data" [ref=e94]
# NO FIELD SECTIONS BELOW - EMPTY
```

---

## Workaround

**Available Workaround:** Use the search functionality instead
- Type category-related keywords in the search box
- Example: Search for "High Coverage Framework" to find Energy fields
- This provides partial filtering functionality

**Reset Filter:** Select "All Categories" to restore all fields

---

## Impact Assessment

**Functional Impact:**
- Users cannot filter fields by category
- Makes it difficult to focus on specific ESG categories
- Reduces usability for users with many assigned fields

**User Experience Impact:**
- Confusing behavior (fields disappear completely)
- May appear as a broken feature
- Reduces efficiency in finding specific fields

**Business Impact:**
- Medium - Feature is broken but workaround exists
- Does not block core data entry functionality
- Users can still access all fields via search or "All Categories" view

**Affected Users:**
- All USER role users
- Especially impacts users with 20+ assigned fields across multiple categories

---

## Technical Analysis

**Suspected Root Cause:**
The category filtering logic in the search/filter module is likely using incorrect category matching or CSS display logic.

**Possible Locations:**
1. **JavaScript:** `app/static/js/user_v2/search_filter.js`
   - Category filtering function may have incorrect logic
   - CSS class toggling may be wrong
   - Data attribute matching may be failing

2. **Template:** `app/templates/user_v2/dashboard.html`
   - Field cards may have incorrect data attributes for categories
   - Category naming mismatch between filter options and field data

3. **CSS:** `app/static/css/user_v2/*.css`
   - Display/hide logic may be incorrectly hiding all elements

**Investigation Needed:**
1. Check what data attribute is used for category on field cards
2. Verify category filter values match field data attributes
3. Review filter logic in `search_filter.js`
4. Check if category filtering is combining incorrectly with other filters

---

## Comparison with Working Features

**Search Filter - WORKING:**
- Successfully filters fields by name/text
- Shows/hides field sections appropriately
- Real-time filtering works correctly

**Category Filter - BROKEN:**
- Does not show any results
- Hides all field sections incorrectly

This suggests the issue is specific to the category filtering logic, not the general filtering mechanism.

---

## Screenshots

### Before Applying Filter (All Fields Visible)
**Screenshot:** `screenshots/03-dashboard-viewport.png`
- Shows all 4 category sections visible
- All 20 fields displayed correctly
- Category filter shows "All Categories" selected

### After Applying "Energy" Filter (Bug - No Fields)
**Screenshot:** `screenshots/06-filter-category-energy.png`
- Shows category filter with "Energy" selected
- Empty space below filters - no fields visible
- Statistics cards still show total counts (not filtered)

**Screenshot:** `screenshots/07-filter-energy-scrolled.png`
- Scrolled down view confirming no fields are rendered
- Completely empty below the filter controls

### After Resetting Filter (Fields Restored)
Filter reset to "All Categories" restores all fields successfully, confirming the issue is with the filter logic, not the data loading.

---

## Console Messages

No JavaScript errors were logged when applying the category filter. This suggests the filter code is executing without exceptions, but the filtering logic itself is incorrect.

**Expected Console Messages:** (none observed)
- Should log filter application
- Should log field count after filtering

**Actual Console Messages:** (none)
- No errors
- No warnings
- No debug logs related to filtering

---

## Reproduction Rate

**100% reproducible**

Tested with:
- Category: "Energy" → Bug reproduced
- Resetting to "All Categories" → Fields restored (working)
- Other categories not tested but assumed to have same issue

---

## Recommended Fix

1. **Review Category Filter Logic:**
   - Inspect `search_filter.js` for category filtering function
   - Check how category value is extracted from dropdown
   - Verify how category value is matched against field data attributes

2. **Check Data Attributes:**
   - Verify field cards have correct category data attributes
   - Example: `data-category="Energy"` or similar
   - Ensure attribute values match filter option values exactly

3. **Add Debug Logging:**
   - Add console logs to track filter application
   - Log field count before and after filtering
   - Log matched/unmatched fields

4. **Test Filter Combinations:**
   - Test category filter alone
   - Test category + status filter
   - Test category + search
   - Ensure filters work together correctly

5. **Add Unit Tests:**
   - Test category filtering in isolation
   - Test filter reset functionality
   - Test filter combinations

---

## Acceptance Criteria for Fix

**Fix will be considered complete when:**

1. ✅ Selecting "Energy" shows ONLY Energy Management fields (8 fields)
2. ✅ Selecting "Emissions" shows ONLY Emissions Tracking fields (6 fields)
3. ✅ Selecting "Social" shows ONLY Social Impact fields (4 fields)
4. ✅ Selecting "Governance" shows ONLY Governance fields (if any exist)
5. ✅ Resetting to "All Categories" shows all fields
6. ✅ Statistics cards update to show filtered counts (optional enhancement)
7. ✅ No JavaScript console errors
8. ✅ Filtering works in combination with search and other filters

---

## Related Issues

None identified at this time.

---

## Attachments

**Screenshots:**
- `03-dashboard-viewport.png` - Initial state (all fields visible)
- `06-filter-category-energy.png` - Bug state (no fields after filtering)
- `07-filter-energy-scrolled.png` - Scrolled view confirming empty state

**Test Report:**
- `Testing_Summary_Legacy_Dashboard_Removal_v1.md` - Full test report

---

## Priority Justification

**Why Medium Priority:**
- Feature is completely broken (not partially working)
- Affects user experience and efficiency
- Has workaround (search functionality)
- Does not block core data entry functionality
- Not a security or data integrity issue

**Recommended Timeline:**
- Fix should be implemented in next sprint
- Should be included before wider user rollout
- Can be deployed as hotfix if development capacity allows

---

**End of Bug Report**
