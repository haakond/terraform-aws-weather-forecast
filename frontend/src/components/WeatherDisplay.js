import React, { useState, useEffect } from 'react';
import WeatherCard from './WeatherCard';
import './WeatherDisplay.css';

const WeatherDisplay = () => {
  const [weatherData, setWeatherData] = useState({});
  const [loading, setLoading] = useState({});
  const [errors, setErrors] = useState({});
  const [globalError, setGlobalError] = useState(null);

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

  // Initialize loading states
  useEffect(() => {
    const initialLoading = {};
    cities.forEach(city => {
      initialLoading[city.id] = true;
    });
    setLoading(initialLoading);
  }, []);

  // Mock data fetching function (will be replaced in task 5.2)
  const fetchWeatherData = async (cityId) => {
    try {
      setLoading(prev => ({ ...prev, [cityId]: true }));
      setErrors(prev => ({ ...prev, [cityId]: null }));

      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));

      // Mock weather data for demonstration
      const mockData = {
        cityId: cityId,
        cityName: cities.find(c => c.id === cityId)?.name || 'Unknown',
        country: cities.find(c => c.id === cityId)?.country || 'Unknown',
        coordinates: cities.find(c => c.id === cityId)?.coordinates || { lat: 0, lon: 0 },
        forecast: {
          date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          temperature: {
            value: Math.round(Math.random() * 30 - 5), // -5 to 25°C
            unit: 'celsius'
          },
          condition: ['clear_day', 'partly_cloudy_day', 'cloudy', 'rain'][Math.floor(Math.random() * 4)],
          description: ['Sunny', 'Partly cloudy', 'Cloudy', 'Light rain'][Math.floor(Math.random() * 4)],
          icon: ['clear_day', 'partly_cloudy_day', 'cloudy', 'rain'][Math.floor(Math.random() * 4)],
          humidity: Math.round(Math.random() * 40 + 40), // 40-80%
          windSpeed: Math.round(Math.random() * 20 + 5) // 5-25 km/h
        },
        lastUpdated: new Date().toISOString(),
        ttl: Math.floor(Date.now() / 1000) + 3600 // 1 hour from now
      };

      // Simulate occasional errors for demonstration
      if (Math.random() < 0.1) {
        throw new Error('Weather service temporarily unavailable');
      }

      setWeatherData(prev => ({ ...prev, [cityId]: mockData }));
      setLoading(prev => ({ ...prev, [cityId]: false }));
    } catch (error) {
      console.error(`Error fetching weather for ${cityId}:`, error);
      setErrors(prev => ({ ...prev, [cityId]: error.message }));
      setLoading(prev => ({ ...prev, [cityId]: false }));
    }
  };

  // Load weather data for all cities
  useEffect(() => {
    const loadAllWeatherData = async () => {
      try {
        setGlobalError(null);

        // Fetch weather data for all cities concurrently
        const fetchPromises = cities.map(city => fetchWeatherData(city.id));
        await Promise.allSettled(fetchPromises);

      } catch (error) {
        console.error('Error loading weather data:', error);
        setGlobalError('Unable to load weather information. Please try again later.');
      }
    };

    loadAllWeatherData();
  }, []);

  // Retry function for individual cities
  const retryCity = (cityId) => {
    fetchWeatherData(cityId);
  };

  // Retry all cities
  const retryAll = () => {
    cities.forEach(city => fetchWeatherData(city.id));
  };

  // Check if all cities have errors
  const allCitiesHaveErrors = cities.every(city => errors[city.id]);
  const anyCityLoading = Object.values(loading).some(isLoading => isLoading);

  if (globalError && allCitiesHaveErrors) {
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
            We're having trouble connecting to the weather service. Please check your internet connection and try again.
          </p>
          <button
            className="weather-display__retry-button"
            onClick={retryAll}
            disabled={anyCityLoading}
          >
            {anyCityLoading ? 'Loading...' : 'Try Again'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="weather-display">
      <div className="weather-display__header">
        <h1 className="weather-display__title">Tomorrow's Weather Forecast</h1>
        <p className="weather-display__subtitle">
          European Cities - {new Date(Date.now() + 24 * 60 * 60 * 1000).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })}
        </p>
      </div>

      <div className="weather-display__grid">
        {cities.map(city => (
          <WeatherCard
            key={city.id}
            cityData={weatherData[city.id] || {
              cityName: city.name,
              country: city.country
            }}
            isLoading={loading[city.id]}
            error={errors[city.id]}
            onRetry={() => retryCity(city.id)}
          />
        ))}
      </div>

      {anyCityLoading && (
        <div className="weather-display__loading-indicator">
          <div className="weather-display__loading-spinner"></div>
          <p className="weather-display__loading-text">Loading weather data...</p>
        </div>
      )}
    </div>
  );
};

export default WeatherDisplay;