import { inject } from '@angular/core';
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';

import { ApiError } from '../models/api-error.model';
import { ToastService } from '../feedback/toast.service';

export const apiErrorInterceptor: HttpInterceptorFn = (req, next) => {
  const toast = inject(ToastService);

  return next(req).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse && error.status !== 401) {
        const apiError = error.error as ApiError | null;
        const detail = apiError?.error?.message ?? 'Something went wrong. Please try again.';
        toast.show({ severity: 'error', summary: 'Error', detail });
      }
      return throwError(() => error);
    }),
  );
};
