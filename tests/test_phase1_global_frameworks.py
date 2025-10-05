"""
Test suite for Phase 1: Global vs Company-Specific Frameworks implementation.

Tests the core functionality of framework classification and service enhancements.
"""

import pytest
import uuid
from app import create_app, db
from app.models import Company, Framework, FrameworkDataField, User
from app.services import frameworks_service
from app.services.initial_data import create_initial_data


@pytest.fixture
def app():
    """Create and configure a test app."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def setup_test_data(app):
    """Setup test data for global framework tests."""
    with app.app_context():
        # Create initial data (includes global provider company)
        create_initial_data()
        
        # Create a second company for testing
        test_company = Company(
            name="Test Company",
            slug="test-company"
        )
        db.session.add(test_company)
        db.session.commit()
        
        # Get the global provider company
        global_provider = Company.get_global_provider()
        
        return {
            'global_provider': global_provider,
            'test_company': test_company
        }


class TestCompanyModel:
    """Test Company model enhancements."""
    
    def test_global_provider_designation(self, app, setup_test_data):
        """Test global provider designation functionality."""
        with app.app_context():
            data = setup_test_data
            global_provider = data['global_provider']
            test_company = data['test_company']
            
            # Test initial state
            assert global_provider.is_global_framework_provider is True
            assert test_company.is_global_framework_provider is False
            
            # Test get_global_provider
            provider = Company.get_global_provider()
            assert provider.id == global_provider.id
            
            # Test get_global_provider_id
            provider_id = Company.get_global_provider_id()
            assert provider_id == global_provider.id
    
    def test_set_global_provider(self, app, setup_test_data):
        """Test setting a new global provider."""
        with app.app_context():
            data = setup_test_data
            global_provider = data['global_provider']
            test_company = data['test_company']
            
            # Set test company as global provider
            result = Company.set_global_provider(test_company.id)
            assert result is True
            
            # Verify the change
            db.session.refresh(global_provider)
            db.session.refresh(test_company)
            
            assert global_provider.is_global_framework_provider is False
            assert test_company.is_global_framework_provider is True
            
            # Verify new provider is returned
            new_provider = Company.get_global_provider()
            assert new_provider.id == test_company.id


class TestFrameworkService:
    """Test framework service enhancements."""
    
    def test_get_global_provider_company_id(self, app, setup_test_data):
        """Test getting global provider company ID."""
        with app.app_context():
            data = setup_test_data
            global_provider = data['global_provider']
            
            provider_id = frameworks_service.get_global_provider_company_id()
            assert provider_id == global_provider.id
    
    def test_is_global_framework(self, app, setup_test_data):
        """Test framework type detection."""
        with app.app_context():
            data = setup_test_data
            global_provider = data['global_provider']
            test_company = data['test_company']
            
            # Get existing frameworks from initial data
            global_frameworks = Framework.query.filter_by(company_id=global_provider.id).all()
            assert len(global_frameworks) > 0
            
            # Test global framework detection
            global_framework = global_frameworks[0]
            assert frameworks_service.is_global_framework(global_framework.framework_id) is True
            
            # Create a company-specific framework
            company_framework = Framework(
                framework_id=str(uuid.uuid4()),
                framework_name="Company Test Framework",
                description="Test framework for company",
                company_id=test_company.id
            )
            db.session.add(company_framework)
            db.session.commit()
            
            # Test company framework detection
            assert frameworks_service.is_global_framework(company_framework.framework_id) is False
    
    def test_separate_frameworks_by_type(self, app, setup_test_data):
        """Test framework separation by type."""
        with app.app_context():
            data = setup_test_data
            global_provider = data['global_provider']
            test_company = data['test_company']
            
            # Create a company-specific framework
            company_framework = Framework(
                framework_id=str(uuid.uuid4()),
                framework_name="Company Test Framework",
                description="Test framework for company",
                company_id=test_company.id
            )
            db.session.add(company_framework)
            db.session.commit()
            
            # Test separation for test company
            frameworks_by_type = frameworks_service.separate_frameworks_by_type(test_company.id)
            
            assert 'global' in frameworks_by_type
            assert 'company' in frameworks_by_type
            assert len(frameworks_by_type['global']) > 0  # Should have global frameworks
            assert len(frameworks_by_type['company']) == 1  # Should have one company framework
            
            # Verify global frameworks are from global provider
            for fw in frameworks_by_type['global']:
                assert fw.company_id == global_provider.id
            
            # Verify company frameworks are from test company
            for fw in frameworks_by_type['company']:
                assert fw.company_id == test_company.id
    
    def test_get_framework_type_info(self, app, setup_test_data):
        """Test framework type information retrieval."""
        with app.app_context():
            data = setup_test_data
            global_provider = data['global_provider']
            test_company = data['test_company']
            
            # Get a global framework
            global_frameworks = Framework.query.filter_by(company_id=global_provider.id).all()
            global_framework = global_frameworks[0]
            
            # Test type info for global framework from test company perspective
            type_info = frameworks_service.get_framework_type_info(
                global_framework.framework_id, 
                test_company.id
            )
            
            assert type_info['framework_exists'] is True
            assert type_info['is_global'] is True
            assert type_info['is_editable'] is False  # Not editable by test company
            assert type_info['owner_company_id'] == global_provider.id
            
            # Create and test company framework
            company_framework = Framework(
                framework_id=str(uuid.uuid4()),
                framework_name="Company Test Framework",
                description="Test framework for company",
                company_id=test_company.id
            )
            db.session.add(company_framework)
            db.session.commit()
            
            type_info = frameworks_service.get_framework_type_info(
                company_framework.framework_id, 
                test_company.id
            )
            
            assert type_info['framework_exists'] is True
            assert type_info['is_global'] is False
            assert type_info['is_editable'] is True  # Editable by test company
            assert type_info['owner_company_id'] == test_company.id
    
    def test_list_frameworks_with_global(self, app, setup_test_data):
        """Test framework listing with global frameworks included."""
        with app.app_context():
            data = setup_test_data
            global_provider = data['global_provider']
            test_company = data['test_company']
            
            # Create a company-specific framework
            company_framework = Framework(
                framework_id=str(uuid.uuid4()),
                framework_name="Company Test Framework",
                description="Test framework for company",
                company_id=test_company.id
            )
            db.session.add(company_framework)
            db.session.commit()
            
            # Test listing with global frameworks included
            frameworks = frameworks_service.list_frameworks(
                test_company.id, 
                include_global=True
            )
            
            # Should have both global and company frameworks
            global_frameworks = [fw for fw in frameworks if fw['is_global']]
            company_frameworks = [fw for fw in frameworks if not fw['is_global']]
            
            assert len(global_frameworks) > 0
            assert len(company_frameworks) == 1
            
            # Test global framework properties
            for fw in global_frameworks:
                assert fw['is_global'] is True
                assert fw['is_editable'] is False
                assert fw['owner_company_id'] == global_provider.id
            
            # Test company framework properties
            for fw in company_frameworks:
                assert fw['is_global'] is False
                assert fw['is_editable'] is True
                assert fw['owner_company_id'] == test_company.id
    
    def test_list_frameworks_without_global(self, app, setup_test_data):
        """Test framework listing without global frameworks."""
        with app.app_context():
            data = setup_test_data
            test_company = data['test_company']
            
            # Create a company-specific framework
            company_framework = Framework(
                framework_id=str(uuid.uuid4()),
                framework_name="Company Test Framework",
                description="Test framework for company",
                company_id=test_company.id
            )
            db.session.add(company_framework)
            db.session.commit()
            
            # Test listing without global frameworks
            frameworks = frameworks_service.list_frameworks(
                test_company.id, 
                include_global=False
            )
            
            # Should only have company frameworks
            assert len(frameworks) == 1
            assert all(not fw['is_global'] for fw in frameworks)
            assert all(fw['is_editable'] for fw in frameworks)


class TestAPIIntegration:
    """Test API integration with Phase 1 changes."""
    
    def test_chart_data_global_vs_company(self, app, setup_test_data):
        """Test chart data shows global vs company distribution."""
        with app.app_context():
            data = setup_test_data
            test_company = data['test_company']
            
            # Create a company-specific framework
            company_framework = Framework(
                framework_id=str(uuid.uuid4()),
                framework_name="Company Test Framework",
                description="Test framework for company",
                company_id=test_company.id
            )
            db.session.add(company_framework)
            db.session.commit()
            
            # Test chart data
            chart_data = frameworks_service.get_chart_data(test_company.id)
            
            assert 'framework_type_distribution' in chart_data
            distribution = chart_data['framework_type_distribution']
            
            assert 'global' in distribution
            assert 'company' in distribution
            assert distribution['global'] > 0  # Should have global frameworks
            assert distribution['company'] == 1  # Should have one company framework


if __name__ == '__main__':
    pytest.main([__file__]) 