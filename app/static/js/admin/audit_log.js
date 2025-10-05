document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const changeTypeFilter = document.getElementById('changeTypeFilter');
    const dateFilter = document.getElementById('dateFilter');
    const tableRows = document.querySelectorAll('.audit-table tbody tr');

    function filterTable() {
        const searchTerm = searchInput.value.toLowerCase();
        const changeType = changeTypeFilter.value;
        const filterDate = dateFilter.value;

        tableRows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const rowChangeType = row.querySelector('.change-type').textContent;
            const rowDate = row.querySelector('td').textContent.split(' ')[0];

            const matchesSearch = text.includes(searchTerm);
            const matchesType = !changeType || rowChangeType === changeType;
            const matchesDate = !filterDate || rowDate === filterDate;

            row.style.display = matchesSearch && matchesType && matchesDate ? '' : 'none';
        });
    }

    // Add event listeners
    searchInput.addEventListener('input', filterTable);
    changeTypeFilter.addEventListener('change', filterTable);
    dateFilter.addEventListener('change', filterTable);
});
