/**
 * Converts wind speed from metres per second to kilometres per hour.
 * @param {number} ms - Wind speed in m/s
 * @returns {number} Wind speed in km/h, rounded to nearest whole number
 */
export function convertWindSpeed(ms) {
  return Math.round(ms * 3.6);
}

/**
 * Converts wind direction in degrees to a 16-point compass cardinal direction label.
 * Uses 22.5° sectors centred on each direction.
 * @param {number} degrees - Wind direction in degrees (0-360)
 * @returns {string} Cardinal direction label (e.g. "north", "south-west")
 */
export function getCardinalDirection(degrees) {
  // Normalize to 0-360 range
  const normalized = ((degrees % 360) + 360) % 360;

  // 16-point compass with 22.5° sectors
  // Each direction is centred, so we offset by 11.25° (half of 22.5°)
  const index = Math.round(normalized / 22.5) % 16;

  const directions = [
    'north',           // 0° (348.75-11.25)
    'north-north-east', // 22.5° (11.25-33.75)
    'north-east',      // 45° (33.75-56.25)
    'east-north-east', // 67.5° (56.25-78.75)
    'east',            // 90° (78.75-101.25)
    'east-south-east', // 112.5° (101.25-123.75)
    'south-east',      // 135° (123.75-146.25)
    'south-south-east', // 157.5° (146.25-168.75)
    'south',           // 180° (168.75-191.25)
    'south-south-west', // 202.5° (191.25-213.75)
    'south-west',      // 225° (213.75-236.25)
    'west-south-west', // 247.5° (236.25-258.75)
    'west',            // 270° (258.75-281.25)
    'west-north-west', // 292.5° (281.25-303.75)
    'north-west',      // 315° (303.75-326.25)
    'north-north-west' // 337.5° (326.25-348.75)
  ];

  return directions[index];
}
