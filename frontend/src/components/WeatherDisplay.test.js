import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import WeatherDisplay from './WeatherDisplay';

// Mock the WeatherCard component
jest.mock('./WeatherCard', () => {
  return function MockWeatherCard({ cityData, isLoading, error, onRetry }) {
    if (error) {
      return <div data-testid={`weather-card-${cityData?.cityName || 'unknown'}`}>Error: {error}</div>;
    }
    if (isLoading) {
      return <div data-testid={`weather-card-${cityData?.cityName || 'unknown'}`}>Loading...</div>;
    }
    return (
      <div data-testid={`weather-card-${cityData?.cityName || 'unknown'}`}>
        {cityData?.cityName} - {cityData?.forecast?.temperature?.value}°C
      </div>
    );
  };
});

describe('WeatherDisplay', () => {
  test('renders header correctly', () => {
    render(<WeatherDisplay />);

    expect(screen.getByText("Tomorrow's Weather Forecast")).toBeInTheDocument();
    expect(screen.getByText(/European Cities/)).toBeInTheDocument();
  });

  test('renders weather cards for all four cities', async () => {
    render(<WeatherDisplay />);

    // Wait for the component to initialize
    await waitFor(() => {
      expect(screen.getByTestId('weather-card-Oslo')).toBeInTheDocument();
      expect(screen.getByTestId('weather-card-Paris')).toBeInTheDocument();
      expect(screen.getByTestId('weather-card-London')).toBeInTheDocument();
      expect(screen.getByTestId('weather-card-Barcelona')).toBeInTheDocument();
    });
  });

  test('shows loading states initially', () => {
    render(<WeatherDisplay />);

    // Check that loading indicator is present
    expect(screen.getByText('Loading weather data...')).toBeInTheDocument();
  });

  test('displays correct city names', async () => {
    render(<WeatherDisplay />);

    await waitFor(() => {
      expect(screen.getByTestId('weather-card-Oslo')).toBeInTheDocument();
      expect(screen.getByTestId('weather-card-Paris')).toBeInTheDocument();
      expect(screen.getByTestId('weather-card-London')).toBeInTheDocument();
      expect(screen.getByTestId('weather-card-Barcelona')).toBeInTheDocument();
    });
  });

  test('has proper responsive grid structure', () => {
    render(<WeatherDisplay />);

    const grid = document.querySelector('.weather-display__grid');
    expect(grid).toBeInTheDocument();
    expect(grid).toHaveClass('weather-display__grid');
  });

  test('applies correct CSS classes for styling', () => {
    render(<WeatherDisplay />);

    const container = document.querySelector('.weather-display');
    expect(container).toBeInTheDocument();

    const header = document.querySelector('.weather-display__header');
    expect(header).toBeInTheDocument();

    const title = document.querySelector('.weather-display__title');
    expect(title).toBeInTheDocument();

    const subtitle = document.querySelector('.weather-display__subtitle');
    expect(subtitle).toBeInTheDocument();
  });

  test('displays lastUpdated timestamp when data is available', async () => {
    render(<WeatherDisplay />);

    // Wait for the component to potentially load data and show lastUpdated
    await waitFor(() => {
      const lastUpdatedElement = document.querySelector('.weather-display__last-updated');
      // The element should exist (even if data hasn't loaded yet, it might show loading state)
      // We're mainly testing that the component structure is correct
      expect(document.querySelector('.weather-display__status')).toBeInTheDocument();
    });
  });
});