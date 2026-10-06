/**
 * Builds the 50..900 `--orv-primary-*` scale (src/styles/tokens.css) from a
 * single tenant brand colour, which takes the brand step, 600.
 *
 * The ratios below are averaged from Orvella's own hand-picked navy scale, so
 * a tenant's generated palette has the same character (how fast it lightens,
 * how dark the deep end goes) as the default brand rather than a flat linear
 * ramp. `dark` is the lifted primary dark mode uses on near-black surfaces.
 */
type Rgb = { r: number; g: number; b: number };

/** Fraction of the way from the base colour toward white. */
const TINT_STOPS: Record<string, number> = {
  50: 0.94,
  100: 0.87,
  200: 0.74,
  300: 0.57,
  400: 0.35,
  500: 0.17,
  dark: 0.26,
};

/** Fraction of the way from the base colour toward black. */
const SHADE_STOPS: Record<string, number> = {
  700: 0.19,
  800: 0.35,
  900: 0.53,
};

function parseHex(hex: string): Rgb | null {
  const match = /^#([0-9a-f]{6})$/i.exec(hex.trim());
  if (!match) {
    return null;
  }
  const value = Number.parseInt(match[1], 16);
  return { r: (value >> 16) & 255, g: (value >> 8) & 255, b: value & 255 };
}

function toHex({ r, g, b }: Rgb): string {
  const channel = (value: number) =>
    Math.round(Math.min(255, Math.max(0, value)))
      .toString(16)
      .padStart(2, '0');
  return `#${channel(r)}${channel(g)}${channel(b)}`;
}

function mix(base: Rgb, target: Rgb, amount: number): Rgb {
  return {
    r: base.r + (target.r - base.r) * amount,
    g: base.g + (target.g - base.g) * amount,
    b: base.b + (target.b - base.b) * amount,
  };
}

/** Returns null for anything that isn't a #rrggbb hex, so callers can fall
 * back to the default brand rather than render a palette of NaN. */
export function buildPrimaryPalette(brandColor: string): Record<string, string> | null {
  const base = parseHex(brandColor);
  if (!base) {
    return null;
  }

  const white: Rgb = { r: 255, g: 255, b: 255 };
  const black: Rgb = { r: 0, g: 0, b: 0 };
  const palette: Record<string, string> = { 600: toHex(base) };

  for (const [step, amount] of Object.entries(TINT_STOPS)) {
    palette[step] = toHex(mix(base, white, amount));
  }
  for (const [step, amount] of Object.entries(SHADE_STOPS)) {
    palette[step] = toHex(mix(base, black, amount));
  }
  return palette;
}
