import { Injectable, inject } from '@angular/core';
import { BrnDialogService } from '@spartan-ng/brain/dialog';

import { ConfirmDialog, ConfirmDialogContext } from './confirm-dialog';

export interface ConfirmOptions {
  header: string;
  message: string;
  acceptLabel?: string;
  rejectLabel?: string;
  /** Red confirm button and warning icon - for deletes, deactivations, revokes. */
  destructive?: boolean;
  accept: () => void;
  reject?: () => void;
}

/**
 * Stand-in for PrimeNG's ConfirmationService.confirm(): same
 * header/message/accept callback shape, rendered as a Spartan alert dialog.
 * Escape and backdrop clicks count as "cancel".
 */
@Injectable({ providedIn: 'root' })
export class ConfirmService {
  private readonly dialogService = inject(BrnDialogService);

  confirm(options: ConfirmOptions): void {
    const context: ConfirmDialogContext = {
      header: options.header,
      message: options.message,
      acceptLabel: options.acceptLabel ?? (options.destructive ? 'Confirm' : 'Yes'),
      rejectLabel: options.rejectLabel ?? 'Cancel',
      destructive: options.destructive ?? false,
    };
    const ref = this.dialogService.open<ConfirmDialogContext, boolean>(
      ConfirmDialog,
      undefined,
      context,
      {
        role: 'alertdialog',
        hasBackdrop: true,
        backdropClass: ['bg-black/50', 'animate-in', 'fade-in-0'],
        ariaLabelledBy: 'confirm-dialog-title',
        ariaDescribedBy: 'confirm-dialog-message',
        autoFocus: 'first-tabbable',
        restoreFocus: true,
      },
    );
    ref.closed$.subscribe((confirmed) => (confirmed ? options.accept() : options.reject?.()));
  }
}
