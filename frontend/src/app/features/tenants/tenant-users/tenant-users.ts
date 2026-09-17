import { Component, OnInit, inject, input, signal } from '@angular/core';
import { FormField, email, form, required } from '@angular/forms/signals';
import { ButtonDirective } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { InputPassword } from 'primeng/inputpassword';
import { Select } from 'primeng/select';
import { MessageService } from 'primeng/api';

import { TenantUserService } from '../../../core/data-access/tenant-user.service';
import { TenantUserRead, TenantUserRole } from '../../../core/models/tenant-user.model';
import { DataTable } from '../../../shared/data-table/data-table';
import { DataTableColumn } from '../../../shared/data-table/data-table.model';
import { FormDrawer } from '../../../shared/form-drawer/form-drawer';

interface TenantUserFormValue {
  email: string;
  password: string;
  role: TenantUserRole;
}

const ROLE_OPTIONS: { label: string; value: TenantUserRole }[] = [
  { label: 'Admin', value: 'admin' },
  { label: 'Member', value: 'member' },
];

const ROLE_LABELS: Record<TenantUserRole, string> = { admin: 'Admin', member: 'Member' };

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
  imports: [ButtonDirective, InputText, InputPassword, Select, FormField, DataTable, FormDrawer],
  templateUrl: './tenant-users.html',
  styleUrl: './tenant-users.scss',
})
export class TenantUsers implements OnInit {
  private readonly tenantUserService = inject(TenantUserService);
  private readonly messageService = inject(MessageService);

  readonly tenantId = input.required<string>();

  protected readonly users = signal<TenantUserRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly drawerVisible = signal(false);
  protected readonly submitting = signal(false);

  protected readonly columns = COLUMNS;
  protected readonly roleOptions = ROLE_OPTIONS;

  protected readonly model = signal<TenantUserFormValue>({
    email: '',
    password: '',
    role: 'member',
  });
  protected readonly userForm = form(this.model, (path) => {
    required(path.email, { message: 'Email is required' });
    email(path.email);
    required(path.password, { message: 'Password is required' });
  });

  ngOnInit(): void {
    this.load();
  }

  protected openCreate(): void {
    this.model.set({ email: '', password: '', role: 'member' });
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
    this.tenantUserService.create(this.tenantId(), value).subscribe({
      next: () => {
        this.submitting.set(false);
        this.drawerVisible.set(false);
        this.messageService.add({
          severity: 'success',
          summary: 'User created',
          detail: `"${value.email}" can now sign in to this tenant's workspace.`,
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
}
