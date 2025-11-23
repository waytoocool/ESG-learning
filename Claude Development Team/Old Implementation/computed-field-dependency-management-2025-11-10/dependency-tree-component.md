# Dependency Tree View Component Specification

**Component Name:** DependencyTreeView
**Version:** 1.0.0
**Type:** Interactive Visualization Component

## 🎯 Component Purpose

Provide a visual hierarchical representation of computed field dependencies, allowing administrators to understand the relationships between fields at a glance.

---

## 🎨 Visual Design

### Tree Structure Layout

```
📊 Employee Turnover Rate (Computed)
├── Formula: A / B
├── Frequency: Quarterly ✅
├── Assigned to: 2 entities
└── Dependencies:
    ├── 📈 [A] Total Employee Turnover
    │   ├── Type: Raw Input
    │   ├── Frequency: Monthly ✅
    │   └── Status: Assigned ✅
    └── 👥 [B] Total Number of Employees
        ├── Type: Raw Input
        ├── Frequency: Monthly ✅
        └── Status: Assigned ✅

📊 Complex KPI (Computed)
├── Formula: (A + B) / C
├── Frequency: Annual ✅
├── Assigned to: Not assigned ⚠️
└── Dependencies:
    ├── 📊 [A] Sub-metric 1 (Computed)
    │   ├── Formula: X * Y
    │   ├── Frequency: Quarterly ✅
    │   └── Dependencies:
    │       ├── 📈 [X] Raw Value 1
    │       └── 📈 [Y] Raw Value 2
    ├── 📈 [B] Raw Input 2
    └── 📈 [C] Raw Input 3
```

---

## 🔧 Component Implementation

### HTML Structure

```html
<div class="dependency-tree-container">
    <div class="tree-header">
        <h3>📊 Field Dependencies</h3>
        <div class="tree-controls">
            <button id="expandAll">➕ Expand All</button>
            <button id="collapseAll">➖ Collapse All</button>
            <button id="refreshTree">🔄 Refresh</button>
            <input type="search" placeholder="Search fields..." id="treeSearch">
        </div>
    </div>

    <div class="tree-legend">
        <span class="legend-item">
            <span class="icon computed">📊</span> Computed Field
        </span>
        <span class="legend-item">
            <span class="icon raw">📈</span> Raw Input Field
        </span>
        <span class="legend-item">
            <span class="status-ok">✅</span> Valid
        </span>
        <span class="legend-item">
            <span class="status-warning">⚠️</span> Issue
        </span>
    </div>

    <div id="dependencyTree" class="tree-content">
        <!-- Dynamic content rendered here -->
    </div>

    <div class="tree-footer">
        <div class="tree-stats">
            <span>Total: <strong id="totalFields">0</strong> fields</span>
            <span>Computed: <strong id="computedCount">0</strong></span>
            <span>Dependencies: <strong id="depCount">0</strong></span>
        </div>
    </div>
</div>
```

### JavaScript Component

