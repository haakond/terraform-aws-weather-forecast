import React from 'react';
import PropTypes from 'prop-types';
import { convertWindSpeed, getCardinalDirection } from '../utils/weatherUtils';

const WeatherTextSummary = ({ forecast }) => {
  if (!forecast) return null;

  const { temperature, description, windSpeed, windDirection } = forecast;

  const desc = description ?? '';
  const temp = temperature?.value != null ? Math.round(temperature.value) : null;

  let sentence;

  if (windSpeed != null) {
    const kmh = convertWindSpeed(windSpeed);
    if (windDirection != null) {
      const direction = getCardinalDirection(windDirection);
      sentence = `${desc} with light winds of ${kmh} km/h from the ${direction}.`;
    } else {
      sentence = `${desc} with winds of ${kmh} km/h.`;
    }
  } else {
    sentence = `${desc}.`;
  }

  // Ensure sentence case: first character uppercase
  sentence = sentence.charAt(0).toUpperCase() + sentence.slice(1);

  const tempClause = temp != null ? ` High of ${temp}°C.` : '';

  return (
    <p className="weather-text-summary">
      {sentence}{tempClause}
    </p>
  );
};

WeatherTextSummary.propTypes = {
  forecast: PropTypes.shape({
    temperature: PropTypes.shape({ value: PropTypes.number }),
    description: PropTypes.string,
    windSpeed: PropTypes.number,
    windDirection: PropTypes.number,
  }),
};

export default WeatherTextSummary;
