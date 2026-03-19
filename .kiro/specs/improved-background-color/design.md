# Design Document: Improved Background Color

## Overview

This is a pure CSS change. The default background gradient used by `.weather-display` (in `WeatherDisplay.css`) and `.weather-card` (in `WeatherCard.css`) is updated from the current blue-purple (`#667eea` → `#764ba2`) to a blue-dominant gradient. No JavaScript, no component logic, and no other CSS rules are touched.

The new gradient is `linear-gradient(135deg, #4158d0 0%, #2575fc 100%)`:
- `#4158d0` — RGB(65, 88, 208): blue channel (208) > red channel (65) ✓
- `#2575fc` — RGB(37, 117, 252): blue channel (252) > red channel (37) ✓

Both stops preserve the 135-degree diagonal direction and the two-stop structure required by the requirements.

## Architecture

The change is entirely contained within the frontend static asset layer. No backend, infrastructure, or API changes are required.

```
frontend/src/components/
  WeatherDisplay.css   ← update .weather-display background gradient
  WeatherCard.css      ← update .weather-card background gradient
```

Both files are bundled by Create React App and deployed as static assets to S3/CloudFront. A standard `npm run build` followed by a CloudFront cache invalidation is sufficient to ship the change.

## Components and Interfaces

### WeatherDisplay.css

The only rule that changes is the base `.weather-display` selector:

```css
/* Before */
.weather-display {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* After */
.weather-display {
  background: linear-gradient(135deg, #4158d0 0%, #2575fc 100%);
}
```

All other rules — responsive breakpoints, dark mode, high-contrast, print, animations — remain untouched.

### WeatherCard.css

The only rule that changes is the base `.weather-card` selector:

```css
/* Before */
.weather-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* After */
.weather-card {
  background: linear-gradient(135deg, #4158d0 0%, #2575fc 100%);
}
```

All condition-specific overrides (`.weather-card--clear`, `.weather-card--cloudy`, `.weather-card--rain`, `.weather-card--snow`, `.weather-card--thunderstorm`, `.weather-card--fog`) remain untouched. Because CSS specificity means these classes override the base rule, they are unaffected by this change.

## Data Models

No data model changes. This feature has no runtime state, no API contract changes, and no storage impact.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Default gradient stops are blue-dominant

*For any* color stop in the default gradient of `.weather-display` and `.weather-card`, the blue channel value of that color shall be strictly greater than the red channel value.

**Validates: Requirements 1.1, 1.2**

### Property 2: WeatherDisplay and WeatherCard default gradients are identical

*For any* build of the frontend, the `background` gradient value declared on `.weather-display` in `WeatherDisplay.css` shall be exactly equal to the `background` gradient value declared on `.weather-card` in `WeatherCard.css`.

**Validates: Requirements 1.3**

### Property 3: Weather-condition-specific gradients are unchanged

*For any* weather-condition modifier class (`.weather-card--clear`, `.weather-card--cloudy`, `.weather-card--rain`, `.weather-card--snow`, `.weather-card--thunderstorm`, `.weather-card--fog`), the gradient value in `WeatherCard.css` shall match the original value exactly.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

### Property 4: Default gradient structure is preserved

The default gradient in both CSS files shall use exactly a 135-degree angle, exactly two color stops positioned at `0%` and `100%`.

**Validates: Requirements 1.4, 1.5**

### Property 5: Media-query gradients are unchanged

The dark-mode gradient (`#1e293b` → `#334155`), the high-contrast background override, and the print `background: white` rule in `WeatherDisplay.css` shall each remain exactly as they were before this change.

**Validates: Requirements 3.1, 3.2, 3.3**

## Error Handling

There are no runtime errors possible for a CSS-only change. The only failure mode is a malformed gradient value, which would cause the browser to fall back to no background (transparent). This is prevented by:

- Verifying the new hex values are valid before committing.
- Running the existing test suite to catch any regressions.
- Visual smoke-test after deployment.

## Testing Strategy

### Dual Testing Approach

Both unit tests (specific examples) and property-based tests (universal properties) are used.

**Unit tests** cover:
- The exact gradient string present in each CSS file after the change (snapshot / string-match).
- Each weather-condition class gradient is unchanged (one assertion per condition).
- Each media-query rule is unchanged (dark mode, high-contrast, print).

**Property-based tests** cover:
- Blue-dominance of both gradient stops (Property 1).
- Gradient consistency between the two files (Property 2).

### Property-Based Testing

Library: **fast-check** (JavaScript/TypeScript, works with Jest which is already used in this project).

Each property test runs a minimum of 100 iterations.

Tag format: `Feature: improved-background-color, Property {N}: {property_text}`

#### Property 1 — Blue-dominant stops

```js
// Feature: improved-background-color, Property 1: default gradient stops are blue-dominant
it('all default gradient stops have blue channel > red channel', () => {
  const stops = extractDefaultGradientStops('WeatherDisplay.css');
  stops.forEach(({ r, b }) => expect(b).toBeGreaterThan(r));
});
```

Because the CSS values are static strings (not generated at runtime), fast-check is used to generate arbitrary hex colors and verify the helper `parseHexChannel` function is correct, then the actual CSS values are asserted as examples.

#### Property 2 — Gradient consistency

```js
// Feature: improved-background-color, Property 2: WeatherDisplay and WeatherCard default gradients are identical
it('WeatherDisplay and WeatherCard share the same default gradient', () => {
  expect(readDefaultGradient('WeatherDisplay.css'))
    .toBe(readDefaultGradient('WeatherCard.css'));
});
```

#### Property 3 — Condition-specific gradients unchanged (unit examples)

One `it` block per condition class asserting the exact original gradient string.

#### Property 4 — Gradient structure (unit example)

Assert the gradient string matches the pattern `linear-gradient(135deg, <color> 0%, <color> 100%)`.

#### Property 5 — Media-query rules unchanged (unit examples)

Assert the dark-mode, high-contrast, and print rules are present and unmodified.

### Test Configuration

- Test runner: Jest (already configured in the project).
- Property-based library: `fast-check` — add as a dev dependency (`npm install --save-dev fast-check`).
- Minimum 100 iterations per property test (`fc.assert(fc.property(...), { numRuns: 100 })`).
- Tests live alongside the existing component tests in `frontend/src/components/`.
