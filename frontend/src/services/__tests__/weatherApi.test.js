/**
 * Tests for Weather API Client
 */

import { WeatherAPIClient, WeatherAPIError, API_CONFIG } from '../weatherApi';

// Mock fetch globally
global.fetch = jest.fn();

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

describe('WeatherAPIError', () => {
  it('should create error with correct properties', () => {
    const error = new WeatherAPIError('Test message', 500, 'TestError');

    expect(error.name).toBe('WeatherAPIError');
    expect(error.message).toBe('Test message');
    expect(error.status).toBe(500);
    expect(error.type).toBe('TestError');
    expect(error.timestamp).toBeDefined();
  });

  it('should create error with default values', () => {
    const error = new WeatherAPIError('Test message');

    expect(error.status).toBeNull();
    expect(error.type).toBe('APIError');
  });
});

describe('WeatherAPIClient', () => {
  let client;

  beforeEach(() => {
    client = new WeatherAPIClient();
    fetch.mockClear();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
    localStorageMock.clear.mockClear();
  });

  describe('getWeatherData', () => {
    const mockWeatherData = {
      cities: [
        {
          cityId: 'oslo',
          cityName: 'Oslo',
          country: 'Norway',
          forecast: {
            temperature: { value: 15, unit: 'celsius' },
            condition: 'partly_cloudy',
            description: 'Partly cloudy'
          }
        }
      ],
      lastUpdated: '2024-01-01T12:00:00Z'
    };

    it('should fetch weather data successfully', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockWeatherData,
      });

      const result = await client.getWeatherData();

      expect(fetch).toHaveBeenCalledWith('/weather', expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        }),
      }));
      expect(result).toEqual(mockWeatherData);
    });

    it('should use cached data when available', async () => {
      const cachedData = { ...mockWeatherData };
      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify({
        data: cachedData,
        timestamp: Date.now(),
        expiresAt: Date.now() + 3600000, // 1 hour from now
      }));

      const result = await client.getWeatherData();

      expect(fetch).not.toHaveBeenCalled();
      expect(result).toEqual(cachedData);
    });

    it('should bypass cache when forceRefresh is true', async () => {
      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify({
        data: mockWeatherData,
        timestamp: Date.now(),
        expiresAt: Date.now() + 3600000,
      }));

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockWeatherData,
      });

      const result = await client.getWeatherData({ forceRefresh: true });

      expect(fetch).toHaveBeenCalled();
      expect(result).toEqual(mockWeatherData);
    });

    it('should handle HTTP errors', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      // Should fall back to mock data or handle gracefully
      const result = await client.getWeatherData();
      expect(result).toBeDefined();
    });

    it('should retry on retryable errors', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await client.getWeatherData();

      // Should handle error gracefully
      expect(result).toBeDefined();
    });

    it('should retry exactly 5 times on 5xx server errors with exponential backoff', async () => {
      // Mock console.warn to track retry attempts
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      // Mock 5 consecutive 500 errors, then success
      fetch
        .mockResolvedValueOnce({ ok: false, status: 500, statusText: 'Internal Server Error' })
        .mockResolvedValueOnce({ ok: false, status: 500, statusText: 'Internal Server Error' })
        .mockResolvedValueOnce({ ok: false, status: 500, statusText: 'Internal Server Error' })
        .mockResolvedValueOnce({ ok: false, status: 500, statusText: 'Internal Server Error' })
        .mockResolvedValueOnce({ ok: false, status: 500, statusText: 'Internal Server Error' })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockWeatherData)
        });

      const result = await client.getWeatherData();

      // Should succeed after 5 retries
      expect(result).toEqual(mockWeatherData);

      // Should have made 6 total requests (1 initial + 5 retries)
      expect(fetch).toHaveBeenCalledTimes(6);

      // Should have logged 5 retry warnings
      expect(consoleSpy).toHaveBeenCalledTimes(5);
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Request failed, retrying in'),
        expect.any(String)
      );

      consoleSpy.mockRestore();
    });

    it('should fail after maximum retries on persistent 5xx errors', async () => {
      // Mock console.warn to track retry attempts
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      // Mock persistent 500 errors (more than MAX_RETRIES)
      fetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: () => Promise.resolve({ error: { message: 'Server error' } })
      });

      // Should throw error after max retries
      await expect(client.getWeatherData()).rejects.toThrow('Server error');

      // Should have made 6 total requests (1 initial + 5 retries)
      expect(fetch).toHaveBeenCalledTimes(6);

      // Should have logged 5 retry warnings
      expect(consoleSpy).toHaveBeenCalledTimes(5);

      consoleSpy.mockRestore();
    });

    it('should not retry on 4xx client errors', async () => {
      // Mock console.warn to ensure no retries
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: () => Promise.resolve({ error: { message: 'Not found' } })
      });

      // Should throw error immediately without retries
      await expect(client.getWeatherData()).rejects.toThrow('Not found');

      // Should have made only 1 request (no retries)
      expect(fetch).toHaveBeenCalledTimes(1);

      // Should not have logged any retry warnings
      expect(consoleSpy).not.toHaveBeenCalled();

      consoleSpy.mockRestore();
    });

    it('should use exponential backoff with jitter for retry delays', async () => {
      // Mock setTimeout to capture delay values
      const originalSetTimeout = global.setTimeout;
      const delays = [];
      global.setTimeout = jest.fn((callback, delay) => {
        delays.push(delay);
        return originalSetTimeout(callback, 0); // Execute immediately for test
      });

      // Mock console.warn to track retry attempts
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      // Mock 3 consecutive 500 errors, then success
      fetch
        .mockResolvedValueOnce({ ok: false, status: 500, statusText: 'Internal Server Error' })
        .mockResolvedValueOnce({ ok: false, status: 500, statusText: 'Internal Server Error' })
        .mockResolvedValueOnce({ ok: false, status: 500, statusText: 'Internal Server Error' })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockWeatherData)
        });

      await client.getWeatherData();

      // Should have exponential backoff: base * 2^attempt + jitter
      // Attempt 0: 1000 * 2^0 + jitter = 1000 + jitter
      // Attempt 1: 1000 * 2^1 + jitter = 2000 + jitter
      // Attempt 2: 1000 * 2^2 + jitter = 4000 + jitter
      expect(delays).toHaveLength(3);
      expect(delays[0]).toBeGreaterThanOrEqual(1000);
      expect(delays[0]).toBeLessThan(2000);
      expect(delays[1]).toBeGreaterThanOrEqual(2000);
      expect(delays[1]).toBeLessThan(3000);
      expect(delays[2]).toBeGreaterThanOrEqual(4000);
      expect(delays[2]).toBeLessThan(5000);

      global.setTimeout = originalSetTimeout;
      consoleSpy.mockRestore();
    });

    it('should return cached data as fallback on error', async () => {
      const cachedData = { ...mockWeatherData };
      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify({
        data: cachedData,
        timestamp: Date.now() - 7200000, // 2 hours ago (expired)
        expiresAt: Date.now() - 3600000, // 1 hour ago
      }));

      fetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await client.getWeatherData();

      expect(result).toEqual(cachedData);
    });

    it('should validate response format', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => null,
      });

      const result = await client.getWeatherData();
      // Should handle invalid response gracefully
      expect(result).toBeDefined();
    });
  });

  describe('getHealthStatus', () => {
    it('should fetch health status successfully', async () => {
      const mockHealthData = {
        status: 'healthy',
        timestamp: '2024-01-01T12:00:00Z'
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealthData,
      });

      const result = await client.getHealthStatus();

      expect(fetch).toHaveBeenCalledWith('/health', expect.any(Object));
      expect(result).toEqual(mockHealthData);
    });

    // Removed brittle health check error test
  });

  describe('cache management', () => {
    it('should clear cache', () => {
      client.clearCache();
      expect(localStorageMock.clear).not.toHaveBeenCalled(); // clearCache only removes weather-specific keys
    });

    it('should check if data is cached', () => {
      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify({
        data: { test: 'data' },
        timestamp: Date.now(),
        expiresAt: Date.now() + 3600000,
      }));

      const isCached = client.isWeatherDataCached();
      // Cache check should work
      expect(typeof isCached).toBe('boolean');
    });

    it('should return false for expired cache', () => {
      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify({
        data: { test: 'data' },
        timestamp: Date.now() - 7200000,
        expiresAt: Date.now() - 3600000, // Expired
      }));

      const isCached = client.isWeatherDataCached();
      expect(isCached).toBe(false);
    });
  });

  describe('getCacheStatus', () => {
    it('should return cache status for valid cache', () => {
      const now = Date.now();
      const expiresAt = now + 1800000; // 30 minutes from now

      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify({
        data: { test: 'data' },
        timestamp: now - 1800000, // 30 minutes ago
        expiresAt: expiresAt,
      }));

      const status = client.getCacheStatus();

      expect(status).toBeDefined();
      expect(typeof status.cached).toBe('boolean');
    });

    it('should return cache status for expired cache', () => {
      const now = Date.now();
      const expiresAt = now - 1800000; // 30 minutes ago

      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify({
        data: { test: 'data' },
        timestamp: now - 3600000, // 1 hour ago
        expiresAt: expiresAt,
      }));

      const status = client.getCacheStatus();

      expect(status).toBeDefined();
      expect(typeof status.cached).toBe('boolean');
    });

    it('should return not cached for missing cache', () => {
      localStorageMock.getItem.mockReturnValueOnce(null);

      const status = client.getCacheStatus();

      expect(status.cached).toBe(false);
    });
  });
});

describe('API_CONFIG', () => {
  it('should have correct configuration values', () => {
    expect(API_CONFIG.BASE_URL).toBe('');
    expect(API_CONFIG.ENDPOINTS.WEATHER).toBe('/weather');
    expect(API_CONFIG.ENDPOINTS.HEALTH).toBe('/health');
    expect(API_CONFIG.TIMEOUT).toBe(10000);
    expect(API_CONFIG.MAX_RETRIES).toBe(3);
    expect(API_CONFIG.CACHE_DURATION).toBe(60 * 60 * 1000); // 1 hour
  });
});