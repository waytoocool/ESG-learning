"""
Examples of how to use tenant-scoped query mixins (T5)

This file demonstrates practical usage of the TenantScopedQueryMixin and 
TenantScopedModelMixin for secure tenant isolation.
"""

from flask import g
from app.extensions import db
from app.models.entity import Entity
from app.models.esg_data import ESGData
from app.models.data_point import DataPoint
from app.models.data_assignment import DataPointAssignment


# =====================================
# BEFORE: Unsafe queries (DO NOT USE)
# =====================================

def unsafe_entity_queries():
    """❌ These queries are UNSAFE - they can access any tenant's data."""
    
    # These queries bypass tenant isolation
    all_entities = Entity.query.all()  # ❌ Returns ALL entities across ALL tenants
    entity = Entity.query.get(entity_id)  # ❌ Can access other tenant's entities
    factories = Entity.query.filter_by(entity_type='Factory').all()  # ❌ Cross-tenant access


# =====================================
# AFTER: Safe tenant-scoped queries
# =====================================

def safe_entity_queries():
    """✅ These queries are SAFE - automatically filtered by tenant."""
    
    # All queries automatically filtered by current tenant (g.tenant)
    tenant_entities = Entity.query_for_tenant(db.session).all()
    entity = Entity.get_for_tenant(db.session, entity_id)
    factories = Entity.query_for_tenant(db.session).filter_by(entity_type='Factory').all()
    
    return tenant_entities, entity, factories


def dashboard_data_example():
    """Example: Getting dashboard data safely with tenant isolation."""
    
    # Count entities for current tenant
    entity_count = Entity.count_for_tenant(db.session)
    
    # Get recent ESG data entries
    recent_esg_data = ESGData.query_for_tenant(db.session).order_by(
        ESGData.created_at.desc()
    ).limit(10).all()
    
    # Get active data point assignments
    active_assignments = DataPointAssignment.query_for_tenant(db.session).filter_by(
        is_active=True
    ).all()
    
    return {
        'entity_count': entity_count,
        'recent_data': recent_esg_data,
        'assignments': active_assignments
    }


def entity_management_example():
    """Example: Entity CRUD operations with tenant safety."""
    
    # Create new entity for current tenant
    new_entity = Entity.create_for_current_tenant(
        db.session,
        name='New Facility',
        entity_type='Factory'
    )
    
    # Check if entity name already exists in current tenant
    name_exists = Entity.exists_for_tenant(db.session, name='New Facility')
    
    # Get specific entity (only if it belongs to current tenant)
    entity = Entity.get_for_tenant(db.session, entity_id)
    
    # Verify entity belongs to current tenant
    if entity and entity.belongs_to_current_tenant():
        # Safe to operate on this entity
        entity.name = 'Updated Name'
        db.session.commit()
    
    return new_entity


def complex_reporting_example():
    """Example: Complex reporting with joins and tenant safety."""
    
    # Complex query with joins - all automatically tenant-filtered
    report_data = db.session.query(Entity, ESGData).join(
        ESGData, Entity.id == ESGData.entity_id
    ).filter(
        Entity.id.in_(
            Entity.query_for_tenant(db.session).with_entities(Entity.id).subquery()
        ),
        ESGData.data_id.in_(
            ESGData.query_for_tenant(db.session).with_entities(ESGData.data_id).subquery()
        )
    ).all()
    
    return report_data


def data_point_assignment_example():
    """Example: Data point assignment with tenant isolation."""
    
    # Get all data points for current tenant
    tenant_data_points = DataPoint.query_for_tenant(db.session).all()
    
    # Get entities that can be assigned data points
    assignable_entities = Entity.query_for_tenant(db.session).filter_by(
        entity_type='Factory'
    ).all()
    
    # Create assignment for current tenant
    if tenant_data_points and assignable_entities:
        assignment = DataPointAssignment.create_for_current_tenant(
            db.session,
            data_point_id=tenant_data_points[0].id,
            entity_id=assignable_entities[0].id,
            fy_start_month=4,
            fy_start_year=2024,
            fy_end_year=2025,
            frequency='Annual',
            assigned_by=1  # current_user.id
        )
        db.session.commit()
        return assignment


