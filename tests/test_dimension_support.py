"""
Test Suite for Phase 2.5: Dimension Support Implementation

This test suite comprehensively tests the dimensional data support including:
- Dimension and DimensionValue models
- FieldDimension associations
- ESGData dimensional storage
- Aggregation service with dimensional filtering
- API endpoints for dimension management
"""

import pytest
from datetime import date, datetime
from flask import Flask
from unittest.mock import patch
from app import create_app
from app.extensions import db
from app.models import (
    Company, User, Framework, FrameworkDataField, Entity, ESGData,
    Dimension, DimensionValue, FieldDimension, FieldVariableMapping,
    DataPointAssignment
)
from app.services.aggregation import AggregationService
import json
import time


@pytest.fixture
def app():
    """Create application for testing."""
    import os
    # Set testing configuration
    os.environ['FLASK_ENV'] = 'testing'
    app = create_app()
    app.config.from_object('app.config.TestingConfig')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_company(db_session):
    """Create a sample company for testing."""
    # Use timestamp to ensure uniqueness
    timestamp = str(int(time.time()))
    company = Company(
        name="Test Company Ltd",
        slug=f"test-company-{timestamp}"
    )
    db_session.add(company)
    db_session.commit()
    return company


@pytest.fixture
def sample_user(db_session, sample_company):
    """Create a sample admin user."""
    user = User(
        name="admin",
        email="admin@test.com",
        role="ADMIN",
        company_id=sample_company.id
    )
    user.set_password("password")
    user.is_email_verified = True
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_framework(db_session, sample_company):
    """Create a sample framework for testing."""
    framework = Framework(
        framework_name="Test Framework",
        company_id=sample_company.id,
        description="Test framework for dimension testing"
    )
    db_session.add(framework)
    db_session.commit()
    return framework


@pytest.fixture
def sample_entity(db_session, sample_company):
    """Create a sample entity for testing."""
    entity = Entity(
        name="Test Entity",
        entity_type="Department",
        company_id=sample_company.id
    )
    db_session.add(entity)
    db_session.commit()
    return entity


class TestDimensionModels:
    """Test dimension model functionality."""
    
    def test_create_dimension(self, db_session, sample_company):
        """Test creating a new dimension."""
        dimension = Dimension(
            name="Gender",
            company_id=sample_company.id,
            description="Employee gender classification"
        )
        db_session.add(dimension)
        db_session.commit()
        
        assert dimension.dimension_id is not None
        assert dimension.name == "Gender"
        assert dimension.company_id == sample_company.id
        assert not dimension.is_system_default
    
    def test_create_dimension_values(self, db_session, sample_company):
        """Test creating dimension values."""
        dimension = Dimension(
            name="Age Group",
            company_id=sample_company.id
        )
        db_session.add(dimension)
        db_session.flush()
        
        values = [
            DimensionValue(
                dimension_id=dimension.dimension_id,
                value="<30",
                company_id=sample_company.id,
                display_name="Under 30",
                display_order=0
            ),
            DimensionValue(
                dimension_id=dimension.dimension_id,
                value="30-50",
                company_id=sample_company.id,
                display_name="30 to 50",
                display_order=1
            ),
            DimensionValue(
                dimension_id=dimension.dimension_id,
                value=">50",
                company_id=sample_company.id,
                display_name="Over 50",
                display_order=2
            )
        ]
        
        for value in values:
            db_session.add(value)
        
        db_session.commit()
        
        ordered_values = dimension.get_ordered_values()
        assert len(ordered_values) == 3
        assert ordered_values[0].value == "<30"
        assert ordered_values[1].value == "30-50"
        assert ordered_values[2].value == ">50"
    
    def test_field_dimension_association(self, db_session, sample_company, sample_framework):
        """Test associating dimensions with fields."""
        # Create dimension
        dimension = Dimension(
            name="Gender",
            company_id=sample_company.id
        )
        db_session.add(dimension)
        db_session.flush()
        
        # Create field
        field = FrameworkDataField(
            framework_id=sample_framework.framework_id,
            company_id=sample_company.id,
            field_name="Employee Count",
            field_code="EMP_COUNT",
            value_type="NUMBER"
        )
        db_session.add(field)
        db_session.flush()
        
        # Create association
        field_dimension = FieldDimension(
            field_id=field.field_id,
            dimension_id=dimension.dimension_id,
            company_id=sample_company.id,
            is_required=True
        )
        db_session.add(field_dimension)
        db_session.commit()
        
        # Verify association
        assert len(field.field_dimensions) == 1
        assert field.field_dimensions[0].dimension.name == "Gender"
        assert field.field_dimensions[0].is_required is True


