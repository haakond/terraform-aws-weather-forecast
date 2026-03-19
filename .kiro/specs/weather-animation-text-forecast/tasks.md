# Implementation Plan: Weather Animation & Text Forecast

## Overview

Extend the backend to expose `windDirection`, add two new frontend components (`WeatherAnimation` and `WeatherTextSummary`), and wire them into `WeatherCard`. Implementation proceeds backend-first, then shared utilities, then components, then integration.

## Tasks

- [ ] 1. Extend backend to expose windDirection
  - [ ] 1.1 Add `windDirection` extraction to `extract_tomorrow_forecast` in `src/lambda_handler.py`
    - Read `wind_from_direction` from `instant_data` using `.get("wind_from_direction", None)`
    - Add `"windDirection"` key to the returned `forecast_data` dict alongside `windSpeed`
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ]* 1.2 Write property test for windDirection extraction round-trip (Property 7)
    - **Property 7: windDirection extraction round-trip**
    - Use `@given(st.floats(min_value=0, max_value=360))` to inject `wind_from_direction` into a synthetic timeseries entry
    - Assert `extract_tomorrow_forecast` returns `windDirection` equal to the input value (within floating-point tolerance)
    - `@settings(max_examples=100)`
    - Add to `tests/unit/test_lambda_handler.py`
    - **Validates: Requirements 3.1, 3.2**

  - [ ]* 1.3 Write property test for missing wind_from_direction (Property 8)
    - **Property 8: Missing wind_from_direction yields null windDirection without error**
    - Use timeseries entries with `wind_from_direction` key absent
    - Assert `windDirection` is `None` and no exception is raised
    - `@settings(max_examples=100)`
    - Add to `tests/unit/test_lambda_handler.py`
    - **Validates: Requirements 3.3**

  - [ ]* 1.4 Write unit tests for windDirection extraction
    - `wind_from_direction` present → `windDirection` equals that value
    - `wind_from_direction` absent → `windDirection` is `None`
    - Full `extract_tomorrow_forecast` output shape includes `windDirection` key
    - Add to `tests/unit/test_lambda_handler.py`
    - _Requirements: 3.1, 3.2, 3.3_

- [ ] 2. Checkpoint — ensure backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 3. Implement shared frontend utility functions
  - [ ] 3.1 Create `frontend/src/utils/weatherUtils.js` with `convertWindSpeed` and `getCardinalDirection`
    - `convertWindSpeed(ms)`: returns `Math.round(ms * 3.6)`
    - `getCardinalDirection(degrees)`: 16-point compass lookup using 22.5° sectors as specified in the design
    - Export both functions
    - _Requirements: 2.2, 2.3_

  - [ ]* 3.2 Write property test for wind speed conversion (Property 1)
    - **Property 1: Wind speed unit conversion is correct**
    - Use `fc.float({ min: 0, max: 200 })` → assert `convertWindSpeed(v) === Math.round(v * 3.6)`
    - `// Feature: weather-animation-text-forecast, Property 1: Wind speed unit conversion is correct`
    - Add to `frontend/src/utils/weatherUtils.test.js`
    - **Validates: Requirements 2.2**

  - [ ]* 3.3 Write property test for cardinal direction validity and periodicity (Property 2)
    - **Property 2: Cardinal direction is valid and periodic for all degree inputs**
    - Use `fc.float({ min: 0, max: 360 })` → assert result is a non-empty string from the 16-label set AND equals `getCardinalDirection(d % 360)`
    - `// Feature: weather-animation-text-forecast, Property 2: Cardinal direction is valid and periodic for all degree inputs`
    - Add to `frontend/src/utils/weatherUtils.test.js`
    - **Validates: Requirements 2.3**

