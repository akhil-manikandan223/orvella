import {
  Component,
  TemplateRef,
  computed,
  effect,
  input,
  output,
  viewChild,
} from '@angular/core';
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

  private readonly tableRef = viewChild(Table);

  protected readonly hasActions = computed(() => this.actions().length > 0);
  protected readonly columnSpan = computed(() => this.columns().length + (this.hasActions() ? 1 : 0));
  protected readonly globalFilterFields = computed(() => this.columns().map((column) => column.field));

  constructor() {
    effect(() => {
      const filterValue = this.globalFilter();
      this.tableRef()?.filterGlobal(filterValue, 'contains');
    });
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
