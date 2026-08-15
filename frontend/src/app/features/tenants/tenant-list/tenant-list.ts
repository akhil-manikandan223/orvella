import { Component, TemplateRef, computed, inject, signal, viewChild } from '@angular/core';
import { RouterLink } from '@angular/router';
import { BreakpointObserver } from '@angular/cdk/layout';
import { toSignal } from '@angular/core/rxjs-interop';
import { ButtonDirective } from 'primeng/button';

import { TenantService } from '../../../core/data-access/tenant.service';
import { TenantRead } from '../../../core/models/tenant.model';
import { PageHeader } from '../../../shared/page-header/page-header';
import { StatusBadge } from '../../../shared/status-badge/status-badge';
import { DataTable } from '../../../shared/data-table/data-table';
import { DataTableAction, DataTableColumn } from '../../../shared/data-table/data-table.model';

@Component({
  selector: 'app-tenant-list',
  imports: [ButtonDirective, RouterLink, PageHeader, StatusBadge, DataTable],
  templateUrl: './tenant-list.html',
  styleUrl: './tenant-list.scss',
})
export class TenantList {
  private readonly tenantService = inject(TenantService);
  private readonly breakpointObserver = inject(BreakpointObserver);

  protected readonly tenants = signal<TenantRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly searchTerm = signal('');

  private readonly isNarrow = toSignal(this.breakpointObserver.observe('(max-width: 700px)'), {
    initialValue: { matches: false, breakpoints: {} },
  });

  protected readonly showSecondaryColumns = computed(() => !this.isNarrow().matches);

  private readonly statusCellTpl =
    viewChild.required<TemplateRef<{ $implicit: TenantRead }>>('statusCell');

  protected readonly columns = computed<DataTableColumn<TenantRead>[]>(() => {
    const columns: DataTableColumn<TenantRead>[] = [
      { field: 'name', header: 'Name', sortable: true },
      { field: 'slug', header: 'Slug', sortable: true },
    ];
    if (this.showSecondaryColumns()) {
      columns.push(
        { field: 'license_number', header: 'License #' },
        { field: 'key_contact_name', header: 'Key Contact' },
      );
    }
    columns.push({ field: 'is_active', header: 'Status', template: this.statusCellTpl() });
    return columns;
  });

  protected readonly actions: DataTableAction<TenantRead>[] = [
    { icon: 'pi pi-eye', label: 'View', routerLink: (tenant) => ['/tenants', tenant.id] },
  ];

  constructor() {
    this.load();
  }

  protected load(): void {
    this.loading.set(true);
    this.tenantService.list().subscribe({
      next: (tenants) => {
        this.tenants.set(tenants);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
