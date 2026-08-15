import { Component, computed, inject, input, signal } from '@angular/core';
import { ButtonDirective } from 'primeng/button';

import { CountryService } from '../../../../core/data-access/country.service';
import { StateService } from '../../../../core/data-access/state.service';
import { CountryRead, StateRead } from '../../../../core/models/geo.model';
import { PageHeader } from '../../../../shared/page-header/page-header';
import { DataTable } from '../../../../shared/data-table/data-table';
import { DataTableAction, DataTableColumn } from '../../../../shared/data-table/data-table.model';
import { EditDialog } from '../../../../shared/edit-dialog/edit-dialog';
import { StateForm } from '../state-form/state-form';

@Component({
  selector: 'app-state-list',
  imports: [ButtonDirective, PageHeader, DataTable, EditDialog, StateForm],
  templateUrl: './state-list.html',
  styleUrl: './state-list.scss',
})
export class StateList {
  private readonly stateService = inject(StateService);
  private readonly countryService = inject(CountryService);

  readonly countryId = input<string | undefined>(undefined, { alias: 'countryId' });

  protected readonly states = signal<StateRead[]>([]);
  protected readonly countries = signal<CountryRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly dialogVisible = signal(false);
  protected readonly editingState = signal<StateRead | null>(null);
  protected readonly searchTerm = signal('');

  protected readonly countryNameById = computed(() => {
    const map = new Map<string, string>();
    for (const country of this.countries()) {
      map.set(country.id, country.name);
    }
    return map;
  });

  protected readonly columns: DataTableColumn<StateRead>[] = [
    { field: 'name', header: 'Name', sortable: true },
    { field: 'slug', header: 'Slug', sortable: true },
    {
      field: 'country_id',
      header: 'Country',
      cell: (state) => this.countryNameById().get(state.country_id) ?? '—',
    },
  ];

  protected readonly actions: DataTableAction<StateRead>[] = [
    { icon: 'pi pi-pencil', label: 'Edit', onClick: (state) => this.openEdit(state) },
  ];

  constructor() {
    this.countryService.list().subscribe((countries) => this.countries.set(countries));
    this.load();
  }

  protected openCreate(): void {
    this.editingState.set(null);
    this.dialogVisible.set(true);
  }

  protected openEdit(state: StateRead): void {
    this.editingState.set(state);
    this.dialogVisible.set(true);
  }

  protected onSaved(): void {
    this.dialogVisible.set(false);
    this.load();
  }

  protected load(): void {
    this.loading.set(true);
    this.stateService.list(this.countryId()).subscribe({
      next: (states) => {
        this.states.set(states);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
