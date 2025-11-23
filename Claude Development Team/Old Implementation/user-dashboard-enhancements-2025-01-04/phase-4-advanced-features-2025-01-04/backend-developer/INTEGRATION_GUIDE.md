# Phase 4: Quick Integration Guide

This guide provides step-by-step instructions for integrating Phase 4 features into the User Dashboard.

---

## Step 1: Database Migration

Run the following to update your database schema:

```bash
# Start Flask shell
python3 run.py shell

# Create new tables/columns
>>> from app.extensions import db
>>> db.create_all()
>>> exit()
```

This will add:
- `is_draft` column to `esg_data` table
- `draft_metadata` column to `esg_data` table
- `idx_esg_draft_lookup` index

---

## Step 2: Update Dashboard Template

Add the following to `app/templates/user_v2/dashboard.html`:

### Add CSS (in `<head>` or `{% block extra_css %}`)
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/user_v2/phase4_features.css') }}">
```

### Add JavaScript (before closing `</body>` or in `{% block extra_js %}`)
```html
<!-- Phase 4: Advanced Features -->
<script src="{{ url_for('static', filename='js/user_v2/auto_save_handler.js') }}"></script>
<script src="{{ url_for('static', filename='js/user_v2/keyboard_shortcuts.js') }}"></script>
<script src="{{ url_for('static', filename='js/user_v2/bulk_paste_handler.js') }}"></script>
<script src="{{ url_for('static', filename='js/user_v2/number_formatter.js') }}"></script>
<script src="{{ url_for('static', filename='js/user_v2/performance_optimizer.js') }}"></script>

<script>
// Global initialization
let globalOptimizer, globalShortcuts;

document.addEventListener('DOMContentLoaded', function() {
    // 1. Initialize Performance Optimizer
    globalOptimizer = new PerformanceOptimizer({
        enableLazyLoading: true,
        enableCaching: true,
        enableWebWorkers: true
    });
    globalOptimizer.initialize();

    // 2. Initialize Keyboard Shortcuts
    globalShortcuts = new KeyboardShortcutHandler({
        onSave: function() {
            if (window.currentAutoSave) {
                window.currentAutoSave.forceSave();
            }
        },
        onSubmit: function() {
            // Implement submit logic
            const submitBtn = document.querySelector('.modal.show .btn-submit');
            if (submitBtn) submitBtn.click();
        },
        onClose: function() {
            // Close modal
            const closeBtn = document.querySelector('.modal.show .btn-close');
            if (closeBtn) closeBtn.click();
        },
        onNextField: function() {
            // Implement navigation
            console.log('Navigate to next field');
        },
        onPreviousField: function() {
            // Implement navigation
            console.log('Navigate to previous field');
        }
    });
    globalShortcuts.enable();

    // 3. Apply Number Formatting
    NumberFormatter.applyToContainer(document.body, {
        fieldType: 'DECIMAL',
        decimals: 2
    });
});
</script>
```

---

## Step 3: Initialize Auto-Save for Modals

When opening a data entry modal, initialize auto-save:

```javascript
function openDataEntryModal(fieldId, entityId, reportingDate) {
    // ... existing modal open logic ...

    // Initialize auto-save
    const autoSave = new AutoSaveHandler({
        fieldId: fieldId,
        entityId: entityId,
        reportingDate: reportingDate,
        getFormData: function() {
            return {
                value: document.getElementById('value-input')?.value,
                notes: document.getElementById('notes-input')?.value,
                confidence: document.getElementById('confidence-select')?.value,
                dimensional_data: getDimensionalData(),  // Your existing function
                context_data: getContextData()           // Your existing function
            };
        },
        onSaveSuccess: function(result) {
            console.log('Draft saved:', result.draft_id);
        },
        onSaveError: function(error) {
            console.error('Auto-save failed:', error);
        },
        onDraftRestored: function(draftData) {
            // Restore draft to form
            if (draftData.value) {
                document.getElementById('value-input').value = draftData.value;
            }
            if (draftData.notes) {
                document.getElementById('notes-input').value = draftData.notes;
            }
            if (draftData.confidence) {
                document.getElementById('confidence-select').value = draftData.confidence;
            }
            if (draftData.dimensional_data) {
                restoreDimensionalData(draftData.dimensional_data);
            }
        }
    });

    autoSave.start();
    window.currentAutoSave = autoSave;

    // Update keyboard shortcuts state
    if (globalShortcuts) {
        globalShortcuts.setModalOpen(true);
    }
}

