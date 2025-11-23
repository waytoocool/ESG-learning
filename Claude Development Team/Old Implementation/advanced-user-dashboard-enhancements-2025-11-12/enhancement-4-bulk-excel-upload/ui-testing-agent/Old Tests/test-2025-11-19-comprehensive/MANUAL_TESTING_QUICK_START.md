# Enhancement #4: Bulk Excel Upload - Manual Testing Quick Start

**Quick Reference Guide for Human Testers**

---

## 🚀 Before You Start

### Prerequisites
- [ ] Flask application running: http://test-company-alpha.127-0-0-1.nip.io:8000/
- [ ] Test user credentials: bob@alpha.com / user123
- [ ] Excel/LibreOffice installed
- [ ] Database browser (DB Browser for SQLite or similar)
- [ ] Screenshot tool ready
- [ ] Test duration: 4-7 hours

---

## ⚡ Quick Test (30 Minutes) - Smoke Test

**Goal:** Verify critical path works

1. **Login:** http://test-company-alpha.127-0-0-1.nip.io:8000/ → bob@alpha.com / user123
2. **Download Template:** Click "Bulk Upload Data" → "Pending Only" → Download
3. **Inspect Template:** Open Excel → Verify 2 sheets ("Data Entry", "Instructions")
4. **Fill Template:** Add values to first 3 rows (e.g., 100, 200, 300)
5. **Upload:** Return to modal → Upload filled template
6. **Validate:** Wait for validation → Verify "Success" message
7. **Submit:** Click "Confirm & Submit" → Verify success
8. **Verify Dashboard:** Check dashboard shows updated counts

**Expected Result:** End-to-end workflow completes without errors

---

## 📋 Critical Path Test (4 Hours) - Pre-Production

### Phase 1: Template Verification (30 min)

**Download all 3 templates:**
```
1. Pending Only → Save as: Template-pending-YYYY-MM-DD.xlsx
2. Overdue Only → Save as: Template-overdue-YYYY-MM-DD.xlsx
3. Overdue + Pending → Save as: Template-overdue-and-pending-YYYY-MM-DD.xlsx
```

**For each template, verify:**
- [ ] File opens in Excel without errors
- [ ] "Data Entry" sheet exists
- [ ] "Instructions" sheet exists
- [ ] Hidden columns (AA, AB, AC) contain IDs
- [ ] Can edit "Value" and "Notes" columns ONLY
- [ ] Cannot edit "Field_Name", "Entity", "Rep_Date" (locked/protected)
- [ ] Row count matches expected (Pending: 3, Overdue: 4-5, Combined: 7-8)

**Screenshot:** Save one screenshot per template showing sheet structure

---

### Phase 2: Upload Workflow (1 hour)

**Test 1: Empty Upload (Expect Errors)**
- [ ] Upload Template-pending.xlsx WITHOUT filling values
- [ ] Expected: Errors like "Row X: Value is required"
- [ ] Screenshot: Error message display

**Test 2: Valid Upload (Success Path)**
- [ ] Fill Template-pending.xlsx:
  ```
  Row 1: Value = 100, Notes = "Test 1"
  Row 2: Value = 200, Notes = "Test 2"
  Row 3: Value = 300, Notes = "Test 3"
  ```
- [ ] Upload → Expected: Validation passes
- [ ] Screenshot: Validation success screen

**Test 3: Invalid Data Type**
- [ ] Change Row 1 Value to "ABCD" (text instead of number)
- [ ] Upload → Expected: Error "Invalid DECIMAL format"
- [ ] Screenshot: Error message

**Test 4: Invalid File Format**
- [ ] Try uploading a .pdf or .txt file
- [ ] Expected: Error "Invalid file format"
- [ ] Screenshot: Error message

---

### Phase 3: Data Validation (1.5 hours)

**Test data types:**
- [ ] INTEGER field with decimal (10.5) → Error
- [ ] PERCENTAGE field with "15" → Accepted
- [ ] PERCENTAGE field with "0.15" → Accepted (both formats work)
- [ ] CURRENCY field with "$1,000.50" → Symbols stripped, accepted
- [ ] BOOLEAN field with "TRUE", "Yes", "1" → All accepted

**Test business rules:**
- [ ] Negative value (-10) → Warning (not error), upload proceeds
- [ ] Very large value (5000000000) → Warning shown

**Test overwrites:**
- [ ] Submit data once (Value = 50)
- [ ] Download template again
- [ ] Change same field to 75
- [ ] Upload → Expected: Overwrite warning with old vs new values

**Screenshot:** Overwrite warning display

---

### Phase 4: Data Submission (1 hour)

**Submit valid data:**
- [ ] Complete upload with 3 valid entries
- [ ] Click "Confirm & Submit"
- [ ] Expected: Success message with batch ID

