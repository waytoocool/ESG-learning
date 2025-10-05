/**
 * Assignment History JavaScript Module
 * 
 * This module handles the interactive assignment history timeline interface
 * with filtering, search, pagination, and modal interactions.
 * 
 * Features:
 * - Real-time filtering and search
 * - Timeline visualization with status indicators
 * - Data series exploration
 * - Assignment details and data impact views
 * - Responsive design with accessibility support
 */

class AssignmentHistoryManager {
    constructor() {
        this.currentPage = 1;
        this.currentFilters = {};
        this.isLoading = false;
        this.timelineContainer = document.getElementById('timelineContainer');
        this.paginationContainer = document.getElementById('paginationContainer');
        this.loadingState = document.getElementById('loadingState');
        this.emptyState = document.getElementById('emptyState');
        
        this.initializeFilters();
        this.initializeEventListeners();
        this.loadFilterOptions();
        this.loadTimeline();
    }

    initializeFilters() {
        this.filters = {
            fieldFilter: document.getElementById('fieldFilter'),
            entityFilter: document.getElementById('entityFilter'),
            dateFromFilter: document.getElementById('dateFromFilter'),
            dateToFilter: document.getElementById('dateToFilter'),
            searchFilter: document.getElementById('searchFilter')
        };

        this.clearFiltersBtn = document.getElementById('clearFilters');
        this.exportBtn = document.getElementById('exportHistory');
    }

