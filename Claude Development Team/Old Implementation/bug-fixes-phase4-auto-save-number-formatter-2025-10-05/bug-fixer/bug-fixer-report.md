# Bug Fixer Investigation Report: Phase 4 Auto-Save and Number Formatter Issues

## Investigation Timeline
**Start**: October 5, 2025 - 14:00 UTC
**End**: October 5, 2025 - 15:30 UTC

## 1. Bug Summary

Two critical bugs were identified in Phase 4 v3 testing that blocked production deployment:

1. **Number Formatter Not Working** (HIGH): Number formatting feature initializes but doesn't apply thousand separators to dynamically created dimensional input fields
2. **Auto-Save Not Initializing** (CRITICAL): Auto-save completely fails to start when modal opens, breaking entire draft functionality

## 2. Reproduction Steps

### Bug #1: Number Formatter
1. Navigate to User Dashboard V2
2. Login as bob@alpha.com
3. Click "Enter Data" on any field
4. Modal opens with dimensional inputs
5. Enter "1234567" in any input
6. Tab out → Number remains unformatted

### Bug #2: Auto-Save
1. Same setup as Bug #1
2. Open browser console
3. Click "Enter Data" button
4. Modal opens
5. Console shows NO auto-save initialization messages
6. No auto-save timer starts

## 3. Investigation Process

### Database Investigation
- Database schema confirmed with is_draft and draft_metadata columns
- No database-level issues found
- Draft API endpoints present and functional

### Code Analysis

**Bug #1: Number Formatter**

Examined `/app/templates/user_v2/dashboard.html` lines 680-700:

```javascript
// Initialize number formatter for all number inputs
document.querySelectorAll('input[type="number"], input[data-format="number"]').forEach(input => {
    const formatter = new NumberFormatter({...});
    formatter.attachToInput(input);
});
```

**Problem Identified**: This code runs on `DOMContentLoaded`, which only attaches formatters to inputs existing at page load. The dimensional matrix inputs are created AFTER modal opens by `DimensionalDataHandler.renderMatrix()` (lines 150-250 in `dimensional_data_handler.js`).

**Bug #2: Auto-Save**

Examined `/app/templates/user_v2/dashboard.html` lines 704-825:

```javascript
// Initialize auto-save when modal is shown
const dataCollectionModalEl = document.getElementById('dataCollectionModal');
if (dataCollectionModalEl) {
    dataCollectionModalEl.addEventListener('show.bs.modal', function(event) {
        const button = event.relatedTarget;
        if (!button) return;  // ❌ PROBLEM: This returns early!
        // ...auto-save initialization
    });
}
```

**Problems Identified**:
1. Code runs OUTSIDE `DOMContentLoaded`, so `dataCollectionModalEl` might be null
2. Listens to `show.bs.modal` but modal opened via `modal.show()` on line 450
3. `event.relatedTarget` is null for programmatic modal.show(), causing early return
4. Auto-save code never executes because of early return on line 735

### Live Environment Testing

Tested at: http://test-company-alpha.127-0-0-1.nip.io:8000/user/v2/dashboard

**Console output before fix:**
```
[LOG] [Phase 4] ✅ Number formatter initialized
[LOG] Opening modal for field: 7421322b-f8b2-4cdc-85d7-3c668b6f9bfb raw_input
# ❌ NO auto-save messages
# ❌ NO dimensional formatter messages
```

## 4. Root Cause Analysis

### Bug #1: Number Formatter Root Cause
**Timing Issue**: Number formatter initialization runs on page load, but dimensional inputs are created dynamically when modal opens. The formatter never sees these inputs because they don't exist at initialization time.

**Chain of Events**:
1. Page loads → NumberFormatter attaches to existing inputs (none in modal yet)
2. User clicks "Enter Data" → Modal opens
3. DimensionalDataHandler creates input fields dynamically
4. Inputs created WITHOUT formatters attached
5. User enters numbers → No formatting applied

### Bug #2: Auto-Save Root Cause
**Event Handling Issue**: Auto-save listener expects Bootstrap data-attribute triggered modals, but the application uses programmatic `modal.show()`. This means `event.relatedTarget` is always null, causing the initialization code to exit early.

**Chain of Events**:
1. Code listens for `show.bs.modal` event
2. User clicks "Enter Data" → `modal.show()` called (line 450)
3. `show.bs.modal` event fires BUT `event.relatedTarget` is null
4. Code checks `if (!button) return;` → EXITS EARLY
5. Auto-save never initializes

**Additional Issue**: Code runs outside DOMContentLoaded, risking null element reference.

## 5. Fix Design

### Bug #1: Number Formatter Fix Design
**Approach**: Create a reusable function to attach formatters that can be called both on page load AND after dimensional matrix renders.

**Strategy**:
1. Extract formatter attachment logic into global function `window.attachNumberFormatters(container)`
2. Call on page load for existing inputs
3. Call after dimensional matrix renders (with 50ms timeout for DOM update)
4. Add duplicate check to prevent double-attachment

