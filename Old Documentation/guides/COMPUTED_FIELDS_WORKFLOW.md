# ESG DataVault - Computed Fields Workflow Documentation

## 🎯 Overview
This document provides a detailed breakdown of the computed fields functionality, including all database operations, queries, joins, and business logic.

## 📊 Database Schema Context

### Key Tables & Relationships
```sql
-- Core entities
Users (id, username, entity_id, role)
Entity (id, name, parent_id)
DataPoint (id, name, value_type, unit)
FrameworkDataField (field_id, field_name, is_computed, formula_expression)

-- Assignment & mapping
DataPointAssignment (data_point_id, entity_id, is_active, frequency)
FieldVariableMapping (computed_field_id, raw_field_id, variable_name, coefficient)

-- Data storage
ESGData (entity_id, field_id, data_point_id, raw_value, calculated_value, reporting_date)
```

### Current Data State
```
DataPoints:
- Energy Usage: ID='45cfa808-bd2a-4634-b6c7-bbf83b184cbd'
- Diesel: ID='b4d042f5-6a17-4287-a206-60c4a526b80e'  
- Petrol: ID='d4da5295-679d-4aaa-ade4-5fe5ee35cc55'

FrameworkDataFields:
- Energy Usage: ID='4b61fbdb-ae87-4636-abed-7429679c6fc8', is_computed=TRUE, formula='A + B'
- Diesel: ID='fe7643e1-1f7b-4538-8c6d-78b882f5a63d', is_computed=FALSE
- Petrol: ID='a2b56c08-4fef-40ee-b52a-01174b99c007', is_computed=FALSE

FieldVariableMappings:
- computed_field_id='4b61fbdb...', raw_field_id='fe7643e1...', variable='A', coefficient=2.0 (Diesel)
- computed_field_id='4b61fbdb...', raw_field_id='a2b56c08...', variable='B', coefficient=4.0 (Petrol)
```

## 🚀 User Journey Scenarios

### Scenario 1: Dashboard Load

#### Step 1: User Authentication & Entity Resolution
```python
# Query 1: Get user entity and build parent hierarchy
user_entity = Entity.get_for_tenant(db.session, current_user.entity_id)
# SQL: SELECT * FROM entity WHERE id = 2 AND tenant_id = ?
z
parent_entities = []
current_entity = user_entity
while current_entity and current_entity.parent_id:
    parent_entities.append(current_entity.parent_id)
    current_entity = Entity.get_for_tenant(db.session, current_entity.parent_id)
# Result: parent_entities = [] (no parents for Company A)
```

#### Step 2: Variable Mappings & Dependencies
```python
# Query 2: Load all variable mappings to understand dependencies
variable_mappings = (FieldVariableMapping.query
    .join(FrameworkDataField, FrameworkDataField.field_id == FieldVariableMapping.raw_field_id)
    .all())

# SQL: 
# SELECT fvm.*, fdf.* 
# FROM field_variable_mapping fvm
# JOIN framework_data_field fdf ON fdf.field_id = fvm.raw_field_id

# Result builds:
raw_fields = {
    'fe7643e1-1f7b-4538-8c6d-78b882f5a63d': {  # Diesel framework field
        'computed_fields': {'4b61fbdb-ae87-4636-abed-7429679c6fc8'},  # Energy Usage
        'variable_names': {'4b61fbdb-ae87-4636-abed-7429679c6fc8': 'A'}
    },
    'a2b56c08-4fef-40ee-b52a-01174b99c007': {  # Petrol framework field
        'computed_fields': {'4b61fbdb-ae87-4636-abed-7429679c6fc8'},  # Energy Usage
        'variable_names': {'4b61fbdb-ae87-4636-abed-7429679c6fc8': 'B'}
    }
}
computed_fields = {'4b61fbdb-ae87-4636-abed-7429679c6fc8'}  # Energy Usage
```

#### Step 3: Data Point Assignments
```python
# Query 3: Get active assignments for user's entity
assignment_subq = (db.session.query(DataPointAssignment)
    .filter(
        DataPointAssignment.is_active == True,
        DataPointAssignment.entity_id.in_([2])  # user_entity + parents
    ).subquery())

# SQL:
# SELECT * FROM data_point_assignment 
# WHERE is_active = TRUE AND entity_id IN (2)

# Results: 3 assignments for Energy Usage, Diesel, Petrol DataPoint IDs
```

