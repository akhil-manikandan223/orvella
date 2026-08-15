import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { ConfirmationService, MessageService } from 'primeng/api';
import { providePrimeNG } from 'primeng/config';
import { definePreset } from '@primeuix/themes';
import Aura from '@primeuix/themes/aura';

import { routes } from './app.routes';
import { AuthService } from './core/auth/auth.service';
import { authInterceptor } from './core/auth/auth.interceptor';
import { apiErrorInterceptor } from './core/interceptors/api-error.interceptor';
import { environment } from '../environments/environment';

const OrvellaPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '#f4f2fd',
      100: '#e9e5fb',
      200: '#cfc5f6',
      300: '#b0a0f0',
      400: '#8f79e8',
      500: '#6d5ce0',
      600: '#5847c4',
      700: '#4636a0',
      800: '#35277b',
      900: '#241a57',
      950: '#160f35',
    },
  },
});

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([authInterceptor, apiErrorInterceptor])),
    providePrimeNG({
      theme: {
        preset: OrvellaPreset,
        options: { darkModeSelector: '.app-dark' },
      },
      license: environment.primeNgLicenseKey,
    }),
    MessageService,
    ConfirmationService,
    provideAppInitializer(() => {
      inject(AuthService);
    }),
  ],
};
