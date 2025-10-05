/**
 * Services Module for Assign Data Points - API Calls & Utilities
 * Phase 1: Foundation
 */

window.ServicesModule = {
    // API Base Configuration
    apiBase: '/admin',

    // Generic API call handler
    async apiCall(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        try {
            const response = await fetch(url, {...defaultOptions, ...options});
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`[ServicesModule] API call failed: ${endpoint}`, error);
            this.showMessage(`API Error: ${error.message}`, 'error');
            throw error;
        }
    },

    // BUG FIX: Add cached entities storage
    _cachedEntities: null,

    // Core API Methods (to be populated from legacy code)
    async loadEntities() {
        console.log('[ServicesModule] Loading entities...');
        const entities = await this.apiCall('/get_entities');
        this._cachedEntities = entities; // Cache for getAvailableEntities()
        return entities;
    },

    // BUG FIX: Add synchronous getter for cached entities (used by PopupsModule)
    getAvailableEntities() {
        if (this._cachedEntities === null) {
            console.warn('[ServicesModule] getAvailableEntities() called before entities loaded. Returning empty array.');
            return [];
        }
        return this._cachedEntities;
    },

    async loadFrameworkFields(frameworkId) {
        console.log(`[ServicesModule] Loading framework fields for: ${frameworkId}`);
        return await this.apiCall(`/get_framework_fields/${frameworkId}`);
    },

    async loadAllFields() {
        console.log('[ServicesModule] Loading ALL fields from ALL frameworks...');
        // Load all framework IDs first, then load all fields
        const frameworksResponse = await this.apiCall('/frameworks/list');
        const frameworks = frameworksResponse?.frameworks || [];

        if (frameworks.length === 0) {
            console.warn('[ServicesModule] No frameworks found');
            return [];
        }

        // Load fields from all frameworks in parallel
        const allFieldsPromises = frameworks.map(fw =>
            this.loadFrameworkFields(fw.framework_id || fw.id)
        );

        const allFieldsArrays = await Promise.all(allFieldsPromises);

        // Flatten the array of arrays into a single array
        const allFields = allFieldsArrays.flat().filter(field => field != null);

        console.log(`[ServicesModule] Loaded ${allFields.length} total fields from ${frameworks.length} frameworks`);
        return allFields;
    },

    async loadExistingDataPoints() {
        console.log('[ServicesModule] Loading existing data points...');
        return await this.apiCall('/get_existing_data_points');
    },

    async loadCompanyTopics() {
        console.log('[ServicesModule] Loading company topics...');
        return await this.apiCall('/topics/company_dropdown');
    },

    // Phase 2: Extended API Methods
    async loadExistingDataPointsWithInactive(includeInactive = false) {
        console.log(`[ServicesModule] Loading existing data points (includeInactive: ${includeInactive})...`);
        const includeInactiveParam = includeInactive ? '?include_inactive=true' : '';

        const [dataPointsResponse, assignmentsResponse] = await Promise.all([
            this.apiCall(`/get_existing_data_points${includeInactiveParam}`),
            this.apiCall('/get_data_point_assignments')
        ]);

        return { dataPoints: dataPointsResponse, assignments: assignmentsResponse };
    },

    async loadDataPointAssignments() {
        console.log('[ServicesModule] Loading data point assignments...');
        return await this.apiCall('/get_data_point_assignments');
    },

    async loadAssignmentsByField(fieldId) {
        console.log(`[ServicesModule] Loading assignments for field: ${fieldId}`);
        return await this.apiCall(`/api/assignments/by-field/${fieldId}`);
    },

    async deactivateAssignment(assignmentId) {
        console.log(`[ServicesModule] Deactivating assignment: ${assignmentId}`);
        return await this.apiCall(`/api/assignments/${assignmentId}/deactivate`, {
            method: 'POST'
        });
    },

    async reactivateAssignment(assignmentId) {
        console.log(`[ServicesModule] Reactivating assignment: ${assignmentId}`);
        return await this.apiCall(`/api/assignments/${assignmentId}/reactivate`, {
            method: 'POST'
        });
    },

    async loadUnitCategories() {
        console.log('[ServicesModule] Loading unit categories...');
        return await this.apiCall('/unit_categories');
    },

    async loadFieldData(fieldId) {
        console.log(`[ServicesModule] Loading field data for: ${fieldId}`);
        return await this.apiCall(`/frameworks/get_field_data/${fieldId}`);
    },

    async searchDataPoints(searchParams) {
        console.log('[ServicesModule] Searching data points with params:', searchParams);
        return await this.apiCall(`/frameworks/all_data_points?${searchParams}`);
    },

    async loadDataPointsForTopic(topicId) {
        console.log(`[ServicesModule] Loading data points for topic: ${topicId}`);
        return await this.apiCall(`/frameworks/all_data_points?topic_id=${topicId}`);
    },

    async loadDataPointByFieldId(fieldId) {
        console.log(`[ServicesModule] Loading data point by field ID: ${fieldId}`);
        return await this.apiCall(`/frameworks/all_data_points?field_id=${fieldId}`);
    },

    async saveConfiguration(fieldId, config) {
        console.log(`[ServicesModule] Saving configuration for field: ${fieldId}`);
        return await this.apiCall('/configure_fields', {
            method: 'POST',
            body: JSON.stringify({ field_id: fieldId, ...config })
        });
    },

    async saveEntityAssignments(fieldId, entityIds, config = {}) {
        console.log(`[ServicesModule] Saving entity assignments for field: ${fieldId}`);
        return await this.apiCall('/assign_entities', {
            method: 'POST',
            body: JSON.stringify({
                field_id: fieldId,
                entity_ids: entityIds,
                ...config
            })
        });
    },

    async loadAllDataPointsForExport() {
        console.log('[ServicesModule] Loading all data points for export...');
        return await this.apiCall('/frameworks/all_data_points');
    },

    async loadAssignmentHistory(fieldId, perPage = 50) {
        console.log(`[ServicesModule] Loading assignment history for field: ${fieldId}`);
        return await this.apiCall(`/assignment-history/api/timeline?field_id=${fieldId}&per_page=${perPage}`);
    },

    // Utility Methods
    showMessage(message, type = 'info') {
        console.log(`[ServicesModule] ${type.toUpperCase()}: ${message}`);
        // For Phase 1, just log - will integrate with actual notification system later
        AppEvents.emit('message-shown', {message, type});
    },

    // Helper function for form data
    serializeForm(form) {
        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        return data;
    },

    // Helper function for URL parameters
    getUrlParams() {
        return new URLSearchParams(window.location.search);
    }
};

// Initialize services
document.addEventListener('DOMContentLoaded', function() {
    console.log('[ServicesModule] Services module initialized');
    AppEvents.emit('services-initialized');
});