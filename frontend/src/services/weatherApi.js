/**
 * Weather API Client
 *
 * Handles communication with the backend weather service including:
 * - API requests with proper error handling
 * - Retry logic with exponential backoff
 * - Browser-side caching respecting backend cache TTL
 * - Request timeout and abort handling
 */

// Configuration constants
const API_CONFIG = {
  // Base URL will be set from window config (injected by Terraform) or environment or default to relative path
  BASE_URL: (window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) || process.env.REACT_APP_API_BASE_URL || '',
  ENDPOINTS: {
    WEATHER: '/weather',
    HEALTH: '/health'
  },
  TIMEOUT: 10000, // 10 seconds
  MAX_RETRIES: 5, // Maximum of 5 retries for 5xx errors
  RETRY_DELAY_BASE: 1000, // 1 second base delay
  CACHE_DURATION: 60 * 60 * 1000, // 1 hour in milliseconds (matching backend)
  CACHE_KEY_PREFIX: 'weather_cache_'
};

/**
 * Custom error class for API-related errors
 */
export class WeatherAPIError extends Error {
  constructor(message, status = null, type = 'APIError') {
    super(message);
    this.name = 'WeatherAPIError';
    this.status = status;
    this.type = type;
    this.timestamp = new Date().toISOString();
  }
}

/**
 * Browser cache manager for weather data
 */
class WeatherCache {
  constructor() {
    this.storage = window.localStorage;
    this.keyPrefix = API_CONFIG.CACHE_KEY_PREFIX;
  }

  /**
   * Generate cache key for weather data
   */
  getCacheKey(endpoint) {
    return `${this.keyPrefix}${endpoint}`;
  }

  /**
   * Store data in cache with TTL
   */
  set(endpoint, data, ttl = API_CONFIG.CACHE_DURATION) {
    try {
      const cacheEntry = {
        data,
        timestamp: Date.now(),
        ttl,
        expiresAt: Date.now() + ttl
      };

      this.storage.setItem(
        this.getCacheKey(endpoint),
        JSON.stringify(cacheEntry)
      );

      console.log(`Cached data for ${endpoint}, expires at:`, new Date(cacheEntry.expiresAt));
    } catch (error) {
      console.warn('Failed to cache data:', error);
      // Continue without caching if localStorage is unavailable
    }
  }

  /**
   * Retrieve data from cache if not expired
   */
  get(endpoint) {
    try {
      const cached = this.storage.getItem(this.getCacheKey(endpoint));
      if (!cached) {
        return null;
      }

      const cacheEntry = JSON.parse(cached);
      const now = Date.now();

      // Check if cache entry is expired
      if (now > cacheEntry.expiresAt) {
        console.log(`Cache expired for ${endpoint}`);
        this.delete(endpoint);
        return null;
      }

      console.log(`Cache hit for ${endpoint}, expires in:`, Math.round((cacheEntry.expiresAt - now) / 1000), 'seconds');
      return cacheEntry.data;
    } catch (error) {
      console.warn('Failed to retrieve cached data:', error);
      return null;
    }
  }

  /**
   * Delete cached data
   */
  delete(endpoint) {
    try {
      this.storage.removeItem(this.getCacheKey(endpoint));
    } catch (error) {
      console.warn('Failed to delete cached data:', error);
    }
  }

  /**
   * Clear all weather cache entries
   */
  clear() {
    try {
      const keys = Object.keys(this.storage);
      keys.forEach(key => {
        if (key.startsWith(this.keyPrefix)) {
          this.storage.removeItem(key);
        }
      });
      console.log('Weather cache cleared');
    } catch (error) {
      console.warn('Failed to clear cache:', error);
    }
  }

  /**
   * Check if data is cached and not expired
   */
  has(endpoint) {
    return this.get(endpoint) !== null;
  }
}

/**
 * HTTP client with retry logic and timeout handling
 */
class HTTPClient {
  constructor() {
    this.activeRequests = new Map();
  }

  /**
   * Sleep utility for retry delays
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Calculate exponential backoff delay
   */
  getRetryDelay(attempt) {
    return API_CONFIG.RETRY_DELAY_BASE * Math.pow(2, attempt) + Math.random() * 1000;
  }

  /**
   * Check if error is retryable
   */
  isRetryableError(error) {
    // Retry on network errors, timeouts, and 5xx server errors
    if (!error.status) return true; // Network error
    if (error.status >= 500) return true; // Server error
    if (error.status === 429) return true; // Rate limited
    return false;
  }

