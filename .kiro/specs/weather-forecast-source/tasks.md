# Implementation Plan: Weather Forecast Source Attribution

## Overview

Extend the Lambda response with static `source` and `source_url` fields, then render a new `Attribution` React component inside `WeatherDisplay`. Includes unit tests and property-based tests (hypothesis on the backend, fast-check on the frontend).

## Tasks

- [ ] 1. Extend backend API response with source fields
  - [ ] 1.1 Add `SOURCE` and `SOURCE_URL` module-level constants to `src/lambda_handler.py`
    - Define `SOURCE = "Norwegian Meteorological Institute"` and `SOURCE_URL = "https://api.met.no"` at module level
    - Inject both fields unconditionally into the dict returned by `get_weather_summary()`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1_
  - [ ] 1.2 Write unit tests for source fields in `tests/unit/test_lambda_handler.py`
    - Assert `source` and `source_url` are present in a normal success response (mocked DynamoDB cache hit)
    - Assert `source` and `source_url` are present when all city fetches raise exceptions
    - _Requirements: 2.3, 2.4_
  - [ ] 1.3 Write property test for Property 2: API response always contains source fields
    - **Property 2: API response always contains source fields**
    - **Validates: Requirements 2.1, 2.2, 2.3, 3.1**
    - Use `@given(st.lists(city_strategy(), min_size=1, max_size=4))` with mocked DynamoDB and API
    - Assert `result["source"] == "Norwegian Meteorological Institute"` and `result["source_url"] == "https://api.met.no"`
    - Minimum 100 examples (`@settings(max_examples=100)`)
  - [ ] 1.4 Write property test for Property 3: source fields present even on total fetch failure
    - **Property 3: Source fields present even on total fetch failure**
    - **Validates: Requirements 2.4**
    - Patch `fetch_weather_data` to raise `Exception` and `get_cached_weather_data` to return `None`
    - Assert both source fields are still present in the response
    - Minimum 100 examples (`@settings(max_examples=100)`)

- [ ] 2. Create `Attribution` React component
  - [ ] 2.1 Create `frontend/src/components/Attribution.js` and `Attribution.css`
    - Render a `<p className="attribution">` containing an `<a>` with `target="_blank" rel="noopener noreferrer"`
    - Apply CSS from the design: `font-size: 0.75rem`, `color: rgba(255,255,255,0.75)`, `text-align: center`, `margin: 1.5rem auto 0`
    - Include `prefers-contrast: high` media query rule setting `color: #ffffff`
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.2, 4.3_
  - [ ] 2.2 Integrate `Attribution` into `WeatherDisplay`
    - Import `Attribution` in `frontend/src/components/WeatherDisplay.js`
    - Render `<Attribution source={weatherData.source} sourceUrl={weatherData.source_url} />` conditionally when `weatherData` is non-null
    - _Requirements: 1.1, 1.2, 1.4, 3.2_
  - [ ] 2.3 Write unit tests for `Attribution` in `frontend/src/components/Attribution.test.js`
    - Render with known props and assert link text equals `source` and `href` equals `sourceUrl`
    - Assert `target="_blank"` and `rel="noopener noreferrer"` are set
    - _Requirements: 1.1, 1.2_
  - [ ] 2.4 Write property test for Property 1: WeatherDisplay renders attribution name and link
    - **Property 1: WeatherDisplay renders attribution name and link**
    - **Validates: Requirements 1.1, 1.2**
    - Use `fc.record({ source: fc.string(), source_url: fc.webUrl() })` and assert `getByRole('link')` has correct text and `href`
    - Minimum 100 runs (`{ numRuns: 100 }`)
  - [ ] 2.5 Extend `WeatherDisplay.test.js` with attribution integration test
    - When `weatherData` includes `source`/`source_url`, assert the Attribution link is present in the rendered output
    - _Requirements: 1.4, 3.2_

- [ ] 3. Checkpoint — ensure all tests pass
  - Run `pytest` in the repo root and `npm test --watchAll=false` in `frontend/`. Confirm both suites are green. Ask the user if any questions arise.

- [ ] 4. Close GitHub issue #7
