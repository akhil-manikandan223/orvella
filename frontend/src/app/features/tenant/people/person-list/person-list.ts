import { Component, computed, inject, signal } from '@angular/core';
import { forkJoin } from 'rxjs';

import { DepartmentService } from '../../../../core/data-access/department.service';
import { LocationService } from '../../../../core/data-access/location.service';
import { PersonService } from '../../../../core/data-access/person.service';
import { TenantAuthService } from '../../../../core/tenant-auth/tenant-auth.service';
import { PersonRead } from '../../../../core/models/organization.model';
import { PageHeader } from '../../../../shared/page-header/page-header';
import { DataTable } from '../../../../shared/data-table/data-table';
import {
  DataTableAction,
  DataTableBulkAction,
  DataTableColumn,
} from '../../../../shared/data-table/data-table.model';
import { FormDrawer } from '../../../../shared/form-drawer/form-drawer';
import { PersonForm } from '../person-form/person-form';
import { ToastService } from '../../../../core/feedback/toast.service';
import { ConfirmService } from '../../../../core/feedback/confirm.service';
import { HlmButton } from '../../../../shared/ui/button';

@Component({
  selector: 'app-person-list',
  imports: [HlmButton, PageHeader, DataTable, FormDrawer, PersonForm],
  templateUrl: './person-list.html',
  styleUrl: './person-list.scss',
})
export class PersonList {
  private readonly personService = inject(PersonService);
  private readonly departmentService = inject(DepartmentService);
  private readonly locationService = inject(LocationService);
  private readonly tenantAuthService = inject(TenantAuthService);
  private readonly confirmService = inject(ConfirmService);
  private readonly toast = inject(ToastService);

  protected readonly people = signal<PersonRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly drawerVisible = signal(false);
  protected readonly editingPerson = signal<PersonRead | null>(null);
  protected readonly searchTerm = signal('');

  private readonly departmentNames = signal<Map<string, string>>(new Map());
  private readonly locationNames = signal<Map<string, string>>(new Map());

  protected readonly canManage = computed(() => this.tenantAuthService.user()?.role === 'admin');

  protected readonly columns = computed<DataTableColumn<PersonRead>[]>(() => {
    const departmentNames = this.departmentNames();
    const locationNames = this.locationNames();
    return [
      {
        field: 'first_name',
        header: 'Name',
        sortable: true,
        cell: (p) => `${p.first_name} ${p.last_name}`,
      },
      { field: 'category', header: 'Category', sortable: true },
      { field: 'email', header: 'Email', hideOnNarrow: true, cell: (p) => p.email ?? '—' },
      {
        field: 'department_id',
        header: 'Department',
        hideOnNarrow: true,
        cell: (p) => (p.department_id && departmentNames.get(p.department_id)) || '—',
      },
      {
        field: 'location_id',
        header: 'Location',
        hideOnNarrow: true,
        cell: (p) => (p.location_id && locationNames.get(p.location_id)) || '—',
      },
    ];
  });

  protected readonly actions = computed<DataTableAction<PersonRead>[]>(() =>
    this.canManage()
      ? [
          { icon: 'pi pi-pencil', label: 'Edit', onClick: (p) => this.openEdit(p) },
          {
            icon: 'pi pi-trash',
            label: 'Delete',
            severity: 'danger',
            onClick: (p) => this.confirmDelete(p),
          },
        ]
      : [],
  );

  protected readonly bulkActions = computed<DataTableBulkAction<PersonRead>[]>(() =>
    this.canManage()
      ? [
          {
            icon: 'pi pi-trash',
            label: 'Delete',
            severity: 'danger',
            onClick: (people) => this.confirmBulkDelete(people),
          },
        ]
      : [],
  );

  constructor() {
    this.load();
  }

  protected openCreate(): void {
    this.editingPerson.set(null);
    this.drawerVisible.set(true);
  }

  protected openEdit(person: PersonRead): void {
    this.editingPerson.set(person);
    this.drawerVisible.set(true);
  }

  protected onSaved(): void {
    this.drawerVisible.set(false);
    this.load();
  }

  protected confirmDelete(person: PersonRead): void {
    this.confirmService.confirm({
      header: 'Delete Person',
      message: `Delete "${person.first_name} ${person.last_name}"? This cannot be undone.`,
      destructive: true,
      accept: () => this.deletePerson(person),
    });
  }

  private deletePerson(person: PersonRead): void {
    this.personService.delete(person.id).subscribe(() => {
      this.toast.show({
        severity: 'success',
        summary: 'Deleted',
        detail: `"${person.first_name} ${person.last_name}" was deleted.`,
      });
      this.load();
    });
  }

  protected confirmBulkDelete(people: PersonRead[]): void {
    const count = people.length;
    this.confirmService.confirm({
      header: 'Delete People',
      message: `Delete ${count} ${count === 1 ? 'person' : 'people'}? This cannot be undone.`,
      destructive: true,
      accept: () => this.deletePeople(people),
    });
  }

  private deletePeople(people: PersonRead[]): void {
    forkJoin(people.map((person) => this.personService.delete(person.id))).subscribe(() => {
      this.toast.show({
        severity: 'success',
        summary: 'Deleted',
        detail: `${people.length} ${people.length === 1 ? 'person' : 'people'} deleted.`,
      });
      this.load();
    });
  }

  protected load(): void {
    this.loading.set(true);
    forkJoin({
      people: this.personService.list(),
      departments: this.departmentService.list(),
      locations: this.locationService.list(),
    }).subscribe({
      next: ({ people, departments, locations }) => {
        this.people.set(people);
        this.departmentNames.set(new Map(departments.map((d) => [d.id, d.name])));
        this.locationNames.set(new Map(locations.map((l) => [l.id, l.name])));
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
