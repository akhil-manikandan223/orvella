import { inject } from '@angular/core';
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, from, switchMap, throwError } from 'rxjs';

import { TenantAuthService } from './tenant-auth.service';

// See auth.interceptor.ts's AUTH_FLOW_PATHS for why these are excluded from
// refresh-and-retry.
const AUTH_FLOW_PATHS = ['/auth/login', '/auth/refresh', '/auth/logout'];

export const tenantAuthInterceptor: HttpInterceptorFn = (req, next) => {
  const tenantAuthService = inject(TenantAuthService);

  const authorizedReq = req.clone({
    setHeaders: tenantAuthService.token()
      ? { Authorization: `Bearer ${tenantAuthService.token()}` }
      : {},
    withCredentials: true,
  });

  return next(authorizedReq).pipe(
    catchError((error: unknown) => {
      const isAuthFlowRequest = AUTH_FLOW_PATHS.some((path) => req.url.includes(path));
      if (error instanceof HttpErrorResponse && error.status === 401 && !isAuthFlowRequest) {
        return from(tenantAuthService.refresh()).pipe(
          switchMap((refreshed) => {
            if (!refreshed) {
              tenantAuthService.logout();
              return throwError(() => error);
            }
            const retriedReq = req.clone({
              setHeaders: { Authorization: `Bearer ${tenantAuthService.token()}` },
              withCredentials: true,
            });
            return next(retriedReq);
          }),
        );
      }
      return throwError(() => error);
    }),
  );
};
