import pytest
from app import create_app
from app.extensions import db
from app.models.framework import Framework, FrameworkDataField, generate_slug
from app.models.data_assignment import DataPointAssignment
from app.models.esg_data import ESGData
from app.models.entity import Entity
from app.models.company import Company
from app.models.user import User
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def test_data(app):
    """Create test data."""
    with app.app_context():
        # Create test company
        company = Company(name="Test Company", slug="test_company")
        db.session.add(company)
        
        # Create test user
        user = User(
            name="Test User",
            email="test@example.com",
            role="ADMIN",
            company_id=company.id,
            is_email_verified=True
        )
        db.session.add(user)
        
        # Create test entity
        entity = Entity(
            name="Test Entity",
            entity_type="Department",
            company_id=company.id
        )
        db.session.add(entity)
        
        # Create test framework
        framework = Framework(
            framework_name="Test Framework",
            description="Test Framework"
        )
        db.session.add(framework)
        
        db.session.commit()
        
        return {
            'company': company,
            'user': user,
            'entity': entity,
            'framework': framework
        }


class TestSlugGeneration:
    """Test slug generation for field codes."""
    
    def test_basic_slug_generation(self):
        """Test basic slug generation from field names."""
        assert generate_slug("Energy Consumption") == "energy_consumption"
        assert generate_slug("CO2 Emissions") == "co2_emissions"
        assert generate_slug("Water Usage (m³)") == "water_usage_m"
        assert generate_slug("Employee Count") == "employee_count"
    
    def test_special_character_handling(self):
        """Test slug generation with special characters."""
        assert generate_slug("GHG Scope 1 (Direct)") == "ghg_scope_1_direct"
        assert generate_slug("Revenue (USD)") == "revenue_usd"
        assert generate_slug("Waste@Site#1") == "wastesite1"
    
    def test_empty_or_none_input(self):
        """Test slug generation with empty or None input."""
        assert generate_slug("") == ""
        assert generate_slug(None) == ""
        assert generate_slug("   ") == ""


class TestFrameworkDataField:
    """Test FrameworkDataField Phase 1 functionality."""
    
    def test_auto_field_code_generation(self, test_data):
        """Test automatic field code generation."""
        field = FrameworkDataField(
            framework_id=test_data['framework'].framework_id,
            field_name="Energy Consumption",
            value_type="NUMBER"
        )
        db.session.add(field)
        db.session.commit()
        
        assert field.field_code == "energy_consumption"
    
    def test_manual_field_code_override(self, test_data):
        """Test manual field code override."""
        field = FrameworkDataField(
            framework_id=test_data['framework'].framework_id,
            field_name="Energy Consumption",
            field_code="custom_energy_code",
            value_type="NUMBER"
        )
        db.session.add(field)
        db.session.commit()
        
        assert field.field_code == "custom_energy_code"
    
    def test_field_code_uniqueness(self, test_data):
        """Test that field codes must be unique."""
        # Create first field
        field1 = FrameworkDataField(
            framework_id=test_data['framework'].framework_id,
            field_name="Energy Consumption",
            field_code="energy_code",
            value_type="NUMBER"
        )
        db.session.add(field1)
        db.session.commit()
        
        # Try to create second field with same code
        field2 = FrameworkDataField(
            framework_id=test_data['framework'].framework_id,
            field_name="Other Field",
            field_code="energy_code",
            value_type="TEXT"
        )
        db.session.add(field2)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
    
    def test_default_value_type(self, test_data):
        """Test default value type is NUMBER."""
        field = FrameworkDataField(
            framework_id=test_data['framework'].framework_id,
            field_name="Test Field",
            field_code="test_field"
        )
        db.session.add(field)
        db.session.commit()
        
        assert field.value_type == "NUMBER"
    
    def test_unit_metadata(self, test_data):
        """Test unit category and default unit fields."""
        field = FrameworkDataField(
            framework_id=test_data['framework'].framework_id,
            field_name="Energy Consumption",
            field_code="energy_consumption",
            value_type="NUMBER",
            unit_category="energy",
            default_unit="kWh"
        )
        db.session.add(field)
        db.session.commit()
        
        assert field.unit_category == "energy"
        assert field.default_unit == "kWh"


