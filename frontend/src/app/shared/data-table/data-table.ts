import {
  Component,
  TemplateRef,
  booleanAttribute,
  computed,
  effect,
  input,
  isDevMode,
  output,
  signal,
  untracked,
} from '@angular/core';
import { AgGridAngular } from 'ag-grid-angular';
import {
  CellClickedEvent,
  CellStyleModule,
  ClientSideRowModelApiModule,
  ClientSideRowModelModule,
  ColDef,
  GetRowIdParams,
  GridApi,
  GridReadyEvent,
  IRowNode,
  IsFullWidthRowParams,
  ModuleRegistry,
  PaginationModule,
  PostSortRowsParams,
  RowClassParams,
  RowHeightParams,
  RowSelectionModule,
  RowSelectionOptions,
  RowStyleModule,
  SelectionChangedEvent,
  ValidationModule,
} from 'ag-grid-community';

import { DataTableAction, DataTableBulkAction, DataTableColumn } from './data-table.model';
import {
  DETAIL_ROW,
  DetailRow,
  GridActionsCell,
  GridDetailRow,
  GridEmptyOverlay,
  GridTemplateCell,
  isDetailRow,
} from './grid-cells';
import { orvellaGridTheme } from './grid-theme';
import { HlmButton, severityToButton } from '../ui/button';

// Registered here rather than at bootstrap so AG Grid stays in the lazy chunk
// shared by the list pages instead of the initial bundle. ValidationModule
// only in dev: it explains missing-module and bad-option mistakes in the
// console, and is dead weight in production.
ModuleRegistry.registerModules([
  ClientSideRowModelModule,
  PaginationModule,
  RowSelectionModule,
  RowStyleModule,
  CellStyleModule,
  ClientSideRowModelApiModule, // brings api.onRowHeightChanged(), used by GridDetailRow
  ...(isDevMode() ? [ValidationModule] : []),
]);

const ACTIONS_COLUMN_ID = '__actions';
/** Fallback height for an expansion row until GridDetailRow measures its content. */
const DETAIL_ROW_INITIAL_HEIGHT = 120;
const COMPACT_COLUMN_WIDTH = 64;
const MIN_COLUMN_WIDTH = 44;

type GridRow<T> = T | DetailRow<T>;

