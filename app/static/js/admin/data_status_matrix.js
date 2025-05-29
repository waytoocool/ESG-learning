// Data Status Matrix JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeMatrix();
    setupAutoRefresh();
    setupKeyboardShortcuts();
});

function initializeMatrix() {
    // Auto-submit form when date changes
    const dateInput = document.getElementById('reporting_date');
    if (dateInput) {
        dateInput.addEventListener('change', function() {
            document.getElementById('periodForm').submit();
        });
    }

    // Initialize tooltips for status indicators
    initializeTooltips();

    // Setup table interactions
    setupTableInteractions();
}

function setupTableInteractions() {
    // Add hover effects and click handlers for status cells
    const statusCells = document.querySelectorAll('.status-indicator');
    
    statusCells.forEach(cell => {
        // Enhanced hover effect
        cell.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1)';
            this.style.zIndex = '20';
        });
        
        cell.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.zIndex = 'auto';
        });
        
        // Click to show details
        cell.addEventListener('click', function() {
            const esgDataId = this.closest('tr').querySelector('[onclick*="viewDetails"]');
            if (esgDataId) {
                // Extract parameters from onclick attribute
                const onclickAttr = esgDataId.getAttribute('onclick');
                const matches = onclickAttr.match(/viewDetails\('([^']+)',\s*'([^']+)',\s*'([^']+)'\)/);
                if (matches) {
                    viewDetails(matches[1], matches[2], matches[3]);
                }
            }
        });
    });
}