**Benefits**:
- Works for both static and dynamic inputs
- Reusable for any future dynamic content
- No breaking changes to existing functionality
- Minimal code changes

### Bug #2: Auto-Save Fix Design
**Approach**: Move auto-save initialization inside DOMContentLoaded and use correct Bootstrap event.

**Strategy**:
1. Move code inside DOMContentLoaded to ensure DOM ready
2. Change from `show.bs.modal` to `shown.bs.modal` (fires AFTER modal shown)
3. Store field ID globally when "Enter Data" clicked (window.currentFieldId)
4. Auto-save reads from global variable instead of event.relatedTarget
5. Use global window.autoSaveHandler instead of local variable

**Benefits**:
- Works with programmatic modal.show()
- Proper event timing (shown vs show)
- No dependency on event.relatedTarget
- Properly scoped within DOMContentLoaded

## 6. Implementation Details

### Files Modified
- `/app/templates/user_v2/dashboard.html` - Main fix implementation

### Bug #1: Number Formatter Fix (Lines 680-711)

**Before**:
```javascript
// Initialize number formatter for all number inputs
document.querySelectorAll('input[type="number"]').forEach(input => {
    const formatter = new NumberFormatter({...});
    formatter.attachToInput(input);
});
console.log('[Phase 4] ✅ Number formatter initialized');
```

**After**:
```javascript
// Create global helper function to attach formatters to inputs
window.attachNumberFormatters = function(container) {
    const selector = container
        ? container.querySelectorAll('input[type="number"], input[data-format="number"]')
        : document.querySelectorAll('input[type="number"], input[data-format="number"]');

    selector.forEach(input => {
        // Skip if already has formatter attached
        if (input._numberFormatter) return;

        const formatter = new NumberFormatter({
            fieldType: input.dataset.fieldType || 'DECIMAL',
            unit: input.dataset.unit || '',
            decimals: input.dataset.decimals ? parseInt(input.dataset.decimals) : 2
        });
        formatter.attachToInput(input);
    });
};

// Apply formatter to existing number inputs
window.attachNumberFormatters();
console.log('[Phase 4] ✅ Number formatter initialized');

// Create global formatter instance for dynamic inputs
window.numberFormatter = new NumberFormatter();
```

**Rationale**:
- Global function allows reuse for dynamic content
- Duplicate check prevents double-attachment
- Maintains backward compatibility
- Supports optional container parameter for scoped attachment

### Bug #1: Dimensional Matrix Hook (Lines 561-576)

**Added code after matrix render**:
```javascript
if (matrix.has_dimensions) {
    matrixContainer.style.display = 'block';
    valueInput.style.display = 'none';

    // Attach number formatters to dynamically created inputs
    if (window.attachNumberFormatters) {
        // Wait for DOM to update, then attach formatters
        setTimeout(() => {
            window.attachNumberFormatters(matrixContainer);
            console.log('[Phase 4] ✅ Number formatters attached to dimensional inputs');
        }, 50);
    }
}
```

**Rationale**:
- 50ms timeout ensures DOM fully updated
- Scoped to matrixContainer for efficiency
- Console log confirms attachment for debugging

### Bug #2: Auto-Save Fix (Lines 722-845)

**Before**:
```javascript
// Outside DOMContentLoaded
const dataCollectionModalEl = document.getElementById('dataCollectionModal');
if (dataCollectionModalEl) {
    dataCollectionModalEl.addEventListener('show.bs.modal', function(event) {
        const button = event.relatedTarget;
        if (!button) return;  // ❌ Exits early!

        const fieldId = button.dataset.fieldId;
        // ...rest of auto-save initialization
    });
}
```

**After**:
```javascript
// INSIDE DOMContentLoaded
console.log('[Phase 4] Advanced features initialization complete');

// Phase 4: Auto-save handler (initialized when modal opens)
window.autoSaveHandler = null;
window.currentFieldId = null;

const dataCollectionModalEl = document.getElementById('dataCollectionModal');
if (dataCollectionModalEl) {
    dataCollectionModalEl.addEventListener('shown.bs.modal', function(event) {
        console.log('[Phase 4] Modal shown event fired');

        // Get field ID from stored value (set when modal opens)
        const fieldId = window.currentFieldId;
        if (!fieldId) {
            console.warn('[Phase 4] No field ID available for auto-save');
            return;
        }

        // ...rest of auto-save initialization using window.autoSaveHandler
    });
}
```

**Added in modal open handler (Line 548-549)**:
```javascript
// Store field ID globally for auto-save to access
window.currentFieldId = fieldId;
```

**Rationale**:
- Code inside DOMContentLoaded ensures DOM ready
- `shown.bs.modal` fires AFTER modal shown (correct timing)
- Global window.currentFieldId set when "Enter Data" clicked
- No dependency on event.relatedTarget
- Global window.autoSaveHandler allows cross-scope access
- Console logs confirm proper execution flow

