import { Component, computed, inject, signal } from '@angular/core';
import { ButtonDirective } from 'primeng/button';
import { ConfirmationService, MessageService } from 'primeng/api';

import { LocationService } from '../../../../core/data-access/location.service';
import { TenantAuthService } from '../../../../core/tenant-auth/tenant-auth.service';
import { LocationRead } from '../../../../core/models/organization.model';
import { PageHeader } from '../../../../shared/page-header/page-header';
import { DataTable } from '../../../../shared/data-table/data-table';
import { DataTableAction, DataTableColumn } from '../../../../shared/data-table/data-table.model';
import { FormDrawer } from '../../../../shared/form-drawer/form-drawer';
import { LocationForm } from '../location-form/location-form';

const COLUMNS: DataTableColumn<LocationRead>[] = [
  { field: 'name', header: 'Name', sortable: true },
  { field: 'address', header: 'Address', cell: (l) => l.address ?? '—' },
];

@Component({
  selector: 'app-location-list',
  imports: [ButtonDirective, PageHeader, DataTable, FormDrawer, LocationForm],
  templateUrl: './location-list.html',
  styleUrl: './location-list.scss',
})
export class LocationList {
  private readonly locationService = inject(LocationService);
  private readonly tenantAuthService = inject(TenantAuthService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly messageService = inject(MessageService);

  protected readonly locations = signal<LocationRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly drawerVisible = signal(false);
  protected readonly editingLocation = signal<LocationRead | null>(null);

  protected readonly canManage = computed(() => this.tenantAuthService.user()?.role === 'admin');

  protected readonly columns = COLUMNS;
  protected readonly actions = computed<DataTableAction<LocationRead>[]>(() =>
    this.canManage()
      ? [
          { icon: 'pi pi-pencil', label: 'Edit', onClick: (l) => this.openEdit(l) },
          {
            icon: 'pi pi-trash',
            label: 'Delete',
            severity: 'danger',
            onClick: (l) => this.confirmDelete(l),
          },
        ]
      : [],
  );

  constructor() {
    this.load();
  }

  protected openCreate(): void {
    this.editingLocation.set(null);
    this.drawerVisible.set(true);
  }

  protected openEdit(location: LocationRead): void {
    this.editingLocation.set(location);
    this.drawerVisible.set(true);
  }

  protected onSaved(): void {
    this.drawerVisible.set(false);
    this.load();
  }

  protected confirmDelete(location: LocationRead): void {
    this.confirmationService.confirm({
      header: 'Delete Location',
      message: `Delete "${location.name}"? People assigned to it will simply become unassigned.`,
      icon: 'pi pi-exclamation-triangle',
      acceptButtonProps: { severity: 'danger' },
      accept: () => this.deleteLocation(location),
    });
  }

  private deleteLocation(location: LocationRead): void {
    this.locationService.delete(location.id).subscribe(() => {
      this.messageService.add({
        severity: 'success',
        summary: 'Deleted',
        detail: `"${location.name}" was deleted.`,
      });
      this.load();
    });
  }

  protected load(): void {
    this.loading.set(true);
    this.locationService.list().subscribe({
      next: (locations) => {
        this.locations.set(locations);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
