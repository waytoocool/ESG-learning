"""
Test script to verify notes functionality fix for dimensional data.
Tests both simple and dimensional data submissions with notes.
"""

import requests
import json
from datetime import date

# Test configuration
BASE_URL = "http://test-company-alpha.127-0-0-1.nip.io:8000"
TEST_USER = {
    "email": "bob@alpha.com",
    "password": "user123"
}

class NotesFixTester:
    def __init__(self):
        self.session = requests.Session()
        self.cookies = None

    def login(self):
        """Login to get session cookie"""
        print("🔐 Logging in as bob@alpha.com...")
        response = self.session.post(
            f"{BASE_URL}/login",
            data=TEST_USER,
            allow_redirects=False
        )

        if response.status_code in [200, 302]:
            self.cookies = self.session.cookies
            print("✅ Login successful!")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False

    def test_simple_data_with_notes(self):
        """Test Case 1: Submit simple data with notes"""
        print("\n📝 Test 1: Simple data with notes")

        payload = {
            "field_id": "test-field-123",  # Replace with actual field ID
            "entity_id": 1,  # Replace with actual entity ID
            "reporting_date": "2025-11-30",
            "raw_value": "100",
            "notes": "Test note for simple data - Enhancement #2 verification"
        }

        response = self.session.post(
            f"{BASE_URL}/user/v2/api/submit-simple-data",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Simple data saved with notes")
                print(f"   Data ID: {result.get('data_id')}")
                return True
            else:
                print(f"❌ Failed: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    def test_dimensional_data_with_notes(self):
        """Test Case 2: Submit dimensional data with notes"""
        print("\n📊 Test 2: Dimensional data with notes")

        payload = {
            "field_id": "test-field-dim-123",  # Replace with actual field ID
            "entity_id": 1,  # Replace with actual entity ID
            "reporting_date": "2025-11-30",
            "dimensional_data": {
                "dimensions": ["gender"],
                "breakdowns": [
                    {
                        "dimensions": {"gender": "Male"},
                        "raw_value": 50
                    },
                    {
                        "dimensions": {"gender": "Female"},
                        "raw_value": 50
                    }
                ]
            },
            "notes": "Test note for dimensional data - Enhancement #2 FIX verification"
        }

        response = self.session.post(
            f"{BASE_URL}/user/v2/api/submit-dimensional-data",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Dimensional data saved with notes")
                print(f"   Data ID: {result.get('data_id')}")
                print(f"   Total: {result.get('overall_total')}")
                return True
            else:
                print(f"❌ Failed: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    def test_update_notes(self):
        """Test Case 3: Update existing notes"""
        print("\n✏️  Test 3: Update existing notes")

        # First create entry
        payload_create = {
            "field_id": "test-field-update-123",
            "entity_id": 1,
            "reporting_date": "2025-11-30",
            "raw_value": "75",
            "notes": "Original note"
        }

        response = self.session.post(
            f"{BASE_URL}/user/v2/api/submit-simple-data",
            json=payload_create,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200 or not response.json().get('success'):
            print("❌ Failed to create initial entry")
            return False

        print("✅ Initial entry created with notes: 'Original note'")

        # Now update with new notes
        payload_update = {
            "field_id": "test-field-update-123",
            "entity_id": 1,
            "reporting_date": "2025-11-30",
            "raw_value": "85",  # Changed value
            "notes": "UPDATED note - this should replace the original"
        }

        response = self.session.post(
            f"{BASE_URL}/user/v2/api/submit-simple-data",
            json=payload_update,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Notes updated successfully")
                print(f"   New value: 85")
                print(f"   New notes: 'UPDATED note - this should replace the original'")
                return True
            else:
                print(f"❌ Failed: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False

    def run_all_tests(self):
        """Run all test cases"""
        print("=" * 60)
        print("🧪 ENHANCEMENT #2 NOTES FIX - TEST SUITE")
        print("=" * 60)

        if not self.login():
            print("\n❌ Test suite aborted - login failed")
            return

        results = []
        results.append(("Simple data with notes", self.test_simple_data_with_notes()))
        results.append(("Dimensional data with notes", self.test_dimensional_data_with_notes()))
        results.append(("Update notes", self.test_update_notes()))

        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status} - {name}")

        print(f"\n{passed}/{total} tests passed ({(passed/total)*100:.0f}%)")

        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Enhancement #2 fix is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")

if __name__ == "__main__":
    tester = NotesFixTester()
    tester.run_all_tests()
