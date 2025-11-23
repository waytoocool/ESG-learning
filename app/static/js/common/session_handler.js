/**
 * Session Handler - Detects session expiration and handles redirects
 *
 * This utility handles the common AJAX session expiration issue where:
 * 1. Session expires
 * 2. Server returns 302 redirect to /login
 * 3. Browser follows redirect transparently
 * 4. JavaScript receives HTML login page instead of JSON
 * 5. Parsing HTML as JSON throws error
 *
 * Usage:
 *   const response = await fetch('/api/endpoint', {...});
 *   await handleSessionExpiration(response);
 *   const data = await response.json(); // Safe to parse now
 */

/**
 * Check if response is HTML (indicating possible session expiration)
 * @param {Response} response - Fetch API response object
 * @returns {boolean} - True if response is HTML
 */
function isHtmlResponse(response) {
    const contentType = response.headers.get('content-type');
    return contentType && contentType.includes('text/html');
}

/**
 * Check if HTML content is the login page
 * @param {string} html - HTML content
 * @returns {boolean} - True if it's the login page
 */
function isLoginPage(html) {
    // Check for common login page indicators
    return html.includes('Welcome to ESG Datavault') ||
           html.includes('/login') ||
           html.includes('name="email"') ||
           html.includes('name="password"');
}

/**
 * Handle potential session expiration by checking response type
 * Redirects to login if session has expired
 *
 * @param {Response} response - Fetch API response object
 * @throws {Error} - If response indicates session expiration
 */
async function handleSessionExpiration(response) {
    // If response is not OK, let normal error handling take over
    if (!response.ok) {
        return;
    }

    // Check if we received HTML instead of JSON
    if (isHtmlResponse(response)) {
        // Clone response so we can read it (responses can only be read once)
        const clonedResponse = response.clone();
        const text = await clonedResponse.text();

        // Check if it's the login page
        if (isLoginPage(text)) {
            console.warn('[Session Handler] Session expired - redirecting to login');

            // Store current URL to redirect back after login
            const currentPath = window.location.pathname + window.location.search;

            // Redirect to login with next parameter
            window.location.href = `/login?next=${encodeURIComponent(currentPath)}`;

            // Throw error to prevent further processing
            throw new Error('Session expired - redirecting to login');
        }
    }
}

/**
 * Safe JSON parse that handles session expiration
 * @param {Response} response - Fetch API response object
 * @returns {Promise<any>} - Parsed JSON data
 * @throws {Error} - If session expired or JSON parsing failed
 */
async function safeJsonParse(response) {
    await handleSessionExpiration(response);

    try {
        return await response.json();
    } catch (error) {
        console.error('[Session Handler] Failed to parse JSON:', error);
        throw new Error('Invalid JSON response from server');
    }
}

/**
 * Enhanced fetch wrapper with automatic session handling
 * @param {string} url - Request URL
 * @param {object} options - Fetch options
 * @returns {Promise<any>} - Parsed JSON response
 */
async function fetchWithSessionHandling(url, options = {}) {
    try {
        const response = await fetch(url, options);

        // Handle session expiration
        await handleSessionExpiration(response);

        // Check for HTTP errors
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        // Parse JSON safely
        return await safeJsonParse(response);

    } catch (error) {
        // If error is session expiration, it will redirect automatically
        // Otherwise, propagate the error
        if (error.message !== 'Session expired - redirecting to login') {
            console.error('[Session Handler] Fetch error:', error);
        }
        throw error;
    }
}

// Export functions for use in other modules
window.handleSessionExpiration = handleSessionExpiration;
window.safeJsonParse = safeJsonParse;
window.fetchWithSessionHandling = fetchWithSessionHandling;
