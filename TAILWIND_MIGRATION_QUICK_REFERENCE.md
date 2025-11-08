# Tailwind Migration Quick Reference Guide

## Quick Start

### Access the New Dashboard
```
http://test-company-alpha.127-0-0-1.nip.io:8000/user/dashboard-v2
```

### File Locations
- **New Template:** `/app/templates/user_v2/dashboard_tailwind.html`
- **Original Template:** `/app/templates/user_v2/dashboard.html`
- **Documentation:** `/USER_DASHBOARD_TAILWIND_MIGRATION.md`

## Common Tasks

### Testing the New Dashboard

1. **Start the Flask application:**
```bash
python3 run.py
```

2. **Login as a test user:**
   - URL: `http://test-company-alpha.127-0-0-1.nip.io:8000/login`
   - User: bob@alpha.com
   - Password: user123

3. **Navigate to the new dashboard:**
   - Click on "Dashboard V2" in navigation, or
   - Visit `/user/dashboard-v2` directly

### Switch Between Versions

**From New Dashboard to Legacy:**
- Click the "Legacy View" button in the header

**From Legacy to New Dashboard:**
- Update the route to point to `dashboard_tailwind.html`

### Rollback to Original

```bash
# If the new version is already in use
cp app/templates/user_v2/dashboard_bootstrap_backup.html app/templates/user_v2/dashboard.html

# Restart Flask
pkill -f "python3 run.py"
python3 run.py
```

## Component Reference

### Statistics Cards
```html
<!-- Card Structure -->
<div class="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
    <div class="p-5">
        <div class="flex items-center">
            <div class="flex-shrink-0">
                <span class="material-icons text-primary-600 text-4xl">icon_name</span>
            </div>
            <div class="ml-5 w-0 flex-1">
                <dl>
                    <dt class="text-sm font-medium text-gray-500 truncate">Label</dt>
                    <dd class="text-3xl font-bold text-gray-900">{{ value }}</dd>
                </dl>
            </div>
        </div>
    </div>
</div>
```

### Field Cards
```html
<!-- Field Card Structure -->
<div class="field-card bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg">
    <!-- Header with badges -->
    <div class="px-4 pt-4 pb-2">
        <h3 class="text-sm font-semibold">{{ field_name }}</h3>
        <span class="badge">Status</span>
    </div>

    <!-- Body with type and frequency -->
    <div class="px-4 py-3 space-y-2">
        <span class="badge">Type</span>
        <span class="badge">Frequency</span>
    </div>

    <!-- Footer with action buttons -->
    <div class="px-4 pb-4">
        <button class="btn-primary">Action</button>
    </div>
</div>
```

### Badges

#### Status Badges
```html
<!-- Complete -->
<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
    Complete
</span>

<!-- Pending -->
<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
    Pending
</span>
```

#### Type Badges
```html
<!-- Raw Input -->
<span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
    <span class="material-icons text-xs mr-1">edit</span>
    Raw Input
</span>

<!-- Computed -->
<span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
    <span class="material-icons text-xs mr-1">functions</span>
    Computed
</span>
```

#### Frequency Badges
```html
<!-- Annual -->
<span class="bg-red-100 text-red-800">Annual</span>

<!-- Quarterly -->
<span class="bg-orange-100 text-orange-800">Quarterly</span>

<!-- Monthly -->
<span class="bg-green-100 text-green-800">Monthly</span>
```

### Buttons

#### Primary Button
```html
<button class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
    <span class="material-icons text-sm mr-2">icon_name</span>
    Button Text
</button>
```

#### Secondary Button
```html
<button class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50">
    Button Text
</button>
```

### Form Inputs

#### Text Input
```html
<input type="text"
       class="block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
       placeholder="Enter text">
```

#### Select Dropdown
```html
<select class="block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm">
    <option value="">Select option</option>
    <option value="1">Option 1</option>
</select>
```

#### Date Input
```html
<input type="date"
       class="block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm">
```

## Color Palette

### Primary Green
- `primary-50`: #f0fdf4 (lightest)
- `primary-500`: #16a34a (brand color)
- `primary-700`: #166534 (dark)

### Status Colors
- **Success/Complete:** `green-100`, `green-800`
- **Warning/Pending:** `yellow-100`, `yellow-800`
- **Error/Overdue:** `red-100`, `red-800`
- **Info:** `blue-100`, `blue-800`

