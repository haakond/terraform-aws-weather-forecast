const fs = require('fs');
const path = require('path');

/**
 * Reads a CSS file and extracts the gradient string from the BASE selector only
 * (.weather-display or .weather-card), ignoring media queries.
 *
 * @param {string} filename - CSS filename relative to this directory
 * @returns {string} - the gradient string, e.g. "linear-gradient(135deg, #4158d0 0%, #2575fc 100%)"
 */
function readDefaultGradient(filename) {
  const css = fs.readFileSync(path.join(__dirname, filename), 'utf8');

  // Find the first occurrence of the base selector block, before any @media
  // Match .weather-display { ... } or .weather-card { ... } — the FIRST block only
  const selectorPattern = /\.(weather-display|weather-card)\s*\{([^}]*)\}/;
  const match = css.match(selectorPattern);

  if (!match) {
    throw new Error(`Could not find base selector block in ${filename}`);
  }

  const blockContent = match[2];

  // Extract the background: value from that block
  const bgMatch = blockContent.match(/background\s*:\s*([^;]+)/);
  if (!bgMatch) {
    throw new Error(`Could not find background property in base selector of ${filename}`);
  }

  return bgMatch[1].trim();
}

/**
 * Parses a 6-digit hex color string and returns the numeric value (0-255)
 * of the specified channel.
 *
 * @param {string} hex - hex color string with or without leading '#'
 * @param {'r'|'g'|'b'} channel - the channel to extract
 * @returns {number} - the channel value (0-255)
 */
function parseHexChannel(hex, channel) {
  const clean = hex.replace(/^#/, '');
  if (clean.length !== 6) {
    throw new Error(`Expected 6-digit hex color, got: ${hex}`);
  }
  const offsets = { r: 0, g: 2, b: 4 };
  const offset = offsets[channel];
  if (offset === undefined) {
    throw new Error(`Unknown channel: ${channel}. Must be 'r', 'g', or 'b'.`);
  }
  return parseInt(clean.slice(offset, offset + 2), 16);
}

module.exports = { readDefaultGradient, parseHexChannel };
