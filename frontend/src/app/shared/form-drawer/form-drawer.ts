import { Component, computed, input, output } from '@angular/core';
import { BrnDialogState } from '@spartan-ng/brain/dialog';
import {
  BrnSheet,
  BrnSheetClose,
  BrnSheetContent,
  BrnSheetOverlay,
  BrnSheetTitle,
} from '@spartan-ng/brain/sheet';

import { HlmButton } from '../ui/button';

/**
 * Right-hand side sheet for create/edit forms, built on Spartan's brain
 * sheet (a CDK dialog: focus trap, Escape, backdrop click, focus restore).
 * Same visible/visibleChange contract the PrimeNG p-drawer version had.
 */
@Component({
  selector: 'app-form-drawer',
  imports: [BrnSheet, BrnSheetContent, BrnSheetOverlay, BrnSheetTitle, BrnSheetClose, HlmButton],
  host: { class: 'contents' },
  template: `
    <div
      brnSheet
      side="right"
      [state]="state()"
      (stateChanged)="onStateChanged($event)"
      [closeOnOutsidePointerEvents]="true"
    >
      <brn-sheet-overlay class="bg-black/40 animate-in fade-in-0" />
      <div
        *brnSheetContent
        class="fixed inset-y-0 right-0 flex h-full max-w-[100vw] flex-col border-l border-border bg-card text-card-foreground shadow-xl animate-in slide-in-from-right duration-200"
        [style.width]="width()"
      >
        <div class="flex items-center justify-between gap-3 border-b border-border px-6 py-4">
          <h2 brnSheetTitle class="m-0 text-lg leading-[26px] font-semibold">{{ header() }}</h2>
          <button
            brnSheetClose
            hlmBtn
            variant="ghost"
            size="icon-sm"
            type="button"
            aria-label="Close"
          >
            <i class="pi pi-times" aria-hidden="true"></i>
          </button>
        </div>
        <div class="flex-1 overflow-y-auto px-6 py-5">
          <ng-content />
        </div>
      </div>
    </div>
  `,
})
export class FormDrawer {
  readonly visible = input.required<boolean>();
  readonly visibleChange = output<boolean>();
  readonly header = input.required<string>();
  readonly width = input('28rem');

  protected readonly state = computed<BrnDialogState>(() => (this.visible() ? 'open' : 'closed'));

  protected onStateChanged(state: BrnDialogState): void {
    const open = state === 'open';
    if (open !== this.visible()) {
      this.visibleChange.emit(open);
    }
  }
}
