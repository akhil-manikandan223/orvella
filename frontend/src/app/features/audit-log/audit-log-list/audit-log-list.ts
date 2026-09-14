import { Component, TemplateRef, computed, effect, inject, signal, viewChild } from '@angular/core';
import { BreakpointObserver } from '@angular/cdk/layout';
import { toSignal } from '@angular/core/rxjs-interop';
import { DatePipe, JsonPipe } from '@angular/common';
import { FormField, form } from '@angular/forms/signals';
import { InputText } from 'primeng/inputtext';

import { AuditLogService } from '../../../core/data-access/audit-log.service';
import { AuditLogRead } from '../../../core/models/audit-log.model';
import { PageHeader } from '../../../shared/page-header/page-header';
import { DataTable } from '../../../shared/data-table/data-table';
import { DataTableColumn } from '../../../shared/data-table/data-table.model';
import { TableSettings } from '../../../shared/table-settings/table-settings';

@Component({
  selector: 'app-audit-log-list',
  imports: [InputText, FormField, JsonPipe, PageHeader, DataTable, TableSettings],
  providers: [DatePipe],
  templateUrl: './audit-log-list.html',
  styleUrl: './audit-log-list.scss',
})
export class AuditLogList {
  private readonly auditLogService = inject(AuditLogService);
  private readonly breakpointObserver = inject(BreakpointObserver);
  private readonly datePipe = inject(DatePipe);

  protected readonly entries = signal<AuditLogRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly expandedRowId = signal<string | null>(null);
  protected readonly entityTypeFilterModel = signal('');
  protected readonly entityTypeFilter = form(this.entityTypeFilterModel);

  private readonly isNarrow = toSignal(this.breakpointObserver.observe('(max-width: 700px)'), {
    initialValue: { matches: false, breakpoints: {} },
  });

  protected readonly showActorColumn = computed(() => !this.isNarrow().matches);

  private readonly expandCellTpl =
    viewChild.required<TemplateRef<{ $implicit: AuditLogRead }>>('expandCell');
  private readonly expansionTpl =
    viewChild.required<TemplateRef<{ $implicit: AuditLogRead }>>('expansionCell');

  protected readonly isRowExpandedFn = (entry: AuditLogRead): boolean =>
    this.expandedRowId() === entry.id;

  private readonly expandColumn = computed<DataTableColumn<AuditLogRead>>(() => ({
    field: 'expand',
    header: '',
    width: '2.5rem',
    template: this.expandCellTpl(),
  }));

  /** Toggleable columns only - the expand-arrow column is structural, not a data field. */
  protected readonly allColumns = computed<DataTableColumn<AuditLogRead>[]>(() => {
    const columns: DataTableColumn<AuditLogRead>[] = [
      { field: 'action', header: 'Action', cell: (entry) => entry.action },
      { field: 'entity_type', header: 'Entity Type' },
    ];
    if (this.showActorColumn()) {
      columns.push({ field: 'actor_type', header: 'Actor', cell: (entry) => entry.actor_type ?? '—' });
    }
    columns.push({
      field: 'created_at',
      header: 'Timestamp',
      cell: (entry) => this.datePipe.transform(entry.created_at, 'medium') ?? '',
    });
    return columns;
  });
  protected readonly visibleFields = signal<Set<string>>(new Set());
  protected readonly columns = computed(() => {
    const visible = this.visibleFields();
    const all = this.allColumns();
    const dataColumns = visible.size === 0 ? all : all.filter((c) => visible.has(c.field));
    return [this.expandColumn(), ...dataColumns];
  });

  protected readonly expansionTemplate = computed(() => this.expansionTpl());

  constructor() {
    effect(() => {
      this.entityTypeFilterModel();
      this.load();
    });
  }

  protected toggleRow(entry: AuditLogRead): void {
    this.expandedRowId.update((current) => (current === entry.id ? null : entry.id));
  }

  protected load(): void {
    this.loading.set(true);
    const entityType = this.entityTypeFilterModel().trim();
    this.auditLogService.list({ entityType: entityType || undefined }).subscribe({
      next: (entries) => {
        this.entries.set(entries);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
