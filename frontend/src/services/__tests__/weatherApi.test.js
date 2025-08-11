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

    // Removed caching tests since browser-side caching is no longer supported

    it('should fail hard on HTTP errors', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ error: { message: 'Server error' } })
      });

      await expect(client.getWeatherData()).rejects.toThrow('Server error');
    });

    it('should fail hard on network errors', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(client.getWeatherData()).rejects.toThrow('Network error');
    });

    // Removed retry and caching fallback tests since these features are no longer supported

    it('should fail hard on invalid response format', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => null,
      });

      await expect(client.getWeatherData()).rejects.toThrow('Invalid response format from weather service');
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

    it('should fail hard on health check errors', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ error: { message: 'Health check failed' } })
      });

      await expect(client.getHealthStatus()).rejects.toThrow('Health check failed');
    });
  });

  // Removed cache management tests since browser-side caching is no longer supported
});

describe('API_CONFIG', () => {
  it('should have correct configuration values', () => {
    expect(API_CONFIG.BASE_URL).toBe('');
    expect(API_CONFIG.ENDPOINTS.WEATHER).toBe('/weather');
    expect(API_CONFIG.ENDPOINTS.HEALTH).toBe('/health');
    expect(API_CONFIG.TIMEOUT).toBe(10000);
  });
});