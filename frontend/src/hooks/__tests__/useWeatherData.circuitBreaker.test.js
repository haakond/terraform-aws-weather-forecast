/**
 * Circuit Breaker and Error Loop Prevention Tests
 *
 * Tests for the circuit breaker pattern, rate limiting, and error threshold
 * detection implemented in the useWeatherData hook.
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useWeatherData } from '../useWeatherData';
import { weatherApiClient, WeatherAPIError } from '../../services/weatherApi';

// Mock the weather API client
jest.mock('../../services/weatherApi');

describe('useWeatherData - Circuit Breaker and Error Prevention', () => {
  let mockGetWeatherData;
  let mockClearCache;
  let mockCancelRequests;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();

    mockGetWeatherData = jest.fn();
    mockClearCache = jest.fn();
    mockCancelRequests = jest.fn();

    weatherApiClient.getWeatherData = mockGetWeatherData;
    weatherApiClient.clearCache = mockClearCache;
    weatherApiClient.cancelRequests = mockCancelRequests;
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Circuit Breaker Pattern', () => {
    it('should open circuit after consecutive failures', async () => {
      const error = new WeatherAPIError('Server error', 500, 'HTTPError');
      mockGetWeatherData.mockRejectedValue(error);

      const { result } = renderHook(() => useWeatherData());

      // Wait for initial load to fail
      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      // Wait for initial failure
      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
        expect(result.current.failureCount).toBe(1);
      });

      // Trigger multiple failures to open circuit using internal fetch (respects safeguards)
      for (let i = 0; i < 4; i++) {
        await act(async () => {
          await result.current._internalFetch(true);
        });

        await waitFor(() => {
          expect(result.current.failureCount).toBe(i + 2); // +1 for initial load, +1 for current fetch
        });
      }

      // Circuit should be open now
      expect(result.current.circuitState).toBe('OPEN');
      expect(result.current.isCircuitOpen).toBe(true);
    });

    it('should prevent requests when circuit is open', async () => {
      const error = new WeatherAPIError('Server error', 500, 'HTTPError');
      mockGetWeatherData.mockRejectedValue(error);

      const { result } = renderHook(() => useWeatherData());

      // Wait for initial failure
      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      // Force circuit to open using internal fetch
      await act(async () => {
        for (let i = 0; i < 4; i++) {
          try {
            await result.current._internalFetch(true);
          } catch (e) {
            // Expected to fail
          }
        }
      });

      await waitFor(() => {
        expect(result.current.circuitState).toBe('OPEN');
      });

      // Reset mock call count
      mockGetWeatherData.mockClear();

      // Try to fetch data - should be blocked by circuit breaker
      await act(async () => {
        // This should not call the API due to circuit breaker
        await result.current._internalFetch();
      });

      // API should not have been called
      expect(mockGetWeatherData).not.toHaveBeenCalled();
      expect(result.current.error?.type).toBe('CircuitBreakerOpen');
    });

    it('should transition to half-open state after timeout', async () => {
      const error = new WeatherAPIError('Server error', 500, 'HTTPError');
      mockGetWeatherData.mockRejectedValue(error);

      const { result } = renderHook(() => useWeatherData());

      // Open the circuit
      await act(async () => {
        for (let i = 0; i < 6; i++) {
          try {
            await result.current.retry();
          } catch (e) {
            // Expected to fail
          }
        }
      });

      await waitFor(() => {
        expect(result.current.circuitState).toBe('OPEN');
      });

      // Fast-forward time to trigger half-open state
      act(() => {
        jest.advanceTimersByTime(60000); // 1 minute timeout
      });

      await waitFor(() => {
        expect(result.current.circuitState).toBe('HALF_OPEN');
      });
    });

    it('should close circuit after successful requests in half-open state', async () => {
      const error = new WeatherAPIError('Server error', 500, 'HTTPError');
      const successData = { cities: [{ cityId: 'oslo', temperature: 20 }] };

      mockGetWeatherData.mockRejectedValue(error);

      const { result } = renderHook(() => useWeatherData());

      // Open the circuit
      await act(async () => {
        for (let i = 0; i < 6; i++) {
          try {
            await result.current.retry();
          } catch (e) {
            // Expected to fail
          }
        }
      });

      // Transition to half-open
      act(() => {
        jest.advanceTimersByTime(60000);
      });

      await waitFor(() => {
        expect(result.current.circuitState).toBe('HALF_OPEN');
      });

      // Mock successful responses
      mockGetWeatherData.mockResolvedValue(successData);

      // Make successful requests to close circuit
      await act(async () => {
        await result.current.retry();
      });

      await act(async () => {
        await result.current.retry();
      });

      await waitFor(() => {
        expect(result.current.circuitState).toBe('CLOSED');
        expect(result.current.successCount).toBeGreaterThanOrEqual(2);
      });
    });

    it('should allow manual reset of circuit breaker', async () => {
      const error = new WeatherAPIError('Server error', 500, 'HTTPError');
      mockGetWeatherData.mockRejectedValue(error);

      const { result } = renderHook(() => useWeatherData());

      // Open the circuit
      await act(async () => {
        for (let i = 0; i < 6; i++) {
          try {
            await result.current.retry();
          } catch (e) {
            // Expected to fail
          }
        }
      });

      await waitFor(() => {
        expect(result.current.circuitState).toBe('OPEN');
      });

      // Manually reset circuit breaker
      await act(async () => {
        result.current.resetCircuitBreaker();
      });

      expect(result.current.circuitState).toBe('CLOSED');
      expect(result.current.failureCount).toBe(0);
      expect(result.current.consecutiveErrors).toBe(0);
    });
  });

  describe('Rate Limiting', () => {
    it('should limit requests when burst limit is exceeded', async () => {
      const successData = { cities: [{ cityId: 'oslo', temperature: 20 }] };
      mockGetWeatherData.mockResolvedValue(successData);

      const { result } = renderHook(() => useWeatherData());

      // Wait for initial load
      await waitFor(() => {
        expect(result.current.weatherData).toBeTruthy();
      });

      // Make rapid requests to trigger burst limit
      await act(async () => {
        for (let i = 0; i < 4; i++) {
          await result.current.refresh();
        }
      });

      await waitFor(() => {
        expect(result.current.isRateLimited).toBe(true);
        expect(result.current.error?.type).toBe('RateLimited');
      });
    });

    it('should reset rate limit after cooldown period', async () => {
      const successData = { cities: [{ cityId: 'oslo', temperature: 20 }] };
      mockGetWeatherData.mockResolvedValue(successData);

      const { result } = renderHook(() => useWeatherData());

      // Trigger rate limiting
      await act(async () => {
        for (let i = 0; i < 4; i++) {
          await result.current.refresh();
        }
      });

      await waitFor(() => {
        expect(result.current.isRateLimited).toBe(true);
      });

      // Fast-forward past cooldown period
      act(() => {
        jest.advanceTimersByTime(5000); // 5 second cooldown
      });

      await waitFor(() => {
        expect(result.current.isRateLimited).toBe(false);
      });
    });

    it('should allow manual reset of rate limiting', async () => {
      const successData = { cities: [{ cityId: 'oslo', temperature: 20 }] };
      mockGetWeatherData.mockResolvedValue(successData);

      const { result } = renderHook(() => useWeatherData());

      // Trigger rate limiting
      await act(async () => {
        for (let i = 0; i < 4; i++) {
          await result.current.refresh();
        }
      });

      await waitFor(() => {
        expect(result.current.isRateLimited).toBe(true);
      });

      // Manually reset rate limit
      await act(async () => {
        result.current.resetRateLimit();
      });

      expect(result.current.isRateLimited).toBe(false);
      expect(result.current.requestsInLastMinute).toBe(0);
    });
  });

  describe('Error Threshold Detection', () => {
    it('should disable auto-retry after consecutive errors', async () => {
      const error = new WeatherAPIError('Network error', null, 'NetworkError');
      mockGetWeatherData.mockRejectedValue(error);

      const { result } = renderHook(() => useWeatherData());

      // Wait for initial load to fail
      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      // Trigger consecutive errors
      await act(async () => {
        await result.current.retry();
      });

      await act(async () => {
        await result.current.retry();
      });

      await waitFor(() => {
        expect(result.current.consecutiveErrors).toBe(3); // Initial + 2 retries
        expect(result.current.autoRetryDisabled).toBe(true);
      });
    });

    it('should reset error count after timeout', async () => {
      const error = new WeatherAPIError('Network error', null, 'NetworkError');
      mockGetWeatherData.mockRejectedValue(error);

      const { result } = renderHook(() => useWeatherData());

      // Trigger consecutive errors to disable auto-retry
      await act(async () => {
        for (let i = 0; i < 3; i++) {
          try {
            await result.current.retry();
          } catch (e) {
            // Expected to fail
          }
        }
      });

      await waitFor(() => {
        expect(result.current.autoRetryDisabled).toBe(true);
      });

      // Fast-forward past reset timeout
      act(() => {
        jest.advanceTimersByTime(120000); // 2 minutes
      });

      await waitFor(() => {
        expect(result.current.consecutiveErrors).toBe(0);
        expect(result.current.autoRetryDisabled).toBe(false);
      });
    });

    it('should not auto-retry when disabled but allow manual retry', async () => {
      const error = new WeatherAPIError('Network error', null, 'NetworkError');
      mockGetWeatherData.mockRejectedValue(error);

      const { result } = renderHook(() => useWeatherData());

      // Disable auto-retry by triggering consecutive errors
      await act(async () => {
        for (let i = 0; i < 3; i++) {
          try {
            await result.current.retry();
          } catch (e) {
            // Expected to fail
          }
        }
      });

      await waitFor(() => {
        expect(result.current.autoRetryDisabled).toBe(true);
      });

      // Clear mock calls
      mockGetWeatherData.mockClear();

      // Trigger another error - should not auto-retry
      await act(async () => {
        await result.current.refresh();
      });

      // Should have made the request but not auto-retried
      expect(mockGetWeatherData).toHaveBeenCalledTimes(1);
    });
  });

  describe('Manual Requests Bypass Safeguards', () => {
    it('should allow manual requests even when circuit is open', async () => {
      const error = new WeatherAPIError('Server error', 500, 'HTTPError');
      const successData = { cities: [{ cityId: 'oslo', temperature: 20 }] };

      mockGetWeatherData.mockRejectedValue(error);

      const { result } = renderHook(() => useWeatherData());

      // Open the circuit
      await act(async () => {
        for (let i = 0; i < 6; i++) {
          try {
            await result.current.retry();
          } catch (e) {
            // Expected to fail
          }
        }
      });

      await waitFor(() => {
        expect(result.current.circuitState).toBe('OPEN');
      });

      // Mock successful response for manual request
      mockGetWeatherData.mockResolvedValue(successData);

      // Manual retry should bypass circuit breaker
      await act(async () => {
        await result.current.retry();
      });

      await waitFor(() => {
        expect(result.current.weatherData).toBeTruthy();
      });
    });

    it('should allow manual requests even when rate limited', async () => {
      const successData = { cities: [{ cityId: 'oslo', temperature: 20 }] };
      mockGetWeatherData.mockResolvedValue(successData);

      const { result } = renderHook(() => useWeatherData());

      // Trigger rate limiting
      await act(async () => {
        for (let i = 0; i < 4; i++) {
          await result.current.refresh();
        }
      });

      await waitFor(() => {
        expect(result.current.isRateLimited).toBe(true);
      });

      // Clear mock calls
      mockGetWeatherData.mockClear();

      // Manual retry should bypass rate limiting
      await act(async () => {
        await result.current.retry();
      });

      // Should have made the API call despite rate limiting
      expect(mockGetWeatherData).toHaveBeenCalled();
    });
  });

  describe('Error Message Enhancement', () => {
    it('should provide context-aware error messages', async () => {
      const error = new WeatherAPIError('Network error', null, 'NetworkError');
      mockGetWeatherData.mockRejectedValue(error);

      const { result } = renderHook(() => useWeatherData());

      // Disable auto-retry
      await act(async () => {
        for (let i = 0; i < 3; i++) {
          try {
            await result.current.retry();
          } catch (e) {
            // Expected to fail
          }
        }
      });

      await waitFor(() => {
        expect(result.current.autoRetryDisabled).toBe(true);
        expect(result.current.getErrorMessage).toContain('Auto-retry has been disabled');
      });
    });

    it('should show circuit breaker timeout in error message', async () => {
      const error = new WeatherAPIError('Server error', 500, 'HTTPError');
      mockGetWeatherData.mockRejectedValue(error);

      const { result } = renderHook(() => useWeatherData());

      // Open circuit
      await act(async () => {
        for (let i = 0; i < 6; i++) {
          try {
            await result.current.retry();
          } catch (e) {
            // Expected to fail
          }
        }
      });

      await waitFor(() => {
        expect(result.current.circuitState).toBe('OPEN');
      });

      // Try to make request (should be blocked)
      await act(async () => {
        await result.current.refresh();
      });

      expect(result.current.getErrorMessage).toContain('Circuit breaker will reset in');
    });
  });
});