import { Component, booleanAttribute, computed, input, model, output } from '@angular/core';
import { FormValueControl } from '@angular/forms/signals';
import {
  BrnCombobox,
  BrnComboboxAnchor,
  BrnComboboxContent,
  BrnComboboxEmpty,
  BrnComboboxInput,
  BrnComboboxItem,
  BrnComboboxList,
  BrnComboboxPopoverTrigger,
} from '@spartan-ng/brain/combobox';
import { BrnPopover, BrnPopoverContent } from '@spartan-ng/brain/popover';

import { hlm } from './hlm';
import { fieldClasses } from './input';

type SelectValue = string | null;

let nextId = 0;

/**
 * Searchable select built on Spartan's brain combobox, replacing PrimeNG's
 * p-select. Implements signal forms' FormValueControl, so `[formField]`
 * binds it directly (value, disabled, invalid and touched all flow through).
 *
 * Options are plain objects; `optionLabel` / `optionValue` name the keys,
 * as they did on p-select. The bound value is the option's `optionValue`.
 */
@Component({
  selector: 'app-select',
  imports: [
    BrnCombobox,
    BrnComboboxAnchor,
    BrnComboboxContent,
    BrnComboboxEmpty,
    BrnComboboxInput,
    BrnComboboxItem,
    BrnComboboxList,
    BrnComboboxPopoverTrigger,
    BrnPopover,
    BrnPopoverContent,
  ],
  host: { class: 'block', '(focusout)': 'touch.emit()' },
  template: `
    <div
      brnCombobox
      brnPopover
      align="start"
      [sideOffset]="4"
      [value]="value()"
      (valueChange)="select($event ?? null)"
      [itemToString]="itemToString()"
      [filter]="filterFn()"
      [autoHighlight]="true"
      [disabled]="disabled()"
    >
      <div brnComboboxAnchor [class]="anchorClass()" [attr.data-invalid]="showInvalid() || null">
        <input
          brnComboboxInput
          brnComboboxPopoverTrigger
          [closeOnTriggerClick]="false"
          [id]="inputId()"
          [placeholder]="placeholder()"
          [readOnly]="!filter()"
          [aria-invalid]="showInvalid()"
          class="h-full w-full min-w-0 cursor-default appearance-none border-0 bg-transparent p-0 pl-3 font-sans text-sm text-foreground outline-none placeholder:text-muted-foreground read-only:cursor-pointer disabled:cursor-not-allowed"
        />
        @if (showClear() && value() !== null && !disabled()) {
          <button
            type="button"
            class="flex size-7 shrink-0 cursor-pointer items-center justify-center rounded border-0 bg-transparent p-0 text-muted-foreground hover:bg-muted"
            aria-label="Clear selection"
            (click)="select(null)"
          >
            <i class="pi pi-times text-xs" aria-hidden="true"></i>
          </button>
        }
        <button
          type="button"
          brnComboboxPopoverTrigger
          tabindex="-1"
          class="mr-1 flex size-7 shrink-0 cursor-pointer items-center justify-center rounded border-0 bg-transparent p-0 text-muted-foreground hover:bg-muted disabled:cursor-not-allowed"
          aria-label="Toggle options"
          [disabled]="disabled()"
        >
          <i class="pi pi-chevron-down text-xs" aria-hidden="true"></i>
        </button>
      </div>

      <ng-template brnPopoverContent>
        <div
          brnComboboxContent
          class="group/content flex max-h-72 w-(--brn-combobox-width) flex-col overflow-hidden rounded-md border border-border bg-popover text-popover-foreground shadow-lg animate-in fade-in-0"
        >
          <div
            brnComboboxEmpty
            class="hidden px-3 py-5 text-center text-sm text-muted-foreground group-has-[[role=listbox][data-empty]]/content:block"
          >
            No results
          </div>
          <div
            brnComboboxList
            class="overflow-y-auto overscroll-contain p-1"
            [aria-label]="placeholder() || 'Options'"
          >
            @for (option of entries(); track option.value) {
              <div
                brnComboboxItem
                [value]="option.value"
                class="relative flex cursor-pointer items-center rounded-sm py-2 pr-8 pl-2.5 text-sm outline-none select-none data-[hidden]:hidden data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground aria-selected:font-medium"
              >
                {{ option.label }}
                @if (option.value === value()) {
                  <i
                    class="pi pi-check absolute right-2.5 text-xs text-accent-foreground"
                    aria-hidden="true"
                  ></i>
                }
              </div>
            }
          </div>
        </div>
      </ng-template>
    </div>
  `,
})
export class AppSelect implements FormValueControl<SelectValue> {
  readonly value = model<SelectValue>(null);
  readonly disabled = input(false, { transform: booleanAttribute });
  readonly invalid = input(false, { transform: booleanAttribute });
  readonly touched = input(false, { transform: booleanAttribute });
  readonly touch = output<void>();

  readonly options = input<readonly object[]>([]);
  readonly optionLabel = input('label');
  readonly optionValue = input('value');
  readonly placeholder = input('');
  readonly inputId = input(`app-select-${nextId++}`);
  /** Type-to-search, on by default (p-select's `filter`). Off makes the input read-only. */
  readonly filter = input(true, { transform: booleanAttribute });
  readonly showClear = input(false, { transform: booleanAttribute });

  protected readonly entries = computed(() =>
    this.options().map((option) => {
      const record = option as Record<string, unknown>;
      return {
        value: record[this.optionValue()] as Exclude<SelectValue, null>,
        label: String(record[this.optionLabel()] ?? ''),
      };
    }),
  );

  /** Rebuilt with the options, so a value set before its options load still gets its label. */
  protected readonly itemToString = computed(() => {
    const labels = new Map(this.entries().map((entry) => [entry.value, entry.label]));
    return (value: SelectValue) => (value === null ? '' : (labels.get(value) ?? ''));
  });

  protected readonly filterFn = computed(() => {
    const toLabel = this.itemToString();
    return (value: SelectValue, search: string) =>
      !this.filter() || !search || toLabel(value).toLowerCase().includes(search.toLowerCase());
  });

  /** Like the text inputs, only flag errors once the user has interacted with the field. */
  protected readonly showInvalid = computed(() => this.invalid() && this.touched());

  protected readonly anchorClass = computed(() =>
    hlm(
      fieldClasses,
      'flex items-center gap-0.5 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/30',
      'data-[invalid]:border-danger data-[invalid]:ring-3 data-[invalid]:ring-danger/20',
      this.disabled() && 'cursor-not-allowed bg-muted',
    ),
  );

  protected select(value: SelectValue): void {
    this.value.set(value);
  }
}
