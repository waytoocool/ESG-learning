# Playwright MCP Quick Reference Guide

## Overview
Playwright MCP provides browser automation tools for UI testing and interaction within Claude Code.

## Prerequisites
```bash
# Start MCP server (required)
npm run mcp:start

# Kill existing Chrome processes if needed
pkill -f chrome
```

## Core Navigation Tools

### 🌐 browser_navigate
```javascript
mcp__playwright__browser_navigate(url)
// Navigate to any URL
```

### 📸 browser_snapshot
```javascript
mcp__playwright__browser_snapshot()
// Get accessibility tree of current page (better than screenshot for actions)
```

### 📷 browser_take_screenshot
```javascript
mcp__playwright__browser_take_screenshot(filename?, fullPage?)
// Capture visual screenshot
```

## Interaction Tools

### 🖱️ browser_click
```javascript
mcp__playwright__browser_click(element, ref)
// Click on elements - requires element description + ref from snapshot
```

### ⌨️ browser_type
```javascript
mcp__playwright__browser_type(element, ref, text, submit?)
// Type text into input fields
```

### 📝 browser_fill_form
```javascript
mcp__playwright__browser_fill_form(fields[])
// Fill multiple form fields at once
fields: [{name, type, ref, value}]
```

### 🔽 browser_select_option
```javascript
mcp__playwright__browser_select_option(element, ref, values[])
// Select dropdown options
```

## Browser Control

### ❌ browser_close
```javascript
mcp__playwright__browser_close()
// Close the browser page
```

### 📐 browser_resize
```javascript
mcp__playwright__browser_resize(width, height)
// Resize browser window for responsive testing
```

### 🗨️ browser_handle_dialog
```javascript
mcp__playwright__browser_handle_dialog(accept, promptText?)
// Handle alerts, confirms, prompts
```

### ⏳ browser_wait_for
```javascript
mcp__playwright__browser_wait_for(time?, text?, textGone?)
// Wait for conditions or time
```

## Advanced Tools

### 🔍 browser_evaluate
```javascript
mcp__playwright__browser_evaluate(function, element?, ref?)
// Execute JavaScript in page context
```

### 📊 browser_console_messages
```javascript
mcp__playwright__browser_console_messages()
// Get all console logs/errors
```

### 🌐 browser_network_requests
```javascript
mcp__playwright__browser_network_requests()
// Get all network requests since page load
```

### 📂 browser_tabs
```javascript
mcp__playwright__browser_tabs(action: 'list'|'new'|'close'|'select', index?)
// Manage browser tabs
```

## Important Considerations

### ⚠️ Common Issues & Solutions

1. **"Browser already in use" error**
   ```bash
   pkill -f chrome  # Kill Chrome processes
   ```

2. **Element Selection**
   - Always use `browser_snapshot` first to get element refs
   - Use exact `ref` values from snapshot (e.g., "e7", "e10")
   - Provide human-readable element descriptions

3. **Authentication Flow**
   ```javascript
   // Example: Login sequence
   browser_navigate("http://127-0-0-1.nip.io:8000/login")
   browser_fill_form([
     {name: "Email", type: "textbox", ref: "e7", value: "admin@yourdomain.com"},
     {name: "Password", type: "textbox", ref: "e9", value: "changeme"}
   ])
   browser_click("Login button", "e10")
   browser_handle_dialog(true)  // Accept any confirmation
   ```

4. **Best Practices**
   - Use `browser_snapshot` over screenshots for element interaction
   - Always handle dialogs that may appear
   - Check console messages for JavaScript errors
   - Wait for page loads/redirects when needed
   - Close browser when done to free resources

5. **Impersonation for Multi-Tenant Apps**
   - SUPER_ADMIN users must impersonate to access tenant-specific pages
   - Navigate to `/superadmin/users` → Click "Impersonate" → Accept dialog

## Quick Test Template

```javascript
// 1. Setup
pkill -f chrome
browser_navigate(url)

// 2. Get page state
browser_snapshot()
browser_console_messages()

// 3. Interact
browser_click(element, ref)
browser_type(element, ref, text)

// 4. Validate
browser_console_messages()  // Check for errors
browser_take_screenshot()    // Visual proof

// 5. Cleanup
browser_close()
```

## Error Monitoring

Key console errors to watch for:
- `TypeError`: Type mismatches (e.g., using Array methods on Map)
- `ReferenceError`: Undefined variables/functions
- `SyntaxError`: JavaScript syntax issues
- `404/500`: Resource/API failures

---
**Pro Tip**: Always use `browser_snapshot` before interacting with elements - it provides the required `ref` values and shows current page state.