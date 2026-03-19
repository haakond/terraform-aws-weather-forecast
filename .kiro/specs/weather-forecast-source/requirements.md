> GitHub Issue: https://github.com/haakond/terraform-aws-weather-forecast/issues/7

# Requirements Document

## Introduction

The weather forecast application currently displays tomorrow's forecast for Oslo, Paris, London, and Barcelona without indicating where the data comes from. End users want to see clear attribution for the weather data source so they can trust the forecasts they rely on. This feature adds visible source attribution — crediting the Norwegian Meteorological Institute (api.met.no) — to the frontend UI.

## Glossary

- **WeatherDisplay**: The full-page container component that renders the main application view
- **WeatherCard**: The individual city forecast card component displaying tomorrow's weather
- **Attribution**: A visible UI element crediting the data provider, including the provider name and a link to their service
- **Data_Provider**: The Norwegian Meteorological Institute, accessed via api.met.no, which supplies all forecast data
- **API_Response**: The JSON payload returned by the backend Lambda/API Gateway to the frontend

## Requirements

### Requirement 1: Display Data Source Attribution in the UI

**User Story:** As an end user, I want to see which source the weather forecasts are coming from, so that I can be confident about tomorrow's weather.

#### Acceptance Criteria

1. THE WeatherDisplay SHALL render an Attribution element that identifies the Data_Provider by name ("Norwegian Meteorological Institute").
2. THE WeatherDisplay SHALL render the Attribution element as a hyperlink pointing to `https://api.met.no`.
3. THE Attribution SHALL be visible on all supported viewport sizes, including mobile.
4. WHEN forecast data is displayed for any city, THE WeatherDisplay SHALL show the Attribution element on the same page.

### Requirement 2: Attribution Included in API Response

**User Story:** As a developer, I want the backend to include source attribution metadata in the API response, so that the frontend can display it without hardcoding provider details.

#### Acceptance Criteria

1. THE API_Response SHALL include a `source` field containing the Data_Provider name ("Norwegian Meteorological Institute").
2. THE API_Response SHALL include a `source_url` field containing the URL `https://api.met.no`.
3. WHEN the backend successfully fetches forecast data from the Data_Provider, THE API_Response SHALL populate the `source` and `source_url` fields.
4. IF the backend fails to fetch data from the Data_Provider, THEN THE API_Response SHALL still include the `source` and `source_url` fields with their static values.

### Requirement 3: Attribution Persists Across Cache Hits

**User Story:** As an end user, I want to see the data source even when the forecast is served from cache, so that attribution is always present regardless of how the data was retrieved.

#### Acceptance Criteria

1. WHEN forecast data is served from the DynamoDB cache, THE API_Response SHALL include the `source` and `source_url` fields.
2. WHEN forecast data is served from the CloudFront cache, THE WeatherDisplay SHALL render the Attribution element.

### Requirement 4: Attribution Styling Consistent with Application Design

**User Story:** As an end user, I want the attribution to look like it belongs in the app, so that it does not feel like an afterthought or distract from the forecast.

#### Acceptance Criteria

1. THE Attribution SHALL be rendered in a font size no larger than the secondary text used in WeatherCard components.
2. WHILE the `prefers-color-scheme: dark` media query is active, THE Attribution SHALL remain legible against the dark-mode background.
3. WHILE the `prefers-contrast: high` media query is active, THE Attribution SHALL meet the existing high-contrast styling rules applied to the rest of the application.
