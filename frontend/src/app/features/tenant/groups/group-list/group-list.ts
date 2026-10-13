import { Component, computed, inject, signal } from '@angular/core';
import { forkJoin } from 'rxjs';

import { DepartmentService } from '../../../../core/data-access/department.service';
import { GroupService } from '../../../../core/data-access/group.service';
import { TenantAuthService } from '../../../../core/tenant-auth/tenant-auth.service';
import { GroupRead } from '../../../../core/models/group.model';
import { DepartmentRead } from '../../../../core/models/organization.model';
import { ConfirmService } from '../../../../core/feedback/confirm.service';
import { ToastService } from '../../../../core/feedback/toast.service';
import { DataTable } from '../../../../shared/data-table/data-table';
import { DataTableAction, DataTableColumn } from '../../../../shared/data-table/data-table.model';
import { FormDrawer } from '../../../../shared/form-drawer/form-drawer';
import { PageHeader } from '../../../../shared/page-header/page-header';
import { HlmButton } from '../../../../shared/ui/button';
import { GroupForm } from '../group-form/group-form';

interface GroupRow extends GroupRead {
  department: string;
}

@Component({
  selector: 'app-group-list',
  imports: [HlmButton, PageHeader, DataTable, FormDrawer, GroupForm],
  templateUrl: './group-list.html',
  styleUrl: './group-list.scss',
})
export class GroupList {
  private readonly groupService = inject(GroupService);
  private readonly departmentService = inject(DepartmentService);
  private readonly tenantAuthService = inject(TenantAuthService);
  private readonly confirmService = inject(ConfirmService);
  private readonly toast = inject(ToastService);

  private readonly groups = signal<GroupRead[]>([]);
  private readonly departments = signal<DepartmentRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly drawerVisible = signal(false);
  protected readonly editingGroup = signal<GroupRead | null>(null);

  // UI tidiness only - TenantPermission.GROUPS_MANAGE is the real boundary,
  // and it matters here: a teacher who could edit supervisors could hand
  // themselves any class in the school.
  protected readonly canManage = computed(() => this.tenantAuthService.user()?.role === 'admin');

  protected readonly rows = computed<GroupRow[]>(() => {
    const names = new Map(this.departments().map((d) => [d.id, d.name]));
    return this.groups().map((group) => ({
      ...group,
      department: (group.department_id && names.get(group.department_id)) || '—',
    }));
  });

  protected readonly columns: DataTableColumn<GroupRow>[] = [
    { field: 'name', header: 'Name', sortable: true },
    { field: 'department', header: 'Department', sortable: true, hideOnNarrow: true },
    {
      field: 'description',
      header: 'Description',
      hideOnNarrow: true,
      cell: (group) => group.description ?? '—',
    },
  ];

  protected readonly actions = computed<DataTableAction<GroupRow>[]>(() =>
    this.canManage()
      ? [
          { icon: 'pi pi-pencil', label: 'Edit', onClick: (group) => this.openEdit(group) },
          {
            icon: 'pi pi-trash',
            label: 'Delete',
            severity: 'danger',
            onClick: (group) => this.confirmDelete(group),
          },
        ]
      : [],
  );

  constructor() {
    this.load();
  }

  protected openCreate(): void {
    this.editingGroup.set(null);
    this.drawerVisible.set(true);
  }

  protected openEdit(group: GroupRead): void {
    this.editingGroup.set(group);
    this.drawerVisible.set(true);
  }

  protected onSaved(): void {
    this.drawerVisible.set(false);
    this.load();
  }

  protected confirmDelete(group: GroupRead): void {
    this.confirmService.confirm({
      header: 'Delete Group',
      message: `Delete "${group.name}"? Its members stay in the directory, but whoever supervised it loses the ability to mark them.`,
      destructive: true,
      accept: () => this.deleteGroup(group),
    });
  }

  private deleteGroup(group: GroupRead): void {
    this.groupService.delete(group.id).subscribe(() => {
      this.toast.show({
        severity: 'success',
        summary: 'Deleted',
        detail: `"${group.name}" was deleted.`,
      });
      this.load();
    });
  }

  protected load(): void {
    this.loading.set(true);
    forkJoin({
      groups: this.groupService.list(),
      departments: this.departmentService.list(),
    }).subscribe({
      next: ({ groups, departments }) => {
        this.groups.set(groups);
        this.departments.set(departments);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