#### Step 4: Load Data Points with Framework Info
```python
# Query 4: Complex join to get data points with framework metadata
all_data_points = (DataPoint.query_for_tenant(db.session)
    .outerjoin(FrameworkDataField, FrameworkDataField.field_id == DataPoint.id)
    .join(assignment_subq, assignment_subq.c.data_point_id == DataPoint.id)
    .join(Entity, Entity.id == assignment_subq.c.entity_id)
    .add_columns(
        FrameworkDataField.description,
        FrameworkDataField.is_computed,
        FrameworkDataField.formula_expression,
        Entity.id.label('assigned_entity_id'),
        Entity.name.label('assigned_entity_name')
    )
    .distinct()
    .all())

# SQL:
# SELECT DISTINCT dp.*, fdf.description, fdf.is_computed, fdf.formula_expression, 
#        e.id as assigned_entity_id, e.name as assigned_entity_name
# FROM data_point dp
# LEFT OUTER JOIN framework_data_field fdf ON fdf.field_id = dp.id
# JOIN (SELECT * FROM data_point_assignment WHERE is_active=TRUE AND entity_id IN (2)) asub 
#      ON asub.data_point_id = dp.id
# JOIN entity e ON e.id = asub.entity_id
# WHERE dp.tenant_id = ?

# CRITICAL: The OUTERJOIN on framework_data_field fails because DataPoint.id != FrameworkDataField.field_id
# This is why is_computed comes back as NULL for all fields
```

#### Step 5: Framework Field Fallback Logic
```python
# For each data point where is_computed is NULL:
for dp, desc, is_computed, formula, assigned_entity_id, assigned_entity_name in all_data_points:
    if is_computed is None:
        # Query 5: Fallback lookup by name
        framework_field = FrameworkDataField.query.filter_by(field_name=dp.name).first()
        # SQL: SELECT * FROM framework_data_field WHERE field_name = 'Energy Usage'
        
        if framework_field:
            is_computed = framework_field.is_computed  # TRUE for Energy Usage
            formula = framework_field.formula_expression  # 'A + B'
            desc = framework_field.description
```

#### Step 6: Data Point Categorization
```python
# Energy Usage: is_computed=TRUE -> goes to computed_points
# Query 6: Get dependencies for computed fields
framework_field = FrameworkDataField.query.filter_by(field_name='Energy Usage').first()
computed_field_id = framework_field.field_id  # '4b61fbdb-ae87-4636-abed-7429679c6fc8'

deps = (FieldVariableMapping.query
       .filter_by(computed_field_id=computed_field_id)
       .all())

# SQL: SELECT * FROM field_variable_mapping WHERE computed_field_id = '4b61fbdb-ae87-4636-abed-7429679c6fc8'
# Returns: 2 dependencies (Diesel A×2.0, Petrol B×4.0)

# Diesel & Petrol: is_computed=FALSE -> go to raw_input_points
```

#### Step 7: Load ESG Data
```python
# Query 7: Load all ESG data for the entity (all dates)
all_esg_data_entries = ESGData.query.filter_by(entity_id=2).all()

# SQL: SELECT * FROM esg_data WHERE entity_id = 2

# Group by date for frontend efficiency
esg_data_by_date = {
    '2024-06-22': {
        'b4d042f5-6a17-4287-a206-60c4a526b80e': {'raw_value': 50.0, 'calculated_value': None},
        'd4da5295-679d-4aaa-ade4-5fe5ee35cc55': {'raw_value': 30.0, 'calculated_value': None},
        '45cfa808-bd2a-4634-b6c7-bbf83b184cbd': {'raw_value': None, 'calculated_value': 220.0}
    }
}
```

### Scenario 2: User Submits Data

#### User Action: Form Submission
```javascript
// Frontend form data:
{
    'reporting_date': '2024-06-22',
    'data_point_b4d042f5-6a17-4287-a206-60c4a526b80e': '50.0',  // Diesel
    'data_point_d4da5295-679d-4aaa-ade4-5fe5ee35cc55': '30.0',  // Petrol
    // Energy Usage field is blocked/readonly (computed field)
}
```