  /**
   * Make HTTP request with retry logic
   */
  async request(url, options = {}) {
    const requestId = `${options.method || 'GET'}_${url}_${Date.now()}`;

    // Cancel any existing request to the same endpoint
    if (this.activeRequests.has(url)) {
      this.activeRequests.get(url).abort();
    }

    // Create abort controller for this request
    const abortController = new AbortController();
    this.activeRequests.set(url, abortController);

    const requestOptions = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers
      },
      signal: abortController.signal,
      ...options
    };

    let lastError;

    for (let attempt = 0; attempt <= API_CONFIG.MAX_RETRIES; attempt++) {
      try {
        console.log(`Making request to ${url} (attempt ${attempt + 1}/${API_CONFIG.MAX_RETRIES + 1})`);

        // Set up timeout
        const timeoutId = setTimeout(() => {
          abortController.abort();
        }, API_CONFIG.TIMEOUT);

        const response = await fetch(url, requestOptions);
        clearTimeout(timeoutId);

        // Remove from active requests
        this.activeRequests.delete(url);

        // Handle HTTP errors
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          const error = new WeatherAPIError(
            errorData.error?.message || `HTTP ${response.status}: ${response.statusText}`,
            response.status,
            errorData.error?.type || 'HTTPError'
          );

          // Check if we should retry
          if (attempt < API_CONFIG.MAX_RETRIES && this.isRetryableError(error)) {
            lastError = error;
            const delay = this.getRetryDelay(attempt);
            console.warn(`Request failed, retrying in ${delay}ms:`, error.message);
            await this.sleep(delay);
            continue;
          }

          throw error;
        }

        // Parse response
        const data = await response.json();
        console.log(`Request successful to ${url}`);
        return data;

      } catch (error) {
        // Remove from active requests on error
        this.activeRequests.delete(url);

        // Handle abort
        if (error.name === 'AbortError') {
          throw new WeatherAPIError('Request was cancelled', null, 'AbortError');
        }

        // Handle network errors
        if (error instanceof TypeError && error.message.includes('fetch')) {
          error = new WeatherAPIError('Network error - please check your connection', null, 'NetworkError');
        }

        // Convert to WeatherAPIError if not already
        if (!(error instanceof WeatherAPIError)) {
          error = new WeatherAPIError(error.message || 'Unknown error occurred', null, 'UnknownError');
        }

        lastError = error;

        // Check if we should retry
        if (attempt < API_CONFIG.MAX_RETRIES && this.isRetryableError(error)) {
          const delay = this.getRetryDelay(attempt);
          console.warn(`Request failed, retrying in ${delay}ms:`, error.message);
          await this.sleep(delay);
          continue;
        }

        // Max retries reached
        console.error(`Request failed after ${attempt + 1} attempts:`, error);
        throw error;
      }
    }

    // This should never be reached, but just in case
    throw lastError || new WeatherAPIError('Request failed after all retries');
  }

  /**
   * Cancel all active requests
   */
  cancelAllRequests() {
    this.activeRequests.forEach(controller => controller.abort());
    this.activeRequests.clear();
  }
}

/**
 * Weather API Client
 */
export class WeatherAPIClient {
  constructor() {
    this.httpClient = new HTTPClient();
    this.cache = new WeatherCache();
    this.baseUrl = API_CONFIG.BASE_URL;
  }

  /**
   * Build full URL for endpoint
   */
  buildUrl(endpoint) {
    return `${this.baseUrl}${endpoint}`;
  }

  /**
   * Fetch weather data for all cities
   */
  async getWeatherData(options = {}) {
    const { useCache = true, forceRefresh = false } = options;
    const endpoint = API_CONFIG.ENDPOINTS.WEATHER;

    try {
      // Check cache first (unless force refresh is requested)
      if (useCache && !forceRefresh) {
        const cachedData = this.cache.get(endpoint);
        if (cachedData) {
          console.log('Returning cached weather data');
          return cachedData;
        }
      }

      // Make API request
      const url = this.buildUrl(endpoint);
      const data = await this.httpClient.request(url);

      // Validate response structure
      if (!data || typeof data !== 'object') {
        throw new WeatherAPIError('Invalid response format from weather service', null, 'ValidationError');
      }

      // Cache the response
      if (useCache) {
        this.cache.set(endpoint, data);
      }

      return data;

    } catch (error) {
      console.error('Error fetching weather data:', error);

      // Try to return cached data as fallback
      if (useCache && !forceRefresh) {
        const cachedData = this.cache.get(endpoint);
        if (cachedData) {
          console.log('Returning stale cached data due to API error');
          return cachedData;
        }
      }

      throw error;
    }
  }

  /**
   * Check API health
   */
  async getHealthStatus() {
    const endpoint = API_CONFIG.ENDPOINTS.HEALTH;
    const url = this.buildUrl(endpoint);

    try {
      const data = await this.httpClient.request(url);
      return data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }

  /**
   * Clear all cached data
   */
  clearCache() {
    this.cache.clear();
  }

  /**
   * Check if weather data is cached
   */
  isWeatherDataCached() {
    return this.cache.has(API_CONFIG.ENDPOINTS.WEATHER);
  }

  /**
   * Cancel all active requests
   */
  cancelRequests() {
    this.httpClient.cancelAllRequests();
  }

  /**
   * Get cache status for debugging
   */
  getCacheStatus() {
    const endpoint = API_CONFIG.ENDPOINTS.WEATHER;
    const cached = this.cache.storage.getItem(this.cache.getCacheKey(endpoint));

    if (!cached) {
      return { cached: false };
    }

    try {
      const cacheEntry = JSON.parse(cached);
      const now = Date.now();
      const timeToExpiry = cacheEntry.expiresAt - now;

      return {
        cached: true,
        expired: timeToExpiry <= 0,
        expiresAt: new Date(cacheEntry.expiresAt),
        timeToExpiry: Math.max(0, Math.round(timeToExpiry / 1000)),
        timestamp: new Date(cacheEntry.timestamp)
      };
    } catch (error) {
      return { cached: false, error: error.message };
    }
  }
}

// Create and export singleton instance
export const weatherApiClient = new WeatherAPIClient();

// Export configuration for testing
export { API_CONFIG };