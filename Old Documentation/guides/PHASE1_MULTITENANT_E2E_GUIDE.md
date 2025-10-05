# Phase 1 Multi-Tenant E2E Test Guide - Complete Workflow

## Overview
This guide covers the comprehensive end-to-end tests for Phase 1 implementation in a multi-tenant environment, testing the complete workflow from super admin to end user with full Phase 1 metadata:

**Phase 1 Features Tested:**
- `field_code` (business keys with auto-generation)
- `unit_category` (energy, money, emission, etc.)
- `default_unit` (kWh, USD, kg, etc.)
- `value_type` (NUMBER, TEXT, BOOLEAN, DATE)

**Multi-Tenant Workflow:**
1. Super Admin creates company
2. Super Admin adds admin to company
3. Admin creates entity and users
4. Admin creates framework with Phase 1 metadata
5. Admin assigns framework to entities
6. Users fill in data

## Prerequisites

### 1. Application Setup
Ensure your ESG DataVault application is running:
```bash
python run.py
```
The app should be accessible at `http://127-0-0-1.nip.io:8000/`

### 2. Super Admin Credentials
Make sure you have super admin credentials configured:
- **Email**: `admin@yourdomain.com`
- **Password**: `secure-password-123`

(Update the credentials in `playwright.config.js` and test files if different)

## Installation

### Quick Setup
```bash
./setup-e2e-tests.sh
```

### Manual Setup
```bash
npm install
npm run install:playwright
npx playwright install
```

## Running Tests

### New Multi-Tenant Test
The main test file is now: `playwright/tests/phase1-multitenant-workflow.spec.js`

```bash
# Run the comprehensive multi-tenant workflow test
npm run playwright:test phase1-multitenant-workflow

# Interactive mode
npm run playwright:ui

# Debug mode
npx playwright test phase1-multitenant-workflow --debug
```

## Complete Test Workflow

### Test 1: Full Multi-Tenant Workflow
**Duration**: ~60-90 seconds
**Steps**:

#### 🔐 Step 1: Super Admin Login
- Navigates to `/login`
- Logs in with super admin credentials
- Verifies access to super admin dashboard

#### 🏢 Step 2: Create Company
- Navigates to `/superadmin/companies`
- Creates "Company 1" with:
  - Domain: company1.test
  - Contact Email: contact@company1.test
  - Contact Phone: +1234567890

#### 👨‍💼 Step 3: Add Admin to Company
- Navigates to `/superadmin/users`
- Creates company admin with:
  - Name: Test Admin
  - Email: testadmin@company1.test
  - Username: testadmin1
  - Role: Admin
  - Company: Company 1

#### 🎭 Step 4: Impersonate Admin
- Finds admin user in users list
- Clicks "Impersonate" button
- Verifies impersonation banner is visible

#### 🏗️ Step 5: Add Entity (as Admin)
- Navigates to `/admin/entities`
- Creates "Entity1" subsidiary

#### 👤 Step 6: Add User to Entity
- Navigates to `/admin/users`
- Creates "User1" with:
  - Name: User1
  - Email: user1@company1.test
  - Username: user1
  - Entity: Entity1

#### 📋 Step 7: Create Framework with Phase 1 Metadata
- Navigates to `/admin/frameworks`
- Creates "Test ESG Framework" with field:
  - **Name**: Energy Consumption
  - **Field Code**: energy_consumption_test (auto-generated + override)
  - **Value Type**: NUMBER
  - **Unit Category**: energy
  - **Default Unit**: kWh
  - **Description**: Full Phase 1 metadata description

#### 🔗 Step 8: Assign Framework to Entity
- Navigates to `/admin/assign_data_points`
- Selects framework and Entity1
- Assigns all framework fields to the entity

#### 🚪 Step 9: Exit Impersonation
- Clicks "Exit Impersonation"
- Returns to super admin dashboard

#### 👥 Step 10: Impersonate User
- Finds User1 in users list
- Impersonates User1

#### 📊 Step 11: Fill Dummy Data
- Navigates to `/user/dashboard`
- Fills energy consumption field with dummy data (150.5)
- Saves data successfully

### Test 2: Phase 1 Metadata Verification
**Purpose**: Verify that Phase 1 metadata is preserved throughout the multi-tenant workflow

**Steps**:
1. Login as super admin
2. Impersonate the admin
3. Navigate to frameworks
4. Open framework details modal
5. Verify all Phase 1 metadata is displayed:
   - Field name
   - Field code
   - Unit category
   - Default unit
   - Value type

## Test Data Structure

### Company Data
```javascript
company: {
  name: 'Company 1',
  domain: 'company1.test',
  contact_email: 'contact@company1.test',
  contact_phone: '+1234567890'
}
```

### Admin Data
```javascript
admin: {
  name: 'Test Admin',
  email: 'testadmin@company1.test',
  username: 'testadmin1',
  password: 'AdminPass123!'
}
```

### Entity Data
```javascript
entity: {
  name: 'Entity1',
  description: 'A subsidiary of the company'
}
```

### User Data
```javascript
user: {
  name: 'User1',
  email: 'user1@company1.test',
  username: 'user1',
  password: 'UserPass123!'
}
```

