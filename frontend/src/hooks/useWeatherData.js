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
  MAX_AUTO_RETRIES: 2 // Reduced since HTTP client already does 5 retries with exponential backoff
};

/**
 * Custom hook for weather data management
 */
export const useWeatherData = (options = {}) => {
  const {
    autoRefresh = true,
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

  // Refs for cleanup and interval management
  const refreshIntervalRef = useRef(null);
  const retryTimeoutRef = useRef(null);
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
  }, []);

  /**
   * Fetch weather data with error handling
   */
  const fetchWeatherData = useCallback(async (options = {}) => {
    const { forceRefresh = false, showLoading = true } = options;

    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);

      console.log('Fetching weather data...', { forceRefresh, enableCache });

      const data = await weatherApiClient.getWeatherData({
        useCache: enableCache,
        forceRefresh
      });

      // Only update state if component is still mounted
      if (mountedRef.current) {
        setWeatherData(data);
        setLastUpdated(new Date());
        setRetryCount(0);

        // Call success callback if provided
        if (onSuccess) {
          onSuccess(data);
        }

        console.log('Weather data updated successfully');
      }

    } catch (err) {
      console.error('Error fetching weather data:', err);

      // Only update state if component is still mounted
      if (mountedRef.current) {
        setError(err);

        // Call error callback if provided
        if (onError) {
          onError(err);
        }

        // Implement automatic retry for certain errors
        if (retryCount < HOOK_CONFIG.MAX_AUTO_RETRIES && shouldAutoRetry(err)) {
          const retryDelay = HOOK_CONFIG.RETRY_INTERVALS[Math.min(retryCount, HOOK_CONFIG.RETRY_INTERVALS.length - 1)];

          console.log(`Auto-retrying in ${retryDelay}ms (attempt ${retryCount + 1}/${HOOK_CONFIG.MAX_AUTO_RETRIES})`);

          retryTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
              setRetryCount(prev => prev + 1);
              fetchWeatherData({ forceRefresh, showLoading: false });
            }
          }, retryDelay);
        }
      }
    } finally {
      if (mountedRef.current && showLoading) {
        setLoading(false);
      }
    }
  }, [enableCache, retryCount, onError, onSuccess]);

  /**
   * Determine if error should trigger automatic retry
   */
  const shouldAutoRetry = useCallback((error) => {
    if (!(error instanceof WeatherAPIError)) return false;

    // Retry on network errors, timeouts, and server errors
    return error.type === 'NetworkError' ||
           error.type === 'TimeoutError' ||
           (error.status && error.status >= 500);
  }, []);

  /**
   * Manual refresh function
   */
  const refresh = useCallback(async (forceRefresh = false) => {
    console.log('Manual refresh triggered', { forceRefresh });
    setRetryCount(0); // Reset retry count on manual refresh
    await fetchWeatherData({ forceRefresh, showLoading: true });
  }, [fetchWeatherData]);

  /**
   * Retry function for error recovery
   */
  const retry = useCallback(async () => {
    console.log('Manual retry triggered');
    setRetryCount(0); // Reset retry count on manual retry
    await fetchWeatherData({ forceRefresh: true, showLoading: true });
  }, [fetchWeatherData]);

  /**
   * Clear cache and refresh
   */
  const clearCacheAndRefresh = useCallback(async () => {
    console.log('Clearing cache and refreshing');
    weatherApiClient.clearCache();
    await refresh(true);
  }, [refresh]);

  /**
   * Setup auto-refresh interval
   */
  const setupAutoRefresh = useCallback(() => {
    if (!autoRefresh || refreshInterval <= 0) return;

    clearTimers();

    refreshIntervalRef.current = setInterval(() => {
      if (mountedRef.current) {
        console.log('Auto-refresh triggered');
        fetchWeatherData({ forceRefresh: false, showLoading: false });
      }
    }, refreshInterval);

    console.log(`Auto-refresh setup with ${refreshInterval}ms interval`);
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
   * Check if data is stale (older than refresh interval)
   */
  const isDataStale = useCallback(() => {
    if (!lastUpdated) return true;
    return Date.now() - lastUpdated.getTime() > refreshInterval;
  }, [lastUpdated, refreshInterval]);

  /**
   * Get formatted error message
   */
  const getErrorMessage = useCallback(() => {
    if (!error) return null;

    if (error instanceof WeatherAPIError) {
      switch (error.type) {
        case 'NetworkError':
          return 'Unable to connect to weather service. Please check your internet connection.';
        case 'TimeoutError':
          return 'Request timed out. The weather service may be experiencing high load.';
        case 'ValidationError':
          return 'Received invalid data from weather service. Please try again.';
        case 'HTTPError':
          if (error.status === 429) {
            return 'Too many requests. Please wait a moment before trying again.';
          }
          if (error.status >= 500) {
            return 'Weather service is temporarily unavailable. Please try again later.';
          }
          return `Service error (${error.status}). Please try again.`;
        default:
          return error.message || 'An unexpected error occurred.';
      }
    }

    return error.message || 'An unknown error occurred.';
  }, [error]);

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

    // Status helpers
    isDataStale: isDataStale(),
    retryCount,
    getCacheStatus,
    getErrorMessage: getErrorMessage(),

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
  const { interval = 30000, enabled = true } = options; // 30 seconds default

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