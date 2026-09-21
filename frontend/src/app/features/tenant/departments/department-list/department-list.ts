import { Component, computed, inject, signal } from '@angular/core';
import { forkJoin } from 'rxjs';
import { ButtonDirective } from 'primeng/button';
import { ConfirmationService, MessageService } from 'primeng/api';

import { DepartmentService } from '../../../../core/data-access/department.service';
import { TenantAuthService } from '../../../../core/tenant-auth/tenant-auth.service';
import { DepartmentRead } from '../../../../core/models/organization.model';
import { PageHeader } from '../../../../shared/page-header/page-header';
import { DataTable } from '../../../../shared/data-table/data-table';
import {
  DataTableAction,
  DataTableBulkAction,
  DataTableColumn,
} from '../../../../shared/data-table/data-table.model';
import { FormDrawer } from '../../../../shared/form-drawer/form-drawer';
import { DepartmentForm } from '../department-form/department-form';

const COLUMNS: DataTableColumn<DepartmentRead>[] = [
  { field: 'name', header: 'Name', sortable: true },
  { field: 'description', header: 'Description', cell: (d) => d.description ?? '—' },
];

@Component({
  selector: 'app-department-list',
  imports: [ButtonDirective, PageHeader, DataTable, FormDrawer, DepartmentForm],
  templateUrl: './department-list.html',
  styleUrl: './department-list.scss',
})
export class DepartmentList {
  private readonly departmentService = inject(DepartmentService);
  private readonly tenantAuthService = inject(TenantAuthService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly messageService = inject(MessageService);

  protected readonly departments = signal<DepartmentRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly drawerVisible = signal(false);
  protected readonly editingDepartment = signal<DepartmentRead | null>(null);
  protected readonly searchTerm = signal('');

  // Frontend-side hiding only, for a cleaner UI - the backend permission
  // check (TenantPermission.DEPARTMENTS_MANAGE) is the real security
  // boundary regardless of what this component shows or hides.
  protected readonly canManage = computed(() => this.tenantAuthService.user()?.role === 'admin');

  protected readonly columns = COLUMNS;
  protected readonly actions = computed<DataTableAction<DepartmentRead>[]>(() =>
    this.canManage()
      ? [
          { icon: 'pi pi-pencil', label: 'Edit', onClick: (d) => this.openEdit(d) },
          {
            icon: 'pi pi-trash',
            label: 'Delete',
            severity: 'danger',
            onClick: (d) => this.confirmDelete(d),
          },
        ]
      : [],
  );

  protected readonly bulkActions = computed<DataTableBulkAction<DepartmentRead>[]>(() =>
    this.canManage()
      ? [
          {
            icon: 'pi pi-trash',
            label: 'Delete',
            severity: 'danger',
            onClick: (departments) => this.confirmBulkDelete(departments),
          },
        ]
      : [],
  );

  constructor() {
    this.load();
  }

  protected openCreate(): void {
    this.editingDepartment.set(null);
    this.drawerVisible.set(true);
  }

  protected openEdit(department: DepartmentRead): void {
    this.editingDepartment.set(department);
    this.drawerVisible.set(true);
  }

  protected onSaved(): void {
    this.drawerVisible.set(false);
    this.load();
  }

  protected confirmDelete(department: DepartmentRead): void {
    this.confirmationService.confirm({
      header: 'Delete Department',
      message: `Delete "${department.name}"? People assigned to it will simply become unassigned.`,
      icon: 'pi pi-exclamation-triangle',
      acceptButtonProps: { severity: 'danger' },
      accept: () => this.deleteDepartment(department),
    });
  }

  private deleteDepartment(department: DepartmentRead): void {
    this.departmentService.delete(department.id).subscribe(() => {
      this.messageService.add({
        severity: 'success',
        summary: 'Deleted',
        detail: `"${department.name}" was deleted.`,
      });
      this.load();
    });
  }

  protected confirmBulkDelete(departments: DepartmentRead[]): void {
    const count = departments.length;
    this.confirmationService.confirm({
      header: 'Delete Departments',
      message: `Delete ${count} department${count === 1 ? '' : 's'}? People assigned to them will simply become unassigned.`,
      icon: 'pi pi-exclamation-triangle',
      acceptButtonProps: { severity: 'danger' },
      accept: () => this.deleteDepartments(departments),
    });
  }

  private deleteDepartments(departments: DepartmentRead[]): void {
    forkJoin(departments.map((department) => this.departmentService.delete(department.id))).subscribe(
      () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Deleted',
          detail: `${departments.length} department${departments.length === 1 ? '' : 's'} deleted.`,
        });
        this.load();
      },
    );
  }

  protected load(): void {
    this.loading.set(true);
    this.departmentService.list().subscribe({
      next: (departments) => {
        this.departments.set(departments);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
