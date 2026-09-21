import { InjectionToken } from '@angular/core';

import { ThemePreference } from '../models/theme.model';

/**
 * Lets the shared ProfileSecurity screen change a password without knowing
 * whose it is. AuthService (platform admin) and TenantAuthService (tenant
 * user) both satisfy this, and each hits its own backend endpoint; the route
 * that loads the screen picks which one via `providers`.
 */
export interface PasswordChanger {
  changePassword(currentPassword: string, newPassword: string): Promise<void>;
}

export const PASSWORD_CHANGER = new InjectionToken<PasswordChanger>('PASSWORD_CHANGER');

/**
 * Same idea for the shared ProfileAppearance screen: it applies the theme
 * locally via ThemeService, and persists it to whichever account is signed
 * in through this.
 */
export interface ThemePreferenceStore {
  saveThemePreference(preference: ThemePreference): Promise<void>;
}

export const THEME_PREFERENCE_STORE = new InjectionToken<ThemePreferenceStore>(
  'THEME_PREFERENCE_STORE',
);
