# Computed Field Dependency Auto-Management Feature

**Feature ID:** CF-DEP-2025-11
**Start Date:** 2025-11-10
**Priority:** P0 (Critical)
**Status:** Planning

## 📋 Executive Summary

### Problem Statement
When administrators assign computed fields to entities in the ESG DataVault system, the raw input fields (dependencies) that feed into these computed fields are NOT automatically assigned. This results in:
- Computed fields that cannot calculate values
- Manual tracking burden on administrators
- Risk of incomplete data collection
- No visibility into field dependencies

### Solution Overview
Implement intelligent auto-cascade assignment system that automatically includes and manages dependencies when computed fields are assigned, with proper validation, visual feedback, and configuration management.

## 🎯 Business Requirements

### BR-1: Auto-Assignment of Dependencies
- **When** a computed field is selected for assignment
- **Then** all its raw field dependencies must be automatically selected
- **With** a notification to the user about auto-added dependencies

### BR-2: Deletion Protection
- **When** attempting to remove a raw field that is a dependency
- **Then** system must warn that it's used by computed fields
- **And** prevent deletion unless explicitly confirmed

### BR-3: Frequency Compatibility
- **Requirement:** Raw field frequency ≤ Computed field frequency
- **Examples:**
  - ✅ Raw: Monthly, Computed: Quarterly (can aggregate)
  - ❌ Raw: Annual, Computed: Monthly (cannot subdivide)

### BR-4: Entity Assignment Rules
- **Default:** Dependencies inherit same entities as computed field
- **Extension:** Dependencies can have additional entities
- **Restriction:** Dependencies must have AT LEAST the computed field's entities

### BR-5: Visual Clarity
- **Display** dependency relationships clearly
- **Show** computed field indicators
- **Provide** dependency tree visualization

## 🔧 Technical Requirements

### TR-1: Backend API Enhancements
```python
# New endpoints required:
POST /api/assignments/validate-dependencies
POST /api/assignments/get-dependencies
POST /api/assignments/check-removal-impact
GET  /api/assignments/dependency-tree/{field_id}
```

### TR-2: Database Integrity
- No schema changes required
- Leverage existing `field_variable_mappings` table
- Maintain referential integrity

### TR-3: Frontend State Management
- Extend `AppState` to track dependency relationships
- Add `dependencyMap` to track field relationships
- Implement cascade selection logic

### TR-4: Performance Requirements
- Dependency resolution < 100ms
- Tree view rendering < 200ms
- Validation checks < 50ms

## 📊 User Stories

### US-1: Admin Assigns Computed Field
**As an** Admin
**I want** dependencies to be auto-selected when I select a computed field
**So that** I don't have to manually track and add each dependency

**Acceptance Criteria:**
1. When selecting computed field "Employee Turnover Rate"
2. System auto-selects "Total Turnover" and "Total Employees"
3. Popup shows "Added 1 computed field + 2 dependencies"
4. All fields appear in selected panel

### US-2: Admin Reviews Dependencies
**As an** Admin
**I want** to see which fields are computed and their dependencies
**So that** I understand the data relationships

**Acceptance Criteria:**
1. Computed fields show calculator icon (🧮)
2. Hover shows "Depends on: Field A, Field B"
3. Dependency tree view available
4. Clear parent-child relationship display

### US-3: Admin Configures Fields
**As an** Admin
**I want** smart configuration inheritance
**So that** related fields have compatible settings

**Acceptance Criteria:**
1. Dependencies inherit computed field's frequency by default
2. Can override if frequency is compatible
3. Warning if incompatible frequency attempted
4. Entity assignment cascades appropriately

### US-4: Admin Removes Fields
**As an** Admin
**I want** protection against breaking dependencies
**So that** I don't accidentally break computed fields

**Acceptance Criteria:**
1. Warning when removing dependency field
2. Shows which computed fields would be affected
3. Requires explicit confirmation
4. Option to remove computed field too

## 🏗️ Architecture Design

### Component Interaction Flow
```
User Action → Frontend Handler → Validation → Backend API → Database
     ↓              ↓                ↓            ↓           ↓
   Click      State Update      Check Deps    Process     Update
     ↓              ↓                ↓            ↓           ↓
  Select      Auto-Select      Compatibility  Validate    Persist
```

### State Management Architecture
```javascript
AppState = {
  selectedDataPoints: Map<fieldId, fieldData>,
  dependencyMap: Map<computedFieldId, Set<dependencyFieldIds>>,
  reverseDependencyMap: Map<rawFieldId, Set<computedFieldIds>>,
  configurations: Map<fieldId, config>,
  validationState: {
    frequencyConflicts: [],
    missingDependencies: [],
    circularDependencies: []
  }
}
```

