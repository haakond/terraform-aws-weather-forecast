/**
 * Simple useWeatherData Hook
 *
 * Simplified React hook for managing weather data state:
 * - Basic data fetching with loading states
 * - Fail hard on any errors
 * - No browser-side caching
 * - No retry logic or circuit breakers
 * - All requests go through Lambda backend only
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { weatherApiClient, WeatherAPIError } from '../services/weatherApi';

/**
 * Simple hook for weather data management
 */
export const useWeatherData = (options = {}) => {
  const {
    onError = null,
    onSuccess = null
  } = options;

  // State management
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Refs for cleanup and preventing loops
  const mountedRef = useRef(true);
  const fetchingRef = useRef(false); // Prevent concurrent fetches

  // Stable refs for callbacks to prevent infinite loops
  const onErrorRef = useRef(onError);
  const onSuccessRef = useRef(onSuccess);

  // Update refs when callbacks change
  useEffect(() => {
    onErrorRef.current = onError;
    onSuccessRef.current = onSuccess;
  }, [onError, onSuccess]);

  /**
   * Fetch weather data - fail hard on any issues
   */
  const fetchWeatherData = useCallback(async (showLoading = true) => {
    // Prevent concurrent fetches
    if (fetchingRef.current) {
      console.log('Fetch already in progress, skipping...');
      return;
    }

    // Prevent fetch if component is unmounted
    if (!mountedRef.current) {
      console.log('Component unmounted, skipping fetch...');
      return;
    }

    try {
      fetchingRef.current = true;

      if (showLoading) {
        setLoading(true);
      }
      setError(null);

      console.log('Fetching weather data from Lambda backend...');

      const data = await weatherApiClient.getWeatherData();

      // Only update state if component is still mounted
      if (mountedRef.current) {
        setWeatherData(data);
        setLastUpdated(new Date());

        // Call success callback if provided
        if (onSuccessRef.current) {
          onSuccessRef.current(data);
        }

        console.log('Weather data updated successfully');
      }

    } catch (err) {
      console.error('Error fetching weather data:', err);

      // Only update state if component is still mounted
      if (mountedRef.current) {
        setError(err);

        // Call error callback if provided
        if (onErrorRef.current) {
          onErrorRef.current(err);
        }
      }
    } finally {
      fetchingRef.current = false;
      if (mountedRef.current && showLoading) {
        setLoading(false);
      }
    }
  }, []); // Empty dependency array to prevent infinite loops

  /**
   * Manual refresh function
   */
  const refresh = useCallback(async () => {
    console.log('Manual refresh triggered');
    await fetchWeatherData(true);
  }, [fetchWeatherData]);

  /**
   * Retry function for error recovery
   */
  const retry = useCallback(async () => {
    console.log('Manual retry triggered');
    await fetchWeatherData(true);
  }, [fetchWeatherData]);

  /**
   * Initial data load - only run once on mount
   */
  useEffect(() => {
    fetchWeatherData(true);
  }, []); // Empty dependency array to run only once on mount

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      fetchingRef.current = false; // Reset fetching state
    };
  }, []);

  /**
   * Get formatted error message
   */
  const getErrorMessage = useCallback(() => {
    if (!error) return null;

    // Check for CORS-related errors
    if (error.message && error.message.includes('CORS')) {
      return 'Unable to connect to weather service due to a configuration issue. Please contact support.';
    }

    if (error instanceof WeatherAPIError) {
      switch (error.type) {
        case 'NetworkError':
          // Check if it's likely a CORS error
          if (error.message && (error.message.includes('fetch') || error.message.includes('blocked'))) {
            return 'Unable to connect to weather service. This may be due to a configuration issue.';
          }
          return 'Unable to connect to weather service. Please check your internet connection and try again.';
        case 'TimeoutError':
          return 'Request timed out. Please try again.';
        case 'ValidationError':
          return 'Received invalid data from weather service. Please try again.';
        case 'HTTPError':
          if (error.status === 429) {
            return 'Too many requests. Please wait a moment before trying again.';
          }
          if (error.status >= 500) {
            return 'Weather service is temporarily unavailable. Please try again later.';
          }
          if (error.status >= 400) {
            return 'Bad request. Please try again.';
          }
          return `Service error (${error.status}). Please try again.`;
        default:
          return error.message || 'An unexpected error occurred. Please try again.';
      }
    }

    return error.message || 'An unknown error occurred. Please try again.';
  }, [error]);

  // Return simplified hook interface
  return {
    // Data state
    weatherData,
    loading,
    error,
    lastUpdated,

    // Actions
    refresh,
    retry,

    // Status helpers
    getErrorMessage: getErrorMessage()
  };
};

/**
 * Hook for individual city weather data
 * Extracts specific city data from the main weather response
 */
export const useCityWeatherData = (cityId, options = {}) => {
  const weatherHook = useWeatherData(options);

  const cityData = weatherHook.weatherData?.cities?.find(city => city.cityId === cityId) || null;

  return {
    ...weatherHook,
    cityData
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