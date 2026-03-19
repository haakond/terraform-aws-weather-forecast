# Implementation Plan: Improved Background Color

## Overview

Pure CSS change updating the default gradient in `WeatherDisplay.css` and `WeatherCard.css` from `#667eea → #764ba2` to `#4158d0 → #2575fc`, with property-based and unit tests using fast-check.

## Tasks

- [ ] 1. Add fast-check dev dependency
  - Run `npm install --save-dev fast-check` in the `frontend/` directory
  - Verify it appears in `package.json` devDependencies
  - _Requirements: Testing Strategy (design.md)_

- [ ] 2. Update CSS gradient values
  - [ ] 2.1 Update `.weather-display` in `frontend/src/components/WeatherDisplay.css`
    - Replace `linear-gradient(135deg, #667eea 0%, #764ba2 100%)` with `linear-gradient(135deg, #4158d0 0%, #2575fc 100%)`
    - Leave all other rules (dark mode, high-contrast, print, animations, breakpoints) untouched
    - _Requirements: 1.1, 1.2, 1.4, 1.5_
  - [ ] 2.2 Update `.weather-card` in `frontend/src/components/WeatherCard.css`
    - Replace `linear-gradient(135deg, #667eea 0%, #764ba2 100%)` with `linear-gradient(135deg, #4158d0 0%, #2575fc 100%)`
    - Leave all condition-specific overrides (`.weather-card--clear`, `--cloudy`, `--rain`, `--snow`, `--thunderstorm`, `--fog`) untouched
    - _Requirements: 1.3, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [ ] 3. Write CSS gradient tests in `frontend/src/components/WeatherDisplay.test.js` and `WeatherCard.test.js`
  - [ ] 3.1 Add test helpers: `readDefaultGradient(filename)` and `parseHexChannel(hex, channel)`
    - `readDefaultGradient` reads the CSS file and extracts the gradient string from the base selector
    - `parseHexChannel` parses a 6-digit hex color and returns the numeric value of `r`, `g`, or `b`
    - Place helpers in a shared file `frontend/src/components/cssTestHelpers.js`
    - _Requirements: 1.1, 1.2, 1.3_
  - [ ]* 3.2 Write property test for Property 1: default gradient stops are blue-dominant
    - **Property 1: Default gradient stops are blue-dominant**
    - **Validates: Requirements 1.1, 1.2**
    - Use `fc.hexaString` or `fc.integer` to generate arbitrary hex colors and verify `parseHexChannel` correctness, then assert the actual CSS stop values satisfy `blue > red`
    - Tag: `Feature: improved-background-color, Property 1: default gradient stops are blue-dominant`
    - Minimum 100 runs (`{ numRuns: 100 }`)
  - [ ]* 3.3 Write property test for Property 2: WeatherDisplay and WeatherCard default gradients are identical
    - **Property 2: WeatherDisplay and WeatherCard default gradients are identical**
    - **Validates: Requirements 1.3**
    - Assert `readDefaultGradient('WeatherDisplay.css') === readDefaultGradient('WeatherCard.css')`
    - Tag: `Feature: improved-background-color, Property 2: WeatherDisplay and WeatherCard default gradients are identical`
  - [ ]* 3.4 Write unit tests for Property 3: weather-condition-specific gradients unchanged
    - **Property 3: Weather-condition-specific gradients are unchanged**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**
    - One `it` block per condition class asserting the exact original gradient string for `--clear`, `--cloudy`, `--rain`, `--snow`, `--thunderstorm`, `--fog`
  - [ ]* 3.5 Write unit test for Property 4: gradient structure is preserved
    - **Property 4: Default gradient structure is preserved**
    - **Validates: Requirements 1.4, 1.5**
    - Assert gradient string matches `linear-gradient(135deg, <color> 0%, <color> 100%)` pattern in both files
  - [ ]* 3.6 Write unit tests for Property 5: media-query rules unchanged
    - **Property 5: Media-query gradients are unchanged**
    - **Validates: Requirements 3.1, 3.2, 3.3**
    - Assert dark-mode gradient (`#1e293b` → `#334155`), high-contrast override, and print `background: white` are present and unmodified in `WeatherDisplay.css`

- [ ] 4. Checkpoint — ensure all tests pass
  - Run `npm test` in `frontend/` and confirm the full suite is green. Ask the user if any questions arise.

- [ ] 5. Post completion comment and close GitHub issue #6
  - Post a comment on https://github.com/haakond/terraform-aws-weather-forecast/issues/6 summarising how each requirement was met (per-requirement summary, max 3 sentences each)
  - Close the GitHub issue via the GitHub MCP server
