# Session Expiration Fix - Implementation Summary

## Problem Statement

When user sessions expire, AJAX requests fail with a confusing error message:
```
Failed to save data: Unexpected token '<', "<!-- // te"... is not valid JSON
```

### Root Cause

1. **Session Expires** - Flask session times out after period of inactivity
2. **AJAX Request Made** - User tries to save data via JavaScript `fetch()`
3. **302 Redirect** - Server returns `302 Found` redirect to `/login`
4. **Browser Follows Redirect** - Browser automatically follows redirect (transparent to JavaScript)
5. **HTML Login Page Returned** - Final response is HTML login page with status `200 OK`
6. **JSON Parse Fails** - JavaScript tries to parse `<!DOCTYPE html>` as JSON → **ERROR**

### Why Page Refresh Works But AJAX Doesn't

| Action | Behavior |
|--------|----------|
| **Page Navigation** (clicking links, refresh) | Browser recognizes 302 redirect and navigates to login page ✅ |
| **AJAX/Fetch Requests** | Browser follows redirects transparently, JavaScript receives HTML as final response ❌ |

## Solution Implemented

### 1. Session Handler Utility (`session_handler.js`)

Created a global session detection utility that:
- ✅ Detects when response is HTML instead of JSON
- ✅ Identifies the login page by checking content
- ✅ Automatically redirects browser to login with `?next=` parameter
- ✅ Prevents cryptic JSON parsing errors

**Location**: `/app/static/js/common/session_handler.js`

**Key Functions**:
```javascript
// Check response before parsing JSON
await window.handleSessionExpiration(response);

// OR use the enhanced fetch wrapper
const data = await window.fetchWithSessionHandling(url, options);
```

### 2. Updated Components

#### A. Dimensional Data Handler
**File**: `app/static/js/user_v2/dimensional_data_handler.js`
**Line**: 637-640

Added session check before parsing response:
```javascript
// SESSION FIX: Check for session expiration before parsing JSON
if (window.handleSessionExpiration) {
    await window.handleSessionExpiration(response);
}
```

#### B. Data Submission (Validation)
**File**: `app/static/js/user_v2/data_submission.js`
**Line**: 194-197

Added same session check for validation API:
```javascript
// SESSION FIX: Check for session expiration before parsing JSON
if (window.handleSessionExpiration) {
    await window.handleSessionExpiration(response);
}
```

#### C. Dashboard Template
**File**: `app/templates/user_v2/dashboard.html`
**Line**: 567-568

Loaded session handler before all other scripts:
```html
<!-- Session Handler - MUST load first to handle session expiration globally -->
<script src="{{ url_for('static', filename='js/common/session_handler.js') }}"></script>
```

## How It Works Now

### Before Fix
```
User → AJAX Request → Session Expired → 302 Redirect → HTML Login Page
                                                            ↓
                                    JavaScript tries to parse HTML as JSON
                                                            ↓
                                    ERROR: Unexpected token '<'
```

### After Fix
```
User → AJAX Request → Session Expired → 302 Redirect → HTML Login Page
                                                            ↓
                            Session Handler detects HTML response
                                                            ↓
                            Session Handler checks if it's login page
                                                            ↓
                            Browser redirects to: /login?next=/current/page
                                                            ↓
                            User logs in → Redirected back to original page ✅
```

## Testing Instructions

### Test 1: Session Expiration During Data Entry

1. **Login** to the application
2. **Open a data entry modal** (e.g., "Total new hires")
3. **Wait for session to expire** (or manually delete session cookie in DevTools)
4. **Try to save data**
5. **Expected Result**:
   - No JSON parsing error
   - Automatic redirect to login page with message "Session expired - redirecting to login"
   - After login, redirected back to dashboard

### Test 2: Session Expiration During Validation

1. **Login** to the application
2. **Open a simple field** (non-dimensional)
3. **Enter a value that triggers validation** (e.g., significantly different from historical)
4. **Wait for session to expire**
5. **Click Save**
6. **Expected Result**:
   - Automatic redirect to login (no error message)
   - After login, can re-enter data

### Test 3: Normal Operation (Session Active)

1. **Login** to the application
2. **Enter and save data normally**
3. **Expected Result**:
   - Data saves successfully
   - No interruptions or redirects
   - Session handler doesn't interfere with normal operation

## Browser DevTools Testing

### Simulate Session Expiration

1. Open **Chrome DevTools** (F12)
2. Go to **Application** tab
3. Under **Cookies**, find `session` cookie
4. **Delete the session cookie**
5. Try to save data
6. Should see automatic redirect to login

### Monitor Console Logs

Expected console output when session expires:
```
[Session Handler] Session expired - redirecting to login
```

## Additional Considerations

### Flask Session Configuration

Current session timeout can be configured in `app/config.py`:
```python
PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)  # Default: 30 minutes
```

### Recommendations for Production

1. **Session Timeout Warning** - Add a warning 5 minutes before expiration
2. **Keep-Alive Ping** - Ping server every 10 minutes to extend session during active use
3. **Auto-Save Draft** - Save form data to localStorage to prevent data loss
4. **Session Refresh** - Implement invisible session refresh on user activity

### Future Enhancements

Consider implementing these in `session_handler.js`:

```javascript
// Auto-save form data before redirect
function saveFormDataToLocalStorage() {
    // Implementation
}

// Session keep-alive
setInterval(() => {
    fetch('/api/ping').catch(() => {});
}, 10 * 60 * 1000); // Every 10 minutes

// Session timeout warning
function showSessionWarning() {
    // Show modal: "Your session will expire in 5 minutes"
}
```

## Files Changed

| File | Lines Changed | Purpose |
|------|--------------|---------|
| `app/static/js/common/session_handler.js` | NEW FILE | Session detection utility |
| `app/static/js/user_v2/dimensional_data_handler.js` | 637-660 | Added session check |
| `app/static/js/user_v2/data_submission.js` | 194-197 | Added session check |
| `app/templates/user_v2/dashboard.html` | 567-568 | Load session handler |

## Rollback Instructions

If this fix causes issues, rollback by:

1. **Remove session handler script** from dashboard.html (line 567-568)
2. **Revert changes** to dimensional_data_handler.js (remove lines 637-640, 658)
3. **Revert changes** to data_submission.js (remove lines 194-197)
4. **Delete file**: `app/static/js/common/session_handler.js`

## Summary

✅ **Session expiration now handled gracefully**
✅ **Users automatically redirected to login**
✅ **No more confusing JSON parse errors**
✅ **Preserves redirect URL for seamless return**
✅ **Works for all AJAX requests** (validation, data submission, dimensional data)

The fix is **backward compatible** and **non-intrusive** - if `window.handleSessionExpiration` is not loaded, the code continues to work as before (with the JSON parse error).
