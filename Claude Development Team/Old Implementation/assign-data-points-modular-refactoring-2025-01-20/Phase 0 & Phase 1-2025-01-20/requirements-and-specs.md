# Phase 0 + 1: Assign Data Points Modular Refactoring Implementation Plan

## Project Overview
**Objective**: Implement Phase 0 (Duplicate Infrastructure) and Phase 1 (Foundation) of the assign data points modular refactoring

**Implementation Date**: 2025-01-20
**Test URL**: `/admin/assign-data-points-v2`
**Original URL**: `/admin/assign-data-points` (remains unchanged)

## Phase 0: Create Duplicate Testing Infrastructure

### Frontend Tasks

#### 1. Create Duplicate Route
**File**: `app/routes/admin.py`

Add new route after existing assign_data_points_redesigned route:
```python
@admin_bp.route('/assign-data-points-v2', methods=['GET'])
@login_required
@require_tenant_for_admin()
def assign_data_points_v2():
    """Modular assign data points interface - Progressive refactoring"""
    from ..services import frameworks_service  # Local import to avoid circular deps

    if is_super_admin():
        frameworks = Framework.query.all()
    else:
        frameworks_by_type = frameworks_service.separate_frameworks_by_type(current_user.company_id)
        frameworks = frameworks_by_type['company'] + frameworks_by_type['global']

    entities = get_admin_entities()
    data_points = get_admin_data_points()

    return render_template('admin/assign_data_points_v2.html',
                         frameworks=frameworks,
                         entities=entities,
                         data_points=data_points)
```

#### 2. Duplicate HTML Template
**Task**: Copy existing template to create v2 version

```bash
cp app/templates/admin/assign_data_points_redesigned.html \
   app/templates/admin/assign_data_points_v2.html
```

**Modifications**: None initially - exact copy for Phase 0

#### 3. Test Phase 0
**Success Criteria**:
- [ ] V2 page loads at `/admin/assign-data-points-v2`
- [ ] Identical functionality to original
- [ ] No visual differences
- [ ] All features work (framework selection, data point selection, etc.)

### Backend Tasks (Parallel Structure Setup)

#### 1. Create New Routes Structure
```bash
mkdir -p app/routes/admin_assignments
mkdir -p app/services/assignments
```

#### 2. Create Blueprint Foundation
**File**: `app/routes/admin_assignments/__init__.py`
```python
from flask import Blueprint

# Create new assignments blueprint for modular architecture
admin_assignments_bp = Blueprint('admin_assignments', __name__, url_prefix='/api/v1/assignments')

# Import route modules (will be created in subsequent phases)
# from .core import *
# from .api import *
# from .versioning import *
# from .history import *
# from .bulk_operations import *
```

#### 3. Create Services Foundation
**File**: `app/services/assignments/__init__.py`
```python
"""
Assignment services package for modular architecture
Consolidates assignment-related business logic
"""

# Service modules will be created progressively:
# - versioning_service.py (from assignment_versioning.py)
# - resolution_service.py (assignment resolution and caching)
# - validation_service.py (business logic validation)
# - cache_service.py (Redis/memory caching)
```

**Note**: No functional code yet - just structure for future phases

## Phase 1: Foundation - Event System & Services

### Frontend Tasks

#### 1. Create Directory Structure
```bash
mkdir -p app/static/js/admin/assign_data_points
mkdir -p app/static/css/admin/assign_data_points
```

#### 2. Create main.js - Global Event System
**File**: `app/static/js/admin/assign_data_points/main.js`

```javascript
/**
 * Main module for Assign Data Points - Global Event System & State Management
 * Phase 1: Foundation
 */

// Global Event System
window.AppEvents = {
    listeners: {},

    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    },

    off(event, callback) {
        if (!this.listeners[event]) return;
        this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    },

    emit(event, data) {
        console.log(`[AppEvents] ${event}:`, data);
        if (!this.listeners[event]) return;
        this.listeners[event].forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`[AppEvents] Error in ${event} listener:`, error);
            }
        });
    }
};

// Global State Management
window.AppState = {
    selectedDataPoints: new Map(),
    configurations: new Map(),
    entityAssignments: new Map(),

    // State mutation methods
    addSelectedDataPoint(dataPoint) {
        this.selectedDataPoints.set(dataPoint.id, dataPoint);
        AppEvents.emit('state-dataPoint-added', dataPoint);
        AppEvents.emit('state-selectedDataPoints-changed', this.selectedDataPoints);
    },

    removeSelectedDataPoint(dataPointId) {
        const dataPoint = this.selectedDataPoints.get(dataPointId);
        this.selectedDataPoints.delete(dataPointId);
        AppEvents.emit('state-dataPoint-removed', dataPoint);
        AppEvents.emit('state-selectedDataPoints-changed', this.selectedDataPoints);
    },

    setConfiguration(dataPointId, config) {
        this.configurations.set(dataPointId, config);
        AppEvents.emit('state-configuration-changed', {dataPointId, config});
    },

    getSelectedCount() {
        return this.selectedDataPoints.size;
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[AppMain] Event system and state management initialized');
    AppEvents.emit('app-initialized');
});
```

#### 3. Create ServicesModule.js - API Foundation
**File**: `app/static/js/admin/assign_data_points/ServicesModule.js`

