import { Service, effect, signal } from '@angular/core';

export type ThemeMode = 'light' | 'dark';

const THEME_STORAGE_KEY = 'orvella.theme';
const DARK_CLASS = 'app-dark';

@Service()
export class ThemeService {
  readonly mode = signal<ThemeMode>(this.resolveInitialMode());

  constructor() {
    effect(() => {
      document.documentElement.classList.toggle(DARK_CLASS, this.mode() === 'dark');
    });
  }

  toggle(): void {
    this.mode.update((current) => (current === 'dark' ? 'light' : 'dark'));
    localStorage.setItem(THEME_STORAGE_KEY, this.mode());
  }

  private resolveInitialMode(): ThemeMode {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') {
      return stored;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
}