### Framework & Field Data
```javascript
framework: {
  name: 'Test ESG Framework',
  description: 'Framework for testing Phase 1 implementation'
},
field: {
  name: 'Energy Consumption',
  field_code: 'energy_consumption_test',
  value_type: 'NUMBER',
  unit_category: 'energy',
  default_unit: 'kWh',
  description: 'Test field for energy consumption with full Phase 1 metadata'
}
```

## Helper Functions

The test includes modular helper functions for each step:

- `loginAsSuperAdmin(page)` - Handles super admin authentication
- `createCompany(page, companyData)` - Creates new company
- `addAdminToCompany(page, adminData, companyName)` - Adds admin user
- `impersonateUser(page, userIdentifier)` - Impersonates any user
- `exitImpersonation(page)` - Exits impersonation mode
- `addEntity(page, entityData)` - Adds entity to company
- `addUserToEntity(page, userData, entityName)` - Adds user to entity
- `createFramework(page, frameworkData, fieldData)` - Creates framework with Phase 1 metadata
- `assignFrameworkToEntity(page, frameworkName, entityName)` - Assigns framework fields
- `fillDummyData(page)` - Fills user data

## Configuration Changes

### Updated Base URL
```javascript
baseURL: 'http://127-0-0-1.nip.io:8000'
```

### Updated Credentials
```javascript
const testConfig = {
  superAdminEmail: 'admin@yourdomain.com',
  superAdminPassword: 'secure-password-123'
};
```

## Test Output Example

```bash
$ npm run playwright:test phase1-multitenant-workflow

Running 2 tests using 1 worker

🚀 Starting comprehensive multi-tenant workflow test...
📋 Step 1: Login as Super Admin
🏢 Step 2: Create Company  
👨‍💼 Step 3: Add Admin to Company
🎭 Step 4: Impersonate Admin
🏗️ Step 5: Add Entity
👤 Step 6: Add User to Entity
📋 Step 7: Create Framework with Phase 1 Metadata
🔗 Step 8: Assign Framework Fields to Entity
🚪 Step 9: Exit Impersonation
👥 Step 10: Impersonate User
📊 Step 11: Fill Dummy Data
✅ Complete multi-tenant workflow test completed successfully!

🔍 Testing Phase 1 metadata in multi-tenant context...
✅ Phase 1 metadata verification completed!

  2 passed (89.3s)
```

## Debugging Tips

### Interactive Mode
```bash
npm run playwright:ui
```
- Watch each step execute in real time
- Pause at any step to inspect the page
- View network requests and responses

### Debug Mode
```bash
npx playwright test phase1-multitenant-workflow --debug
```
- Step through each action
- Inspect element selectors
- Debug failing steps

### Screenshots and Videos
Playwright automatically captures:
- Screenshots on failure
- Videos of test execution
- Trace files for detailed debugging

## Selectors Strategy

The test uses flexible selectors to handle different UI implementations:

```javascript
// Multiple selector options for flexibility
await page.click('a[href*="create_company"], button[id*="create"], .btn:has-text("Create Company"), .btn:has-text("Add Company")');

// Text-based selectors for robustness
await page.click('.btn:has-text("Impersonate")');

// Form field selectors with fallbacks
await page.fill('input[name="company_name"], #company_name', companyData.name);
```

## Error Handling

### Common Issues

1. **Impersonation Banner Not Found**
   - Check if impersonation UI is implemented
   - Verify selector matches your HTML structure

2. **Company Creation Fails**
   - Verify company creation form fields
   - Check for validation errors

3. **Framework Assignment Fails**
   - Ensure assign_data_points page exists
   - Verify field selection UI

4. **User Data Input Fails**
   - Check user dashboard implementation
   - Verify data input form structure

### Timeouts
All operations include appropriate timeouts:
- Success messages: 10 seconds
- Page navigation: 5 seconds
- Element interactions: 3 seconds

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Multi-Tenant E2E Tests
on: [push, pull_request]
jobs:
  playwright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm install
      - run: npx playwright install
      - run: python run.py &
      - run: sleep 10  # Wait for server to start
      - run: npm run playwright:test phase1-multitenant-workflow
```

## Extending the Tests

### Adding More Field Types
```javascript
const additionalFields = [
  {
    name: 'Water Usage',
    value_type: 'NUMBER',
    unit_category: 'volume',
    default_unit: 'liters'
  },
  {
    name: 'Compliance Status',
    value_type: 'BOOLEAN',
    unit_category: '',
    default_unit: ''
  }
];
```

### Testing Multiple Companies
```javascript
const companies = [
  { name: 'Company 1', domain: 'company1.test' },
  { name: 'Company 2', domain: 'company2.test' }
];
```

## Summary

This comprehensive test suite validates:

✅ **Complete Multi-Tenant Flow** - From super admin to end user
✅ **Phase 1 Metadata Integration** - All new fields work in multi-tenant context
✅ **User Role Isolation** - Proper access controls and impersonation
✅ **Data Assignment Flow** - Framework to entity to user pipeline
✅ **Real-World Scenario** - Matches actual usage patterns

The test provides confidence that Phase 1 implementation works correctly in the full multi-tenant ESG DataVault environment! 