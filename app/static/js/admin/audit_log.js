// Toggle details function
function toggleDetails(logId) {
    const detailRow = document.getElementById('details-' + logId);
    const expandBtn = event.target.closest('.expand-btn');

    if (detailRow) {
        if (detailRow.style.display === 'none') {
            detailRow.style.display = 'table-row';
            expandBtn.classList.add('expanded');
        } else {
            detailRow.style.display = 'none';
            expandBtn.classList.remove('expanded');
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const changeTypeFilter = document.getElementById('changeTypeFilter');
    const dateFilter = document.getElementById('dateFilter');
    const auditRows = document.querySelectorAll('.audit-row');

    function filterTable() {
        const searchTerm = searchInput.value.toLowerCase();
        const changeType = changeTypeFilter.value;
        const filterDate = dateFilter.value;

        auditRows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const changeTypeElement = row.querySelector('.change-type');
            const dateElement = row.querySelectorAll('td')[1]; // Second column (Date)

            if (!changeTypeElement || !dateElement) return;

            const rowChangeType = changeTypeElement.textContent;
            const rowDate = dateElement.textContent.split(' ')[0];

            const matchesSearch = text.includes(searchTerm);
            const matchesType = !changeType || rowChangeType === changeType;
            const matchesDate = !filterDate || rowDate === filterDate;

            const shouldShow = matchesSearch && matchesType && matchesDate;
            row.style.display = shouldShow ? '' : 'none';

            // Also hide/show corresponding detail row
            const logId = row.getAttribute('data-log-id');
            const detailRow = document.getElementById('details-' + logId);
            if (detailRow) {
                detailRow.style.display = shouldShow && detailRow.style.display === 'table-row' ? 'table-row' : 'none';
            }
        });
    }

    // Add event listeners
    if (searchInput) searchInput.addEventListener('input', filterTable);
    if (changeTypeFilter) changeTypeFilter.addEventListener('change', filterTable);
    if (dateFilter) dateFilter.addEventListener('change', filterTable);
});
