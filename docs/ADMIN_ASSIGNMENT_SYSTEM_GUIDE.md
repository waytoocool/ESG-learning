# Admin Assignment System Guide

## Overview

The Enhanced Assignment Management System provides comprehensive tools for managing ESG data point assignments with versioning, bulk operations, and detailed history tracking. This guide covers all new features introduced in Feature Cycle 001.

## Table of Contents

1. [SUPER_ADMIN Impersonation](#super_admin-impersonation)
2. [Assignment History](#assignment-history)
3. [Bulk Operations](#bulk-operations)
4. [Assignment Versioning](#assignment-versioning)
5. [Best Practices](#best-practices)

---

## SUPER_ADMIN Impersonation

### Purpose
SUPER_ADMIN users must use impersonation to access company-specific admin pages, ensuring proper tenant context and data isolation.

### How It Works

1. **Login as SUPER_ADMIN**
   - Use your SUPER_ADMIN credentials
   - You'll land on the SUPER_ADMIN dashboard

2. **Access Company-Specific Pages**
   - Navigate to "Companies" in the sidebar
   - Find the company you want to manage
   - Click "Impersonate Admin" button
   - You'll be redirected to that company's admin dashboard

3. **Working Under Impersonation**
   - Orange banner appears at the top indicating impersonation mode
   - All admin features work normally within the company context
   - You can access all admin pages: Assignment History, Bulk Operations, etc.

4. **Exit Impersonation**
   - Click "Exit Impersonation" in the orange banner
   - Or navigate back to SUPER_ADMIN dashboard manually

### Important Notes
- **Required for Admin Pages**: Direct access to admin pages without impersonation will redirect to SUPER_ADMIN dashboard
- **Data Isolation**: You can only see data for the impersonated company
- **Audit Trail**: All actions are logged with impersonation context

---

## Assignment History

### Purpose
View and track the complete lifecycle of assignment changes with timeline visualization and detailed version history.

### Navigation
- **Path**: `/admin/assignment-history`
- **Sidebar**: "Assignment History" link in admin navigation

### Features

#### 1. **Timeline View**
- **Visual Timeline**: Chronological display of assignment changes
- **Date Range Filter**: Filter by specific date ranges
- **Entity Filter**: View assignments for specific entities
- **Framework Filter**: Filter by reporting frameworks
- **Search**: Find assignments by field name or entity

#### 2. **Assignment Details**
- **Version History**: See all versions of an assignment
- **Change Tracking**: View what changed between versions
- **User Attribution**: See who made each change and when
- **Status Changes**: Track assignment lifecycle status

#### 3. **Statistics Dashboard**
- **Summary Cards**: Quick overview of assignment metrics
- **Recent Changes**: Latest assignment modifications
- **Active Assignments**: Current assignment counts
- **Data Series Tracking**: Monitor assignment versioning

### Using Assignment History

1. **Access the Page**
   - Navigate to "Assignment History" in admin sidebar
   - Ensure you're properly impersonating if you're a SUPER_ADMIN

2. **Filter Timeline**
   - Use date picker for date range filtering
   - Select specific entities or frameworks from dropdowns
   - Use search bar for text-based filtering

3. **View Details**
   - Click on any timeline entry to see detailed information
   - Modal popup shows comprehensive assignment details
   - Review version history and change attribution

4. **Export Data**
   - Use export functionality for reporting
   - Filter data before export for specific subsets

---

## Bulk Operations

### Purpose
Efficiently manage multiple assignments simultaneously through four specialized operation types.

### Navigation
- **Path**: `/admin/bulk-operations`
- **Sidebar**: "Bulk Operations" link in admin navigation

### Operation Types

#### 1. **Bulk Create Tab**

**Purpose**: Create multiple assignments across entities and frameworks simultaneously.

**Workflow**:
1. **Selection Step**
   - Choose target entities (multi-select)
   - Select framework and specific fields
   - Set filtering criteria

2. **Configuration Step**
   - Set default frequency (Annual, Quarterly, Monthly, etc.)
   - Choose default units
   - Assign topics if needed
   - Configure override options

3. **Preview Step**
   - Review assignments to be created
   - Validate configuration
   - Check for conflicts or duplicates
   - Make final adjustments

4. **Execute Step**
   - Create assignments
   - Monitor progress
   - Review success/error summary

**Best Use Cases**:
- Setting up new entities with complete assignment sets
- Rolling out new framework requirements across multiple entities
- Creating assignment templates for similar entities

#### 2. **Bulk Update Tab**

**Purpose**: Update collection frequencies for multiple existing assignments.

**Workflow**:
1. **Filter Assignments**
   - Filter by entity, framework, current frequency
   - Select specific assignments from filtered results
   - Use "Select All" for batch operations

2. **Configure Updates**
   - Choose new frequency
   - Provide reason for change (for audit trail)
   - Review selected assignments

3. **Execute Updates**
   - Updates create new assignment versions
   - Monitor progress during execution
   - Review update summary

**Best Use Cases**:
- Changing reporting cycles (e.g., Annual to Quarterly)
- Responding to regulatory requirement changes
- Standardizing frequencies across entities

#### 3. **Copy Template Tab**

**Purpose**: Copy assignment configurations from one entity to multiple target entities.

**Workflow**:
1. **Select Source**
   - Choose source entity with desired assignment configuration
   - Preview assignments to be copied
   - Optionally filter by framework

2. **Select Targets**
   - Choose multiple target entities
   - Search and filter available entities
   - Preview target entity information

3. **Configure Options**
   - Override frequency if needed
   - Override units if needed
   - Override topic assignments if needed
   - Choose which assignments to copy

4. **Execute Copy**
   - Copy assignments to target entities
   - Handle conflicts and duplicates
   - Review copy results

**Best Use Cases**:
- Setting up new entities based on existing templates
- Standardizing assignments across similar entities
- Propagating best-practice configurations

#### 4. **Import/Export Tab**

**Purpose**: CSV-based bulk operations for large-scale assignment management.

**Export Features**:
- **Filter Options**: Export specific subsets of assignments
- **Format Options**: Choose export columns and formatting
- **Template Download**: Get CSV template for imports

**Import Features**:
- **File Upload**: Drag & drop or browse for CSV files
- **Validation Mode**: Preview imports before execution
- **Error Handling**: Detailed error reporting and resolution guidance
- **Progress Tracking**: Monitor large import operations

**CSV Format**:
```csv
entity_name,field_id,frequency,unit,topic_name,action
Entity A,field-uuid-1,Annual,kg,Environmental,create
Entity B,field-uuid-2,Quarterly,tonnes,Social,update
```

**Best Use Cases**:
- Large-scale assignment migrations
- Bulk data imports from external systems
- Backup and restore operations
- Template-based assignment creation

### Bulk Operations Best Practices

1. **Start Small**
   - Test with a few assignments first
   - Use preview mode extensively
   - Validate data before large operations

2. **Use Proper Filtering**
   - Filter data appropriately before bulk operations
   - Double-check entity and framework selections
   - Verify assignment counts match expectations

3. **Audit Trail**
   - Provide meaningful reasons for bulk changes
   - Use bulk operations during maintenance windows
   - Monitor assignment history after bulk operations

4. **Error Handling**
   - Review error reports carefully
   - Fix errors in small batches
   - Use CSV exports to analyze and fix bulk issues

---

## Assignment Versioning

### How It Works

The assignment versioning system tracks all changes to assignments using:
- **data_series_id**: Unique identifier for an assignment series
- **series_version**: Version number (increments with each change)
- **series_status**: Current status (active, inactive, deprecated)

### Version Lifecycle

1. **Creation**: New assignment gets data_series_id and version 1
2. **Updates**: Changes create new version, increment series_version
3. **Status Changes**: Status updates tracked in version history
4. **Deactivation**: Assignment marked inactive but history preserved

### Benefits

- **Complete Audit Trail**: Every change is tracked and attributed
- **Rollback Capability**: Previous versions remain accessible
- **Change Impact Analysis**: See what changed between versions
- **Compliance Support**: Full change history for regulatory requirements

---

## Best Practices

### General Guidelines

1. **Plan Before Bulk Operations**
   - Use preview mode extensively
   - Start with small test batches
   - Have rollback plan ready

2. **Maintain Data Quality**
   - Use consistent naming conventions
   - Validate data before imports
   - Regular cleanup of inactive assignments

3. **Leverage Assignment History**
   - Review changes regularly
   - Use history for troubleshooting
   - Export history for compliance reporting

4. **SUPER_ADMIN Workflows**
   - Always use impersonation for company-specific tasks
   - Keep impersonation sessions focused and time-limited
   - Exit impersonation when switching between companies

### Performance Considerations

1. **Bulk Operations Limits**
   - Bulk Create: Maximum 1000 assignments per batch
   - Bulk Update: Maximum 500 assignments per batch
   - Template Copy: Maximum 100 target entities per operation

2. **Large Dataset Handling**
   - Use filtering to reduce dataset size
   - Break large operations into smaller batches
   - Monitor system performance during bulk operations

3. **Assignment Resolution**
   - Assignment resolution service provides < 50ms response times
   - Caching optimizes performance for frequently accessed assignments
   - Use assignment_id references for best performance

### Troubleshooting

#### Common Issues

1. **Impersonation Problems**
   - Ensure proper SUPER_ADMIN role
   - Clear browser cache/cookies if impersonation fails
   - Check company status and availability

2. **Bulk Operation Failures**
   - Review error logs in operation results
   - Check data validation requirements
   - Verify entity and framework relationships

3. **Assignment History Issues**
   - Refresh page if timeline doesn't load
   - Check date range filters
   - Verify assignment permissions

#### Getting Help

- Check application logs for detailed error messages
- Use preview modes to validate operations before execution
- Contact system administrator for permission or data issues

---

## Summary

The Enhanced Assignment Management System provides powerful tools for:
- **Comprehensive assignment lifecycle management** with full versioning
- **Efficient bulk operations** for large-scale assignment management
- **Detailed audit trails** with timeline visualization
- **Secure multi-tenant access** through SUPER_ADMIN impersonation

These features significantly improve administrative efficiency while maintaining data integrity and providing comprehensive audit capabilities for regulatory compliance.