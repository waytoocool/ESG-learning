/**
 * Frameworks UI Utilities Module
 * Handles UI utilities like scroll buttons, field filtering, and activity loading
 */

window.FrameworksUIUtils = (function() {
    'use strict';

    // Scroll button management (exact copy from original)
    function updateScrollButtons() {
        const cardDeck = document.getElementById('frameworkCardDeck');
        const scrollLeftBtn = document.getElementById('scrollLeft');
        const scrollRightBtn = document.getElementById('scrollRight');
        
        if (cardDeck && scrollLeftBtn && scrollRightBtn) {
            scrollLeftBtn.disabled = cardDeck.scrollLeft === 0;
            scrollRightBtn.disabled = 
                cardDeck.scrollLeft + cardDeck.clientWidth >= cardDeck.scrollWidth;
        }
    }

    function setupScrollButtons() {
        const cardDeck = document.getElementById('frameworkCardDeck');
        const scrollLeftBtn = document.getElementById('scrollLeft');
        const scrollRightBtn = document.getElementById('scrollRight');
        
        if (cardDeck && scrollLeftBtn && scrollRightBtn) {
            scrollLeftBtn.addEventListener('click', function() {
                cardDeck.scrollBy({
                    left: -cardDeck.clientWidth,
                    behavior: 'smooth'
                });
            });

            scrollRightBtn.addEventListener('click', function() {
                cardDeck.scrollBy({
                    left: cardDeck.clientWidth,
                    behavior: 'smooth'
                });
            });

            // Initial button state
            updateScrollButtons();

            // Update scroll buttons on scroll and resize
            cardDeck.addEventListener('scroll', updateScrollButtons);
            window.addEventListener('resize', updateScrollButtons);
        }
    }

    // Filter fields by data status (exact copy from original)
    function filterFieldsByDataStatus(filterId) {
        const rows = document.querySelectorAll('#modalFieldsList .field-row');
        
        rows.forEach(row => {
            const hasData = row.getAttribute('data-has-data') === 'true';
            let shouldShow = true;
            
            switch(filterId) {
                case 'withDataFields':
                    shouldShow = hasData;
                    break;
                case 'missingDataFields':
                    shouldShow = !hasData;
                    break;
                case 'allFields':
                default:
                    shouldShow = true;
                    break;
            }
            
            row.style.display = shouldShow ? '' : 'none';
        });
    }

    // Load recent activity (exact copy from original)
    function loadRecentActivity() {
        fetch('/admin/frameworks/recent_activity')
            .then(response => response.json())
            .then(data => {
                const activityList = document.getElementById('recentActivityList');
                if (activityList) {
                    activityList.innerHTML = ''; // Clear existing
                    if (data.success && data.activities.length > 0) {
                        data.activities.forEach(activity => {
                            const listItem = document.createElement('li');
                            listItem.className = 'list-group-item';
                            const activityDate = new Date(activity.date).toLocaleString();
                            listItem.innerHTML = `<strong>${activity.type}:</strong> ${activity.name} <span class="text-muted float-end">${activityDate}</span>`;
                            activityList.appendChild(listItem);
                        });
                    } else {
                        activityList.innerHTML = '<li class="list-group-item text-muted">No recent activity to display.</li>';
                    }
                }
            })
            .catch(error => console.error('Error loading recent activity:', error));
    }

    // Template preview function (exact copy from original)
    function previewTemplate(templateKey) {
        fetch(`/admin/import_templates/${templateKey}/preview`)
            .then(response => response.json())
            .then(data => {
                if (!data.success || !data.preview) {
                    throw new Error('Failed to load template preview');
                }
                
                const preview = data.preview;
                
                // Switch to preview step
                document.getElementById('templateSelectionStep').classList.add('d-none');
                document.getElementById('templatePreviewStep').classList.remove('d-none');
                
                // Update buttons
                document.getElementById('previewTemplateBtn').style.display = 'none';
                document.getElementById('backToTemplatesBtn').style.display = 'inline-block';
                document.getElementById('confirmImportBtn').style.display = 'inline-block';
                
                // Store template key for import
                document.getElementById('confirmImportBtn').setAttribute('data-template-key', templateKey);
                
                // Set template name
                document.getElementById('templateFrameworkName').value = preview.template_name;
                
                // Update summary
                const summary = document.getElementById('importSummary');
                summary.innerHTML = `
                    <div class="small">
                        <div><strong>New Fields:</strong> ${preview.new_field_count}</div>
                        <div><strong>Duplicate Fields:</strong> ${preview.duplicate_field_count}</div>
                        <div><strong>Total Fields:</strong> ${preview.total_template_fields}</div>
                    </div>
                `;
                
                // Update badges
                document.getElementById('newFieldsBadge').textContent = preview.new_field_count;
                document.getElementById('duplicateFieldsBadge').textContent = preview.duplicate_field_count;
                
                // Populate new fields
                const newFieldsList = document.getElementById('newFieldsList');
                newFieldsList.innerHTML = '';
                preview.new_fields.forEach(field => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td><input type="checkbox" class="field-select" data-field-code="${field.field_code}" checked></td>
                        <td>${field.field_name}</td>
                        <td><code>${field.field_code}</code></td>
                        <td>${field.topic_path || 'Uncategorised'}</td>
                        <td>${field.default_unit || '-'}</td>
                        <td><span class="badge bg-secondary">${field.value_type}</span></td>
                    `;
                    newFieldsList.appendChild(row);
                });
                
                // Populate duplicates
                const duplicatesList = document.getElementById('duplicateFieldsList');
                duplicatesList.innerHTML = '';
                preview.duplicate_fields.forEach(field => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${field.field_name}</td>
                        <td><code>${field.field_code}</code></td>
                        <td>${field.topic_path || 'Uncategorised'}</td>
                        <td><span class="badge bg-warning">Already exists</span></td>
                    `;
                    duplicatesList.appendChild(row);
                });
            })
            .catch(error => {
                alert('Error loading template preview');
            });
    }

    // Public API
    return {
        initialize: function() {
            console.log('FrameworksUIUtils: Initializing...');
            setupScrollButtons();
            
            // Load recent activity on page load
            loadRecentActivity();
            
            // Setup field filter event listeners
            const filterButtons = document.querySelectorAll('input[name="fieldFilter"]');
            filterButtons.forEach(button => {
                button.addEventListener('change', function() {
                    filterFieldsByDataStatus(this.id);
                });
            });
        },
        
        // Core functions
        updateScrollButtons: updateScrollButtons,
        setupScrollButtons: setupScrollButtons,
        filterFieldsByDataStatus: filterFieldsByDataStatus,
        loadRecentActivity: loadRecentActivity,
        previewTemplate: previewTemplate,
        
        refresh: function() {
            updateScrollButtons();
            loadRecentActivity();
        },
        
        isReady: function() {
            return true;
        }
    };
})(); 