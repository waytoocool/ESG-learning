# Material Topics Not Loading in Configuration Modal - Bug Report

**Date**: 2025-10-02
**Tested By**: UI Testing Agent
**Feature**: Assign Data Points - Configuration Modal
**Bug Severity**: HIGH
**Status**: CONFIRMED

---

## Executive Summary

Material topics are successfully fetched from the backend API (`/admin/topics/company_dropdown`) but are NOT being populated into the "Assign Material Topic" dropdown when the Configuration Modal opens. The API returns 5 valid topics, but the dropdown only shows placeholder options.

---

## Test Environment

- **URL**: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2
- **User**: alice@alpha.com (ADMIN)
- **Company**: Test Company Alpha
- **Browser**: Playwright (Chromium)

---

## Steps to Reproduce

1. Navigate to the Assign Data Points page
2. Select at least one data point by checking its checkbox
3. Click the "Configure Selected" button
4. Observe the "Assign Material Topic" dropdown in the opened modal
5. Note that it only shows:
   - "Select a material topic..."
   - "── Framework Topics ──" (disabled)

---

## Expected Behavior

The "Assign Material Topic" dropdown should be populated with 5 company topics:
1. Emissions Tracking
2. Energy Management
3. Social Impact
4. Waste Management
5. Water Management

---

## Actual Behavior

The dropdown only shows 2 placeholder options and NO actual topics, despite the API successfully returning topic data.

---

## Technical Analysis

### 1. API Call Status: SUCCESS ✓

**Evidence from Network Tab:**
```
GET http://test-company-alpha.127-0-0-1.nip.io:8000/admin/topics/company_dropdown => [200] OK
```

The API call IS being made and returns successfully with status 200.

### 2. API Response: VALID ✓

**Manual API Test Result:**
```javascript
window.ServicesModule.loadCompanyTopics()
```

**Response:**
```json
{
  "success": true,
  "count": 5,
  "topics": [
    {
      "topic_id": "151be653-36c3-48f1-8392-0db217241901",
      "name": "Emissions Tracking",
      "display_name": "Emissions Tracking",
      "description": "Topic for Emissions Tracking",
      "level": 0,
      "full_path": "Emissions Tracking"
    },
    {
      "topic_id": "23681103-0523-4645-ae5e-7fa31da273e9",
      "name": "Energy Management",
      "display_name": "Energy Management",
      "description": "Topic for Energy Management",
      "level": 0,
      "full_path": "Energy Management"
    },
    {
      "topic_id": "10d17af2-dc40-49e9-b298-88d507cc2e31",
      "name": "Social Impact",
      "display_name": "Social Impact",
      "description": "Topic for Social Impact",
      "level": 0,
      "full_path": "Social Impact"
    },
    {
      "topic_id": "c5172fff-ae0e-4144-ba65-2832ef946176",
      "name": "Waste Management",
      "display_name": "Waste Management",
      "description": "Topic for Waste Management",
      "level": 0,
      "full_path": "Waste Management"
    },
    {
      "topic_id": "159ddf81-09e4-46b0-971c-712685d3148d",
      "name": "Water Management",
      "display_name": "Water Management",
      "description": "Topic for Water Management",
      "level": 0,
      "full_path": "Water Management"
    }
  ]
}
```

### 3. DOM Element Status: EXISTS ✓

**Dropdown Element:**
```javascript
document.getElementById('modalTopicSelect')
```
- Element exists: TRUE
- Element ID: `modalTopicSelect`
- Current option count: 2 (only placeholders)

**Current HTML:**
```html
<select id="modalTopicSelect" class="form-select">
    <option value="">Select a material topic...</option>
    <option value="framework_topic" disabled="">── Framework Topics ──</option>
    <!-- Options populated by JavaScript -->
</select>
```

### 4. JavaScript Module Status: LOADED ✓

```javascript
typeof window.ServicesModule // "object"
typeof window.ServicesModule.loadCompanyTopics // "function"
```

Both the ServicesModule and the `loadCompanyTopics` function exist and are callable.

---

## Root Cause Analysis

### Problem: Missing DOM Population Logic

**Location**: `/app/static/js/admin/assign_data_points/PopupsModule.js`

**Analysis**:

1. **Current Code Flow**:
   ```javascript
   showConfigurationModal()
     → analyzeCurrentConfigurations()
       → populateModalWithCurrentConfig()
   ```

