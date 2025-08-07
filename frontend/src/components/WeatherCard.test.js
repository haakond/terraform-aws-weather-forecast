import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import WeatherCard from './WeatherCard';

// Mock weather data
const mockCityData = {
  cityId: 'oslo',
  cityName: 'Oslo',
  country: 'Norway',
  coordinates: { lat: 59.9139, lon: 10.7522 },
  forecast: {
    date: '2024-01-15',
    temperature: {
      value: -2,
      unit: 'celsius'
    },
    condition: 'partly_cloudy',
    description: 'Partly cloudy',
    icon: 'partly_cloudy_day',
    humidity: 75,
    windSpeed: 12
  },
  lastUpdated: '2024-01-14T10:30:00Z',
  ttl: 1705230600
};

describe('WeatherCard', () => {
  test('renders weather data correctly', () => {
    render(<WeatherCard cityData={mockCityData} />);

    expect(screen.getByText('Oslo')).toBeInTheDocument();
    expect(screen.getByText('Norway')).toBeInTheDocument();
    expect(screen.getByText('-2')).toBeInTheDocument();
    expect(screen.getByText('°C')).toBeInTheDocument();
    expect(screen.getByText('Partly cloudy')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
    expect(screen.getByText('12 km/h')).toBeInTheDocument();
  });

  test('renders loading state correctly', () => {
    render(<WeatherCard cityData={mockCityData} isLoading={true} />);

    // Check for skeleton loading elements
    expect(document.querySelector('.weather-card--loading')).toBeInTheDocument();
    expect(document.querySelector('.weather-card__skeleton')).toBeInTheDocument();
  });

  test('renders error state correctly', () => {
    const mockRetry = jest.fn();
    render(
      <WeatherCard
        cityData={mockCityData}
        error="Network error"
        onRetry={mockRetry}
      />
    );

    expect(screen.getByText('Unable to load weather data')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();

    // Test retry button functionality
    fireEvent.click(screen.getByText('Retry'));
    expect(mockRetry).toHaveBeenCalledTimes(1);
  });

  test('renders no data state correctly', () => {
    render(<WeatherCard cityData={null} />);

    expect(screen.getByText('No Data')).toBeInTheDocument();
    expect(screen.getByText('Weather data not available')).toBeInTheDocument();
  });

  test('handles missing forecast data', () => {
    const incompleteData = {
      cityName: 'Oslo',
      country: 'Norway'
    };

    render(<WeatherCard cityData={incompleteData} />);

    expect(screen.getByText('No Data')).toBeInTheDocument();
  });

  test('applies correct accessibility attributes', () => {
    render(<WeatherCard cityData={mockCityData} />);

    const weatherIcon = document.querySelector('.weather-card__icon');
    expect(weatherIcon).toHaveAttribute('aria-label', 'Weather condition: Partly cloudy');
  });

  test('displays weather icon correctly', () => {
    render(<WeatherCard cityData={mockCityData} />);

    const weatherIcon = document.querySelector('.weather-card__icon');
    expect(weatherIcon).toHaveTextContent('⛅'); // partly_cloudy_day emoji
  });
});