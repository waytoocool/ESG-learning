"""
Unit tests for tenant-scoped query mixins (Epic 1, Task T5)

This test suite verifies that the TenantScopedQueryMixin and TenantScopedModelMixin
provide proper tenant isolation for multi-tenant data models.

Test Coverage:
✅ 1. Query filtering by tenant
✅ 2. Cross-tenant data isolation
✅ 3. Tenant-aware model creation
✅ 4. Error handling without tenant context
✅ 5. Helper method functionality
✅ 6. Multiple tenant scenarios
"""

import pytest
from flask import g
from app import create_app
from app.extensions import db
from app.models.company import Company
from app.models.entity import Entity
from app.models.esg_data import ESGData
from app.models.framework import FrameworkDataField
from app.models.data_assignment import DataPointAssignment
from app.models.framework import Framework, FrameworkDataField
from app.models.user import User
from datetime import date, datetime


class TestTenantScopedQueryMixin:
    """Test suite for tenant-scoped query functionality."""

    @pytest.fixture
    def app(self):
        """Create test Flask application with in-memory database."""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()

    def test_query_for_tenant_basic_filtering(self, app):
        """✅ Test 1: Basic tenant filtering with query_for_tenant."""
        with app.app_context():
            # Create test companies
            acme_company = Company(name="Acme Corp", slug="acme")
            beta_company = Company(name="Beta Inc", slug="beta")
            gamma_company = Company(name="Gamma LLC", slug="gamma")
            
            db.session.add_all([acme_company, beta_company, gamma_company])
            db.session.commit()
            
            # Create entities for each tenant
            acme_entity1 = Entity(name="Acme HQ", entity_type="Headquarters", company_id=acme_company.id)
            acme_entity2 = Entity(name="Acme Factory", entity_type="Factory", company_id=acme_company.id)
            beta_entity1 = Entity(name="Beta Office", entity_type="Office", company_id=beta_company.id)
            beta_entity2 = Entity(name="Beta Warehouse", entity_type="Warehouse", company_id=beta_company.id)
            gamma_entity1 = Entity(name="Gamma Lab", entity_type="Laboratory", company_id=gamma_company.id)
            
            db.session.add_all([acme_entity1, acme_entity2, beta_entity1, beta_entity2, gamma_entity1])
            db.session.commit()
            
            # Test with Acme tenant
            g.tenant = acme_company
            
            # Query entities for Acme - should only return Acme entities
            acme_entities = Entity.query_for_tenant(db.session).all()
            assert len(acme_entities) == 2
            assert all(entity.company_id == acme_company.id for entity in acme_entities)
            assert all(entity.name.startswith('Acme') for entity in acme_entities)
            
            # Test with Beta tenant
            g.tenant = beta_company
            
            # Query entities for Beta - should only return Beta entities
            beta_entities = Entity.query_for_tenant(db.session).all()
            assert len(beta_entities) == 2
            assert all(entity.company_id == beta_company.id for entity in beta_entities)
            assert all(entity.name.startswith('Beta') for entity in beta_entities)
            
            # Test with Gamma tenant
            g.tenant = gamma_company
            
            # Query entities for Gamma - should only return Gamma entities
            gamma_entities = Entity.query_for_tenant(db.session).all()
            assert len(gamma_entities) == 1
            assert all(entity.company_id == gamma_company.id for entity in gamma_entities)
            assert all(entity.name.startswith('Gamma') for entity in gamma_entities)

    def test_cross_tenant_data_isolation(self, app):
        """✅ Test 2: Verify complete isolation between tenants."""
        with app.app_context():
            # Create test companies
            acme_company = Company(name="Acme Corp", slug="acme")
            beta_company = Company(name="Beta Inc", slug="beta")
            
            db.session.add_all([acme_company, beta_company])
            db.session.commit()
            
            # Create framework and data points
            framework = Framework(framework_name="Test Framework", description="Test framework for tenant isolation")
            db.session.add(framework)
            db.session.commit()
            
            # Create entities for each tenant
            acme_entity1 = Entity(name="Acme HQ", entity_type="Headquarters", company_id=acme_company.id)
            acme_entity2 = Entity(name="Acme Factory", entity_type="Factory", company_id=acme_company.id)
            beta_entity1 = Entity(name="Beta Office", entity_type="Office", company_id=beta_company.id)
            beta_entity2 = Entity(name="Beta Warehouse", entity_type="Warehouse", company_id=beta_company.id)
            
            db.session.add_all([acme_entity1, acme_entity2, beta_entity1, beta_entity2])
            db.session.commit()
            
            # Create data points for each tenant
            acme_dp1 = FrameworkDataField(field_name="Acme Metric 1", value_type="NUMBER", framework_id=framework.framework_id, company_id=acme_company.id)
            acme_dp2 = FrameworkDataField(field_name="Acme Metric 2", value_type="TEXT", framework_id=framework.framework_id, company_id=acme_company.id)
            beta_dp1 = FrameworkDataField(field_name="Beta Metric 1", value_type="NUMBER", framework_id=framework.framework_id, company_id=beta_company.id)
            
            db.session.add_all([acme_dp1, acme_dp2, beta_dp1])
            db.session.commit()
            
            # Set Acme as current tenant
            g.tenant = acme_company
            
            # Query all models for Acme
            acme_entities = Entity.query_for_tenant(db.session).all()
            acme_data_points = FrameworkDataField.query_for_tenant(db.session).all()
            
            # Verify Acme data
            assert len(acme_entities) == 2
            assert len(acme_data_points) == 2
            assert all(entity.name.startswith('Acme') for entity in acme_entities)
            assert all(dp.name.startswith('Acme') for dp in acme_data_points)
            
            # Switch to Beta tenant
            g.tenant = beta_company
            
            # Query all models for Beta
            beta_entities = Entity.query_for_tenant(db.session).all()
            beta_data_points = FrameworkDataField.query_for_tenant(db.session).all()
            
            # Verify Beta data is completely different
            assert len(beta_entities) == 2
            assert len(beta_data_points) == 1
            assert all(entity.name.startswith('Beta') for entity in beta_entities)
            assert all(dp.name.startswith('Beta') for dp in beta_data_points)
            
            # Verify no overlap in IDs
            acme_entity_ids = {entity.id for entity in acme_entities}
            beta_entity_ids = {entity.id for entity in beta_entities}
            assert acme_entity_ids.isdisjoint(beta_entity_ids)

    def test_get_for_tenant_method(self, app):
        """✅ Test 3: Test get_for_tenant method for single record retrieval."""
        with app.app_context():
            # Create test companies
            acme_company = Company(name="Acme Corp", slug="acme")
            beta_company = Company(name="Beta Inc", slug="beta")
            
            db.session.add_all([acme_company, beta_company])
            db.session.commit()
            
            # Create entities
            acme_entity = Entity(name="Acme HQ", entity_type="Headquarters", company_id=acme_company.id)
            beta_entity = Entity(name="Beta Office", entity_type="Office", company_id=beta_company.id)
            
            db.session.add_all([acme_entity, beta_entity])
            db.session.commit()
            
            # Get entity IDs
            acme_entity_id = acme_entity.id
            beta_entity_id = beta_entity.id
            
            # Test with Acme tenant
            g.tenant = acme_company
            
            # Should be able to get Acme entity
            retrieved_acme_entity = Entity.get_for_tenant(db.session, acme_entity_id)
            assert retrieved_acme_entity is not None
            assert retrieved_acme_entity.company_id == acme_company.id
            assert retrieved_acme_entity.name.startswith('Acme')
            
            # Should NOT be able to get Beta entity (different tenant)
            beta_entity_from_acme = Entity.get_for_tenant(db.session, beta_entity_id)
            assert beta_entity_from_acme is None
            
            # Switch to Beta tenant
            g.tenant = beta_company
            
            # Should be able to get Beta entity
            retrieved_beta_entity = Entity.get_for_tenant(db.session, beta_entity_id)
            assert retrieved_beta_entity is not None
            assert retrieved_beta_entity.company_id == beta_company.id
            assert retrieved_beta_entity.name.startswith('Beta')
            
            # Should NOT be able to get Acme entity (different tenant)
            acme_entity_from_beta = Entity.get_for_tenant(db.session, acme_entity_id)
            assert acme_entity_from_beta is None

    def test_count_for_tenant_method(self, app):
        """✅ Test 4: Test count_for_tenant method."""
        with app.app_context():
            # Create test companies
            acme_company = Company(name="Acme Corp", slug="acme")
            beta_company = Company(name="Beta Inc", slug="beta")
            gamma_company = Company(name="Gamma LLC", slug="gamma")
            
            db.session.add_all([acme_company, beta_company, gamma_company])
            db.session.commit()
            
            # Create framework
            framework = Framework(framework_name="Test Framework", description="Test framework")
            db.session.add(framework)
            db.session.commit()
            
            # Create entities for each tenant
            acme_entity1 = Entity(name="Acme HQ", entity_type="Headquarters", company_id=acme_company.id)
            acme_entity2 = Entity(name="Acme Factory", entity_type="Factory", company_id=acme_company.id)
            beta_entity1 = Entity(name="Beta Office", entity_type="Office", company_id=beta_company.id)
            beta_entity2 = Entity(name="Beta Warehouse", entity_type="Warehouse", company_id=beta_company.id)
            gamma_entity1 = Entity(name="Gamma Lab", entity_type="Laboratory", company_id=gamma_company.id)
            
            db.session.add_all([acme_entity1, acme_entity2, beta_entity1, beta_entity2, gamma_entity1])
            db.session.commit()
            
            # Create data points for each tenant
            acme_dp1 = DataPoint(name="Acme Metric 1", value_type="numeric", framework_id=framework.framework_id, company_id=acme_company.id)
            acme_dp2 = DataPoint(name="Acme Metric 2", value_type="text", framework_id=framework.framework_id, company_id=acme_company.id)
            beta_dp1 = DataPoint(name="Beta Metric 1", value_type="numeric", framework_id=framework.framework_id, company_id=beta_company.id)
            gamma_dp1 = DataPoint(name="Gamma Metric 1", value_type="numeric", framework_id=framework.framework_id, company_id=gamma_company.id)
            
            db.session.add_all([acme_dp1, acme_dp2, beta_dp1, gamma_dp1])
            db.session.commit()
            
            # Test entity counts for each tenant
            g.tenant = acme_company
            assert Entity.count_for_tenant(db.session) == 2
            assert FrameworkDataField.count_for_tenant(db.session) == 2
            
            g.tenant = beta_company
            assert Entity.count_for_tenant(db.session) == 2
            assert FrameworkDataField.count_for_tenant(db.session) == 1
            
            g.tenant = gamma_company
            assert Entity.count_for_tenant(db.session) == 1
            assert FrameworkDataField.count_for_tenant(db.session) == 1

    def test_exists_for_tenant_method(self, app):
        """✅ Test 5: Test exists_for_tenant method."""
        with app.app_context():
            # Create test companies
            acme_company = Company(name="Acme Corp", slug="acme")
            beta_company = Company(name="Beta Inc", slug="beta")
            
            db.session.add_all([acme_company, beta_company])
            db.session.commit()
            
            # Create entities
            acme_entity = Entity(name="Acme HQ", entity_type="Headquarters", company_id=acme_company.id)
            beta_entity = Entity(name="Beta Office", entity_type="Office", company_id=beta_company.id)
            
            db.session.add_all([acme_entity, beta_entity])
            db.session.commit()
            
            # Test with Acme tenant
            g.tenant = acme_company
            
            # Should find Acme entities
            assert Entity.exists_for_tenant(db.session, name='Acme HQ') == True
            assert Entity.exists_for_tenant(db.session, entity_type='Headquarters') == True
            
            # Should NOT find Beta entities
            assert Entity.exists_for_tenant(db.session, name='Beta Office') == False
            assert Entity.exists_for_tenant(db.session, entity_type='Office') == False
            
            # Test with Beta tenant
            g.tenant = beta_company
            
            # Should find Beta entities
            assert Entity.exists_for_tenant(db.session, name='Beta Office') == True
            assert Entity.exists_for_tenant(db.session, entity_type='Office') == True
            
            # Should NOT find Acme entities
            assert Entity.exists_for_tenant(db.session, name='Acme HQ') == False
            assert Entity.exists_for_tenant(db.session, entity_type='Headquarters') == False

    def test_tenant_model_mixin_methods(self, app):
        """✅ Test 6: Test TenantScopedModelMixin methods."""
        with app.app_context():
            # Create test companies
            acme_company = Company(name="Acme Corp", slug="acme")
            beta_company = Company(name="Beta Inc", slug="beta")
            
            db.session.add_all([acme_company, beta_company])
            db.session.commit()
            
            # Create entities
            acme_entity = Entity(name="Acme HQ", entity_type="Headquarters", company_id=acme_company.id)
            beta_entity = Entity(name="Beta Office", entity_type="Office", company_id=beta_company.id)
            
            db.session.add_all([acme_entity, beta_entity])
            db.session.commit()
            
            # Test belongs_to_tenant method
            assert acme_entity.belongs_to_tenant(acme_company) == True
            assert acme_entity.belongs_to_tenant(beta_company) == False
            assert beta_entity.belongs_to_tenant(beta_company) == True
            assert beta_entity.belongs_to_tenant(acme_company) == False
            
            # Test belongs_to_current_tenant method
            g.tenant = acme_company
            assert acme_entity.belongs_to_current_tenant() == True
            assert beta_entity.belongs_to_current_tenant() == False
            
            g.tenant = beta_company
            assert acme_entity.belongs_to_current_tenant() == False
            assert beta_entity.belongs_to_current_tenant() == True

    def test_create_for_tenant_methods(self, app):
        """✅ Test 7: Test tenant-aware record creation methods."""
        with app.app_context():
            # Create test companies
            acme_company = Company(name="Acme Corp", slug="acme")
            beta_company = Company(name="Beta Inc", slug="beta")
            
            db.session.add_all([acme_company, beta_company])
            db.session.commit()
            
            # Test create_for_tenant method
            new_entity = Entity.create_for_tenant(
                db.session, 
                acme_company, 
                name='Acme New Office',
                entity_type='Office'
            )
            
            assert new_entity.company_id == acme_company.id
            assert new_entity.name == 'Acme New Office'
            assert new_entity.entity_type == 'Office'
            
            # Test create_for_current_tenant method
            g.tenant = beta_company
            
            new_entity2 = Entity.create_for_current_tenant(
                db.session,
                name='Beta New Lab',
                entity_type='Laboratory'
            )
            
            assert new_entity2.company_id == beta_company.id
            assert new_entity2.name == 'Beta New Lab'
            assert new_entity2.entity_type == 'Laboratory'
            
            # Commit and verify isolation
            db.session.commit()
            
            # Switch tenants and verify each can only see their own new entities
            g.tenant = acme_company
            acme_entities = Entity.query_for_tenant(db.session).all()
            assert len(acme_entities) == 1  # Only the new entity
            assert any(entity.name == 'Acme New Office' for entity in acme_entities)
            assert not any(entity.name == 'Beta New Lab' for entity in acme_entities)
            
            g.tenant = beta_company
            beta_entities = Entity.query_for_tenant(db.session).all()
            assert len(beta_entities) == 1  # Only the new entity
            assert any(entity.name == 'Beta New Lab' for entity in beta_entities)
            assert not any(entity.name == 'Acme New Office' for entity in beta_entities)

    def test_error_handling_without_tenant(self, app):
        """✅ Test 8: Error handling when tenant context is missing."""
        with app.app_context():
            # Clear tenant context
            if hasattr(g, 'tenant'):
                delattr(g, 'tenant')
            
            # Should raise exception for query_for_tenant
            with pytest.raises(Exception, match="Tenant not loaded in request context"):
                Entity.query_for_tenant(db.session).all()
            
            # Should raise exception for get_for_tenant
            with pytest.raises(Exception, match="Tenant not loaded in request context"):
                Entity.get_for_tenant(db.session, 1)
            
            # Should raise exception for count_for_tenant
            with pytest.raises(Exception, match="Tenant not loaded in request context"):
                Entity.count_for_tenant(db.session)
            
            # Should raise exception for exists_for_tenant
            with pytest.raises(Exception, match="Tenant not loaded in request context"):
                Entity.exists_for_tenant(db.session, name='Test')
            
            # Should raise exception for belongs_to_current_tenant
            entity = Entity(name='Test', entity_type='Test', company_id=1)
            with pytest.raises(Exception, match="Tenant not loaded in request context"):
                entity.belongs_to_current_tenant()
            
            # Should raise exception for create_for_current_tenant
            with pytest.raises(Exception, match="Tenant not loaded in request context"):
                Entity.create_for_current_tenant(db.session, name='Test', entity_type='Test')

    def test_complex_queries_with_tenant_filtering(self, app):
        """✅ Test 9: Complex queries with additional filters and tenant isolation."""
        with app.app_context():
            # Create test companies
            acme_company = Company(name="Acme Corp", slug="acme")
            beta_company = Company(name="Beta Inc", slug="beta")
            
            db.session.add_all([acme_company, beta_company])
            db.session.commit()
            
            # Create entities with different types
            acme_hq = Entity(name="Acme HQ", entity_type="Headquarters", company_id=acme_company.id)
            acme_factory = Entity(name="Acme Factory", entity_type="Factory", company_id=acme_company.id)
            beta_office = Entity(name="Beta Office", entity_type="Office", company_id=beta_company.id)
            beta_warehouse = Entity(name="Beta Warehouse", entity_type="Warehouse", company_id=beta_company.id)
            
            db.session.add_all([acme_hq, acme_factory, beta_office, beta_warehouse])
            db.session.commit()
            
            # Test complex filtering with multiple conditions
            g.tenant = acme_company
            
            # Should find Acme headquarters
            acme_hq_results = Entity.query_for_tenant(db.session).filter_by(entity_type='Headquarters').all()
            assert len(acme_hq_results) == 1
            assert acme_hq_results[0].name == 'Acme HQ'
            assert acme_hq_results[0].company_id == acme_company.id
            
            # Should find Acme factories
            acme_factories = Entity.query_for_tenant(db.session).filter_by(entity_type='Factory').all()
            assert len(acme_factories) == 1
            assert acme_factories[0].name == 'Acme Factory'
            
            # Switch to Beta and test different entity types
            g.tenant = beta_company
            
            # Should NOT find headquarters (Beta doesn't have any)
            beta_hq = Entity.query_for_tenant(db.session).filter_by(entity_type='Headquarters').all()
            assert len(beta_hq) == 0
            
            # Should find Beta offices and warehouses
            beta_offices = Entity.query_for_tenant(db.session).filter_by(entity_type='Office').all()
            beta_warehouses = Entity.query_for_tenant(db.session).filter_by(entity_type='Warehouse').all()
            assert len(beta_offices) == 1
            assert len(beta_warehouses) == 1

    def test_multiple_model_tenant_isolation(self, app):
        """✅ Test 10: Verify tenant isolation works across multiple models."""
        with app.app_context():
            # Create test companies
            acme_company = Company(name="Acme Corp", slug="acme")
            beta_company = Company(name="Beta Inc", slug="beta")
            
            db.session.add_all([acme_company, beta_company])
            db.session.commit()
            
            # Create framework
            framework = Framework(framework_name="Test Framework", description="Test framework")
            db.session.add(framework)
            db.session.commit()
            
            # Create entities and data points
            acme_entity = Entity(name="Acme HQ", entity_type="Headquarters", company_id=acme_company.id)
            beta_entity = Entity(name="Beta Office", entity_type="Office", company_id=beta_company.id)
            
            acme_dp = DataPoint(name="Acme Metric", value_type="numeric", framework_id=framework.framework_id, company_id=acme_company.id)
            beta_dp = DataPoint(name="Beta Metric", value_type="numeric", framework_id=framework.framework_id, company_id=beta_company.id)
            
            db.session.add_all([acme_entity, beta_entity, acme_dp, beta_dp])
            db.session.commit()
            
            # Test isolation across Entity, DataPoint models
            g.tenant = acme_company
            
            acme_entities = Entity.query_for_tenant(db.session).all()
            acme_data_points = FrameworkDataField.query_for_tenant(db.session).all()
            
            # Verify all records belong to Acme
            assert all(entity.company_id == acme_company.id for entity in acme_entities)
            assert all(dp.company_id == acme_company.id for dp in acme_data_points)
            
            # Switch tenant and verify complete isolation
            g.tenant = beta_company
            
            beta_entities = Entity.query_for_tenant(db.session).all()
            beta_data_points = FrameworkDataField.query_for_tenant(db.session).all()
            
            # Verify all records belong to Beta
            assert all(entity.company_id == beta_company.id for entity in beta_entities)
            assert all(dp.company_id == beta_company.id for dp in beta_data_points)
            
            # Verify no overlap between tenants
            acme_entity_ids = {e.id for e in acme_entities}
            beta_entity_ids = {e.id for e in beta_entities}
            acme_dp_ids = {dp.id for dp in acme_data_points}
            beta_dp_ids = {dp.id for dp in beta_data_points}
            
            assert acme_entity_ids.isdisjoint(beta_entity_ids)
            assert acme_dp_ids.isdisjoint(beta_dp_ids) 