## 🚦 Implementation Phases

### Phase 1: Backend Foundation (Day 1)
- [ ] API endpoint for dependency validation
- [ ] API endpoint for dependency retrieval
- [ ] API endpoint for removal impact check
- [ ] Service layer methods for dependency management

### Phase 2: Frontend Auto-Selection (Day 1-2)
- [ ] Auto-cascade selection logic
- [ ] Notification system for auto-added fields
- [ ] State management updates
- [ ] Selection conflict resolution

### Phase 3: Visual Indicators (Day 2)
- [ ] Computed field badges/icons
- [ ] Dependency count display
- [ ] Tooltip enhancements
- [ ] Tree view component

### Phase 4: Configuration Management (Day 3)
- [ ] Frequency compatibility validation
- [ ] Entity assignment cascading
- [ ] Configuration inheritance logic
- [ ] Override mechanisms

### Phase 5: Protection & Validation (Day 3-4)
- [ ] Deletion protection system
- [ ] Pre-save validation
- [ ] Warning modals
- [ ] Confirmation dialogs

### Phase 6: Testing & Polish (Day 4)
- [ ] Comprehensive UI testing
- [ ] Edge case handling
- [ ] Performance optimization
- [ ] Documentation updates

## 🎨 UI/UX Specifications

### Visual Indicators
1. **Computed Field Badge:** 🧮 or ⚡ icon
2. **Dependency Count:** Small badge showing "(2 deps)"
3. **Status Colors:**
   - Green: All dependencies satisfied
   - Yellow: Configuration warning
   - Red: Missing dependencies

### Notification Messages
```javascript
// Success messages
"✅ Added 'Employee Turnover Rate' and 2 dependencies"
"✅ Configuration applied to all related fields"

// Warning messages
"⚠️ 'Total Employees' has Monthly frequency but 'Turnover Rate' needs Quarterly"
"⚠️ This field is required by 2 computed fields"

// Error messages
"❌ Cannot remove: Field is required by 'Employee Turnover Rate'"
"❌ Frequency conflict: Dependencies need higher frequency than computed field"
```

### Modal Designs
1. **Dependency Tree Modal**
   - Collapsible tree structure
   - Shows all relationships
   - Frequency/entity indicators

2. **Conflict Resolution Modal**
   - Clear explanation of conflict
   - Options to resolve
   - Impact preview

## ⚠️ Risk Assessment

### Risk 1: Performance Impact
**Mitigation:** Implement caching for dependency lookups

### Risk 2: User Confusion
**Mitigation:** Clear visual indicators and helpful messages

### Risk 3: Breaking Existing Workflows
**Mitigation:** Backward compatibility, optional overrides

### Risk 4: Complex Dependencies
**Mitigation:** Limit dependency depth, circular check

## 📈 Success Metrics

1. **Reduction in incomplete assignments:** Target 90% reduction
2. **Time to assign complex fields:** Target 50% reduction
3. **User errors:** Target 75% reduction
4. **Support tickets:** Target 60% reduction in dependency-related issues

## 🔄 Migration Strategy

### Existing Data
1. Scan existing assignments for orphaned computed fields
2. Generate report of missing dependencies
3. Offer bulk fix option for administrators

### Rollback Plan
1. Feature flag to enable/disable
2. Preserve manual assignment capability
3. Database changes are additive only

## 📚 Dependencies

### Technical Dependencies
- SQLAlchemy models
- Flask-Login for user context
- JavaScript AppState system
- Existing assignment APIs

### Business Dependencies
- Admin training materials update
- User documentation update
- Support team briefing

## 🎯 Definition of Done

- [ ] All test cases passing
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Performance benchmarks met
- [ ] Accessibility standards met
- [ ] Security review passed
- [ ] Deployed to staging
- [ ] User acceptance testing passed
- [ ] Production deployment successful

## 📞 Stakeholders

- **Product Owner:** Feature requirements and priorities
- **Development Team:** Implementation and testing
- **QA Team:** Test planning and execution
- **Support Team:** User training and documentation
- **End Users:** Company administrators

## 🗓️ Timeline

**Total Estimated Effort:** 4-5 days

| Day | Focus Area | Deliverables |
|-----|------------|--------------|
| 1 | Backend + Auto-selection | APIs, Core logic |
| 2 | Visual indicators + Tree view | UI components |
| 3 | Configuration + Protection | Smart features |
| 4 | Testing + Edge cases | Quality assurance |
| 5 | Documentation + Deployment | Release ready |

## 📝 Notes

- Priority on backward compatibility
- Focus on user education through UI
- Emphasis on preventing errors rather than fixing them
- Consider future enhancements for multi-level dependencies