```javascript
/**
 * DependencyTreeView.js
 * Interactive dependency tree visualization component
 */

window.DependencyTreeView = (function() {
    'use strict';

    const state = {
        treeData: [],
        expandedNodes: new Set(),
        searchTerm: '',
        isInitialized: false
    };

    const config = {
        animationDuration: 300,
        indentSize: 30,
        maxDepth: 10
    };

    // Initialize component
    async function init() {
        console.log('[DependencyTreeView] Initializing...');

        // Cache DOM elements
        cacheElements();

        // Bind events
        bindEvents();

        // Load initial data
        await loadTreeData();

        // Render tree
        renderTree();

        state.isInitialized = true;
        console.log('[DependencyTreeView] Initialized successfully');
    }

    function cacheElements() {
        state.elements = {
            container: document.getElementById('dependencyTree'),
            expandAllBtn: document.getElementById('expandAll'),
            collapseAllBtn: document.getElementById('collapseAll'),
            refreshBtn: document.getElementById('refreshTree'),
            searchInput: document.getElementById('treeSearch'),
            totalFields: document.getElementById('totalFields'),
            computedCount: document.getElementById('computedCount'),
            depCount: document.getElementById('depCount')
        };
    }

    function bindEvents() {
        // Control buttons
        state.elements.expandAllBtn?.addEventListener('click', expandAll);
        state.elements.collapseAllBtn?.addEventListener('click', collapseAll);
        state.elements.refreshBtn?.addEventListener('click', refresh);

        // Search
        state.elements.searchInput?.addEventListener('input', handleSearch);

        // Tree node interactions
        state.elements.container?.addEventListener('click', handleNodeClick);

        // AppEvents integration
        AppEvents.on('dependency-data-changed', refresh);
        AppEvents.on('field-selection-changed', updateHighlights);
    }

    async function loadTreeData() {
        try {
            console.log('[DependencyTreeView] Loading tree data...');

            const response = await fetch('/admin/api/assignments/dependency-tree');
            if (!response.ok) throw new Error('Failed to load tree data');

            const data = await response.json();
            state.treeData = data.dependency_tree || [];

            updateStats();
            console.log('[DependencyTreeView] Loaded', state.treeData.length, 'computed fields');

        } catch (error) {
            console.error('[DependencyTreeView] Failed to load data:', error);
            showError('Failed to load dependency tree');
        }
    }

    function renderTree() {
        if (!state.elements.container) return;

        const html = state.treeData
            .filter(node => matchesSearch(node))
            .map(node => renderNode(node, 0))
            .join('');

        state.elements.container.innerHTML = html || '<div class="empty-state">No dependencies found</div>';
        updateHighlights();
    }

    function renderNode(node, depth = 0) {
        const nodeId = `node-${node.field_id}`;
        const isExpanded = state.expandedNodes.has(nodeId);
        const hasChildren = node.dependencies && node.dependencies.length > 0;
        const isSelected = AppState.isSelected(node.field_id);

        // Check assignment status
        const assignmentStatus = checkAssignmentStatus(node);

        const html = `
            <div class="tree-node depth-${depth} ${isSelected ? 'selected' : ''}"
                 data-node-id="${nodeId}"
                 data-field-id="${node.field_id}"
                 style="padding-left: ${depth * config.indentSize}px">

                <div class="node-header">
                    ${hasChildren ? `
                        <span class="node-toggle ${isExpanded ? 'expanded' : ''}"
                              data-toggle="${nodeId}">
                            ${isExpanded ? '▼' : '▶'}
                        </span>
                    ` : '<span class="node-spacer"></span>'}

                    <span class="node-icon">
                        ${node.is_computed ? '📊' : '📈'}
                    </span>

                    <span class="node-name ${assignmentStatus.hasIssues ? 'has-issues' : ''}">
                        ${highlightSearch(node.field_name)}
                        ${node.variable ? `<small>[${node.variable}]</small>` : ''}
                    </span>

                    <span class="node-status">
                        ${assignmentStatus.icon}
                    </span>

                    <div class="node-actions">
                        ${!isSelected ? `
                            <button class="btn-add-to-selection"
                                    data-field-id="${node.field_id}"
                                    title="Add to selection">
                                ➕
                            </button>
                        ` : `
                            <span class="in-selection" title="Already selected">✓</span>
                        `}
                        <button class="btn-info"
                                data-field-id="${node.field_id}"
                                title="View details">
                            ℹ️
                        </button>
                    </div>
                </div>

                ${node.is_computed ? `
                    <div class="node-details">
                        <span class="formula">Formula: ${node.formula}</span>
                        ${assignmentStatus.message ? `
                            <span class="status-message ${assignmentStatus.type}">
                                ${assignmentStatus.message}
                            </span>
                        ` : ''}
                    </div>
                ` : ''}

                ${hasChildren && isExpanded ? `
                    <div class="node-children">
                        ${node.dependencies.map(child =>
                            renderNode(child, depth + 1)
                        ).join('')}
                    </div>
                ` : ''}
            </div>
        `;

        return html;
    }

    function checkAssignmentStatus(node) {
        // Check if field is assigned
        const isAssigned = checkIfAssigned(node.field_id);

        // Check frequency compatibility
        const frequencyValid = checkFrequencyCompatibility(node);

        // Determine status
        if (!isAssigned) {
            return {
                hasIssues: true,
                icon: '⚠️',
                type: 'warning',
                message: 'Not assigned to any entities'
            };
        }

        if (!frequencyValid.isValid) {
            return {
                hasIssues: true,
                icon: '❌',
                type: 'error',
                message: frequencyValid.message
            };
        }

        return {
            hasIssues: false,
            icon: '✅',
            type: 'success',
            message: null
        };
    }

    function checkIfAssigned(fieldId) {
        // Check against AppState or make API call
        return AppState.entityAssignments.has(fieldId);
    }

    function checkFrequencyCompatibility(node) {
        if (!node.is_computed) return {isValid: true};

        // Check if dependencies have compatible frequencies
        const nodeFreq = AppState.configurations.get(node.field_id)?.frequency;
        if (!nodeFreq) return {isValid: true};

        for (const dep of node.dependencies || []) {
            const depFreq = AppState.configurations.get(dep.field_id)?.frequency;
            if (depFreq && !isFrequencyCompatible(depFreq, nodeFreq)) {
                return {
                    isValid: false,
                    message: `Dependency '${dep.field_name}' has incompatible frequency`
                };
            }
        }

        return {isValid: true};
    }

    function isFrequencyCompatible(depFreq, computedFreq) {
        const hierarchy = {
            'Annual': 1,
            'Quarterly': 2,
            'Monthly': 3
        };

        return hierarchy[depFreq] >= hierarchy[computedFreq];
    }

    function handleNodeClick(event) {
        const target = event.target;

        // Handle toggle
        if (target.classList.contains('node-toggle')) {
            const nodeId = target.dataset.toggle;
            toggleNode(nodeId);
            return;
        }

        // Handle add to selection
        if (target.classList.contains('btn-add-to-selection')) {
            const fieldId = target.dataset.fieldId;
            addToSelection(fieldId);
            return;
        }

        // Handle info button
        if (target.classList.contains('btn-info')) {
            const fieldId = target.dataset.fieldId;
            showFieldInfo(fieldId);
            return;
        }
    }

    function toggleNode(nodeId) {
        if (state.expandedNodes.has(nodeId)) {
            state.expandedNodes.delete(nodeId);
        } else {
            state.expandedNodes.add(nodeId);
        }
        renderTree();
    }

    function expandAll() {
        // Add all nodes with children to expanded set
        function collectNodes(nodes) {
            nodes.forEach(node => {
                if (node.dependencies && node.dependencies.length > 0) {
                    state.expandedNodes.add(`node-${node.field_id}`);
                    collectNodes(node.dependencies);
                }
            });
        }
        collectNodes(state.treeData);
        renderTree();
    }

    function collapseAll() {
        state.expandedNodes.clear();
        renderTree();
    }

    function handleSearch(event) {
        state.searchTerm = event.target.value.toLowerCase();
        renderTree();
    }

    function matchesSearch(node) {
        if (!state.searchTerm) return true;

        // Check if node or any child matches
        function searchInNode(n) {
            if (n.field_name.toLowerCase().includes(state.searchTerm)) {
                return true;
            }
            if (n.dependencies) {
                return n.dependencies.some(searchInNode);
            }
            return false;
        }

        return searchInNode(node);
    }

    function highlightSearch(text) {
        if (!state.searchTerm) return text;

        const regex = new RegExp(`(${state.searchTerm})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    function addToSelection(fieldId) {
        // Find field data
        const fieldData = findFieldInTree(fieldId);
        if (fieldData) {
            AppEvents.emit('data-point-add-requested', {
                fieldId: fieldId,
                field: fieldData
            });
        }
    }

    function findFieldInTree(fieldId) {
        function searchNode(nodes) {
            for (const node of nodes) {
                if (node.field_id === fieldId) {
                    return node;
                }
                if (node.dependencies) {
                    const found = searchNode(node.dependencies);
                    if (found) return found;
                }
            }
            return null;
        }
        return searchNode(state.treeData);
    }

    function showFieldInfo(fieldId) {
        const field = findFieldInTree(fieldId);
        if (field) {
            // Show modal with field details
            if (window.PopupManager) {
                const content = `
                    <div class="field-info-modal">
                        <h3>${field.field_name}</h3>
                        <dl>
                            <dt>Type:</dt>
                            <dd>${field.is_computed ? 'Computed' : 'Raw Input'}</dd>
                            ${field.formula ? `
                                <dt>Formula:</dt>
                                <dd><code>${field.formula}</code></dd>
                            ` : ''}
                            <dt>Field ID:</dt>
                            <dd><small>${field.field_id}</small></dd>
                        </dl>
                    </div>
                `;
                PopupManager.showModal('Field Information', content);
            }
        }
    }

    function updateHighlights() {
        // Update visual state based on current selections
        document.querySelectorAll('.tree-node').forEach(node => {
            const fieldId = node.dataset.fieldId;
            if (AppState.isSelected(fieldId)) {
                node.classList.add('selected');
            } else {
                node.classList.remove('selected');
            }
        });
    }

    function updateStats() {
        let totalFields = 0;
        let computedCount = 0;
        let depCount = 0;

        function countNodes(nodes) {
            nodes.forEach(node => {
                totalFields++;
                if (node.is_computed) {
                    computedCount++;
                }
                if (node.dependencies) {
                    depCount += node.dependencies.length;
                    countNodes(node.dependencies);
                }
            });
        }

        countNodes(state.treeData);

        if (state.elements.totalFields) {
            state.elements.totalFields.textContent = totalFields;
        }
        if (state.elements.computedCount) {
            state.elements.computedCount.textContent = computedCount;
        }
        if (state.elements.depCount) {
            state.elements.depCount.textContent = depCount;
        }
    }

    async function refresh() {
        console.log('[DependencyTreeView] Refreshing...');
        await loadTreeData();
        renderTree();
    }

    function showError(message) {
        if (state.elements.container) {
            state.elements.container.innerHTML = `
                <div class="error-state">
                    <span class="error-icon">❌</span>
                    <p>${message}</p>
                    <button onclick="DependencyTreeView.refresh()">Retry</button>
                </div>
            `;
        }
    }

    // Public API
    return {
        init,
        refresh,
        expandAll,
        collapseAll,
        getTreeData: () => state.treeData,
        isInitialized: () => state.isInitialized
    };
})();
```

### CSS Styling

```css
/* Dependency Tree Styles */
.dependency-tree-container {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    overflow: hidden;
    max-height: 600px;
    display: flex;
    flex-direction: column;
}

