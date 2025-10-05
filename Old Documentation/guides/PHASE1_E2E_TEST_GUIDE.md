# Phase 1 E2E Test Guide - Field Creation with Full Metadata

## Overview
This guide covers the end-to-end tests for Phase 1 implementation, specifically testing the happy path for creating framework fields with full metadata including:
- `field_code` (business keys)
- `unit_category` (energy, money, emission, etc.)
- `default_unit` (kWh, USD, kg, etc.)
- `value_type` (NUMBER, TEXT, BOOLEAN, DATE)

## Prerequisites

### 1. Application Setup
Ensure your ESG DataVault application is running:
```bash
python run.py
```
The app should be accessible at `http://localhost:5000`

### 2. Test Data
Make sure you have admin credentials configured:
- **Email**: `admin@datavault.com`
- **Password**: `admin123`

(Update the credentials in `cypress.config.js` and `playwright/tests/phase1-field-creation.spec.js` if different)

## Installation

### Install Node.js Dependencies
```bash
npm install
```

### For Cypress Only
```bash
npm run install:cypress
```

### For Playwright Only
```bash
npm run install:playwright
npx playwright install
```

## Running Tests

### Cypress Tests

#### Interactive Mode (Recommended for Development)
```bash
npm run cypress:open
```
This opens the Cypress Test Runner where you can:
- Select `E2E Testing`
- Choose your browser
- Run individual tests interactively

#### Headless Mode (CI/Production)
```bash
npm run cypress:run
```

### Playwright Tests

#### Interactive Mode
```bash
npm run playwright:ui
```

#### Headless Mode
```bash
npm run playwright:test
```

#### Specific Browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

## Test Scenarios

### 1. Happy Path Test
**File**: `cypress/e2e/phase1-field-creation.cy.js` / `playwright/tests/phase1-field-creation.spec.js`

Tests the complete workflow:
1. Login as admin
2. Navigate to frameworks page
3. Create new framework with basic info
4. Add data point with full Phase 1 metadata:
   - Field name: "Energy Consumption"
   - Field code: "energy_consumption_test" (overriding auto-generated)
   - Value type: "NUMBER"
   - Unit category: "energy"
   - Default unit: "kWh"
   - Description: Full description
5. Submit form
6. Verify success message
7. Verify framework appears in list

### 2. Auto-Generation Test
Tests that field codes are automatically generated from field names:
- "Carbon Emissions" → "carbon_emissions"
- "Water Usage (Liters)" → "water_usage_liters"
- "Employee Count - Full Time" → "employee_count_full_time"

### 3. Validation Test
Tests form validation:
- Required framework name
- Required field names
- HTML5 validation behavior

### 4. Comprehensive Field Types Test
Tests all supported Phase 1 configurations:
- NUMBER fields with energy/money/emission/weight/volume categories
- BOOLEAN fields (no unit categories)
- TEXT fields (no unit categories)
- DATE fields (no unit categories)

### 5. Metadata Preservation Test (Playwright only)
Tests that field metadata is preserved and displayed correctly in the framework details modal.

## Test Data Management

### Automatic Cleanup
The tests use timestamps to create unique framework names, preventing conflicts:
```javascript
const timestamp = Date.now()
const frameworkName = `Test Framework ${timestamp}`
```

### Manual Cleanup
After running tests, you may want to clean up test frameworks:
1. Navigate to `/admin/frameworks`
2. Look for frameworks with "Test" in the name
3. Delete manually (or implement delete functionality in UI)

## Debugging Tests

### Cypress Debugging
- Tests run in interactive mode show real-time browser actions
- Use `cy.pause()` to pause execution
- Browser DevTools available during test execution
- Screenshots/videos available for failed tests

### Playwright Debugging
- Use `await page.pause()` to pause execution
- Run with `--debug` flag: `npx playwright test --debug`
- Trace viewer available: `npx playwright show-trace`
- Screenshots/videos automatically captured on failure

## Configuration

### Cypress Configuration (`cypress.config.js`)
- Base URL: `http://localhost:5000`
- Viewport: 1280x720
- Test credentials in `env` section
- Video/screenshot settings

### Playwright Configuration (`playwright.config.js`)
- Base URL: `http://localhost:5000`
- Multi-browser testing (Chrome, Firefox, Safari)
- Automatic server startup
- Trace/video recording on failure

## Common Issues & Solutions

### 1. Application Not Running
**Error**: Connection refused or timeout
**Solution**: Ensure `python run.py` is running and accessible at `http://localhost:5000`

### 2. Authentication Failures
**Error**: Tests fail at login step
**Solution**: Verify admin credentials in config files match your database

### 3. Database State Issues
**Error**: Tests fail due to existing data
**Solution**: Run tests against a clean test database or implement proper cleanup

### 4. Timing Issues
**Error**: Elements not found or actions fail
**Solution**: Tests include appropriate waits, but you may need to adjust timeouts for slower environments

### 5. Migration Issues
**Error**: Database schema doesn't match expected structure
**Solution**: Ensure all Phase 1 migrations have been applied:
```bash
flask db upgrade
```

## Test Coverage

### Phase 1 Features Covered ✅
- [x] Field code auto-generation from field names
- [x] Manual field code override
- [x] Value type selection (NUMBER, TEXT, BOOLEAN, DATE)
- [x] Unit category selection (energy, money, emission, weight, volume, percentage, time, count)
- [x] Default unit specification
- [x] Field description
- [x] Form validation
- [x] Success message verification
- [x] Framework creation with metadata
- [x] Metadata preservation and display

### Not Covered (Future Enhancements)
- [ ] Framework editing with field metadata updates
- [ ] Field deletion
- [ ] Bulk field operations
- [ ] Field code uniqueness validation UI feedback
- [ ] Unit category validation against default unit

## CI/CD Integration

### GitHub Actions Example
```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  cypress:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm install
      - run: python run.py &
      - run: npm run cypress:run
  
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
      - run: npm run playwright:test
```

## Next Steps

1. **Run the tests** to verify Phase 1 implementation
2. **Review test results** and fix any failing scenarios
3. **Integrate into CI/CD** for automated testing
4. **Extend tests** for Phase 2 features when implemented
5. **Add API tests** to complement UI tests
6. **Performance testing** for large frameworks with many fields

## Support

For issues with these tests:
1. Check the application logs during test execution
2. Review browser console for JavaScript errors
3. Verify database state and migrations
4. Check test configuration matches your environment

The tests are designed to be comprehensive and robust, covering the full happy path for Phase 1 field creation with metadata. They should pass consistently on a properly configured ESG DataVault instance with Phase 1 implementation complete. 