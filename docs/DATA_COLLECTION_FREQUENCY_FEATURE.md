# Data Collection Frequency & Financial Year Feature

## Overview

This feature enhances the ESG DataVault system by adding **Financial Year (FY) and Frequency configuration** to data point assignments. Instead of allowing users to submit data for any date, administrators can now configure:

1. **Financial Year periods** (e.g., April 2024 to March 2025, January 2024 to December 2024)
2. **Data collection frequency** (Annual, Quarterly, Monthly)

## Key Features

### For Administrators

#### Enhanced Data Point Assignment
- **FY Configuration**: Set custom financial year start month and year range
- **Frequency Selection**: Choose between Annual, Quarterly, or Monthly data collection
- **Visual Indicators**: Frequency badges and FY displays in the assignment interface
- **Validation**: Automatic validation of FY date ranges

#### Assignment Interface
- Expandable accordion with configuration panels for each data point
- Real-time updates of assignment configurations
- Clear frequency and FY display for each assigned data point

### For Users

#### Restricted Date Selection
- **Automatic Validation**: Users can only submit data for valid reporting dates
- **Date Suggestions**: Dropdown with valid dates based on assignment configuration
- **Error Prevention**: Clear error messages when invalid dates are selected
- **Frequency Information**: Visual display of data collection frequencies

## Implementation Details

### Database Changes

#### New Table: `data_point_assignments`
```sql
CREATE TABLE data_point_assignments (
    id VARCHAR(36) PRIMARY KEY,
    data_point_id VARCHAR(36) NOT NULL,
    entity_id INTEGER NOT NULL,
    fy_start_month INTEGER NOT NULL DEFAULT 4,
    fy_start_year INTEGER NOT NULL,
    fy_end_year INTEGER NOT NULL,
    frequency ENUM('Monthly', 'Quarterly', 'Annual') NOT NULL DEFAULT 'Annual',
    assigned_date DATETIME,
    assigned_by INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Backend Changes

#### New Model: `DataPointAssignment`
- Handles FY and frequency configuration
- Generates valid reporting dates based on frequency
- Validates reporting dates against configuration

#### Updated Routes
- **Admin**: Enhanced assignment endpoints with FY/frequency support
- **User**: New validation endpoints for date checking

### Frontend Changes

#### Admin Interface
- Enhanced assignment accordion with FY/frequency controls
- Real-time configuration updates
- Visual frequency badges and FY displays

#### User Interface
- Date validation and suggestions
- Frequency information display
- Error prevention with clear messaging

## Usage Guide

### Setting Up Data Point Assignments (Admin)

1. **Navigate** to Admin → Data Points Management
2. **Select** data points to assign
3. **Configure** for each data point:
   - **FY Start Month**: January, April, July, or October
   - **FY Start Year**: e.g., 2024
   - **FY End Year**: e.g., 2025
   - **Frequency**: Annual, Quarterly, or Monthly
4. **Select** entities to assign to
5. **Save** the assignment configuration

### Data Collection (User)

1. **Navigate** to User Dashboard
2. **Select** a reporting date (only valid dates will be available)
3. **View** frequency information for assigned data points
4. **Submit** data (automatic validation prevents invalid submissions)

## Examples

### Annual Data Collection
- **Configuration**: FY April 2024 - March 2025, Annual frequency
- **Valid Dates**: March 31, 2025 only
- **Use Case**: Annual financial reporting

### Quarterly Data Collection
- **Configuration**: FY April 2024 - March 2025, Quarterly frequency
- **Valid Dates**: June 30, 2024; September 30, 2024; December 31, 2024; March 31, 2025
- **Use Case**: Quarterly ESG reporting

### Monthly Data Collection
- **Configuration**: FY January 2024 - December 2024, Monthly frequency
- **Valid Dates**: Last day of each month in the FY
- **Use Case**: Monthly operational metrics

## Benefits

1. **Data Consistency**: Ensures data is collected at appropriate intervals
2. **Compliance**: Supports different reporting standards and requirements
3. **User Experience**: Clear guidance on when data should be submitted
4. **Administrative Control**: Flexible configuration per data point and entity
5. **Error Prevention**: Automatic validation prevents incorrect submissions

## Migration

The feature includes a migration script (`create_assignment_table.py`) that:
- Creates the new `data_point_assignments` table
- Maintains backward compatibility with existing assignments
- Safely adds the new functionality without data loss

## Technical Notes

- Uses `python-dateutil` for accurate date calculations
- Supports different calendar systems and leap years
- Maintains backward compatibility with existing entity-data point relationships
- Includes comprehensive error handling and validation 