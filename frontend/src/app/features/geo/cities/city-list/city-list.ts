import { Component, computed, inject, input, signal } from '@angular/core';
import { ButtonDirective } from 'primeng/button';

import { CityService } from '../../../../core/data-access/city.service';
import { DistrictService } from '../../../../core/data-access/district.service';
import { StateService } from '../../../../core/data-access/state.service';
import { CityRead, DistrictRead, StateRead } from '../../../../core/models/geo.model';
import { PageHeader } from '../../../../shared/page-header/page-header';
import { DataTable } from '../../../../shared/data-table/data-table';
import { DataTableAction, DataTableColumn } from '../../../../shared/data-table/data-table.model';
import { FormDrawer } from '../../../../shared/form-drawer/form-drawer';
import { CityForm } from '../city-form/city-form';

@Component({
  selector: 'app-city-list',
  imports: [ButtonDirective, PageHeader, DataTable, FormDrawer, CityForm],
  templateUrl: './city-list.html',
  styleUrl: './city-list.scss',
})
export class CityList {
  private readonly cityService = inject(CityService);
  private readonly stateService = inject(StateService);
  private readonly districtService = inject(DistrictService);

  readonly stateId = input<string | undefined>(undefined, { alias: 'stateId' });
  readonly districtId = input<string | undefined>(undefined, { alias: 'districtId' });

  protected readonly cities = signal<CityRead[]>([]);
  protected readonly states = signal<StateRead[]>([]);
  protected readonly districts = signal<DistrictRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly dialogVisible = signal(false);
  protected readonly editingCity = signal<CityRead | null>(null);
  protected readonly searchTerm = signal('');

  protected readonly stateNameById = computed(() => {
    const map = new Map<string, string>();
    for (const state of this.states()) {
      map.set(state.id, state.name);
    }
    return map;
  });

  protected readonly districtNameById = computed(() => {
    const map = new Map<string, string>();
    for (const district of this.districts()) {
      map.set(district.id, district.name);
    }
    return map;
  });

  protected readonly columns: DataTableColumn<CityRead>[] = [
    { field: 'name', header: 'Name', sortable: true },
    { field: 'slug', header: 'Slug', sortable: true },
    {
      field: 'state_id',
      header: 'State',
      cell: (city) => this.stateNameById().get(city.state_id) ?? '—',
    },
    {
      field: 'district_id',
      header: 'District',
      cell: (city) => (city.district_id ? (this.districtNameById().get(city.district_id) ?? '—') : '—'),
    },
  ];

  protected readonly actions: DataTableAction<CityRead>[] = [
    { icon: 'pi pi-pencil', label: 'Edit', onClick: (city) => this.openEdit(city) },
  ];

  constructor() {
    this.stateService.list().subscribe((states) => this.states.set(states));
    this.districtService.list().subscribe((districts) => this.districts.set(districts));
    this.load();
  }

  protected openCreate(): void {
    this.editingCity.set(null);
    this.dialogVisible.set(true);
  }

  protected openEdit(city: CityRead): void {
    this.editingCity.set(city);
    this.dialogVisible.set(true);
  }

  protected onSaved(): void {
    this.dialogVisible.set(false);
    this.load();
  }

  protected load(): void {
    this.loading.set(true);
    this.cityService.list(this.stateId(), this.districtId()).subscribe({
      next: (cities) => {
        this.cities.set(cities);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
