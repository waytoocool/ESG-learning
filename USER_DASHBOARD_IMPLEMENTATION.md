# User Dashboard Implementation Plan

## Overview
Update user data entry interfaces to work with the new indefinite assignment system and assignment versioning. This implementation should be done AFTER the main assignment system is complete.

## Prerequisites
- Main assignment system implementation completed
- ESGData model has `assignment_id` field populated
- Company FY configuration is functional
- Assignment versioning system is operational

## Phase 1: Data Entry Interface Updates

### 1.1 Date Selection Logic Updates
- **Remove Year-Based Logic**: Update date pickers to use company FY configuration
- **Dynamic Date Ranges**: Calculate valid reporting periods based on:
  - Company's FY end month/day
  - Assignment frequency (Monthly/Quarterly/Annual)
  - Current date and available reporting periods
- **Assignment Resolution**: Show appropriate assignment based on selected date
- **Transition Handling**: Handle transitions between assignment versions seamlessly

### 1.2 Assignment-Based Data Entry
- **Update Data Entry Forms**: Use `assignment_id` instead of `field_id` for new entries
- **Backward Compatibility**: Support both `assignment_id` and `field_id` during transition
- **Version Awareness**: Ensure data entry uses correct assignment version for selected date
- **Validation Updates**: Update form validation to use assignment-based rules

## Phase 2: Data Retrieval Updates

### 2.1 Dashboard Data Queries
- **Update Data Loading**: Modify queries to use `assignment_id` primarily
- **Fallback Logic**: Maintain `field_id` fallback for existing data
- **Assignment Resolution**: Create service to resolve correct assignment for any date
- **Performance Optimization**: Optimize queries for assignment-based data retrieval

### 2.2 Data Display Logic
- **Version-Aware Display**: Show data according to the assignment version it was entered under
- **Historical Context**: Provide context when displaying data from different assignment versions
- **Frequency Indicators**: Show data collection frequency clearly to users
- **Data Series Continuity**: Handle display of data across different assignment versions

## Phase 3: User Experience Enhancements

### 3.1 Improved Date Selection
- **Smart Date Picker**: 
  - Show available reporting periods based on company FY
  - Highlight periods with existing data
  - Indicate periods with different assignment versions
  - Provide visual cues for data entry deadlines

### 3.2 Assignment Context Display
- **Current Assignment Info**: Show users which assignment version they're entering data for
- **Frequency Indicators**: Clear display of data collection frequency
- **Historical Data Access**: Allow users to view (but not edit) legacy assignment data
- **Change Notifications**: Inform users when assignment configurations have changed

## Phase 4: Data Consistency Features

### 4.1 Version Transition Handling
- **Seamless Transitions**: When assignments change mid-year, handle user experience gracefully
- **Data Migration Prompts**: If needed, prompt users about data entry changes
- **Legacy Data Access**: Provide read-only access to data from superseded assignments
- **Clear Messaging**: Explain to users when they're working with new vs historical assignments

### 4.2 Data Entry Validation
- **Assignment-Based Rules**: Validate data entry against current assignment configuration
- **Date Range Validation**: Ensure dates are valid for the assignment being used
- **Frequency Compliance**: Validate data entry frequency against assignment settings
- **Duplicate Prevention**: Prevent duplicate entries for same assignment/date combination

## Phase 5: Computed Fields Updates

### 5.1 Calculation Engine Updates  
- **Assignment-Aware Calculations**: Update computed field logic to work with assignment versioning
- **Cross-Version Dependencies**: Handle computed fields that depend on data from different assignment versions
- **Recalculation Logic**: Ensure computed fields recalculate when underlying assignments change
- **Historical Accuracy**: Maintain calculation accuracy across assignment version changes

### 5.2 Formula Resolution
- **Variable Mapping Updates**: Update variable mapping to use assignment-based resolution
- **Dependency Tracking**: Track dependencies across different assignment versions
- **Calculation History**: Maintain history of calculations across assignment changes
- **Error Handling**: Robust error handling for missing or changed assignments

## Phase 6: User Interface Polish

