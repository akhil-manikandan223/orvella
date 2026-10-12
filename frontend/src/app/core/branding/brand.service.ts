import { DOCUMENT, Service, computed, inject, signal } from '@angular/core';

import { buildPrimaryPalette } from './brand-palette';

/** The same white wordmark the platform-admin topbar uses - both bars are
 * primary-coloured in light and dark alike, so one asset covers both. */
const ORVELLA_LOCKUP = 'assets/logos/orvella-lockup-on-dark.png';

/**
 * Applies a tenant's branding to the running app.
 *
 * Only ever used on a tenant subdomain, where exactly one tenant is served
 * for the lifetime of the page - so there is no "switch back" case to undo.
 * The platform-admin console never calls this and keeps Orvella's own accent.
 */
@Service()
export class BrandService {
  private readonly document = inject(DOCUMENT);
  private readonly _logoUrl = signal<string | null>(null);

  /** The tenant's own logo, or null when they haven't set one. */
  readonly logoUrl = this._logoUrl.asReadonly();
  readonly hasCustomLogo = computed(() => this._logoUrl() !== null);

  apply(branding: { logo_url?: string | null; brand_color?: string | null } | null): void {
    this._logoUrl.set(branding?.logo_url?.trim() || null);

    const brandColor = branding?.brand_color?.trim();
    if (!brandColor) {
      return;
    }
    const palette = buildPrimaryPalette(brandColor);
    if (!palette) {
      return;
    }
    // Inline on <html>, so it beats the :root defaults in tokens.css; every
    // semantic token (--primary, --accent, --topbar ...) derives from these.
    const root = this.document.documentElement.style;
    for (const [step, color] of Object.entries(palette)) {
      root.setProperty(`--orv-primary-${step}`, color);
    }
  }

  /** The tenant's own logo when they've set one, otherwise Orvella's lockup.
   * No light/dark variant to choose between any more: the topbar is
   * primary-coloured in both themes, so the white wordmark is always right. */
  resolveLogo(): string {
    return this._logoUrl() ?? ORVELLA_LOCKUP;
  }
}
