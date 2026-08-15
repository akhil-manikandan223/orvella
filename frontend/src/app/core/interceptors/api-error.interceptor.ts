import { inject } from '@angular/core';
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { MessageService } from 'primeng/api';
import { catchError, throwError } from 'rxjs';

import { ApiError } from '../models/api-error.model';

export const apiErrorInterceptor: HttpInterceptorFn = (req, next) => {
  const messageService = inject(MessageService);

  return next(req).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse && error.status !== 401) {
        const apiError = error.error as ApiError | null;
        const detail = apiError?.error?.message ?? 'Something went wrong. Please try again.';
        messageService.add({ severity: 'error', summary: 'Error', detail });
      }
      return throwError(() => error);
    }),
  );
};
