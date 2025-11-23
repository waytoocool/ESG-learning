#!/usr/bin/env python3
"""
Comprehensive Validation Engine Test Suite
Tests all validation engine components according to testing-manual.md
"""

import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://test-company-alpha.127-0-0-1.nip.io:8000"
TEST_USER = "bob@alpha.com"
TEST_PASSWORD = "user123"
TEST_ADMIN = "alice@alpha.com"
TEST_ADMIN_PASSWORD = "admin123"

class ValidationEngineTests:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Host': 'test-company-alpha.127-0-0-1.nip.io:8000'
        })
        self.results = []

    def log_result(self, test_name, passed, message="", details=""):
        """Log test result"""
        result = {
            'test': test_name,
            'passed': passed,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status}: {test_name}")
        if message:
            print(f"  Message: {message}")
        if details:
            print(f"  Details: {details}")

    def login_user(self, email, password):
        """Login as user"""
        try:
            # Get login page first to get CSRF token if needed
            response = self.session.get(f"{BASE_URL}/login")

            # Login
            response = self.session.post(
                f"{BASE_URL}/login",
                data={'email': email, 'password': password},
                allow_redirects=True
            )

            if response.status_code == 200 and 'dashboard' in response.url.lower():
                self.log_result("Login", True, f"Logged in as {email}")
                return True
            else:
                self.log_result("Login", False, f"Failed to login as {email}",
                              f"Status: {response.status_code}, URL: {response.url}")
                return False
        except Exception as e:
            self.log_result("Login", False, f"Exception during login: {str(e)}")
            return False

    def test_validation_api_endpoint(self):
        """Test Case 3.1: Validation API - Successful Validation"""
        print("\n" + "="*60)
        print("TEST: Validation API Endpoint")
        print("="*60)

        # Login as user
        if not self.login_user(TEST_USER, TEST_PASSWORD):
            return

        # Test data
        test_data = {
            "field_id": "0f944ca1-4052-45c8-8e9e-3fbcf84ba44c",  # Total rate of new hires
            "entity_id": 3,  # Alpha Factory
            "value": 1500,
            "reporting_date": "2026-03-31",
            "assignment_id": None,
            "dimension_values": None,
            "has_attachments": False
        }

        try:
            response = self.session.post(
                f"{BASE_URL}/api/user/validate-submission",
                json=test_data,
                headers={'Content-Type': 'application/json'}
            )

            print(f"  Status Code: {response.status_code}")
            print(f"  Response: {response.text[:500]}")

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    validation = data.get('validation', {})
                    self.log_result(
                        "Validation API Endpoint",
                        True,
                        f"API returned success",
                        f"Passed: {validation.get('passed')}, Risk Score: {validation.get('risk_score')}, Flags: {len(validation.get('flags', []))}"
                    )

                    # Print validation details
                    print("\n  Validation Details:")
                    print(f"    Passed: {validation.get('passed')}")
                    print(f"    Risk Score: {validation.get('risk_score')}")
                    print(f"    Flags Count: {len(validation.get('flags', []))}")
                    for i, flag in enumerate(validation.get('flags', []), 1):
                        print(f"    Flag {i}: [{flag.get('severity')}] {flag.get('message')}")
                else:
                    self.log_result(
                        "Validation API Endpoint",
                        False,
                        "API returned success=false",
                        f"Error: {data.get('error')}"
                    )
            else:
                self.log_result(
                    "Validation API Endpoint",
                    False,
                    f"API returned status {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_result(
                "Validation API Endpoint",
                False,
                f"Exception: {str(e)}"
            )

    def test_company_settings_threshold(self):
        """Test Case 4.8: Company Settings UI - Validation Threshold"""
        print("\n" + "="*60)
        print("TEST: Company Settings Validation Threshold")
        print("="*60)

        # Login as admin
        if not self.login_user(TEST_ADMIN, TEST_ADMIN_PASSWORD):
            return

        try:
            # Get current settings
            response = self.session.get(f"{BASE_URL}/admin/company-settings")

            if response.status_code == 200:
                # Check if validation threshold field exists in HTML
                if 'validation_trend_threshold_pct' in response.text:
                    self.log_result(
                        "Company Settings - Threshold Field Exists",
                        True,
                        "Validation threshold field found in HTML"
                    )
                else:
                    self.log_result(
                        "Company Settings - Threshold Field Exists",
                        False,
                        "Validation threshold field NOT found in HTML"
                    )

                # Try to update threshold
                update_response = self.session.post(
                    f"{BASE_URL}/admin/company-settings",
                    data={
                        'fy_end_month': 3,
                        'fy_end_day': 31,
                        'data_due_days': 10,
                        'validation_trend_threshold_pct': 25.0
                    }
                )

                if update_response.status_code in [200, 302]:
                    self.log_result(
                        "Company Settings - Update Threshold",
                        True,
                        "Successfully updated validation threshold to 25.0%"
                    )

                    # Reset to default
                    self.session.post(
                        f"{BASE_URL}/admin/company-settings",
                        data={
                            'fy_end_month': 3,
                            'fy_end_day': 31,
                            'data_due_days': 10,
                            'validation_trend_threshold_pct': 20.0
                        }
                    )
                else:
                    self.log_result(
                        "Company Settings - Update Threshold",
                        False,
                        f"Failed to update threshold, status: {update_response.status_code}"
                    )
            else:
                self.log_result(
                    "Company Settings Access",
                    False,
                    f"Cannot access company settings, status: {response.status_code}"
                )
        except Exception as e:
            self.log_result(
                "Company Settings Test",
                False,
                f"Exception: {str(e)}"
            )

    def test_validation_service_unit_tests(self):
        """Test Case 2: Validation Service Unit Tests"""
        print("\n" + "="*60)
        print("TEST: Validation Service Unit Tests (Backend)")
        print("="*60)

        try:
            # Import validation service
            import sys
            sys.path.insert(0, '/Users/prateekgoyal/Desktop/Prateek/ESG DataVault Development/Claude/sakshi-learning')

            from app.services.validation_service import ValidationService

            # Test 1: Variance Calculation
            variance = ValidationService._calculate_variance(150, 100)
            if variance == 50.0:
                self.log_result("Variance Calculation (150 vs 100)", True, f"Result: {variance}%")
            else:
                self.log_result("Variance Calculation (150 vs 100)", False,
                              f"Expected 50.0, got {variance}")

            # Test 2: Risk Score Calculation
            flags = [
                {'severity': 'error'},      # +25
                {'severity': 'warning'},    # +10
                {'severity': 'warning'},    # +10
                {'severity': 'info'}        # +2
            ]
            score = ValidationService._calculate_risk_score(flags)
            expected = 47
            if score == expected:
                self.log_result("Risk Score Calculation", True, f"Result: {score}")
            else:
                self.log_result("Risk Score Calculation", False,
                              f"Expected {expected}, got {score}")

            # Test 3: Period Label Formatting
            monthly = ValidationService._format_period_label(2024, 11, 'Monthly')
            quarterly = ValidationService._format_period_label(2024, 12, 'Quarterly')
            annual = ValidationService._format_period_label(2024, 3, 'Annual')

            tests = [
                (monthly, 'Nov 2024', 'Monthly format'),
                (quarterly, 'Q4 2024', 'Quarterly format'),
                (annual, 'FY 2024', 'Annual format')
            ]

            for result, expected, test_name in tests:
                if result == expected:
                    self.log_result(f"Period Label - {test_name}", True, f"Result: {result}")
                else:
                    self.log_result(f"Period Label - {test_name}", False,
                                  f"Expected '{expected}', got '{result}'")

        except Exception as e:
            self.log_result(
                "Validation Service Unit Tests",
                False,
                f"Exception: {str(e)}"
            )

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total*100):.1f}%")

        if failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if not result['passed']:
                    print(f"  - {result['test']}")
                    if result['message']:
                        print(f"    {result['message']}")

        # Save results to file
        results_file = '/Users/prateekgoyal/Desktop/Prateek/ESG DataVault Development/Claude/sakshi-learning/test_results/validation_engine_test_results.json'
        try:
            import os
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            with open(results_file, 'w') as f:
                json.dump({
                    'summary': {
                        'total': total,
                        'passed': passed,
                        'failed': failed,
                        'success_rate': passed/total*100
                    },
                    'results': self.results
                }, f, indent=2)
            print(f"\nResults saved to: {results_file}")
        except Exception as e:
            print(f"\nFailed to save results: {e}")

def main():
    """Run all tests"""
    print("="*60)
    print("VALIDATION ENGINE - COMPREHENSIVE TEST SUITE")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tests = ValidationEngineTests()

    # Run tests
    tests.test_validation_service_unit_tests()
    tests.test_validation_api_endpoint()
    tests.test_company_settings_threshold()

    # Print summary
    tests.print_summary()

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

if __name__ == "__main__":
    main()
