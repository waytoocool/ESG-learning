# ISSUE REPORT: Duplicate Material Topics

**Issue ID**: CRITICAL-001
**Date**: 2025-01-29
**Reporter**: UI Testing Agent
**Severity**: **HIGH PRIORITY** 🔴
**Status**: **CONFIRMED** ✅

## Issue Summary

Material topics with identical names appear multiple times in the assign data points interface, causing user confusion and potential data integrity issues.

## Problem Description

### Visual Symptoms
1. **Topic Hierarchy (Left Panel)**: "Energy Management" appears twice in the topic tree
2. **Selected Data Points (Right Panel)**: Multiple instances of same-named topics appear with different field counts
3. **User Impact**: Users cannot distinguish between different framework contexts

### Specific Duplicates Identified

#### Energy Management (Confirmed Duplicate)
- **Instance 1**: Custom ESG Framework
  - Topic ID: `0fd588de-6ba1-4062-99f3-88a28d9c3654`
  - Field Count: 2
- **Instance 2**: High Coverage Framework
  - Topic ID: `a94f328f-2fdd-4360-b7b8-3571775ee3d2`
  - Field Count: 10

#### Social Impact (Visual Duplication)
- Appears 4 times in selected data points list
- Multiple instances marked as "Social Impact (Framework)"
- Different field counts for each instance

## Technical Root Cause

### API Analysis
**Endpoint**: `/admin/frameworks/all_topics_tree`
**Problem**: Returns topics with identical names from different frameworks without proper context or deduplication

**API Response Data**:
```json
{
  "totalTopics": 11,
  "uniqueNames": 10,
  "duplicateNames": ["Energy Management"]
}
```

### Frontend Behavior
- Frontend renders each API response topic as separate UI element
- No framework context displayed in topic names
- No deduplication logic implemented

## Impact Assessment

### User Experience Impact
- ❌ **Confusing Interface**: Users see duplicate topic names without context
- ❌ **Wrong Selection Risk**: Users may select wrong framework's topic
- ❌ **Workflow Disruption**: Admins waste time identifying correct topics

### Data Integrity Impact
- ❌ **Assignment Errors**: Risk of assigning to wrong framework topic
- ❌ **Reporting Inconsistencies**: Mixed data from different frameworks
- ❌ **Audit Trail Issues**: Unclear which framework topic was selected

## Evidence Screenshots

1. **`duplicate-topics-and-gear-icons.png`**: Shows "Energy Management" appearing twice in left panel
2. **`current-assign-data-points-state.png`**: Full page view showing multiple "Social Impact" instances

## Reproduction Steps

1. Navigate to `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2`
2. Login as admin user
3. Observe left panel "Topic Hierarchy"
4. **Expected**: Each topic name appears once with framework context
5. **Actual**: "Energy Management" appears twice without framework distinction

## Proposed Solutions

### Option 1: Backend API Enhancement (Recommended)
**Modify `/admin/frameworks/all_topics_tree` endpoint:**
- Add framework name to topic display name
- Format: `"Energy Management (Custom ESG Framework)"`
- Format: `"Energy Management (High Coverage Framework)"`

### Option 2: Frontend Deduplication
**Update topic rendering logic:**
- Group topics by name
- Show framework source as subtitle
- Allow expansion to see framework-specific instances

### Option 3: Database Review
**Data integrity check:**
- Review if topics should be framework-unique
- Consider unique constraints on (topic_name, framework_id)
- Implement proper topic hierarchy

## Acceptance Criteria for Fix

✅ **Primary**: No duplicate topic names visible in UI without framework context
✅ **Secondary**: Users can clearly distinguish between same-named topics from different frameworks
✅ **Tertiary**: No impact on existing topic assignments or data integrity

## Priority Justification

**HIGH PRIORITY** because:
- Directly impacts core admin workflow
- Risk of data assignment errors
- Affects data quality and reporting
- User experience degradation

## Next Steps

1. **Immediate**: Escalate to product-manager-agent for priority assignment
2. **Backend**: Assign to backend developer for API endpoint modification
3. **Testing**: Schedule regression testing after fix implementation
4. **Documentation**: Update user guides with new topic display format

---

**Issue Status**: ✅ **Ready for Development Assignment**
**Estimated Fix Complexity**: **Medium** (Backend API change + Frontend display update)