**Verify in database:**
```bash
# Open database
sqlite3 instance/esg_data.db

# Check new data
SELECT field_id, raw_value, notes, created_at
FROM esg_data
WHERE entity_id=3
ORDER BY created_at DESC
LIMIT 3;

# Check audit log
SELECT change_type, old_value, new_value, metadata
FROM esg_data_audit_log
ORDER BY changed_at DESC
LIMIT 3;

# Check bulk upload log
SELECT upload_id, new_entries, updated_entries, status, upload_date
FROM bulk_upload_logs
ORDER BY upload_date DESC
LIMIT 1;
```

**Expected results:**
- [ ] 3 new rows in esg_data
- [ ] raw_value matches uploaded values (100, 200, 300)
- [ ] notes matches uploaded notes
- [ ] 3 new audit log entries with change_type = "Excel Upload"
- [ ] 1 bulk_upload_log record with new_entries = 3, status = "Success"

**Screenshot:** Database query results

**Verify dashboard:**
- [ ] Dashboard shows Pending count decreased by 3
- [ ] Dashboard shows Complete count increased by 3
- [ ] Field cards reflect new status

**Screenshot:** Updated dashboard

---

## 🔍 Detailed Test (7+ Hours) - Comprehensive

**Add these additional phases after completing critical path:**

### Phase 5: Attachments (45 min)
- Test file upload for data entries
- Test file deduplication (same file to multiple entries)
- Test file size limits (20MB)

### Phase 6: Error Handling (1 hour)
- Network error during upload
- Session timeout (wait 35 minutes)
- Corrupt file upload
- SQL injection attempt in Notes
- XSS attempt in Notes

### Phase 7: Edge Cases (1 hour)
- Maximum rows (1000 rows)
- Exceed maximum (1001 rows)
- Single row upload
- Special characters in Notes (Unicode, emojis)
- Zero value
- Decimal precision

### Phase 8: Performance (30 min)
- Large file upload speed
- Validation performance (1000 rows)
- Submission performance (1000 rows)

---

## 📊 Test Results Template

**Copy this template for each test:**

```markdown
### Test: [Test Name]
**Date:** YYYY-MM-DD HH:MM
**Tester:** [Your Name]
**Status:** ✅ PASS / ❌ FAIL / ⚠️ WARNING

**Steps Taken:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Result:**
[What should happen]

**Actual Result:**
[What actually happened]

**Screenshots:**
- screenshot-1.png
- screenshot-2.png

**Notes:**
[Any observations, issues, or comments]

**Database Verification:**
```sql
[SQL query used]
```
[Query results]
```

---

## 🐛 Bug Report Template

**If you find a bug, use this format:**

```markdown
## BUG-ENH4-XXX: [Brief Description]

**Severity:** Critical / High / Medium / Low
**Found By:** [Your Name]
**Date:** YYYY-MM-DD
**Environment:** http://test-company-alpha.127-0-0-1.nip.io:8000/
**User:** bob@alpha.com

**Description:**
[Detailed description of the bug]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Screenshots:**
- [Attach screenshots]

**Console Errors:** (if applicable)
```
[Paste console errors]
```

**Server Logs:** (if applicable)
```
[Paste server logs]
```

**Database State:** (if applicable)
```sql
[SQL query showing unexpected state]
```

**Impact:**
[How does this affect users?]

**Workaround:** (if known)
[Temporary solution if available]

**Suggested Fix:** (optional)
[If you have ideas]
```

---

## 📁 Test Artifacts Organization

**Save all files to:**
```
Claude Development Team/
  advanced-user-dashboard-enhancements-2025-11-12/
    enhancement-4-bulk-excel-upload/
      ui-testing-agent/
        test-2025-11-19-comprehensive/
          screenshots/
            01-template-pending-download.png
            02-template-structure.png
            03-upload-success.png
            04-validation-errors.png
            05-submission-success.png
            06-database-verification.png
            07-dashboard-updated.png
            [... more screenshots ...]

          templates/
            Template-pending-2025-11-19.xlsx
            Template-overdue-2025-11-19.xlsx
            Template-overdue-and-pending-2025-11-19.xlsx
            Template-pending-FILLED-test1.xlsx
            Template-pending-FILLED-test2.xlsx
            [... test data files ...]

          results/
            Phase1-Template-Verification-Results.md
            Phase2-Upload-Workflow-Results.md
            Phase3-Data-Validation-Results.md
            Phase4-Data-Submission-Results.md
            [... test result documents ...]

          TESTING_SUMMARY_v4_COMPREHENSIVE.md (Already created)
          MANUAL_TESTING_QUICK_START.md (This file)
```