class TestESGDataDimensional:
    """Test ESGData dimensional support."""
    
    def test_create_dimensional_esg_data(self, db_session, sample_company):
        """Test creating ESG data with dimensional breakdown."""
        esg_data = ESGData(
            field_id="test-field-1",  # Mock field ID
            entity_id=1,  # Mock entity ID
            raw_value="100.0",
            reporting_date=date(2024, 1, 1),
            company_id=sample_company.id,
            calculated_value=100.0,
            dimension_values={
                "gender": "Male",
                "age": "<30"
            }
        )
        db_session.add(esg_data)
        db_session.commit()
        
        assert esg_data.data_id is not None
        assert esg_data.calculated_value == 100.0
        assert esg_data.get_dimension_value("gender") == "Male"
        assert esg_data.get_dimension_value("age") == "<30"
        assert esg_data.get_dimension_value("department") is None
        assert esg_data.has_dimensions() is True
    
    def test_set_dimension_values(self, db_session, sample_company, sample_framework, sample_entity):
        """Test setting and updating dimension values."""
        # Create field
        field = FrameworkDataField(
            framework_id=sample_framework.framework_id,
            company_id=sample_company.id,
            field_name="Employee Count",
            field_code="EMP_COUNT",
            value_type="NUMBER"
        )
        db_session.add(field)
        db_session.flush()
        
        esg_data = ESGData(
            field_id=field.field_id,
            entity_id=sample_entity.id,
            raw_value="50.0",
            reporting_date=date(2024, 1, 1),
            company_id=sample_company.id,
            calculated_value=50.0
        )
        db_session.add(esg_data)
        db_session.commit()
        
        # Initially no dimensions
        assert not esg_data.has_dimensions()
        
        # Set dimension values
        esg_data.set_dimension_value("gender", "Female")
        esg_data.set_dimension_value("age", "30-50")
        db_session.commit()
        
        # Verify dimensions are set
        assert esg_data.has_dimensions()
        assert esg_data.get_dimension_value("gender") == "Female"
        assert esg_data.get_dimension_value("age") == "30-50"
        
        # Test dimension key generation
        expected_key = "age:30-50,gender:Female"
        assert esg_data.get_dimension_key() == expected_key


class TestFieldVariableMappingDimensional:
    """Test FieldVariableMapping with dimensional filtering."""
    
    def test_create_dimensional_mapping(self, db_session, sample_company):
        """Test creating a field variable mapping with dimension filters."""
        mapping = FieldVariableMapping(
            computed_field_id="test-computed-1",  # Mock IDs
            raw_field_id="test-raw-2",
            variable_name="A",
            coefficient=1.0,
            dimension_filter={"gender": "Male", "age": "<30"},
            aggregation_type="SPECIFIC_DIMENSION"
        )
        db_session.add(mapping)
        db_session.commit()
        
        assert mapping.mapping_id is not None
        assert mapping.dimension_filter == {"gender": "Male", "age": "<30"}
        assert mapping.aggregation_type == "SPECIFIC_DIMENSION"
        
        # Test direct attribute access instead of helper methods
        assert mapping.dimension_filter is not None
        assert mapping.dimension_filter == {"gender": "Male", "age": "<30"}
    
    def test_sum_all_dimensions_mapping(self, db_session, sample_company, sample_framework):
        """Test mapping that sums across all dimensions."""
        # Create fields
        raw_field = FrameworkDataField(
            framework_id=sample_framework.framework_id,
            company_id=sample_company.id,
            field_name="Employee Count by Demographics",
            field_code="EMP_COUNT_DEMO",
            value_type="NUMBER"
        )
        computed_field = FrameworkDataField(
            framework_id=sample_framework.framework_id,
            company_id=sample_company.id,
            field_name="Total Employee Count",
            field_code="TOTAL_EMP_COUNT",
            value_type="NUMBER",
            is_computed=True,
            formula_expression="A"
        )
        db_session.add(raw_field)
        db_session.add(computed_field)
        db_session.flush()
        
        mapping = FieldVariableMapping(
            computed_field_id=computed_field.field_id,
            raw_field_id=raw_field.field_id,
            variable_name="A",
            coefficient=1.0,
            aggregation_type="SUM_ALL_DIMENSIONS"
        )
        db_session.add(mapping)
        db_session.commit()
        
        assert mapping.aggregation_type == "SUM_ALL_DIMENSIONS"
        assert mapping.dimension_filter is None


