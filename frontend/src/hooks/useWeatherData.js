/**
 * useWeatherData Hook
 *
 * Custom React hook for managing weather data state including:
 * - Data fetching with loading states
 * - Error handling and retry logic
 * - Cache management
 * - Automatic refresh intervals
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { weatherApiClient, WeatherAPIError } from '../services/weatherApi';

// Hook configuration
const HOOK_CONFIG = {
  AUTO_REFRESH_INTERVAL: 5 * 60 * 1000, // 5 minutes
  RETRY_INTERVALS: [2000, 5000], // Progressive retry delays (reduced from 3 to 2 attempts)
  MAX_AUTO_RETRIES: 2, // Reduced since HTTP client already does 5 retries with exponential backoff

  // Circuit breaker configuration
  CIRCUIT_BREAKER: {
    FAILURE_THRESHOLD: 5, // Number of consecutive failures before opening circuit
    SUCCESS_THRESHOLD: 2, // Number of consecutive successes to close circuit
    TIMEOUT: 60000, // 1 minute timeout before trying half-open state
    MAX_TIMEOUT: 300000, // 5 minutes maximum timeout
    BACKOFF_MULTIPLIER: 2 // Exponential backoff multiplier
  },

  // Rate limiting configuration
  RATE_LIMIT: {
    MAX_REQUESTS_PER_MINUTE: 20, // Maximum requests per minute
    BURST_LIMIT: 10, // Maximum burst requests (increased for testing)
    COOLDOWN_PERIOD: 5000 // 5 seconds cooldown after burst limit
  },

  // Error threshold configuration
  ERROR_THRESHOLD: {
    MAX_CONSECUTIVE_ERRORS: 3, // Disable auto-retry after this many consecutive errors
    RESET_TIMEOUT: 120000 // 2 minutes before resetting error count
  }
};

/**
 * Circuit breaker states
 */
const CIRCUIT_STATES = {
  CLOSED: 'CLOSED',     // Normal operation
  OPEN: 'OPEN',         // Circuit is open, requests are blocked
  HALF_OPEN: 'HALF_OPEN' // Testing if service is back up
};

/**
 * Custom hook for weather data management
 */
