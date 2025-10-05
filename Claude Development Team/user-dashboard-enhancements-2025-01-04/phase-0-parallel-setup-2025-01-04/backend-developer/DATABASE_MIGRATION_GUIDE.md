# Database Migration Guide - Phase 0

## Overview
Phase 0 implementation adds new database columns and tables that require database recreation or migration.

## Changes Required

### 1. User Table
**New Column:**
- `use_new_data_entry` BOOLEAN DEFAULT FALSE

### 2. UserFeedback Table (New)
**Schema:**
```sql
CREATE TABLE user_feedback (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    interface_version VARCHAR(20) NOT NULL,
    feedback_type VARCHAR(50),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

---

## Development Environment Migration

### Option 1: Database Recreation (Recommended for Dev)

**WARNING: This will delete all existing data!**

```bash
# Navigate to project root
cd "/Users/prateekgoyal/Desktop/Prateek/ESG DataVault Development/Claude/sakshi-learning"

# Backup existing database
cp instance/esg_data.db instance/esg_data.db.backup.$(date +%Y%m%d_%H%M%S)

# Delete current database
rm instance/esg_data.db

# Start the app - db.create_all() will create new schema
python3 run.py
```

The app will automatically:
1. Create all tables with new schema
2. Seed initial SUPER_ADMIN user
3. Create test companies and users

---

### Option 2: Manual SQL Migration (Preserve Data)

If you want to preserve existing data:

```bash
# Navigate to project root
cd "/Users/prateekgoyal/Desktop/Prateek/ESG DataVault Development/Claude/sakshi-learning"

# Open SQLite database
sqlite3 instance/esg_data.db

# Run migration SQL
```

```sql
-- Add new column to user table
ALTER TABLE user ADD COLUMN use_new_data_entry BOOLEAN DEFAULT 0;

-- Create user_feedback table
CREATE TABLE user_feedback (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    interface_version VARCHAR(20) NOT NULL,
    feedback_type VARCHAR(50),
    message TEXT,
    created_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY(user_id) REFERENCES user (id)
);

-- Verify changes
.schema user
.schema user_feedback

-- Exit
.quit
```

---

## Production Environment Migration

### Using Alembic (Recommended)

If using Alembic for migrations, create a new migration:

```bash
# Generate migration
alembic revision --autogenerate -m "Add Phase 0 user preferences and feedback"

# Review the generated migration file in migrations/versions/

# Apply migration
alembic upgrade head
```

### Manual SQL for Production

```sql
-- Phase 0: Add user preference toggle
ALTER TABLE user ADD COLUMN use_new_data_entry BOOLEAN DEFAULT FALSE;

-- Phase 0: Create user feedback table
CREATE TABLE IF NOT EXISTS user_feedback (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    interface_version VARCHAR(20) NOT NULL,
    feedback_type VARCHAR(50),
    message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES user (id)
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS ix_user_feedback_user_id ON user_feedback(user_id);
CREATE INDEX IF NOT EXISTS ix_user_feedback_created_at ON user_feedback(created_at);
```

---

## Verification

After migration, verify the changes:

```bash
# Open database
sqlite3 instance/esg_data.db

# Check user table schema
.schema user

# Should include:
# use_new_data_entry BOOLEAN DEFAULT 0

# Check user_feedback table exists
.schema user_feedback

# Test query
SELECT COUNT(*) FROM user WHERE use_new_data_entry = 1;

# Exit
.quit
```

---

## Rollback Plan

If you need to rollback:

### Development
```bash
# Restore from backup
cp instance/esg_data.db.backup.YYYYMMDD_HHMMSS instance/esg_data.db
```

### Production
```sql
-- Remove new column (Note: SQLite doesn't support DROP COLUMN directly)
-- You'll need to recreate the table without the column

-- Drop feedback table
DROP TABLE IF EXISTS user_feedback;
```

---

## Testing After Migration

1. **Start the application:**
   ```bash
   python3 run.py
   ```

2. **Check for errors in logs:**
   - Look for "Database tables created successfully"
   - No errors about missing columns

3. **Test user login:**
   - Login as a test user
   - Navigate to `/user/dashboard`
   - Should not redirect (use_new_data_entry is False by default)

4. **Test API endpoints:**
   ```bash
   # Get preferences (after login)
   curl http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/api/preferences

   # Toggle interface (after login)
   curl -X POST http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/api/toggle-interface \
     -H "Content-Type: application/json" \
     -d '{"useNewInterface": true}'
   ```

---

## Common Issues

### Issue 1: "no such column: user.use_new_data_entry"
**Solution:** Database migration not applied. Follow migration steps above.

### Issue 2: "table user_feedback already exists"
**Solution:** Table already created. Safe to ignore or use `IF NOT EXISTS` clause.

### Issue 3: App won't start after migration
**Solution:**
1. Check database file permissions
2. Verify SQLite version compatibility
3. Review app logs for specific errors

---

## Quick Start Script

Save this as `migrate_phase0.sh`:

```bash
#!/bin/bash

echo "Phase 0 Database Migration"
echo "=========================="
echo ""
echo "This will recreate your database. All data will be lost!"
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    # Backup
    echo "Creating backup..."
    cp instance/esg_data.db instance/esg_data.db.backup.$(date +%Y%m%d_%H%M%S)

    # Remove old database
    echo "Removing old database..."
    rm instance/esg_data.db

    # Start app to recreate
    echo "Recreating database..."
    python3 -c "from app import create_app; app = create_app()"

    echo "Migration complete!"
    echo "You can now start the app with: python3 run.py"
else
    echo "Migration cancelled."
fi
```

Make it executable:
```bash
chmod +x migrate_phase0.sh
./migrate_phase0.sh
```

---

**Last Updated:** 2025-01-04
**Phase:** Phase 0 - Parallel Implementation Setup
