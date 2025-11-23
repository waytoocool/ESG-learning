# Automated Validation Engine - Requirements & Specifications

**Feature:** Automated Data Validation System
**Project Start Date:** 2025-11-20
**Status:** Planning Phase
**Priority:** High

---

## 📋 Executive Summary

Implement an automated validation engine that runs pre-checks on ESG data submissions before they reach the checker queue. The system will validate data quality, detect anomalies through historical trend analysis, check computed field impacts, and require user acknowledgment of warnings before final submission.

---

## 🎯 Business Objectives

1. **Data Quality Assurance**: Catch data entry errors and anomalies before review
2. **Checker Efficiency**: Provide checkers with context and validation flags to prioritize reviews
3. **User Accountability**: Require users to acknowledge and explain significant deviations
4. **Compliance Support**: Maintain audit trail of validation warnings and user explanations

---

## 🔧 Core Requirements

### **1. Validation Checks to Implement**

#### **A. Required Attachments Validation**
- **Purpose**: Ensure supporting documents are uploaded when required
- **Configuration**: Field-level setting during data point assignment
- **Behavior**: Warn if attachment missing for fields flagged as requiring attachments
- **Severity**: Warning (does not block submission)

#### **B. Historical Trend Analysis**
- **Purpose**: Detect anomalies by comparing with historical values
- **Configuration**: Company-level threshold percentage (default: 20%)
- **Comparison Logic**:
  - Compare with last 2 sequential periods
  - Compare with same period last year (seasonal comparison)
  - Smart frequency handling:
    - Monthly: Compare with previous 2 months + same month last year
    - Quarterly: Compare with previous 2 quarters + same quarter last year
    - Annual: Compare with previous 2 years
- **Behavior**: Warn if variance exceeds threshold percentage
- **Severity**: Warning (does not block submission)

#### **C. Computed Field Impact Validation**
- **Purpose**: Validate impact on computed fields when dependency values change
- **Configuration**: Automatic (no configuration required)
- **Behavior**:
  1. Detect if submitted field is a dependency for any computed field
  2. Calculate projected computed field value with new dependency data
  3. Run trend analysis on projected computed field value
  4. Warn if projected value causes significant change in computed field
- **Validation Timing**: Pre-save (along with other validations)
- **Edge Case Handling**: Skip validation if computed field has incomplete dependencies
- **Severity**: Warning (does not block submission)

---

### **2. User Experience Flow**

#### **Current Flow (Before Validation)**
```
User fills form → Clicks "Save" → Data saved → Success message
```

#### **New Flow (With Validation)**
```
User fills form → Clicks "Save"
                     ↓
         Run All Validation Checks
                     ↓
    ┌────────────────┴────────────────┐
    ↓                                  ↓
  ✅ All Pass                     ⚠️ Warnings Found
    ↓                                  ↓
Save & Success              Show Validation Modal
                                       ↓
                          ┌────────────┴───────────┐
                          ↓                        ↓
                    User Reviews          User Cancels Edit
                  Adds Explanation              ↓
                       Notes              Back to Form
                          ↓
                  Clicks "Review & Submit"
                          ↓
                  Data Saved with:
                  - Validation results (JSON)
                  - User's explanation notes
                  - review_status = "pending_review"
                          ↓
                  Goes to Checker Queue
```

---

### **3. Validation Modal Behavior**

#### **Display Requirements**
- Group similar warnings together (e.g., all trend warnings in one section)
- Show validation context (historical values, variance percentages, thresholds)
- Provide suggested explanations to guide user
- Allow user to add explanation notes (required when warnings present)
- Character counter for notes field (max: 2000 characters)

#### **User Actions**
- **Cancel**: Return to form without saving
- **Review & Submit**: Save data with validation results and user notes

#### **Post-Submission Behavior**
- Data remains editable (same as current behavior)
- Re-validation occurs on every save (new submissions and updates)
- Validation results are overwritten with latest results

