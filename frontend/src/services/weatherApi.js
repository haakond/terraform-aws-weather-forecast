/**
 * Simple Weather API Client
 *
 * Simplified client that:
 * - Makes direct requests to Lambda backend only
 * - Fails hard on any communication issues
 * - No browser-side caching
 * - No retry logic (Lambda handles retries)
 * - All 3rd party API requests go through Lambda backend
 */

// Configuration constants
const API_CONFIG = {
  // Base URL will be set from window config (injected by Terraform) or environment or default to relative path
  BASE_URL: (window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) || process.env.REACT_APP_API_BASE_URL || '',
  ENDPOINTS: {
    WEATHER: '/weather',
    HEALTH: '/health'
  },
  TIMEOUT: 10000 // 10 seconds
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
 * Simple Weather API Client
 */
export class WeatherAPIClient {
  constructor() {
    this.baseUrl = API_CONFIG.BASE_URL;
  }

  /**
   * Build full URL for endpoint
   */
  buildUrl(endpoint) {
    return `${this.baseUrl}${endpoint}`;
  }

  /**
   * Make HTTP request - fail hard on any issues
   */
  async request(url, options = {}) {
    const abortController = new AbortController();

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

    // Set up timeout
    const timeoutId = setTimeout(() => {
      abortController.abort();
    }, API_CONFIG.TIMEOUT);

    try {
      const response = await fetch(url, requestOptions);
      clearTimeout(timeoutId);

      // Fail hard on any HTTP errors
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new WeatherAPIError(
          errorData.error?.message || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData.error?.type || 'HTTPError'
        );
      }

      // Parse and return response
      const data = await response.json();

      // Validate response structure
      if (!data || typeof data !== 'object') {
        throw new WeatherAPIError('Invalid response format from weather service', null, 'ValidationError');
      }

      return data;

    } catch (error) {
      clearTimeout(timeoutId);

      // Handle abort/timeout
      if (error.name === 'AbortError') {
        throw new WeatherAPIError('Request timed out', null, 'TimeoutError');
      }

      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new WeatherAPIError('Network error - unable to connect to weather service', null, 'NetworkError');
      }

      // Convert to WeatherAPIError if not already
      if (!(error instanceof WeatherAPIError)) {
        throw new WeatherAPIError(error.message || 'Unknown error occurred', null, 'UnknownError');
      }

      throw error;
    }
  }

  /**
   * Fetch weather data for all cities - fail hard on any issues
   * All 3rd party API requests are handled by the Lambda backend
   */
  async getWeatherData() {
    const url = this.buildUrl(API_CONFIG.ENDPOINTS.WEATHER);
    return await this.request(url);
  }

  /**
   * Check API health - fail hard on any issues
   */
  async getHealthStatus() {
    const url = this.buildUrl(API_CONFIG.ENDPOINTS.HEALTH);
    return await this.request(url);
  }
}

// Create and export singleton instance
export const weatherApiClient = new WeatherAPIClient();

// Export configuration for testing
export { API_CONFIG };