# Quick Reference: Computed Field Dependency Testing

**Last Updated:** 2025-11-10
**Status:** Post-Bug-Fix Code Analysis Complete

---

## 🚀 5-Minute Quick Test

```bash
# 1. Start app
python3 run.py

# 2. Open browser
http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points

# 3. Login: alice@alpha.com / admin123

# 4. Open console (F12)
window.DependencyManager.isReady()  // Must return: true

# 5. Search "employee turnover" and click "+"

# 6. Check results:
✅ PASS: 3 fields added (1 computed + 2 dependencies)
✅ PASS: Purple badge visible on computed field
✅ PASS: No console errors
❌ FAIL: Only 1 field added OR console errors
```

---

## 📋 Test Cases Summary

| ID | Test Name | Priority | Time | Critical? |
|----|-----------|----------|------|-----------|
| TC-001 | Auto-Cascade | P0 | 5 min | 🔴 YES |
| TC-002 | Partial Dependency | P1 | 5 min | 🟡 NO |
| TC-003 | Visual Indicators | P0 | 5 min | 🔴 YES |
| TC-004 | Collapsible Grouping | P0 | 10 min | 🟡 NO* |
| TC-005 | Removal Protection | P1 | 5 min | 🟡 NO |
| TC-006 | Cascade Removal | P1 | 5 min | 🟡 NO |
| TC-007 | Search & Filter | P2 | 3 min | 🟢 NO |
| TC-008 | Manual Selection | P0 | 3 min | 🔴 YES |
| TC-009 | Shared Dependency | P1 | 7 min | 🟡 NO |

\* Can gracefully degrade to flat list

---

## 🐛 Bug Fixes Summary

### Bug #1: Auto-Cascade TypeError ✅
- **File:** `DependencyManager.js:248-291`
- **Status:** FIXED
- **Confidence:** 95%

### Bug #2: Missing Purple Badges ✅
- **File:** `SelectDataPointsPanel.js:497, 650-660`
- **Status:** FIXED
- **Confidence:** 95%

### Feature: Collapsible Grouping ⚠️
- **Files:** `SelectedDataPointsPanel.js:1139-1443` + CSS
- **Status:** IMPLEMENTED, UNTESTED
- **Confidence:** 60% (timing concerns)

---

## 🔍 Console Commands Cheat Sheet

```javascript
// Check if DependencyManager is ready
window.DependencyManager.isReady()
// Expected: true

// Check dependency map
window.DependencyManager.getDependencyMap()
// Expected: Map with entries

// Check for grouping elements after adding computed field
document.querySelector('.computed-field-group')
// Expected: HTMLDivElement (if grouping works)

// Check for toggle button
document.querySelector('.dependency-toggle-btn')
// Expected: HTMLButtonElement (if grouping works)

// Check dependencies container
document.querySelector('.computed-field-dependencies')
// Expected: HTMLDivElement with 'expanded' or 'collapsed' class

// Check selected items count
document.querySelector('.selected-count').textContent
// Expected: "3 data points selected" after adding computed field
```

---

## ✅ Pass Criteria

**Minimum for Deployment:**
- ✅ TC-001 (Auto-Cascade) PASS
- ✅ TC-003 (Visual Indicators) PASS
- ✅ TC-008 (Manual Selection) PASS
- ✅ No console errors

**Optional (Nice to Have):**
- ⚠️ TC-004 (Collapsible Grouping) - Can degrade gracefully

---

## ❌ Failure Scenarios

**BLOCK DEPLOYMENT if:**
- ❌ Auto-cascade doesn't work (only 1 field added)
- ❌ Console shows TypeError
- ❌ Purple badges still missing
- ❌ Manual selection broken

**INVESTIGATE if:**
- ⚠️ Collapsible grouping doesn't appear
- ⚠️ Console shows "DependencyManager not ready"
- ⚠️ Toggle button missing

**ACCEPTABLE DEGRADATION:**
- ⚠️ Collapsible grouping doesn't work BUT
- ✅ Auto-cascade works AND
- ✅ Purple badges visible AND
- ✅ Falls back to flat list gracefully

---

## 🎯 Expected Visual Results

### After Adding Computed Field:

**Selected Panel Should Show:**
```
┌─────────────────────────────────────────┐
│ 🧮 Total rate of employee turnover...  │ ← Purple badge
│    (2 dependencies)                      │
│    ▾ Toggle button (if grouping works)  │ ← Chevron
│    ↳ Number of employees who left       │ ← Indented
│    ↳ Total number of employees          │ ← Indented
└─────────────────────────────────────────┘
```

**Counter Should Show:**
```
3 data points selected
```

**Notification Should Show:**
```
✅ Added 'Total rate of employee turnover...' and 2 dependencies
```

---

## 📊 Good vs Bad Console Logs

### ✅ GOOD (Feature Working)
```
[DependencyManager] Loading dependency tree...
[DependencyManager] Loaded 2 computed fields with dependencies
[DependencyManager] Ready
[DependencyManager] Auto-adding 2 dependencies for [field-id]
[SelectedDataPointsPanel] Generating flat HTML...
[SelectedDataPointsPanel] Generating flat HTML with dependency grouping...
```

### ❌ BAD (Feature Broken)
```
TypeError: Cannot read properties of undefined (reading 'find')
[DependencyManager] Failed to load dependency tree
ReferenceError: DependencyManager is not defined
```

### ⚠️ WARNING (Degraded)
```
[SelectedDataPointsPanel] DependencyManager not ready
[SelectedDataPointsPanel] Generating flat HTML... (without grouping)
```

---

## 🔧 Quick Troubleshooting

### Issue: No purple badges
**Fix:** Hard refresh (Cmd+Shift+R / Ctrl+F5)

### Issue: Auto-cascade doesn't work
**Check:** `window.DependencyManager.isReady()` - must be true
**Fix:** Wait 5 seconds after page load, try again

### Issue: No collapsible grouping
**Check:** Console for "DependencyManager not ready"
**Status:** Timing issue - acceptable degradation
**See:** `Collapsible_Grouping_Investigation.md` for detailed fix

### Issue: TypeError in console
**Status:** Bug fix didn't work - BLOCK DEPLOYMENT
**Action:** Review `DependencyManager.js:248-291`

---

## 📁 Document Quick Links

- **Full Testing Guide:** `Manual_Testing_Guide.md`
- **Test Analysis:** `Testing_Summary_Computed_Field_Dependency_v2.md`
- **Grouping Debug:** `Collapsible_Grouping_Investigation.md`
- **Executive Summary:** `EXECUTIVE_SUMMARY.md`
- **This Document:** `QUICK_REFERENCE.md`

---

## 🎬 What to Do Next

1. **Run 5-minute quick test** (top of this document)
2. **If PASS:** Run full test suite (30 min)
3. **If FAIL:** Check troubleshooting section
4. **Document results:** Update `README.md` test results table
5. **Make decision:** Deploy, investigate, or block

---

## 📞 Who to Contact

**Feature Not Working?**
→ Review `Collapsible_Grouping_Investigation.md`

**Need Test Instructions?**
→ Follow `Manual_Testing_Guide.md`

**Deployment Decision?**
→ Read `EXECUTIVE_SUMMARY.md`

**Technical Details?**
→ See `Testing_Summary_Computed_Field_Dependency_v2.md`

---

**Prepared By:** UI Testing Agent
**Version:** v2
**Date:** 2025-11-10
