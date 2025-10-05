# Phase 0 Quick Reference Card

## 🚀 Getting Started

### Database Setup
```bash
# Backup & recreate database
cp instance/esg_data.db instance/esg_data.db.backup
rm instance/esg_data.db
python3 run.py
```

---

## 📁 File Locations

### Models
- `/app/models/user.py` - Added `use_new_data_entry` field
- `/app/models/user_feedback.py` - New feedback model

### Routes
- `/app/routes/user_v2/` - All new v2 routes
  - `__init__.py` - Blueprint setup
  - `dashboard.py` - Placeholder dashboard
  - `preferences_api.py` - Toggle & preferences
  - `feedback_api.py` - Feedback collection

### Templates
- `/app/templates/user_v2/dashboard_placeholder.html`

### Config
- `/app/config.py` - Feature flags added

---

## 🔌 API Endpoints

### Toggle Interface
```bash
POST /user/v2/api/toggle-interface
Content-Type: application/json

{"useNewInterface": true}
```

### Get Preferences
```bash
GET /user/v2/api/preferences
```

### Submit Feedback
```bash
POST /user/v2/api/feedback
Content-Type: application/json

{
  "interfaceVersion": "modal",
  "feedbackType": "suggestion",
  "message": "Your feedback"
}
```

---

## 🗄️ Database Schema

### User Table Addition
```sql
ALTER TABLE user ADD COLUMN use_new_data_entry BOOLEAN DEFAULT 0;
```

### New Feedback Table
```sql
CREATE TABLE user_feedback (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    interface_version VARCHAR(20) NOT NULL,
    feedback_type VARCHAR(50),
    message TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

---

## ⚙️ Feature Flags

### Environment Variables
```bash
FEATURE_NEW_DATA_ENTRY_ENABLED=True    # Global on/off
FEATURE_NEW_DATA_ENTRY_DEFAULT=False   # Default for new users
FEATURE_NEW_DATA_ENTRY_PERCENTAGE=10   # Rollout percentage
AB_TEST_ENABLED=False                  # A/B testing
AB_TEST_SAMPLE_SIZE=100               # Sample size
```

### Usage in Code
```python
if current_app.config.get('FEATURE_NEW_DATA_ENTRY_ENABLED', False):
    # Feature is enabled
```

---

## 🧪 Testing

### Manual Testing Steps
1. ✅ Start app - no errors
2. ✅ Login as user
3. ✅ Access `/user/dashboard` - should show legacy
4. ✅ Toggle preference via API or database
5. ✅ Refresh - should redirect to `/user/v2/dashboard`
6. ✅ Click "Switch Back" button
7. ✅ Should return to legacy dashboard

### API Testing
```bash
# Get preferences
curl http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/api/preferences

# Toggle to new interface
curl -X POST http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/api/toggle-interface \
  -H "Content-Type: application/json" \
  -d '{"useNewInterface": true}'

# Submit feedback
curl -X POST http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/api/feedback \
  -H "Content-Type: application/json" \
  -d '{"interfaceVersion":"modal","feedbackType":"praise","message":"Great work!"}'
```

---

## 🛠️ Common Tasks

### Enable/Disable Feature
```bash
# Disable globally
export FEATURE_NEW_DATA_ENTRY_ENABLED=False

# Re-enable
export FEATURE_NEW_DATA_ENTRY_ENABLED=True
```

### Toggle User Preference via Database
```bash
sqlite3 instance/esg_data.db

# Enable for user ID 2
UPDATE user SET use_new_data_entry = 1 WHERE id = 2;

# Disable for user ID 2
UPDATE user SET use_new_data_entry = 0 WHERE id = 2;

.quit
```

### View Feedback
```bash
sqlite3 instance/esg_data.db

SELECT u.email, uf.interface_version, uf.feedback_type, uf.message, uf.created_at
FROM user_feedback uf
JOIN user u ON uf.user_id = u.id
ORDER BY uf.created_at DESC;

.quit
```

---

## ⚠️ Important Notes

### Breaking Changes
- ❌ None - fully backward compatible

### Required Actions
- ✅ Database migration (recreate or alter table)
- ✅ Restart app after code update

### Known Limitations
- Phase 0 only provides toggle infrastructure
- Full dashboard coming in Phase 1
- Placeholder UI shown for opted-in users

---

## 📊 Monitoring

### Check Feature Usage
```sql
-- Count users by preference
SELECT
    use_new_data_entry,
    COUNT(*) as user_count
FROM user
GROUP BY use_new_data_entry;

-- Recent toggles (check logs)
-- Users who toggled to new interface
SELECT * FROM user WHERE use_new_data_entry = 1;
```

### Check Feedback
```sql
-- Feedback summary
SELECT
    interface_version,
    feedback_type,
    COUNT(*) as count
FROM user_feedback
GROUP BY interface_version, feedback_type;
```

---

## 🔄 Rollback

### Emergency Disable
```bash
# Set environment variable
export FEATURE_NEW_DATA_ENTRY_ENABLED=False

# Restart app
pkill -f "python3 run.py"
python3 run.py
```

### Complete Rollback
```bash
# Restore backup database
cp instance/esg_data.db.backup instance/esg_data.db

# Revert code changes
git revert <commit-hash>
```

---

## 📚 Documentation Files

1. `backend-developer-report.md` - Detailed technical report
2. `DATABASE_MIGRATION_GUIDE.md` - Migration instructions
3. `IMPLEMENTATION_SUMMARY.md` - High-level summary
4. `QUICK_REFERENCE.md` - This file

---

## 🎯 Next Phase Preview

### Phase 1 Will Add:
- Full modal-based data entry
- Dimensional data grid
- File upload interface
- Historical data display
- Entity switcher
- Computation context

---

**Phase 0 Complete** ✅
**Ready for Phase 1** 🚀
