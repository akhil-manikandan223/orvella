import { Component, effect, inject, input, output, signal, viewChild } from '@angular/core';
import { ButtonDirective } from 'primeng/button';
import { Popover } from 'primeng/popover';

import { TablePreferenceService } from '../../core/data-access/table-preference.service';
import { DataTableColumn } from '../data-table/data-table.model';
import { FormDrawer } from '../form-drawer/form-drawer';

@Component({
  selector: 'app-table-settings',
  imports: [ButtonDirective, Popover, FormDrawer],
  templateUrl: './table-settings.html',
  styleUrl: './table-settings.scss',
})
export class TableSettings<T extends object = Record<string, unknown>> {
  private readonly preferenceService = inject(TablePreferenceService);

  /** Stable key identifying this listing table server-side, e.g. 'countries'. */
  readonly tableKey = input.required<string>();
  readonly columns = input.required<DataTableColumn<T>[]>();
  readonly visibleFieldsChange = output<Set<string>>();

  protected readonly popoverRef = viewChild(Popover);

  protected readonly drawerVisible = signal(false);
  protected readonly visibleFields = signal<Set<string>>(new Set());
  protected readonly saving = signal(false);

  constructor() {
    effect(() => {
      const key = this.tableKey();
      const allFields = this.columns().map((column) => column.field);
      this.preferenceService.get(key).subscribe((preference) => {
        const saved = preference?.visible_columns.filter((field) => allFields.includes(field));
        const visible = new Set(saved && saved.length > 0 ? saved : allFields);
        this.visibleFields.set(visible);
        this.visibleFieldsChange.emit(visible);
      });
    });
  }

  protected togglePopover(event: Event): void {
    this.popoverRef()?.toggle(event);
  }

  protected openCustomize(): void {
    this.popoverRef()?.hide();
    this.drawerVisible.set(true);
  }

  protected onColumnToggle(field: string, event: Event): void {
    const checkbox = event.target as HTMLInputElement;
    const next = new Set(this.visibleFields());
    if (checkbox.checked) {
      next.add(field);
    } else {
      if (next.size <= 1) {
        checkbox.checked = true;
        return;
      }
      next.delete(field);
    }
    this.visibleFields.set(next);
  }

  protected saveChanges(): void {
    this.saving.set(true);
    const visibleColumns = Array.from(this.visibleFields());
    this.preferenceService.save(this.tableKey(), { visible_columns: visibleColumns }).subscribe({
      next: () => {
        this.saving.set(false);
        this.visibleFieldsChange.emit(this.visibleFields());
        this.drawerVisible.set(false);
      },
      error: () => this.saving.set(false),
    });
  }
}
