# Phase 2 Manual Testing Guide
## Dimension Configuration - Assign Data Points

**Purpose:** Quick reference for manual UI validation of Phase 2 features

---

## Test Environment Setup

**URL:** http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points
**Login Credentials:** alice@alpha.com / admin123
**Browser:** Chrome, Firefox, or Safari (latest version recommended)

---

## Quick Test Checklist (5 minutes)

### 1. Page Load Test ✅
- [ ] Page loads without errors
- [ ] Open browser console (F12) - verify no red errors
- [ ] Look for console log: `[AppMain] DimensionModule initialized`

### 2. UI Elements Test ✅
- [ ] Each field card shows a "Manage Dimensions" button (layer-group icon)
- [ ] Button is styled consistently with other action buttons

### 3. Modal Open Test ✅
- [ ] Click "Manage Dimensions" on any field card
- [ ] Modal opens with title showing field name
- [ ] Modal shows two sections:
  - "Assigned Dimensions" (may be empty)
  - "Available Dimensions" (should show "Gender" and "Age")

### 4. Assign Dimension Test ✅
- [ ] In modal, find "Gender" in Available Dimensions
- [ ] Click "Assign" button next to "Gender"
- [ ] Verify "Gender" moves to Assigned Dimensions section
- [ ] Close modal
- [ ] Verify a badge appears on the field card showing "Gender"

### 5. Badge Tooltip Test ✅
- [ ] Hover over the "Gender" badge
- [ ] Verify tooltip appears showing dimension values (Male, Female)

### 6. Remove Dimension Test ✅
- [ ] Open modal again for the same field
- [ ] Find "Gender" in Assigned Dimensions section
- [ ] Click "Remove" button
- [ ] Verify "Gender" moves back to Available Dimensions
- [ ] Close modal
- [ ] Verify badge disappears from field card

---

## Comprehensive Test Suite (15 minutes)

### Test 1: Assign Multiple Dimensions

**Steps:**
1. Click "Manage Dimensions" on "Total new hires" field
2. Assign both "Gender" and "Age" dimensions
3. Verify both badges appear on field card
4. Hover over each badge to see values

**Expected Result:**
- Two badges visible: "Gender" and "Age"
- Tooltips show correct values

---

### Test 2: Create New Dimension

**Steps:**
1. Click "Manage Dimensions" on any field
2. Scroll to "Create New Dimension" section at bottom of modal
3. Fill in:
   - Name: "Department"
   - Description: "Employee department breakdown"
   - Values: "IT, Finance, HR, Operations" (comma-separated)
4. Click "Create Dimension" button

**Expected Result:**
- Success message appears
- "Department" immediately appears in Available Dimensions list
- Can now assign "Department" to fields

---

### Test 3: Computed Field Validation

**Prerequisites:** Need a computed field that depends on raw fields

**Steps:**
1. Identify a computed field (look for formula icon or "Computed" label)
2. Click "Manage Dimensions" on the computed field
3. Try to assign a dimension (e.g., "Gender")

**Expected Result:**
- If dependencies don't have "Gender", validation error appears
- Error message lists which dependencies are missing the dimension
- Assignment is blocked until dependencies have required dimensions

**Validation Rule:**
> Computed fields can only have dimensions that ALL their dependencies also have

---

### Test 4: Prevent Invalid Removal

**Steps:**
1. Assign "Gender" to a raw field (e.g., "Total employees")
2. Assign "Gender" to a computed field that uses the raw field
3. Try to remove "Gender" from the raw field

**Expected Result:**
- Validation error appears
- Error message shows which computed fields require this dimension
- Removal is blocked

**Validation Rule:**
> Cannot remove a dimension from a raw field if computed fields require it

---

### Test 5: Integration with Existing Features

**Steps:**
1. Perform dimension operations (assign/remove)
2. Test existing features:
   - Configuration modal (frequency, fiscal year)
   - Entity assignment
   - Field removal
   - Search/filter

**Expected Result:**
- All existing features work normally
- No conflicts or broken functionality
- Dimension features integrate seamlessly

---

## Fields with Pre-Existing Dimensions

These fields already have dimensions assigned (good for testing):

1. **Total number of employees**
   - Dimensions: Age, Gender
   - Framework: Complete Framework

2. **Total new hires**
   - Dimensions: Gender, Age
   - Framework: Complete Framework

3. **Total employee turnover**
   - Dimensions: Gender, Age
   - Framework: Complete Framework

---

## Console Log Reference

### Success Indicators
```
[AppMain] DimensionModule initialized
[DimensionModule] Initializing dimension management for Assign Data Points...
[DimensionManagerShared] Initialized with context: assign-data-points
[DimensionModule] Shared component initialized successfully
[DimensionModule] Event listeners attached for dimension buttons
[DimensionModule] Initialization complete
```

### Error Indicators (should NOT see these)
```
[ERROR] Cannot import DimensionModule
[ERROR] Failed to load dimensions
[ERROR] API endpoint returned 404
DimensionModule is not defined
```

---

## API Endpoint Testing (Developer)

### Check Dimensions for Company
```bash
curl -X GET http://test-company-alpha.127-0-0-1.nip.io:8000/admin/dimensions \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

### Get Field Dimensions
```bash
curl -X GET http://test-company-alpha.127-0-0-1.nip.io:8000/admin/fields/{field_id}/dimensions \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

### Assign Dimension to Field
```bash
curl -X POST http://test-company-alpha.127-0-0-1.nip.io:8000/admin/fields/{field_id}/dimensions \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{"dimension_ids": ["dimension_id_1", "dimension_id_2"]}'
```

---

## Troubleshooting

### Modal doesn't open
- Check console for errors
- Verify DimensionModule initialized
- Check if JavaScript files loaded (Network tab)

### "Failed to load dimensions" error
- Check backend is running
- Verify API endpoints return 200 (not 404)
- Check browser console for specific error

### Badges don't appear
- Verify dimension was actually assigned (check modal)
- Check console for rendering errors
- Inspect badge container element in DOM

### Tooltips don't show
- Ensure badges rendered successfully first
- Check if tooltip CSS loaded
- Verify dimension has values

---

## Performance Expectations

| Action | Expected Time |
|--------|---------------|
| Page load | < 3 seconds |
| Modal open | < 500ms |
| Assign dimension | < 300ms |
| Badge render | < 100ms |
| Tooltip show | Instant |

---

## Browser Compatibility

**Minimum Versions:**
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

**Not Supported:**
- Internet Explorer (any version)

---

## Test Data Reference

**Available Dimensions:**
1. Gender
   - Values: Male, Female
2. Age
   - Values: Age <=30, 30 < Age <= 50, Age > 50

**Test Company:** Test Company Alpha
**Admin User:** alice@alpha.com / admin123

---

## Reporting Issues

If you find any issues during manual testing:

1. **Take a screenshot** showing the issue
2. **Check browser console** for error messages (F12 → Console tab)
3. **Note the steps** to reproduce
4. **Record browser version** and OS

Include in bug report:
- URL where issue occurred
- User role (ADMIN)
- Steps to reproduce
- Expected vs actual behavior
- Screenshot + console logs

---

**Document Version:** 1.0
**Last Updated:** 2025-01-20
**Status:** Ready for Manual Testing
