/**
 * Frameworks Topics Module
 * Handles topic management functionality
 */

window.FrameworksTopics = (function() {
    'use strict';

    // Private variables - these will be referenced from the main file
    let topics = [];
    let customTopics = [];
    let currentFrameworkId = null;
    let topicsContainer = null;
    let topicModal = null;
    let addTopicBtn = null;
    let saveTopic = null;
    let wizardStateRef = null; // Reference to the wizardState object

    // Initialize DOM elements
    function initializeDOMElements(containerId) {
        topicsContainer = document.getElementById(containerId || 'topicsContainer');
        addTopicBtn = document.getElementById('addTopicWizard');
        saveTopic = document.getElementById('saveTopicWizard');
        
        if (document.getElementById('topicModal')) {
            topicModal = new bootstrap.Modal(document.getElementById('topicModal'));
        }
    }

    // Topic Management Functions (exact copies from original)
    function loadCustomTopics() {
        fetch('/admin/topics/custom', { credentials: 'include' })
            .then(response => response.json())
            .then(data => {
                customTopics = data;
                updateTopicDropdowns();
            })
            .catch(error => console.error('Error loading custom topics:', error));
    }

    function updateTopicDropdowns(excludeTopicId = null) {
        const parentTopicSelect = document.getElementById('parentTopic');
        const allTopicSelects = document.querySelectorAll('.topic-select');
        
        // Helper function to check if a topic should be excluded
        const shouldExcludeTopic = (topic) => {
            if (!excludeTopicId) return false;
            // Only exclude the exact topic being edited
            return topic.topic_id === excludeTopicId;
        };
        
        // Update parent topic dropdown in modal
        if (parentTopicSelect) {
            parentTopicSelect.innerHTML = '<option value="">-- Root Topic --</option>';
            const allTopics = topics.concat(customTopics);
            
            allTopics.forEach(topic => {
                const shouldExclude = shouldExcludeTopic(topic);
                if (!shouldExclude) {
                    addTopicOptionRecursive(parentTopicSelect, topic, '', excludeTopicId);
                }
            });
        }
        
        // Update topic selects in data point rows (don't exclude anything for data point assignment)
        allTopicSelects.forEach(select => {
            const currentValue = select.value;
            select.innerHTML = '<option value="">-- Select Topic --</option>';
            topics.concat(customTopics).forEach(topic => {
                addTopicOptionRecursive(select, topic, '');
            });
            select.value = currentValue;
        });
    }

    function addTopicOptionRecursive(select, topic, prefix, excludeTopicId) {
        // Skip if this topic should be excluded
        if (excludeTopicId && topic.topic_id === excludeTopicId) {
            return;
        }
        
        const option = document.createElement('option');
        option.value = topic.topic_id;
        option.textContent = prefix + topic.name;
        if (topic.is_custom) option.textContent += ' (Custom)';
        select.appendChild(option);
        
        if (topic.children) {
            topic.children.forEach(child => {
                addTopicOptionRecursive(select, child, prefix + '  ', excludeTopicId);
            });
        }
    }

    function displayTopicsTree(showCompanyTopicsOnly = false) {
        if (!topicsContainer) return;
        
        topicsContainer.innerHTML = '';
        let topicsToDisplay = [];

        if (!currentFrameworkId && wizardStateRef && wizardStateRef.formData && wizardStateRef.formData.topics) {
            // If creating a new framework, use topics from wizardState
            topicsToDisplay = wizardStateRef.formData.topics;
        } else if (showCompanyTopicsOnly) {
            topicsToDisplay = customTopics;
        } else {
            topicsToDisplay = topics.concat(customTopics);
        }

        if (topicsToDisplay.length === 0) {
            topicsContainer.innerHTML = '<p class="text-muted">No topics created yet. Click "Add Topic" to create one.</p>';
            return;
        }
        
        topicsToDisplay.forEach(topic => {
            if (!topic.parent_id) { // Only display root topics
                const topicElement = createTopicElement(topic);
                topicsContainer.appendChild(topicElement);
            }
        });
    }

    function toggleCompanyTopics(showCompanyTopicsOnly) {
        displayTopicsTree(showCompanyTopicsOnly);
    }

    function createTopicElement(topic, level = 0) {
        const div = document.createElement('div');
        div.className = 'topic-item';
        div.style.marginLeft = (level * 20) + 'px';
        
        const indent = '  '.repeat(level);
        const customBadge = topic.is_custom ? '<span class="badge bg-info">Custom</span>' : '';
        const fieldCount = topic.field_count || 0;
        
        div.innerHTML = `
            <div class="d-flex justify-content-between align-items-center p-2 border rounded mb-2">
                <div>
                    <strong>${indent}${topic.name}</strong> ${customBadge}
                    <small class="text-muted d-block">${topic.description || 'No description'}</small>
                    <small class="text-info">${fieldCount} field(s)</small>
                </div>
                <div>
                    <button class="btn btn-sm btn-outline-primary edit-topic" data-topic-id="${topic.topic_id}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-topic" data-topic-id="${topic.topic_id}" ${topic.is_custom ? 'disabled title="Company-wide topics cannot be deleted"' : ''}>
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        
        // Add children recursively
        if (topic.children) {
            topic.children.forEach(child => {
                const childElement = createTopicElement(child, level + 1);
                div.appendChild(childElement);
            });
        }
        
        return div;
    }

    function getCurrentCompanyId() {
        // This should be set from the session or user context
        return window.currentCompanyId || null;
    }

    // Helper function to recursively find a topic in the topic tree
    function findTopicRecursively(topicsList, targetId) {
        for (let topic of topicsList) {
            if (topic.topic_id === targetId) {
                return topic;
            }
            if (topic.children && topic.children.length > 0) {
                const found = findTopicRecursively(topic.children, targetId);
                if (found) {
                    return found;
                }
            }
        }
        return null;
    }

    function loadFrameworkTopics(frameworkId) {
        if (!frameworkId) return;
        
        fetch(`/admin/frameworks/${frameworkId}/topics`, { credentials: 'include' })
            .then(response => response.json())
            .then(data => {
                if (data && data.success) {
                    topics = data.topics || [];
                } else if (Array.isArray(data)) {
                    topics = data; // fallback legacy
                } else {
                    topics = [];
                }
                displayTopicsTree();
                updateTopicDropdowns();
            })
            .catch(error => console.error('Error loading framework topics:', error));
    }

    function updateDrawerTopicDropdown() {
        const topicSelect = document.getElementById('dpTopic');
        if (!topicSelect) return;
        
        topicSelect.innerHTML = '<option value="">-- Select Topic --</option>';
        
        let topicsForDropdown = [];
        if (!currentFrameworkId && wizardStateRef && wizardStateRef.formData && wizardStateRef.formData.topics) {
            topicsForDropdown = wizardStateRef.formData.topics;
        } else {
            topicsForDropdown = topics.concat(customTopics);
        }

        topicsForDropdown.forEach(topic => {
            addTopicOptionRecursive(topicSelect, topic, '');
        });
    }

    function deleteTopic(topicId) {
        // If in new framework creation mode, delete from wizardState
        if (!currentFrameworkId && wizardStateRef && wizardStateRef.formData && wizardStateRef.formData.topics) {
            wizardStateRef.formData.topics = wizardStateRef.formData.topics.filter(topic => topic.topic_id !== topicId);
            displayTopicsTree();
            updateTopicDropdowns();
            alert('Topic deleted from framework wizard.');
            return;
        }

        // If framework_id exists, delete from backend
        if (currentFrameworkId) {
            fetch(`/admin/frameworks/${currentFrameworkId}/topics/${topicId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    loadFrameworkTopics(currentFrameworkId);
                    loadCustomTopics();
                    alert('Topic deleted successfully!');
                }
            })
            .catch(error => {
                alert('Error deleting topic');
            });
        } else {
            alert('Cannot delete topic: Framework ID is missing.');
        }
    }

    // Setup event listeners
    function setupEventListeners() {
        // Add Topic & Topic-Modal handlers (only if elements exist on the page)
        if (addTopicBtn && topicModal && saveTopic) {
            // Open Topic modal
            addTopicBtn.addEventListener('click', function() {
                // Update dropdown options when opening modal for new topic
                updateTopicDropdowns();
                topicModal.show();
            });

            // Clear editing state when modal is hidden
            document.getElementById('topicModal').addEventListener('hidden.bs.modal', function() {
                // Reset editing state
                topicModal._editingTopicId = null;
                // Reset dropdown to include all topics again
                updateTopicDropdowns();
                // Clear form
                document.getElementById('topicForm').reset();
            });

            // Save Topic inside modal
            saveTopic.addEventListener('click', async function() {
                const isCustomTopicElement = document.getElementById('isCustomTopic');
                const isCustomTopic = isCustomTopicElement ? isCustomTopicElement.checked : false;
                
                const formData = {
                    name: document.getElementById('topicName').value,
                    description: document.getElementById('topicDescription').value,
                    parent_id: document.getElementById('parentTopic').value || null,
                    framework_id: isCustomTopic ? null : currentFrameworkId,
                    company_id: isCustomTopic ? getCurrentCompanyId() : null
                };

                // If editing existing topic, send PUT
                const editingId = topicModal._editingTopicId;
                const method = editingId ? 'PUT' : 'POST';
                const endpoint = editingId ? `/admin/topics/${editingId}` : '/admin/topics';

                // Validation remains

                fetch(endpoint, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Error: ' + data.error);
                    } else {
                        topicModal.hide();
                        document.getElementById('topicForm').reset();
                        topicModal._editingTopicId = null;
                        if (formData.company_id) {
                            loadCustomTopics();
                        } else {
                            loadFrameworkTopics(currentFrameworkId);
                        }
                    }
                })
                .catch(error => {
                    console.error('Error saving topic:', error);
                    alert('Error saving topic');
                });
                return;
            });
        }

        // Event delegation for topic and dependency management
        document.addEventListener('click', function(e) {
            const delBtn = e.target.closest('.delete-topic');
            if (delBtn) {
                const topicId = delBtn.getAttribute('data-topic-id');
                if (confirm('Are you sure you want to delete this topic?')) {
                    deleteTopic(topicId);
                }
                return;
            }
            const editBtn = e.target.closest('.edit-topic');
            if (editBtn) {
                const topicId = editBtn.getAttribute('data-topic-id');
                
                const topic = findTopicRecursively(topics.concat(customTopics), topicId);
                
                // Try to find parent_id from the nested structure
                let parentId = topic?.parent_id;
                if (!parentId && topic) {
                    // Try to find the parent by looking for which topic contains this as a child
                    const allTopics = topics.concat(customTopics);
                    for (let potentialParent of allTopics) {
                        if (potentialParent.children && potentialParent.children.some(child => child.topic_id === topicId)) {
                            parentId = potentialParent.topic_id;
                            break;
                        }
                    }
                }
                
                if (topic && topicModal && document.getElementById('topicName')) {
                    // Update dropdown options first, excluding the current topic to prevent circular dependencies
                    updateTopicDropdowns(topicId);
                    
                    // Prefill modal fields
                    document.getElementById('topicName').value = topic.name;
                    document.getElementById('topicDescription').value = topic.description || '';
                    
                    // Set parent topic with improved logic
                    const parentTopicSelect = document.getElementById('parentTopic');
                    
                    if (parentTopicSelect && parentId) {
                        // Give the DOM a moment to update the dropdown options
                        setTimeout(() => {
                            parentTopicSelect.value = parentId;
                            
                            // If that didn't work, try to find the option manually
                            if (parentTopicSelect.value !== parentId) {
                                const parentOption = Array.from(parentTopicSelect.options).find(opt => opt.value === parentId);
                                if (parentOption) {
                                    parentTopicSelect.value = parentId;
                                }
                            }
                        }, 50);
                    } else if (parentTopicSelect) {
                        parentTopicSelect.value = '';
                    }
                    
                    const isCustomCheckbox = document.getElementById('isCustomTopic');
                    if (isCustomCheckbox) {
                        isCustomCheckbox.checked = topic.is_custom || false;
                    }
                    // Store editing state
                    topicModal._editingTopicId = topicId;
                    topicModal.show();
                }
                return;
            }
        });
    }

    // Public API
    return {
        initialize: function(frameworkId, containerId, wizardState) {
            currentFrameworkId = frameworkId;
            initializeDOMElements(containerId);
            setupEventListeners();
            loadCustomTopics();
            if (currentFrameworkId) {
                loadFrameworkTopics(currentFrameworkId);
            }
            wizardStateRef = wizardState; // Store the wizardState reference
        },
        
        // Core functions
        loadCustomTopics: loadCustomTopics,
        updateTopicDropdowns: updateTopicDropdowns,
        addTopicOptionRecursive: addTopicOptionRecursive,
        displayTopicsTree: displayTopicsTree,
        createTopicElement: createTopicElement,
        loadFrameworkTopics: loadFrameworkTopics,
        updateDrawerTopicDropdown: updateDrawerTopicDropdown,
        deleteTopic: deleteTopic,
        toggleCompanyTopics: toggleCompanyTopics,
        findTopicRecursively: findTopicRecursively,
        
        // Getters/Setters
        setTopics: function(newTopics) {
            topics = newTopics;
        },
        
        setCustomTopics: function(newCustomTopics) {
            customTopics = newCustomTopics;
        },
        
        getTopics: function() {
            return topics;
        },
        
        getCustomTopics: function() {
            return customTopics;
        },

        /**
         * Update framework ID after it becomes available (wizard step 1)
         */
        setFrameworkId: function(fid) {
            currentFrameworkId = fid;
            // Re-display tree/dropdowns now that backend saving will work
            displayTopicsTree();
            updateTopicDropdowns();
        },

        getAllTopics: function() {
            // If a framework ID is available, topics should always be fetched from the backend
            // The `topics` array is kept in sync by `loadFrameworkTopics`
            if (currentFrameworkId) {
                return topics;
            } else if (wizardStateRef && wizardStateRef.formData && wizardStateRef.formData.topics) {
                // If in wizard context but no framework ID yet (i.e., before initial save),
                // use the temporary topics from wizardStateRef.
                return wizardStateRef.formData.topics;
            } else {
                // Fallback for other contexts or if no wizard state
                return topics.concat(customTopics);
            }
        },

        /**
         * Refresh topics display
         */
        refresh: function() {
            if (currentFrameworkId) {
                loadFrameworkTopics(currentFrameworkId);
            }
            loadCustomTopics();
        },

        /**
         * Check if module is ready
         */
        isReady: function() {
            return true; // Topics module is ready when initialized
        }
    };
})(); 