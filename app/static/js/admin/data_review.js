// Data Review JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeDataReview();
});

let currentEditRow = null;
let originalValue = null;

function initializeDataReview() {
    // Add event listeners for filter changes
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        const filterElements = filterForm.querySelectorAll('select, input');
        filterElements.forEach(element => {
            if (element.type === 'date' || element.tagName === 'SELECT') {
                element.addEventListener('change', function() {
                    // Auto-submit form when filters change
                    setTimeout(() => filterForm.submit(), 100);
                });
            }
        });
    }

    // Add search functionality
    addSearchFunctionality();
    
    // Initialize tooltips if needed
    initializeTooltips();
}

function clearFilters() {
    const form = document.getElementById('filterForm');
    if (form) {
        // Clear all form elements
        const inputs = form.querySelectorAll('input, select');
        inputs.forEach(input => {
            if (input.type === 'date' || input.type === 'text') {
                input.value = '';
            } else if (input.tagName === 'SELECT') {
                input.selectedIndex = 0;
            }
        });
        
        // Submit the form to apply cleared filters
        form.submit();
    }
}

function editRecord(button) {
    // Cancel any other active edits
    if (currentEditRow && currentEditRow !== button.closest('tr')) {
        cancelEdit(currentEditRow.querySelector('.cancel-btn'));
    }
    
    const row = button.closest('tr');
    const valueContainer = row.querySelector('.value-container');
    const displayValue = valueContainer.querySelector('.display-value');
    const editValue = valueContainer.querySelector('.edit-value');
    
    // Store references
    currentEditRow = row;
    originalValue = displayValue.textContent.trim();
    
    // Switch to edit mode
    displayValue.style.display = 'none';
    editValue.style.display = 'block';
    editValue.focus();
    editValue.select();
    
    // Toggle buttons
    button.style.display = 'none';
    row.querySelector('.save-btn').style.display = 'inline-block';
    row.querySelector('.cancel-btn').style.display = 'inline-block';
    
    // Add enter key listener
    editValue.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            saveRecord(row.querySelector('.save-btn'));
        } else if (e.key === 'Escape') {
            cancelEdit(row.querySelector('.cancel-btn'));
        }
    });
}

function cancelEdit(button) {
    const row = button.closest('tr');
    const valueContainer = row.querySelector('.value-container');
    const displayValue = valueContainer.querySelector('.display-value');
    const editValue = valueContainer.querySelector('.edit-value');
    
    // Restore original value
    editValue.value = originalValue;
    
    // Switch back to display mode
    displayValue.style.display = 'block';
    editValue.style.display = 'none';
    
    // Toggle buttons
    row.querySelector('.edit-btn').style.display = 'inline-block';
    row.querySelector('.save-btn').style.display = 'none';
    button.style.display = 'none';
    
    // Clear references
    currentEditRow = null;
    originalValue = null;
}

function saveRecord(button) {
    const row = button.closest('tr');
    const valueContainer = row.querySelector('.value-container');
    const editValue = valueContainer.querySelector('.edit-value');
    const newValue = editValue.value.trim();
    
    // Validate the new value
    if (newValue === '') {
        alert('Value cannot be empty');
        editValue.focus();
        return;
    }
    
    // Check if value actually changed
    if (newValue === originalValue) {
        cancelEdit(button.closest('tr').querySelector('.cancel-btn'));
        return;
    }
    
    // Show confirmation modal
    showEditConfirmation(row.dataset.id, originalValue, newValue, row);
}

function showEditConfirmation(dataId, currentValue, newValue, row) {
    const modal = document.getElementById('editReasonModal');
    const currentValueSpan = document.getElementById('currentValue');
    const newValueSpan = document.getElementById('newValue');
    
    currentValueSpan.textContent = currentValue;
    newValueSpan.textContent = newValue;
    
    // Store data for confirmation
    modal.dataset.dataId = dataId;
    modal.dataset.newValue = newValue;
    modal.dataset.currentValue = currentValue;
    modal.dataset.rowIndex = Array.from(row.parentNode.children).indexOf(row);
    
    modal.style.display = 'block';
}

function closeEditModal() {
    const modal = document.getElementById('editReasonModal');
    const editReason = document.getElementById('editReason');
    
    modal.style.display = 'none';
    editReason.value = '';
    
    // Remove stored data
    delete modal.dataset.dataId;
    delete modal.dataset.newValue;
    delete modal.dataset.currentValue;
    delete modal.dataset.rowIndex;
}