class TestAggregationServiceDimensional:
    """Test AggregationService with dimensional data."""
    
    def setup_dimensional_data(self, db_session, sample_company, sample_framework, sample_entity):
        """Set up test data with multiple dimensions."""
        # Create raw field for employee count by demographics
        raw_field = FrameworkDataField(
            framework_id=sample_framework.framework_id,
            company_id=sample_company.id,
            field_name="Employee Count by Demographics",
            field_code="EMP_COUNT_DEMO",
            value_type="NUMBER"
        )
        db_session.add(raw_field)
        db_session.flush()
        
        # Create ESG data with different dimensional breakdowns
        # Male employees by age group
        male_under_30 = ESGData(
            field_id=raw_field.field_id,
            entity_id=sample_entity.id,
            raw_value="25.0",
            reporting_date=date(2024, 1, 1),
            company_id=sample_company.id,
            calculated_value=25.0,
            dimension_values={"gender": "Male", "age": "<30"}
        )
        male_30_50 = ESGData(
            field_id=raw_field.field_id,
            entity_id=sample_entity.id,
            raw_value="30.0",
            reporting_date=date(2024, 1, 1),
            company_id=sample_company.id,
            calculated_value=30.0,
            dimension_values={"gender": "Male", "age": "30-50"}
        )
        male_over_50 = ESGData(
            field_id=raw_field.field_id,
            entity_id=sample_entity.id,
            raw_value="15.0",
            reporting_date=date(2024, 1, 1),
            company_id=sample_company.id,
            calculated_value=15.0,
            dimension_values={"gender": "Male", "age": ">50"}
        )
        
        # Female employees by age group
        female_under_30 = ESGData(
            field_id=raw_field.field_id,
            entity_id=sample_entity.id,
            raw_value="20.0",
            reporting_date=date(2024, 1, 1),
            company_id=sample_company.id,
            calculated_value=20.0,
            dimension_values={"gender": "Female", "age": "<30"}
        )
        female_30_50 = ESGData(
            field_id=raw_field.field_id,
            entity_id=sample_entity.id,
            raw_value="35.0",
            reporting_date=date(2024, 1, 1),
            company_id=sample_company.id,
            calculated_value=35.0,
            dimension_values={"gender": "Female", "age": "30-50"}
        )
        female_over_50 = ESGData(
            field_id=raw_field.field_id,
            entity_id=sample_entity.id,
            raw_value="10.0",
            reporting_date=date(2024, 1, 1),
            company_id=sample_company.id,
            calculated_value=10.0,
            dimension_values={"gender": "Female", "age": ">50"}
        )
        
        db_session.add_all([
            male_under_30, male_30_50, male_over_50,
            female_under_30, female_30_50, female_over_50
        ])
        db_session.commit()
        
        return raw_field
    
    def test_specific_dimension_aggregation(self, db_session, sample_company, sample_framework, sample_entity):
        """Test aggregation with specific dimension filtering."""
        raw_field = self.setup_dimensional_data(db_session, sample_company, sample_framework, sample_entity)
        
        # Create computed field for male employees only
        computed_field = FrameworkDataField(
            framework_id=sample_framework.framework_id,
            company_id=sample_company.id,
            field_name="Total Male Employees",
            field_code="TOTAL_MALE_EMP",
            value_type="NUMBER",
            is_computed=True,
            formula_expression="A"
        )
        db_session.add(computed_field)
        db_session.flush()
        
        # Create mapping with gender filter
        mapping = FieldVariableMapping(
            computed_field_id=computed_field.field_id,
            raw_field_id=raw_field.field_id,
            variable_name="A",
            coefficient=1.0,
            dimension_filter={"gender": "Male"},
            aggregation_type="SPECIFIC_DIMENSION"
        )
        db_session.add(mapping)
        db_session.commit()
        
        # Create assignment for the computed field
        computed_assignment = DataPointAssignment(
            field_id=computed_field.field_id,
            entity_id=sample_entity.id,
            company_id=sample_company.id,
            frequency='Annual',
            assigned_by=1  # Using user ID 1 (super admin from seed data)
        )
        db_session.add(computed_assignment)
        db_session.commit()
        
        # Test aggregation service
        aggregation_service = AggregationService()
        
        # Create custom rule for summing dimensional data
        from app.services.aggregation import AggregationRule, AggregationMethod
        sum_rule = AggregationRule(
            method=AggregationMethod.SUM,
            lookback_months=12,
            is_required=True
        )
        
        # The aggregation should sum only Male employees: 25 + 30 + 15 = 70
        result = aggregation_service._aggregate_dependency_values(
            raw_field.field_id,
            sample_entity.id,
            date(2024, 1, 1),
            sum_rule,
            computed_assignment,
            mapping
        )
        
        assert result == 70.0
    
    def test_sum_all_dimensions_aggregation(self, db_session, sample_company, sample_framework, sample_entity):
        """Test aggregation that sums all dimensional values."""
        raw_field = self.setup_dimensional_data(db_session, sample_company, sample_framework, sample_entity)
        
        # Create computed field for total employees
        computed_field = FrameworkDataField(
            framework_id=sample_framework.framework_id,
            company_id=sample_company.id,
            field_name="Total Employees",
            field_code="TOTAL_EMP",
            value_type="NUMBER",
            is_computed=True,
            formula_expression="A"
        )
        db_session.add(computed_field)
        db_session.flush()
        
        # Create mapping without dimension filter
        mapping = FieldVariableMapping(
            computed_field_id=computed_field.field_id,
            raw_field_id=raw_field.field_id,
            variable_name="A",
            coefficient=1.0,
            aggregation_type="SUM_ALL_DIMENSIONS"
        )
        db_session.add(mapping)
        db_session.commit()
        
        # Create assignment for the computed field
        computed_assignment = DataPointAssignment(
            field_id=computed_field.field_id,
            entity_id=sample_entity.id,
            company_id=sample_company.id,
            frequency='Annual',
            assigned_by=1  # Using user ID 1 (super admin from seed data)
        )
        db_session.add(computed_assignment)
        db_session.commit()
        
        # Test aggregation service
        aggregation_service = AggregationService()
        
        # Create custom rule for summing dimensional data
        from app.services.aggregation import AggregationRule, AggregationMethod
        sum_rule = AggregationRule(
            method=AggregationMethod.SUM,
            lookback_months=12,
            is_required=True
        )
        
        # The aggregation should sum all employees: 25+30+15+20+35+10 = 135
        result = aggregation_service._aggregate_dependency_values(
            raw_field.field_id,
            sample_entity.id,
            date(2024, 1, 1),
            sum_rule,
            computed_assignment,
            mapping
        )
        
        assert result == 135.0


