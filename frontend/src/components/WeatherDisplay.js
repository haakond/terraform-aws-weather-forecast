import React from 'react';
import WeatherCard from './WeatherCard';
import { useWeatherData } from '../hooks/useWeatherData';
import { WeatherAPIError } from '../services/weatherApi';
import './WeatherDisplay.css';

const WeatherDisplay = () => {
  // Use the weather data hook for state management
  const {
    weatherData,
    loading,
    error,
    lastUpdated,
    refresh,
    retry,
    clearCacheAndRefresh,
    resetCircuitBreaker,
    resetRateLimit,
    isDataStale,
    retryCount,
    getCacheStatus,
    getErrorMessage,
    circuitState,
    isCircuitOpen,
    failureCount,
    isRateLimited,
    rateLimitResetTime,
    consecutiveErrors,
    autoRetryDisabled
  } = useWeatherData({
    autoRefresh: false, // Disabled auto-refresh
    enableCache: true,
    onError: (error) => {
      console.error('Weather data error:', error);
    },
    onSuccess: (data) => {
      // console.log('Weather data loaded successfully:', data);
    }
  });

  // City configuration matching the design document
  const cities = [
    {
      id: 'oslo',
      name: 'Oslo',
      country: 'Norway',
      coordinates: { lat: 59.9139, lon: 10.7522 }
    },
    {
      id: 'paris',
      name: 'Paris',
      country: 'France',
      coordinates: { lat: 48.8566, lon: 2.3522 }
    },
    {
      id: 'london',
      name: 'London',
      country: 'United Kingdom',
      coordinates: { lat: 51.5074, lon: -0.1278 }
    },
    {
      id: 'barcelona',
      name: 'Barcelona',
      country: 'Spain',
      coordinates: { lat: 41.3851, lon: 2.1734 }
    }
  ];

  // Helper function to get city data from API response
  const getCityData = (cityId) => {
    if (!weatherData || !weatherData.cities) {
      return null;
    }
    return weatherData.cities.find(city => city.cityId === cityId);
  };

  // Helper function to check if a city has an error
  const getCityError = (cityId) => {
    const cityData = getCityData(cityId);
    if (!cityData && error) {
      return getErrorMessage;
    }
    return null;
  };

  // Helper function to check if a city is loading
  const isCityLoading = (cityId) => {
    return loading && !getCityData(cityId);
  };

  // Check if all cities have errors or no data
  const hasGlobalError = error && (!weatherData || !weatherData.cities || weatherData.cities.length === 0);

  // Global error state - show when there's an error and no data available
  if (hasGlobalError) {
    return (
      <div className="weather-display">
        <div className="weather-display__header">
          <h1 className="weather-display__title">Tomorrow's Weather Forecast</h1>
          <p className="weather-display__subtitle">European Cities</p>
        </div>

        <div className="weather-display__global-error">
          <div className="weather-display__error-icon">
            {isCircuitOpen ? '🚫' : isRateLimited ? '⏱️' : '🌩️'}
          </div>
          <h2 className="weather-display__error-title">
            {isCircuitOpen ? 'Service Protection Active' :
             isRateLimited ? 'Rate Limited' :
             'Weather Service Unavailable'}
          </h2>
          <p className="weather-display__error-message">
            {getErrorMessage}
          </p>

          {/* Circuit breaker status */}
          {isCircuitOpen && (
            <div className="weather-display__circuit-status">
              <p className="weather-display__circuit-info">
                Circuit breaker is open after {failureCount} consecutive failures.
                The service will be tested again automatically.
              </p>
            </div>
          )}

          {/* Rate limiting status */}
          {isRateLimited && rateLimitResetTime && (
            <div className="weather-display__rate-limit-status">
              <p className="weather-display__rate-limit-info">
                Rate limit will reset in {Math.ceil((rateLimitResetTime - Date.now()) / 1000)} seconds.
              </p>
            </div>
          )}

          {/* Auto-retry disabled status */}
          {autoRetryDisabled && (
            <div className="weather-display__auto-retry-status">
              <p className="weather-display__auto-retry-info">
                ⚠️ Auto-retry has been disabled after {consecutiveErrors} consecutive errors.
                You can still try manually.
              </p>
            </div>
          )}

          <div className="weather-display__error-actions">
            <button
              className="weather-display__retry-button"
              onClick={retry}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Try Again'}
            </button>
            <button
              className="weather-display__clear-cache-button"
              onClick={clearCacheAndRefresh}
              disabled={loading}
            >
              Clear Cache & Retry
            </button>

            {/* Advanced recovery options */}
            {(isCircuitOpen || isRateLimited || autoRetryDisabled) && (
              <div className="weather-display__advanced-actions">
                {isCircuitOpen && (
                  <button
                    className="weather-display__reset-circuit-button"
                    onClick={resetCircuitBreaker}
                    disabled={loading}
                    title="Reset circuit breaker protection"
                  >
                    Reset Protection
                  </button>
                )}
                {isRateLimited && (
                  <button
                    className="weather-display__reset-rate-limit-button"
                    onClick={resetRateLimit}
                    disabled={loading}
                    title="Reset rate limiting"
                  >
                    Reset Rate Limit
                  </button>
                )}
              </div>
            )}
          </div>

          {retryCount > 0 && (
            <p className="weather-display__retry-info">
              Retry attempt {retryCount} of 3
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="weather-display">
      <div className="weather-display__header">
        <h1 className="weather-display__title" id="main-title">
          Tomorrow's Weather Forecast
        </h1>
        <p className="weather-display__subtitle" aria-describedby="main-title">
          European Cities - {new Date(Date.now() + 24 * 60 * 60 * 1000).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })}
        </p>

        {/* Status indicators */}
        <div className="weather-display__status">
          {lastUpdated && (
            <p className="weather-display__last-updated">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}

          {/* Cache status for debugging */}
          {process.env.NODE_ENV === 'development' && (
            <div className="weather-display__debug">
              <button
                onClick={() => console.log('Cache status:', getCacheStatus())}
                className="weather-display__debug-button"
              >
                Debug Cache
              </button>
              <button
                onClick={() => refresh(true)}
                className="weather-display__debug-button"
                disabled={loading}
              >
                Force Refresh
              </button>
            </div>
          )}
        </div>
      </div>

      <div
        className="weather-display__grid"
        role="main"
        aria-label="Weather forecast cards for European cities"
      >
        {cities.map((city, index) => {
          const cityData = getCityData(city.id);
          const cityError = getCityError(city.id);
          const cityLoading = isCityLoading(city.id);

          return (
            <WeatherCard
              key={city.id}
              cityData={cityData || {
                cityName: city.name,
                country: city.country
              }}
              isLoading={cityLoading}
              error={cityError}
              onRetry={() => refresh(true)}
              style={{ animationDelay: `${index * 0.1}s` }}
            />
          );
        })}
      </div>

      {/* Global loading indicator */}
      {loading && (
        <div className="weather-display__loading-indicator">
          <div className="weather-display__loading-spinner"></div>
          <p className="weather-display__loading-text">
            {retryCount > 0 ? `Retrying... (${retryCount}/3)` : 'Loading weather data...'}
          </p>
        </div>
      )}

      {/* Refresh controls */}
      {!loading && !hasGlobalError && (
        <div className="weather-display__controls">
          <button
            className="weather-display__refresh-button"
            onClick={() => refresh(false)}
            disabled={loading}
            title="Refresh weather data (uses cache if available)"
          >
            🔄 Refresh
          </button>
          <button
            className="weather-display__force-refresh-button"
            onClick={() => refresh(true)}
            disabled={loading}
            title="Force refresh (bypasses cache)"
          >
            ⚡ Force Refresh
          </button>
        </div>
      )}

      {/* Error banner for partial failures */}
      {error && weatherData && weatherData.cities && weatherData.cities.length > 0 && (
        <div className="weather-display__partial-error">
          <p className="weather-display__partial-error-message">
            ⚠️ Some weather data may be outdated due to service issues.
            <button
              className="weather-display__partial-error-retry"
              onClick={retry}
              disabled={loading}
            >
              Try updating
            </button>
          </p>
        </div>
      )}
    </div>
  );
};

export default WeatherDisplay;