```javascript
/**
 * Services Module for Assign Data Points - API Calls & Utilities
 * Phase 1: Foundation
 */

window.ServicesModule = {
    // API Base Configuration
    apiBase: '/admin',

    // Generic API call handler
    async apiCall(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        try {
            const response = await fetch(url, {...defaultOptions, ...options});
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`[ServicesModule] API call failed: ${endpoint}`, error);
            this.showMessage(`API Error: ${error.message}`, 'error');
            throw error;
        }
    },

    // Core API Methods (to be populated from legacy code)
    async loadEntities() {
        console.log('[ServicesModule] Loading entities...');
        return await this.apiCall('/get_entities');
    },

    async loadFrameworkFields(frameworkId) {
        console.log(`[ServicesModule] Loading framework fields for: ${frameworkId}`);
        return await this.apiCall(`/get_framework_fields/${frameworkId}`);
    },

    async loadExistingDataPoints() {
        console.log('[ServicesModule] Loading existing data points...');
        return await this.apiCall('/get_existing_data_points');
    },

    async loadCompanyTopics() {
        console.log('[ServicesModule] Loading company topics...');
        return await this.apiCall('/topics/company_dropdown');
    },

    // Utility Methods
    showMessage(message, type = 'info') {
        console.log(`[ServicesModule] ${type.toUpperCase()}: ${message}`);
        // For Phase 1, just log - will integrate with actual notification system later
        AppEvents.emit('message-shown', {message, type});
    },

    // Helper function for form data
    serializeForm(form) {
        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        return data;
    },

    // Helper function for URL parameters
    getUrlParams() {
        return new URLSearchParams(window.location.search);
    }
};

// Initialize services
document.addEventListener('DOMContentLoaded', function() {
    console.log('[ServicesModule] Services module initialized');
    AppEvents.emit('services-initialized');
});
```

#### 4. Update V2 Template
**File**: `app/templates/admin/assign_data_points_v2.html`

Add new modules before the legacy file:
```html
<!-- Phase 1: Add foundation modules BEFORE legacy file -->
<script src="{{ url_for('static', filename='js/admin/assign_data_points/main.js') }}"></script>
<script src="{{ url_for('static', filename='js/admin/assign_data_points/ServicesModule.js') }}"></script>

<!-- Legacy file continues to handle all functionality -->
<script src="{{ url_for('static', filename='js/admin/assign_data_points_redesigned.js') }}"></script>
```

### Backend Tasks (Phase 1)

#### 1. Create Core Services Structure
**File**: `app/services/assignments/versioning_service.py`
```python
"""
Assignment Versioning Service - Foundation
Will consolidate logic from assignment_versioning.py in future phases
"""

class AssignmentVersioningService:
    """Placeholder for future versioning logic extraction"""
    pass

class AssignmentResolutionService:
    """Placeholder for future resolution logic extraction"""
    pass
```

#### 2. Create API Structure
**File**: `app/routes/admin_assignments/core.py`
```python
"""
Core assignment routes - Foundation
Will be populated in future phases
"""
from flask import Blueprint

# Placeholder for future route extraction
```

## Testing Strategy for Phase 0 + 1

### Phase 0 Testing
**Test URL**: `/admin/assign-data-points-v2`

1. **Visual Verification**:
   - [ ] Page loads identically to original
   - [ ] All UI elements present
   - [ ] No visual differences

2. **Functional Verification**:
   - [ ] Framework dropdown works
   - [ ] Data point selection works
   - [ ] Search functionality works
   - [ ] Configuration modals work
   - [ ] All existing features operational

### Phase 1 Testing
**Test URL**: `/admin/assign-data-points-v2`

1. **Console Verification**:
   ```javascript
   // In browser console:
   typeof AppEvents !== 'undefined'  // Should return true
   typeof AppState !== 'undefined'   // Should return true
   typeof ServicesModule !== 'undefined'  // Should return true

   // Test event system
   AppEvents.emit('test-event', {test: 'data'})
   // Should log event

   // Test services
   ServicesModule.loadEntities().then(console.log)
   // Should return entity data
   ```

2. **Network Verification**:
   - [ ] API calls visible in DevTools Network tab
   - [ ] No duplicate requests
   - [ ] Error handling works

3. **State Verification**:
   - [ ] AppState methods work
   - [ ] Event listeners fire
   - [ ] No console errors

### UI Testing Agent Integration

After Phase 0 + 1 completion, use ui-testing-agent with:
```bash
npm run mcp:start  # Start MCP server
```

**Testing Scope**:
- Visual regression testing
- Functional workflow testing
- Performance benchmarking
- Cross-browser compatibility

## Success Criteria

### Phase 0 Complete
- [ ] V2 page functionally identical to original
- [ ] No regressions identified
- [ ] Parallel backend structure created

### Phase 1 Complete
- [ ] New modules loaded without affecting functionality
- [ ] Event system operational
- [ ] Services module ready for integration
- [ ] Console verification passes
- [ ] UI testing agent validation passes

## Risk Mitigation

1. **Rollback Plan**: Remove new script tags to revert to Phase 0
2. **Performance Monitoring**: Track page load times
3. **Error Handling**: Comprehensive console error monitoring
4. **Backup**: Original page always available at `/admin/assign-data-points`

## Next Steps After Phase 0 + 1

1. **Phase 2**: Services Integration - Replace legacy API calls
2. **Progressive Extraction**: Toolbar, panels, modals
3. **Versioning Integration**: Extract assignment versioning logic
4. **Backend Consolidation**: Move to new routes structure
5. **Complete Migration**: Remove legacy code

## Dependencies

- **Flask Application**: Running and accessible
- **Test Environment**: test-company-alpha
- **Admin Credentials**: alice@alpha.com / admin123
- **Playwright MCP**: For UI testing
- **Browser Tools**: For debugging and verification