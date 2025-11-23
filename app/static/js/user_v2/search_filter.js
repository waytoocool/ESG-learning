/**
 * Search and Filter Handler
 * Handles search and filtering functionality for the dashboard field cards
 */

class SearchFilterHandler {
    constructor(options = {}) {
        this.searchInputId = options.searchInputId || 'searchMetrics';
        this.filterStatusId = options.filterStatusId || 'filterStatus';
        this.filterCategoryId = options.filterCategoryId || 'filterCategory';
        this.filterFieldTypeId = options.filterFieldTypeId || 'filterFieldType';

        this.init();
    }

    init() {
        this.attachEventListeners();
        console.log('[SearchFilter] Initialized');
    }

    /**
     * Attach event listeners to search and filter inputs
     */
    attachEventListeners() {
        const searchInput = document.getElementById(this.searchInputId);
        const filterStatus = document.getElementById(this.filterStatusId);
        const filterCategory = document.getElementById(this.filterCategoryId);
        const filterFieldType = document.getElementById(this.filterFieldTypeId);

        if (searchInput) searchInput.addEventListener('input', () => this.applyFilters());
        if (filterStatus) filterStatus.addEventListener('change', () => this.applyFilters());
        if (filterCategory) filterCategory.addEventListener('change', () => this.applyFilters());
        if (filterFieldType) filterFieldType.addEventListener('change', () => this.applyFilters());
    }

    /**
     * Apply all filters to field cards
     */
    applyFilters() {
        const searchInput = document.getElementById(this.searchInputId);
        const filterStatus = document.getElementById(this.filterStatusId);
        const filterCategory = document.getElementById(this.filterCategoryId);
        const filterFieldType = document.getElementById(this.filterFieldTypeId);

        const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
        const statusFilter = filterStatus ? filterStatus.value : '';
        const categoryFilter = filterCategory ? filterCategory.value.toLowerCase() : '';
        const fieldTypeFilter = filterFieldType ? filterFieldType.value : '';

        // Filter each field card
        document.querySelectorAll('.field-card').forEach(card => {
            const fieldName = card.dataset.fieldName;
            const status = card.dataset.status;
            const fieldType = card.dataset.fieldType;
            const categorySection = card.closest('.category-section');
            const category = categorySection ? categorySection.dataset.category : '';

            const matchesSearch = !searchTerm || fieldName.includes(searchTerm);
            const matchesStatus = !statusFilter || status === statusFilter;
            const matchesCategory = !categoryFilter || category === categoryFilter;
            const matchesFieldType = !fieldTypeFilter || fieldType === fieldTypeFilter;

            if (matchesSearch && matchesStatus && matchesCategory && matchesFieldType) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });

        // Hide/show category sections if all cards are hidden
        this.updateCategorySections();
    }

    /**
     * Update category section visibility based on visible cards
     */
    updateCategorySections() {
        document.querySelectorAll('.category-section').forEach(section => {
            const visibleCards = section.querySelectorAll('.field-card[style="display: block;"], .field-card:not([style*="display"])');
            if (visibleCards.length === 0) {
                section.style.display = 'none';
            } else {
                section.style.display = 'block';
            }
        });
    }

    /**
     * Reset all filters
     */
    resetFilters() {
        const searchInput = document.getElementById(this.searchInputId);
        const filterStatus = document.getElementById(this.filterStatusId);
        const filterCategory = document.getElementById(this.filterCategoryId);
        const filterFieldType = document.getElementById(this.filterFieldTypeId);

        if (searchInput) searchInput.value = '';
        if (filterStatus) filterStatus.value = '';
        if (filterCategory) filterCategory.value = '';
        if (filterFieldType) filterFieldType.value = '';

        this.applyFilters();
    }
}

// Make available globally
window.SearchFilterHandler = SearchFilterHandler;

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    if (!window.searchFilterHandler) {
        window.searchFilterHandler = new SearchFilterHandler();
    }
});
