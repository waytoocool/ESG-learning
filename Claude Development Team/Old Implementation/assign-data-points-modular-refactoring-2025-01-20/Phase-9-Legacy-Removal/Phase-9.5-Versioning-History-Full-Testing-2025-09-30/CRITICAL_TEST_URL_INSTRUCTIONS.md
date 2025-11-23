# ⚠️ CRITICAL: CORRECT TEST URL FOR PHASE 9.5

**Date**: 2025-10-01
**For**: ui-testing-agent
**Status**: MANDATORY - DO NOT DEVIATE

---

## ❌ WRONG URL (DO NOT TEST THIS)

```
http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign_data_points_redesigned
```

**Why it's wrong**: This is the OLD legacy page, NOT the NEW modular page under test.

---

## ✅ CORRECT URL (TEST THIS ONE)

```
http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2
```

**Copy this exact URL and use it for ALL Phase 9.5 testing.**

---

## Verification Before Testing

Before starting any tests, verify you are on the correct page:

1. **Navigate to**: `http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2`

2. **Check Browser URL bar** - it should show:
   - ✅ CORRECT: `/admin/assign-data-points-v2` at the end
   - ❌ WRONG: `/admin/assign_data_points_redesigned` at the end

3. **Open DevTools Console** and verify you see:
   ```
   [VersioningModule] Initialization complete
   [ImportExportModule] Initialization complete
   [HistoryModule] Initialization complete
   ```

4. **If you see these messages**: ✅ You are on the CORRECT page, proceed with testing

5. **If you DON'T see these messages**: ❌ You are on the WRONG page or modules failed to load

---

## Quick Reference

| Page | URL | Status |
|------|-----|--------|
| ❌ OLD (WRONG) | `/admin/assign_data_points_redesigned` | DO NOT TEST |
| ✅ NEW (CORRECT) | `/admin/assign-data-points-v2` | TEST THIS |

---

## Test Credentials

```
Company: test-company-alpha
Admin: alice@alpha.com
Password: admin123
```

---

## What If Modules Don't Load?

If after navigating to `/admin/assign-data-points-v2` you still don't see module initialization messages:

```bash
# Clear browser cache
pkill -f chrome

# Restart Playwright MCP
npm run mcp:start

# Then re-test
```

---

## Final Checklist

Before executing Phase 9.5 tests, confirm:

- [ ] URL contains `/admin/assign-data-points-v2` (note the `-v2` at the end)
- [ ] Console shows 3 module initialization messages
- [ ] Network tab shows HTTP 200 for all 3 module files
- [ ] No JavaScript errors in console
- [ ] Logged in as alice@alpha.com

**ONLY proceed with testing if ALL checkboxes are checked.**

---

**REMEMBER**: The URL is `/admin/assign-data-points-v2` with a hyphen and "v2" at the end.

**NOT**: `/admin/assign_data_points_redesigned` (this is the old page)

---

**Status**: Ready for ui-testing-agent
**Action Required**: Test ONLY the v2 URL above
**Expected Result**: All 3 modules load successfully, ready for 45 tests
