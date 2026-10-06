import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { providePrimeNG } from 'primeng/config';
import { definePreset } from '@primeuix/themes';
import Aura from '@primeuix/themes/aura';

import { routes } from './app.routes';
import { AuthService } from './core/auth/auth.service';
import { authInterceptor } from './core/auth/auth.interceptor';
import { TenantAuthService } from './core/tenant-auth/tenant-auth.service';
import { tenantAuthInterceptor } from './core/tenant-auth/tenant-auth.interceptor';
import { isTenantHost } from './core/tenancy/host-context';
import { apiErrorInterceptor } from './core/interceptors/api-error.interceptor';
import { environment } from '../environments/environment';

const tenantMode = isTenantHost();

// Orvella navy scale - mirrors --orv-primary-* in src/styles/tokens.css
// (600 is the brand color). Keep the two in sync until PrimeNG is retired.
const OrvellaPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '#eef3fb',
      100: '#d9e4f5',
      200: '#b3c8eb',
      300: '#85a6dc',
      400: '#4f7cc6',
      500: '#2a5daf',
      600: '#0e4491',
      700: '#0b3878',
      800: '#092c5e',
      900: '#071f43',
      950: '#04142c',
    },
  },
});

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(
      withInterceptors([
        tenantMode ? tenantAuthInterceptor : authInterceptor,
        apiErrorInterceptor,
      ]),
    ),
    providePrimeNG({
      theme: {
        preset: OrvellaPreset,
        options: { darkModeSelector: '.app-dark' },
      },
      license: environment.primeNgLicenseKey,
    }),
    provideAppInitializer(() => {
      if (tenantMode) {
        inject(TenantAuthService);
      } else {
        inject(AuthService);
      }
    }),
  ],
};
