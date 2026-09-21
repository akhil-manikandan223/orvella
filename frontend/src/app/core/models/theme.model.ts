/** What the user actually chose - persisted verbatim, including 'system'. */
export type ThemePreference = 'light' | 'dark' | 'system';

/** What's actually applied right now - 'system' always resolves to one of these. */
export type ThemeMode = 'light' | 'dark';

export interface ThemePreferenceUpdate {
  theme_preference: ThemePreference;
}
