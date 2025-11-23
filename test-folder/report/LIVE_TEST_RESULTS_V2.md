# Live Browser Test Results - Version 2
## Computed Field Dependency Auto-Management Feature

**Test Date:** 2025-11-10 21:22:37
**Tester:** UI Testing Agent (Automated - Playwright)
**Environment:** http://test-company-alpha.127-0-0-1.nip.io:8000

---

## Executive Summary

### GO/NO-GO Decision: **NO-GO**

**Deployment Readiness:** NOT READY
**Risk Level:** HIGH

---

## Test Results Summary

| Test | Name | Result | Impact |
|------|------|--------|--------|
| TC-001 | Auto-Cascade Selection | FAIL | BLOCKING |
| TC-008 | Visual Indicators | PASS | BLOCKING |
| TC-004 | Collapsible Grouping | NOT_RUN | DEGRADABLE |
| RT-001 | Regression Test | FAIL | BLOCKING |

**Results:**
- PASS: 1
- FAIL: 2
- PARTIAL: 0
- DEGRADED: 0

---

## Detailed Results


### TC-001: Auto-Cascade Selection

**Status:** FAIL

**Log:**

- ℹ️ Taking initial screenshot...
- ℹ️ Checking for existing selections...
- ℹ️ Searching for computed field...
- ℹ️ Looking for computed fields with purple badges...
- ℹ️ Found 100 visible field(s)
- ℹ️ Found 4 computed field badge(s)
- ✅ ✅ Purple badges found!
- ℹ️ Clicking '+' button on computed field...
- ❌ ❌ Add button not visible


### TC-008: Visual Indicators

**Status:** PASS

**Log:**

- ℹ️ Clearing search to see all fields...
- ℹ️ Counting purple/computed field badges...
- ℹ️ Found 2 visible computed field badge(s)
- ✅ ✅ PASS: Found expected computed field badges
- ℹ️ Badge 1 text: '(2)'
- ✅ Badge 1 has proper indicators
- ℹ️ Badge 2 text: '(2)'
- ✅ Badge 2 has proper indicators


### TC-004: Collapsible Grouping

**Status:** NOT_RUN

**Log:**

- ℹ️ Checking DependencyManager status...
- ℹ️ DependencyManager.isReady(): True
- ℹ️ Currently 0 items selected
- ⚠️ ⚠️ No items selected to test grouping


### RT-001: Regression Test

**Status:** FAIL

**Log:**

- ℹ️ Clearing all selections...
- ℹ️ Searching for regular fields...
- ℹ️ Found regular field, adding it...
- ❌ ❌ Add button not visible


## Console Errors: 2

- ❌ Failed to load resource: the server responded with a status of 404 (NOT FOUND)
- ❌ Failed to load resource: the server responded with a status of 404 (NOT FOUND)

## Console Warnings: 2

- ⚠️ [AppMain] HistoryModule not loaded or missing init method
- ⚠️ [CoreUI] Deselect All function not available in legacy manager

---

## Decision: NO-GO

**Action:** ❌ BLOCK - Fix issues first

**Blocking Issues:**

- TC-001: Auto-Cascade Selection
- RT-001: Regression Test

---

**Screenshots:** test-folder/screenshots/live-test-v2/

*Generated: 2025-11-10T21:22:37.289957*
