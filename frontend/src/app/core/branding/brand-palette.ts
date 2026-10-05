/**
 * Builds a PrimeNG 50..950 primary palette from a single tenant brand colour.
 *
 * The ratios below were reverse-engineered from Orvella's own hand-picked
 * purple scale in app.config.ts, so a tenant's generated palette has the same
 * character (how fast it lightens, how dark the deep end goes) as the default
 * brand rather than a flat linear ramp.
 *
 * Written by hand rather than importing @primeuix/styled's `palette()`: that
 * helper is only a transitive dependency here, and reaching into an
 * undeclared package would break on any hoisting or version change.
 */
type Rgb = { r: number; g: number; b: number };

/** Fraction of the way from the base colour toward white. */
const TINT_STOPS: Record<number, number> = {
  50: 0.92,
  100: 0.85,
  200: 0.67,
  300: 0.46,
  400: 0.23,
};

/** Fraction of the way from the base colour toward black. */
const SHADE_STOPS: Record<number, number> = {
  600: 0.19,
  700: 0.36,
  800: 0.51,
  900: 0.67,
  950: 0.8,
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
  const palette: Record<string, string> = { 500: toHex(base) };

  for (const [step, amount] of Object.entries(TINT_STOPS)) {
    palette[step] = toHex(mix(base, white, amount));
  }
  for (const [step, amount] of Object.entries(SHADE_STOPS)) {
    palette[step] = toHex(mix(base, black, amount));
  }
  return palette;
}