---

## ⏱️ Time Tracking

**Track your testing time:**

| Phase | Planned | Actual | Status | Notes |
|-------|---------|--------|--------|-------|
| Template Verification | 30 min | ___ min | ☐ | ___ |
| Upload Workflow | 1 hour | ___ min | ☐ | ___ |
| Data Validation | 1.5 hours | ___ min | ☐ | ___ |
| Data Submission | 1 hour | ___ min | ☐ | ___ |
| **Critical Path Total** | **4 hours** | **___ hours** | **☐** | ___ |
| Attachments | 45 min | ___ min | ☐ | ___ |
| Error Handling | 1 hour | ___ min | ☐ | ___ |
| Edge Cases | 1 hour | ___ min | ☐ | ___ |
| Performance | 30 min | ___ min | ☐ | ___ |
| **Full Test Total** | **7.25 hours** | **___ hours** | **☐** | ___ |

---

## ✅ Testing Checklist

**Pre-Testing:**
- [ ] Flask app running
- [ ] Database backed up
- [ ] Screenshot tool ready
- [ ] Test plan reviewed
- [ ] Time allocated (4-7 hours)

**Phase 1: Template Verification**
- [ ] Downloaded all 3 templates
- [ ] Inspected sheet structure
- [ ] Verified hidden columns
- [ ] Tested cell protection
- [ ] Took screenshots

**Phase 2: Upload Workflow**
- [ ] Tested empty upload (errors)
- [ ] Tested valid upload (success)
- [ ] Tested invalid data type
- [ ] Tested invalid file format
- [ ] Took screenshots

**Phase 3: Data Validation**
- [ ] Tested data types
- [ ] Tested business rules
- [ ] Tested overwrite detection
- [ ] Took screenshots

**Phase 4: Data Submission**
- [ ] Submitted data successfully
- [ ] Verified database records
- [ ] Verified audit trail
- [ ] Verified dashboard updates
- [ ] Took screenshots

**Post-Testing:**
- [ ] Organized all test artifacts
- [ ] Created test results document
- [ ] Filed bug reports (if any)
- [ ] Updated testing status
- [ ] Shared results with team

---

## 🆘 Troubleshooting

**Problem: Flask app not running**
```bash
cd "/Users/prateekgoyal/Desktop/Prateek/ESG DataVault Development/Claude/sakshi-learning"
python3 run.py
# Wait for "Running on http://127-0-0-1.nip.io:8000"
```

**Problem: Port 8000 in use**
```bash
lsof -ti:8000 | xargs kill -9
# Then restart Flask
```

**Problem: Cannot login**
- Check URL: http://test-company-alpha.127-0-0-1.nip.io:8000/
- Credentials: bob@alpha.com / user123
- Try clearing browser cookies

**Problem: Bulk Upload button not visible**
- Refresh page (Cmd+Shift+R / Ctrl+Shift+R)
- Check JavaScript console for errors
- Verify you're logged in as USER role

**Problem: Template download fails**
- Check Flask logs for errors
- Verify user has assignments (query database)
- Try different filter (Pending vs Overdue)

**Problem: Upload fails**
- Check file format (.xlsx, .xls, or .csv)
- Check file size (<5MB)
- Check file is not corrupted
- Verify hidden columns not deleted

**Problem: Database locked**
```bash
# Close all database connections
pkill -f sqlite3
# Wait 5 seconds
sleep 5
# Try again
```

---

## 📞 Support

**Questions or Issues?**
- Review comprehensive testing summary: `TESTING_SUMMARY_v4_COMPREHENSIVE.md`
- Check Flask logs: Look at terminal running `python3 run.py`
- Check browser console: F12 → Console tab
- Check database: `sqlite3 instance/esg_data.db` → `.tables` → `SELECT * FROM ...`

**Slack Channels:**
- #esg-datavault-dev (Development questions)
- #testing (Testing issues)
- #bugs (Bug reports)

**Key Files to Reference:**
- Requirements: `requirements-and-specs.md`
- Testing Guide: `TESTING_GUIDE.md`
- Previous Test Results: `test-2025-11-19/TESTING_SUMMARY_v3.md`

---

## 🎯 Success Criteria

**Minimum for Production Release:**
- ✅ All Phase 1-4 tests PASS (critical path)
- ✅ Zero critical bugs found
- ✅ Database verification clean
- ✅ Dashboard updates correctly

**Ideal for Production Release:**
- ✅ All 8 phases complete
- ✅ All 90 test cases executed
- ✅ Zero high/critical bugs
- ✅ Performance benchmarks met
- ✅ Comprehensive test documentation

---

**Good luck with testing! 🚀**

**Questions?** Reach out to the development team or review the comprehensive testing summary.
