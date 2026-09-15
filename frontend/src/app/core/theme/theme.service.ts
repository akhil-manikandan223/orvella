import { Service, computed, effect, signal } from '@angular/core';

/** What the user actually chose - persisted verbatim, including 'system'. */
export type ThemePreference = 'light' | 'dark' | 'system';
/** What's actually applied right now - 'system' always resolves to one of these. */
export type ThemeMode = 'light' | 'dark';

const THEME_STORAGE_KEY = 'orvella.theme';
const DARK_CLASS = 'app-dark';

@Service()
export class ThemeService {
  private readonly media = window.matchMedia('(prefers-color-scheme: dark)');
  private readonly systemPrefersDark = signal(this.media.matches);

  readonly preference = signal<ThemePreference>(this.resolveInitialPreference());

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

  setPreference(preference: ThemePreference): void {
    this.preference.set(preference);
    localStorage.setItem(THEME_STORAGE_KEY, preference);
  }

  private resolveInitialPreference(): ThemePreference {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === 'light' || stored === 'dark' || stored === 'system') {
      return stored;
    }
    return 'system';
  }
}
