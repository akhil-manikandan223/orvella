import { TemplateRef } from '@angular/core';

export type DataTableColumnAlign = 'left' | 'center' | 'right';

export interface DataTableColumn<T = unknown> {
  field: string;
  header: string;
  sortable?: boolean;
  width?: string;
  align?: DataTableColumnAlign;
  /** Plain-text formatter. Ignored when `template` is provided. Defaults to `String(row[field])`. */
  cell?: (row: T) => string;
  /** Custom cell rendering, obtained via a `viewChild()` signal query in the caller. */
  template?: TemplateRef<{ $implicit: T }>;
}

export type DataTableActionSeverity =
  | 'success'
  | 'danger'
  | 'secondary'
  | 'info'
  | 'warn'
  | 'contrast';

export interface DataTableAction<T = unknown> {
  icon: string;
  label: string;
  severity?: DataTableActionSeverity;
  visible?: (row: T) => boolean;
  disabled?: (row: T) => boolean;
  /** Renders as a button. Mutually exclusive with `routerLink`. */
  onClick?: (row: T) => void;
  /** Renders as an anchor (preserves ctrl/cmd-click, open-in-new-tab). Mutually exclusive with `onClick`. */
  routerLink?: (row: T) => unknown[];
}
