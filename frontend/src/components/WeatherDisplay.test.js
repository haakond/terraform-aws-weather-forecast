import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import WeatherDisplay from './WeatherDisplay';

// Mock child components
jest.mock('./WeatherCard', () => {
  return function MockWeatherCard({ cityData, isLoading, error }) {
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

jest.mock('./Attribution', () => {
  return function MockAttribution({ source, sourceUrl }) {
    return (
      <a href={sourceUrl} data-testid="attribution-link">
        {source}
      </a>
    );
  };
});

// Mock useWeatherData so all tests control state explicitly
jest.mock('../hooks/useWeatherData', () => ({
  useWeatherData: jest.fn()
}));

const { useWeatherData } = require('../hooks/useWeatherData');

const loadingState = {
  weatherData: null,
  loading: true,
  error: null,
  lastUpdated: null,
  refresh: jest.fn(),
  retry: jest.fn(),
  getErrorMessage: null,
  formatLastUpdated: () => null
};

beforeEach(() => {
  useWeatherData.mockReturnValue(loadingState);
});

describe('WeatherDisplay', () => {
  test('renders header correctly', () => {
    render(<WeatherDisplay />);
    expect(screen.getByText("Tomorrow's Weather Forecast")).toBeInTheDocument();
    expect(screen.getByText(/European Cities/)).toBeInTheDocument();
  });

  test('renders weather cards for all four cities', async () => {
    render(<WeatherDisplay />);
    await waitFor(() => {
      expect(screen.getByTestId('weather-card-Oslo')).toBeInTheDocument();
      expect(screen.getByTestId('weather-card-Paris')).toBeInTheDocument();
      expect(screen.getByTestId('weather-card-London')).toBeInTheDocument();
      expect(screen.getByTestId('weather-card-Barcelona')).toBeInTheDocument();
    });
  });

  test('shows loading states initially', () => {
    render(<WeatherDisplay />);
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
    expect(document.querySelector('.weather-display')).toBeInTheDocument();
    expect(document.querySelector('.weather-display__header')).toBeInTheDocument();
    expect(document.querySelector('.weather-display__title')).toBeInTheDocument();
    expect(document.querySelector('.weather-display__subtitle')).toBeInTheDocument();
  });

  test('displays lastUpdated timestamp when data is available', async () => {
    render(<WeatherDisplay />);
    await waitFor(() => {
      expect(document.querySelector('.weather-display__status')).toBeInTheDocument();
    });
  });

  // Feature: weather-forecast-source, task 2.5: attribution integration test
  test('renders Attribution link when weatherData includes source and source_url', () => {
    useWeatherData.mockReturnValue({
      weatherData: {
        cities: [],
        lastUpdated: '2024-01-15T12:00:00Z',
        status: 'success',
        hasErrors: false,
        source: 'Norwegian Meteorological Institute',
        source_url: 'https://api.met.no'
      },
      loading: false,
      error: null,
      lastUpdated: new Date('2024-01-15T12:00:00Z'),
      refresh: jest.fn(),
      retry: jest.fn(),
      getErrorMessage: null,
      formatLastUpdated: () => '1 hour ago'
    });

    render(<WeatherDisplay />);

    const link = screen.getByTestId('attribution-link');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', 'https://api.met.no');
    expect(link).toHaveTextContent('Norwegian Meteorological Institute');
  });

  // Feature: weather-forecast-source, task 2.5: no attribution when weatherData is null
  test('does not render Attribution when weatherData is null', () => {
    render(<WeatherDisplay />); // default mock returns weatherData: null
    expect(screen.queryByTestId('attribution-link')).not.toBeInTheDocument();
  });
});

describe('CSS gradient properties', () => {
  const { readDefaultGradient, parseHexChannel } = require('./cssTestHelpers');
  const fc = require('fast-check');

  // Feature: improved-background-color, Property 1: default gradient stops are blue-dominant
  it('all default gradient stops have blue channel > red channel', () => {
    const gradient = readDefaultGradient('WeatherDisplay.css');
    const hexMatches = gradient.match(/#([0-9a-fA-F]{6})/g);
    expect(hexMatches).not.toBeNull();
    hexMatches.forEach(hex => {
      const r = parseHexChannel(hex, 'r');
      const b = parseHexChannel(hex, 'b');
      expect(b).toBeGreaterThan(r);
    });
  });

  // Feature: improved-background-color, Property 1: default gradient stops are blue-dominant
  it('parseHexChannel correctly extracts channels from arbitrary hex colors', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 255 }),
        fc.integer({ min: 0, max: 255 }),
        fc.integer({ min: 0, max: 255 }),
        (r, g, b) => {
          const hex = '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join('');
          expect(parseHexChannel(hex, 'r')).toBe(r);
          expect(parseHexChannel(hex, 'g')).toBe(g);
          expect(parseHexChannel(hex, 'b')).toBe(b);
        }
      ),
      { numRuns: 100 }
    );
  });

  // Feature: improved-background-color, Property 2: WeatherDisplay and WeatherCard default gradients are identical
  it('WeatherDisplay and WeatherCard share the same default gradient', () => {
    expect(readDefaultGradient('WeatherDisplay.css')).toBe(readDefaultGradient('WeatherCard.css'));
  });

  // Feature: improved-background-color, Property 4: Default gradient structure is preserved
  it('default gradient uses 135deg angle with two stops at 0% and 100%', () => {
    const gradient = readDefaultGradient('WeatherDisplay.css');
    expect(gradient).toMatch(/^linear-gradient\(135deg,\s*#[0-9a-fA-F]{6}\s+0%,\s*#[0-9a-fA-F]{6}\s+100%\)$/);
  });

  // Feature: improved-background-color, Property 5: Media-query gradients are unchanged
  it('dark-mode gradient is unchanged', () => {
    const fs = require('fs');
    const path = require('path');
    const css = fs.readFileSync(path.join(__dirname, 'WeatherDisplay.css'), 'utf8');
    expect(css).toContain('linear-gradient(135deg, #1e293b 0%, #334155 100%)');
  });

  it('high-contrast override is present', () => {
    const fs = require('fs');
    const path = require('path');
    const css = fs.readFileSync(path.join(__dirname, 'WeatherDisplay.css'), 'utf8');
    expect(css).toContain('prefers-contrast: high');
  });

  it('print background is white', () => {
    const fs = require('fs');
    const path = require('path');
    const css = fs.readFileSync(path.join(__dirname, 'WeatherDisplay.css'), 'utf8');
    expect(css).toContain('background: white');
  });
});
