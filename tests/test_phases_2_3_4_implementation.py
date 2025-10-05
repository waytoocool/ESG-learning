"""
Test suite for Phases 2, 3, and 4 implementation
Tests topic management, dependency tracking, and UX enhancements
"""

import pytest
import json
from app import create_app, db
from app.models import (Framework, FrameworkDataField, Topic, FieldVariableMapping, 
                       DataPointAssignment, Company, User, Entity)
from app.utils.unit_conversions import UnitConverter, convert_to_field_default
from app.utils.field_import_templates import FieldImportTemplate


class TestPhase2Topics:
    """Test Phase 2: Topic model & user-defined categories."""
    
    def test_topic_creation(self, test_data):
        """Test creating topics with hierarchy."""
        framework = test_data['framework']
        
        # Create parent topic
        parent_topic = Topic(
            name="Environmental",
            description="Environmental sustainability topics",
            framework_id=framework.framework_id
        )
        db.session.add(parent_topic)
        db.session.flush()
        
        # Create child topic
        child_topic = Topic(
            name="Energy",
            description="Energy consumption topics",
            framework_id=framework.framework_id,
            parent_id=parent_topic.topic_id
        )
        db.session.add(child_topic)
        db.session.commit()
        
        # Test hierarchy
        assert parent_topic.level == 0
        assert child_topic.level == 1
        assert child_topic.parent == parent_topic
        assert parent_topic.children[0] == child_topic
        assert child_topic.get_full_path() == "Environmental > Energy"


class TestPhase3DependencyTracking:
    """Test Phase 3: Enhanced dependency tracking."""
    
    def test_field_dependencies(self, test_data):
        """Test dependency tracking for computed fields."""
        framework = test_data['framework']
        
        # Create raw fields
        field_a = FrameworkDataField(
            framework_id=framework.framework_id,
            field_name="Field A",
            field_code="field_a",
            value_type="NUMBER"
        )
        field_b = FrameworkDataField(
            framework_id=framework.framework_id,
            field_name="Field B", 
            field_code="field_b",
            value_type="NUMBER"
        )
        db.session.add_all([field_a, field_b])
        db.session.flush()
        
        # Create computed field
        computed_field = FrameworkDataField(
            framework_id=framework.framework_id,
            field_name="Field C",
            field_code="field_c",
            value_type="NUMBER",
            is_computed=True,
            formula_expression="A + B"
        )
        db.session.add(computed_field)
        db.session.flush()
        
        # Create variable mappings
        mapping_a = FieldVariableMapping(
            computed_field_id=computed_field.field_id,
            raw_field_id=field_a.field_id,
            variable_name="A"
        )
        mapping_b = FieldVariableMapping(
            computed_field_id=computed_field.field_id,
            raw_field_id=field_b.field_id,
            variable_name="B"
        )
        db.session.add_all([mapping_a, mapping_b])
        db.session.commit()
        
        # Test dependency methods
        assert field_a.has_dependants() == True
        assert field_b.has_dependants() == True
        assert computed_field.has_dependants() == False
        
        dependants_a = field_a.get_dependants()
        assert len(dependants_a) == 1
        assert dependants_a[0] == computed_field


class TestPhase4UXEnhancements:
    """Test Phase 4: UX polish & quality-of-life improvements."""
    
    def test_unit_conversion(self):
        """Test unit conversion functionality."""
        # Test energy conversions
        result, success, error = UnitConverter.convert_value(1000, 'kWh', 'MWh')
        assert success == True
        assert result == 1.0
        assert error is None
        
        # Test invalid conversion
        result, success, error = UnitConverter.convert_value(100, 'kWh', 'USD')
        assert success == False
        assert 'different categories' in error
    
    def test_field_import_templates(self):
        """Test field import template functionality."""
        # Test getting available templates
        templates = FieldImportTemplate.get_available_templates()
        assert 'gri' in templates
        assert templates['gri']['name'] == 'GRI Standards'
        assert templates['gri']['field_count'] > 0


# Fixtures for tests
@pytest.fixture
def test_data(app):
    """Create test data for phase testing."""
    with app.app_context():
        # Create company
        company = Company(name="Test Company", domain="test.com")
        db.session.add(company)
        db.session.flush()
        
        # Create user
        user = User(
            email="test@test.com",
            password_hash="hashed_password",
            role="admin",
            company_id=company.id
        )
        db.session.add(user)
        db.session.flush()
        
        # Create framework
        framework = Framework(
            framework_name="Test Framework",
            description="Test framework for phases"
        )
        db.session.add(framework)
        db.session.flush()
        
        # Create entity
        entity = Entity(
            name="Test Entity",
            entity_type="subsidiary",
            company_id=company.id
        )
        db.session.add(entity)
        db.session.commit()
        
        return {
            'company': company,
            'user': user,
            'framework': framework,
            'entity': entity
        }
 