@Component({
  selector: 'app-data-table',
  imports: [AgGridAngular, HlmButton],
  templateUrl: './data-table.html',
  styleUrl: './data-table.scss',
  host: { '[class.data-table--flush]': 'flush()' },
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

  /**
   * Drops the table's own card chrome (border, radius, shadow) for a table
   * that sits inside another card, so the outer card draws the only frame.
   */
  readonly flush = input(false, { transform: booleanAttribute });

  /** Adds the leading checkbox column. Opt-in: only worth it where `bulkActions` do something. */
  readonly selectable = input(false);
  readonly bulkActions = input<DataTableBulkAction<T>[]>([]);
  readonly selectionChange = output<T[]>();

  /** Global (search-box) filter text. Matched against every column's field. */
  readonly globalFilter = input('');

  /** Enables an expandable second row per record, rendered via `expansionTemplate`. */
  readonly expandable = input(false);
  readonly isRowExpanded = input<(row: T) => boolean>(() => false);
  readonly expansionTemplate = input<TemplateRef<{ $implicit: T }> | null>(null);
  readonly rowClicked = output<T>();

  protected readonly theme = orvellaGridTheme;
  private readonly gridApi = signal<GridApi<GridRow<T>> | null>(null);

  protected readonly selection = signal<T[]>([]);
  protected readonly hasBulkActions = computed(
    () => this.selectable() && this.bulkActions().length > 0,
  );

  private readonly globalFilterFields = computed(() =>
    this.columns().map((column) => column.field),
  );

  /**
   * Filtered here rather than with AG Grid's quick filter so the match rule
   * stays exactly what callers relied on under PrimeNG: a case-insensitive
   * substring of any column's raw field value.
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

  /** Filtered rows, each expanded record followed by its full-width expansion row. */
  protected readonly rowData = computed<GridRow<T>[]>(() => {
    const rows = this.filteredValue();
    if (!this.expandable() || !this.expansionTemplate()) {
      return rows;
    }
    const isExpanded = this.isRowExpanded();
    return rows.flatMap((row): GridRow<T>[] =>
      isExpanded(row) ? [row, { [DETAIL_ROW]: row, __detailKey: this.detailKey(row) }] : [row],
    );
  });

  protected readonly columnDefs = computed<ColDef<GridRow<T>>[]>(() => {
    const defs = this.columns().map((column) => this.toColDef(column));
    const actions = this.actions();
    if (actions.length > 0) {
      defs.push({
        colId: ACTIONS_COLUMN_ID,
        headerName: '',
        width: Math.max(64, 24 + actions.length * 40),
        sortable: false,
        resizable: false,
        cellRenderer: GridActionsCell,
        cellRendererParams: { actions },
      });
    }
    return defs;
  });

  protected readonly rowSelection = computed<RowSelectionOptions<GridRow<T>> | undefined>(() =>
    this.selectable()
      ? {
          mode: 'multiRow',
          checkboxes: true,
          headerCheckbox: true,
          enableClickSelection: false,
          isRowSelectable: (node) => !isDetailRow(node.data),
        }
      : undefined,
  );

  protected readonly fullWidthRowParams = computed(() => ({
    template: this.expansionTemplate(),
  }));
  protected readonly emptyOverlayParams = computed(() => ({
    message: this.emptyMessage(),
    icon: this.emptyIcon(),
  }));
  protected readonly detailRowRenderer = GridDetailRow;
  protected readonly emptyOverlay = GridEmptyOverlay;

  protected readonly getRowId = (params: GetRowIdParams<GridRow<T>>): string =>
    isDetailRow<T>(params.data) ? params.data.__detailKey : this.rowKey(params.data);

  protected readonly isFullWidthRow = (params: IsFullWidthRowParams<GridRow<T>>): boolean =>
    isDetailRow(params.rowNode.data);

  protected readonly getRowHeight = (params: RowHeightParams<GridRow<T>>): number | undefined =>
    isDetailRow(params.data) ? DETAIL_ROW_INITIAL_HEIGHT : undefined;

  protected readonly getRowClass = (params: RowClassParams<GridRow<T>>): string | undefined =>
    this.expandable() && !isDetailRow(params.data) ? 'data-table__row--clickable' : undefined;

  /** Keeps each expansion row glued under its parent when the user sorts. */
  protected readonly postSortRows = (params: PostSortRowsParams<GridRow<T>>): void => {
    const details = new Map<string, IRowNode<GridRow<T>>>();
    const records: IRowNode<GridRow<T>>[] = [];
    for (const node of params.nodes) {
      if (isDetailRow<T>(node.data)) {
        details.set(node.data.__detailKey, node);
      } else {
        records.push(node);
      }
    }
    if (details.size === 0) {
      return;
    }
    const ordered = records.flatMap((node) => {
      const detail = details.get(this.detailKey(node.data as T));
      return detail ? [node, detail] : [node];
    });
    params.nodes.splice(0, params.nodes.length, ...ordered);
  };

  constructor() {
    /** Reset to page 1 whenever the search narrows/widens the result set. */
    effect(() => {
      this.globalFilter();
      untracked(() => this.gridApi()?.paginationGoToFirstPage());
    });

    // A reload after a bulk action hands back a fresh array whose rows no
    // longer match what was ticked - keeping the old selection would leave
    // the bulk bar acting on records that may not exist any more. getRowId
    // makes AG Grid carry selection across rowData updates, so it has to be
    // cleared explicitly.
    effect(() => {
      this.value();
      untracked(() => this.clearSelection());
    });
  }

  protected bulkVariant(action: DataTableBulkAction<T>) {
    return severityToButton(action.severity, 'solid').variant;
  }

  protected onGridReady(event: GridReadyEvent<GridRow<T>>): void {
    this.gridApi.set(event.api);
  }

  protected onSelectionChanged(event: SelectionChangedEvent<GridRow<T>>): void {
    const rows = event.api.getSelectedRows().filter((row): row is T => !isDetailRow(row));
    this.selection.set(rows);
    this.selectionChange.emit(rows);
  }

  protected clearSelection(): void {
    const api = this.gridApi();
    if (api && api.getSelectedNodes().length > 0) {
      api.deselectAll(); // onSelectionChanged emits the empty selection.
      return;
    }
    this.selection.set([]);
    this.selectionChange.emit([]);
  }

  /** Data-column clicks toggle expansion; checkbox and action cells keep their own meaning. */
  protected onCellClicked(event: CellClickedEvent<GridRow<T>>): void {
    if (!this.expandable() || !event.data || isDetailRow(event.data)) {
      return;
    }
    const colId = event.column.getColId();
    if (this.globalFilterFields().includes(colId)) {
      this.rowClicked.emit(event.data);
    }
  }

  private toColDef(column: DataTableColumn<T>): ColDef<GridRow<T>> {
    const requested = toPixels(column.width);
    // Quartz pads cells 16px a side; below this a narrow icon column (the
    // audit log's expand arrow) would be truncated to an ellipsis.
    const compact = requested !== undefined && requested < COMPACT_COLUMN_WIDTH;
    const width = requested === undefined ? undefined : Math.max(requested, MIN_COLUMN_WIDTH);
    const cellClasses = [
      column.align ? `data-table__cell--${column.align}` : '',
      compact ? 'data-table__cell--compact' : '',
    ].filter(Boolean);
    return {
      colId: column.field,
      field: column.field as ColDef<GridRow<T>>['field'],
      headerName: column.header,
      // No type inference: AG Grid would swap boolean fields to its own
      // checkbox renderer and ignore valueFormatter (column.cell).
      cellDataType: false,
      sortable: column.sortable ?? false,
      resizable: true,
      ...(width ? { width, minWidth: width } : { flex: 1, minWidth: 120 }),
      valueFormatter: (params) => (params.data ? this.cellValue(params.data as T, column) : ''),
      cellRenderer: column.template ? GridTemplateCell : undefined,
      cellRendererParams: column.template ? { template: column.template } : undefined,
      cellClass: cellClasses,
      headerClass: cellClasses,
    };
  }

  private cellValue(row: T, column: DataTableColumn<T>): string {
    if (column.cell) {
      return column.cell(row);
    }
    const value = (row as Record<string, unknown>)[column.field];
    return value === null || value === undefined ? '' : String(value);
  }

  private rowKey(row: T): string {
    return String((row as Record<string, unknown>)[this.dataKey()]);
  }

  private detailKey(row: T): string {
    return `detail:${this.rowKey(row)}`;
  }
}

/** Converts the `width` strings callers already pass ('8rem', '120px') to AG Grid pixels. */
function toPixels(width: string | undefined): number | undefined {
  const match = width?.trim().match(/^(\d+(?:\.\d+)?)(rem|px)$/);
  if (!match) {
    return undefined;
  }
  const amount = Number(match[1]);
  return match[2] === 'rem' ? amount * 16 : amount;
}