export const useWeatherData = (options = {}) => {
  const {
    autoRefresh = false, // Disabled by default
    refreshInterval = HOOK_CONFIG.AUTO_REFRESH_INTERVAL,
    enableCache = true,
    onError = null,
    onSuccess = null
  } = options;

  // State management
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  // Circuit breaker state
  const [circuitState, setCircuitState] = useState(CIRCUIT_STATES.CLOSED);
  const [failureCount, setFailureCount] = useState(0);
  const [successCount, setSuccessCount] = useState(0);
  const [lastFailureTime, setLastFailureTime] = useState(null);
  const [circuitTimeout, setCircuitTimeout] = useState(HOOK_CONFIG.CIRCUIT_BREAKER.TIMEOUT);

  // Rate limiting state
  const [requestHistory, setRequestHistory] = useState([]);
  const [isRateLimited, setIsRateLimited] = useState(false);
  const [rateLimitResetTime, setRateLimitResetTime] = useState(null);

  // Error threshold state
  const [consecutiveErrors, setConsecutiveErrors] = useState(0);
  const [autoRetryDisabled, setAutoRetryDisabled] = useState(false);
  const [lastErrorResetTime, setLastErrorResetTime] = useState(null);

  // Refs for cleanup and interval management
  const refreshIntervalRef = useRef(null);
  const retryTimeoutRef = useRef(null);
  const circuitTimeoutRef = useRef(null);
  const rateLimitTimeoutRef = useRef(null);
  const errorResetTimeoutRef = useRef(null);
  const mountedRef = useRef(true);

  /**
   * Clear all timers and intervals
   */
  const clearTimers = useCallback(() => {
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
      refreshIntervalRef.current = null;
    }
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
    if (circuitTimeoutRef.current) {
      clearTimeout(circuitTimeoutRef.current);
      circuitTimeoutRef.current = null;
    }
    if (rateLimitTimeoutRef.current) {
      clearTimeout(rateLimitTimeoutRef.current);
      rateLimitTimeoutRef.current = null;
    }
    if (errorResetTimeoutRef.current) {
      clearTimeout(errorResetTimeoutRef.current);
      errorResetTimeoutRef.current = null;
    }
  }, []);

  /**
   * Check if circuit breaker allows requests
   */
  const isCircuitOpen = useCallback(() => {
    if (circuitState === CIRCUIT_STATES.CLOSED) {
      return false;
    }

    if (circuitState === CIRCUIT_STATES.OPEN) {
      const now = Date.now();
      if (lastFailureTime && (now - lastFailureTime) >= circuitTimeout) {
        // Try half-open state
        setCircuitState(CIRCUIT_STATES.HALF_OPEN);
        setSuccessCount(0);
        console.log('Circuit breaker moving to HALF_OPEN state');
        return false;
      }
      return true;
    }

    // HALF_OPEN state allows limited requests
    return false;
  }, [circuitState, lastFailureTime, circuitTimeout]);

  /**
   * Record circuit breaker success
   */
  const recordCircuitSuccess = useCallback(() => {
    const newSuccessCount = successCount + 1;
    setSuccessCount(newSuccessCount);
    setFailureCount(0);
    setConsecutiveErrors(0);
    setAutoRetryDisabled(false);

    if (circuitState === CIRCUIT_STATES.HALF_OPEN && newSuccessCount >= HOOK_CONFIG.CIRCUIT_BREAKER.SUCCESS_THRESHOLD) {
      setCircuitState(CIRCUIT_STATES.CLOSED);
      setCircuitTimeout(HOOK_CONFIG.CIRCUIT_BREAKER.TIMEOUT);
      console.log('Circuit breaker CLOSED - service recovered');
    }
  }, [successCount, circuitState]);

  /**
   * Record circuit breaker failure
   */
  const recordCircuitFailure = useCallback(() => {
    const newFailureCount = failureCount + 1;
    const newConsecutiveErrors = consecutiveErrors + 1;

    setFailureCount(newFailureCount);
    setSuccessCount(0);
    setConsecutiveErrors(newConsecutiveErrors);
    setLastFailureTime(Date.now());

    // Check if we should disable auto-retry
    if (newConsecutiveErrors >= HOOK_CONFIG.ERROR_THRESHOLD.MAX_CONSECUTIVE_ERRORS) {
      setAutoRetryDisabled(true);
      console.log('Auto-retry disabled due to consecutive errors');

      // Set timeout to reset error count
      if (errorResetTimeoutRef.current) {
        clearTimeout(errorResetTimeoutRef.current);
      }
      errorResetTimeoutRef.current = setTimeout(() => {
        if (mountedRef.current) {
          setConsecutiveErrors(0);
          setAutoRetryDisabled(false);
          setLastErrorResetTime(Date.now());
          console.log('Error count reset - auto-retry re-enabled');
        }
      }, HOOK_CONFIG.ERROR_THRESHOLD.RESET_TIMEOUT);
    }

    // Open circuit if failure threshold reached
    if (newFailureCount >= HOOK_CONFIG.CIRCUIT_BREAKER.FAILURE_THRESHOLD) {
      setCircuitState(CIRCUIT_STATES.OPEN);
      const newTimeout = Math.min(circuitTimeout * HOOK_CONFIG.CIRCUIT_BREAKER.BACKOFF_MULTIPLIER, HOOK_CONFIG.CIRCUIT_BREAKER.MAX_TIMEOUT);
      setCircuitTimeout(newTimeout);
      console.log(`Circuit breaker OPEN for ${newTimeout}ms due to ${newFailureCount} failures`);

      // Set timeout to try half-open state
      if (circuitTimeoutRef.current) {
        clearTimeout(circuitTimeoutRef.current);
      }
      circuitTimeoutRef.current = setTimeout(() => {
        if (mountedRef.current) {
          setCircuitState(CIRCUIT_STATES.HALF_OPEN);
          console.log('Circuit breaker moving to HALF_OPEN state');
        }
      }, newTimeout);
    }
  }, [failureCount, consecutiveErrors, circuitTimeout]);

  /**
   * Check rate limiting without causing state updates
   */
  const checkRateLimit = useCallback(() => {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;

    // Clean old requests from history (don't update state here)
    const recentRequests = requestHistory.filter(timestamp => timestamp > oneMinuteAgo);

    // Check if rate limited
    if (isRateLimited && rateLimitResetTime && now < rateLimitResetTime) {
      return false; // Still rate limited
    }

    // Check burst limit (requests in last 5 seconds)
    const fiveSecondsAgo = now - 5000;
    const burstRequests = recentRequests.filter(timestamp => timestamp > fiveSecondsAgo);

    if (burstRequests.length >= HOOK_CONFIG.RATE_LIMIT.BURST_LIMIT) {
      return false;
    }

    // Check per-minute limit
    if (recentRequests.length >= HOOK_CONFIG.RATE_LIMIT.MAX_REQUESTS_PER_MINUTE) {
      return false;
    }

    return true; // Not rate limited
  }, [requestHistory, isRateLimited, rateLimitResetTime]);

  /**
   * Apply rate limiting (updates state)
   */
  const applyRateLimit = useCallback((reason) => {
    const now = Date.now();
    setIsRateLimited(true);

    if (reason === 'burst') {
      const resetTime = now + HOOK_CONFIG.RATE_LIMIT.COOLDOWN_PERIOD;
      setRateLimitResetTime(resetTime);
      console.log(`Rate limited due to burst`);

      // Set timeout to reset rate limit
      if (rateLimitTimeoutRef.current) {
        clearTimeout(rateLimitTimeoutRef.current);
      }
      rateLimitTimeoutRef.current = setTimeout(() => {
        if (mountedRef.current) {
          setIsRateLimited(false);
          setRateLimitResetTime(null);
        }
      }, HOOK_CONFIG.RATE_LIMIT.COOLDOWN_PERIOD);
    } else if (reason === 'minute') {
      const resetTime = now + 60000;
      setRateLimitResetTime(resetTime);
      console.log(`Rate limited (too many requests in last minute)`);
    }
  }, []);

  /**
   * Clean request history periodically
   */
  useEffect(() => {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;
    const recentRequests = requestHistory.filter(timestamp => timestamp > oneMinuteAgo);

    if (recentRequests.length !== requestHistory.length) {
      setRequestHistory(recentRequests);
    }

    // Reset rate limit if cooldown period passed
    if (isRateLimited && rateLimitResetTime && now >= rateLimitResetTime) {
      setIsRateLimited(false);
      setRateLimitResetTime(null);
      console.log('Rate limit reset');
    }
  }, [requestHistory, isRateLimited, rateLimitResetTime]);

  /**
   * Record a new request for rate limiting
   */
  const recordRequest = useCallback(() => {
    const now = Date.now();
    setRequestHistory(prev => [...prev, now]);
  }, []);

  /**
   * Fetch weather data with error handling and circuit breaker protection
   */
  const fetchWeatherData = useCallback(async (options = {}) => {
    const { forceRefresh = false, showLoading = true, currentRetryCount = 0, bypassSafeguards = false } = options;

    // Check circuit breaker (unless bypassed for manual requests)
    if (!bypassSafeguards && isCircuitOpen()) {
      const circuitError = new WeatherAPIError(
        'Service temporarily unavailable due to repeated failures. Please try again later.',
        null,
        'CircuitBreakerOpen'
      );

      if (mountedRef.current) {
        setError(circuitError);
        if (onError) {
          onError(circuitError);
        }
      }
      return;
    }

    // Check rate limiting (unless bypassed for manual requests)
    if (!bypassSafeguards) {
      const now = Date.now();
      const oneMinuteAgo = now - 60000;
      const fiveSecondsAgo = now - 5000;

      // Clean old requests
      const recentRequests = requestHistory.filter(timestamp => timestamp > oneMinuteAgo);
      const burstRequests = recentRequests.filter(timestamp => timestamp > fiveSecondsAgo);

      // Check if currently rate limited
      if (isRateLimited && rateLimitResetTime && now < rateLimitResetTime) {
        const rateLimitError = new WeatherAPIError(
          'Too many requests. Please wait a moment before trying again.',
          429,
          'RateLimited'
        );

        if (mountedRef.current) {
          setError(rateLimitError);
          if (onError) {
            onError(rateLimitError);
          }
        }
        return;
      }

      // Check burst limit
      if (burstRequests.length >= HOOK_CONFIG.RATE_LIMIT.BURST_LIMIT) {
        applyRateLimit('burst');
        const rateLimitError = new WeatherAPIError(
          'Too many requests. Please wait a moment before trying again.',
          429,
          'RateLimited'
        );

        if (mountedRef.current) {
          setError(rateLimitError);
          if (onError) {
            onError(rateLimitError);
          }
        }
        return;
      }

      // Check per-minute limit
      if (recentRequests.length >= HOOK_CONFIG.RATE_LIMIT.MAX_REQUESTS_PER_MINUTE) {
        applyRateLimit('minute');
        const rateLimitError = new WeatherAPIError(
          'Too many requests. Please wait a moment before trying again.',
          429,
          'RateLimited'
        );

        if (mountedRef.current) {
          setError(rateLimitError);
          if (onError) {
            onError(rateLimitError);
          }
        }
        return;
      }

      // Record request for rate limiting
      recordRequest();
    }

    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);

      console.log('Fetching weather data...', {
        forceRefresh,
        enableCache,
        currentRetryCount,
        circuitState,
        consecutiveErrors,
        autoRetryDisabled
      });

      const data = await weatherApiClient.getWeatherData({
        useCache: enableCache,
        forceRefresh
      });

      // Only update state if component is still mounted
      if (mountedRef.current) {
        setWeatherData(data);
        setLastUpdated(new Date());
        setRetryCount(0);

        // Record success for circuit breaker
        recordCircuitSuccess();

        // Call success callback if provided
        if (onSuccess) {
          onSuccess(data);
        }

        console.log('Weather data updated successfully');
      }

    } catch (err) {
      console.error('Error fetching weather data:', err);

      // Record failure for circuit breaker
      recordCircuitFailure();

      // Only update state if component is still mounted
      if (mountedRef.current) {
        setError(err);

        // Call error callback if provided
        if (onError) {
          onError(err);
        }

        // Implement automatic retry for certain errors (if not disabled)
        if (!autoRetryDisabled &&
            currentRetryCount < HOOK_CONFIG.MAX_AUTO_RETRIES &&
            shouldAutoRetry(err) &&
            !bypassSafeguards) {

          const retryDelay = HOOK_CONFIG.RETRY_INTERVALS[Math.min(currentRetryCount, HOOK_CONFIG.RETRY_INTERVALS.length - 1)];

          console.log(`Auto-retrying in ${retryDelay}ms (attempt ${currentRetryCount + 1}/${HOOK_CONFIG.MAX_AUTO_RETRIES})`);

          retryTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
              const newRetryCount = currentRetryCount + 1;
              setRetryCount(newRetryCount);
              fetchWeatherData({ forceRefresh, showLoading: false, currentRetryCount: newRetryCount });
            }
          }, retryDelay);
        } else if (autoRetryDisabled) {
          console.log('Auto-retry disabled due to consecutive errors');
        }
      }
    } finally {
      if (mountedRef.current && showLoading) {
        setLoading(false);
      }
    }
  }, [enableCache, onError, onSuccess, isCircuitOpen, recordRequest, recordCircuitSuccess, recordCircuitFailure, autoRetryDisabled, requestHistory, isRateLimited, rateLimitResetTime, applyRateLimit]);

  /**
   * Determine if error should trigger automatic retry
   */
  const shouldAutoRetry = (error) => {
    if (!(error instanceof WeatherAPIError)) return false;

    // Retry on network errors, timeouts, and server errors
    return error.type === 'NetworkError' ||
           error.type === 'TimeoutError' ||
           (error.status && error.status >= 500);
  };

  /**
   * Internal fetch function that respects safeguards (for testing and auto-retry)
   */
  const internalFetch = useCallback(async (forceRefresh = false) => {
    await fetchWeatherData({ forceRefresh, showLoading: true, bypassSafeguards: false });
  }, [fetchWeatherData]);

  /**
   * Manual refresh function (bypasses circuit breaker and rate limiting)
   */
  const refresh = useCallback(async (forceRefresh = false) => {
    console.log('Manual refresh triggered', { forceRefresh });
    setRetryCount(0); // Reset retry count on manual refresh
    await fetchWeatherData({ forceRefresh, showLoading: true, bypassSafeguards: true });
  }, [fetchWeatherData]);

  /**
   * Retry function for error recovery (bypasses circuit breaker and rate limiting)
   */
  const retry = useCallback(async () => {
    console.log('Manual retry triggered');
    setRetryCount(0); // Reset retry count on manual retry
    await fetchWeatherData({ forceRefresh: true, showLoading: true, bypassSafeguards: true });
  }, [fetchWeatherData]);

  /**
   * Reset circuit breaker manually
   */
  const resetCircuitBreaker = useCallback(() => {
    console.log('Manually resetting circuit breaker');
    setCircuitState(CIRCUIT_STATES.CLOSED);
    setFailureCount(0);
    setSuccessCount(0);
    setLastFailureTime(null);
    setCircuitTimeout(HOOK_CONFIG.CIRCUIT_BREAKER.TIMEOUT);
    setConsecutiveErrors(0);
    setAutoRetryDisabled(false);

    // Clear any pending timeouts
    if (circuitTimeoutRef.current) {
      clearTimeout(circuitTimeoutRef.current);
      circuitTimeoutRef.current = null;
    }
    if (errorResetTimeoutRef.current) {
      clearTimeout(errorResetTimeoutRef.current);
      errorResetTimeoutRef.current = null;
    }
  }, []);

  /**
   * Reset rate limiting manually
   */
  const resetRateLimit = useCallback(() => {
    console.log('Manually resetting rate limit');
    setIsRateLimited(false);
    setRateLimitResetTime(null);
    setRequestHistory([]);

    if (rateLimitTimeoutRef.current) {
      clearTimeout(rateLimitTimeoutRef.current);
      rateLimitTimeoutRef.current = null;
    }
  }, []);

  /**
   * Clear cache and refresh
   */
  const clearCacheAndRefresh = useCallback(async () => {
    console.log('Clearing cache and refreshing');
    weatherApiClient.clearCache();
    await refresh(true);
  }, [refresh]);

  /**
   * Setup auto-refresh interval (disabled by default)
   */
  const setupAutoRefresh = useCallback(() => {
    if (!autoRefresh || refreshInterval <= 0) {
      console.log('Auto-refresh is disabled');
      return;
    }

    clearTimers();

    refreshIntervalRef.current = setInterval(() => {
      if (mountedRef.current) {
        console.log('Auto-refresh triggered');
        fetchWeatherData({ forceRefresh: false, showLoading: false });
      }
    }, refreshInterval);

    console.log(`Auto-refresh setup with ${Math.round(refreshInterval/1000)}s interval`);
  }, [autoRefresh, refreshInterval, fetchWeatherData, clearTimers]);

  /**
   * Initial data load
   */
  useEffect(() => {
    fetchWeatherData({ forceRefresh: false, showLoading: true });
  }, [fetchWeatherData]);

  /**
   * Setup auto-refresh
   */
  useEffect(() => {
    setupAutoRefresh();
    return clearTimers;
  }, [setupAutoRefresh, clearTimers]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      clearTimers();
      weatherApiClient.cancelRequests();
    };
  }, [clearTimers]);

  /**
   * Get cache status for debugging
   */
  const getCacheStatus = useCallback(() => {
    return weatherApiClient.getCacheStatus();
  }, []);

  /**
   * Check if data is stale (only relevant when auto-refresh is enabled)
   */
  const isDataStale = useCallback(() => {
    if (!autoRefresh || !lastUpdated) return false;
    return Date.now() - lastUpdated.getTime() > refreshInterval;
  }, [lastUpdated, refreshInterval, autoRefresh]);

  /**
   * Get formatted error message with circuit breaker and rate limiting context
   */
  const getErrorMessage = useCallback(() => {
    if (!error) return null;

    if (error instanceof WeatherAPIError) {
      switch (error.type) {
        case 'CircuitBreakerOpen':
          return `Service temporarily unavailable due to repeated failures. Circuit breaker will reset in ${Math.ceil(circuitTimeout / 1000)} seconds.`;
        case 'RateLimited':
          const resetIn = rateLimitResetTime ? Math.ceil((rateLimitResetTime - Date.now()) / 1000) : 0;
          return `Too many requests. Please wait ${resetIn > 0 ? resetIn + ' seconds' : 'a moment'} before trying again.`;
        case 'NetworkError':
          const networkMsg = 'Unable to connect to weather service. Please check your internet connection.';
          return autoRetryDisabled ? `${networkMsg} Auto-retry has been disabled due to repeated failures.` : networkMsg;
        case 'TimeoutError':
          const timeoutMsg = 'Request timed out. The weather service may be experiencing high load.';
          return autoRetryDisabled ? `${timeoutMsg} Auto-retry has been disabled due to repeated failures.` : timeoutMsg;
        case 'ValidationError':
          return 'Received invalid data from weather service. Please try again.';
        case 'HTTPError':
          if (error.status === 429) {
            return 'Too many requests. Please wait a moment before trying again.';
          }
          if (error.status >= 500) {
            const serverMsg = 'Weather service is temporarily unavailable. Please try again later.';
            return autoRetryDisabled ? `${serverMsg} Auto-retry has been disabled due to repeated failures.` : serverMsg;
          }
          return `Service error (${error.status}). Please try again.`;
        default:
          return error.message || 'An unexpected error occurred.';
      }
    }

    return error.message || 'An unknown error occurred.';
  }, [error, circuitTimeout, rateLimitResetTime, autoRetryDisabled]);

  // Return hook interface
  return {
    // Data state
    weatherData,
    loading,
    error,
    lastUpdated,

    // Actions
    refresh,
    retry,
    clearCacheAndRefresh,
    resetCircuitBreaker,
    resetRateLimit,

    // Internal actions (for testing)
    _internalFetch: internalFetch,

    // Status helpers
    isDataStale: isDataStale(),
    retryCount,
    getCacheStatus,
    getErrorMessage: getErrorMessage(),

    // Circuit breaker status
    circuitState,
    isCircuitOpen: isCircuitOpen(),
    failureCount,
    successCount,
    circuitTimeout,

    // Rate limiting status
    isRateLimited,
    rateLimitResetTime,
    requestsInLastMinute: requestHistory.length,

    // Error threshold status
    consecutiveErrors,
    autoRetryDisabled,
    lastErrorResetTime,

    // Configuration
    autoRefresh,
    refreshInterval
  };
};

