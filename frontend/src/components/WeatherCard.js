import React from 'react';
import './WeatherCard.css';

const WeatherCard = ({
  cityData,
  isLoading = false,
  error = null
}) => {
  if (error) {
    return (
      <div className="weather-card weather-card--error">
        <div className="weather-card__header">
          <h3 className="weather-card__city">
            {cityData?.cityName || 'Unknown City'}
          </h3>
          <span className="weather-card__country">
            {cityData?.country || ''}
          </span>
        </div>
        <div className="weather-card__error">
          <div className="weather-card__error-icon">⚠️</div>
          <p className="weather-card__error-message">
            Unable to load weather data
          </p>
          <button
            className="weather-card__retry-button"
            onClick={() => window.location.reload()}
            aria-label="Retry loading weather data"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="weather-card weather-card--loading">
        <div className="weather-card__header">
          <div className="weather-card__skeleton weather-card__skeleton--title"></div>
          <div className="weather-card__skeleton weather-card__skeleton--subtitle"></div>
        </div>
        <div className="weather-card__content">
          <div className="weather-card__skeleton weather-card__skeleton--icon"></div>
          <div className="weather-card__skeleton weather-card__skeleton--temperature"></div>
          <div className="weather-card__skeleton weather-card__skeleton--description"></div>
        </div>
      </div>
    );
  }

  if (!cityData || !cityData.forecast) {
    return (
      <div className="weather-card weather-card--no-data">
        <div className="weather-card__header">
          <h3 className="weather-card__city">No Data</h3>
        </div>
        <div className="weather-card__content">
          <p>Weather data not available</p>
        </div>
      </div>
    );
  }

  const { cityName, country, forecast } = cityData;
  const { temperature, condition, description, icon } = forecast;

  return (
    <div className="weather-card">
      <div className="weather-card__header">
        <h3 className="weather-card__city">{cityName}</h3>
        <span className="weather-card__country">{country}</span>
      </div>

      <div className="weather-card__content">
        <div className="weather-card__icon-container">
          <div
            className={`weather-card__icon weather-card__icon--${icon}`}
            aria-label={`Weather condition: ${description}`}
          >
            {getWeatherIcon(icon)}
          </div>
        </div>

        <div className="weather-card__temperature">
          <span className="weather-card__temp-value">
            {Math.round(temperature.value)}
          </span>
          <span className="weather-card__temp-unit">°C</span>
        </div>

        <p className="weather-card__description">{description}</p>

        <div className="weather-card__details">
          {forecast.humidity && (
            <div className="weather-card__detail">
              <span className="weather-card__detail-label">Humidity</span>
              <span className="weather-card__detail-value">{forecast.humidity}%</span>
            </div>
          )}
          {forecast.windSpeed && (
            <div className="weather-card__detail">
              <span className="weather-card__detail-label">Wind</span>
              <span className="weather-card__detail-value">{forecast.windSpeed} km/h</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Weather icon mapping function
const getWeatherIcon = (iconType) => {
  const iconMap = {
    'clear_day': '☀️',
    'clear_night': '🌙',
    'partly_cloudy_day': '⛅',
    'partly_cloudy_night': '☁️',
    'cloudy': '☁️',
    'rain': '🌧️',
    'snow': '❄️',
    'thunderstorm': '⛈️',
    'fog': '🌫️',
    'wind': '💨',
    'default': '🌤️'
  };

  return iconMap[iconType] || iconMap.default;
};

export default WeatherCard;