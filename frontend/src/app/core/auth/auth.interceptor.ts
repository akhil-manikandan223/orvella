import { inject } from '@angular/core';
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, from, switchMap, throwError } from 'rxjs';

import { AuthService } from './auth.service';

// The login/refresh/logout endpoints themselves must never trigger a
// refresh-and-retry - a 401 from /auth/login just means "wrong password",
// and a 401 from /auth/refresh means the refresh token itself is no longer
// valid, which refreshing again obviously can't fix.
const AUTH_FLOW_PATHS = ['/auth/login', '/auth/refresh', '/auth/logout'];

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);

  const authorizedReq = req.clone({
    setHeaders: authService.token() ? { Authorization: `Bearer ${authService.token()}` } : {},
    // Always set, even for the unauthenticated login call: this is what
    // makes the browser attach/accept the httpOnly refresh cookie despite
    // the frontend (:6200) and backend (:8000) being different origins in
    // local dev.
    withCredentials: true,
  });

  return next(authorizedReq).pipe(
    catchError((error: unknown) => {
      const isAuthFlowRequest = AUTH_FLOW_PATHS.some((path) => req.url.includes(path));
      if (error instanceof HttpErrorResponse && error.status === 401 && !isAuthFlowRequest) {
        return from(authService.refresh()).pipe(
          switchMap((refreshed) => {
            if (!refreshed) {
              authService.logout();
              return throwError(() => error);
            }
            const retriedReq = req.clone({
              setHeaders: { Authorization: `Bearer ${authService.token()}` },
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