# =====================================
# Error handling examples
# =====================================

def error_handling_example():
    """Example: Proper error handling for tenant-scoped queries."""
    
    try:
        entities = Entity.query_for_tenant(db.session).all()
        return entities
    except Exception as e:
        if "Tenant not loaded" in str(e):
            # Handle missing tenant context
            # This could happen if middleware failed or user not authenticated
            return {"error": "No tenant context available"}
        else:
            # Handle other database errors
            return {"error": f"Database error: {str(e)}"}


# =====================================
# Super Admin special cases
# =====================================

def admin_cross_tenant_access(current_user):
    """Example: How super admins can access cross-tenant data when needed."""
    
    if current_user.is_super_admin():
        # Super admins can bypass tenant isolation when necessary
        all_entities = Entity.query.all()
        
        # Or get data for specific tenant
        specific_tenant_entities = Entity.query.filter_by(company_id=tenant_id).all()
        
        return all_entities
    else:
        # Regular users get tenant-scoped data
        return Entity.query_for_tenant(db.session).all()


# =====================================
# Migration helpers
# =====================================

def migrate_unsafe_to_safe_query():
    """Example: How to migrate an unsafe query to tenant-safe."""
    
    # ❌ BEFORE: Unsafe query
    # user_entities = Entity.query.filter_by(entity_type='Office').all()
    
    # ✅ AFTER: Safe tenant-scoped query
    user_entities = Entity.query_for_tenant(db.session).filter_by(entity_type='Office').all()
    
    return user_entities


# =====================================
# Testing helpers
# =====================================

def test_tenant_isolation_example():
    """Example: How to test tenant isolation in your code."""
    
    # Create test companies
    from app.models.company import Company
    
    acme = Company(name="Acme Corp", slug="acme")
    beta = Company(name="Beta Inc", slug="beta")
    db.session.add_all([acme, beta])
    db.session.commit()
    
    # Create entities for different tenants
    acme_entity = Entity.create_for_tenant(db.session, acme, name="Acme HQ", entity_type="Office")
    beta_entity = Entity.create_for_tenant(db.session, beta, name="Beta HQ", entity_type="Office")
    db.session.commit()
    
    # Test isolation
    g.tenant = acme
    acme_entities = Entity.query_for_tenant(db.session).all()
    assert len(acme_entities) == 1
    assert acme_entities[0].name == "Acme HQ"
    
    g.tenant = beta
    beta_entities = Entity.query_for_tenant(db.session).all()
    assert len(beta_entities) == 1
    assert beta_entities[0].name == "Beta HQ"
    
    # Verify no cross-contamination
    assert acme_entities[0].id != beta_entities[0].id
    
    print("✅ Tenant isolation working correctly!")


# =====================================
# Performance considerations
# =====================================

def performance_optimized_queries():
    """Example: Performance-optimized tenant-scoped queries."""
    
    # Use eager loading with tenant filtering
    entities_with_data = Entity.query_for_tenant(db.session).options(
        db.joinedload(Entity.esg_data)
    ).all()
    
    # Use subqueries for complex filtering
    high_value_entities = Entity.query_for_tenant(db.session).filter(
        Entity.id.in_(
            db.session.query(ESGData.entity_id)
            .filter(ESGData.calculated_value > 1000)
            .filter(ESGData.company_id == g.tenant.id)  # Explicit tenant filter for subquery
            .distinct()
            .subquery()
        )
    ).all()
    
    return entities_with_data, high_value_entities


if __name__ == "__main__":
    # Example usage (requires Flask app context)
    print("These are example functions demonstrating tenant-scoped query usage.")
    print("Run within a Flask app context with proper tenant middleware setup.") 