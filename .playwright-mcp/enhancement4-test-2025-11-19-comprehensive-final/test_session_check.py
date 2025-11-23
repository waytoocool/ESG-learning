#!/usr/bin/env python3
"""
Quick test to check if session is persisting validated_rows
"""

import requests

BASE_URL = "http://test-company-alpha.127-0-0-1.nip.io:8000"
LOGIN_EMAIL = "bob@alpha.com"
LOGIN_PASSWORD = "user123"

session = requests.Session()

# Login
response = session.post(f"{BASE_URL}/login", data={"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD}, allow_redirects=True)
print(f"Login status: {response.status_code}")

# Download template
response = session.post(f"{BASE_URL}/api/user/v2/bulk-upload/template", json={"filter": "pending"})
print(f"Template download status: {response.status_code}")

# Upload template (use one from earlier test)
template_path = "/Users/prateekgoyal/Desktop/Prateek/ESG DataVault Development/Claude/sakshi-learning/.playwright-mcp/enhancement4-test-2025-11-19-comprehensive-final/templates-all-tests/Template-pending-E2E-FILLED-20251119-090442.xlsx"

with open(template_path, 'rb') as f:
    response = session.post(f"{BASE_URL}/api/user/v2/bulk-upload/upload", files={'file': f})
    result = response.json()
    print(f"Upload response: {result}")
    upload_id = result.get('upload_id')

# Validate
response = session.post(f"{BASE_URL}/api/user/v2/bulk-upload/validate", json={"upload_id": upload_id})
result = response.json()
print(f"\nValidation response:")
print(f"  success: {result.get('success')}")
print(f"  valid: {result.get('valid')}")
print(f"  valid_count: {result.get('valid_count')}")

# Immediately check session by trying to submit
response = session.post(f"{BASE_URL}/api/user/v2/bulk-upload/submit", data={"upload_id": upload_id})
print(f"\nSubmit response: {response.status_code}")
print(f"  {response.json()}")