.tree-header {
    padding: 15px;
    background: #f9fafb;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.tree-header h3 {
    margin: 0;
    font-size: 1.125rem;
    color: #111827;
}

.tree-controls {
    display: flex;
    gap: 10px;
    align-items: center;
}

.tree-controls button {
    padding: 6px 12px;
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.875rem;
    transition: all 0.2s;
}

.tree-controls button:hover {
    background: #f3f4f6;
    border-color: #9ca3af;
}

.tree-controls input {
    padding: 6px 12px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    width: 200px;
}

.tree-legend {
    padding: 10px 15px;
    background: #fafbfc;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    gap: 20px;
    font-size: 0.875rem;
    color: #6b7280;
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 5px;
}

.tree-content {
    flex: 1;
    overflow-y: auto;
    padding: 15px;
}

/* Tree Node Styles */
.tree-node {
    margin: 2px 0;
    transition: background 0.2s;
}

.tree-node:hover {
    background: #f9fafb;
}

.tree-node.selected {
    background: #eff6ff;
}

.node-header {
    display: flex;
    align-items: center;
    padding: 8px;
    gap: 8px;
    position: relative;
}

.node-toggle {
    width: 20px;
    text-align: center;
    cursor: pointer;
    user-select: none;
    color: #6b7280;
    transition: transform 0.2s;
}

