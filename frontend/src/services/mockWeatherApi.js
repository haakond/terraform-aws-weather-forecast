/**
 * Mock Weather API for Development and Testing
 *
 * This mock service simulates the backend API responses for development
 * and testing when the actual backend is not available.
 */

// Mock data that matches the expected backend response format
const MOCK_CITIES_DATA = {
  cities: [
    {
      cityId: 'oslo',
      cityName: 'Oslo',
      country: 'Norway',
      coordinates: { lat: 59.9139, lon: 10.7522 },
      forecast: {
        date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        temperature: {
          value: Math.round(Math.random() * 15 + 5), // 5-20°C
          unit: 'celsius'
        },
        condition: 'partly_cloudy_day',
        description: 'Partly cloudy',
        icon: 'partly_cloudy_day',
        humidity: Math.round(Math.random() * 20 + 60), // 60-80%
        windSpeed: Math.round(Math.random() * 10 + 5) // 5-15 km/h
      },
      lastUpdated: new Date().toISOString(),
      ttl: Math.floor(Date.now() / 1000) + 3600 // 1 hour from now
    },
    {
      cityId: 'paris',
      cityName: 'Paris',
      country: 'France',
      coordinates: { lat: 48.8566, lon: 2.3522 },
      forecast: {
        date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        temperature: {
          value: Math.round(Math.random() * 15 + 10), // 10-25°C
          unit: 'celsius'
        },
        condition: 'clear_day',
        description: 'Sunny',
        icon: 'clear_day',
        humidity: Math.round(Math.random() * 20 + 50), // 50-70%
        windSpeed: Math.round(Math.random() * 15 + 5) // 5-20 km/h
      },
      lastUpdated: new Date().toISOString(),
      ttl: Math.floor(Date.now() / 1000) + 3600
    },
    {
      cityId: 'london',
      cityName: 'London',
      country: 'United Kingdom',
      coordinates: { lat: 51.5074, lon: -0.1278 },
      forecast: {
        date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        temperature: {
          value: Math.round(Math.random() * 12 + 8), // 8-20°C
          unit: 'celsius'
        },
        condition: 'cloudy',
        description: 'Cloudy',
        icon: 'cloudy',
        humidity: Math.round(Math.random() * 20 + 65), // 65-85%
        windSpeed: Math.round(Math.random() * 12 + 8) // 8-20 km/h
      },
      lastUpdated: new Date().toISOString(),
      ttl: Math.floor(Date.now() / 1000) + 3600
    },
    {
      cityId: 'barcelona',
      cityName: 'Barcelona',
      country: 'Spain',
      coordinates: { lat: 41.3851, lon: 2.1734 },
      forecast: {
        date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        temperature: {
          value: Math.round(Math.random() * 15 + 15), // 15-30°C
          unit: 'celsius'
        },
        condition: 'clear_day',
        description: 'Sunny',
        icon: 'clear_day',
        humidity: Math.round(Math.random() * 15 + 45), // 45-60%
        windSpeed: Math.round(Math.random() * 10 + 5) // 5-15 km/h
      },
      lastUpdated: new Date().toISOString(),
      ttl: Math.floor(Date.now() / 1000) + 3600
    }
  ],
  lastUpdated: new Date().toISOString(),
  cities_count: 4,
  requestId: 'mock-request-' + Date.now(),
  version: '1.0.0',
  service: 'weather-forecast-app'
};

const MOCK_HEALTH_DATA = {
  status: 'healthy',
  timestamp: new Date().toISOString(),
  version: '1.0.0',
  service: 'weather-forecast-app',
  requestId: 'mock-health-' + Date.now(),
  environment: {
    company_website: 'example.com',
    aws_region: 'eu-west-1',
    function_name: 'mock-weather-api',
    function_version: '$LATEST',
    memory_limit: 512
  }
};

/**
 * Mock fetch implementation that simulates API responses
 */
export const mockFetch = (url, options = {}) => {
  return new Promise((resolve, reject) => {
    // Simulate network delay
    const delay = Math.random() * 1000 + 500; // 500-1500ms

    setTimeout(() => {
      // Simulate occasional network errors (5% chance)
      if (Math.random() < 0.05) {
        reject(new Error('Network error - simulated failure'));
        return;
      }

      // Handle different endpoints
      if (url.includes('/weather')) {
        // Simulate occasional server errors (2% chance)
        if (Math.random() < 0.02) {
          resolve({
            ok: false,
            status: 500,
            statusText: 'Internal Server Error',
            json: async () => ({
              error: {
                type: 'ServerError',
                message: 'Weather service temporarily unavailable',
                timestamp: new Date().toISOString()
              }
            })
          });
          return;
        }

        // Return successful weather data
        resolve({
          ok: true,
          status: 200,
          json: async () => ({
            ...MOCK_CITIES_DATA,
            // Randomize data slightly for each request
            cities: MOCK_CITIES_DATA.cities.map(city => ({
              ...city,
              forecast: {
                ...city.forecast,
                temperature: {
                  ...city.forecast.temperature,
                  value: city.forecast.temperature.value + Math.round(Math.random() * 4 - 2) // ±2°C variation
                },
                humidity: Math.max(30, Math.min(90, city.forecast.humidity + Math.round(Math.random() * 10 - 5))), // ±5% variation
                windSpeed: Math.max(0, city.forecast.windSpeed + Math.round(Math.random() * 4 - 2)) // ±2 km/h variation
              },
              lastUpdated: new Date().toISOString()
            })),
            lastUpdated: new Date().toISOString(),
            requestId: 'mock-request-' + Date.now()
          })
        });
      } else if (url.includes('/health')) {
        // Return health status
        resolve({
          ok: true,
          status: 200,
          json: async () => ({
            ...MOCK_HEALTH_DATA,
            timestamp: new Date().toISOString(),
            requestId: 'mock-health-' + Date.now()
          })
        });
      } else {
        // Unknown endpoint
        resolve({
          ok: false,
          status: 404,
          statusText: 'Not Found',
          json: async () => ({
            error: {
              type: 'NotFound',
              message: `Path ${url} not found`,
              timestamp: new Date().toISOString()
            }
          })
        });
      }
    }, delay);
  });
};

/**
 * Setup mock fetch for development/testing
 */
export const setupMockApi = () => {
  // Only setup mock in development or test environments
  if (process.env.NODE_ENV === 'development' || process.env.NODE_ENV === 'test') {
    // Store original fetch
    const originalFetch = global.fetch;

    // Replace with mock
    global.fetch = mockFetch;

    console.log('🔧 Mock Weather API enabled for development/testing');

    // Return cleanup function
    return () => {
      global.fetch = originalFetch;
      console.log('🔧 Mock Weather API disabled');
    };
  }

  return () => {}; // No-op cleanup for production
};

/**
 * Check if we should use mock API
 */
export const shouldUseMockApi = () => {
  return process.env.NODE_ENV === 'development' ||
         process.env.NODE_ENV === 'test' ||
         process.env.REACT_APP_USE_MOCK_API === 'true';
};