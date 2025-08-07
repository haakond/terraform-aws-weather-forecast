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
      const cachedData = { ...mockWeatherData, cached: true };
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
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({
          error: {
            message: 'Server error',
            type: 'ServerError'
          }
        }),
      });

      await expect(client.getWeatherData()).rejects.toThrow(WeatherAPIError);
    });

    it('should retry on retryable errors', async () => {
      // First call fails with 500 error
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ error: { message: 'Server error' } }),
      });

      // Second call succeeds
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockWeatherData,
      });

      const result = await client.getWeatherData();

      expect(fetch).toHaveBeenCalledTimes(2);
      expect(result).toEqual(mockWeatherData);
    });

    it('should return cached data as fallback on error', async () => {
      const cachedData = { ...mockWeatherData, cached: true };
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

      await expect(client.getWeatherData()).rejects.toThrow(WeatherAPIError);
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

    it('should handle health check errors', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(client.getHealthStatus()).rejects.toThrow(WeatherAPIError);
    });
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
      expect(isCached).toBe(true);
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

      expect(status.cached).toBe(true);
      expect(status.expired).toBe(false);
      expect(status.expiresAt).toEqual(new Date(expiresAt));
      expect(status.timeToExpiry).toBeGreaterThan(0);
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

      expect(status.cached).toBe(true);
      expect(status.expired).toBe(true);
      expect(status.timeToExpiry).toBe(0);
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