.node-toggle:hover {
    color: #111827;
    transform: scale(1.2);
}

.node-spacer {
    width: 20px;
    display: inline-block;
}

.node-icon {
    font-size: 1.25rem;
}

.node-name {
    flex: 1;
    font-weight: 500;
    color: #111827;
}

.node-name small {
    margin-left: 8px;
    color: #6b7280;
    font-weight: normal;
}

.node-name.has-issues {
    color: #dc2626;
}

.node-status {
    margin-right: 10px;
}

.node-actions {
    display: flex;
    gap: 5px;
    opacity: 0;
    transition: opacity 0.2s;
}

.tree-node:hover .node-actions {
    opacity: 1;
}

.node-actions button {
    padding: 2px 6px;
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 1rem;
    transition: transform 0.2s;
}

.node-actions button:hover {
    transform: scale(1.2);
}

.in-selection {
    color: #10b981;
    font-weight: bold;
}

.node-details {
    padding: 4px 8px 4px 36px;
    font-size: 0.875rem;
    color: #6b7280;
}

.formula {
    font-family: 'Monaco', 'Courier New', monospace;
    background: #f3f4f6;
    padding: 2px 6px;
    border-radius: 4px;
}

.status-message {
    margin-left: 10px;
    padding: 2px 6px;
    border-radius: 4px;
}

