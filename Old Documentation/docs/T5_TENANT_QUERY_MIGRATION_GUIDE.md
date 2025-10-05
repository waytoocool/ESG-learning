# Task T5: Tenant-Scoped Query Migration Guide

## Overview

This guide demonstrates how to migrate existing unsafe queries to use the new `TenantScopedQueryMixin` for proper tenant isolation.

## Migration Pattern

### Before (Unsafe)
```python
# ❌ UNSAFE - Can access any company's data
entities = Entity.query.filter_by(entity_type='Factory').all()
entity = Entity.query.get(entity_id)
data_point = DataPoint.query.filter_by(name='Revenue').first()
```

### After (Tenant-Safe)
```python
# ✅ SAFE - Automatically filtered by current tenant
entities = Entity.query_for_tenant(db.session).filter_by(entity_type='Factory').all()
entity = Entity.get_for_tenant(db.session, entity_id)
data_point = DataPoint.query_for_tenant(db.session).filter_by(name='Revenue').first()
```

## Detailed Migration Examples

### 1. Basic Query Replacements

```python
# ❌ Before: Direct model queries
Entity.query.all()
ESGData.query.filter_by(entity_id=entity_id).all()
DataPoint.query.filter(DataPoint.name.like('%carbon%')).all()

# ✅ After: Tenant-scoped queries
Entity.query_for_tenant(db.session).all()
ESGData.query_for_tenant(db.session).filter_by(entity_id=entity_id).all()
DataPoint.query_for_tenant(db.session).filter(DataPoint.name.like('%carbon%')).all()
```

### 2. Single Record Retrieval

```python
# ❌ Before: Can access any tenant's record
entity = Entity.query.get(entity_id)
data_point = DataPoint.query.filter_by(id=dp_id).first()

# ✅ After: Only returns record if it belongs to current tenant
entity = Entity.get_for_tenant(db.session, entity_id)
data_point = DataPoint.query_for_tenant(db.session).filter_by(id=dp_id).first()
```

### 3. Complex Queries with Joins

```python
# ❌ Before: Unsafe join query
query = ESGData.query.join(Entity).filter(
    Entity.entity_type == 'Factory',
    ESGData.reporting_date >= start_date
).all()

# ✅ After: Tenant-scoped join query
query = ESGData.query_for_tenant(db.session).join(Entity).filter(
    Entity.entity_type == 'Factory',
    ESGData.reporting_date >= start_date
).all()
```

### 4. Counting Records

```python
# ❌ Before: Counts all records across tenants
total_entities = Entity.query.count()
factory_count = Entity.query.filter_by(entity_type='Factory').count()

# ✅ After: Counts only current tenant's records
total_entities = Entity.count_for_tenant(db.session)
factory_count = Entity.query_for_tenant(db.session).filter_by(entity_type='Factory').count()
```

### 5. Existence Checks

```python
# ❌ Before: Can find records from any tenant
exists = Entity.query.filter_by(name='HQ').first() is not None

# ✅ After: Only finds records from current tenant
exists = Entity.exists_for_tenant(db.session, name='HQ')
```

### 6. Record Creation

```python
# ❌ Before: Manual company_id assignment (error-prone)
entity = Entity(
    name='New Office',
    entity_type='Office',
    company_id=current_user.company_id  # Manual assignment
)

# ✅ After: Automatic tenant assignment
entity = Entity.create_for_current_tenant(
    db.session,
    name='New Office',
    entity_type='Office'
)
```

## File-by-File Migration Examples

### Routes (`app/routes/user.py`)

```python
# ❌ Before (Line 169)
all_esg_data_entries = ESGData.query.filter_by(
    entity_id=current_user.entity_id
).all()

# ✅ After 
all_esg_data_entries = ESGData.query_for_tenant(db.session).filter_by(
    entity_id=current_user.entity_id
).all()

# ❌ Before (Line 291)
data_point = DataPoint.query.get(field_id)

# ✅ After
data_point = DataPoint.get_for_tenant(db.session, field_id)

# ❌ Before (Line 306)
esg_data = ESGData.query.filter_by(
    data_point_id=field_id,
    entity_id=current_user.entity_id,
    reporting_date=reporting_date
).first()

# ✅ After
esg_data = ESGData.query_for_tenant(db.session).filter_by(
    data_point_id=field_id,
    entity_id=current_user.entity_id,
    reporting_date=reporting_date
).first()
```

