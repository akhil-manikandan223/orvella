import { Service, computed, signal } from '@angular/core';
import { updatePrimaryPalette } from '@primeuix/themes';

import { buildPrimaryPalette } from './brand-palette';

const ORVELLA_LOGO_LIGHT = 'assets/logos/orvella-header-light-logo.png';
const ORVELLA_LOGO_DARK = 'assets/logos/orvella-header-dark-logo.png';

/**
 * Applies a tenant's branding to the running app.
 *
 * Only ever used on a tenant subdomain, where exactly one tenant is served
 * for the lifetime of the page - so there is no "switch back" case to undo.
 * The platform-admin console never calls this and keeps Orvella's own accent.
 */
@Service()
export class BrandService {
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
    if (palette) {
      updatePrimaryPalette(palette);
    }
  }

  /** Falls back to the Orvella mark for the current theme when the tenant
   * has no logo of their own. */
  resolveLogo(mode: 'light' | 'dark'): string {
    return this._logoUrl() ?? (mode === 'dark' ? ORVELLA_LOGO_DARK : ORVELLA_LOGO_LIGHT);
  }
}
