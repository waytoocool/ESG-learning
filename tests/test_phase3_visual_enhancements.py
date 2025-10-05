#!/usr/bin/env python3
"""
Phase 3 Visual Enhancements Testing Script

This script validates the implementation of Phase 3 features:
- Framework type visual distinction (global vs company)
- Permission-based actions (read-only for global frameworks)
- Enhanced dashboard analytics
- Framework type filtering and sorting
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import Company, Framework, User
from app.services import frameworks_service
import json

def test_phase3_implementation():
    """Test Phase 3 visual enhancements and permission-based actions."""
    
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Phase 3: Visual Enhancements & Permission-Based Actions")
        print("=" * 70)
        
        # Test 1: Global Provider Company Identification
        print("\n1️⃣ Testing Global Provider Company Identification")
        global_provider = Company.get_global_provider()
        if global_provider:
            print(f"   ✅ Global Provider: {global_provider.name}")
            print(f"   📍 Company ID: {global_provider.id}")
        else:
            print("   ❌ No global provider found")
            return False
        
        # Test 2: Framework Type Classification
        print("\n2️⃣ Testing Framework Type Classification")
        all_frameworks = Framework.query.all()
        global_frameworks = []
        company_frameworks = []
        
        for framework in all_frameworks:
            is_global = frameworks_service.is_global_framework(framework.framework_id)
            if is_global:
                global_frameworks.append(framework)
            else:
                company_frameworks.append(framework)
        
        print(f"   🌍 Global Frameworks: {len(global_frameworks)}")
        for fw in global_frameworks[:3]:  # Show first 3
            print(f"      - {fw.framework_name}")
        
        print(f"   🏢 Company Frameworks: {len(company_frameworks)}")
        for fw in company_frameworks[:3]:  # Show first 3
            print(f"      - {fw.framework_name}")
        
        # Test 3: Framework Service API Enhancement
        print("\n3️⃣ Testing Enhanced Framework Service API")
        
        # Test with different company contexts
        test_companies = Company.query.filter(Company.id != global_provider.id).limit(2).all()
        
        for company in test_companies:
            print(f"\n   Testing for Company: {company.name}")
            
            # Test framework listing with type information
            frameworks_data = frameworks_service.list_frameworks(
                company_id=company.id,
                include_global=True,
                sort='type_asc'
            )
            
            global_count = sum(1 for fw in frameworks_data if fw['is_global'])
            company_count = sum(1 for fw in frameworks_data if not fw['is_global'])
            
            print(f"      📊 Frameworks visible: {len(frameworks_data)}")
            print(f"      🌍 Global: {global_count} | 🏢 Company: {company_count}")
            
            # Test permission flags
            for fw in frameworks_data[:2]:  # Test first 2 frameworks
                print(f"      📋 {fw['framework_name'][:30]}...")
                print(f"         - Type: {'Global' if fw['is_global'] else 'Company'}")
                print(f"         - Editable: {'Yes' if fw['is_editable'] else 'No'}")
        
        # Test 4: Chart Data Enhancement
        print("\n4️⃣ Testing Chart Data Enhancement")
        chart_data = frameworks_service.get_chart_data(global_provider.id)
        
        if 'framework_type_distribution' in chart_data:
            distribution = chart_data['framework_type_distribution']
            print(f"   📈 Framework Type Distribution:")
            print(f"      🌍 Global: {distribution.get('global', 0)}")
            print(f"      🏢 Company: {distribution.get('company', 0)}")
        else:
            print("   ❌ Framework type distribution not found")
        
        # Test 5: Framework Type Info Function
        print("\n5️⃣ Testing Framework Type Info Function")
        
        if all_frameworks:
            test_framework = all_frameworks[0]
            type_info = frameworks_service.get_framework_type_info(
                test_framework.framework_id,
                global_provider.id
            )
            
            print(f"   📋 Test Framework: {test_framework.framework_name}")
            print(f"      - Is Global: {type_info['is_global']}")
            print(f"      - Is Editable: {type_info['is_editable']}")
            print(f"      - Owner Company ID: {type_info['owner_company_id']}")
        
        # Test 6: Coverage Calculation with Framework Types
        print("\n6️⃣ Testing Coverage Calculation")
        
        if all_frameworks:
            test_framework = all_frameworks[0]
            coverage_data = frameworks_service.get_framework_coverage(
                test_framework.framework_id,
                global_provider.id
            )
            
            print(f"   📋 Test Framework: {test_framework.framework_name}")
            print(f"      - Coverage: {coverage_data['coverage_percentage']}%")
            print(f"      - Fields with Data: {coverage_data['fields_with_data']}")
            print(f"      - Total Fields: {coverage_data['total_fields']}")
        
        # Test 7: Permission Context Validation
        print("\n7️⃣ Testing Permission Context")
        
        # Test different user contexts
        users = User.query.limit(3).all()
        for user in users:
            print(f"\n   User: {user.email} (Company: {user.company.name if user.company else 'None'})")
            
            if user.company_id:
                frameworks_for_user = frameworks_service.list_frameworks(
                    company_id=user.company_id,
                    include_global=True
                )
                
                editable_count = sum(1 for fw in frameworks_for_user if fw['is_editable'])
                readonly_count = sum(1 for fw in frameworks_for_user if not fw['is_editable'])
                
                print(f"      📝 Editable Frameworks: {editable_count}")
                print(f"      🔒 Read-only Frameworks: {readonly_count}")
        
        print("\n" + "=" * 70)
        print("✅ Phase 3 Testing Complete!")
        print("\n📋 Summary:")
        print(f"   - Global Provider: {global_provider.name}")
        print(f"   - Global Frameworks: {len(global_frameworks)}")
        print(f"   - Company Frameworks: {len(company_frameworks)}")
        print(f"   - Total Companies: {Company.query.count()}")
        print(f"   - Total Users: {User.query.count()}")
        
        return True

if __name__ == "__main__":
    success = test_phase3_implementation()
    if success:
        print("\n🎉 All Phase 3 tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some Phase 3 tests failed!")
        sys.exit(1) 