import { Component, TemplateRef, computed, effect, input, output, signal } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Table, SortIcon, SortableColumn } from 'primeng/table';
import { ButtonDirective } from 'primeng/button';

import { EmptyState } from '../empty-state/empty-state';
import { DataTableAction, DataTableColumn } from './data-table.model';

@Component({
  selector: 'app-data-table',
  imports: [Table, SortableColumn, SortIcon, ButtonDirective, RouterLink, NgTemplateOutlet, EmptyState],
  templateUrl: './data-table.html',
  styleUrl: './data-table.scss',
})
export class DataTable<T extends object = Record<string, unknown>> {
  readonly columns = input.required<DataTableColumn<T>[]>();
  readonly value = input.required<T[]>();
  readonly actions = input<DataTableAction<T>[]>([]);
  readonly loading = input(false);
  readonly dataKey = input('id');
  readonly rowsPerPage = input(50);
  readonly rowsPerPageOptions = input<number[]>([25, 50, 100]);
  readonly emptyMessage = input('No records found.');
  readonly emptyIcon = input('pi pi-inbox');

  /** Global (search-box) filter text. Matched against every column's field. */
  readonly globalFilter = input('');

  /** Enables an expandable second row per record, rendered via `expansionTemplate`. */
  readonly expandable = input(false);
  readonly isRowExpanded = input<(row: T) => boolean>(() => false);
  readonly expansionTemplate = input<TemplateRef<{ $implicit: T }> | null>(null);
  readonly rowClicked = output<T>();

  protected readonly hasActions = computed(() => this.actions().length > 0);
  protected readonly columnSpan = computed(() => this.columns().length + (this.hasActions() ? 1 : 0));
  private readonly globalFilterFields = computed(() => this.columns().map((column) => column.field));

  /**
   * Filtered by hand rather than via PrimeNG's own filterGlobal()/totalRecords
   * sync: that combination proved to get totalRecords stuck (see the pagination
   * fix history) - computing the filtered set ourselves keeps totalRecords
   * always correct with zero reliance on PrimeNG's internal bookkeeping.
   */
  protected readonly filteredValue = computed(() => {
    const term = this.globalFilter().trim().toLowerCase();
    if (!term) {
      return this.value();
    }
    const fields = this.globalFilterFields();
    return this.value().filter((row) =>
      fields.some((field) => {
        const raw = (row as Record<string, unknown>)[field];
        return raw != null && String(raw).toLowerCase().includes(term);
      }),
    );
  });

  /** Reset to page 1 whenever the search narrows/widens the result set. */
  protected readonly firstRow = signal(0);

  constructor() {
    effect(() => {
      this.globalFilter();
      this.firstRow.set(0);
    });
  }

  protected onPageChange(event: { first: number }): void {
    this.firstRow.set(event.first);
  }

  protected cellValue(row: T, column: DataTableColumn<T>): string {
    if (column.cell) {
      return column.cell(row);
    }
    const value = (row as Record<string, unknown>)[column.field];
    return value === null || value === undefined ? '' : String(value);
  }

  protected isActionVisible(action: DataTableAction<T>, row: T): boolean {
    return action.visible ? action.visible(row) : true;
  }

  protected isActionDisabled(action: DataTableAction<T>, row: T): boolean {
    return action.disabled ? action.disabled(row) : false;
  }

  protected onRowClick(row: T): void {
    if (this.expandable()) {
      this.rowClicked.emit(row);
    }
  }
}