class TestDimensionAPIEndpoints:
    """Test dimension management API endpoints."""
    
    def test_create_dimension_endpoint(self, client, app, db_session, sample_company, sample_user):
        """Test POST /admin/dimensions endpoint."""
        # First, perform login to establish proper session
        login_response = client.post(
            '/login',
            data={
                'email': sample_user.email,
                'password': 'password'
            },
            headers={'Host': f'{sample_company.slug}.localhost:5000'}
        )
        
        # Should redirect to dashboard after successful login
        assert login_response.status_code in [200, 302]
            
        dimension_data = {
            'name': 'Gender',
            'description': 'Employee gender classification',  
            'values': [
                {'value': 'Male', 'display_name': 'Male'},
                {'value': 'Female', 'display_name': 'Female'},
                {'value': 'Other', 'display_name': 'Other/Prefer not to say'}
            ]
        }
        
        # Make API request with proper authentication
        response = client.post(
            '/admin/dimensions',
            data=json.dumps(dimension_data),
            content_type='application/json',
            headers={'Host': f'{sample_company.slug}.localhost:5000'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'dimension_id' in data
        
        # Verify dimension was created
        dimension = Dimension.query.filter_by(name='Gender').first()
        assert dimension is not None
        assert len(dimension.dimension_values) == 3
    
    def test_get_dimensions_endpoint(self, client, app, db_session, sample_company, sample_user):
        """Test GET /admin/dimensions endpoint."""
        # Create test dimension
        dimension = Dimension(
            name="Age Group",
            company_id=sample_company.id,
            description="Employee age groups"
        )
        db_session.add(dimension)
        db_session.flush()
        
        dim_value = DimensionValue(
            dimension_id=dimension.dimension_id,
            value="<30",
            company_id=sample_company.id,
            display_name="Under 30",
            display_order=0
        )
        db_session.add(dim_value)
        db_session.commit()
        
        # First, perform login to establish proper session
        login_response = client.post(
            '/login',
            data={
                'email': sample_user.email,
                'password': 'password'
            },
            headers={'Host': f'{sample_company.slug}.localhost:5000'}
        )
        
        # Should redirect to dashboard after successful login  
        assert login_response.status_code in [200, 302]
        
        # Make API request with proper authentication
        response = client.get(
            '/admin/dimensions',
            headers={'Host': f'{sample_company.slug}.localhost:5000'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['dimensions']) == 1
        assert data['dimensions'][0]['name'] == 'Age Group'
        assert len(data['dimensions'][0]['values']) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 