### Neutral Colors
- **Background:** `gray-50` (light), `gray-900` (dark)
- **Cards:** `white` (light), `gray-800` (dark)
- **Text:** `gray-900` (light), `white` (dark)
- **Borders:** `gray-300` (light), `gray-600` (dark)

## Responsive Breakpoints

```javascript
// Tailwind default breakpoints
sm: '640px',   // Small devices (landscape phones)
md: '768px',   // Medium devices (tablets)
lg: '1024px',  // Large devices (desktops)
xl: '1280px',  // Extra large devices (large desktops)
```

### Grid Layouts
```html
<!-- Responsive grid: 1-2-3-4 columns -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
    <!-- Items -->
</div>

<!-- Statistics: 1-2-4 columns -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
    <!-- Cards -->
</div>
```

## Dark Mode

### Enable Dark Mode
```javascript
// Add to <html> tag
<html class="dark">

// Or toggle programmatically
document.documentElement.classList.toggle('dark');
```

### Dark Mode Classes
```html
<!-- Background -->
<div class="bg-white dark:bg-gray-800">

<!-- Text -->
<p class="text-gray-900 dark:text-white">

<!-- Borders -->
<div class="border-gray-300 dark:border-gray-600">
```

## JavaScript Integration

### Search and Filter
```javascript
// Search functionality
const searchInput = document.getElementById('searchMetrics');
searchInput.addEventListener('input', applyFilters);

// Filter by status
const filterStatus = document.getElementById('filterStatus');
filterStatus.addEventListener('change', applyFilters);
```

### Modal Integration
```javascript
// Keep existing Bootstrap modal code
const modal = new bootstrap.Modal(document.getElementById('dataCollectionModal'));

// Open modal
document.querySelectorAll('.open-data-modal').forEach(button => {
    button.addEventListener('click', function() {
        modal.show();
    });
});
```

### Preserve Phase 4 Features
```javascript
// Auto-save still works
window.autoSaveHandler = new AutoSaveHandler({...});

// Keyboard shortcuts still work
window.keyboardShortcuts = new KeyboardShortcutHandler({...});

// Number formatter still works
window.attachNumberFormatters();
```

## Debugging

### Enable Debug Logging
```javascript
// In browser console
localStorage.setItem('debug', 'true');
```

### Check for Issues
```javascript
// Verify Tailwind is loaded
console.log(tailwind.config);

// Check if Material Icons are loaded
console.log(document.querySelector('link[href*="material-icons"]'));

// Verify JavaScript handlers
console.log(window.autoSaveHandler);
console.log(window.keyboardShortcuts);
```

### Common Console Errors

**"tailwind is not defined"**
- Ensure Tailwind CDN script is in `<head>` before config

**"Material Icons not displaying"**
- Check if Google Fonts link is present
- Verify network access to fonts.googleapis.com

**"Modal not opening"**
- Verify Bootstrap JavaScript is loaded
- Check for JavaScript errors in console

## Performance Tips

### Production Build
```bash
# Build optimized Tailwind CSS
npx tailwindcss -i ./src/input.css -o ./app/static/css/tailwind.min.css --minify

# Update template to use local file instead of CDN
<link href="{{ url_for('static', filename='css/tailwind.min.css') }}" rel="stylesheet">
```

### Lazy Loading
```javascript
// Images
<img loading="lazy" src="..." />

// Performance optimizer already handles lazy loading
window.perfOptimizer.initialize();
```

## Testing Checklist

```markdown
- [ ] Statistics cards show correct counts
- [ ] Search filters fields correctly
- [ ] Category filters work
- [ ] Status filters work
- [ ] Field type filters work
- [ ] Modal opens and closes
- [ ] Data entry form works
- [ ] File upload works
- [ ] Auto-save activates
- [ ] Keyboard shortcuts work
- [ ] Computation context modal opens
- [ ] Dark mode toggle works
- [ ] Responsive on mobile
- [ ] Responsive on tablet
- [ ] Responsive on desktop
```

## Quick Fixes

### Reset Filters
```javascript
document.getElementById('searchMetrics').value = '';
document.getElementById('filterStatus').value = '';
document.getElementById('filterCategory').value = '';
document.getElementById('filterFieldType').value = '';
applyFilters();
```

### Force Refresh Data
```javascript
location.reload();
```

### Clear Auto-save Cache
```javascript
if (window.autoSaveHandler) {
    window.autoSaveHandler.clearDraft();
}
```

## Support

### File an Issue
Include:
- Browser and version
- Steps to reproduce
- Console errors
- Screenshots (if visual issue)

### Contact
Development Team
