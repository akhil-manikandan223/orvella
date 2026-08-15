import { Component, computed, inject, input, signal } from '@angular/core';
import { ButtonDirective } from 'primeng/button';

import { DistrictService } from '../../../../core/data-access/district.service';
import { StateService } from '../../../../core/data-access/state.service';
import { DistrictRead, StateRead } from '../../../../core/models/geo.model';
import { PageHeader } from '../../../../shared/page-header/page-header';
import { DataTable } from '../../../../shared/data-table/data-table';
import { DataTableAction, DataTableColumn } from '../../../../shared/data-table/data-table.model';
import { EditDialog } from '../../../../shared/edit-dialog/edit-dialog';
import { DistrictForm } from '../district-form/district-form';

@Component({
  selector: 'app-district-list',
  imports: [ButtonDirective, PageHeader, DataTable, EditDialog, DistrictForm],
  templateUrl: './district-list.html',
  styleUrl: './district-list.scss',
})
export class DistrictList {
  private readonly districtService = inject(DistrictService);
  private readonly stateService = inject(StateService);

  readonly stateId = input<string | undefined>(undefined, { alias: 'stateId' });

  protected readonly districts = signal<DistrictRead[]>([]);
  protected readonly states = signal<StateRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly dialogVisible = signal(false);
  protected readonly editingDistrict = signal<DistrictRead | null>(null);
  protected readonly searchTerm = signal('');

  protected readonly stateNameById = computed(() => {
    const map = new Map<string, string>();
    for (const state of this.states()) {
      map.set(state.id, state.name);
    }
    return map;
  });

  protected readonly columns: DataTableColumn<DistrictRead>[] = [
    { field: 'name', header: 'Name', sortable: true },
    { field: 'slug', header: 'Slug', sortable: true },
    {
      field: 'state_id',
      header: 'State',
      cell: (district) => this.stateNameById().get(district.state_id) ?? '—',
    },
  ];

  protected readonly actions: DataTableAction<DistrictRead>[] = [
    { icon: 'pi pi-pencil', label: 'Edit', onClick: (district) => this.openEdit(district) },
  ];

  constructor() {
    this.stateService.list().subscribe((states) => this.states.set(states));
    this.load();
  }

  protected openCreate(): void {
    this.editingDistrict.set(null);
    this.dialogVisible.set(true);
  }

  protected openEdit(district: DistrictRead): void {
    this.editingDistrict.set(district);
    this.dialogVisible.set(true);
  }

  protected onSaved(): void {
    this.dialogVisible.set(false);
    this.load();
  }

  protected load(): void {
    this.loading.set(true);
    this.districtService.list(this.stateId()).subscribe({
      next: (districts) => {
        this.districts.set(districts);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