#### Step 1: Date Validation
```python
# Query 8: Validate reporting date against assignments
for data_point_id in ['b4d042f5...', 'd4da5295...']:
    assignment = DataPointAssignment.query.filter_by(
        data_point_id=data_point_id,
        entity_id=2,
        is_active=True
    ).first()
    
    # SQL: SELECT * FROM data_point_assignment 
    #      WHERE data_point_id = ? AND entity_id = 2 AND is_active = TRUE
    
    if assignment and not assignment.is_valid_reporting_date(reporting_date):
        # Validate frequency constraints
        pass
```

#### Step 2: Process Each Form Field

##### Processing Diesel (Raw Field)
```python
field_id = 'b4d042f5-6a17-4287-a206-60c4a526b80e'  # Diesel DataPoint ID
value = '50.0'

# Query 9: Get data point
data_point = DataPoint.query.get(field_id)
# SQL: SELECT * FROM data_point WHERE id = 'b4d042f5-6a17-4287-a206-60c4a526b80e'

# Query 10: Find framework field (ID lookup fails, fallback to name)
framework_field = FrameworkDataField.query.filter_by(field_id=field_id).first()  # Returns None
framework_field = FrameworkDataField.query.filter_by(field_name='Diesel').first()  # Success
# SQL: SELECT * FROM framework_data_field WHERE field_name = 'Diesel'

# Check: is_computed = FALSE -> Continue processing

# Query 11: Validate assignment
assignment = DataPointAssignment.query.filter_by(
    data_point_id=field_id,
    entity_id=2,
    is_active=True
).first()
# SQL: SELECT * FROM data_point_assignment WHERE data_point_id = ? AND entity_id = 2 AND is_active = TRUE

# Query 12: Save raw data
esg_data = ESGData(
    entity_id=2,
    field_id='b4d042f5-6a17-4287-a206-60c4a526b80e',  # DataPoint ID
    data_point_id='b4d042f5-6a17-4287-a206-60c4a526b80e',  # DataPoint ID
    raw_value=50.0,
    reporting_date='2024-06-22'
)
db.session.add(esg_data)

# Query 13: Track affected computed fields
deps = FieldVariableMapping.query.filter_by(raw_field_id='fe7643e1-1f7b-4538-8c6d-78b882f5a63d').all()
# SQL: SELECT * FROM field_variable_mapping WHERE raw_field_id = 'fe7643e1-1f7b-4538-8c6d-78b882f5a63d'
# Result: Energy Usage field ID added to affected_computed_fields set
```

##### Processing Petrol (Raw Field)
```python
# Similar process as Diesel
# Results in second ESGData entry and same computed field affected
```

#### Step 3: Compute Affected Fields

##### Computing Energy Usage
```python
framework_field_id = '4b61fbdb-ae87-4636-abed-7429679c6fc8'  # Energy Usage framework field

# Query 14: Get framework field
framework_field = FrameworkDataField.query.get(framework_field_id)
# SQL: SELECT * FROM framework_data_field WHERE field_id = '4b61fbdb-ae87-4636-abed-7429679c6fc8'

# Query 15: Find corresponding data point
data_point = DataPoint.query.filter_by(name='Energy Usage').first()
# SQL: SELECT * FROM data_point WHERE name = 'Energy Usage'

# Query 16: Get dependencies
dependencies = FieldVariableMapping.query.filter_by(computed_field_id=framework_field_id).all()
# SQL: SELECT * FROM field_variable_mapping WHERE computed_field_id = '4b61fbdb-ae87-4636-abed-7429679c6fc8'
# Returns: [
#   {raw_field_id: 'fe7643e1...', variable_name: 'A', coefficient: 2.0},
#   {raw_field_id: 'a2b56c08...', variable_name: 'B', coefficient: 4.0}
# ]

dependency_values = {}

# For Diesel dependency (A):
# Query 17: Get raw framework field
raw_framework_field = FrameworkDataField.query.get('fe7643e1-1f7b-4538-8c6d-78b882f5a63d')
# SQL: SELECT * FROM framework_data_field WHERE field_id = 'fe7643e1-1f7b-4538-8c6d-78b882f5a63d'

# Query 18: Find raw data point
raw_data_point = DataPoint.query.filter_by(name='Diesel').first()
# SQL: SELECT * FROM data_point WHERE name = 'Diesel'

# Query 19: Get ESG data value
esg_data = ESGData.query.filter_by(
    data_point_id='b4d042f5-6a17-4287-a206-60c4a526b80e',
    entity_id=2,
    reporting_date='2024-06-22'
).first()
# SQL: SELECT * FROM esg_data WHERE data_point_id = ? AND entity_id = 2 AND reporting_date = ?

dependency_values['A'] = 50.0 * 2.0 = 100.0

# Similar process for Petrol dependency (B):
dependency_values['B'] = 30.0 * 4.0 = 120.0

# Formula evaluation: A + B = 100.0 + 120.0 = 220.0
computed_value = 220.0
```

