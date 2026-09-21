import { ThemePreference } from './theme.model';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface PlatformAdminRead {
  id: string;
  email: string;
  theme_preference: ThemePreference;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}
