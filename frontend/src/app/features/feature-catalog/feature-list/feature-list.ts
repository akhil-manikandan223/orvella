import { Component, TemplateRef, computed, inject, signal, viewChild } from '@angular/core';
import { ButtonDirective } from 'primeng/button';

import { FeatureService } from '../../../core/data-access/feature.service';
import { FeatureRead } from '../../../core/models/feature.model';
import { PageHeader } from '../../../shared/page-header/page-header';
import { StatusBadge } from '../../../shared/status-badge/status-badge';
import { DataTable } from '../../../shared/data-table/data-table';
import { DataTableAction, DataTableColumn } from '../../../shared/data-table/data-table.model';
import { FormDrawer } from '../../../shared/form-drawer/form-drawer';
import { FeatureForm } from '../feature-form/feature-form';

@Component({
  selector: 'app-feature-list',
  imports: [ButtonDirective, PageHeader, StatusBadge, DataTable, FormDrawer, FeatureForm],
  templateUrl: './feature-list.html',
  styleUrl: './feature-list.scss',
})
export class FeatureList {
  private readonly featureService = inject(FeatureService);

  protected readonly features = signal<FeatureRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly dialogVisible = signal(false);
  protected readonly editingFeature = signal<FeatureRead | null>(null);
  protected readonly searchTerm = signal('');

  private readonly keyCellTpl =
    viewChild.required<TemplateRef<{ $implicit: FeatureRead }>>('keyCell');
  private readonly statusCellTpl =
    viewChild.required<TemplateRef<{ $implicit: FeatureRead }>>('statusCell');

  protected readonly columns = computed<DataTableColumn<FeatureRead>[]>(() => [
    { field: 'key', header: 'Key', template: this.keyCellTpl() },
    { field: 'name', header: 'Name', sortable: true },
    { field: 'description', header: 'Description', cell: (feature) => feature.description || '—' },
    { field: 'status', header: 'Status', template: this.statusCellTpl() },
  ]);

  protected readonly actions: DataTableAction<FeatureRead>[] = [
    { icon: 'pi pi-pencil', label: 'Edit', onClick: (feature) => this.openEdit(feature) },
  ];

  constructor() {
    this.load();
  }

  protected openCreate(): void {
    this.editingFeature.set(null);
    this.dialogVisible.set(true);
  }

  protected openEdit(feature: FeatureRead): void {
    this.editingFeature.set(feature);
    this.dialogVisible.set(true);
  }

  protected onSaved(): void {
    this.dialogVisible.set(false);
    this.load();
  }

  protected load(): void {
    this.loading.set(true);
    this.featureService.list().subscribe({
      next: (features) => {
        this.features.set(features);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
