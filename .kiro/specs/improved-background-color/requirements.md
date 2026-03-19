> GitHub Issue: https://github.com/haakond/terraform-aws-weather-forecast/issues/6

# Requirements Document

## Introduction

The weather forecast application currently uses a blue-purple to purple gradient (`#667eea` → `#764ba2`) as the primary background for the weather display and weather cards. End users find the background too purple and want it shifted to be more distinctly blue. This feature updates the default background gradient to use blue-dominant colors while preserving the existing gradient style and all weather-condition-specific card backgrounds.

## Glossary

- **WeatherDisplay**: The full-page container component (`WeatherDisplay.css`) that renders the main application background
- **WeatherCard**: The individual city forecast card component (`WeatherCard.css`) that uses the default gradient when no weather-condition class is applied
- **Default_Gradient**: The fallback gradient applied to `.weather-display` and `.weather-card` when no weather-condition-specific class overrides it
- **Weather_Condition_Gradient**: A gradient applied to `.weather-card` based on the current weather condition (clear, cloudy, rain, snow, thunderstorm, fog)

## Requirements

### Requirement 1: Update Default Background Gradient to Blue-Dominant Colors

**User Story:** As an end user, I want the application background to appear more blue than purple, so that the visual experience feels cooler and more sky-like.

#### Acceptance Criteria

1. THE WeatherDisplay SHALL render the `.weather-display` background using a gradient where the blue channel value of the start color is greater than the red channel value of the start color.
2. THE WeatherDisplay SHALL render the `.weather-display` background using a gradient where the blue channel value of the end color is greater than the red channel value of the end color.
3. WHEN the Default_Gradient is applied, THE WeatherCard SHALL use the same blue-dominant gradient as the WeatherDisplay background.
4. THE WeatherDisplay SHALL preserve the existing 135-degree diagonal gradient direction.
5. THE WeatherDisplay SHALL maintain a smooth two-stop gradient (0% start color, 100% end color).

### Requirement 2: Preserve Weather-Condition-Specific Card Backgrounds

**User Story:** As an end user, I want weather-condition card backgrounds to remain unchanged, so that the visual cues for different weather types are not disrupted.

#### Acceptance Criteria

1. WHEN a `.weather-card--clear` class is applied, THE WeatherCard SHALL continue to render the existing clear-weather gradient unchanged.
2. WHEN a `.weather-card--cloudy` class is applied, THE WeatherCard SHALL continue to render the existing cloudy-weather gradient unchanged.
3. WHEN a `.weather-card--rain` class is applied, THE WeatherCard SHALL continue to render the existing rain-weather gradient unchanged.
4. WHEN a `.weather-card--snow` class is applied, THE WeatherCard SHALL continue to render the existing snow-weather gradient unchanged.
5. WHEN a `.weather-card--thunderstorm` class is applied, THE WeatherCard SHALL continue to render the existing thunderstorm-weather gradient unchanged.
6. WHEN a `.weather-card--fog` class is applied, THE WeatherCard SHALL continue to render the existing fog-weather gradient unchanged.

### Requirement 3: Preserve Dark Mode and Accessibility Backgrounds

**User Story:** As an end user using dark mode or high-contrast settings, I want the background adjustments to not break my display preferences, so that the application remains usable under all system settings.

#### Acceptance Criteria

1. WHILE the `prefers-color-scheme: dark` media query is active, THE WeatherDisplay SHALL continue to render the existing dark-mode gradient (`#1e293b` → `#334155`) unchanged.
2. WHILE the `prefers-contrast: high` media query is active, THE WeatherDisplay SHALL continue to apply the existing high-contrast background override unchanged.
3. WHILE the `print` media query is active, THE WeatherDisplay SHALL continue to render a white background unchanged.
