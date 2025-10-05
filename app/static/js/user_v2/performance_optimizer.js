/**
 * Performance Optimizer for User V2 Dashboard
 * ============================================
 *
 * Provides performance optimizations for large datasets and complex calculations.
 *
 * Features:
 * - Lazy loading for historical data
 * - Virtual scrolling for long tables
 * - Client-side caching (metadata, historical data)
 * - Debounced calculations
 * - Web Workers for heavy computations
 *
 * Usage:
 *   const optimizer = new PerformanceOptimizer({
 *       enableLazyLoading: true,
 *       enableCaching: true,
 *       enableWebWorkers: true
 *   });
 *   optimizer.initialize();
 */

class PerformanceOptimizer {
    constructor(options = {}) {
        // Configuration
        this.enableLazyLoading = options.enableLazyLoading !== false;
        this.enableCaching = options.enableCaching !== false;
        this.enableWebWorkers = options.enableWebWorkers !== false;
        this.enableVirtualScroll = options.enableVirtualScroll !== false;

        // Cache configuration
        this.cacheConfig = {
            fieldMetadata: 60 * 60 * 1000,      // 1 hour
            historicalData: 30 * 60 * 1000,     // 30 minutes
            dimensionValues: -1,                 // Session (never expire)
            userPreferences: -1                  // Session
        };

        // Debounce configuration
        this.debounceDelay = options.debounceDelay || 300; // 300ms

        // State
        this.cache = new Map();
        this.workers = new Map();
        this.debouncedFunctions = new Map();
        this.observers = new Map();

        // Bind methods
        this.getCached = this.getCached.bind(this);
        this.setCached = this.setCached.bind(this);
        this.debounce = this.debounce.bind(this);
    }

    /**
     * Initialize performance optimizer
     */
    initialize() {
        console.log('Performance Optimizer initialized');

        // Set up lazy loading observers
        if (this.enableLazyLoading) {
            this.setupLazyLoading();
        }

        // Set up virtual scrolling
        if (this.enableVirtualScroll) {
            this.setupVirtualScrolling();
        }

        // Initialize Web Workers
        if (this.enableWebWorkers) {
            this.initializeWebWorkers();
        }

        // Clean up old cache periodically
        this.startCacheCleanup();
    }

    /**
     * Get cached data
     */
    getCached(key) {
        if (!this.enableCaching) return null;

        const cached = this.cache.get(key);

        if (!cached) return null;

        // Check if expired
        if (cached.expiry > 0 && Date.now() > cached.expiry) {
            this.cache.delete(key);
            return null;
        }

        return cached.data;
    }

    /**
     * Set cached data
     */
    setCached(key, data, ttl = null) {
        if (!this.enableCaching) return;

        const cacheType = key.split(':')[0];
        const defaultTTL = this.cacheConfig[cacheType] || 30 * 60 * 1000;

        const expiry = ttl === -1 ? -1 : Date.now() + (ttl || defaultTTL);

        this.cache.set(key, {
            data: data,
            expiry: expiry,
            timestamp: Date.now()
        });
    }

    /**
     * Clear cache
     */
    clearCache(pattern = null) {
        if (pattern) {
            // Clear specific pattern
            for (const [key] of this.cache) {
                if (key.includes(pattern)) {
                    this.cache.delete(key);
                }
            }
        } else {
            // Clear all
            this.cache.clear();
        }
    }

    /**
     * Start cache cleanup timer
     */
    startCacheCleanup() {
        // Run cleanup every 5 minutes
        setInterval(() => {
            const now = Date.now();
            for (const [key, value] of this.cache) {
                if (value.expiry > 0 && now > value.expiry) {
                    this.cache.delete(key);
                }
            }
        }, 5 * 60 * 1000);
    }

    /**
     * Debounce a function
     */
    debounce(func, delay = null) {
        const actualDelay = delay || this.debounceDelay;

        // Create unique key for this function
        const key = func.toString();

        if (!this.debouncedFunctions.has(key)) {
            let timeout = null;

            const debouncedFunc = function (...args) {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    func.apply(this, args);
                }, actualDelay);
            };