## 7. Verification Results

### Test Scenarios
- [x] Tested with USER role (bob@alpha.com)
- [x] Tested in test-company-alpha tenant
- [x] Tested with dimensional field (High Coverage Framework Field 1)
- [x] Regression testing completed (page load formatters still work)

### Verification Steps

**Bug #1: Number Formatter**
1. Opened User Dashboard V2
2. Clicked "Enter Data" on High Coverage Framework Field 1
3. Modal opened with Gender dimensional breakdown
4. Console showed: `[Phase 4] ✅ Number formatters attached to dimensional inputs` ✅
5. Checked all 3 inputs had formatters attached: `hasFormatter: true` ✅
6. Formatter behavior verified (focus shows raw, blur formats)

**Bug #2: Auto-Save**
1. Opened same modal
2. Console showed: `[Phase 4] Modal shown event fired` ✅
3. Console showed: `Auto-save started for field 7421322b-f8b2-4cdc-85d7-3c668b6f9bfb` ✅
4. Console showed: `[Phase 4] ✅ Auto-save started for field: 7421322b-f8b2-4cdc-85d7-3c668b6f9bfb` ✅
5. Status indicator appeared showing "Ready" then "Unsaved changes" ✅
6. Form changes triggered status updates ✅

### Console Output After Fix
```
[LOG] [Phase 4] ✅ Number formatter initialized
[LOG] [Phase 4] Advanced features initialization complete
[LOG] Opening modal for field: 7421322b-f8b2-4cdc-85d7-3c668b6f9bfb raw_input
[LOG] [Phase 4] ✅ Number formatters attached to dimensional inputs
[LOG] [Phase 4] Modal shown event fired
[LOG] Auto-save started for field 7421322b-f8b2-4cdc-85d7-3c668b6f9bfb
[LOG] [Phase 4] ✅ Auto-save started for field: 7421322b-f8b2-4cdc-85d7-3c668b6f9bfb
```

All expected console messages present! ✅

### Screenshot Evidence
Screenshot saved: `.playwright-mcp/bug-fix-test-number-formatting.png`
- Shows modal with dimensional inputs
- Shows "Unsaved changes" status (auto-save working)
- Shows number entered in input field

## 8. Related Issues and Recommendations

### Similar Code Patterns
**Potential Issue**: Any other dynamically created inputs in modals might need similar formatter attachment. Review other modal-based input creation.

**Recommendation**: Consider moving to a MutationObserver pattern for truly dynamic input detection if more dynamic content is added.

### Preventive Measures
1. **Documentation**: Document the pattern for attaching formatters to dynamic content
2. **Code Comments**: Add comments explaining why formatters need re-attachment for dynamic inputs
3. **Testing**: Add UI tests specifically for dynamic modal content
4. **Event Listener Review**: Audit all Bootstrap modal event listeners to ensure correct event usage

### Edge Cases Discovered
1. **Focus/Blur Behavior**: Formatters show raw numbers on focus (correct UX)
2. **Programmatic Value Setting**: Programmatically setting input.value bypasses formatters (expected behavior)
3. **Modal Lifecycle**: Bootstrap 5 has specific event timing - `shown.bs.modal` is key for post-render actions

## 9. Backward Compatibility

**Impact**: ZERO breaking changes

- Existing page load inputs still work exactly as before
- New global function is additive, doesn't replace existing code
- Auto-save changes are internal, no API changes
- All existing functionality preserved
- No database migration needed
- No configuration changes required

**Migration**: None required - fixes are transparent to users and other code

## 10. Additional Notes

### Performance Considerations
- 50ms setTimeout minimal impact
- Formatter attachment is O(n) where n = number of inputs
- Auto-save uses 30-second interval (configurable)
- No memory leaks - auto-save properly cleaned up on modal close

### Bootstrap 5 Event Reference
- `show.bs.modal` - Fires immediately when show method called
- `shown.bs.modal` - Fires AFTER modal shown (transitions complete)
- `hide.bs.modal` - Fires immediately when hide method called
- `hidden.bs.modal` - Fires AFTER modal hidden (transitions complete)

**Key Lesson**: Use `shown.bs.modal` for post-render initialization, not `show.bs.modal`

### Testing Tools Used
- Playwright MCP for browser automation
- Browser console for debugging
- Live environment testing at test-company-alpha subdomain

### Future Enhancements
1. Consider MutationObserver for automatic formatter attachment to any new number inputs
2. Add unit tests for NumberFormatter class
3. Add integration tests for auto-save functionality
4. Consider visual indicator when formatting applied (subtle animation)

---

**Report Generated**: October 5, 2025
**Bug Fixer**: Claude (Anthropic)
**Status**: ✅ COMPLETE - Both bugs fixed and verified
**Ready for v4 Testing**: YES
