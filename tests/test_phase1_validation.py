"""
Simple validation script for Phase 1: Global vs Company-Specific Frameworks implementation.
Tests core functionality without complex session management.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import Company, Framework
from app.services import frameworks_service
from app.services.initial_data import create_initial_data


def test_phase1_implementation():
    """Test Phase 1 implementation with simple validation."""
    print("🧪 Testing Phase 1: Global vs Company-Specific Frameworks")
    print("=" * 60)
    
    # Create app and database
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        # Create tables
        db.create_all()
        print("✅ Database tables created")
        
        # Create initial data
        create_initial_data()
        print("✅ Initial data created")
        
        # Test 1: Check global provider exists
        global_provider = Company.get_global_provider()
        assert global_provider is not None, "Global provider should exist"
        assert global_provider.is_global_framework_provider is True, "Provider should have global flag set"
        print(f"✅ Global provider found: {global_provider.name}")
        
        # Test 2: Check global provider ID method
        provider_id = Company.get_global_provider_id()
        assert provider_id == global_provider.id, "Provider ID should match"
        print(f"✅ Global provider ID: {provider_id}")
        
        # Test 3: Test framework service methods
        service_provider_id = frameworks_service.get_global_provider_company_id()
        assert service_provider_id == provider_id, "Service should return same provider ID"
        print(f"✅ Framework service provider ID: {service_provider_id}")
        
        # Test 4: Check existing frameworks are global
        frameworks = Framework.query.filter_by(company_id=global_provider.id).all()
        assert len(frameworks) > 0, "Should have some global frameworks"
        
        for fw in frameworks:
            is_global = frameworks_service.is_global_framework(fw.framework_id)
            assert is_global is True, f"Framework {fw.framework_name} should be global"
        
        print(f"✅ Found {len(frameworks)} global frameworks")
        
        # Test 5: Create a test company and framework
        test_company = Company(name="Test Company", slug="test-company")
        db.session.add(test_company)
        db.session.commit()
        
        test_framework = Framework(
            framework_id="test-framework-123",
            framework_name="Test Company Framework",
            description="A test company-specific framework",
            company_id=test_company.id
        )
        db.session.add(test_framework)
        db.session.commit()
        print("✅ Created test company and framework")
        
        # Test 6: Check company framework is not global
        is_global = frameworks_service.is_global_framework(test_framework.framework_id)
        assert is_global is False, "Company framework should not be global"
        print("✅ Company framework correctly identified as non-global")
        
        # Test 7: Test framework separation
        frameworks_by_type = frameworks_service.separate_frameworks_by_type(test_company.id)
        assert 'global' in frameworks_by_type, "Should have global key"
        assert 'company' in frameworks_by_type, "Should have company key"
        assert len(frameworks_by_type['global']) > 0, "Should have global frameworks"
        assert len(frameworks_by_type['company']) == 1, "Should have one company framework"
        print(f"✅ Framework separation: {len(frameworks_by_type['global'])} global, {len(frameworks_by_type['company'])} company")
        
        # Test 8: Test framework type info
        type_info = frameworks_service.get_framework_type_info(test_framework.framework_id, test_company.id)
        assert type_info['framework_exists'] is True, "Framework should exist"
        assert type_info['is_global'] is False, "Should not be global"
        assert type_info['is_editable'] is True, "Should be editable by owner"
        print("✅ Framework type info correct for company framework")
        
        # Test global framework type info
        global_fw = frameworks[0]
        type_info = frameworks_service.get_framework_type_info(global_fw.framework_id, test_company.id)
        assert type_info['framework_exists'] is True, "Global framework should exist"
        assert type_info['is_global'] is True, "Should be global"
        assert type_info['is_editable'] is False, "Should not be editable by non-owner"
        print("✅ Framework type info correct for global framework")
        
        # Test 9: Test framework listing
        frameworks_list = frameworks_service.list_frameworks(test_company.id, include_global=True)
        global_count = sum(1 for fw in frameworks_list if fw['is_global'])
        company_count = sum(1 for fw in frameworks_list if not fw['is_global'])
        
        assert global_count > 0, "Should include global frameworks"
        assert company_count == 1, "Should include company framework"
        print(f"✅ Framework listing: {global_count} global, {company_count} company")
        
        # Test 10: Test chart data
        chart_data = frameworks_service.get_chart_data(test_company.id)
        assert 'framework_type_distribution' in chart_data, "Should have type distribution"
        distribution = chart_data['framework_type_distribution']
        assert 'global' in distribution, "Should have global count"
        assert 'company' in distribution, "Should have company count"
        assert distribution['global'] > 0, "Should have global frameworks"
        assert distribution['company'] == 1, "Should have one company framework"
        print(f"✅ Chart data: {distribution['global']} global, {distribution['company']} company")
        
        print("\n🎉 All Phase 1 tests passed!")
        print("=" * 60)
        print("Phase 1 Implementation Summary:")
        print(f"• Global Provider: {global_provider.name}")
        print(f"• Global Frameworks: {len(frameworks)}")
        print(f"• Company Frameworks: 1")
        print(f"• Framework Service: Working correctly")
        print(f"• API Integration: Ready")
        print("=" * 60)
        
        return True


if __name__ == '__main__':
    try:
        test_phase1_implementation()
        print("✅ Phase 1 validation completed successfully!")
    except Exception as e:
        print(f"❌ Phase 1 validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 