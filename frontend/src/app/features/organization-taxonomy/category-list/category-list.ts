import { Component, computed, inject, signal } from '@angular/core';
import { ButtonDirective } from 'primeng/button';

import { OrganizationCategoryService } from '../../../core/data-access/organization-category.service';
import { OrganizationCategoryRead } from '../../../core/models/organization-taxonomy.model';
import { PageHeader } from '../../../shared/page-header/page-header';
import { DataTable } from '../../../shared/data-table/data-table';
import { DataTableAction, DataTableColumn } from '../../../shared/data-table/data-table.model';
import { FormDrawer } from '../../../shared/form-drawer/form-drawer';
import { TableSettings } from '../../../shared/table-settings/table-settings';
import { CategoryForm } from '../category-form/category-form';

const COLUMNS: DataTableColumn<OrganizationCategoryRead>[] = [
  { field: 'name', header: 'Name', sortable: true },
  { field: 'slug', header: 'Slug', sortable: true },
];

@Component({
  selector: 'app-category-list',
  imports: [ButtonDirective, PageHeader, DataTable, FormDrawer, TableSettings, CategoryForm],
  templateUrl: './category-list.html',
  styleUrl: './category-list.scss',
})
export class CategoryList {
  private readonly categoryService = inject(OrganizationCategoryService);

  protected readonly categories = signal<OrganizationCategoryRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly dialogVisible = signal(false);
  protected readonly editingCategory = signal<OrganizationCategoryRead | null>(null);
  protected readonly searchTerm = signal('');

  protected readonly allColumns = COLUMNS;
  protected readonly visibleFields = signal<Set<string>>(new Set());
  protected readonly columns = computed(() => {
    const visible = this.visibleFields();
    return visible.size === 0 ? this.allColumns : this.allColumns.filter((c) => visible.has(c.field));
  });
  protected readonly actions: DataTableAction<OrganizationCategoryRead>[] = [
    { icon: 'pi pi-pencil', label: 'Edit', onClick: (category) => this.openEdit(category) },
  ];

  constructor() {
    this.load();
  }

  protected openCreate(): void {
    this.editingCategory.set(null);
    this.dialogVisible.set(true);
  }

  protected openEdit(category: OrganizationCategoryRead): void {
    this.editingCategory.set(category);
    this.dialogVisible.set(true);
  }

  protected onSaved(): void {
    this.dialogVisible.set(false);
    this.load();
  }

  protected load(): void {
    this.loading.set(true);
    this.categoryService.list().subscribe({
      next: (categories) => {
        this.categories.set(categories);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
