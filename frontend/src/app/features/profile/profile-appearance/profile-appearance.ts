import { Component, inject } from '@angular/core';

import { THEME_PREFERENCE_STORE } from '../../../core/auth/password-changer';
import { ThemePreference, ThemeService } from '../../../core/theme/theme.service';

interface ThemeOption {
  value: ThemePreference;
  label: string;
  hint: string;
}

const THEME_OPTIONS: ThemeOption[] = [
  { value: 'light', label: 'Light', hint: 'Always use the light theme.' },
  { value: 'dark', label: 'Dark', hint: 'Always use the dark theme.' },
  { value: 'system', label: 'System', hint: "Match this device's theme setting." },
];

@Component({
  selector: 'app-profile-appearance',
  templateUrl: './profile-appearance.html',
  styleUrl: './profile-appearance.scss',
})
export class ProfileAppearance {
  protected readonly themeService = inject(ThemeService);
  // Whose account this saves against depends on which route loaded the
  // screen - see THEME_PREFERENCE_STORE.
  private readonly themeStore = inject(THEME_PREFERENCE_STORE);
  protected readonly themeOptions = THEME_OPTIONS;

  protected onThemeChange(value: ThemePreference): void {
    // Applied immediately so the switch feels instant; the save is what makes
    // it stick to this account rather than this browser.
    this.themeService.setPreference(value);
    void this.themeStore.saveThemePreference(value);
  }
}
