/**
 * VersioningModule.js
 *
 * Assignment Versioning and Lifecycle Management Module
 *
 * This module handles all assignment versioning logic including:
 * - Data series management with version tracking
 * - Assignment resolution based on fiscal year and date
 * - Version lifecycle management (active, superseded, draft)
 * - Conflict detection and resolution
 * - FY-based validation
 *
 * Dependencies: ServicesModule, AppState, AppEvents
 *
 * @version 1.0.0
 * @date 2025-01-30
 */

(function() {
    'use strict';

    // Module-level state
    const state = {
        versionCache: new Map(),           // Cache for version objects
        resolutionCache: new Map(),        // Cache for resolution results
        conflictRegistry: new Map(),       // Track detected conflicts
        activeSeries: new Map(),           // Track active series IDs
        initialized: false
    };

    // Cache configuration
    const CACHE_CONFIG = {
        maxSize: 1000,                     // Maximum cache entries
        ttl: 300000,                       // Time to live: 5 minutes
        resolutionTTL: 180000              // Resolution cache: 3 minutes
    };

    /**
     * Initialize the VersioningModule
     */
    function init() {
        if (state.initialized) {
            console.warn('[VersioningModule] Already initialized');
            return;
        }

        console.log('[VersioningModule] Initializing...');

        // Set up event listeners
        setupEventListeners();

        // Initialize cache cleanup
        startCacheCleanup();

        state.initialized = true;
        console.log('[VersioningModule] Initialization complete');
    }

    /**
     * Set up event listeners for cross-module communication
     */
    function setupEventListeners() {
        if (!window.AppEvents) {
            console.error('[VersioningModule] AppEvents not available');
            return;
        }

        // Listen for assignment save events
        window.AppEvents.on('assignment-saved', handleAssignmentSaved);

        // Listen for assignment delete events
        window.AppEvents.on('assignment-deleted', handleAssignmentDeleted);

        // Listen for FY configuration changes
        window.AppEvents.on('fy-config-changed', handleFYConfigChanged);

        // Listen for configuration changes that may trigger versioning
        window.AppEvents.on('state-configuration-changed', handleConfigurationChanged);

        console.log('[VersioningModule] Event listeners registered');
    }

    /**
     * Create a new assignment version
     *
     * @param {Object} assignmentData - Assignment configuration data
     * @param {string} assignmentData.field_id - Framework field ID
     * @param {number} assignmentData.entity_id - Entity ID
     * @param {string} assignmentData.frequency - Data collection frequency
     * @param {string} assignmentData.unit - Unit override (optional)
     * @param {Object} options - Additional options
     * @param {string} options.reason - Reason for version creation
     * @param {string} options.existingAssignmentId - ID of assignment to version
     * @returns {Promise<Object>} Created version information
     */
    async function createAssignmentVersion(assignmentData, options = {}) {
        console.log('[VersioningModule] Creating assignment version:', assignmentData);

        try {
            // Validate input data
            const validation = validateAssignmentData(assignmentData);
            if (!validation.isValid) {
                throw new Error(`Invalid assignment data: ${validation.error}`);
            }

            // Check for existing active assignment
            const existingAssignment = options.existingAssignmentId
                ? await getAssignmentById(options.existingAssignmentId)
                : await findActiveAssignment(assignmentData.field_id, assignmentData.entity_id);

            let versionData;

            if (existingAssignment) {
                // Create new version of existing assignment
                versionData = await createNewVersion(existingAssignment, assignmentData, options);
            } else {
                // Create first version (v1) of new assignment
                versionData = await createFirstVersion(assignmentData, options);
            }

            // Update caches
            updateVersionCache(versionData);

            // Emit event for other modules
            if (window.AppEvents) {
                window.AppEvents.emit('version-created', {
                    versionId: versionData.id,
                    seriesId: versionData.data_series_id,
                    version: versionData.series_version,
                    fieldId: versionData.field_id,
                    entityId: versionData.entity_id
                });
            }

            console.log('[VersioningModule] Version created successfully:', versionData);
            return {
                success: true,
                version: versionData
            };

        } catch (error) {
            console.error('[VersioningModule] Error creating version:', error);
            throw error;
        }
    }

    /**
     * Create the first version (v1) of a new assignment
     */
    async function createFirstVersion(assignmentData, options) {
        console.log('[VersioningModule] Creating first version (v1)');

        const data_series_id = generateSeriesId();

        const versionPayload = {
            ...assignmentData,
            data_series_id: data_series_id,
            series_version: 1,
            series_status: 'active',
            reason: options.reason || 'Initial assignment creation'
        };

        // Call API to create assignment
        const response = await window.ServicesModule.apiCall(
            '/api/assignments/version/create',
            {
                method: 'POST',
                body: JSON.stringify(versionPayload)
            }
        );

        return response.assignment;
    }

    /**
     * Create a new version of an existing assignment
     */
    async function createNewVersion(existingAssignment, assignmentData, options) {
        console.log('[VersioningModule] Creating new version, current version:', existingAssignment.series_version);

        // First, supersede the previous version
        await supersedePreviousVersion(existingAssignment.id);

        // Create new version with incremented version number
        const versionPayload = {
            ...assignmentData,
            data_series_id: existingAssignment.data_series_id,
            series_version: existingAssignment.series_version + 1,
            series_status: 'active',
            reason: options.reason || 'Assignment configuration updated'
        };

        // Call API to create assignment
        const response = await window.ServicesModule.apiCall(
            '/api/assignments/version/create',
            {
                method: 'POST',
                body: JSON.stringify(versionPayload)
            }
        );

        return response.assignment;
    }

    /**
     * Mark a previous version as superseded
     *
     * @param {string} assignmentId - ID of assignment to supersede
     * @returns {Promise<Object>} Supersession result
     */
    async function supersedePreviousVersion(assignmentId) {
        console.log('[VersioningModule] Superseding assignment:', assignmentId);

        try {
            const response = await window.ServicesModule.apiCall(
                `/api/assignments/version/${assignmentId}/supersede`,
                {
                    method: 'PUT'
                }
            );

            // Invalidate caches for this assignment
            invalidateAssignmentCache(assignmentId);

            // Emit event
            if (window.AppEvents) {
                window.AppEvents.emit('version-superseded', {
                    assignmentId: assignmentId,
                    supersededAt: new Date().toISOString()
                });
            }

            console.log('[VersioningModule] Assignment superseded successfully');
            return response;

        } catch (error) {
            console.error('[VersioningModule] Error superseding assignment:', error);
            throw error;
        }
    }

    /**
     * Resolve the active assignment for a given field, entity, and date
     *
     * @param {string} fieldId - Framework field ID
     * @param {number} entityId - Entity ID
     * @param {Date|string} date - Target date for resolution
     * @returns {Promise<Object|null>} Resolved assignment or null
     */
    async function resolveActiveAssignment(fieldId, entityId, date = null) {
        const targetDate = date ? new Date(date) : new Date();
        const cacheKey = getResolutionCacheKey(fieldId, entityId, targetDate);

        // Check cache first
        const cached = getFromResolutionCache(cacheKey);
        if (cached !== undefined) {
            console.log('[VersioningModule] Resolution cache hit');
            return cached;
        }

        console.log('[VersioningModule] Resolving assignment for:', { fieldId, entityId, date: targetDate });

        try {
            const response = await window.ServicesModule.apiCall(
                '/api/assignments/resolve',
                {
                    method: 'POST',
                    body: JSON.stringify({
                        field_id: fieldId,
                        entity_id: entityId,
                        date: targetDate.toISOString().split('T')[0]
                    })
                }
            );

            const assignment = response.assignment || null;

            // Cache the result
            setInResolutionCache(cacheKey, assignment);

            // Emit event
            if (window.AppEvents) {
                window.AppEvents.emit('resolution-changed', {
                    fieldId,
                    entityId,
                    date: targetDate,
                    assignment: assignment
                });
            }

            return assignment;

        } catch (error) {
            console.error('[VersioningModule] Error resolving assignment:', error);

            // Cache negative result to avoid repeated failed lookups
            setInResolutionCache(cacheKey, null);
            return null;
        }
    }

    /**
     * Get assignment version for a specific date
     *
     * @param {string} seriesId - Data series ID
     * @param {Date|string} date - Target date
     * @returns {Promise<Object|null>} Assignment version or null
     */
    async function getVersionForDate(seriesId, date) {
        const targetDate = new Date(date);
        console.log('[VersioningModule] Getting version for date:', { seriesId, date: targetDate });

        try {
            const response = await window.ServicesModule.apiCall(
                `/api/assignments/series/${seriesId}/versions`,
                {
                    method: 'GET'
                }
            );

            const versions = response.versions || [];

            // Find the version that covers this date
            // This would need proper date range logic based on FY
            const activeVersion = versions.find(v =>
                v.series_status === 'active' &&
                isDateInVersionRange(targetDate, v)
            );

            return activeVersion || null;

        } catch (error) {
            console.error('[VersioningModule] Error getting version for date:', error);
            return null;
        }
    }

    /**
     * Update version status
     *
     * @param {string} versionId - Assignment ID
     * @param {string} newStatus - New status (active, superseded, draft)
     * @returns {Promise<Object>} Updated version
     */
    async function updateVersionStatus(versionId, newStatus) {
        console.log('[VersioningModule] Updating version status:', { versionId, newStatus });

        // Validate status transition
        const validation = validateStatusTransition(null, newStatus);
        if (!validation.isValid) {
            throw new Error(`Invalid status transition: ${validation.error}`);
        }

        try {
            const response = await window.ServicesModule.apiCall(
                `/api/assignments/version/${versionId}/status`,
                {
                    method: 'PUT',
                    body: JSON.stringify({ status: newStatus })
                }
            );

            // Invalidate caches
            invalidateAssignmentCache(versionId);

            // Emit event
            if (window.AppEvents) {
                window.AppEvents.emit('version-activated', {
                    versionId: versionId,
                    status: newStatus
                });
            }

            return response;

        } catch (error) {
            console.error('[VersioningModule] Error updating version status:', error);
            throw error;
        }
    }

    /**
     * Detect version conflicts for an assignment
     *
     * @param {Object} assignmentData - Assignment data to check
     * @returns {Promise<Object>} Conflict detection result
     */
    async function detectVersionConflicts(assignmentData) {
        console.log('[VersioningModule] Detecting conflicts for:', assignmentData);

        try {
            // Check for existing active assignments with overlapping dates
            const existingAssignment = await findActiveAssignment(
                assignmentData.field_id,
                assignmentData.entity_id
            );

            if (!existingAssignment) {
                return { hasConflict: false };
            }

            // Check for date range overlaps
            const dateOverlap = checkDateRangeOverlap(existingAssignment, assignmentData);

            if (dateOverlap) {
                const conflict = {
                    hasConflict: true,
                    type: 'date_overlap',
                    existingAssignment: existingAssignment,
                    message: 'An active assignment already exists for this field and entity with overlapping dates',
                    resolution: 'supersede_existing'
                };

                // Store in conflict registry
                const conflictKey = `${assignmentData.field_id}:${assignmentData.entity_id}`;
                state.conflictRegistry.set(conflictKey, conflict);

                // Emit event
                if (window.AppEvents) {
                    window.AppEvents.emit('version-conflict', conflict);
                }

                return conflict;
            }

            return { hasConflict: false };

        } catch (error) {
            console.error('[VersioningModule] Error detecting conflicts:', error);
            return { hasConflict: false, error: error.message };
        }
    }

    /**
     * Check fiscal year compatibility
     *
     * @param {Object} assignmentData - Assignment data
     * @returns {Promise<Object>} FY compatibility result
     */
    async function checkFYCompatibility(assignmentData) {
        console.log('[VersioningModule] Checking FY compatibility');

        try {
            // Get company FY configuration
            const fyConfig = await getFYConfiguration();

            if (!fyConfig) {
                console.warn('[VersioningModule] No FY configuration found');
                return { isCompatible: true, warning: 'No FY configuration available' };
            }

            // Validate assignment dates against FY
            const validation = validateDateInFY(assignmentData.start_date, fyConfig);

            if (!validation.isValid) {
                // Emit warning event
                if (window.AppEvents) {
                    window.AppEvents.emit('fy-validation-warning', {
                        assignmentData,
                        fyConfig,
                        message: validation.message
                    });
                }
            }

            return validation;

        } catch (error) {
            console.error('[VersioningModule] Error checking FY compatibility:', error);
            return { isCompatible: true, error: error.message };
        }
    }

    /**
     * Validate if a date falls within fiscal year
     *
     * @param {Date|string} date - Date to validate
     * @param {Object} fyConfig - Fiscal year configuration
     * @returns {Object} Validation result
     */
    function validateDateInFY(date, fyConfig) {
        if (!date || !fyConfig) {
            return { isValid: true };
        }

        const targetDate = new Date(date);
        const fyStart = new Date(fyConfig.fy_start_date);
        const fyEnd = new Date(fyConfig.fy_end_date);

        const isValid = targetDate >= fyStart && targetDate <= fyEnd;

        return {
            isValid,
            message: isValid
                ? 'Date is within fiscal year'
                : `Date ${date} is outside fiscal year range (${fyConfig.fy_start_date} to ${fyConfig.fy_end_date})`
        };
    }

    // ===========================
    // Helper Functions
    // ===========================

    /**
     * Find active assignment for field+entity combination
     */
    async function findActiveAssignment(fieldId, entityId) {
        try {
            const response = await window.ServicesModule.apiCall(
                `/api/assignments/by-field/${fieldId}?entity_id=${entityId}&status=active`,
                {
                    method: 'GET'
                }
            );

            const assignments = response.assignments || [];
            return assignments.find(a =>
                a.entity_id === entityId &&
                a.series_status === 'active'
            );

        } catch (error) {
            console.error('[VersioningModule] Error finding active assignment:', error);
            return null;
        }
    }

    /**
     * Get assignment by ID
     */
    async function getAssignmentById(assignmentId) {
        try {
            const response = await window.ServicesModule.apiCall(
                `/api/assignments/${assignmentId}`,
                {
                    method: 'GET'
                }
            );

            return response.assignment;

        } catch (error) {
            console.error('[VersioningModule] Error getting assignment:', error);
            return null;
        }
    }

    /**
     * Get company fiscal year configuration
     */
    async function getFYConfiguration() {
        try {
            const response = await window.ServicesModule.apiCall(
                '/admin/api/company/fy-config',
                {
                    method: 'GET'
                }
            );

            return response.fy_config;

        } catch (error) {
            console.error('[VersioningModule] Error getting FY config:', error);
            return null;
        }
    }

    /**
     * Generate a new series ID (UUID v4)
     */
    function generateSeriesId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * Validate assignment data
     */
    function validateAssignmentData(data) {
        if (!data.field_id) {
            return { isValid: false, error: 'field_id is required' };
        }
        if (!data.entity_id) {
            return { isValid: false, error: 'entity_id is required' };
        }
        if (!data.frequency) {
            return { isValid: false, error: 'frequency is required' };
        }

        return { isValid: true };
    }

    /**
     * Validate version status transition
     */
    function validateStatusTransition(currentStatus, newStatus) {
        const validStatuses = ['active', 'superseded', 'draft'];

        if (!validStatuses.includes(newStatus)) {
            return { isValid: false, error: `Invalid status: ${newStatus}` };
        }

        // Prevent superseded -> active transition
        if (currentStatus === 'superseded' && newStatus === 'active') {
            return { isValid: false, error: 'Cannot reactivate superseded version' };
        }

        return { isValid: true };
    }

    /**
     * Check if date ranges overlap
     */
    function checkDateRangeOverlap(assignment1, assignment2) {
        // Simplified overlap check - in production would use proper date range logic
        if (!assignment1.start_date || !assignment2.start_date) {
            return false;
        }

        const start1 = new Date(assignment1.start_date);
        const start2 = new Date(assignment2.start_date);
        const end1 = assignment1.end_date ? new Date(assignment1.end_date) : new Date('2099-12-31');
        const end2 = assignment2.end_date ? new Date(assignment2.end_date) : new Date('2099-12-31');

        return (start1 <= end2 && start2 <= end1);
    }

    /**
     * Check if date is within version range
     */
    function isDateInVersionRange(date, version) {
        const targetDate = new Date(date);
        const startDate = version.start_date ? new Date(version.start_date) : new Date('1900-01-01');
        const endDate = version.end_date ? new Date(version.end_date) : new Date('2099-12-31');

        return targetDate >= startDate && targetDate <= endDate;
    }

    // ===========================
    // Cache Management
    // ===========================

    /**
     * Update version cache
     */
    function updateVersionCache(versionData) {
        if (!versionData || !versionData.id) return;

        // Enforce cache size limit
        if (state.versionCache.size >= CACHE_CONFIG.maxSize) {
            const firstKey = state.versionCache.keys().next().value;
            state.versionCache.delete(firstKey);
        }

        state.versionCache.set(versionData.id, {
            data: versionData,
            timestamp: Date.now()
        });

        // Track active series
        if (versionData.data_series_id && versionData.series_status === 'active') {
            state.activeSeries.set(versionData.data_series_id, versionData.id);
        }
    }

    /**
     * Get resolution cache key
     */
    function getResolutionCacheKey(fieldId, entityId, date) {
        const dateStr = date.toISOString().split('T')[0];
        return `${fieldId}:${entityId}:${dateStr}`;
    }

    /**
     * Get from resolution cache
     */
    function getFromResolutionCache(key) {
        const cached = state.resolutionCache.get(key);

        if (!cached) return undefined;

        // Check if cache entry is still valid (TTL)
        if (Date.now() - cached.timestamp > CACHE_CONFIG.resolutionTTL) {
            state.resolutionCache.delete(key);
            return undefined;
        }

        return cached.data;
    }

    /**
     * Set in resolution cache
     */
    function setInResolutionCache(key, data) {
        // Enforce cache size limit
        if (state.resolutionCache.size >= CACHE_CONFIG.maxSize) {
            const firstKey = state.resolutionCache.keys().next().value;
            state.resolutionCache.delete(firstKey);
        }

        state.resolutionCache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    /**
     * Invalidate assignment cache
     */
    function invalidateAssignmentCache(assignmentId) {
        // Remove from version cache
        state.versionCache.delete(assignmentId);

        // Clear resolution cache (simplified - in production would be more targeted)
        state.resolutionCache.clear();

        console.log('[VersioningModule] Cache invalidated for assignment:', assignmentId);
    }

    /**
     * Clear all caches
     */
    function clearAllCaches() {
        state.versionCache.clear();
        state.resolutionCache.clear();
        state.conflictRegistry.clear();
        state.activeSeries.clear();
        console.log('[VersioningModule] All caches cleared');
    }

    /**
     * Start periodic cache cleanup
     */
    function startCacheCleanup() {
        setInterval(() => {
            const now = Date.now();

            // Clean version cache
            for (const [key, value] of state.versionCache.entries()) {
                if (now - value.timestamp > CACHE_CONFIG.ttl) {
                    state.versionCache.delete(key);
                }
            }

            // Clean resolution cache
            for (const [key, value] of state.resolutionCache.entries()) {
                if (now - value.timestamp > CACHE_CONFIG.resolutionTTL) {
                    state.resolutionCache.delete(key);
                }
            }

        }, 60000); // Run every minute
    }

    // ===========================
    // Event Handlers
    // ===========================

    function handleAssignmentSaved(data) {
        console.log('[VersioningModule] Assignment saved event:', data);

        // Invalidate related caches
        if (data.assignmentId) {
            invalidateAssignmentCache(data.assignmentId);
        }
    }

    function handleAssignmentDeleted(data) {
        console.log('[VersioningModule] Assignment deleted event:', data);

        if (data.assignmentId) {
            invalidateAssignmentCache(data.assignmentId);
        }
    }

    function handleFYConfigChanged(data) {
        console.log('[VersioningModule] FY config changed event:', data);

        // Clear resolution cache as FY changes affect date validation
        state.resolutionCache.clear();
    }

    function handleConfigurationChanged(data) {
        console.log('[VersioningModule] Configuration changed event:', data);

        // This might trigger version creation in the future
        // For now, just log it
    }

    // ===========================
    // Public API
    // ===========================

    window.VersioningModule = {
        // Initialization
        init,

        // Version Management
        createAssignmentVersion,
        supersedePreviousVersion,
        updateVersionStatus,

        // Resolution
        resolveActiveAssignment,
        getVersionForDate,

        // Validation
        detectVersionConflicts,
        checkFYCompatibility,
        validateDateInFY,

        // Cache Management
        clearAllCaches,

        // Utilities
        generateSeriesId,

        // For testing/debugging
        _state: state,
        _getResolutionCacheKey: getResolutionCacheKey
    };

    console.log('[VersioningModule] Module loaded');

})();