### 6.1 Dashboard Redesign Elements
- **Assignment Status Indicators**: Show current assignment status and versions
- **Data Series Overview**: Provide overview of data across different assignment versions
- **Historical Data Navigation**: Easy navigation between current and historical data
- **Progress Tracking**: Show data entry progress for current assignments

### 6.2 Mobile Responsiveness
- **Mobile Date Pickers**: Optimize date selection for mobile devices
- **Touch-Friendly Interface**: Ensure assignment-related UI elements work well on mobile
- **Responsive Data Tables**: Handle assignment version information in mobile layouts
- **Offline Capability**: Consider offline data entry with assignment version sync

## Phase 7: Advanced User Features

### 7.1 Data Export Capabilities
- **Assignment-Aware Exports**: Export data with assignment version information
- **Historical Data Exports**: Allow export of data across multiple assignment versions
- **Metadata Inclusion**: Include assignment configuration in data exports
- **Format Options**: Support various export formats with assignment context

### 7.2 Data Analysis Tools
- **Trend Analysis**: Show trends across assignment version changes
- **Comparison Tools**: Compare data between different assignment versions
- **Data Quality Indicators**: Show data quality metrics across assignment versions
- **Completeness Tracking**: Track data completeness for current assignments

## Technical Implementation Details

### Database Query Updates
```python
# Update user dashboard queries to use assignment_id
def get_user_data_for_period(user_id, start_date, end_date):
    # Use assignment resolution service
    assignments = resolve_assignments_for_period(user_id, start_date, end_date)
    # Query ESGData using assignment_id with field_id fallback
    return query_data_with_assignment_fallback(assignments, start_date, end_date)
```

### Assignment Resolution Service
```python
class AssignmentResolutionService:
    def get_active_assignment_for_date(self, field_id, entity_id, date):
        # Find active assignment for specific date
        # Handle assignment version transitions
        # Return appropriate assignment_id
        pass
    
    def get_user_assignments(self, user_id, date_range):
        # Get all assignments for user's entity within date range
        # Handle assignment version changes within period
        # Return assignment timeline
        pass
```

### Data Entry Form Updates
```python
# Update forms to use assignment_id
class ESGDataEntryForm:
    assignment_id = HiddenField()  # Instead of field_id
    reporting_date = DateField()
    # ... other fields
    
    def validate_assignment_date(self, field):
        # Validate date is appropriate for assignment
        # Check assignment is active for selected date
        pass
```

## Migration Strategy

### Phase A: Dual System Support
- Support both `field_id` and `assignment_id` in user interfaces
- Gradual migration of user workflows to assignment-based system
- Maintain backward compatibility for existing bookmarks/URLs

### Phase B: Assignment-First Approach
- Default to assignment-based logic for new data entry
- Use `field_id` only as fallback for historical data
- Update all user-facing interfaces to show assignment context

### Phase C: Complete Transition
- Remove `field_id` dependencies from user interface code
- Full assignment-based data entry and display
- Archive old field-based logic (after thorough testing)

## Testing Requirements

### User Workflow Testing
- Data entry with new assignment system
- Date selection and validation
- Assignment version transitions
- Historical data access
- Computed field calculations

### Performance Testing
- Dashboard loading with assignment resolution
- Data query performance with new schema
- Mobile interface responsiveness
- Large dataset handling

### User Acceptance Testing
- User experience with new date selection
- Understanding of assignment version changes  
- Data entry efficiency compared to old system
- Historical data accessibility

## Success Metrics
- User data entry time remains same or improves
- Zero data entry errors due to assignment system
- User satisfaction with new date selection interface
- Successful handling of assignment version transitions
- Maintained or improved dashboard performance

## Timeline: 6 weeks
- **Week 1-2**: Data entry interface updates and assignment resolution
- **Week 3-4**: User experience enhancements and computed fields
- **Week 5**: Testing and performance optimization
- **Week 6**: Polish and user training preparation

## Dependencies
- Completion of MAIN_ASSIGNMENT_SYSTEM_IMPLEMENTATION.md
- ESGData migration to include assignment_id
- Company FY configuration functionality
- Admin assignment management system operational