function closeDataEntryModal() {
    // Stop auto-save
    if (window.currentAutoSave) {
        window.currentAutoSave.stop();
        window.currentAutoSave = null;
    }

    // Update keyboard shortcuts state
    if (globalShortcuts) {
        globalShortcuts.setModalOpen(false);
    }

    // ... existing modal close logic ...
}
```

---

## Step 4: Enable Bulk Paste for Dimensional Tables

For dimensional data tables, add bulk paste support:

```javascript
function initializeDimensionalTable(tableElement, fieldId, dimensions) {
    // ... existing table initialization ...

    // Add bulk paste handler
    const bulkPaste = new BulkPasteHandler({
        targetTable: tableElement,
        dimensions: dimensions,
        fieldType: 'DECIMAL',  // or get from field metadata
        onPaste: async function(parsedData) {
            // Apply pasted data
            try {
                const response = await fetch('/api/user/v2/apply-bulk-paste', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        field_id: fieldId,
                        entity_id: currentEntityId,
                        reporting_date: currentReportingDate,
                        parsed_data: parsedData
                    })
                });

                const result = await response.json();

                if (result.success) {
                    // Reload table data
                    reloadDimensionalTable();
                    showSuccess(`Pasted ${result.total_count} entries`);
                } else {
                    showError(result.error);
                }
            } catch (error) {
                console.error('Bulk paste error:', error);
                showError('Failed to apply bulk paste');
            }
        },
        onError: function(error) {
            showError('Paste error: ' + error.message);
        }
    });

    bulkPaste.enable();

    return bulkPaste;
}
```

---

## Step 5: Apply Number Formatting to Input Fields

For number input fields, apply smart formatting:

```html
<!-- Add data attributes to number inputs -->
<input type="text"
       id="value-input"
       data-format="number"
       data-field-type="DECIMAL"
       data-unit="kWh"
       data-decimals="2">

<script>
// The number formatter will automatically attach to these inputs
// because we called NumberFormatter.applyToContainer() in Step 2
</script>
```

Or manually attach to specific inputs:

```javascript
const formatter = new NumberFormatter({
    fieldType: 'DECIMAL',
    unit: 'kWh',
    decimals: 2
});
formatter.attachToInput(document.getElementById('value-input'));
```

---

## Step 6: Add Auto-Save Status to Modal Header

Update your modal template to include auto-save status:

```html
<div class="modal-header">
    <h5 class="modal-title">Enter Data - {{ field_name }}</h5>

    <!-- Auto-save status will be inserted here by AutoSaveHandler -->
    <div class="auto-save-status-container"></div>

    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