2. **Issue Identified**:
   - The `showConfigurationModal()` function (line 284) does NOT call any method to load company topics into the dropdown
   - The `populateModalWithCurrentConfig()` function (line 378) only sets existing values but doesn't populate options
   - There is NO initialization code to load topics when the modal opens

3. **Missing Code**:
   - No call to `window.ServicesModule.loadCompanyTopics()` when modal opens
   - No DOM manipulation to populate the `<select id="modalTopicSelect">` with topic options
   - No event listener to load topics on modal show

### Expected Implementation

The PopupsModule should include topic loading logic similar to this pattern:

```javascript
async showConfigurationModal(dataPoints, selectedCount) {
    // ... existing code ...

    // MISSING: Load company topics and populate dropdown
    await this.loadAndPopulateTopics();

    // ... rest of code ...
}

async loadAndPopulateTopics() {
    if (!this.elements.modalTopicSelect) return;

    try {
        const response = await window.ServicesModule.loadCompanyTopics();

        if (response && response.success && response.topics) {
            // Clear existing options (keep placeholder)
            // Populate with actual topics
            response.topics.forEach(topic => {
                const option = document.createElement('option');
                option.value = topic.topic_id;
                option.textContent = topic.display_name;
                this.elements.modalTopicSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('[PopupsModule] Error loading topics:', error);
    }
}
```

---

## Impact Assessment

### User Impact: HIGH
- Admins CANNOT assign material topics to data points through the UI
- This is a core feature for ESG reporting and materiality assessment
- Workaround: None available through UI

### Business Impact: HIGH
- Prevents proper organization of ESG data by material topics
- Blocks materiality assessment workflow
- Reduces data quality and reporting accuracy

### Technical Debt: MEDIUM
- Missing feature implementation rather than regression
- Affects only one module (PopupsModule)
- Does not affect other parts of the application

---

## Screenshots

### Screenshot 1: Configuration Modal with Empty Topics Dropdown
![Configuration Modal](screenshots/debug-material-topics-modal-open.png)

**Evidence**: The "Assign Material Topic" dropdown shows only placeholder options despite the Material Topic Assignment toggle being enabled (blue/on).

### Screenshot 2: Console Debug Output
Browser console shows that:
- API call succeeds
- `ServicesModule.loadCompanyTopics()` works correctly
- Topics are available but not rendered in UI

---

## Recommended Fix

**Priority**: HIGH
**Estimated Effort**: 2-4 hours

### Implementation Steps:

1. **Add topic loading method to PopupsModule**:
   - Location: `/app/static/js/admin/assign_data_points/PopupsModule.js`
   - Function: `async loadAndPopulateTopics()`

2. **Call topic loading when modal opens**:
   - Update `showConfigurationModal()` to await topic loading
   - Ensure topics are loaded BEFORE modal is displayed

3. **Handle topic selection state**:
   - Pre-select existing topics if editing
   - Support "Mixed topics" indicator for multi-select

4. **Add error handling**:
   - Show user-friendly message if topics fail to load
   - Provide retry mechanism

### Code Snippet Location

**File**: `/app/static/js/admin/assign_data_points/PopupsModule.js`
**Function**: `showConfigurationModal` (line 284)
**Missing Call**: After line 304, before modal.show() at line 311

---

## Verification Criteria

After fix is applied, verify:

1. ✓ Topics dropdown populates with all 5 company topics
2. ✓ Topics load before modal is displayed (no flash of empty dropdown)
3. ✓ Existing topic assignments are pre-selected correctly
4. ✓ "Mixed topics" state is handled for multi-selection
5. ✓ Error handling shows user-friendly message if load fails
6. ✓ Network tab shows single API call per modal open (no duplicate calls)
7. ✓ Selected topic is saved correctly when configuration is applied

---

## Additional Notes

- The ServicesModule already has a working `loadCompanyTopics()` method
- The API endpoint `/admin/topics/company_dropdown` is working correctly
- The issue is purely frontend DOM population logic
- No backend changes are required

---

## Related Files

1. `/app/static/js/admin/assign_data_points/PopupsModule.js` - Primary file requiring changes
2. `/app/static/js/admin/assign_data_points/ServicesModule.js` - Contains working `loadCompanyTopics()` method
3. `/app/routes/admin_dimensions.py` - Backend API endpoint (working correctly)

---

**Report Generated**: 2025-10-02
**Agent**: UI Testing Agent (Claude Development Team)