.status-message.warning {
    background: #fef3c7;
    color: #92400e;
}

.status-message.error {
    background: #fee2e2;
    color: #991b1b;
}

.node-children {
    border-left: 2px solid #e5e7eb;
    margin-left: 20px;
    animation: slideDown 0.3s ease;
}

/* Tree Footer */
.tree-footer {
    padding: 10px 15px;
    background: #f9fafb;
    border-top: 1px solid #e5e7eb;
}

.tree-stats {
    display: flex;
    gap: 20px;
    font-size: 0.875rem;
    color: #6b7280;
}

.tree-stats strong {
    color: #111827;
    font-weight: 600;
}

/* Empty & Error States */
.empty-state,
.error-state {
    padding: 40px;
    text-align: center;
    color: #6b7280;
}

.error-state .error-icon {
    font-size: 2rem;
    color: #ef4444;
    display: block;
    margin-bottom: 10px;
}

.error-state button {
    margin-top: 15px;
    padding: 8px 16px;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
}

/* Search Highlight */
mark {
    background: #fef3c7;
    color: inherit;
    padding: 0 2px;
    border-radius: 2px;
}

/* Animations */
@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Responsive */
@media (max-width: 768px) {
    .tree-controls {
        flex-wrap: wrap;
    }

    .tree-controls input {
        width: 100%;
    }

    .tree-legend {
        flex-wrap: wrap;
    }
}
```

---

## 🔗 Integration Points

### 1. With AppState
```javascript
// Listen for selection changes
AppEvents.on('state-selectedDataPoints-changed', () => {
    DependencyTreeView.updateHighlights();
});

// Listen for configuration changes
AppEvents.on('state-configuration-changed', () => {
    DependencyTreeView.refresh();
});
```

### 2. With DependencyManager
```javascript
// Share tree data
DependencyManager.setTreeData(DependencyTreeView.getTreeData());

// Coordinate selection
DependencyTreeView.onFieldSelect((fieldId) => {
    DependencyManager.handleFieldSelection({fieldId});
});
```

### 3. With PopupManager
```javascript
// Show field details modal
DependencyTreeView.onFieldInfo((field) => {
    PopupManager.showFieldDetailsModal(field);
});
```

---

## 🎯 Usage Example

```html
<!-- In assign_data_points.html -->
<div class="modal" id="dependencyTreeModal">
    <div class="modal-content large">
        <div class="modal-header">
            <h2>Field Dependencies</h2>
            <button class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
            <!-- Tree component renders here -->
            <div id="dependencyTreeContainer"></div>
        </div>
    </div>
</div>

<script>
// Initialize when modal opens
document.getElementById('viewDependenciesBtn').addEventListener('click', () => {
    if (!DependencyTreeView.isInitialized()) {
        DependencyTreeView.init();
    }
    document.getElementById('dependencyTreeModal').classList.add('active');
});
</script>
```

---

## 📊 Performance Considerations

1. **Lazy Loading:** Load child nodes on expand for large trees
2. **Virtual Scrolling:** For trees with 1000+ nodes
3. **Caching:** Cache rendered HTML for unchanged nodes
4. **Debouncing:** Debounce search input (300ms)
5. **Memoization:** Memoize expensive calculations

---

## ♿ Accessibility

1. **Keyboard Navigation:**
   - Arrow keys to navigate
   - Space/Enter to expand/collapse
   - Tab through actions

2. **ARIA Attributes:**
   ```html
   <div role="tree" aria-label="Field dependencies">
     <div role="treeitem" aria-expanded="true" aria-level="1">
   ```

3. **Screen Reader Support:**
   - Announce node relationships
   - Describe formulas
   - Status announcements

---

## 🧪 Testing

```javascript
// Unit tests
describe('DependencyTreeView', () => {
    test('renders tree correctly', () => {
        const mockData = [...];
        DependencyTreeView.setData(mockData);
        expect(DependencyTreeView.getNodeCount()).toBe(10);
    });

    test('expands and collapses nodes', () => {
        DependencyTreeView.expandAll();
        expect(DependencyTreeView.getExpandedCount()).toBe(5);
    });

    test('search filters correctly', () => {
        DependencyTreeView.search('employee');
        expect(DependencyTreeView.getVisibleNodes()).toBe(3);
    });
});
```