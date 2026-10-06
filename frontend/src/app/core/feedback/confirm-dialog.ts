import { Component, inject } from '@angular/core';
import { BrnDialogRef, injectBrnDialogContext } from '@spartan-ng/brain/dialog';

import { HlmButton } from '../../shared/ui/button';

export interface ConfirmDialogContext {
  header: string;
  message: string;
  acceptLabel: string;
  rejectLabel: string;
  destructive: boolean;
}

/**
 * Body of the alert dialog ConfirmService opens. Cancel comes first in the
 * DOM so it takes initial focus: a stray Enter never confirms a destructive
 * action.
 */
@Component({
  selector: 'app-confirm-dialog',
  imports: [HlmButton],
  host: {
    class:
      'block w-[min(28rem,calc(100vw-2rem))] rounded-[10px] border border-border bg-popover p-5 text-popover-foreground shadow-xl animate-in fade-in-0 zoom-in-95',
  },
  template: `
    <div class="flex gap-3">
      @if (context.destructive) {
        <span
          class="flex size-9 shrink-0 items-center justify-center rounded-full bg-danger-surface text-danger"
          aria-hidden="true"
        >
          <i class="pi pi-exclamation-triangle"></i>
        </span>
      }
      <div class="min-w-0">
        <h2 id="confirm-dialog-title" class="m-0 text-base font-semibold">{{ context.header }}</h2>
        <p id="confirm-dialog-message" class="mt-1.5 mb-0 text-sm leading-5 text-muted-foreground">
          {{ context.message }}
        </p>
      </div>
    </div>
    <div class="mt-5 flex justify-end gap-2">
      <button hlmBtn variant="outline" type="button" (click)="close(false)">
        {{ context.rejectLabel }}
      </button>
      <button
        hlmBtn
        type="button"
        [variant]="context.destructive ? 'destructive' : 'default'"
        (click)="close(true)"
      >
        {{ context.acceptLabel }}
      </button>
    </div>
  `,
})
export class ConfirmDialog {
  protected readonly context = injectBrnDialogContext<ConfirmDialogContext>();
  private readonly dialogRef = inject<BrnDialogRef<boolean>>(BrnDialogRef);

  protected close(confirmed: boolean): void {
    this.dialogRef.close(confirmed);
  }
}
