#!/usr/bin/env python3
"""
Test script for Validation API endpoints
Tests Phase 3: API Endpoints implementation
"""

import sys
import json
from datetime import datetime, date
from app import create_app, db
from app.models.user import User
from app.models.company import Company
from app.models.entity import Entity
from app.models.framework import FrameworkDataField
from app.models.data_assignment import DataPointAssignment
from app.models.esg_data import ESGData

def test_validation_api():
    """Test the validation API endpoint"""
    print("\n" + "="*60)
    print("VALIDATION API - ENDPOINT TESTS")
    print("="*60 + "\n")

    app = create_app()

    with app.app_context():
        # Get test user (alice@alpha.com from test-company-alpha)
        test_user = User.query.filter_by(email='alice@alpha.com').first()
        if not test_user:
            print("❌ Test user not found!")
            return False

        print(f"✓ Test user: {test_user.email} (Company: {test_user.company.name})")
        print(f"✓ Company ID: {test_user.company_id}")

        # Get a test assignment for this company
        assignment = DataPointAssignment.query.filter_by(
            company_id=test_user.company_id,
            series_status='active'
        ).first()

        if not assignment:
            print("❌ No active assignments found for test company!")
            return False

        print(f"✓ Test assignment: {assignment.field.field_name}")
        print(f"✓ Field ID: {assignment.field_id}")
        print(f"✓ Entity ID: {assignment.entity_id}")

        # Get existing data for comparison
        existing_data = ESGData.query.filter_by(
            company_id=test_user.company_id,
            field_id=assignment.field_id,
            entity_id=assignment.entity_id
        ).order_by(ESGData.reporting_date.desc()).first()

        if existing_data:
            print(f"✓ Found historical data: {existing_data.value} on {existing_data.reporting_date}")
            test_value = float(existing_data.value) * 1.5  # 50% increase to trigger warning
        else:
            print("⚠ No historical data found, using test value 1500")
            test_value = 1500.0

        print("\n" + "-"*60)
        print("[Test 1] Validate Submission Endpoint")
        print("-"*60)

        # Create test client and login
        # Set the correct tenant subdomain in the host header
        client = app.test_client()

        # Login with tenant context
        response = client.post('/login',
            data={
                'email': 'alice@alpha.com',
                'password': 'admin123'
            },
            headers={'Host': 'test-company-alpha.127-0-0-1.nip.io:8000'},
            follow_redirects=True)

        if response.status_code != 200:
            print(f"❌ Login failed with status {response.status_code}")
            return False

        print("✓ Login successful")

        # Test validation endpoint
        test_data = {
            'field_id': assignment.field_id,
            'entity_id': assignment.entity_id,
            'value': test_value,
            'reporting_date': datetime.now().strftime('%Y-%m-%d'),
            'assignment_id': assignment.id,
            'dimension_values': None,
            'has_attachments': False
        }

        print(f"\nTest payload:")
        print(json.dumps(test_data, indent=2))

        response = client.post(
            '/api/user/validate-submission',
            json=test_data,
            content_type='application/json',
            headers={'Host': 'test-company-alpha.127-0-0-1.nip.io:8000'}
        )

        print(f"\nResponse status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Validation endpoint failed with status {response.status_code}")
            print(f"Response: {response.get_data(as_text=True)}")
            return False

        result = response.get_json()
        print(f"✓ Validation endpoint returned 200 OK")
        print(f"\nValidation result:")
        print(json.dumps(result, indent=2))

        if not result.get('success'):
            print(f"❌ Validation failed: {result.get('error')}")
            return False

        validation = result.get('validation', {})
        print(f"\n✓ Validation completed successfully")
        print(f"  - Passed: {validation.get('passed')}")
        print(f"  - Risk Score: {validation.get('risk_score')}")
        print(f"  - Flags Count: {len(validation.get('flags', []))}")

        for i, flag in enumerate(validation.get('flags', []), 1):
            print(f"  - Flag {i}: [{flag.get('severity')}] {flag.get('message')}")

        print("\n" + "-"*60)
        print("[Test 2] Validation Stats Endpoint")
        print("-"*60)

        response = client.get('/api/user/validation-stats?days=30',
            headers={'Host': 'test-company-alpha.127-0-0-1.nip.io:8000'})

        print(f"Response status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Stats endpoint failed with status {response.status_code}")
            print(f"Response: {response.get_data(as_text=True)}")
            return False

        stats = response.get_json()
        print(f"✓ Stats endpoint returned 200 OK")
        print(f"\nValidation stats:")
        print(json.dumps(stats, indent=2))

        print("\n" + "="*60)
        print("✓ ALL VALIDATION API TESTS PASSED!")
        print("="*60 + "\n")

        return True