</div>
```

---

## Step 7: Test the Integration

### Test Auto-Save:
1. Open a data entry modal
2. Enter some data
3. Wait 30 seconds
4. Check console for "Draft saved" message
5. Close modal without saving
6. Reopen modal
7. Verify draft is restored with confirmation prompt

### Test Keyboard Shortcuts:
1. Press `Ctrl/Cmd+?` to view help overlay
2. Try `Ctrl/Cmd+S` to save
3. Try `Ctrl/Cmd+Enter` to submit
4. Try `ESC` to close modal
5. Navigate table with arrow keys

### Test Bulk Paste:
1. Open Excel or Google Sheets
2. Copy a 2D table with headers
3. Open dimensional data modal
4. Press `Ctrl+V`
5. Review preview
6. Click "Apply"
7. Verify data is saved

### Test Number Formatting:
1. Focus on a number input
2. Type: `1234567.89`
3. Blur (click outside)
4. Verify displays as: `1,234,567.89`
5. Focus again
6. Verify shows raw: `1234567.89`

---

## Troubleshooting

### Auto-save not working
- Check browser console for errors
- Verify API endpoint `/api/user/v2/save-draft` is accessible
- Check user permissions
- Clear localStorage: `localStorage.clear()`

### Keyboard shortcuts not responding
- Check for conflicts with browser extensions
- Try in incognito mode
- Verify shortcuts are enabled: `globalShortcuts.isEnabled`

### Bulk paste fails
- Verify clipboard data format (TSV or CSV)
- Check for special characters
- Ensure table has `data-virtual-scroll` or similar attribute
- Review console for validation errors

### Number formatting incorrect
- Check field type is set correctly
- Verify unit is recognized
- Review locale settings
- Check for invalid input characters

---

## Optional Enhancements

### 1. Add Draft Indicator to Table Rows

```javascript
function renderTableRow(field, data) {
    const hasDraft = data.has_draft;

    return `
        <tr>
            <td>
                ${field.name}
                ${hasDraft ? '<span class="badge bg-warning">Draft</span>' : ''}
            </td>
            <td>${data.value || '-'}</td>
            <td>
                <button onclick="openModal(${field.id})">Edit</button>
            </td>
        </tr>
    `;
}
```

### 2. Show Draft List in Dashboard

```javascript
async function loadDraftsList() {
    const response = await fetch('/api/user/v2/list-drafts');
    const result = await response.json();

    if (result.success && result.count > 0) {
        showDraftsNotification(result.drafts);
    }
}

function showDraftsNotification(drafts) {
    const notification = `
        <div class="alert alert-info">
            You have ${drafts.length} unsaved draft(s).
            <button onclick="reviewDrafts()">Review</button>
        </div>
    `;
    document.getElementById('notifications').innerHTML = notification;
}
```

### 3. Add Cache Statistics Display

```javascript
function showCacheStats() {
    const stats = globalOptimizer.getCacheStats();

    console.log(`Cache Statistics:
        - Total Items: ${stats.totalItems}
        - Total Size: ${(stats.totalSize / 1024).toFixed(2)} KB
        - Types: ${JSON.stringify(stats.typeStats, null, 2)}
    `);
}

// Add button to admin panel
// <button onclick="showCacheStats()">View Cache Stats</button>
```

---

## Performance Monitoring

Add performance tracking:

```javascript
// Monitor page load performance
window.addEventListener('load', function() {
    const perf = globalOptimizer.monitorPerformance();

    console.log('Performance Metrics:', perf);

    // Send to analytics
    if (window.analytics) {
        window.analytics.track('page_load', perf);
    }
});

// Monitor modal load time
function openModalWithTracking(fieldId) {
    performance.mark('modal-open-start');

    openDataEntryModal(fieldId);

    performance.mark('modal-open-end');
    performance.measure('modal-load', 'modal-open-start', 'modal-open-end');

    const loadTime = performance.getEntriesByName('modal-load')[0].duration;
    console.log(`Modal loaded in ${loadTime.toFixed(2)}ms`);
}
```

---

## Next Steps

After integration:

1. ✅ Run comprehensive testing
2. ✅ Collect user feedback
3. ✅ Monitor error logs
4. ✅ Track performance metrics
5. ✅ Update user documentation
6. ✅ Conduct training sessions

---

**Integration Complete!** 🎉

Your User Dashboard now has:
- ✅ Auto-save functionality
- ✅ Keyboard shortcuts
- ✅ Bulk paste from Excel
- ✅ Smart number formatting
- ✅ Performance optimizations

For detailed documentation, see:
- `IMPLEMENTATION_SUMMARY.md` - Full technical documentation
- `requirements-and-specs.md` - Original requirements
- API documentation in implementation summary
