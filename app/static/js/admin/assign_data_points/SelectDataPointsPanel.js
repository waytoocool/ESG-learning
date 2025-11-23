/**
 * SelectDataPointsPanel Module for Assign Data Points - Left Panel Functionality
 * Phase 4: Left panel functionality extracted from legacy code
 */

window.SelectDataPointsPanel = {
    // State tracking
    currentFrameworkId: null,
    currentView: 'topic-tree', // 'topic-tree', 'flat-list', 'search-results'
    searchTerm: '',
    isInitialized: false,

    // DOM element references
    elements: {
        frameworkSelect: null,
        searchInput: null,
        clearSearchButton: null,
        viewToggleButtons: null,
        topicTreeView: null,
        flatListView: null,
        searchResultsView: null,
        expandCollapseAll: null,
        leftPanelContainer: null
    },

    // Cached data
    frameworksData: null,
    topicsData: null,
    flatListData: null,
    searchResults: null,

    // Initialization
    init() {
        console.log('[SelectDataPointsPanel] Initializing SelectDataPointsPanel module...');
        this.cacheElements();
        this.bindEvents();
        this.setupEventListeners();
        this.loadFrameworks();

        // FIX BUG #2 (P0 CRITICAL): Auto-load topics on initialization
        // This matches legacy behavior where OLD page shows all topics immediately
        // NEW page was showing "Loading topic hierarchy..." indefinitely until framework selected
        console.log('[SelectDataPointsPanel] Auto-loading topic tree on initialization...');
        this.loadTopicTree(null);  // Load all topics from all frameworks

        this.isInitialized = true;
        AppEvents.emit('select-data-points-panel-initialized');
        console.log('[SelectDataPointsPanel] SelectDataPointsPanel initialized successfully');
    },

    // Element caching for performance
    cacheElements() {
        this.elements = {
            frameworkSelect: document.getElementById('framework_select'),
            searchInput: document.getElementById('dataPointSearch'),
            clearSearchButton: document.getElementById('clearSearch'),
            viewToggleButtons: document.querySelectorAll('#topicTreeViewBtn, #flatListViewBtn'),
            topicTreeView: document.getElementById('topicTreeView'), // Parent container
            topicTreeContainer: document.getElementById('topicTree'), // FIX: Child container for topic tree rendering
            flatListView: document.getElementById('flatListView'), // Parent container
            flatListContainer: document.getElementById('availableFields'), // FIX: Child container for flat list rendering
            searchResultsView: document.getElementById('searchResultsView'),
            expandCollapseAll: document.getElementById('expandCollapseAll'),
            leftPanelContainer: document.querySelector('.left-panel')
        };
        console.log('[SelectDataPointsPanel] DOM elements cached:', {
            frameworkSelect: !!this.elements.frameworkSelect,
            searchInput: !!this.elements.searchInput,
            topicTreeView: !!this.elements.topicTreeView,
            topicTreeContainer: !!this.elements.topicTreeContainer,
            flatListView: !!this.elements.flatListView,
            flatListContainer: !!this.elements.flatListContainer
        });
    },

    // Event binding
    bindEvents() {
        // Framework selection
        if (this.elements.frameworkSelect) {
            this.elements.frameworkSelect.addEventListener('change', (e) => {
                this.handleFrameworkChange(e.target.value);
            });
        }

        // Search functionality - trigger only on Enter key or search icon click
        if (this.elements.searchInput) {
            // Remove auto-search on input, only trigger on Enter
            this.elements.searchInput.addEventListener('keyup', (e) => {
                if (e.key === 'Enter') {
                    const searchTerm = e.target.value.trim();
                    if (searchTerm.length >= 2) {
                        this.performSearch(searchTerm);
                    } else if (searchTerm.length === 0) {
                        this.clearSearch();
                    }
                }
            });
        }

        // Make search icon clickable
        const searchIcon = document.querySelector('.search-icon');
        if (searchIcon) {
            searchIcon.style.cursor = 'pointer';
            searchIcon.addEventListener('click', () => {
                if (this.elements.searchInput) {
                    const searchTerm = this.elements.searchInput.value.trim();
                    if (searchTerm.length >= 2) {
                        this.performSearch(searchTerm);
                    }
                }
            });
        }

        if (this.elements.clearSearchButton) {
            this.elements.clearSearchButton.addEventListener('click', () => {
                this.clearSearch();
            });
        }

        // View toggle buttons
        this.elements.viewToggleButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const viewType = e.target.dataset.view;
                this.handleViewToggle(viewType);
            });
        });

        // FIX BUG #6: Wire up Expand/Collapse All buttons for topic tree
        const expandAllBtn = document.getElementById('expandAllTopics');
        const collapseAllBtn = document.getElementById('collapseAllTopics');

        if (expandAllBtn) {
            expandAllBtn.addEventListener('click', () => {
                this.expandAllTopics();
            });
        }

        if (collapseAllBtn) {
            collapseAllBtn.addEventListener('click', () => {
                this.collapseAllTopics();
            });
        }

        // Topic tree events (using event delegation on parent container)
        if (this.elements.topicTreeView) {
            // Topic toggle events
            this.elements.topicTreeView.addEventListener('click', (e) => {
                if (e.target.closest('.topic-toggle')) {
                    const topicId = e.target.closest('.topic-toggle').dataset.topicId;
                    this.toggleTopic(topicId);
                }
            });

            // "Add All" button events for topics
            this.elements.topicTreeView.addEventListener('click', (e) => {
                if (e.target.closest('.topic-add-all-btn')) {
                    const topicId = e.target.closest('.topic-add-all-btn').dataset.topicId;
                    this.handleAddAllFromTopic(topicId);
                }
            });

            // Individual "+" button events for data points in topic tree
            this.elements.topicTreeView.addEventListener('click', (e) => {
                const addBtn = e.target.closest('.add-field-btn');
                if (addBtn) {
                    const fieldId = addBtn.dataset.fieldId;
                    console.log('[SelectDataPointsPanel] Add button clicked for field in topic tree:', fieldId);
                    this.handleAddFieldFromTree(fieldId);
                }
            });

            // Data point checkbox events
            this.elements.topicTreeView.addEventListener('change', (e) => {
                if (e.target.classList.contains('data-point-checkbox')) {
                    const fieldId = e.target.dataset.fieldId;
                    const isChecked = e.target.checked;
                    this.handleDataPointSelection(fieldId, isChecked);
                }
            });
        }

        // Flat list events (using event delegation on parent container)
        if (this.elements.flatListContainer) {
            // Add field button clicks
            this.elements.flatListContainer.addEventListener('click', (e) => {
                const addBtn = e.target.closest('.add-field-btn');
                if (addBtn) {
                    const fieldId = addBtn.dataset.fieldId;
                    console.log('[SelectDataPointsPanel] Add button clicked for field:', fieldId);

                    const dataPointItem = this.findDataPointById(fieldId);
                    if (dataPointItem) {
                        const fieldData = {
                            id: dataPointItem.field_id || dataPointItem.id || fieldId,
                            field_id: dataPointItem.field_id || dataPointItem.id || fieldId,
                            name: dataPointItem.field_name || dataPointItem.name,
                            field_name: dataPointItem.field_name || dataPointItem.name,
                            topic: dataPointItem.topic,
                            path: dataPointItem.path,
                            ...dataPointItem
                        };
                        AppEvents.emit('data-point-add-requested', { fieldId, field: fieldData });
                        console.log('[SelectDataPointsPanel] Field added with complete data:', fieldData);
                    } else {
                        console.warn('[SelectDataPointsPanel] Field not found in flatListData, emitting fieldId only:', fieldId);
                        AppEvents.emit('data-point-add-requested', { fieldId });
                    }
                    addBtn.classList.add('selected');
                    addBtn.title = 'Already selected';
                }
            });

            // "Add All" framework button clicks
            this.elements.flatListContainer.addEventListener('click', (e) => {
                const addAllBtn = e.target.closest('.add-all-framework');
                if (addAllBtn) {
                    e.stopPropagation();
                    const frameworkName = addAllBtn.dataset.framework;
                    console.log('[SelectDataPointsPanel] Add All clicked for framework:', frameworkName);
                    this.handleAddAllFromFramework(frameworkName);
                }
            });

            // Framework header toggle clicks
            this.elements.flatListContainer.addEventListener('click', (e) => {
                const header = e.target.closest('.framework-header');
                if (header && !e.target.closest('.add-all-framework')) {
                    const frameworkNode = header.closest('.framework-node');
                    const toggleIcon = header.querySelector('.toggle-icon');
                    const children = frameworkNode.querySelector('.framework-fields');

                    const isExpanded = header.getAttribute('aria-expanded') === 'true';
                    if (isExpanded) {
                        children.style.display = 'none';
                        toggleIcon.classList.remove('fa-chevron-down');
                        toggleIcon.classList.add('fa-chevron-right');
                        header.setAttribute('aria-expanded', 'false');
                    } else {
                        children.style.display = 'block';
                        toggleIcon.classList.remove('fa-chevron-right');
                        toggleIcon.classList.add('fa-chevron-down');
                        header.setAttribute('aria-expanded', 'true');
                    }
                }
            });
        }

        console.log('[SelectDataPointsPanel] Event handlers bound');
    },

    // AppEvents listeners
    setupEventListeners() {
        // Listen for external state changes
        AppEvents.on('state-framework-changed', (data) => {
            this.syncFrameworkSelection(data.frameworkId);
        });

        AppEvents.on('state-search-changed', (data) => {
            this.syncSearchState(data.searchTerm);
        });

        AppEvents.on('state-view-changed', (data) => {
            this.syncViewState(data.viewType);
            // FIX BUG #1: Auto-render flat list when switching to flat-list view
            if (data.viewType === 'flat-list' && this.flatListData && this.flatListData.length > 0) {
                console.log('[SelectDataPointsPanel] Auto-rendering flat list on view change');
                this.renderFlatList();
            }
        });

        // Listen for data point selection changes
        AppEvents.on('data-point-selected', (data) => {
            this.updateDataPointSelection(data.fieldId, true);
        });

        AppEvents.on('data-point-deselected', (data) => {
            this.updateDataPointSelection(data.fieldId, false);
        });

        // Listen for CoreUI events (Phase 3 integration)
        AppEvents.on('toolbar-configure-clicked', (data) => {
            console.log('[SelectDataPointsPanel] Configure button clicked, selected count:', data.selectedCount);
        });

        AppEvents.on('toolbar-assign-clicked', (data) => {
            console.log('[SelectDataPointsPanel] Assign button clicked, selected count:', data.selectedCount);
        });

        AppEvents.on('toolbar-save-clicked', (data) => {
            console.log('[SelectDataPointsPanel] Save button clicked');
        });

        // Listen for company topics loaded
        AppEvents.on('company-topics-loaded', (data) => {
            console.log('[SelectDataPointsPanel] Company topics loaded:', data);
            if (data.success && data.topics) {
                this.topicsData = data.topics;
                this.renderTopicTree();
            }
        });

        console.log('[SelectDataPointsPanel] Event listeners set up');
    },

    // Framework handling
    async loadFrameworks() {
        try {
            console.log('[SelectDataPointsPanel] Loading frameworks...');
            AppEvents.emit('panel-loading-started', { section: 'frameworks' });

            const response = await fetch('/admin/frameworks/list');
            if (!response.ok) {
                console.warn('[SelectDataPointsPanel] Framework list API returned', response.status, 'using fallback');
                // For now, populate with a default option until the API is fixed
                this.frameworksData = [];
                this.populateFrameworkSelect();
                AppEvents.emit('frameworks-loaded', { count: 0 });
                return;
            }

            const data = await response.json();
            console.log('[SelectDataPointsPanel] Raw API response:', data);

            // Handle different API response formats
            this.frameworksData = data.frameworks || data || [];
            console.log('[SelectDataPointsPanel] Processed frameworks data:', this.frameworksData);

            this.populateFrameworkSelect();
            AppEvents.emit('frameworks-loaded', { count: this.frameworksData.length });

        } catch (error) {
            console.error('[SelectDataPointsPanel] Error loading frameworks:', error);
            console.log('[SelectDataPointsPanel] Using fallback framework loading');
            // For now, populate with a default option until the API is fixed
            this.frameworksData = [];
            this.populateFrameworkSelect();
            AppEvents.emit('panel-error', {
                section: 'frameworks',
                error: error.message
            });
        } finally {
            AppEvents.emit('panel-loading-ended', { section: 'frameworks' });
        }
    },

    populateFrameworkSelect() {
        if (!this.elements.frameworkSelect) {
            console.warn('[SelectDataPointsPanel] Framework select element not found');
            return;
        }

        if (!this.frameworksData || !Array.isArray(this.frameworksData)) {
            console.warn('[SelectDataPointsPanel] Invalid frameworks data:', this.frameworksData);
            return;
        }

        // Clear existing options
        this.elements.frameworkSelect.innerHTML = '<option value="">All Frameworks</option>';

        // Add framework options with validation
        this.frameworksData.forEach((framework, index) => {
            if (!framework) {
                console.warn('[SelectDataPointsPanel] Null framework at index:', index);
                return;
            }

            const option = document.createElement('option');
            option.value = framework.id || framework.framework_id || '';
            option.textContent = framework.name || framework.framework_name || `Framework ${index + 1}`;

            if (!option.value) {
                console.warn('[SelectDataPointsPanel] Framework missing ID:', framework);
            }

            this.elements.frameworkSelect.appendChild(option);
        });

        console.log('[SelectDataPointsPanel] Framework select populated with', this.frameworksData.length, 'frameworks');
    },

    async handleFrameworkChange(frameworkId) {
        console.log('[SelectDataPointsPanel] Framework changed:', frameworkId);

        this.currentFrameworkId = frameworkId;

        // Emit framework change event
        AppEvents.emit('framework-changed', {
            frameworkId: frameworkId,
            frameworkName: this.getFrameworkName(frameworkId)
        });

        // Update AppState
        if (window.AppState) {
            AppState.setFramework(frameworkId, this.getFrameworkName(frameworkId));
        }

        // Load topic tree for selected framework
        await this.loadTopicTree(frameworkId);

        // Clear search if active
        if (this.searchTerm) {
            this.clearSearch();
        }
    },

    getFrameworkName(frameworkId) {
        if (!frameworkId || !this.frameworksData) return 'All Frameworks';
        const framework = this.frameworksData.find(f => f.id == frameworkId);
        return framework ? framework.name : 'Unknown Framework';
    },

    // Topic tree handling
    async loadTopicTree(frameworkId = null) {
        try {
            console.log('[SelectDataPointsPanel] Loading topic tree for framework:', frameworkId);
            AppEvents.emit('panel-loading-started', { section: 'topics' });

            // Load topic tree structure
            const url = frameworkId
                ? `/admin/frameworks/all_topics_tree?framework_id=${frameworkId}`
                : '/admin/frameworks/all_topics_tree';

            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const topicStructure = await response.json();

            // FIX BUG #1: Load fields from all frameworks when no framework is selected
            // OLD CODE: When frameworkId was null, only topic structure was loaded without fields
            // NEW CODE: Load all fields from all frameworks and merge with topics
            if (frameworkId) {
                // Framework selected - load only that framework's fields
                console.log('[SelectDataPointsPanel] Loading framework fields for:', frameworkId);
                const fields = await window.ServicesModule.loadFrameworkFields(frameworkId);

                if (fields && fields.length > 0) {
                    console.log('[SelectDataPointsPanel] Loaded', fields.length, 'framework fields');
                    // Merge fields into topic structure
                    this.topicsData = this.mergeFieldsIntoTopics(topicStructure, fields);
                } else {
                    this.topicsData = topicStructure;
                }
            } else {
                // No framework selected - load ALL fields from ALL frameworks
                console.log('[SelectDataPointsPanel] Loading ALL fields from ALL frameworks');
                const allFields = await window.ServicesModule.loadAllFields();

                if (allFields && allFields.length > 0) {
                    console.log('[SelectDataPointsPanel] Loaded', allFields.length, 'total fields from all frameworks');
                    // Merge all fields into topic structure
                    this.topicsData = this.mergeFieldsIntoTopics(topicStructure, allFields);
                } else {
                    console.warn('[SelectDataPointsPanel] No fields loaded, using empty topic structure');
                    this.topicsData = topicStructure;
                }
            }

            this.renderTopicTree();
            this.generateFlatList();

            AppEvents.emit('topics-loaded', {
                topicCount: this.countTopics(this.topicsData),
                dataPointCount: this.countDataPoints(this.topicsData)
            });

        } catch (error) {
            console.error('[SelectDataPointsPanel] Error loading topic tree:', error);
            AppEvents.emit('panel-error', {
                section: 'topics',
                error: error.message
            });
        } finally {
            AppEvents.emit('panel-loading-ended', { section: 'topics' });
        }
    },

    // Merge framework fields into topic structure
    mergeFieldsIntoTopics(topics, fields) {
        console.log('[SelectDataPointsPanel] Merging', fields.length, 'fields into topic structure');

        // Create a map of topic_id -> fields for faster lookup
        const fieldsByTopic = {};
        fields.forEach(field => {
            const topicId = field.topic_id;
            if (topicId) {
                if (!fieldsByTopic[topicId]) {
                    fieldsByTopic[topicId] = [];
                }
                fieldsByTopic[topicId].push({
                    id: field.field_id,
                    name: field.field_name,
                    field_code: field.field_code,
                    field_name: field.field_name,
                    unit: field.default_unit || field.unit,
                    description: field.description,
                    topic_id: field.topic_id,
                    is_computed: field.is_computed || false  // BUG FIX: Include is_computed property for visual indicators
                });
            }
        });

        console.log('[SelectDataPointsPanel] Fields grouped by topic:', Object.keys(fieldsByTopic).length, 'topics');

        // Recursively merge fields into topics
        const mergeTopics = (topicArray) => {
            return topicArray.map(topic => {
                const mergedTopic = { ...topic };

                // Normalize topic ID field - API returns 'topic_id', but we need 'id' for consistency
                const topicId = topic.topic_id || topic.id;
                mergedTopic.id = topicId;

                // Add data points if this topic has any
                if (fieldsByTopic[topicId]) {
                    mergedTopic.data_points = fieldsByTopic[topicId];
                    console.log(`[SelectDataPointsPanel] Topic "${topic.name}" (${topicId}) has ${mergedTopic.data_points.length} fields`);
                } else {
                    mergedTopic.data_points = [];
                }

                // Normalize sub-topics field - API uses 'children', we use 'sub_topics'
                if (topic.children && topic.children.length > 0) {
                    mergedTopic.sub_topics = mergeTopics(topic.children);
                } else if (topic.sub_topics && topic.sub_topics.length > 0) {
                    mergedTopic.sub_topics = mergeTopics(topic.sub_topics);
                }

                return mergedTopic;
            });
        };

        const merged = mergeTopics(topics);
        console.log('[SelectDataPointsPanel] Topic merge complete');
        return merged;
    },

    renderTopicTree() {
        // FIX BUG #3 (P0 CRITICAL): Render into #topicTree child container, not #topicTreeView parent
        // Old page renders into #topicTree, new page was rendering into #topicTreeView
        // This caused topic hierarchy to not display properly
        if (!this.elements.topicTreeContainer || !this.topicsData) {
            console.warn('[SelectDataPointsPanel] Cannot render topic tree:', {
                topicTreeContainer: !!this.elements.topicTreeContainer,
                topicsData: !!this.topicsData
            });
            return;
        }

        console.log('[SelectDataPointsPanel] Rendering topic tree into #topicTree...');

        const treeHtml = this.generateTopicTreeHtml(this.topicsData);
        this.elements.topicTreeContainer.innerHTML = treeHtml;

        // Event listeners are now bound once in bindEvents() using event delegation
        this.updateDataPointSelections();

        AppEvents.emit('topic-tree-rendered');
        console.log('[SelectDataPointsPanel] Topic tree rendered successfully');
    },

    generateTopicTreeHtml(topics) {
        if (!topics || topics.length === 0) {
            return '<div class="no-data">No topics available</div>';
        }

        let html = '<div class="topic-tree">';

        topics.forEach(topic => {
            html += this.generateTopicHtml(topic);
        });

        html += '</div>';
        return html;
    },

    generateTopicHtml(topic) {
        const hasDataPoints = topic.data_points && topic.data_points.length > 0;
        const hasSubTopics = topic.sub_topics && topic.sub_topics.length > 0;
        const totalDataPoints = this.getTopicDataPointCount(topic);

        let html = `<div class="topic-item" data-topic-id="${topic.id}">`;

        // Topic header
        html += `<div class="topic-header">`;

        if (hasSubTopics || hasDataPoints) {
            html += `<span class="topic-toggle" data-topic-id="${topic.id}">
                        <i class="fas fa-chevron-right"></i>
                     </span>`;
        }

        html += `<span class="topic-name">${topic.name}</span>`;

        // Add "Add All" button for topics with data points (wrapped in topic-actions for hover effect)
        if (totalDataPoints > 0) {
            html += `<div class="topic-actions">
                        <button class="topic-add-all-btn btn btn-sm btn-outline-primary"
                                data-topic-id="${topic.id}"
                                title="Add all ${totalDataPoints} fields from this topic">
                            <i class="fas fa-plus-circle"></i> Add All
                        </button>
                    </div>`;
        }

        html += `</div>`;

        // Topic children (collapsed by default)
        // FIX BUG #4: Use 'topic-children' class to match CSS, not 'topic-content'
        if (hasDataPoints || hasSubTopics) {
            html += `<div class="topic-children" style="display: none;">`;

            // Data points
            if (hasDataPoints) {
                html += '<div class="topic-data-points">';
                topic.data_points.forEach(dataPoint => {
                    html += this.generateDataPointHtml(dataPoint, topic.id);
                });
                html += '</div>';
            }

            // Sub topics
            if (hasSubTopics) {
                html += '<div class="sub-topics">';
                topic.sub_topics.forEach(subTopic => {
                    html += this.generateTopicHtml(subTopic);
                });
                html += '</div>';
            }

            html += '</div>';
        }

        html += '</div>';
        return html;
    },

    generateDataPointHtml(dataPoint, topicId) {
        const isSelected = window.AppState ? AppState.isSelected(dataPoint.id) : false;
        const checkedAttr = isSelected ? 'checked' : '';
        // Use consistent button class with .selected modifier for state
        const buttonClass = isSelected ? 'add-field-btn btn btn-sm btn-primary selected' : 'add-field-btn btn btn-sm btn-primary';
        const buttonTitle = isSelected ? 'Field already selected' : 'Add this field';

        // Extract field data with fallbacks
        const fieldName = dataPoint.field_name || dataPoint.name || '';
        const fieldCode = dataPoint.field_code || dataPoint.code || '';
        const description = dataPoint.description || '';

        // BUG FIX: Check if field is computed and get dependency count
        const isComputed = dataPoint.is_computed || false;
        const dependencyCount = window.DependencyManager && isComputed ?
            window.DependencyManager.getDependencies(dataPoint.id).length : 0;

        const computedBadge = isComputed ?
            `<span class="computed-badge" title="Computed field with ${dependencyCount} dependencies">
                <i class="fas fa-calculator"></i> <small>(${dependencyCount})</small>
            </span>` : '';

        return `
            <div class="topic-data-point ${isComputed ? 'is-computed' : ''}" data-field-id="${dataPoint.id}" data-topic-id="${topicId}">
                <div class="field-info">
                    <div class="field-details">
                        <div class="field-display">
                            <div class="field-first-line">
                                <span class="field-name">${fieldName}</span>
                                ${computedBadge}
                            </div>
                            <div class="field-second-line">
                                <span class="field-code">${fieldCode}</span>
                                ${description ? `<span class="field-description" title="${description}">${description}</span>` : ''}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="field-actions">
                    <button class="${buttonClass}"
                            data-field-id="${dataPoint.id}"
                            data-topic-id="${topicId}"
                            title="${buttonTitle}">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
            </div>
        `;
    },

    // REMOVED: bindTopicTreeEvents() - Event delegation is now handled in bindEvents()
    // This method was causing duplicate event listeners and double-firing of toggle events

    toggleTopic(topicId) {
        const topicElement = this.elements.topicTreeView.querySelector(`[data-topic-id="${topicId}"]`);
        if (!topicElement) return;

        // FIX BUG #5: Look for '.topic-children' to match HTML structure, not '.topic-content'
        const content = topicElement.querySelector('.topic-children');
        const toggle = topicElement.querySelector('.topic-toggle i');

        if (!content || !toggle) return;

        const isExpanded = content.style.display !== 'none';

        if (isExpanded) {
            content.style.display = 'none';
            toggle.className = 'fas fa-chevron-right';
            AppEvents.emit('topic-collapsed', { topicId });
        } else {
            content.style.display = 'block';
            toggle.className = 'fas fa-chevron-down';
            AppEvents.emit('topic-expanded', { topicId });
        }
    },

    // FIX BUG #6: Expand/Collapse All functionality for topic tree
    expandAllTopics() {
        if (!this.elements.topicTreeView) return;

        const allTopicItems = this.elements.topicTreeView.querySelectorAll('.topic-item');
        allTopicItems.forEach(topicItem => {
            const childrenContainer = topicItem.querySelector('.topic-children');
            const toggleIcon = topicItem.querySelector('.topic-toggle i');

            if (childrenContainer) {
                childrenContainer.style.display = 'block';
                if (toggleIcon) {
                    toggleIcon.className = 'fas fa-chevron-down';
                }
            }
        });

        AppEvents.emit('all-topics-expanded');
        console.log('[SelectDataPointsPanel] All topics expanded');
    },

    collapseAllTopics() {
        if (!this.elements.topicTreeView) return;

        const allTopicItems = this.elements.topicTreeView.querySelectorAll('.topic-item');
        allTopicItems.forEach(topicItem => {
            const childrenContainer = topicItem.querySelector('.topic-children');
            const toggleIcon = topicItem.querySelector('.topic-toggle i');

            if (childrenContainer) {
                childrenContainer.style.display = 'none';
                if (toggleIcon) {
                    toggleIcon.className = 'fas fa-chevron-right';
                }
            }
        });

        AppEvents.emit('all-topics-collapsed');
        console.log('[SelectDataPointsPanel] All topics collapsed');
    },

    handleDataPointSelection(fieldId, isSelected) {
        console.log('[SelectDataPointsPanel] Data point selection changed:', fieldId, isSelected);

        // Update AppState
        if (window.AppState) {
            if (isSelected) {
                // FIX BUG #2 (P0): Use findDataPointById() to get complete field data object
                // Previous bug: passed fieldId string instead of complete object, causing "Unnamed Field"
                const dataPoint = this.findDataPointById(fieldId);
                if (dataPoint) {
                    const fieldData = {
                        id: dataPoint.field_id || dataPoint.id || fieldId,
                        field_id: dataPoint.field_id || dataPoint.id || fieldId,
                        name: dataPoint.field_name || dataPoint.name,
                        field_name: dataPoint.field_name || dataPoint.name,
                        topic: dataPoint.topic,
                        path: dataPoint.path,
                        ...dataPoint  // Spread all other properties
                    };
                    AppState.addSelectedDataPoint(fieldData);
                    console.log('[SelectDataPointsPanel] Added data point via checkbox:', fieldData);
                } else {
                    console.error('[SelectDataPointsPanel] Could not find data point for fieldId:', fieldId);
                }
            } else {
                AppState.removeSelectedDataPoint(fieldId);
            }
        }

        // Emit selection events
        const eventName = isSelected ? 'data-point-selected' : 'data-point-deselected';
        AppEvents.emit(eventName, { fieldId, isSelected });

        // Update UI across all views
        this.updateDataPointSelections();
    },

    // Search functionality
    handleSearchInput(searchTerm) {
        console.log('[SelectDataPointsPanel] Search input:', searchTerm);

        this.searchTerm = searchTerm.trim();

        // Debounce search with shorter delay for better UX
        clearTimeout(this.searchDebounce);
        this.searchDebounce = setTimeout(() => {
            if (this.searchTerm.length >= 2) {
                this.performSearch(this.searchTerm);
            } else if (this.searchTerm.length === 0) {
                this.clearSearch();
            }
        }, 150);

        AppEvents.emit('search-input-changed', { searchTerm: this.searchTerm });
    },

    async performSearch(searchTerm) {
        if (!searchTerm || searchTerm.length < 2) return;

        try {
            // Store search term
            this.searchTerm = searchTerm;

            console.log('[SelectDataPointsPanel] Performing search:', searchTerm);
            AppEvents.emit('panel-loading-started', { section: 'search' });

            // Switch to search results view
            this.handleViewToggle('search-results');

            // Perform search on current topics data
            this.searchResults = this.searchInTopicsData(searchTerm);

            this.renderSearchResults();

            AppEvents.emit('search-completed', {
                searchTerm,
                resultCount: this.countSearchResults()
            });

        } catch (error) {
            console.error('[SelectDataPointsPanel] Search error:', error);
            AppEvents.emit('panel-error', {
                section: 'search',
                error: error.message
            });
        } finally {
            AppEvents.emit('panel-loading-ended', { section: 'search' });
        }
    },

    searchInTopicsData(searchTerm) {
        if (!this.topicsData) return [];

        const results = [];
        const searchLower = searchTerm.toLowerCase();

        const searchInTopic = (topic, parentPath = '') => {
            const currentPath = parentPath ? `${parentPath} > ${topic.name}` : topic.name;

            // Search in topic name
            if (topic.name.toLowerCase().includes(searchLower)) {
                results.push({
                    type: 'topic',
                    topic: topic,
                    path: currentPath,
                    match: 'name'
                });
            }

            // Search in data points
            if (topic.data_points) {
                topic.data_points.forEach(dataPoint => {
                    if (dataPoint.name.toLowerCase().includes(searchLower)) {
                        results.push({
                            type: 'data_point',
                            dataPoint: dataPoint,
                            topic: topic,
                            path: currentPath,
                            match: 'name'
                        });
                    }
                });
            }

            // Search in sub topics
            if (topic.sub_topics) {
                topic.sub_topics.forEach(subTopic => {
                    searchInTopic(subTopic, currentPath);
                });
            }
        };

        this.topicsData.forEach(topic => searchInTopic(topic));
        return results;
    },

    renderSearchResults() {
        if (!this.elements.searchResultsView || !this.searchResults) return;

        console.log('[SelectDataPointsPanel] Rendering search results...');

        // Get the actual results container (child div)
        const searchResultsContainer = document.getElementById('searchResults');
        if (!searchResultsContainer) {
            console.error('[SelectDataPointsPanel] #searchResults container not found');
            return;
        }

        if (this.searchResults.length === 0) {
            searchResultsContainer.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>No results found for "${this.searchTerm}"</p>
                </div>
            `;
            return;
        }

        // Group results by framework
        const groupedResults = this.groupSearchResultsByFramework();

        let html = '';

        // Render grouped results
        Object.entries(groupedResults).forEach(([frameworkName, results]) => {
            html += `
                <div class="search-group">
                    <h6 class="search-group-header">
                        <i class="fas fa-layer-group"></i> ${frameworkName} (${results.length})
                    </h6>
            `;

            results.forEach(result => {
                if (result.type === 'data_point') {
                    html += this.generateSearchDataPointHtml(result);
                }
            });

            html += '</div>';
        });

        searchResultsContainer.innerHTML = html;

        this.bindSearchResultsEvents();
        this.updateDataPointSelections();

        AppEvents.emit('search-results-rendered', {
            resultCount: this.searchResults.length
        });
    },

    groupSearchResultsByFramework() {
        const grouped = {};

        this.searchResults.forEach(result => {
            // Only process data_point type results
            if (result.type !== 'data_point') return;

            // Get framework name from topic object
            const frameworkName = result.topic?.framework_name || 'Uncategorized';
            if (!grouped[frameworkName]) {
                grouped[frameworkName] = [];
            }
            grouped[frameworkName].push(result);
        });

        return grouped;
    },

    generateSearchDataPointHtml(result) {
        const isSelected = window.AppState ? AppState.isSelected(result.dataPoint.id) : false;
        const fieldName = result.dataPoint.name || result.dataPoint.field_name || '';
        const description = result.dataPoint.description || '';

        // Build breadcrumb path - get framework name from topic object
        const breadcrumbParts = [];
        if (result.topic?.framework_name) {
            breadcrumbParts.push(result.topic.framework_name);
        }
        if (result.path) {
            breadcrumbParts.push(result.path);
        }
        const breadcrumbPath = breadcrumbParts.join(' > ');

        // Highlight search term in field name and description
        const highlightedName = this.highlightSearchTerm(fieldName, this.searchTerm);
        const highlightedDescription = description ? this.highlightSearchTerm(description, this.searchTerm) : '';

        return `
            <div class="search-result-item" data-field-id="${result.dataPoint.id}">
                <div class="field-main-info">
                    <div class="field-name-section">
                        <span class="search-field-name">${highlightedName}</span>
                    </div>
                    <div class="search-breadcrumb">
                        <i class="fas fa-sitemap"></i>
                        <span class="breadcrumb-path">${breadcrumbPath}</span>
                    </div>
                    ${highlightedDescription ? `
                    <div class="field-description">
                        <small class="description-text">${highlightedDescription}</small>
                    </div>
                    ` : ''}
                </div>
                <div class="search-result-actions">
                    <button class="add-search-result btn btn-sm btn-primary ${isSelected ? 'selected' : ''}"
                            data-field-id="${result.dataPoint.id}"
                            title="${isSelected ? 'Already selected' : 'Add this field'}">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
            </div>
        `;
    },

    highlightSearchTerm(text, searchTerm) {
        if (!text || !searchTerm) return text;

        const regex = new RegExp(`(${this.escapeRegex(searchTerm)})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    },

    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    },

    bindSearchResultsEvents() {
        this.elements.searchResultsView.addEventListener('click', (e) => {
            const button = e.target.closest('.add-search-result');
            if (button) {
                const fieldId = button.dataset.fieldId;
                this.handleDataPointSelection(fieldId, true);
            }
        });
    },

    clearSearch() {
        console.log('[SelectDataPointsPanel] Clearing search');

        this.searchTerm = '';
        this.searchResults = null;

        if (this.elements.searchInput) {
            this.elements.searchInput.value = '';
        }

        // Return to previous view (topic-tree by default)
        this.handleViewToggle('topic-tree');

        AppEvents.emit('search-cleared');
    },

    // View handling
    handleViewToggle(viewType) {
        console.log('[SelectDataPointsPanel] View toggle:', viewType);

        this.currentView = viewType;

        // Update view toggle buttons
        this.elements.viewToggleButtons.forEach(button => {
            if (button.dataset.view === viewType) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });

        // Show/hide view containers
        const views = {
            'topic-tree': this.elements.topicTreeView,
            'flat-list': this.elements.flatListView,
            'search-results': this.elements.searchResultsView
        };

        Object.entries(views).forEach(([view, element]) => {
            if (element) {
                element.style.display = view === viewType ? 'block' : 'none';
            }
        });

        // Load view-specific data if needed
        switch (viewType) {
            case 'flat-list':
                this.renderFlatList();
                break;
            case 'search-results':
                if (!this.searchResults && this.searchTerm) {
                    this.performSearch(this.searchTerm);
                }
                break;
        }

        AppEvents.emit('view-changed', { viewType, previousView: this.currentView });

        // Update AppState
        if (window.AppState) {
            AppState.setView(viewType);
        }
    },

    // Flat list handling
    generateFlatList() {
        if (!this.topicsData) return;

        this.flatListData = [];

        const flattenTopics = (topics, parentPath = '') => {
            topics.forEach(topic => {
                const currentPath = parentPath ? `${parentPath} > ${topic.name}` : topic.name;

                if (topic.data_points) {
                    topic.data_points.forEach(dataPoint => {
                        this.flatListData.push({
                            dataPoint: dataPoint,
                            topic: topic,
                            path: currentPath
                        });
                    });
                }

                if (topic.sub_topics) {
                    flattenTopics(topic.sub_topics, currentPath);
                }
            });
        };

        flattenTopics(this.topicsData);
        console.log('[SelectDataPointsPanel] Flat list generated:', this.flatListData.length, 'items');
    },

    renderFlatList() {
        // FIX: Render into the child container #availableFields, not the parent #flatListView
        if (!this.elements.flatListContainer || !this.flatListData) {
            console.warn('[SelectDataPointsPanel] Cannot render flat list - missing container or data:', {
                flatListContainer: !!this.elements.flatListContainer,
                flatListData: !!this.flatListData,
                dataLength: this.flatListData?.length
            });
            return;
        }

        console.log('[SelectDataPointsPanel] Rendering flat list with', this.flatListData.length, 'items...');

        if (this.flatListData.length === 0) {
            this.elements.flatListContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-info-circle"></i>
                    <p>No data points available</p>
                    <small>Select a framework to view data points</small>
                </div>
            `;
            return;
        }

        // Group by framework for better organization (matching legacy behavior)
        const groupedByFramework = this.flatListData.reduce((acc, item) => {
            const frameworkName = item.dataPoint.framework_name || item.topic.framework_name || 'Unknown Framework';
            if (!acc[frameworkName]) {
                acc[frameworkName] = [];
            }
            acc[frameworkName].push(item);
            return acc;
        }, {});

        let html = '<div class="flat-data-points-list topic-tree-style">';

        // Render each framework group
        Object.entries(groupedByFramework).forEach(([frameworkName, items]) => {
            html += `
                <div class="framework-node topic-node" data-framework="${frameworkName}">
                    <div class="framework-header topic-header" role="button" aria-expanded="true">
                        <div class="topic-toggle">
                            <i class="fas fa-chevron-down toggle-icon"></i>
                        </div>
                        <div class="topic-info">
                            <span class="framework-name topic-name">${frameworkName}</span>
                            <span class="field-count">(${items.length} fields)</span>
                        </div>
                        <div class="topic-actions">
                            <button class="add-all-framework btn btn-sm btn-outline-primary"
                                    data-framework="${frameworkName}"
                                    title="Add all fields in this framework">
                                <i class="fas fa-plus-circle"></i> Add All
                            </button>
                        </div>
                    </div>
                    <div class="framework-fields topic-children">
            `;

            items.forEach(item => {
                const isSelected = window.AppState ? AppState.isSelected(item.dataPoint.id) : false;
                const fieldName = item.dataPoint.field_name || item.dataPoint.name || '';
                const fieldCode = item.dataPoint.field_code || item.dataPoint.code || '';
                const description = item.dataPoint.description || '';

                // Check if field is computed and get dependency count
                const isComputed = item.dataPoint.is_computed || false;
                const dependencyCount = window.DependencyManager && isComputed ?
                    window.DependencyManager.getDependencies(item.dataPoint.id).length : 0;

                const computedBadge = isComputed ?
                    `<span class="computed-badge" title="Computed field with ${dependencyCount} dependencies">
                        <i class="fas fa-calculator"></i> <small>(${dependencyCount})</small>
                    </span>` : '';

                html += `
                    <div class="field-item topic-data-point ${isComputed ? 'is-computed' : ''}" data-field-id="${item.dataPoint.id}">
                        <div class="field-info">
                            <div class="field-details">
                                <div class="field-display">
                                    <div class="field-first-line">
                                        <span class="field-name">${fieldName}</span>
                                        ${computedBadge}
                                    </div>
                                    <div class="field-second-line">
                                        <span class="field-code">${fieldCode}</span>
                                        ${description ? `<span class="field-description" title="${description}">${description}</span>` : ''}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="field-actions">
                            <button class="add-field-btn btn btn-sm btn-primary ${isSelected ? 'selected' : ''}"
                                    data-field-id="${item.dataPoint.id}"
                                    title="${isSelected ? 'Already selected' : 'Add this field'}">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        });

        html += '</div>';
        this.elements.flatListContainer.innerHTML = html;

        // Note: Event listeners are bound once in bindEvents(), no need to rebind here
        this.updateDataPointSelections();

        AppEvents.emit('flat-list-rendered', {
            itemCount: this.flatListData.length
        });

        console.log('[SelectDataPointsPanel] Flat list rendered successfully');
    },

    generateFlatListItemHtml(item) {
        const isSelected = window.AppState ? AppState.isSelected(item.dataPoint.id) : false;
        const checkedAttr = isSelected ? 'checked' : '';

        // Extract field data (support both old 'name' and new 'field_name' properties)
        const fieldCode = item.dataPoint.field_code || item.dataPoint.code || '';
        const fieldName = item.dataPoint.field_name || item.dataPoint.name || '';
        const description = item.dataPoint.description || '';

        return `
            <div class="flat-list-item" data-field-id="${item.dataPoint.id}">
                <div class="item-content">
                    <div class="data-point-code">${fieldCode}</div>
                    <div class="data-point-name">${fieldName}</div>
                    <div class="data-point-description" title="${description}">${description}</div>
                </div>
                <button class="add-field-btn btn btn-sm btn-primary ${isSelected ? 'selected' : ''}"
                        data-field-id="${item.dataPoint.id}"
                        title="${isSelected ? 'Field already selected' : 'Add this field'}">
                    <i class="fas fa-plus"></i>
                </button>
            </div>
        `;
    },

    // DEPRECATED: bindFlatListEvents() - Event listeners now bound once in bindEvents()
    // This method is no longer called to prevent duplicate event listeners
    bindFlatListEvents() {
        // All flat list event listeners are now bound once in bindEvents() method
        // to match the pattern used by topic tree events and prevent duplicate listeners
        console.log('[SelectDataPointsPanel] bindFlatListEvents() is deprecated - events bound in bindEvents()');
    },

    // Expand/Collapse All
    handleExpandCollapseAll() {
        if (this.currentView !== 'topic-tree') return;

        const allTopicContents = this.elements.topicTreeView.querySelectorAll('.topic-content');
        const allToggles = this.elements.topicTreeView.querySelectorAll('.topic-toggle i');

        // Check if any topics are collapsed
        const hasCollapsed = Array.from(allTopicContents).some(content =>
            content.style.display === 'none'
        );

        if (hasCollapsed) {
            // Expand all
            allTopicContents.forEach(content => {
                content.style.display = 'block';
            });
            allToggles.forEach(toggle => {
                toggle.className = 'fas fa-chevron-down';
            });

            if (this.elements.expandCollapseAll) {
                this.elements.expandCollapseAll.textContent = 'Collapse All';
            }

            AppEvents.emit('all-topics-expanded');
        } else {
            // Collapse all
            allTopicContents.forEach(content => {
                content.style.display = 'none';
            });
            allToggles.forEach(toggle => {
                toggle.className = 'fas fa-chevron-right';
            });

            if (this.elements.expandCollapseAll) {
                this.elements.expandCollapseAll.textContent = 'Expand All';
            }

            AppEvents.emit('all-topics-collapsed');
        }
    },

    // Utility functions
    /**
     * Find complete data point object by field ID
     * Searches both flatListData and topicsData hierarchy
     * Used by flat list add button to get complete field data
     */
    findDataPointById(fieldId) {
        // First try flatListData (if available and populated)
        if (this.flatListData && this.flatListData.length > 0) {
            const item = this.flatListData.find(item =>
                item.dataPoint.id === fieldId ||
                item.dataPoint.field_id === fieldId ||
                String(item.dataPoint.id) === String(fieldId) ||
                String(item.dataPoint.field_id) === String(fieldId)
            );

            if (item) {
                return {
                    ...item.dataPoint,
                    topic: item.topic,
                    path: item.path
                };
            }
        }

        // Fallback: search topicsData recursively
        if (this.topicsData) {
            const searchInTopics = (topics, parentPath = '') => {
                for (const topic of topics) {
                    const currentPath = parentPath ? `${parentPath} > ${topic.name}` : topic.name;

                    if (topic.data_points) {
                        const dataPoint = topic.data_points.find(dp =>
                            dp.id === fieldId ||
                            dp.field_id === fieldId ||
                            String(dp.id) === String(fieldId) ||
                            String(dp.field_id) === String(fieldId)
                        );

                        if (dataPoint) {
                            return {
                                ...dataPoint,
                                topic: topic,
                                path: currentPath
                            };
                        }
                    }

                    if (topic.sub_topics) {
                        const found = searchInTopics(topic.sub_topics, currentPath);
                        if (found) return found;
                    }
                }
                return null;
            };

            return searchInTopics(this.topicsData);
        }

        return null;
    },

    updateDataPointSelections() {
        if (!window.AppState) return;

        const checkboxes = document.querySelectorAll('.data-point-checkbox');
        checkboxes.forEach(checkbox => {
            const fieldId = checkbox.dataset.fieldId;
            const isSelected = AppState.isSelected(fieldId);
            checkbox.checked = isSelected;
        });
    },

    updateDataPointSelection(fieldId, isSelected) {
        const checkboxes = document.querySelectorAll(`[data-field-id="${fieldId}"] .data-point-checkbox`);
        checkboxes.forEach(checkbox => {
            checkbox.checked = isSelected;
        });

        // Update button visual state in all views (topic tree and flat list)
        const buttons = document.querySelectorAll(`.add-field-btn[data-field-id="${fieldId}"]`);
        buttons.forEach(button => {
            if (isSelected) {
                button.classList.add('selected');
                button.title = 'Field already selected';
            } else {
                button.classList.remove('selected');
                button.title = 'Add this field';
            }
        });
    },

    syncFrameworkSelection(frameworkId) {
        if (this.elements.frameworkSelect && this.currentFrameworkId !== frameworkId) {
            this.elements.frameworkSelect.value = frameworkId || '';
            this.handleFrameworkChange(frameworkId);
        }
    },

    syncSearchState(searchTerm) {
        if (this.elements.searchInput && this.searchTerm !== searchTerm) {
            this.elements.searchInput.value = searchTerm || '';
            this.searchTerm = searchTerm || '';

            if (searchTerm) {
                this.performSearch(searchTerm);
            } else {
                this.clearSearch();
            }
        }
    },

    syncViewState(viewType) {
        if (this.currentView !== viewType) {
            this.handleViewToggle(viewType);
        }
    },

    countTopics(topics) {
        if (!topics || !Array.isArray(topics)) return 0;

        let count = topics.length;
        topics.forEach(topic => {
            if (topic.sub_topics) {
                count += this.countTopics(topic.sub_topics);
            }
        });
        return count;
    },

    countDataPoints(topics) {
        if (!topics || !Array.isArray(topics)) return 0;

        let count = 0;
        topics.forEach(topic => {
            if (topic.data_points) {
                count += topic.data_points.length;
            }
            if (topic.sub_topics) {
                count += this.countDataPoints(topic.sub_topics);
            }
        });
        return count;
    },

    getTopicDataPointCount(topic) {
        let count = 0;
        if (topic.data_points) {
            count += topic.data_points.length;
        }
        if (topic.sub_topics) {
            count += this.countDataPoints(topic.sub_topics);
        }
        return count;
    },

    countSearchResults() {
        return this.searchResults ? this.searchResults.length : 0;
    },

    /**
     * Add all data points from a topic (including sub-topics)
     * @param {string} topicId - The topic ID to add all fields from
     */
    handleAddAllFromTopic(topicId) {
        console.log('[SelectDataPointsPanel] Add all fields from topic:', topicId);

        // Find the topic in topicsData
        const topic = this.findTopicById(topicId);
        if (!topic) {
            console.error('[SelectDataPointsPanel] Topic not found:', topicId);
            return;
        }

        // Collect all data points from this topic and sub-topics recursively
        const allDataPoints = this.collectAllDataPoints(topic);

        console.log(`[SelectDataPointsPanel] Adding ${allDataPoints.length} fields from topic "${topic.name}"`);

        // Add each data point to selection
        let addedCount = 0;
        allDataPoints.forEach(dataPoint => {
            if (!window.AppState.isSelected(dataPoint.id)) {
                window.AppState.addSelectedDataPoint(dataPoint);
                addedCount++;
            }
        });

        console.log(`[SelectDataPointsPanel] Added ${addedCount} new fields (${allDataPoints.length - addedCount} already selected)`);

        // Update UI
        this.updateDataPointSelections();

        // Emit event
        AppEvents.emit('topic-bulk-add', {
            topicId: topicId,
            topicName: topic.name,
            totalCount: allDataPoints.length,
            addedCount: addedCount
        });
    },

    /**
     * Add all data points from a framework (in flat list view)
     * @param {string} frameworkName - The framework name to add all fields from
     */
    handleAddAllFromFramework(frameworkName) {
        console.log('[SelectDataPointsPanel] Add all fields from framework:', frameworkName);

        // Find all data points for this framework in flatListData
        const frameworkDataPoints = this.flatListData.filter(item => {
            const itemFramework = item.dataPoint.framework_name || item.topic.framework_name || 'Unknown Framework';
            return itemFramework === frameworkName;
        });

        if (frameworkDataPoints.length === 0) {
            console.warn('[SelectDataPointsPanel] No data points found for framework:', frameworkName);
            return;
        }

        console.log(`[SelectDataPointsPanel] Adding ${frameworkDataPoints.length} fields from framework "${frameworkName}"`);

        // Add each data point to selection
        let addedCount = 0;
        frameworkDataPoints.forEach(item => {
            const dataPoint = item.dataPoint;
            if (!window.AppState.isSelected(dataPoint.id)) {
                window.AppState.addSelectedDataPoint(dataPoint);
                addedCount++;
            }
        });

        console.log(`[SelectDataPointsPanel] Added ${addedCount} new fields (${frameworkDataPoints.length - addedCount} already selected)`);

        // Update UI
        this.updateDataPointSelections();

        // Emit event
        AppEvents.emit('framework-bulk-add', {
            frameworkName: frameworkName,
            totalCount: frameworkDataPoints.length,
            addedCount: addedCount
        });
    },

    /**
     * Handle individual field add button click from topic tree
     * @param {string} fieldId - The field ID to add
     */
    handleAddFieldFromTree(fieldId) {
        console.log('[SelectDataPointsPanel] Adding individual field from topic tree:', fieldId);

        // Find complete data point object
        const dataPoint = this.findDataPointById(fieldId);

        if (!dataPoint) {
            console.error('[SelectDataPointsPanel] Could not find data point for fieldId:', fieldId);
            return;
        }

        // Prepare complete field data
        const fieldData = {
            id: dataPoint.field_id || dataPoint.id || fieldId,
            field_id: dataPoint.field_id || dataPoint.id || fieldId,
            name: dataPoint.field_name || dataPoint.name,
            field_name: dataPoint.field_name || dataPoint.name,
            topic: dataPoint.topic,
            path: dataPoint.path,
            ...dataPoint  // Spread all other properties
        };

        // Add to AppState if not already selected
        if (window.AppState && !window.AppState.isSelected(fieldData.id)) {
            window.AppState.addSelectedDataPoint(fieldData);
            console.log('[SelectDataPointsPanel] Field added from topic tree:', fieldData);

            // Update UI to reflect selection
            this.updateDataPointSelections();

            // Emit event
            AppEvents.emit('data-point-add-requested', { fieldId, field: fieldData });
        } else {
            console.log('[SelectDataPointsPanel] Field already selected:', fieldId);
        }
    },

    /**
     * Find topic by ID in topicsData hierarchy
     * @param {string} topicId - The topic ID to search for
     * @returns {Object|null} The topic object if found, null otherwise
     */
    findTopicById(topicId) {
        if (!this.topicsData) return null;

        const searchTopics = (topics) => {
            for (const topic of topics) {
                // Handle both id and topic_id field names
                if (topic.id === topicId || topic.topic_id === topicId ||
                    String(topic.id) === String(topicId) || String(topic.topic_id) === String(topicId)) {
                    return topic;
                }
                if (topic.sub_topics) {
                    const found = searchTopics(topic.sub_topics);
                    if (found) return found;
                }
            }
            return null;
        };

        return searchTopics(this.topicsData);
    },

    /**
     * Collect all data points from topic and sub-topics recursively
     * @param {Object} topic - The topic to collect data points from
     * @returns {Array} Array of data point objects with complete metadata
     */
    collectAllDataPoints(topic) {
        const dataPoints = [];

        // Add data points from this topic
        if (topic.data_points && Array.isArray(topic.data_points)) {
            topic.data_points.forEach(dp => {
                dataPoints.push({
                    id: dp.field_id || dp.id,
                    field_id: dp.field_id || dp.id,
                    name: dp.field_name || dp.name,
                    field_name: dp.field_name || dp.name,
                    unit: dp.unit || dp.default_unit,
                    topic: topic,
                    path: topic.name,
                    ...dp  // Spread all other properties
                });
            });
        }

        // Recursively add from sub-topics
        if (topic.sub_topics && Array.isArray(topic.sub_topics)) {
            topic.sub_topics.forEach(subTopic => {
                const subDataPoints = this.collectAllDataPoints(subTopic);
                dataPoints.push(...subDataPoints);
            });
        }

        return dataPoints;
    },

    // Public API methods
    isReady() {
        return this.isInitialized;
    },

    getCurrentFramework() {
        return this.currentFrameworkId;
    },

    getCurrentView() {
        return this.currentView;
    },

    getSearchTerm() {
        return this.searchTerm;
    },

    refresh() {
        console.log('[SelectDataPointsPanel] Refreshing panel...');
        this.loadTopicTree(this.currentFrameworkId);
    }
};