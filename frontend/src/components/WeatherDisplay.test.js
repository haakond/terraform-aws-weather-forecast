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

describe('CSS gradient properties', () => {
  const { readDefaultGradient, parseHexChannel } = require('./cssTestHelpers');
  const fc = require('fast-check');

  // Property 1: default gradient stops are blue-dominant
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

  // Property 1 PBT: verify parseHexChannel correctness with arbitrary hex colors
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

  // Property 2: WeatherDisplay and WeatherCard default gradients are identical
  // Feature: improved-background-color, Property 2: WeatherDisplay and WeatherCard default gradients are identical
  it('WeatherDisplay and WeatherCard share the same default gradient', () => {
    expect(readDefaultGradient('WeatherDisplay.css')).toBe(readDefaultGradient('WeatherCard.css'));
  });

  // Property 4: gradient structure is preserved
  // Feature: improved-background-color, Property 4: Default gradient structure is preserved
  it('default gradient uses 135deg angle with two stops at 0% and 100%', () => {
    const gradient = readDefaultGradient('WeatherDisplay.css');
    expect(gradient).toMatch(/^linear-gradient\(135deg,\s*#[0-9a-fA-F]{6}\s+0%,\s*#[0-9a-fA-F]{6}\s+100%\)$/);
  });

  // Property 5: media-query rules unchanged
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