function initializeTooltips() {
    const statusIndicators = document.querySelectorAll('.status-indicator[title]');
    
    statusIndicators.forEach(indicator => {
        indicator.addEventListener('mouseenter', function(e) {
            showTooltip(e, this.getAttribute('title'));
        });
        
        indicator.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(event, text) {
    // Remove existing tooltip
    hideTooltip();
    
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: fixed;
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.8rem;
        z-index: 1000;
        pointer-events: none;
        white-space: nowrap;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    
    document.body.appendChild(tooltip);
    
    // Position tooltip
    const rect = tooltip.getBoundingClientRect();
    tooltip.style.left = (event.clientX - rect.width / 2) + 'px';
    tooltip.style.top = (event.clientY - rect.height - 10) + 'px';
}

function hideTooltip() {
    const tooltip = document.querySelector('.custom-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

function viewDetails(esgDataId, dataPointName, entityName) {
    // Set modal title
    document.getElementById('modalTitle').textContent = `${dataPointName} - ${entityName}`;
    
    // Set edit link
    const editLink = document.getElementById('editDataLink');
    const currentDate = document.getElementById('reporting_date').value;
    editLink.href = `/admin/data_review?entity_id=${encodeURIComponent(entityName)}&date_from=${currentDate}&date_to=${currentDate}`;
    
    // Load data details via AJAX
    showLoading();
    
    fetch(`/admin/esg_data_details/${esgDataId}`)
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                displayDataDetails(data.data);
            } else {
                showError('Failed to load data details');
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Error loading data details:', error);
            showError('Error loading data details');
        });
    
    // Show modal
    document.getElementById('detailsModal').style.display = 'block';
}

function displayDataDetails(data) {
    const modalBody = document.getElementById('modalBody');
    
    modalBody.innerHTML = `
        <div class="data-details">
            <div class="detail-section">
                <h4><i class="fas fa-info-circle"></i> General Information</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Data Point:</label>
                        <span>${data.data_point_name}</span>
                    </div>
                    <div class="detail-item">
                        <label>Entity:</label>
                        <span>${data.entity_name}</span>
                    </div>
                    <div class="detail-item">
                        <label>Framework:</label>
                        <span>${data.framework_name}</span>
                    </div>
                    <div class="detail-item">
                        <label>Reporting Date:</label>
                        <span>${formatDate(data.reporting_date)}</span>
                    </div>
                    <div class="detail-item">
                        <label>Field Type:</label>
                        <span class="field-type ${data.is_computed ? 'computed' : 'raw'}">
                            ${data.is_computed ? 'Computed' : 'Raw'}
                        </span>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h4><i class="fas fa-chart-line"></i> Value Information</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Current Value:</label>
                        <span class="current-value">${data.current_value || 'Not set'}</span>
                    </div>
                    ${data.unit ? `
                    <div class="detail-item">
                        <label>Unit:</label>
                        <span>${data.unit}</span>
                    </div>
                    ` : ''}
                    <div class="detail-item">
                        <label>Last Updated:</label>
                        <span>${data.updated_at ? formatDateTime(data.updated_at) : 'Never'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Status:</label>
                        <span class="status-badge ${data.status}">${data.status.charAt(0).toUpperCase() + data.status.slice(1)}</span>
                    </div>
                </div>
            </div>
            
            ${data.evidence_files && data.evidence_files.length > 0 ? `
            <div class="detail-section">
                <h4><i class="fas fa-paperclip"></i> Evidence Files</h4>
                <div class="evidence-list">
                    ${data.evidence_files.map(file => `
                        <div class="evidence-item">
                            <i class="fas fa-file"></i>
                            <span class="filename">${file.filename}</span>
                            <span class="filesize">(${formatFileSize(file.size)})</span>
                            <a href="/download/${file.id}" class="download-btn" title="Download">
                                <i class="fas fa-download"></i>
                            </a>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            ${data.audit_trail && data.audit_trail.length > 0 ? `
            <div class="detail-section">
                <h4><i class="fas fa-history"></i> Audit Trail</h4>
                <div class="audit-list">
                    ${data.audit_trail.map(entry => `
                        <div class="audit-entry">
                            <div class="audit-header">
                                <span class="audit-action">${entry.change_type}</span>
                                <span class="audit-date">${formatDateTime(entry.change_date)}</span>
                            </div>
                            <div class="audit-details">
                                <span class="audit-user">by ${entry.changed_by_username}</span>
                                ${entry.old_value !== null ? `<span class="audit-change">from ${entry.old_value} to ${entry.new_value}</span>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
        </div>
    `;
}

function closeModal() {
    document.getElementById('detailsModal').style.display = 'none';
}

function setupAutoRefresh() {
    // Add refresh button to page
    addRefreshButton();
    
    // Optional: Auto-refresh every 5 minutes
    setInterval(function() {
        if (document.visibilityState === 'visible') {
            refreshData();
        }
    }, 300000); // 5 minutes
}

function addRefreshButton() {
    const header = document.querySelector('.page-header');
    if (header) {
        const refreshBtn = document.createElement('button');
        refreshBtn.className = 'refresh-btn';
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
        refreshBtn.onclick = refreshData;
        
        refreshBtn.style.cssText = `
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.3s ease;
        `;
        
        header.style.position = 'relative';
        header.appendChild(refreshBtn);
    }
}

function refreshData() {
    // Show loading indicator
    showLoading();
    
    // Reload the page with current parameters
    window.location.reload();
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Escape key to close modal
        if (e.key === 'Escape') {
            closeModal();
        }
        
        // R key to refresh (Ctrl+R is browser default)
        if (e.key === 'r' && !e.ctrlKey && !e.metaKey) {
            refreshData();
        }
        
        // F key to focus on date input
        if (e.key === 'f' && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            const dateInput = document.getElementById('reporting_date');
            if (dateInput) {
                dateInput.focus();
            }
        }
    });
}

function showLoading() {
    // Create loading overlay
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.innerHTML = `
        <div class="loading-spinner">
            <i class="fas fa-spinner fa-spin"></i>
            <span>Loading...</span>
        </div>
    `;
    
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 2000;
        backdrop-filter: blur(2px);
    `;
    
    overlay.querySelector('.loading-spinner').style.cssText = `
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
        font-size: 1.2rem;
        color: #667eea;
    `;
    
    overlay.querySelector('.fa-spinner').style.fontSize = '2rem';
    
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <i class="fas ${type === 'success' ? 'fa-check' : type === 'error' ? 'fa-exclamation-triangle' : 'fa-info'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

function showError(message) {
    showToast(message, 'error');
}

function showSuccess(message) {
    showToast(message, 'success');
}

// Utility functions
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
}

function formatDateTime(dateTimeString) {
    if (!dateTimeString) return 'N/A';
    return new Date(dateTimeString).toLocaleString();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Export functions for use in HTML
window.viewDetails = viewDetails;
window.closeModal = closeModal;
window.refreshData = refreshData;

// Click outside modal to close
window.onclick = function(event) {
    const modal = document.getElementById('detailsModal');
    if (event.target === modal) {
        closeModal();
    }
}; 