#### Step 4: Save Computed Value
```python
# Query 20: Check if computed ESG data exists
computed_data = ESGData.query.filter_by(
    data_point_id='45cfa808-bd2a-4634-b6c7-bbf83b184cbd',  # Energy Usage DataPoint ID
    entity_id=2,
    reporting_date='2024-06-22'
).first()
# SQL: SELECT * FROM esg_data WHERE data_point_id = ? AND entity_id = 2 AND reporting_date = ?

# Create new ESG data entry
computed_data = ESGData(
    entity_id=2,
    field_id='4b61fbdb-ae87-4636-abed-7429679c6fc8',     # Framework field ID
    data_point_id='45cfa808-bd2a-4634-b6c7-bbf83b184cbd', # DataPoint ID
    raw_value=None,
    calculated_value=220.0,
    reporting_date='2024-06-22'
)
db.session.add(computed_data)

# Query 21: Commit all changes
db.session.commit()
```

## 🔍 Key Database Insights

### Critical ID Mappings
```
The system maintains two parallel ID systems:
1. DataPoint.id (used for assignments and ESG data storage)
2. FrameworkDataField.field_id (used for computation logic and dependencies)

Mapping by name is used as the bridge between these systems.
```

### Query Performance Considerations
```sql
-- Most expensive query (Dashboard load):
SELECT DISTINCT dp.*, fdf.description, fdf.is_computed, fdf.formula_expression
FROM data_point dp
LEFT OUTER JOIN framework_data_field fdf ON fdf.field_id = dp.id  -- This join fails
JOIN data_point_assignment dpa ON dpa.data_point_id = dp.id
JOIN entity e ON e.id = dpa.entity_id
WHERE dp.tenant_id = ? AND dpa.is_active = TRUE AND dpa.entity_id IN (?)

-- Optimization opportunity: Pre-compute field mappings or use materialized views
```

### Data Consistency Checks
```python
# The system performs these key validations:
1. Assignment validation (entity has permission to submit data)
2. Date validation (reporting date matches assignment frequency)
3. Computed field skip validation (prevents manual entry)
4. Dependency availability check (all raw values present before computation)
5. Tenant isolation (all queries respect tenant boundaries)
```

## 📈 Performance Metrics

### Database Operations Count
```
Dashboard Load: ~15-20 queries
- 1 user/entity lookup
- 1 variable mappings load
- 1 assignments load  
- 1 complex data points join
- 3-5 framework field fallback lookups
- 3-5 dependency queries for computed fields
- 1 ESG data bulk load

Form Submission: ~10-15 queries per raw field + 5-8 per computed field
- Validation queries: 2-3 per field
- Raw data save: 1 per field
- Computed field processing: 3-5 per dependency + 1 save
- Final commit: 1
```

### Optimization Opportunities
1. **Materialized Views**: Pre-compute DataPoint ↔ FrameworkDataField mappings
2. **Bulk Operations**: Batch dependency lookups and ESG data saves
3. **Caching**: Cache framework field mappings and dependency trees
4. **Index Optimization**: Ensure proper indexing on tenant_id, entity_id, reporting_date

## 🛡️ Error Handling & Edge Cases

### Handled Scenarios
- Missing framework fields (fallback to name lookup)
- Incomplete dependency data (skip computation with logging)
- Invalid reporting dates (validation with user feedback)
- Tenant isolation violations (automatic filtering)
- Concurrent data modifications (database-level constraints)

### Monitoring Points
- Computation success/failure rates
- Query performance metrics
- Data consistency validation
- User experience timing (dashboard load, form submission)
