import { Component, OnInit, computed, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { FormField, email, form, required } from '@angular/forms/signals';
import { ButtonDirective } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { InputPassword } from 'primeng/inputpassword';
import { Select } from 'primeng/select';
import { SelectButton } from 'primeng/selectbutton';
import { ConfirmationService, MessageService } from 'primeng/api';

import { TenantUserService } from '../../../core/data-access/tenant-user.service';
import { TenantUserRead, TenantUserRole } from '../../../core/models/tenant-user.model';
import { DataTable } from '../../../shared/data-table/data-table';
import { DataTableAction, DataTableColumn } from '../../../shared/data-table/data-table.model';
import { FormDrawer } from '../../../shared/form-drawer/form-drawer';

interface TenantUserFormValue {
  email: string;
  password: string;
  role: TenantUserRole;
}

type StatusFilter = 'active' | 'all' | 'inactive';

const ROLE_OPTIONS: { label: string; value: TenantUserRole }[] = [
  { label: 'Admin', value: 'admin' },
  { label: 'Member', value: 'member' },
];

const ROLE_LABELS: Record<TenantUserRole, string> = { admin: 'Admin', member: 'Member' };

const STATUS_FILTER_OPTIONS: { label: string; value: StatusFilter }[] = [
  { label: 'Active', value: 'active' },
  { label: 'All', value: 'all' },
  { label: 'Inactive', value: 'inactive' },
];

const COLUMNS: DataTableColumn<TenantUserRead>[] = [
  { field: 'email', header: 'Email', sortable: true },
  { field: 'role', header: 'Role', cell: (user) => ROLE_LABELS[user.role] },
  {
    field: 'is_active',
    header: 'Status',
    cell: (user) => (user.is_active ? 'Active' : 'Inactive'),
  },
];

@Component({
  selector: 'app-tenant-users',
  imports: [
    ButtonDirective,
    InputText,
    InputPassword,
    Select,
    SelectButton,
    FormsModule,
    FormField,
    DataTable,
    FormDrawer,
  ],
  templateUrl: './tenant-users.html',
  styleUrl: './tenant-users.scss',
})
export class TenantUsers implements OnInit {
  private readonly tenantUserService = inject(TenantUserService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);

  readonly tenantId = input.required<string>();

  protected readonly users = signal<TenantUserRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly drawerVisible = signal(false);
  protected readonly submitting = signal(false);
  protected readonly statusFilter = signal<StatusFilter>('active');

  protected readonly columns = COLUMNS;
  protected readonly roleOptions = ROLE_OPTIONS;
  protected readonly statusFilterOptions = STATUS_FILTER_OPTIONS;

  protected readonly filteredUsers = computed(() => {
    const filter = this.statusFilter();
    if (filter === 'all') {
      return this.users();
    }
    const wantActive = filter === 'active';
    return this.users().filter((user) => user.is_active === wantActive);
  });

  protected readonly actions = computed<DataTableAction<TenantUserRead>[]>(() => [
    {
      icon: 'pi pi-pencil',
      label: 'Edit',
      onClick: (user) => this.openEdit(user),
    },
    {
      icon: 'pi pi-ban',
      label: 'Deactivate',
      severity: 'danger',
      visible: (user) => user.is_active,
      onClick: (user) => this.confirmDeactivate(user),
    },
    {
      icon: 'pi pi-check',
      label: 'Activate',
      severity: 'success',
      visible: (user) => !user.is_active,
      onClick: (user) => this.activate(user),
    },
  ]);

  protected readonly editingUser = signal<TenantUserRead | null>(null);
  protected readonly drawerHeader = computed(() =>
    this.editingUser() ? 'Edit Tenant User' : 'New Tenant User',
  );

  protected readonly model = signal<TenantUserFormValue>({
    email: '',
    password: '',
    role: 'member',
  });
  protected readonly userForm = form(this.model, (path) => {
    required(path.email, { message: 'Email is required' });
    email(path.email);
    required(path.password, {
      message: 'Password is required',
      when: () => !this.editingUser(),
    });
  });

  ngOnInit(): void {
    this.load();
  }

  protected openCreate(): void {
    this.editingUser.set(null);
    this.model.set({ email: '', password: '', role: 'member' });
    this.drawerVisible.set(true);
  }

  protected openEdit(user: TenantUserRead): void {
    this.editingUser.set(user);
    this.model.set({ email: user.email, password: '', role: user.role });
    this.drawerVisible.set(true);
  }

  protected onSubmit(event: Event): void {
    event.preventDefault();
    if (this.userForm().invalid()) {
      this.userForm().markAsTouched();
      return;
    }

    this.submitting.set(true);
    const value = this.model();
    const editing = this.editingUser();
    const request = editing
      ? this.tenantUserService.update(this.tenantId(), editing.id, {
          email: value.email,
          role: value.role,
        })
      : this.tenantUserService.create(this.tenantId(), value);

    request.subscribe({
      next: () => {
        this.submitting.set(false);
        this.drawerVisible.set(false);
        this.messageService.add({
          severity: 'success',
          summary: editing ? 'User updated' : 'User created',
          detail: editing
            ? `"${value.email}" has been updated.`
            : `"${value.email}" can now sign in to this tenant's workspace.`,
        });
        this.load();
      },
      error: () => this.submitting.set(false),
    });
  }

  protected load(): void {
    this.loading.set(true);
    this.tenantUserService.list(this.tenantId()).subscribe({
      next: (users) => {
        this.users.set(users);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  protected confirmDeactivate(user: TenantUserRead): void {
    this.confirmationService.confirm({
      header: 'Deactivate User',
      message: `Deactivate "${user.email}"? They will immediately lose access to this tenant's workspace.`,
      icon: 'pi pi-exclamation-triangle',
      acceptButtonProps: { severity: 'danger' },
      accept: () => this.setActive(user, false),
    });
  }

  protected activate(user: TenantUserRead): void {
    this.setActive(user, true);
  }

  private setActive(user: TenantUserRead, isActive: boolean): void {
    this.tenantUserService
      .update(this.tenantId(), user.id, { is_active: isActive })
      .subscribe(() => {
        this.messageService.add({
          severity: 'success',
          summary: isActive ? 'User activated' : 'User deactivated',
          detail: isActive
            ? `"${user.email}" can sign in again.`
            : `"${user.email}" can no longer sign in.`,
        });
        this.load();
      });
  }
}