def test_company_settings():
    """Test that company settings page loads with validation threshold"""
    print("\n" + "="*60)
    print("COMPANY SETTINGS - UI TEST")
    print("="*60 + "\n")

    app = create_app()

    with app.app_context():
        # Get test company
        company = Company.query.filter_by(slug='test-company-alpha').first()

        if not company:
            print("❌ Test company not found!")
            return False

        print(f"✓ Test company: {company.name}")
        print(f"✓ Current validation threshold: {company.validation_trend_threshold_pct}%")

        # Create test client and login as admin
        client = app.test_client()

        response = client.post('/login',
            data={
                'email': 'alice@alpha.com',
                'password': 'admin123'
            },
            headers={'Host': 'test-company-alpha.127-0-0-1.nip.io:8000'},
            follow_redirects=True)

        if response.status_code != 200:
            print(f"❌ Login failed with status {response.status_code}")
            return False

        print("✓ Login successful")

        # Test GET company settings page
        print("\n" + "-"*60)
        print("[Test 1] GET Company Settings Page")
        print("-"*60)

        response = client.get('/admin/company-settings',
            headers={'Host': 'test-company-alpha.127-0-0-1.nip.io:8000'})

        print(f"Response status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Company settings page failed with status {response.status_code}")
            return False

        html = response.get_data(as_text=True)

        # Check if validation threshold field is present
        if 'validation_trend_threshold_pct' in html:
            print("✓ Validation threshold field found in HTML")
        else:
            print("❌ Validation threshold field NOT found in HTML")
            return False

        if 'Trend Variance Threshold' in html:
            print("✓ Field label found in HTML")
        else:
            print("❌ Field label NOT found in HTML")
            return False

        # Test POST update company settings
        print("\n" + "-"*60)
        print("[Test 2] POST Update Company Settings")
        print("-"*60)

        new_threshold = 15.5

        response = client.post('/admin/company-settings',
            data={
                'fy_end_month': company.fy_end_month,
                'fy_end_day': company.fy_end_day,
                'data_due_days': company.data_due_days,
                'validation_trend_threshold_pct': new_threshold
            },
            headers={'Host': 'test-company-alpha.127-0-0-1.nip.io:8000'},
            follow_redirects=True)

        print(f"Response status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Settings update failed with status {response.status_code}")
            return False

        # Verify the threshold was updated
        db.session.refresh(company)

        if company.validation_trend_threshold_pct == new_threshold:
            print(f"✓ Validation threshold updated successfully to {new_threshold}%")
        else:
            print(f"❌ Threshold not updated. Current value: {company.validation_trend_threshold_pct}%")
            return False

        # Reset to default
        company.validation_trend_threshold_pct = 20.0
        db.session.commit()
        print("✓ Reset threshold to default (20%)")

        print("\n" + "="*60)
        print("✓ ALL COMPANY SETTINGS TESTS PASSED!")
        print("="*60 + "\n")

        return True


if __name__ == '__main__':
    try:
        # Run tests
        api_passed = test_validation_api()
        settings_passed = test_company_settings()

        if api_passed and settings_passed:
            print("\n" + "🎉"*30)
            print("✓ ALL PHASE 3 TESTS PASSED!")
            print("🎉"*30 + "\n")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
