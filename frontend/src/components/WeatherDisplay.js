import React from 'react';
import WeatherCard from './WeatherCard';
import { useWeatherData } from '../hooks/useWeatherData';
import { WeatherAPIError } from '../services/weatherApi';
import './WeatherDisplay.css';

const WeatherDisplay = () => {
  // Use the simplified weather data hook for state management
  const {
    weatherData,
    loading,
    error,
    lastUpdated,
    refresh,
    retry,
    getErrorMessage
  } = useWeatherData({
    onError: (error) => {
      console.error('Weather data error:', error);
    },
    onSuccess: (data) => {
      console.log('Weather data loaded successfully:', data);
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
          <div className="weather-display__error-icon">🌩️</div>
          <h2 className="weather-display__error-title">Weather Service Unavailable</h2>
          <p className="weather-display__error-message">
            {getErrorMessage}
          </p>

          <div className="weather-display__error-actions">
            <button
              className="weather-display__retry-button"
              onClick={retry}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Try Again'}
            </button>
          </div>
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

          {/* Debug controls for development */}
          {process.env.NODE_ENV === 'development' && (
            <div className="weather-display__debug">
              <button
                onClick={() => refresh()}
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
              onRetry={() => refresh()}
              style={{ animationDelay: `${index * 0.1}s` }}
            />
          );
        })}
      </div>

      {/* Global loading indicator */}
      {loading && (
        <div className="weather-display__loading-indicator">
          <div className="weather-display__loading-spinner"></div>
          <p className="weather-display__loading-text">Loading weather data...</p>
        </div>
      )}

      {/* Refresh controls */}
      {!loading && !hasGlobalError && (
        <div className="weather-display__controls">
          <button
            className="weather-display__refresh-button"
            onClick={() => refresh()}
            disabled={loading}
            title="Refresh weather data"
          >
            🔄 Refresh
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