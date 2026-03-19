# Requirements Document

> GitHub Issue: https://github.com/haakond/terraform-aws-weather-forecast/issues/10

## Introduction

This feature adds two enhancements to each city's weather card in the forecast web app:

1. A CSS animation that visually represents the forecasted weather condition (e.g. animated rain drops, spinning sun, drifting clouds)
2. A plain-text weather summary that describes the forecast in natural language, including wind speed and direction

The backend already exposes `condition`, `icon`, `windSpeed`, and `description` fields in the API response. This feature is primarily a frontend change to the `WeatherCard` component, with a minor backend extension to expose wind direction.

## Glossary

- **WeatherCard**: The React component that displays forecast data for a single city
- **Weather_Animation**: A CSS-based animated visual element rendered inside a WeatherCard that corresponds to the forecasted weather condition
- **Text_Summary**: A plain-text sentence or short paragraph describing tomorrow's forecast for a city, including temperature, condition, and wind
- **Condition**: A normalised weather condition string (e.g. `clearsky`, `rain`, `snow`) derived from the met.no `symbol_code`
- **Wind_Speed**: Wind speed in metres per second (m/s) as returned by the met.no API via the `windSpeed` field
- **Wind_Direction**: Wind direction in degrees (0–360) from north, as returned by the met.no API via the `wind_from_direction` instant detail
- **Reduced_Motion**: The `prefers-reduced-motion` CSS media query, used to respect user accessibility preferences
- **WeatherDisplay**: The parent React component that renders all four WeatherCards

## Requirements

### Requirement 1: Weather Animation per City Card

**User Story:** As an end user, I want to see an animation that corresponds to the forecasted weather for each city, so that I can understand the forecast at a glance without reading text.

#### Acceptance Criteria

1. WHEN a WeatherCard renders with a known `condition`, THE Weather_Animation SHALL display an animation that visually corresponds to that condition (e.g. animated sun rays for `clearsky`, falling drops for `rain`, drifting flakes for `snow`)
2. THE WeatherCard SHALL support distinct animations for the following conditions: `clearsky`, `partlycloudy`, `cloudy`, `rain`, `snow`, `fog`, `thunderstorm`
3. IF the `condition` value is unknown or absent, THEN THE Weather_Animation SHALL display a neutral default animation (e.g. slowly drifting clouds)
4. WHILE the WeatherCard is in a loading state, THE Weather_Animation SHALL NOT be rendered
5. WHILE the WeatherCard is in an error state, THE Weather_Animation SHALL NOT be rendered
6. THE Weather_Animation SHALL be implemented using CSS animations using only `transform` and `opacity` properties to ensure rendering performance
7. WHERE the user has enabled `prefers-reduced-motion`, THE Weather_Animation SHALL reduce or eliminate motion while preserving the static weather visual
8. THE Weather_Animation SHALL be fully visible and correctly sized on viewport widths from 320px to 1440px

### Requirement 2: Plain-Text Weather Summary

**User Story:** As an end user, I want to see a plain-text description of the forecast for each city including wind information, so that I can quickly understand the conditions in words.

#### Acceptance Criteria

1. WHEN a WeatherCard renders with valid forecast data, THE Text_Summary SHALL display a human-readable sentence describing the forecast including temperature, condition description, and wind speed
2. THE Text_Summary SHALL display wind speed in km/h, converted from the m/s value provided by the API (1 m/s = 3.6 km/h), rounded to the nearest whole number
3. WHERE wind direction data is available, THE Text_Summary SHALL include a cardinal or intercardinal direction label (e.g. "from the north-west") derived from the `wind_from_direction` degree value
4. IF wind speed data is absent from the API response, THEN THE Text_Summary SHALL display the temperature and condition description without a wind component
5. THE Text_Summary SHALL use sentence case and plain English (e.g. "Partly cloudy with light winds of 12 km/h from the south-west. High of 14°C.")
6. WHILE the WeatherCard is in a loading state, THE Text_Summary SHALL NOT be rendered
7. WHILE the WeatherCard is in an error state, THE Text_Summary SHALL NOT be rendered
8. THE Text_Summary SHALL be readable at all viewport widths from 320px to 1440px without horizontal overflow

### Requirement 3: Backend Wind Direction Exposure

**User Story:** As a frontend developer, I want the API response to include wind direction, so that the text summary can display a meaningful wind description.

#### Acceptance Criteria

1. WHEN the Lambda handler extracts tomorrow's forecast from the met.no timeseries, THE Lambda_Handler SHALL include the `wind_from_direction` value (degrees, 0–360) from the `instant.details` block in the forecast response
2. THE Lambda_Handler SHALL expose wind direction as a `windDirection` field (numeric, degrees) alongside the existing `windSpeed` field in the city forecast JSON
3. IF the `wind_from_direction` field is absent from the met.no response, THEN THE Lambda_Handler SHALL set `windDirection` to `null` in the response without raising an error
4. THE WeatherForecast data model SHALL include an optional `wind_direction` field of type `Optional[float]` validated to the range 0–360 inclusive
