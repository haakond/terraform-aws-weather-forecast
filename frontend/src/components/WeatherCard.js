import React from 'react';
import './WeatherCard.css';

const WeatherCard = ({
  cityData,
  isLoading = false,
  error = null,
  onRetry = null
}) => {
  // Helper function to format timestamp for user-friendly display
  const formatLastUpdated = (timestamp) => {
    if (!timestamp) {
      return null;
    }

    let date;
    try {
      // Handle both Date objects and ISO string timestamps
      date = timestamp instanceof Date ? timestamp : new Date(timestamp);

      // Validate the parsed date
      if (isNaN(date.getTime())) {
        return null;
      }
    } catch (e) {
      return null;
    }

    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    // Handle future timestamps (shouldn't happen but be defensive)
    if (diffMs < 0) {
      return 'Just now';
    }

    // Less than 1 minute
    if (diffMinutes < 1) {
      return 'Just now';
    }

    // Less than 1 hour
    if (diffMinutes < 60) {
      return `${diffMinutes} minute${diffMinutes === 1 ? '' : 's'} ago`;
    }

    // Less than 24 hours
    if (diffHours < 24) {
      return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
    }

    // Less than 7 days
    if (diffDays < 7) {
      return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
    }

    // More than 7 days - show actual date
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
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
            onClick={onRetry || (() => window.location.reload())}
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

  // Determine weather-based CSS class for dynamic styling
  const getWeatherClass = (condition) => {
    if (condition.includes('clear') || condition.includes('sun')) return 'weather-card--clear';
    if (condition.includes('cloud')) return 'weather-card--cloudy';
    if (condition.includes('rain')) return 'weather-card--rain';
    if (condition.includes('snow')) return 'weather-card--snow';
    if (condition.includes('thunder')) return 'weather-card--thunderstorm';
    if (condition.includes('fog') || condition.includes('mist')) return 'weather-card--fog';
    return '';
  };

  const weatherClass = getWeatherClass(condition || '');

  return (
    <div
      className={`weather-card ${weatherClass}`}
      role="article"
      aria-labelledby={`weather-${cityName.toLowerCase().replace(/\s+/g, '-')}-title`}
      tabIndex="0"
    >
      <div className="weather-card__header">
        <h3
          id={`weather-${cityName.toLowerCase().replace(/\s+/g, '-')}-title`}
          className="weather-card__city"
        >
          {cityName}
        </h3>
        <span className="weather-card__country" aria-label={`Country: ${country}`}>
          {country}
        </span>
      </div>

      <div className="weather-card__content">
        <div className="weather-card__icon-container">
          <div
            className={`weather-card__icon weather-card__icon--${icon}`}
            aria-label={`Weather condition: ${description}`}
            role="img"
          >
            {getWeatherIcon(icon)}
          </div>
        </div>

        <div className="weather-card__temperature" role="group" aria-label="Temperature">
          <span
            className="weather-card__temp-value"
            aria-label={`Temperature: ${Math.round(temperature.value)} degrees Celsius`}
          >
            {Math.round(temperature.value)}
          </span>
          <span className="weather-card__temp-unit" aria-hidden="true">°C</span>
        </div>

        <p className="weather-card__description" aria-label={`Weather description: ${description}`}>
          {description}
        </p>

        <div className="weather-card__details" role="group" aria-label="Additional weather details">
          {forecast.humidity && (
            <div className="weather-card__detail" role="group">
              <span className="weather-card__detail-label" id={`humidity-${cityName.toLowerCase().replace(/\s+/g, '-')}`}>
                Humidity
              </span>
              <span
                className="weather-card__detail-value"
                aria-labelledby={`humidity-${cityName.toLowerCase().replace(/\s+/g, '-')}`}
                aria-label={`${forecast.humidity} percent humidity`}
              >
                {forecast.humidity}%
              </span>
            </div>
          )}
          {forecast.windSpeed && (
            <div className="weather-card__detail" role="group">
              <span className="weather-card__detail-label" id={`wind-${cityName.toLowerCase().replace(/\s+/g, '-')}`}>
                Wind
              </span>
              <span
                className="weather-card__detail-value"
                aria-labelledby={`wind-${cityName.toLowerCase().replace(/\s+/g, '-')}`}
                aria-label={`${forecast.windSpeed} kilometers per hour wind speed`}
              >
                {forecast.windSpeed} km/h
              </span>
            </div>
          )}
        </div>

        {/* Last updated timestamp */}
        {cityData.lastUpdated && (
          <div className="weather-card__last-updated" role="group" aria-label="Data freshness">
            <span
              className="weather-card__last-updated-text"
              aria-live="polite"
              aria-label={`Data for ${cityName} last updated ${formatLastUpdated(cityData.lastUpdated) || 'recently'}`}
            >
              Updated {formatLastUpdated(cityData.lastUpdated) || 'recently'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced weather icon mapping function with comprehensive conditions
const getWeatherIcon = (iconType) => {
  const iconMap = {
    // Clear sky conditions
    'clear_day': '☀️',
    'clear_night': '🌙',
    'clearsky': '☀️',

    // Partly cloudy conditions
    'partly_cloudy_day': '⛅',
    'partly_cloudy_night': '☁️',
    'partlycloudy': '⛅',
    'fair': '🌤️',

    // Cloudy conditions
    'cloudy': '☁️',

    // Rain conditions
    'light_rain': '🌦️',
    'lightrain': '🌦️',
    'rain': '🌧️',
    'heavy_rain': '⛈️',
    'heavyrain': '⛈️',

    // Snow conditions
    'light_snow': '🌨️',
    'lightsnow': '🌨️',
    'snow': '❄️',
    'heavy_snow': '🌨️',
    'heavysnow': '🌨️',

    // Thunderstorm conditions
    'thunderstorm': '⛈️',
    'thunder': '⛈️',

    // Fog conditions
    'fog': '🌫️',
    'mist': '🌫️',

    // Wind conditions
    'wind': '💨',
    'windy': '💨',

    // Unknown/default
    'unknown': '🌤️',
    'default': '🌤️'
  };

  return iconMap[iconType] || iconMap.default;
};

export default WeatherCard;