class TestDataPointAssignment:
    """Test DataPointAssignment Phase 1 changes."""
    
    def test_assignment_without_value_type(self, test_data):
        """Test that assignments no longer store value_type."""
        field = FrameworkDataField(
            framework_id=test_data['framework'].framework_id,
            field_name="Test Field",
            field_code="test_field",
            value_type="NUMBER"
        )
        db.session.add(field)
        db.session.commit()
        
        assignment = DataPointAssignment(
            field_id=field.field_id,
            entity_id=test_data['entity'].id,
            company_id=test_data['company'].id,
            fy_start_month=4,
            fy_start_year=2024,
            fy_end_year=2025,
            frequency="Annual",
            assigned_by=test_data['user'].id
        )
        db.session.add(assignment)
        db.session.commit()
        
        # Value type should come from field, not assignment
        assert assignment.value_type == "NUMBER"
        assert assignment.field.value_type == "NUMBER"
    
    def test_effective_unit_property(self, test_data):
        """Test effective_unit property returns assignment unit or field default."""
        field = FrameworkDataField(
            framework_id=test_data['framework'].framework_id,
            field_name="Test Field",
            field_code="test_field",
            value_type="NUMBER",
            default_unit="kWh"
        )
        db.session.add(field)
        db.session.commit()
        
        # Assignment without unit override
        assignment1 = DataPointAssignment(
            field_id=field.field_id,
            entity_id=test_data['entity'].id,
            company_id=test_data['company'].id,
            fy_start_month=4,
            fy_start_year=2024,
            fy_end_year=2025,
            frequency="Annual",
            assigned_by=test_data['user'].id
        )
        db.session.add(assignment1)
        
        # Assignment with unit override
        assignment2 = DataPointAssignment(
            field_id=field.field_id,
            entity_id=test_data['entity'].id,
            company_id=test_data['company'].id,
            unit="MWh",
            fy_start_month=4,
            fy_start_year=2024,
            fy_end_year=2025,
            frequency="Annual",
            assigned_by=test_data['user'].id
        )
        db.session.add(assignment2)
        db.session.commit()
        
        assert assignment1.effective_unit == "kWh"  # Uses field default
        assert assignment2.effective_unit == "MWh"  # Uses assignment override


class TestESGData:
    """Test ESGData Phase 1 changes."""
    
    def test_unit_determination(self, test_data):
        """Test unit determination in ESGData."""
        field = FrameworkDataField(
            framework_id=test_data['framework'].framework_id,
            field_name="Test Field",
            field_code="test_field",
            value_type="NUMBER",
            default_unit="kWh"
        )
        db.session.add(field)
        db.session.commit()
        
        # ESG data without unit (should use field default)
        data1 = ESGData(
            entity_id=test_data['entity'].id,
            field_id=field.field_id,
            raw_value="100",
            reporting_date="2024-12-31",
            company_id=test_data['company'].id
        )
        db.session.add(data1)
        
        # ESG data with explicit unit
        data2 = ESGData(
            entity_id=test_data['entity'].id,
            field_id=field.field_id,
            raw_value="0.1",
            reporting_date="2024-12-31",
            company_id=test_data['company'].id,
            unit="MWh"
        )
        db.session.add(data2)
        db.session.commit()
        
        assert data1.effective_unit == "kWh"  # Uses field default
        assert data2.effective_unit == "MWh"  # Uses explicit unit
    
    def test_value_type_property(self, test_data):
        """Test value_type property comes from field."""
        field = FrameworkDataField(
            framework_id=test_data['framework'].framework_id,
            field_name="Test Field",
            field_code="test_field",
            value_type="BOOLEAN"
        )
        db.session.add(field)
        db.session.commit()
        
        data = ESGData(
            entity_id=test_data['entity'].id,
            field_id=field.field_id,
            raw_value="true",
            reporting_date="2024-12-31",
            company_id=test_data['company'].id
        )
        db.session.add(data)
        db.session.commit()
        
        assert data.value_type == "BOOLEAN" 