---

### **4. Edge Case Handling**

| Scenario | Behavior |
|----------|----------|
| **No Historical Data** | Show INFO message: "ℹ️ No historical data available for comparison. This is your first submission for this period." |
| **Incomplete Computed Field Dependencies** | Skip computed field validation (cannot calculate without all dependencies) |
| **Dimensional Data** | Compare both total aggregated values AND individual dimensions; show all warnings that exceed threshold |
| **Multiple Warnings** | Group similar warnings together in validation modal |
| **Update Existing Data** | Always validate on save (same as new submissions) |

---

## 📊 Database Schema Changes

### **1. Company Model Enhancement**
```python
class Company:
    # Add validation threshold configuration
    validation_trend_threshold_pct = db.Column(db.Float, default=20.0)
    # Default: Flag submissions that change by more than 20%
```

### **2. DataPointAssignment Model Enhancement**
```python
class DataPointAssignment:
    # Add attachment requirement flag
    attachment_required = db.Column(db.Boolean, default=False)
    # Set during data point assignment (same as frequency)
    # Applies to all entities with this field assignment
```

### **3. ESGData Model Enhancement**
```python
class ESGData:
    # Validation and review workflow fields
    review_status = db.Column(
        db.Enum('draft', 'submitted', 'auto_approved', 'pending_review',
                'approved', 'rejected', 'needs_revision', name='review_status_type'),
        default='draft',
        nullable=False
    )
    submitted_at = db.Column(db.DateTime, nullable=True)

    # Validation results storage (JSON)
    validation_results = db.Column(db.JSON, nullable=True)
    # Structure: {
    #   "timestamp": "2024-12-31T10:30:00Z",
    #   "passed": false,
    #   "risk_score": 35,
    #   "flags": [
    #     {
    #       "type": "trend_variance",
    #       "severity": "warning",
    #       "message": "Value increased 25% vs Nov 2024",
    #       "details": {...}
    #     }
    #   ]
    # }
```

### **4. AuditLog Enhancement**
```python
class AuditLog:
    # Add validation-related action types
    action_type = db.Column(db.Enum(
        # ... existing types ...
        'Data_Submitted',
        'Validation_Passed',
        'Validation_Warning',
        'Validation_Failed',
        'User_Acknowledged_Warning',
        name='audit_action_type'
    ))
```

---

## 🔐 Configuration Approach

### **Company-Level Configuration**
- **Location**: Company Settings page
- **Setting**: Validation trend threshold percentage
- **Default**: 20%
- **Configurable By**: ADMIN role

### **Field-Level Configuration**
- **Location**: Assign Data Points modal (same dialog as frequency selection)
- **Setting**: Require Attachment checkbox
- **Scope**: Applies to all entity assignments for this field
- **Configurable By**: ADMIN role during data point assignment

### **Hardcoded Defaults**
- Comparison lookback periods: 2
- Seasonal comparison: Enabled (same period last year)
- Validation timing: Pre-save (on Save button click)
- Predefined rule types only (no custom rules)

---

## 🎨 UI Changes Required

### **1. Admin UI Changes**

#### **Company Settings Page**
Add new section:
```
┌─────────────────────────────────────────────────┐
│  Validation Settings                            │
├─────────────────────────────────────────────────┤
│  Trend Variance Threshold: [20] %              │
│  Flag submissions that change by more than X%   │
│                                                 │
│  ℹ️ Data submissions exceeding this threshold  │
│     will require explanation from users.        │
└─────────────────────────────────────────────────┘
```

#### **Assign Data Points Modal**
Add checkbox after frequency selection:
```
┌─────────────────────────────────────────────────┐
│  Configure Assignment                           │
├─────────────────────────────────────────────────┤
│  Frequency: [Annual ▼] [Monthly] [Quarterly]   │
│                                                 │
│  Fiscal Year: [2024 ▼]                         │
│                                                 │
│  ☑ Require attachment for this field           │  ← NEW
│  📎 Supporting documents will be mandatory      │
│                                                 │
│  [Assign] [Cancel]                             │
└─────────────────────────────────────────────────┘
```

