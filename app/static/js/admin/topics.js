/**
 * Topic Management JavaScript
 * Handles standalone topic management functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let topics = [];
    let currentEditingTopicId = null;
    
    // DOM elements
    const createTopicBtn = document.getElementById('createTopicBtn');
    const refreshTopicsBtn = document.getElementById('refreshTopicsBtn');
    const topicTreeContainer = document.getElementById('topicTreeContainer');
    const topicModal = new bootstrap.Modal(document.getElementById('topicModal'));
    const topicUsageModal = new bootstrap.Modal(document.getElementById('topicUsageModal'));
    const deleteConfirmModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
    const saveTopicBtn = document.getElementById('saveTopicBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    
    // Initialize page
    init();
    
    function init() {
        loadTopics();
        setupEventListeners();
    }
    
    function setupEventListeners() {
        // Create topic button
        createTopicBtn.addEventListener('click', function() {
            openCreateTopicModal();
        });
        
        // Refresh topics button
        refreshTopicsBtn.addEventListener('click', function() {
            loadTopics();
        });
        
        // Save topic button
        saveTopicBtn.addEventListener('click', function() {
            saveTopic();
        });
        
        // Confirm delete button
        confirmDeleteBtn.addEventListener('click', function() {
            deleteTopic();
        });
        
        // Event delegation for topic actions
        topicTreeContainer.addEventListener('click', function(e) {
            const topicId = e.target.closest('[data-topic-id]')?.getAttribute('data-topic-id');
            
            if (e.target.classList.contains('edit-topic-btn')) {
                editTopic(topicId);
            } else if (e.target.classList.contains('delete-topic-btn')) {
                confirmDeleteTopic(topicId);
            } else if (e.target.classList.contains('view-usage-btn')) {
                console.log('View Usage button clicked for topicId:', topicId);
                viewTopicUsage(topicId);
            } else if (e.target.classList.contains('add-child-btn')) {
                openCreateTopicModal(topicId);
            }
        });
    }
    
    function loadTopics() {
        showLoading();
        
        fetch('/admin/topics/custom')
            .then(response => response.json())
            .then(data => {
                topics = data;
                renderTopics();
                updateStatistics();
            })
            .catch(error => {
                console.error('Error loading topics:', error);
                showError('Failed to load topics');
            })
            .finally(() => {
                hideLoading();
            });
    }
    
    function renderTopics() {
        if (topics.length === 0) {
            topicTreeContainer.innerHTML = `
                <div class="empty-state">
                    <div class="icon">
                        <i class="fas fa-tags"></i>
                    </div>
                    <h5>No Topics Created Yet</h5>
                    <p>Create your first topic to organize your data fields into meaningful categories.</p>
                    <button type="button" class="btn btn-primary" onclick="document.getElementById('createTopicBtn').click()">
                        <i class="fas fa-plus"></i> Create First Topic
                    </button>
                </div>
            `;
            return;
        }
        
        const topicTree = buildTopicTree(topics);
        topicTreeContainer.innerHTML = topicTree;
    }
    
    function buildTopicTree(topicList, parentId = null, level = 0) {
        let html = '';
        
        const filteredTopics = topicList.filter(topic => topic.parent_id === parentId);
        
        filteredTopics.forEach(topic => {
            const hasChildren = topicList.some(t => t.parent_id === topic.topic_id);
            const fieldCount = topic.field_count || 0;
            const frameworkCount = topic.framework_count || 0;
            
            html += `
                <div class="topic-item" data-topic-id="${topic.topic_id}" style="margin-left: ${level * 20}px;">
                    <div class="topic-card">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <div class="topic-title">
                                    ${'  '.repeat(level)}${topic.name}
                                    ${hasChildren ? '<i class="fas fa-sitemap text-muted ms-2"></i>' : ''}
                                </div>
                                <div class="topic-description">
                                    ${topic.description || 'No description provided'}
                                </div>
                                <div class="topic-meta">
                                    <span class="topic-badge bg-info text-white">
                                        <i class="fas fa-layer-group"></i> Level ${topic.level || 0}
                                    </span>
                                    <span class="topic-badge ${fieldCount > 0 ? 'bg-success' : 'bg-secondary'} text-white">
                                        <i class="fas fa-database"></i> ${fieldCount} Fields
                                    </span>
                                    <span class="topic-badge ${frameworkCount > 0 ? 'bg-primary' : 'bg-secondary'} text-white">
                                        <i class="fas fa-project-diagram"></i> ${frameworkCount} Frameworks
                                    </span>
                                    <span class="topic-badge bg-warning text-dark">
                                        <i class="fas fa-building"></i> Company-wide
                                    </span>
                                </div>
                            </div>
                            <div class="topic-actions">
                                <button type="button" class="btn btn-sm btn-outline-success add-child-btn" 
                                        title="Add Child Topic">
                                    <i class="fas fa-plus"></i>
                                </button>
                                <button type="button" class="btn btn-sm btn-outline-info view-usage-btn"
                                        title="View Usage">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button type="button" class="btn btn-sm btn-outline-primary edit-topic-btn"
                                        title="Edit Topic">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button type="button" class="btn btn-sm btn-outline-danger delete-topic-btn"
                                        title="Delete Topic"
                                        ${fieldCount > 0 || hasChildren ? 'disabled' : ''}>
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Add children recursively
            if (hasChildren) {
                html += buildTopicTree(topicList, topic.topic_id, level + 1);
            }
        });
        
        return html;
    }
    
    function updateStatistics() {
        const totalTopics = topics.length;
        const rootTopics = topics.filter(t => !t.parent_id).length;
        const usedTopics = topics.filter(t => t.field_count && t.field_count > 0).length;
        const frameworksWithTopics = new Set(topics.filter(t => t.framework_count && t.framework_count > 0).map(t => t.framework_id)).size;
        
        document.getElementById('totalTopicsCount').textContent = totalTopics;
        document.getElementById('rootTopicsCount').textContent = rootTopics;
        document.getElementById('usedTopicsCount').textContent = usedTopics;
        document.getElementById('frameworksUsingTopicsCount').textContent = frameworksWithTopics;
    }
    
    function openCreateTopicModal(parentId = null) {
        currentEditingTopicId = null;
        
        // Reset form
        document.getElementById('topicForm').reset();
        document.getElementById('topicModalLabel').textContent = parentId ? 'Create Child Topic' : 'Create Topic';
        
        // Update parent dropdown
        updateParentTopicDropdown(parentId);
        
        if (parentId) {
            document.getElementById('parentTopic').value = parentId;
        }
        
        topicModal.show();
    }
    
    function editTopic(topicId) {
        const topic = topics.find(t => t.topic_id === topicId);
        if (!topic) return;
        
        currentEditingTopicId = topicId;
        
        // Populate form
        document.getElementById('topicId').value = topic.topic_id;
        document.getElementById('topicName').value = topic.name;
        document.getElementById('topicDescription').value = topic.description || '';
        document.getElementById('topicModalLabel').textContent = 'Edit Topic';
        
        // Update parent dropdown
        updateParentTopicDropdown(topic.parent_id, topicId);
        document.getElementById('parentTopic').value = topic.parent_id || '';
        
        topicModal.show();
    }
    
    function updateParentTopicDropdown(selectedId = null, excludeId = null) {
        const parentSelect = document.getElementById('parentTopic');
        parentSelect.innerHTML = '<option value="">-- Root Topic --</option>';
        
        function addTopicOptions(topicList, parentId = null, prefix = '') {
            const filteredTopics = topicList.filter(t => 
                t.parent_id === parentId && 
                t.topic_id !== excludeId
            );
            
            filteredTopics.forEach(topic => {
                const option = document.createElement('option');
                option.value = topic.topic_id;
                option.textContent = prefix + topic.name;
                if (topic.topic_id === selectedId) {
                    option.selected = true;
                }
                parentSelect.appendChild(option);
                
                // Add children recursively
                addTopicOptions(topicList, topic.topic_id, prefix + '  ');
            });
        }
        
        addTopicOptions(topics);
    }
    
    function saveTopic() {
        const formData = new FormData(document.getElementById('topicForm'));
        const topicData = {
            name: formData.get('name'),
            description: formData.get('description'),
            parent_id: formData.get('parent_id') || null,
            company_id: getCurrentCompanyId() // Always create as company-wide topic
        };
        
        if (!topicData.name) {
            showError('Topic name is required');
            return;
        }
        
        showLoading();
        
        const url = currentEditingTopicId ? 
            `/admin/topics/${currentEditingTopicId}` : 
            '/admin/topics';
        const method = currentEditingTopicId ? 'PUT' : 'POST';
        
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(topicData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
            } else {
                topicModal.hide();
                loadTopics();
                showSuccess(currentEditingTopicId ? 'Topic updated successfully' : 'Topic created successfully');
            }
        })
        .catch(error => {
            console.error('Error saving topic:', error);
            showError('Failed to save topic');
        })
        .finally(() => {
            hideLoading();
        });
    }
    
    function confirmDeleteTopic(topicId) {
        const topic = topics.find(t => t.topic_id === topicId);
        if (!topic) return;
        
        document.getElementById('deleteTopicName').textContent = topic.name;
        
        // Check for warnings
        const warnings = [];
        const hasChildren = topics.some(t => t.parent_id === topicId);
        const fieldCount = topic.field_count || 0;
        
        if (hasChildren) {
            warnings.push('This topic has child topics that must be deleted first.');
        }
        if (fieldCount > 0) {
            warnings.push(`This topic is used by ${fieldCount} field(s). Reassign fields before deletion.`);
        }
        
        const warningsContainer = document.getElementById('deleteWarnings');
        if (warnings.length > 0) {
            warningsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <ul class="mb-0">
                        ${warnings.map(w => `<li>${w}</li>`).join('')}
                    </ul>
                </div>
            `;
            document.getElementById('confirmDeleteBtn').disabled = true;
        } else {
            warningsContainer.innerHTML = '';
            document.getElementById('confirmDeleteBtn').disabled = false;
        }
        
        confirmDeleteBtn.setAttribute('data-topic-id', topicId);
        deleteConfirmModal.show();
    }
    
    function deleteTopic() {
        const topicId = confirmDeleteBtn.getAttribute('data-topic-id');
        if (!topicId) return;
        
        showLoading();
        
        fetch(`/admin/topics/${topicId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
            } else {
                deleteConfirmModal.hide();
                loadTopics();
                showSuccess('Topic deleted successfully');
            }
        })
        .catch(error => {
            console.error('Error deleting topic:', error);
            showError('Failed to delete topic');
        })
        .finally(() => {
            hideLoading();
        });
    }
    
    function viewTopicUsage(topicId) {
        const topic = topics.find(t => t.topic_id === topicId);
        if (!topic) return;
        
        showLoading();
        console.log(`Fetching usage data for topic ID: ${topicId}`);
        fetch(`/admin/topics/${topicId}/usage`)
            .then(response => response.json())
            .then(data => {
                renderTopicUsage(topic, data);
                topicUsageModal.show();
            })
            .catch(error => {
                console.error('Error loading topic usage:', error);
                showError('Failed to load topic usage');
            })
            .finally(() => {
                hideLoading();
            });
    }
    
    function renderTopicUsage(topic, usageData) {
        const modalTitle = document.getElementById('topicUsageModalLabel');
        modalTitle.textContent = `Usage: ${topic.name}`;
        
        const content = document.getElementById('topicUsageContent');
        
        if (!usageData.frameworks || usageData.frameworks.length === 0) {
            content.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-info-circle fa-3x text-muted mb-3"></i>
                    <h5>Not Used Yet</h5>
                    <p class="text-muted">This topic is not currently used by any frameworks or fields.</p>
                </div>
            `;
            return;
        }
        
        let html = `
            <div class="mb-3">
                <h6><i class="fas fa-chart-bar"></i> Usage Summary</h6>
                <div class="row">
                    <div class="col-md-6">
                        <div class="text-center p-3 bg-light rounded">
                            <div class="h4 text-primary mb-1">${usageData.frameworks.length}</div>
                            <div class="text-muted">Frameworks</div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="text-center p-3 bg-light rounded">
                            <div class="h4 text-success mb-1">${usageData.total_fields || 0}</div>
                            <div class="text-muted">Total Fields</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <h6><i class="fas fa-project-diagram"></i> Frameworks Using This Topic</h6>
            <div class="framework-list">
        `;
        
        usageData.frameworks.forEach(framework => {
            html += `
                <div class="framework-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${framework.framework_name}</strong>
                            <div class="text-muted small">${framework.description || 'No description'}</div>
                        </div>
                        <span class="badge bg-primary">${framework.field_count} fields</span>
                    </div>
                    ${framework.fields && framework.fields.length > 0 ? `
                        <div class="field-list">
                            <small class="text-muted">Fields:</small>
                            ${framework.fields.map(field => `
                                <div class="field-item">• ${field.field_name} (${field.field_code})</div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
        });
        
        html += '</div>';
        content.innerHTML = html;
    }
    
    // Utility functions
    function getCurrentCompanyId() {
        // This should be set from the session or user context
        return window.currentCompanyId || null;
    }
    
    function showLoading() {
        // Add loading state to buttons
        const buttons = [createTopicBtn, refreshTopicsBtn, saveTopicBtn];
        buttons.forEach(btn => {
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            }
        });
    }
    
    function hideLoading() {
        // Reset button states
        if (createTopicBtn) {
            createTopicBtn.disabled = false;
            createTopicBtn.innerHTML = '<i class="fas fa-plus"></i> Create Topic';
        }
        if (refreshTopicsBtn) {
            refreshTopicsBtn.disabled = false;
            refreshTopicsBtn.innerHTML = '<i class="fas fa-sync"></i> Refresh';
        }
        if (saveTopicBtn) {
            saveTopicBtn.disabled = false;
            saveTopicBtn.innerHTML = '<i class="fas fa-save"></i> Save Topic';
        }
    }
    
    function showError(message) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-danger border-0 position-fixed';
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-exclamation-circle me-2"></i> ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        document.body.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            document.body.removeChild(toast);
        });
    }
    
    function showSuccess(message) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-success border-0 position-fixed';
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-check-circle me-2"></i> ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        document.body.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            document.body.removeChild(toast);
        });
    }
}); 