### Services (`app/services/aggregation.py`)

```python
# ❌ Before (Line 482)
dependency_values = ESGData.query.filter(
    ESGData.data_point_id == dependency_field_id,
    ESGData.entity_id == entity_id,
    ESGData.reporting_date >= period_start,
    ESGData.reporting_date <= period_end,
    ESGData.raw_value.isnot(None)
).order_by(ESGData.reporting_date).all()

# ✅ After
dependency_values = ESGData.query_for_tenant(db.session).filter(
    ESGData.data_point_id == dependency_field_id,
    ESGData.entity_id == entity_id,
    ESGData.reporting_date >= period_start,
    ESGData.reporting_date <= period_end,
    ESGData.raw_value.isnot(None)
).order_by(ESGData.reporting_date).all()
```

### Admin Routes (`app/routes/admin.py`)

```python
# ❌ Before (Line 398)
entities = Entity.query.all()
data_points = DataPoint.query.all()

# ✅ After - Admin routes need special handling
# Option 1: Use tenant-scoped queries if admin belongs to a company
if current_user.company_id:
    entities = Entity.query_for_tenant(db.session).all()
    data_points = DataPoint.query_for_tenant(db.session).all()
else:
    # Super admin can see all - use manual filtering or create special methods
    entities = Entity.query.all()
    data_points = DataPoint.query.all()

# Option 2: Create admin-specific methods for cross-tenant access
entities = Entity.query_for_admin(db.session, current_user).all()
```

## Special Cases and Considerations

### 1. Super Admin Access

Super admins need access to all tenant data. Handle this with conditional logic:

```python
if current_user.is_super_admin():
    # Super admin sees all data
    entities = Entity.query.all()
else:
    # Regular users see only their tenant's data
    entities = Entity.query_for_tenant(db.session).all()
```

### 2. Cross-Tenant Operations

Some operations may legitimately need cross-tenant access. These should be:
- Explicitly documented
- Restricted to super admins
- Use special methods with clear naming

```python
# For super admin operations only
def get_all_tenant_data_for_admin(user):
    if not user.is_super_admin():
        raise PermissionError("Only super admins can access cross-tenant data")
    return Entity.query.all()
```

### 3. Framework and Non-Tenant Data

Some models (like Framework, FrameworkDataField) are shared across tenants:

```python
# These remain unchanged - no tenant isolation needed
frameworks = Framework.query.all()
fields = FrameworkDataField.query.filter_by(framework_id=framework_id).all()
```

## Testing Your Migration

### 1. Unit Tests
Run the tenant isolation tests:
```bash
pytest tests/test_tenant_scoped_queries.py -v
```

### 2. Manual Testing
1. Create test data for multiple tenants
2. Switch between tenant subdomains
3. Verify each tenant only sees their own data
4. Test edge cases (invalid tenant, missing tenant)

### 3. Security Audit
1. Search for remaining direct `.query` calls on tenant-scoped models
2. Verify all user-facing queries use tenant-scoped methods
3. Check that admin functions properly handle super admin vs tenant admin

## Migration Checklist

- [ ] Update all Entity queries to use `query_for_tenant`
- [ ] Update all ESGData queries to use `query_for_tenant`
- [ ] Update all DataPoint queries to use `query_for_tenant`
- [ ] Update all DataPointAssignment queries to use `query_for_tenant`
- [ ] Replace `.get()` calls with `get_for_tenant()`
- [ ] Replace existence checks with `exists_for_tenant()`
- [ ] Update record creation to use `create_for_current_tenant()`
- [ ] Handle super admin special cases
- [ ] Add tenant context validation where needed
- [ ] Run comprehensive tests
- [ ] Security audit of remaining direct queries

## Performance Considerations

The tenant-scoped queries add a `WHERE company_id = ?` clause to every query. This is efficient because:

1. `company_id` columns are indexed
2. Tenant filtering happens at the database level
3. Results in smaller result sets
4. Better security with minimal performance impact

## Error Handling

Always handle the case where tenant context is missing:

```python
try:
    entities = Entity.query_for_tenant(db.session).all()
except Exception as e:
    if "Tenant not loaded" in str(e):
        # Handle missing tenant context
        return redirect(url_for('auth.login'))
    raise
``` 