/**
 * Hook for individual city weather data
 * Extracts specific city data from the main weather response
 */
export const useCityWeatherData = (cityId, options = {}) => {
  const weatherHook = useWeatherData(options);

  const cityData = weatherHook.weatherData?.cities?.find(city => city.cityId === cityId) || null;
  const cityLoading = weatherHook.loading;
  const cityError = weatherHook.error;

  return {
    ...weatherHook,
    cityData,
    loading: cityLoading,
    error: cityError
  };
};

/**
 * Hook for health check monitoring
 */
export const useHealthCheck = (options = {}) => {
  const { interval = 30000, enabled = false } = options; // Disabled by default

  const [healthStatus, setHealthStatus] = useState(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [healthError, setHealthError] = useState(null);

  const intervalRef = useRef(null);
  const mountedRef = useRef(true);

  const checkHealth = useCallback(async () => {
    if (!enabled) return;

    try {
      setHealthLoading(true);
      setHealthError(null);

      const status = await weatherApiClient.getHealthStatus();

      if (mountedRef.current) {
        setHealthStatus(status);
      }
    } catch (error) {
      if (mountedRef.current) {
        setHealthError(error);
      }
    } finally {
      if (mountedRef.current) {
        setHealthLoading(false);
      }
    }
  }, [enabled]);

  useEffect(() => {
    if (!enabled) return;

    // Initial check
    checkHealth();

    // Setup interval
    intervalRef.current = setInterval(checkHealth, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [checkHealth, interval, enabled]);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  return {
    healthStatus,
    healthLoading,
    healthError,
    checkHealth,
    isHealthy: healthStatus?.status === 'healthy'
  };
};