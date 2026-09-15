import { Component, inject } from '@angular/core';

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
  protected readonly themeOptions = THEME_OPTIONS;

  protected onThemeChange(value: ThemePreference): void {
    this.themeService.setPreference(value);
  }
}
