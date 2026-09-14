import { inject } from '@angular/core';
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';

import { TenantAuthService } from './tenant-auth.service';

export const tenantAuthInterceptor: HttpInterceptorFn = (req, next) => {
  const tenantAuthService = inject(TenantAuthService);
  const token = tenantAuthService.token();

  const authorizedReq = token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(authorizedReq).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse && error.status === 401) {
        tenantAuthService.logout();
      }
      return throwError(() => error);
    }),
  );
};