### **2. User UI Changes**

#### **Validation Warning Modal**
New modal component shown when validation warnings detected:
```
┌─────────────────────────────────────────────────────────┐
│  ⚠️  Validation Warnings                          [×]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Please review the following issues:                   │
│                                                         │
│  ⚠️ Trend Analysis Warnings                            │
│  • Value increased 25% vs Nov 2024 (1200 → 1500)      │
│  • Value increased 30% vs Dec 2023 (1150 → 1500)      │
│                                                         │
│  Previous values:                                       │
│  • Nov 2024: 1200 tonnes                               │
│  • Oct 2024: 1180 tonnes                               │
│  • Dec 2023 (same month last year): 1150 tonnes        │
│                                                         │
│  ⚠️ Computed Field Impact                              │
│  • This change will increase Total Emissions by 22%    │
│    (8000 → 9760 tonnes)                                │
│                                                         │
│  📎 Missing Attachment                                 │
│  • Supporting document is required for this field      │
│                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                                         │
│  📝 Please explain these changes: *                    │
│  ┌───────────────────────────────────────────────┐    │
│  │ New facility opened in December, increasing   │    │
│  │ production capacity and emissions output.     │    │
│  │                                                │    │
│  │                                                │    │
│  └───────────────────────────────────────────────┘    │
│  128 / 2000 characters                                 │
│                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                                         │
│  [Cancel]                    [Review & Submit]         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Integration Points

### **Existing Systems**
1. **ESG Data Entry**: Integrate validation on Save button click
2. **Computed Fields System**: Leverage existing dependency tracking
3. **Assignment Versioning**: Use existing assignment resolution logic
4. **Audit Logging**: Add validation events to audit trail

### **Future Systems (Out of Scope)**
1. **Checker Dashboard**: Will consume validation results from ESGData.validation_results
2. **Review Workflow**: Will use review_status field for workflow management
3. **Data Locking**: Post-approval data locking (future phase)

---

## ✅ Success Criteria

1. **Functional**:
   - All three validation checks (attachments, trends, computed fields) working correctly
   - Validation modal displays grouped warnings with context
   - User can add explanation notes and submit
   - Validation results stored in database
   - Audit trail captures validation events

2. **Performance**:
   - Validation completes in < 2 seconds for typical submission
   - No impact on page load times
   - Efficient database queries for historical data

3. **User Experience**:
   - Clear, actionable warning messages
   - Helpful context (historical values, variance percentages)
   - Smooth modal interaction (no page reloads)
   - Maintains existing edit/resubmit workflows

4. **Configuration**:
   - Admin can easily configure company threshold
   - Admin can set attachment requirements during assignment
   - No complex rule configuration required

---

## 🚫 Out of Scope

1. **Auto-Approval**: All submissions go to checker queue (no auto-approval path)
2. **Blocking Validation**: Validation warnings do not prevent submission
3. **Custom Rules**: Only predefined validation types (no custom JavaScript/Python rules)
4. **Range/Threshold Checks**: Too cumbersome to configure per field
5. **Data Type Validation**: Already handled in UI input controls
6. **Checker Dashboard**: Future phase (separate implementation)
7. **Review Workflow UI**: Future phase (separate implementation)

---

## 📚 Related Documentation

- **Implementation Plan**: `backend-developer/implementation-plan.md`
- **Testing Manual**: `testing-manual.md`
- **CLAUDE.md**: Main project documentation

---

## 📝 Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-11-20 | Claude Code | Initial requirements document created |

---

## ✅ Sign-off

- [ ] Requirements reviewed by stakeholder
- [ ] Technical approach validated
- [ ] Edge cases documented
- [ ] Ready for implementation
