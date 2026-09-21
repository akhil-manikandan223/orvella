import { Service, computed, effect, signal } from '@angular/core';

import { ThemeMode, ThemePreference } from '../models/theme.model';

export type { ThemeMode, ThemePreference };

/**
 * localStorage only caches the CURRENT user's choice so the app paints the
 * right theme before /me comes back. It is not the source of truth: the
 * signed-in user's stored preference is, and it overwrites this on login.
 * The cache is cleared on logout so the next person to sign in on this
 * browser doesn't inherit the previous one's theme - which is exactly the
 * bug this replaced.
 */
const THEME_CACHE_KEY = 'orvella.theme';
const DARK_CLASS = 'app-dark';

@Service()
export class ThemeService {
  private readonly media = window.matchMedia('(prefers-color-scheme: dark)');
  private readonly systemPrefersDark = signal(this.media.matches);

  readonly preference = signal<ThemePreference>(this.readCache());

  /** The resolved light/dark mode actually in effect - what components render against. */
  readonly mode = computed<ThemeMode>(() => {
    const preference = this.preference();
    return preference === 'system' ? (this.systemPrefersDark() ? 'dark' : 'light') : preference;
  });

  constructor() {
    // Live-reactive: if the user has "system" selected and their OS theme
    // changes while the app is open, follow it without a reload.
    this.media.addEventListener('change', (event) => this.systemPrefersDark.set(event.matches));

    effect(() => {
      document.documentElement.classList.toggle(DARK_CLASS, this.mode() === 'dark');
    });
  }

  /** Quick light/dark flip for the topbar toggle button - opts out of "system" if set. */
  toggle(): void {
    this.setPreference(this.mode() === 'dark' ? 'light' : 'dark');
  }

  /** Applies and caches locally. Persisting to the user's account is the
   * caller's job - see PROFILE_THEME_STORE. */
  setPreference(preference: ThemePreference): void {
    this.preference.set(preference);
    try {
      localStorage.setItem(THEME_CACHE_KEY, preference);
    } catch {
      // Private mode / blocked storage: the theme still applies for this
      // session, it just won't survive a reload before /me returns.
    }
  }

  /** Called once the signed-in user's own preference is known. */
  applyFromAccount(preference: ThemePreference | undefined): void {
    this.setPreference(preference ?? 'system');
  }

  /** On logout, so the next account on this browser starts from its own
   * preference rather than inheriting this one. */
  resetToSystemDefault(): void {
    this.preference.set('system');
    try {
      localStorage.removeItem(THEME_CACHE_KEY);
    } catch {
      // Nothing to clean up if storage is unavailable.
    }
  }

  private readCache(): ThemePreference {
    try {
      const cached = localStorage.getItem(THEME_CACHE_KEY);
      if (cached === 'light' || cached === 'dark' || cached === 'system') {
        return cached;
      }
    } catch {
      // Fall through to the system default.
    }
    return 'system';
  }
}
