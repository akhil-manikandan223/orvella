import { Component, inject, signal } from '@angular/core';
import { ButtonDirective } from 'primeng/button';

import { CountryService } from '../../../../core/data-access/country.service';
import { CountryRead } from '../../../../core/models/geo.model';
import { PageHeader } from '../../../../shared/page-header/page-header';
import { DataTable } from '../../../../shared/data-table/data-table';
import { DataTableAction, DataTableColumn } from '../../../../shared/data-table/data-table.model';
import { EditDialog } from '../../../../shared/edit-dialog/edit-dialog';
import { CountryForm } from '../country-form/country-form';

const COLUMNS: DataTableColumn<CountryRead>[] = [
  { field: 'name', header: 'Name', sortable: true },
  { field: 'slug', header: 'Slug', sortable: true },
];

@Component({
  selector: 'app-country-list',
  imports: [ButtonDirective, PageHeader, DataTable, EditDialog, CountryForm],
  templateUrl: './country-list.html',
  styleUrl: './country-list.scss',
})
export class CountryList {
  private readonly countryService = inject(CountryService);

  protected readonly countries = signal<CountryRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly dialogVisible = signal(false);
  protected readonly editingCountry = signal<CountryRead | null>(null);
  protected readonly searchTerm = signal('');

  protected readonly columns = COLUMNS;
  protected readonly actions: DataTableAction<CountryRead>[] = [
    { icon: 'pi pi-pencil', label: 'Edit', onClick: (country) => this.openEdit(country) },
  ];

  constructor() {
    this.load();
  }

  protected openCreate(): void {
    this.editingCountry.set(null);
    this.dialogVisible.set(true);
  }

  protected openEdit(country: CountryRead): void {
    this.editingCountry.set(country);
    this.dialogVisible.set(true);
  }

  protected onSaved(): void {
    this.dialogVisible.set(false);
    this.load();
  }

  protected load(): void {
    this.loading.set(true);
    this.countryService.list().subscribe({
      next: (countries) => {
        this.countries.set(countries);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
