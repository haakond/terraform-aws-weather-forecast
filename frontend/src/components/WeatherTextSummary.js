import React from 'react';
import './WeatherTextSummary.css';
import './WeatherCredits.css';

const WeatherTextSummary = ({
  weatherData = null,
  isLoading = false,
  error = null
}) => {
  // Handle loading state
  if (isLoading) {
    return (
      <div className="weather-text-summary weather-text-summary--loading">
        <div className="weather-text-summary__skeleton"></div>
      </div>
    );
  }

  // Handle error state
  if (error) {
    return (
      <div className="weather-text-summary weather-text-summary--error">
        <p className="weather-text-summary__error-message">
          ⚠️ Unable to load weather summary
        </p>
      </div>
    );
  }

  // Handle no data state
  if (!weatherData || !weatherData.cities || weatherData.cities.length === 0) {
    return (
      <div className="weather-text-summary weather-text-summary--no-data">
        <p className="weather-text-summary__no-data-message">
          No weather data available
        </p>
      </div>
    );
  }

  // Format weather data for each city
  const formatCityWeather = (city) => {
    if (!city || !city.forecast) {
      return `${city?.cityName || 'Unknown'}: No data`;
    }

    const { cityName, forecast } = city;
    const temp = forecast.temperature ? Math.round(forecast.temperature.value) : '--';
    const description = forecast.description || 'Unknown';

    return `${cityName}: ${temp}°C, ${description}`;
  };

  // Create text summary for all cities with line breaks for cinematic effect
  const summaryLines = weatherData.cities.map(formatCityWeather);

  return (
    <div
      className="credits-container"
      role="complementary"
      aria-label="Text-based weather summary with Star Wars credits effect"
      aria-live="polite"
      tabIndex="0"
    >
      <div className="credits-content" aria-hidden="false">
        <div className="credits-text">
          {summaryLines.map((line, index) => (
            <React.Fragment key={index}>
              {line}
              {index < summaryLines.length - 1 && <br />}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};

export default WeatherTextSummary;