- [ ] 4. Implement `WeatherTextSummary` component
  - [ ] 4.1 Create `frontend/src/components/WeatherTextSummary.js`
    - Import `convertWindSpeed` and `getCardinalDirection` from `weatherUtils`
    - Accept `forecast` prop (shape: `temperature`, `description`, `windSpeed`, `windDirection`)
    - Return `null` if `forecast` is null/undefined
    - Build sentence per design spec: with wind+direction / wind only / no wind variants
    - Render as `<p className="weather-text-summary">`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 4.2 Write property test for text summary with wind present (Property 3)
    - **Property 3: Text summary contains required fields when wind is present and uses sentence case**
    - Use `fc.record({ temperature: ..., description: fc.string(), windSpeed: fc.float({ min: 0.1 }), windDirection: fc.float({ min: 0, max: 360 }) })`
    - Assert summary contains km/h value, a direction label, starts uppercase, ends with period
    - `// Feature: weather-animation-text-forecast, Property 3: Text summary contains required fields when wind is present and uses sentence case`
    - Add to `frontend/src/components/WeatherTextSummary.test.js`
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.5**

  - [ ]* 4.3 Write property test for text summary without wind (Property 4)
    - **Property 4: Text summary omits wind when windSpeed is absent**
    - Forecast objects with `windSpeed: null` or absent → assert summary does not contain "km/h" or any of the 16 cardinal direction labels
    - `// Feature: weather-animation-text-forecast, Property 4: Text summary omits wind when windSpeed is absent`
    - Add to `frontend/src/components/WeatherTextSummary.test.js`
    - **Validates: Requirements 2.4**

  - [ ]* 4.4 Write unit tests for WeatherTextSummary
    - Wind + direction → correct sentence format
    - Wind, no direction → omits direction clause
    - No wind → omits wind clause entirely
    - Null forecast → renders nothing
    - Add to `frontend/src/components/WeatherTextSummary.test.js`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 5. Implement `WeatherAnimation` component
  - [ ] 5.1 Create `frontend/src/components/WeatherAnimation.js`
    - Accept `condition` prop
    - Map condition to one of 7 scenes; unknown/absent falls back to `cloudy`
    - Render purely decorative CSS elements; wrap in `aria-hidden="true"`
    - Add `PropTypes` validation
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ] 5.2 Create `frontend/src/components/WeatherAnimation.css`
    - Define keyframe animations using only `transform` and `opacity` properties for all 7 scenes
    - Include `@media (prefers-reduced-motion: reduce)` block that removes motion while preserving static visuals
    - Ensure component is fully visible and correctly sized from 320px to 1440px viewport width
    - _Requirements: 1.6, 1.7, 1.8_

  - [ ]* 5.3 Write property test for known conditions rendering (Property 5)
    - **Property 5: WeatherAnimation renders a condition-specific scene for all known conditions**
    - Use `fc.constantFrom('clearsky','partlycloudy','cloudy','rain','snow','fog','thunderstorm')` → render `WeatherAnimation`, assert at least one DOM element has a CSS class containing the condition name
    - `// Feature: weather-animation-text-forecast, Property 5: WeatherAnimation renders a condition-specific scene for all known conditions`
    - Add to `frontend/src/components/WeatherAnimation.test.js`
    - **Validates: Requirements 1.1, 1.2**

  - [ ]* 5.4 Write property test for unknown condition fallback (Property 6)
    - **Property 6: WeatherAnimation renders the cloudy fallback for unknown or absent conditions**
    - Use `fc.string()` filtered to exclude known conditions → assert rendered DOM matches the `cloudy` render
    - `// Feature: weather-animation-text-forecast, Property 6: WeatherAnimation renders the cloudy fallback for unknown or absent conditions`
    - Add to `frontend/src/components/WeatherAnimation.test.js`
    - **Validates: Requirements 1.3**

  - [ ]* 5.5 Write unit tests for WeatherAnimation
    - Each of the 7 known conditions renders the correct CSS class
    - Unknown condition renders `cloudy` fallback
    - Component has `aria-hidden="true"`
    - Add to `frontend/src/components/WeatherAnimation.test.js`
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 6. Checkpoint — ensure frontend utility and component tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Wire new components into `WeatherCard`
  - [ ] 7.1 Update `frontend/src/components/WeatherCard.js` to render `WeatherAnimation` and `WeatherTextSummary`
    - Import `WeatherAnimation` and `WeatherTextSummary`
    - Render `<WeatherAnimation condition={forecast.condition} />` above the emoji icon
    - Render `<WeatherTextSummary forecast={forecast} />` below the description
    - Both components are only rendered in the non-loading, non-error branch (already gated by existing conditional returns)
    - _Requirements: 1.4, 1.5, 2.6, 2.7_

  - [ ]* 7.2 Write integration tests for WeatherCard with new child components
    - `WeatherCard` with full forecast renders both `WeatherAnimation` and `WeatherTextSummary`
    - `WeatherCard` in loading state renders neither component
    - `WeatherCard` in error state renders neither component
    - Add to `frontend/src/components/WeatherCard.test.js`
    - _Requirements: 1.4, 1.5, 2.6, 2.7_

- [ ] 8. Final checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Close GitHub issue #10

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis (backend) and fast-check (frontend), both already project dependencies
- Checkpoints ensure incremental validation at backend, component, and integration levels