            this.debouncedFunctions.set(key, debouncedFunc);
        }

        return this.debouncedFunctions.get(key);
    }

    /**
     * Setup lazy loading with Intersection Observer
     */
    setupLazyLoading() {
        // Create observer for lazy-loading elements
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;

                    // Trigger load
                    const loadEvent = new CustomEvent('lazyload', {
                        detail: { element }
                    });
                    element.dispatchEvent(loadEvent);

                    // Call data-load-function if specified
                    const loadFunc = element.dataset.loadFunction;
                    if (loadFunc && window[loadFunc]) {
                        window[loadFunc](element);
                    }

                    // Unobserve after loading
                    observer.unobserve(element);
                }
            });
        }, {
            rootMargin: '50px' // Load 50px before entering viewport
        });

        this.observers.set('lazyload', observer);

        // Observe all elements with data-lazy-load attribute
        document.querySelectorAll('[data-lazy-load]').forEach(el => {
            observer.observe(el);
        });
    }

    /**
     * Setup virtual scrolling for long tables
     */
    setupVirtualScrolling() {
        const tables = document.querySelectorAll('[data-virtual-scroll]');

        tables.forEach(table => {
            this.applyVirtualScrolling(table);
        });
    }

    /**
     * Apply virtual scrolling to a table
     */
    applyVirtualScrolling(table) {
        const tbody = table.querySelector('tbody');
        if (!tbody) return;

        const rows = Array.from(tbody.querySelectorAll('tr'));
        const rowCount = rows.length;

        // Only apply if many rows
        if (rowCount < 100) return;

        const rowHeight = rows[0]?.offsetHeight || 40;
        const visibleRows = Math.ceil(window.innerHeight / rowHeight) + 5; // Buffer rows

        // Create virtual scroll container
        const container = document.createElement('div');
        container.className = 'virtual-scroll-container';
        container.style.height = `${rowCount * rowHeight}px`;
        container.style.position = 'relative';

        // Create viewport
        const viewport = document.createElement('div');
        viewport.className = 'virtual-scroll-viewport';
        viewport.style.height = '100vh';
        viewport.style.overflow = 'auto';

        // Move table into viewport
        table.parentNode.insertBefore(container, table);
        container.appendChild(viewport);
        viewport.appendChild(table);

        // Render function
        let lastScrollTop = 0;

        const renderVisibleRows = () => {
            const scrollTop = viewport.scrollTop;
            const startIndex = Math.floor(scrollTop / rowHeight);
            const endIndex = Math.min(startIndex + visibleRows, rowCount);

            // Update tbody
            tbody.innerHTML = '';

            for (let i = startIndex; i < endIndex; i++) {
                const row = rows[i].cloneNode(true);
                row.style.position = 'absolute';
                row.style.top = `${i * rowHeight}px`;
                tbody.appendChild(row);
            }

            lastScrollTop = scrollTop;
        };

        // Debounce scroll handler
        const debouncedRender = this.debounce(renderVisibleRows, 50);

        viewport.addEventListener('scroll', debouncedRender);

        // Initial render
        renderVisibleRows();
    }

    /**
     * Initialize Web Workers
     */
    initializeWebWorkers() {
        // Check if Web Workers are supported
        if (typeof Worker === 'undefined') {
            console.warn('Web Workers not supported');
            return;
        }

        // Create calculation worker
        const calculationWorkerCode = `
            self.onmessage = function(e) {
                const { type, data } = e.data;

                switch (type) {
                    case 'sum':
                        const sum = data.reduce((a, b) => a + b, 0);
                        self.postMessage({ type: 'sum', result: sum });
                        break;

                    case 'average':
                        const avg = data.reduce((a, b) => a + b, 0) / data.length;
                        self.postMessage({ type: 'average', result: avg });
                        break;

                    case 'aggregate':
                        // Perform complex aggregation
                        const aggregated = {};
                        data.forEach(item => {
                            const key = item.dimension || 'default';
                            if (!aggregated[key]) {
                                aggregated[key] = 0;
                            }
                            aggregated[key] += item.value || 0;
                        });
                        self.postMessage({ type: 'aggregate', result: aggregated });
                        break;

                    default:
                        self.postMessage({ type: 'error', error: 'Unknown type' });
                }
            };
        `;

        const blob = new Blob([calculationWorkerCode], { type: 'application/javascript' });
        const workerUrl = URL.createObjectURL(blob);
        const worker = new Worker(workerUrl);

        this.workers.set('calculation', worker);
    }

    /**
     * Perform calculation using Web Worker
     */
    async calculateWithWorker(type, data) {
        if (!this.enableWebWorkers) {
            // Fallback to main thread
            return this.calculateOnMainThread(type, data);
        }

        const worker = this.workers.get('calculation');
        if (!worker) {
            return this.calculateOnMainThread(type, data);
        }

        return new Promise((resolve, reject) => {
            worker.onmessage = (e) => {
                const { type: resultType, result, error } = e.data;

                if (error) {
                    reject(new Error(error));
                } else {
                    resolve(result);
                }
            };

            worker.onerror = (error) => {
                reject(error);
            };

            worker.postMessage({ type, data });
        });
    }

    /**
     * Fallback calculation on main thread
     */
    calculateOnMainThread(type, data) {
        switch (type) {
            case 'sum':
                return data.reduce((a, b) => a + b, 0);

            case 'average':
                return data.reduce((a, b) => a + b, 0) / data.length;

            case 'aggregate':
                const aggregated = {};
                data.forEach(item => {
                    const key = item.dimension || 'default';
                    if (!aggregated[key]) {
                        aggregated[key] = 0;
                    }
                    aggregated[key] += item.value || 0;
                });
                return aggregated;

            default:
                throw new Error('Unknown calculation type');
        }
    }

    /**
     * Batch API calls
     */
    async batchApiCalls(calls) {
        // Group calls by endpoint
        const grouped = {};

        calls.forEach(call => {
            const key = `${call.method}:${call.endpoint}`;
            if (!grouped[key]) {
                grouped[key] = [];
            }
            grouped[key].push(call);
        });

        // Execute batches in parallel
        const results = await Promise.all(
            Object.values(grouped).map(batch => {
                // If endpoint supports batch requests, send as batch
                // Otherwise, execute in parallel
                return Promise.all(
                    batch.map(call => fetch(call.endpoint, call.options))
                );
            })
        );

        return results.flat();
    }

    /**
     * Prefetch data for likely next actions
     */
    async prefetchData(predictions) {
        const prefetchPromises = predictions.map(async (prediction) => {
            const { endpoint, cacheKey } = prediction;

            // Check if already cached
            if (this.getCached(cacheKey)) {
                return;
            }

            // Fetch and cache
            try {
                const response = await fetch(endpoint);
                const data = await response.json();
                this.setCached(cacheKey, data);
            } catch (error) {
                console.warn('Prefetch failed:', error);
            }
        });

        await Promise.all(prefetchPromises);
    }

    /**
     * Monitor performance metrics
     */
    monitorPerformance() {
        if (!window.performance || !window.performance.getEntriesByType) {
            return null;
        }

        const navigation = performance.getEntriesByType('navigation')[0];
        const paint = performance.getEntriesByType('paint');

        return {
            pageLoad: navigation?.loadEventEnd - navigation?.fetchStart,
            domReady: navigation?.domContentLoadedEventEnd - navigation?.fetchStart,
            firstPaint: paint.find(p => p.name === 'first-paint')?.startTime,
            firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime
        };
    }

    /**
     * Get cache statistics
     */
    getCacheStats() {
        let totalSize = 0;
        let totalItems = 0;
        const typeStats = {};

        for (const [key, value] of this.cache) {
            const type = key.split(':')[0];

            if (!typeStats[type]) {
                typeStats[type] = { count: 0, size: 0 };
            }

            typeStats[type].count++;

            // Estimate size
            const size = JSON.stringify(value.data).length;
            typeStats[type].size += size;
            totalSize += size;
            totalItems++;
        }

        return {
            totalItems,
            totalSize,
            typeStats
        };
    }

    /**
     * Clean up resources
     */
    cleanup() {
        // Clear cache
        this.cache.clear();

        // Terminate workers
        for (const [key, worker] of this.workers) {
            worker.terminate();
        }
        this.workers.clear();

        // Disconnect observers
        for (const [key, observer] of this.observers) {
            observer.disconnect();
        }
        this.observers.clear();

        console.log('Performance Optimizer cleaned up');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceOptimizer;
}
