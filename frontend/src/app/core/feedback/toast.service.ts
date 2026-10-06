import { Injectable } from '@angular/core';
import { toast } from '@spartan-ng/brain/sonner';

export type ToastSeverity = 'success' | 'info' | 'warn' | 'error';

export interface ToastMessage {
  severity: ToastSeverity;
  summary: string;
  detail?: string;
}

/**
 * App-wide toasts, rendered by <app-toaster> (Spartan's sonner toaster).
 * Same message shape PrimeNG's MessageService.add() took, so call sites
 * only swap the service, not their arguments.
 */
@Injectable({ providedIn: 'root' })
export class ToastService {
  show({ severity, summary, detail }: ToastMessage): void {
    const data = detail ? { description: detail } : undefined;
    switch (severity) {
      case 'success':
        toast.success(summary, data);
        break;
      case 'warn':
        toast.warning(summary, data);
        break;
      case 'error':
        toast.error(summary, data);
        break;
      default:
        toast.info(summary, data);
    }
  }
}