    initializeEventListeners() {
        // Filter change listeners
        Object.values(this.filters).forEach(filter => {
            filter.addEventListener('change', () => this.handleFilterChange());
        });

        // Search input listener with debounce
        let searchTimeout;
        this.filters.searchFilter.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => this.handleFilterChange(), 500);
        });

        // Control buttons
        this.clearFiltersBtn.addEventListener('click', () => this.clearFilters());
        this.exportBtn.addEventListener('click', () => this.exportHistory());

        // Modal initialization
        this.initializeModals();
    }

    initializeModals() {
        // Bootstrap modals
        this.assignmentDetailsModal = new bootstrap.Modal(document.getElementById('assignmentDetailsModal'));
        this.dataSeriesModal = new bootstrap.Modal(document.getElementById('dataSeriesModal'));
        this.dataEntriesModal = new bootstrap.Modal(document.getElementById('dataEntriesModal'));
    }

    async loadFilterOptions() {
        try {
            const response = await fetch('/admin/assignment-history/api/filters');
            if (!response.ok) throw new Error('Failed to load filter options');
            
            const data = await response.json();
            
            this.populateFilterSelect(this.filters.fieldFilter, data.fields, 'name');
            this.populateFilterSelect(this.filters.entityFilter, data.entities, 'name');
            
            // Set date range defaults
            if (data.date_range.min_date) {
                this.filters.dateFromFilter.min = data.date_range.min_date;
            }
            if (data.date_range.max_date) {
                this.filters.dateToFilter.max = data.date_range.max_date;
            }
            
        } catch (error) {
            console.error('Error loading filter options:', error);
            this.showError('Failed to load filter options');
        }
    }

    populateFilterSelect(selectElement, options, labelField) {
        // Clear existing options (except the first 'All' option)
        while (selectElement.children.length > 1) {
            selectElement.removeChild(selectElement.lastChild);
        }
        
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.id;
            optionElement.textContent = option[labelField];
            selectElement.appendChild(optionElement);
        });
    }

    handleFilterChange() {
        // Reset to first page when filters change
        this.currentPage = 1;
        this.collectFilters();
        this.loadTimeline();
    }

    collectFilters() {
        this.currentFilters = {
            field_id: this.filters.fieldFilter.value || undefined,
            entity_id: this.filters.entityFilter.value || undefined,
            date_from: this.filters.dateFromFilter.value || undefined,
            date_to: this.filters.dateToFilter.value || undefined,
            search: this.filters.searchFilter.value.trim() || undefined
        };
        
        // Remove undefined values
        Object.keys(this.currentFilters).forEach(key => {
            if (this.currentFilters[key] === undefined) {
                delete this.currentFilters[key];
            }
        });
    }

    clearFilters() {
        Object.values(this.filters).forEach(filter => {
            filter.value = '';
        });
        
        this.currentFilters = {};
        this.currentPage = 1;
        this.loadTimeline();
    }

    async loadTimeline(page = 1) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.currentPage = page;
        this.showLoading();
        
        try {
            const params = new URLSearchParams({
                page: page.toString(),
                per_page: '20',
                ...this.currentFilters
            });
            
            const response = await fetch(`/admin/assignment-history/api/timeline?${params}`);
            if (!response.ok) throw new Error('Failed to load timeline data');
            
            const data = await response.json();
            
            if (data.timeline.length === 0) {
                this.showEmptyState();
            } else {
                this.renderTimeline(data.timeline);
                this.renderPagination(data.pagination);
            }
            
        } catch (error) {
            console.error('Error loading timeline:', error);
            this.showError('Failed to load assignment timeline');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    renderTimeline(timelineData) {
        this.hideEmptyState();
        
        this.timelineContainer.innerHTML = timelineData.map(item => {
            const statusClass = item.status.toLowerCase();
            const markerIcon = this.getStatusIcon(item.status);
            
            return `
                <div class="timeline-item" data-assignment-id="${item.id}">
                    <div class="timeline-marker ${statusClass}">
                        ${markerIcon}
                    </div>
                    <div class="timeline-content ${statusClass}">
                        <div class="assignment-header">
                            <div class="assignment-title">
                                <h4>${this.escapeHtml(item.field_name)}</h4>
                                <p class="assignment-subtitle">
                                    Entity: ${this.escapeHtml(item.entity_name)} | 
                                    Frequency: ${item.frequency} | 
                                    Unit: ${item.unit || 'Default'}
                                </p>
                            </div>
                            <div class="assignment-status">
                                <span class="status-badge ${statusClass}">${item.status_display}</span>
                                <span class="version-info">${item.version_display}</span>
                            </div>
                        </div>
                        
                        <div class="assignment-details">
                            <div class="detail-item">
                                <span class="detail-label">Assigned Date</span>
                                <span class="detail-value">${this.formatDate(item.assigned_date)}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Assigned By</span>
                                <span class="detail-value">${this.escapeHtml(item.assigned_by)}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Data Entries</span>
                                <span class="detail-value">${item.data_entry_count}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Series Version</span>
                                <span class="detail-value">v${item.version}</span>
                            </div>
                        </div>
                        
                        ${item.changes_summary !== 'Initial assignment' ? `
                        <div class="changes-summary">
                            <span class="detail-label">Changes Made</span>
                            <span class="detail-value">${this.escapeHtml(item.changes_summary)}</span>
                        </div>
                        ` : ''}
                        
                        <div class="timeline-actions">
                            <button class="action-btn" onclick="assignmentHistory.viewSeriesHistory('${item.series_id}')">
                                <i class="fas fa-history"></i> View Series
                            </button>
                            <button class="action-btn" onclick="assignmentHistory.viewDataEntries('${item.id}')">
                                <i class="fas fa-database"></i> View Data (${item.data_entry_count})
                            </button>
                            ${item.is_active ? `
                            <button class="action-btn" onclick="assignmentHistory.viewAssignmentDetails('${item.id}')">
                                <i class="fas fa-eye"></i> Details
                            </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderPagination(paginationData) {
        if (paginationData.pages <= 1) {
            this.paginationContainer.innerHTML = '';
            return;
        }
        
        const { page, pages, has_prev, has_next, total } = paginationData;
        
        let paginationHTML = `
            <div class="pagination-info">
                Showing page ${page} of ${pages} (${total} total assignments)
            </div>
            <div class="pagination-controls">
                <button class="page-btn" ${!has_prev ? 'disabled' : ''} onclick="assignmentHistory.loadTimeline(${page - 1})">
                    <i class="fas fa-chevron-left"></i>
                </button>
        `;
        
        // Page numbers
        const startPage = Math.max(1, page - 2);
        const endPage = Math.min(pages, page + 2);
        
        if (startPage > 1) {
            paginationHTML += `<button class="page-btn" onclick="assignmentHistory.loadTimeline(1)">1</button>`;
            if (startPage > 2) {
                paginationHTML += `<span class="pagination-ellipsis">...</span>`;
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `
                <button class="page-btn ${i === page ? 'active' : ''}" onclick="assignmentHistory.loadTimeline(${i})">
                    ${i}
                </button>
            `;
        }
        
        if (endPage < pages) {
            if (endPage < pages - 1) {
                paginationHTML += `<span class="pagination-ellipsis">...</span>`;
            }
            paginationHTML += `<button class="page-btn" onclick="assignmentHistory.loadTimeline(${pages})">${pages}</button>`;
        }
        
        paginationHTML += `
                <button class="page-btn" ${!has_next ? 'disabled' : ''} onclick="assignmentHistory.loadTimeline(${page + 1})">
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        `;
        
        this.paginationContainer.innerHTML = paginationHTML;
    }

    async viewSeriesHistory(seriesId) {
        try {
            const response = await fetch(`/admin/assignment-history/api/series/${seriesId}`);
            if (!response.ok) throw new Error('Failed to load series data');
            
            const data = await response.json();
            
            const modalContent = document.getElementById('dataSeriesContent');
            const modalTitle = document.getElementById('dataSeriesModalLabel');
            
            modalTitle.textContent = `${data.series_summary.field_name} - ${data.series_summary.entity_name}`;
            
            modalContent.innerHTML = `
                <div class="series-summary">
                    <div class="row">
                        <div class="col-md-3">
                            <strong>Total Versions:</strong><br>
                            ${data.series_summary.total_versions}
                        </div>
                        <div class="col-md-3">
                            <strong>Current Version:</strong><br>
                            v${data.series_summary.current_version}
                        </div>
                        <div class="col-md-3">
                            <strong>First Assigned:</strong><br>
                            ${this.formatDate(data.series_summary.first_assigned)}
                        </div>
                        <div class="col-md-3">
                            <strong>Last Updated:</strong><br>
                            ${this.formatDate(data.series_summary.last_updated)}
                        </div>
                    </div>
                </div>
                
                <div class="series-timeline">
                    ${data.version_history.map((version, index) => `
                        <div class="series-version">
                            <div class="series-marker ${version.is_active ? 'current' : ''}"></div>
                            <div class="series-content">
                                <div class="version-header">
                                    <div class="version-title">
                                        Version ${version.version} 
                                        <span class="status-badge ${version.status}">${version.status}</span>
                                    </div>
                                    <div class="version-date">${this.formatDate(version.assigned_date)}</div>
                                </div>
                                
                                <div class="version-details">
                                    <div class="row">
                                        <div class="col-md-4">
                                            <strong>Frequency:</strong> ${version.frequency}
                                        </div>
                                        <div class="col-md-4">
                                            <strong>Unit:</strong> ${version.unit || 'Default'}
                                        </div>
                                        <div class="col-md-4">
                                            <strong>Data Entries:</strong> ${version.data_entry_count}
                                        </div>
                                    </div>
                                    <div class="mt-2">
                                        <strong>Assigned By:</strong> ${version.assigned_by}
                                    </div>
                                </div>
                                
                                ${version.changes.length > 0 ? `
                                <div class="changes-section mt-3">
                                    <strong>Changes from Previous Version:</strong>
                                    <ul class="changes-list">
                                        ${version.changes.map(change => `
                                            <li>${change.field}: ${change.old_value} → ${change.new_value}</li>
                                        `).join('')}
                                    </ul>
                                </div>
                                ` : index === 0 ? '<div class="mt-3"><em>Initial assignment version</em></div>' : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            
            this.dataSeriesModal.show();
            
        } catch (error) {
            console.error('Error loading series history:', error);
            this.showError('Failed to load series history');
        }
    }

    async viewDataEntries(assignmentId) {
        try {
            const response = await fetch(`/admin/assignment-history/api/data-entries/${assignmentId}`);
            if (!response.ok) throw new Error('Failed to load data entries');
            
            const data = await response.json();
            
            const modalContent = document.getElementById('dataEntriesContent');
            const modalTitle = document.getElementById('dataEntriesModalLabel');
            
            modalTitle.textContent = `Data Entries - ${data.assignment_info.field_name}`;
            
            modalContent.innerHTML = `
                <div class="assignment-info mb-3">
                    <div class="row">
                        <div class="col-md-6">
                            <strong>Field:</strong> ${this.escapeHtml(data.assignment_info.field_name)}<br>
                            <strong>Entity:</strong> ${this.escapeHtml(data.assignment_info.entity_name)}
                        </div>
                        <div class="col-md-6">
                            <strong>Version:</strong> v${data.assignment_info.version}<br>
                            <strong>Frequency:</strong> ${data.assignment_info.frequency}
                        </div>
                    </div>
                </div>
                
                <div class="summary-stats mb-3">
                    <div class="row">
                        <div class="col-md-4">
                            <div class="stat-card">
                                <div class="stat-number">${data.summary.total_entries}</div>
                                <div class="stat-label">Total Entries</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="stat-card">
                                <div class="stat-number">${data.summary.direct_entries}</div>
                                <div class="stat-label">Direct Links</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="stat-card">
                                <div class="stat-number">${data.summary.legacy_entries}</div>
                                <div class="stat-label">Legacy Links</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                ${data.data_entries.length > 0 ? `
                <div class="table-responsive">
                    <table class="data-entries-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Value</th>
                                <th>Unit</th>
                                <th>Link Type</th>
                                <th>Created By</th>
                                <th>Created</th>
                                <th>File</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.data_entries.map(entry => `
                                <tr>
                                    <td>${this.formatDate(entry.reporting_date)}</td>
                                    <td>${entry.raw_value || 'N/A'}</td>
                                    <td>${entry.unit || 'N/A'}</td>
                                    <td>
                                        <span class="link-type-badge ${entry.link_type}">
                                            ${entry.link_type}
                                        </span>
                                    </td>
                                    <td>${this.escapeHtml(entry.created_by)}</td>
                                    <td>${this.formatDate(entry.created_at)}</td>
                                    <td>${entry.has_file ? '<i class="fas fa-file text-success"></i>' : ''}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                ` : '<p class="text-muted">No data entries found for this assignment.</p>'}
            `;
            
            this.dataEntriesModal.show();
            
        } catch (error) {
            console.error('Error loading data entries:', error);
            this.showError('Failed to load data entries');
        }
    }

    async viewAssignmentDetails(assignmentId) {
        // This would show detailed assignment configuration
        // For now, just show a placeholder
        const modalContent = document.getElementById('assignmentDetailsContent');
        modalContent.innerHTML = `
            <p>Assignment details for ID: ${assignmentId}</p>
            <p>This feature shows detailed assignment configuration including:</p>
            <ul>
                <li>Field specifications</li>
                <li>Entity mapping</li>
                <li>Frequency settings</li>
                <li>Topic assignments</li>
                <li>Historical changes</li>
            </ul>
        `;
        
        this.assignmentDetailsModal.show();
    }

    async exportHistory() {
        try {
            // Create download parameters with current filters
            const params = new URLSearchParams({
                export: 'csv',
                ...this.currentFilters
            });
            
            // Create a temporary link to trigger download
            const link = document.createElement('a');
            link.href = `/admin/assignment-history/api/timeline?${params}`;
            link.download = `assignment_history_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
        } catch (error) {
            console.error('Error exporting history:', error);
            this.showError('Failed to export assignment history');
        }
    }

    getStatusIcon(status) {
        switch (status.toLowerCase()) {
            case 'active':
                return '<i class="fas fa-check"></i>';
            case 'superseded':
                return '<i class="fas fa-times"></i>';
            case 'legacy':
                return '<i class="fas fa-archive"></i>';
            default:
                return '<i class="fas fa-question"></i>';
        }
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (error) {
            return 'Invalid Date';
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    showLoading() {
        this.loadingState.style.display = 'block';
        this.timelineContainer.style.display = 'none';
        this.paginationContainer.style.display = 'none';
        this.emptyState.style.display = 'none';
        
        // Show loading indicator in timeline header
        const indicator = document.querySelector('.timeline-status .loading-indicator');
        if (indicator) {
            indicator.style.display = 'inline';
        }
    }

    hideLoading() {
        this.loadingState.style.display = 'none';
        this.timelineContainer.style.display = 'block';
        this.paginationContainer.style.display = 'block';
        
        // Hide loading indicator
        const indicator = document.querySelector('.timeline-status .loading-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    showEmptyState() {
        this.emptyState.style.display = 'block';
        this.timelineContainer.style.display = 'none';
        this.paginationContainer.style.display = 'none';
    }

    hideEmptyState() {
        this.emptyState.style.display = 'none';
    }

    showError(message) {
        // Create and show error alert
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            <strong>Error:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Insert at the top of the container
        const container = document.querySelector('.assignment-history-container');
        container.insertBefore(alert, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

// Initialize when DOM is loaded
let assignmentHistory;

document.addEventListener('DOMContentLoaded', function() {
    assignmentHistory = new AssignmentHistoryManager();
});

// Export for global access
window.assignmentHistory = assignmentHistory;