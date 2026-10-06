import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { routes } from './app.routes';
import { AuthService } from './core/auth/auth.service';
import { authInterceptor } from './core/auth/auth.interceptor';
import { TenantAuthService } from './core/tenant-auth/tenant-auth.service';
import { tenantAuthInterceptor } from './core/tenant-auth/tenant-auth.interceptor';
import { isTenantHost } from './core/tenancy/host-context';
import { apiErrorInterceptor } from './core/interceptors/api-error.interceptor';

const tenantMode = isTenantHost();

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(
      withInterceptors([tenantMode ? tenantAuthInterceptor : authInterceptor, apiErrorInterceptor]),
    ),
    provideAppInitializer(() => {
      if (tenantMode) {
        inject(TenantAuthService);
      } else {
        inject(AuthService);
      }
    }),
  ],
};
