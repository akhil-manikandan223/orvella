import { Component, TemplateRef, computed, inject, input, output, signal, viewChild } from '@angular/core';
import { ButtonDirective } from 'primeng/button';

import { FeatureService } from '../../../core/data-access/feature.service';
import { TenantService } from '../../../core/data-access/tenant.service';
import { FeatureRead } from '../../../core/models/feature.model';
import { StatusBadge } from '../../../shared/status-badge/status-badge';
import { DataTable } from '../../../shared/data-table/data-table';
import { DataTableColumn } from '../../../shared/data-table/data-table.model';
import { ToastService } from '../../../core/feedback/toast.service';
import { ConfirmService } from '../../../core/feedback/confirm.service';

@Component({
  selector: 'app-tenant-feature-toggles',
  imports: [ButtonDirective, StatusBadge, DataTable],
  templateUrl: './tenant-feature-toggles.html',
  styleUrl: './tenant-feature-toggles.scss',
})
export class TenantFeatureToggles {
  private readonly featureService = inject(FeatureService);
  private readonly tenantService = inject(TenantService);
  private readonly confirmService = inject(ConfirmService);
  private readonly toast = inject(ToastService);

  readonly tenantId = input.required<string>();
  readonly enabledFeatures = input.required<FeatureRead[]>();
  readonly toggled = output<void>();

  protected readonly allFeatures = signal<FeatureRead[]>([]);
  protected readonly togglingFeatureId = signal<string | null>(null);

  protected readonly enabledFeatureIds = computed(
    () => new Set(this.enabledFeatures().map((feature) => feature.id)),
  );

  private readonly featureCellTpl =
    viewChild.required<TemplateRef<{ $implicit: FeatureRead }>>('featureCell');
  private readonly statusCellTpl =
    viewChild.required<TemplateRef<{ $implicit: FeatureRead }>>('statusCell');
  private readonly enabledCellTpl =
    viewChild.required<TemplateRef<{ $implicit: FeatureRead }>>('enabledCell');

  protected readonly columns = computed<DataTableColumn<FeatureRead>[]>(() => [
    { field: 'name', header: 'Feature', template: this.featureCellTpl() },
    { field: 'status', header: 'Status', template: this.statusCellTpl() },
    { field: 'id', header: 'Enabled', width: '10rem', template: this.enabledCellTpl() },
  ]);

  constructor() {
    this.featureService.list().subscribe((features) => this.allFeatures.set(features));
  }

  protected isEnabled(feature: FeatureRead): boolean {
    return this.enabledFeatureIds().has(feature.id);
  }

  protected onToggleClick(feature: FeatureRead): void {
    if (this.isEnabled(feature)) {
      this.confirmService.confirm({
        header: 'Disable Feature',
        message: `Disable "${feature.name}" for this tenant? Their users will immediately lose access to it.`,
        destructive: true,
        accept: () => this.toggle(feature, false),
      });
      return;
    }
    this.toggle(feature, true);
  }

  private toggle(feature: FeatureRead, enabled: boolean): void {
    this.togglingFeatureId.set(feature.id);
    this.tenantService.toggleFeature(this.tenantId(), feature.id, { enabled }).subscribe({
      next: () => {
        this.togglingFeatureId.set(null);
        this.toast.show({
          severity: 'success',
          summary: enabled ? 'Feature enabled' : 'Feature disabled',
          detail: `"${feature.name}" is now ${enabled ? 'enabled' : 'disabled'} for this tenant.`,
        });
        this.toggled.emit();
      },
      error: () => this.togglingFeatureId.set(null),
    });
  }
}