function confirmEdit() {
    const modal = document.getElementById('editReasonModal');
    const dataId = modal.dataset.dataId;
    const newValue = modal.dataset.newValue;
    const editReason = document.getElementById('editReason').value;
    const rowIndex = parseInt(modal.dataset.rowIndex);
    
    showLoading();
    
    // Send AJAX request to update the data
    fetch('/admin/data_review', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            data_id: dataId,
            new_value: newValue,
            edit_reason: editReason
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            // Update the display
            const row = document.querySelector(`tr[data-id="${dataId}"]`);
            if (row) {
                const valueContainer = row.querySelector('.value-container');
                const displayValue = valueContainer.querySelector('.display-value');
                const editValue = valueContainer.querySelector('.edit-value');
                
                // Update display value
                displayValue.textContent = newValue;
                
                // Switch back to display mode
                displayValue.style.display = 'block';
                editValue.style.display = 'none';
                
                // Toggle buttons
                row.querySelector('.edit-btn').style.display = 'inline-block';
                row.querySelector('.save-btn').style.display = 'none';
                row.querySelector('.cancel-btn').style.display = 'none';
                
                // Show success message
                showSuccessMessage('Data updated successfully');
            }
            
            closeEditModal();
            
            // Clear references
            currentEditRow = null;
            originalValue = null;
        } else {
            showErrorMessage(data.message || 'Failed to update data');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showErrorMessage('An error occurred while updating the data');
    });
}

function viewAttachment(attachmentId) {
    // This would typically open the attachment in a new window or download it
    // For now, we'll show an alert
    alert(`Viewing attachment with ID: ${attachmentId}`);
    
    // TODO: Implement actual attachment viewing/downloading
    // window.open(`/admin/view_attachment/${attachmentId}`, '_blank');
}

function exportData() {
    showLoading();
    
    // Get current filter parameters
    const urlParams = new URLSearchParams(window.location.search);
    const exportUrl = '/admin/export_data_review?' + urlParams.toString();
    
    // Create a temporary link and click it to download
    const link = document.createElement('a');
    link.href = exportUrl;
    link.download = 'esg_data_export.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    hideLoading();
    showSuccessMessage('Export started. Download will begin shortly.');
}

function addSearchFunctionality() {
    // Add a search input if it doesn't exist
    const tableControls = document.querySelector('.table-controls');
    if (tableControls && !document.getElementById('searchInput')) {
        const searchContainer = document.createElement('div');
        searchContainer.className = 'search-container';
        searchContainer.innerHTML = `
            <input type="text" id="searchInput" placeholder="Search table..." class="search-input">
        `;
        
        tableControls.querySelector('.table-info').appendChild(searchContainer);
        
        // Add search functionality
        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('input', function() {
            filterTable(this.value.toLowerCase());
        });
    }
}

function filterTable(searchTerm) {
    const table = document.getElementById('dataTable');
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
    
    // Update record count
    const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none');
    const tableInfo = document.querySelector('.table-info span');
    if (tableInfo) {
        tableInfo.textContent = `${visibleRows.length} records found${searchTerm ? ' (filtered)' : ''}`;
    }
}

function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'flex';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

function showSuccessMessage(message) {
    // Create and show a success toast
    const toast = createToast('success', message);
    document.body.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}

function showErrorMessage(message) {
    // Create and show an error toast
    const toast = createToast('error', message);
    document.body.appendChild(toast);
    
    // Remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}

function createToast(type, message) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    // Add toast styles
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#28a745' : '#dc3545'};
        color: white;
        padding: 15px 20px;
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        min-width: 300px;
    `;
    
    return toast;
}

function initializeTooltips() {
    // Initialize any tooltips for better UX
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            showTooltip(this, this.dataset.tooltip);
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element, text) {
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: #333;
        color: white;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        z-index: 10001;
        pointer-events: none;
        white-space: nowrap;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
    tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
}

function hideTooltip() {
    const tooltip = document.querySelector('.custom-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Handle modal clicks outside content
window.addEventListener('click', function(event) {
    const modal = document.getElementById('editReasonModal');
    if (event.target === modal) {
        closeEditModal();
    }
});

// Handle escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('editReasonModal');
        if (modal.style.display === 'block') {
            closeEditModal();
        }
    }
});

// Add CSS for animations and additional styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .search-container {
        margin-left: 20px;
    }
    
    .search-input {
        padding: 8px 12px;
        border: 2px solid #e1e5e9;
        border-radius: 6px;
        font-size: 14px;
        min-width: 200px;
        transition: border-color 0.3s ease;
    }
    
    .search-input:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .toast-content {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .toast-close {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 0;
        margin-left: auto;
        opacity: 0.8;
        transition: opacity 0.3s ease;
    }
    
    .toast-close:hover {
        opacity: 1;
    }
`;

document.head.appendChild(style); 