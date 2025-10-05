/**
 * Frameworks Main Module
 * Handles core framework functionality like display, filtering, and coverage
 */

window.FrameworksMain = (function() {
    'use strict';

    // Private variables
    let currentTypeFilter = 'all';
    let filterAll = null;
    let filterGlobal = null;
    let filterCompany = null;

    // Initialize DOM elements
    function initializeDOMElements() {
        filterAll = document.getElementById('filterAll');
        filterGlobal = document.getElementById('filterGlobal');
        filterCompany = document.getElementById('filterCompany');
    }

    // Main Framework Functions (exact copies from original)
    function initializeFrameworkCards() {
        const frameworkCards = document.querySelectorAll('.framework-card');
        
        frameworkCards.forEach((card, index) => {
            const frameworkId = card.getAttribute('data-framework-id');
            if (frameworkId) {
                loadFrameworkCoverage(frameworkId, card);
            }
        });
        // Removed filterAndSortFrameworks call to prevent lexical declaration error
    }

    function loadFrameworkCoverage(frameworkId, cardElement) {
        fetch(`/admin/frameworks/coverage/${frameworkId}`, { credentials: 'include' })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                updateCoverageDisplay(cardElement, data);
                // Removed filterAndSortFrameworks call to prevent lexical declaration error
            })
            .catch(error => {
                const coverageText = cardElement.querySelector('.coverage-text');
                if (coverageText) {
                    coverageText.textContent = 'Coverage data unavailable';
                }
            });
    }

    function updateCoverageDisplay(cardElement, coverageData) {
        const progressBar = cardElement.querySelector('.coverage-progress');
        const coverageText = cardElement.querySelector('.coverage-text');
        
        if (progressBar && coverageText) {
            const percentage = coverageData.coverage_percentage || 0;
            
            // Update progress bar
            progressBar.style.width = `${percentage}%`;
            progressBar.setAttribute('aria-valuenow', percentage);
            
            // Update coverage class based on percentage
            progressBar.className = 'progress-bar';
            if (percentage >= 80) {
                progressBar.classList.add('bg-success');
            } else if (percentage >= 50) {
                progressBar.classList.add('bg-warning');
            } else {
                progressBar.classList.add('bg-danger');
            }
            
            // Update text
            const fieldsWithData = coverageData.fields_with_data || 0;
            const totalFields = coverageData.total_fields || 0;
            const lastUpdate = coverageData.last_updated ? new Date(coverageData.last_updated).toLocaleDateString() : 'Never';
            
            coverageText.innerHTML = `
                ${fieldsWithData}/${totalFields} fields (${percentage.toFixed(1)}%)
                <br><span class="text-muted">Last update: ${lastUpdate}</span>
            `;
        }
    }

    function loadFrameworkDetails(frameworkId) {
        console.log('Loading framework details for:', frameworkId);
        
        const detailsUrl = `/admin/frameworks/${frameworkId}/details`;
        const coverageUrl = `/admin/frameworks/coverage/${frameworkId}`;
        
        console.log('API URLs:', { detailsUrl, coverageUrl });
        
        // Show loading state in modal
        document.getElementById('frameworkModalBody').innerHTML = `
            <div class="text-center p-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading framework details...</p>
            </div>
        `;
        
        Promise.all([
            fetch(detailsUrl, { credentials: 'include' }).then(r => {
                console.log('Details response status:', r.status, r.statusText);
                return r.text().then(text => {
                    console.log('Details response text:', text);
                    try {
                        const json = JSON.parse(text);
                        console.log('Details response JSON:', json);
                        return json;
                    } catch (e) {
                        console.error('Failed to parse details JSON:', e);
                        throw new Error('Invalid JSON response for details: ' + text);
                    }
                });
            }),
            fetch(coverageUrl, { credentials: 'include' }).then(r => {
                console.log('Coverage response status:', r.status, r.statusText);
                return r.text().then(text => {
                    console.log('Coverage response text:', text);
                    try {
                        const json = JSON.parse(text);
                        console.log('Coverage response JSON:', json);
                        return json;
                    } catch (e) {
                        console.error('Failed to parse coverage JSON:', e);
                        throw new Error('Invalid JSON response for coverage: ' + text);
                    }
                });
            })
        ])
        .then(([detailsResponse, coverageResponse]) => {
            console.log('Both responses received:', { detailsResponse, coverageResponse });
            
            if (detailsResponse.success && coverageResponse.success) {
                console.log('Both responses successful, displaying details...');
                displayFrameworkDetailsWithCoverage(detailsResponse, coverageResponse);
            } else {
                console.error('API responses not successful:', {
                    detailsSuccess: detailsResponse.success,
                    coverageSuccess: coverageResponse.success,
                    detailsError: detailsResponse.error,
                    coverageError: coverageResponse.error
                });
                document.getElementById('frameworkModalBody').innerHTML = 
                    '<div class="alert alert-danger">Error loading framework details: ' + 
                    (detailsResponse.error || coverageResponse.error || 'Unknown error') + '</div>';
            }
        })
        .catch(error => {
            console.error('Error in loadFrameworkDetails:', error);
            document.getElementById('frameworkModalBody').innerHTML = 
                '<div class="alert alert-danger">Error loading framework details: ' + error.message + '</div>';
        });
    }

    function displayFrameworkDetailsWithCoverage(details, coverage) {
        const modalTitle = document.getElementById('frameworkModalTitle');
        const modalBody = document.getElementById('frameworkModalBody');

        modalTitle.textContent = details.framework_name;
        
        // Create coverage summary
        const coveragePercentage = coverage.coverage_percentage || 0;
        const fieldsWithData = coverage.fields_with_data || 0;
        const totalFields = coverage.total_fields || 0;
        
        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-8">
                    <h6>Description</h6>
                    <p class="text-muted">${details.description || 'No description provided.'}</p>
                    
                    <h6>Framework Statistics</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="stat-card p-3 bg-light rounded mb-3">
                                <h5 class="text-primary">${details.total_fields || 0}</h5>
                                <small class="text-muted">Total Fields</small>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="stat-card p-3 bg-light rounded mb-3">
                                <h5 class="text-info">${details.computed_fields || 0}</h5>
                                <small class="text-muted">Computed Fields</small>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="coverage-dashboard p-3 bg-light rounded">
                        <h6 class="mb-3">Data Coverage</h6>
                        <div class="text-center mb-3">
                            <div class="coverage-circle" style="background: conic-gradient(var(--bs-success) ${coveragePercentage * 3.6}deg, var(--bs-light) 0deg); width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                                <div style="background: white; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                    <strong>${coveragePercentage.toFixed(0)}%</strong>
                                </div>
                            </div>
                        </div>
                        <div class="coverage-details">
                            <div class="d-flex justify-content-between mb-2">
                                <span>Fields with data:</span>
                                <strong>${fieldsWithData}</strong>
                            </div>
                            <div class="d-flex justify-content-between mb-2">
                                <span>Total fields:</span>
                                <strong>${totalFields}</strong>
                            </div>
                            <div class="d-flex justify-content-between mb-2">
                                <span>Missing data:</span>
                                <strong class="text-danger">${totalFields - fieldsWithData}</strong>
                            </div>
                            <hr>
                            <small class="text-muted">
                                Last updated: ${coverage.last_updated ? new Date(coverage.last_updated).toLocaleString() : 'Never'}
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add data points table if available
        if (details.data_points && details.data_points.length > 0) {
            modalBody.innerHTML += `
                <div class="mt-4">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h6>Data Points</h6>
                        <div class="btn-group btn-group-sm" role="group">
                            <input type="radio" class="btn-check" name="fieldFilter" id="allFields" autocomplete="off" checked>
                            <label class="btn btn-outline-secondary" for="allFields">All</label>
                            
                            <input type="radio" class="btn-check" name="fieldFilter" id="withDataFields" autocomplete="off">
                            <label class="btn btn-outline-success" for="withDataFields">With Data</label>
                            
                            <input type="radio" class="btn-check" name="fieldFilter" id="missingDataFields" autocomplete="off">
                            <label class="btn btn-outline-danger" for="missingDataFields">Missing Data</label>
                        </div>
                    </div>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Field Name</th>
                                    <th>Code</th>
                                    <th>Type</th>
                                    <th>Unit</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${details.data_points.map(dp => `
                                    <tr class="field-row" data-has-data="${dp.has_data}">
                                        <td>${dp.field_name}</td>
                                        <td><code>${dp.field_code}</code></td>
                                        <td>${dp.value_type}</td>
                                        <td>${dp.default_unit || '-'}</td>
                                        <td>
                                            <span class="badge ${dp.has_data ? 'bg-success' : 'bg-danger'}">
                                                ${dp.has_data ? 'Has Data' : 'No Data'}
                                            </span>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }
    }

    function filterAndSortFrameworks() {
        // Ensure required DOM elements are available
        const deck = document.getElementById('frameworkCardDeck');
        if (!deck) return;

        // Use document.getElementById directly to avoid lexical declaration issues
        const searchElement = document.getElementById('frameworkSearch');
        const sortElement = document.getElementById('frameworkSort');
        
        const searchTerm = (searchElement && searchElement.value) ? searchElement.value.trim().toLowerCase() : '';
        const sortValue = sortElement ? sortElement.value : 'name_asc';

        // Collect all cards
        const allCards = Array.from(deck.querySelectorAll('.framework-card'));

        // Helper to determine if a card should be visible based on current filters
        const isVisible = (card) => {
            // Type filter (global / company) - use default 'all' if currentTypeFilter not yet initialized
            const typeFilter = (typeof currentTypeFilter !== 'undefined') ? currentTypeFilter : 'all';
            const isGlobal = card.getAttribute('data-is-global') === 'true';
            if (typeFilter === 'global' && !isGlobal) return false;
            if (typeFilter === 'company' && isGlobal) return false;

            // Search filter (name / description)
            if (searchTerm) {
                const name = card.querySelector('.card-title')?.textContent.toLowerCase() || '';
                const description = card.querySelector('.card-text')?.textContent.toLowerCase() || '';
                if (!name.includes(searchTerm) && !description.includes(searchTerm)) return false;
            }
            return true;
        };

        // Apply visibility filter first
        const visibleCards = allCards.filter(card => {
            const show = isVisible(card);
            card.style.display = show ? '' : 'none';
            return show;
        });

        // Sorting helpers
        const getCoverage = (card) => {
            const text = card.querySelector('.coverage-text')?.textContent || '';
            const match = text.match(/([0-9]+\.?[0-9]*)%/);
            return match ? parseFloat(match[1]) : 0;
        };
        const compareNames = (a, b) => a.localeCompare(b);

        // Sort the visible cards based on selected criteria
        visibleCards.sort((a, b) => {
            switch (sortValue) {
                case 'name_asc':
                    return compareNames(a.querySelector('.card-title').textContent, b.querySelector('.card-title').textContent);
                case 'name_desc':
                    return compareNames(b.querySelector('.card-title').textContent, a.querySelector('.card-title').textContent);
                case 'coverage_asc':
                    return getCoverage(a) - getCoverage(b);
                case 'coverage_desc':
                    return getCoverage(b) - getCoverage(a);
                case 'type_asc':
                    return (a.getAttribute('data-is-global') === b.getAttribute('data-is-global')) ?
                        compareNames(a.querySelector('.card-title').textContent, b.querySelector('.card-title').textContent) :
                        (a.getAttribute('data-is-global') === 'true' ? -1 : 1);
                case 'type_desc':
                    return (a.getAttribute('data-is-global') === b.getAttribute('data-is-global')) ?
                        compareNames(a.querySelector('.card-title').textContent, b.querySelector('.card-title').textContent) :
                        (a.getAttribute('data-is-global') === 'true' ? 1 : -1);
                default:
                    return 0;
            }
        });

        // Re-append cards in the new order so the visual layout reflects the sort
        visibleCards.forEach(card => deck.appendChild(card));

        // If table view is active, refresh it to reflect the new ordering/visibility
        const tableView = document.getElementById('frameworkTableView');
        if (tableView && tableView.style.display !== 'none') {
            renderFrameworkTable();
        }
    }

    function updateFilterButtons() {
        // Remove active class from all filter buttons
        [filterAll, filterGlobal, filterCompany].forEach(btn => {
            if (btn) btn.classList.remove('active');
        });
        
        // Add active class to current filter
        switch (currentTypeFilter) {
            case 'all':
                if (filterAll) filterAll.classList.add('active');
                break;
            case 'global':
                if (filterGlobal) filterGlobal.classList.add('active');
                break;
            case 'company':
                if (filterCompany) filterCompany.classList.add('active');
                break;
        }
    }

    function renderFrameworkTable() {
        // Get required elements dynamically
        const frameworkTableBody = document.getElementById('frameworkTableBody');
        const noFrameworksTable = document.getElementById('noFrameworksTable');
        
        // Check if required elements exist
        if (!frameworkTableBody || !noFrameworksTable) {
            console.error('Required table elements not found');
            return;
        }
        
        // Get all framework cards (which contain the data)
        const frameworkCards = Array.from(document.querySelectorAll('.framework-card'));
        frameworkTableBody.innerHTML = ''; // Clear existing rows

        if (frameworkCards.length === 0) {
            noFrameworksTable.style.display = 'block';
            return;
        }
        noFrameworksTable.style.display = 'none';

        frameworkCards.forEach(card => {
            const frameworkId = card.getAttribute('data-framework-id');
            const frameworkName = card.querySelector('.card-title')?.textContent || 'Unknown';
            const description = card.querySelector('.card-text')?.textContent || 'No description';
            const coverageText = card.querySelector('.coverage-text')?.textContent || '0% (0 fields)';
            const totalFields = coverageText.split('/')[1] ? parseInt(coverageText.split('/')[1].split(' ')[0]) : 'N/A';
            const lastUpdated = coverageText.includes('Last update:') ? coverageText.split('Last update:')[1].trim() : 'Never';
            
            // Get framework type information
            const isGlobal = card.getAttribute('data-is-global') === 'true';
            const isEditable = card.getAttribute('data-is-editable') === 'true';
            const frameworkType = isGlobal ? 'Global' : 'Company';
            const typeClass = isGlobal ? 'global' : 'company';
            const buttonClass = isGlobal ? 'info' : 'success';

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${frameworkName}</td>
                <td><span class="framework-type-cell ${typeClass}">${frameworkType}</span></td>
                <td>${description}</td>
                <td>${coverageText.split('(')[0].trim()}</td>
                <td>${totalFields}</td>
                <td>${lastUpdated}</td>
                <td>
                    <button class="btn btn-sm btn-outline-${buttonClass} view-details-btn" data-bs-toggle="modal" data-bs-target="#frameworkDetailsModal" data-framework-id="${frameworkId}">
                        View Details
                    </button>
                    ${!isGlobal ? `
                    <button class="btn btn-sm btn-outline-primary ms-1 edit-framework-btn" data-framework-id="${frameworkId}" title="Edit Framework">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger ms-1 delete-framework-btn" data-framework-id="${frameworkId}" title="Delete Framework">
                        <i class="fas fa-trash"></i>
                    </button>
                    ` : ''}
                </td>
            `;
            frameworkTableBody.appendChild(row);
        });

        // Re-attach event listeners for view details buttons in table
        frameworkTableBody.querySelectorAll('.view-details-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const frameworkId = this.getAttribute('data-framework-id');
                loadFrameworkDetails(frameworkId);
            });
        });
        
        // Re-attach event listeners for edit buttons in table
        frameworkTableBody.querySelectorAll('.edit-framework-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const frameworkId = this.getAttribute('data-framework-id');
                editFramework(frameworkId);
            });
        });

        // Re-attach event listeners for delete buttons in table
        frameworkTableBody.querySelectorAll('.delete-framework-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const frameworkId = this.getAttribute('data-framework-id');
                confirmAndDelete(frameworkId, this.closest('tr'));
            });
        });
    }

    function editFramework(frameworkId) {
        // Redirect to framework wizard in edit mode
        window.location.href = `/admin/frameworks/wizard?edit=${frameworkId}`;
    }

    async function confirmAndDelete(frameworkId, domElement) {
        if (!confirm('Are you sure you want to delete this framework? This action cannot be undone.')) {
            return;
        }
        try {
            const response = await fetch(`/admin/frameworks/${frameworkId}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            if (data.success) {
                // Remove element from DOM (row or card)
                if (domElement) {
                    domElement.remove();
                } else {
                    const card = document.querySelector(`.framework-card[data-framework-id="${frameworkId}"]`);
                    if (card) card.remove();
                }
                alert('Framework deleted successfully');
            } else {
                alert('Error deleting framework: ' + (data.error || 'Unknown error'));
            }
        } catch (err) {
            console.error('Delete error', err);
            alert('Error deleting framework');
        }
    }

    function enhanceFrameworkModal(frameworkId, isGlobal, isEditable) {
        // This function would enhance the modal with additional functionality
        console.log('Enhancing framework modal for:', frameworkId, 'Global:', isGlobal, 'Editable:', isEditable);
    }

    // Setup event listeners
    function setupEventListeners() {
        // Initialize filter buttons
        if (filterAll) {
            filterAll.addEventListener('click', () => {
                currentTypeFilter = 'all';
                updateFilterButtons();
                filterAndSortFrameworks();
            });
        }

        if (filterGlobal) {
            filterGlobal.addEventListener('click', () => {
                currentTypeFilter = 'global';
                updateFilterButtons();
                filterAndSortFrameworks();
            });
        }

        if (filterCompany) {
            filterCompany.addEventListener('click', () => {
                currentTypeFilter = 'company';
                updateFilterButtons();
                filterAndSortFrameworks();
            });
        }

        // Search and sort functionality
        const searchElement = document.getElementById('frameworkSearch');
        const sortElement = document.getElementById('frameworkSort');

        if (searchElement) {
            searchElement.addEventListener('input', filterAndSortFrameworks);
        }

        if (sortElement) {
            sortElement.addEventListener('change', filterAndSortFrameworks);
        }

        // Setup view details event listeners for cards using event delegation
        setupViewDetailsEventListeners();

        // View toggle functionality
        setTimeout(() => {
            const cardViewBtn = document.getElementById('cardViewBtn');
            const tableViewBtn = document.getElementById('tableViewBtn');
            const frameworkCardView = document.getElementById('frameworkCardView');
            const frameworkTableView = document.getElementById('frameworkTableView');

            if (cardViewBtn && tableViewBtn && frameworkCardView && frameworkTableView) {
                console.log('Setting up view toggle event listeners...');
                
                cardViewBtn.addEventListener('click', () => {
                    console.log('Card view clicked');
                    cardViewBtn.classList.add('active');
                    tableViewBtn.classList.remove('active');
                    frameworkCardView.style.display = '';
                    frameworkTableView.style.display = 'none';
                });

                tableViewBtn.addEventListener('click', () => {
                    console.log('Table view clicked');
                    tableViewBtn.classList.add('active');
                    cardViewBtn.classList.remove('active');
                    frameworkCardView.style.display = 'none';
                    frameworkTableView.style.display = '';
                    renderFrameworkTable();
                });
            } else {
                console.error('View toggle elements not found:', {
                    cardViewBtn: !!cardViewBtn,
                    tableViewBtn: !!tableViewBtn,
                    frameworkCardView: !!frameworkCardView,
                    frameworkTableView: !!frameworkTableView
                });
            }
        }, 100);
    }

    // Setup view details event listeners using event delegation
    function setupViewDetailsEventListeners() {
        // Use event delegation on the document body to handle all view details buttons
        document.addEventListener('click', function(e) {
            const viewBtn = e.target.closest('.view-details-btn');
            if (viewBtn) {
                e.preventDefault();
                const frameworkId = viewBtn.getAttribute('data-framework-id');
                if (frameworkId) {
                    console.log('View details clicked for framework:', frameworkId);
                    
                    // Show modal
                    const modalEl = document.getElementById('frameworkDetailsModal');
                    if (modalEl) {
                        const bsModal = bootstrap.Modal.getOrCreateInstance(modalEl);
                        bsModal.show();
                    }
                    
                    // Load details
                    loadFrameworkDetails(frameworkId);
                }
            }

            // Handle click on edit-framework button (card or table)
            const editBtn = e.target.closest('.edit-framework-btn');
            if (editBtn) {
                e.preventDefault();
                const frameworkId = editBtn.getAttribute('data-framework-id');
                if (frameworkId) {
                    console.log('Edit framework clicked for:', frameworkId);
                    editFramework(frameworkId);
                }
            }

            // handle delete btn on cards
            const delBtn = e.target.closest('.delete-framework-btn');
            if (delBtn) {
                e.preventDefault();
                const fid = delBtn.getAttribute('data-framework-id');
                confirmAndDelete(fid, delBtn.closest('.framework-card'));
                return;
            }
        });
    }

    // Public API
    return {
        initialize: function() {
            console.log('FrameworksMain: Initializing...');
            initializeDOMElements();
            setupEventListeners();
            initializeFrameworkCards();
            console.log('FrameworksMain: Initialization complete');
        },
        
        // Core functions
        initializeFrameworkCards: initializeFrameworkCards,
        loadFrameworkCoverage: loadFrameworkCoverage,
        updateCoverageDisplay: updateCoverageDisplay,
        loadFrameworkDetails: loadFrameworkDetails,
        displayFrameworkDetailsWithCoverage: displayFrameworkDetailsWithCoverage,
        filterAndSortFrameworks: filterAndSortFrameworks,
        updateFilterButtons: updateFilterButtons,
        renderFrameworkTable: renderFrameworkTable,
        editFramework: editFramework,
        enhanceFrameworkModal: enhanceFrameworkModal,
        setupViewDetailsEventListeners: setupViewDetailsEventListeners,
        
        // Utility functions
        setCurrentTypeFilter: function(filter) {
            currentTypeFilter = filter;
            updateFilterButtons();
        },
        
        getCurrentTypeFilter: function() {
            return currentTypeFilter;
        },
        
        refresh: function() {
            initializeFrameworkCards();
        },

        /**
         * Check if module is ready
         */
        isReady: function() {
            return true; // Main module is ready when initialized
        }
    };
})(); 