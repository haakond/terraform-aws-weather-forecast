import React from 'react';
import { render, cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';
import Attribution from './Attribution';
const fc = require('fast-check');

describe('Attribution', () => {
  test('renders link with correct text and href', () => {
    const { getByRole } = render(
      <Attribution source="Norwegian Meteorological Institute" sourceUrl="https://api.met.no" />
    );
    const link = getByRole('link');
    expect(link).toHaveTextContent('Norwegian Meteorological Institute');
    expect(link).toHaveAttribute('href', 'https://api.met.no');
  });

  test('sets target="_blank" and rel="noopener noreferrer"', () => {
    const { getByRole } = render(
      <Attribution source="Norwegian Meteorological Institute" sourceUrl="https://api.met.no" />
    );
    const link = getByRole('link');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  // Feature: weather-forecast-source, Property 1: WeatherDisplay renders attribution name and link
  test('property: link text and href match any source/sourceUrl props', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1 }).filter(s => s.trim().length > 0),
        fc.webUrl(),
        (source, sourceUrl) => {
          const { getByRole } = render(
            <Attribution source={source} sourceUrl={sourceUrl} />
          );
          const link = getByRole('link');
          expect(link.textContent).toBe(source);
          expect(link).toHaveAttribute('href', sourceUrl);
          cleanup();
        }
      ),
      { numRuns: 100 }
    );
  });
});
