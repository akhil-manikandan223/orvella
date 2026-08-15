import { Component, computed, inject, signal } from '@angular/core';
import { ButtonDirective } from 'primeng/button';

import { OrganizationCategoryService } from '../../../core/data-access/organization-category.service';
import { OrganizationTypeService } from '../../../core/data-access/organization-type.service';
import {
  OrganizationCategoryRead,
  OrganizationTypeRead,
} from '../../../core/models/organization-taxonomy.model';
import { PageHeader } from '../../../shared/page-header/page-header';
import { DataTable } from '../../../shared/data-table/data-table';
import { DataTableAction, DataTableColumn } from '../../../shared/data-table/data-table.model';
import { FormDrawer } from '../../../shared/form-drawer/form-drawer';
import { TypeForm } from '../type-form/type-form';

@Component({
  selector: 'app-type-list',
  imports: [ButtonDirective, PageHeader, DataTable, FormDrawer, TypeForm],
  templateUrl: './type-list.html',
  styleUrl: './type-list.scss',
})
export class TypeList {
  private readonly typeService = inject(OrganizationTypeService);
  private readonly categoryService = inject(OrganizationCategoryService);

  protected readonly types = signal<OrganizationTypeRead[]>([]);
  protected readonly categories = signal<OrganizationCategoryRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly dialogVisible = signal(false);
  protected readonly editingType = signal<OrganizationTypeRead | null>(null);
  protected readonly searchTerm = signal('');

  protected readonly categoryNameById = computed(() => {
    const map = new Map<string, string>();
    for (const category of this.categories()) {
      map.set(category.id, category.name);
    }
    return map;
  });

  protected readonly columns: DataTableColumn<OrganizationTypeRead>[] = [
    { field: 'name', header: 'Name', sortable: true },
    { field: 'slug', header: 'Slug', sortable: true },
    {
      field: 'organization_category_id',
      header: 'Category',
      cell: (type) => this.categoryNameById().get(type.organization_category_id) ?? '—',
    },
  ];

  protected readonly actions: DataTableAction<OrganizationTypeRead>[] = [
    {
      icon: 'pi pi-star',
      label: 'Manage feature template',
      routerLink: (type) => ['/organization-types', type.id, 'template'],
    },
    { icon: 'pi pi-pencil', label: 'Edit', onClick: (type) => this.openEdit(type) },
  ];

  constructor() {
    this.categoryService.list().subscribe((categories) => this.categories.set(categories));
    this.load();
  }

  protected openCreate(): void {
    this.editingType.set(null);
    this.dialogVisible.set(true);
  }

  protected openEdit(type: OrganizationTypeRead): void {
    this.editingType.set(type);
    this.dialogVisible.set(true);
  }

  protected onSaved(): void {
    this.dialogVisible.set(false);
    this.load();
  }

  protected load(): void {
    this.loading.set(true);
    this.typeService.list().subscribe({
      next: (types) => {
        this.types.set(types);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
