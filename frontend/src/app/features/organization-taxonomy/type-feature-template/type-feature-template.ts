import { Component, computed, effect, inject, input, signal, untracked } from '@angular/core';
import { FormField, form } from '@angular/forms/signals';
import { forkJoin } from 'rxjs';

import { FeatureService } from '../../../core/data-access/feature.service';
import { OrganizationTypeService } from '../../../core/data-access/organization-type.service';
import { FeatureRead } from '../../../core/models/feature.model';
import { OrganizationTypeRead } from '../../../core/models/organization-taxonomy.model';
import { PageHeader } from '../../../shared/page-header/page-header';
import { EmptyState } from '../../../shared/empty-state/empty-state';
import { ToastService } from '../../../core/feedback/toast.service';
import { ConfirmService } from '../../../core/feedback/confirm.service';
import { HlmButton } from '../../../shared/ui/button';
import { AppSelect } from '../../../shared/ui/select';

@Component({
  selector: 'app-type-feature-template',
  imports: [HlmButton, AppSelect, FormField, PageHeader, EmptyState],
  templateUrl: './type-feature-template.html',
  styleUrl: './type-feature-template.scss',
})
export class TypeFeatureTemplate {
  private readonly typeService = inject(OrganizationTypeService);
  private readonly featureService = inject(FeatureService);
  private readonly confirmService = inject(ConfirmService);
  private readonly toast = inject(ToastService);

  readonly id = input.required<string>();

  protected readonly type = signal<OrganizationTypeRead | null>(null);
  protected readonly allFeatures = signal<FeatureRead[]>([]);
  protected readonly templateFeatures = signal<FeatureRead[]>([]);
  protected readonly loading = signal(false);
  protected readonly featureIdToAddModel = signal<string | null>(null);
  protected readonly featureIdToAdd = form(this.featureIdToAddModel);
  protected readonly adding = signal(false);

  protected readonly availableFeatures = computed(() => {
    const attachedIds = new Set(this.templateFeatures().map((feature) => feature.id));
    return this.allFeatures().filter((feature) => !attachedIds.has(feature.id));
  });

  constructor() {
    // Not a plain this.load(): `id` is a required input bound from the route
    // (withComponentInputBinding), and reading it in the constructor throws
    // NG0950 before the router has set it. The effect runs once it is set,
    // and again if the route param changes.
    effect(() => {
      this.id();
      untracked(() => this.load());
    });
  }

  protected addFeature(): void {
    const featureId = this.featureIdToAddModel();
    if (!featureId) {
      return;
    }
    this.adding.set(true);
    this.typeService.attachTemplateFeature(this.id(), featureId).subscribe({
      next: () => {
        this.featureIdToAddModel.set(null);
        this.adding.set(false);
        this.reloadTemplateFeatures();
      },
      error: () => this.adding.set(false),
    });
  }

  protected confirmRemove(feature: FeatureRead): void {
    this.confirmService.confirm({
      header: 'Remove Feature',
      message: `Remove "${feature.name}" from this type's feature template? Tenants created afterwards will no longer receive it by default.`,
      destructive: true,
      accept: () => this.removeFeature(feature),
    });
  }

  private removeFeature(feature: FeatureRead): void {
    this.typeService.detachTemplateFeature(this.id(), feature.id).subscribe({
      next: () => {
        this.toast.show({
          severity: 'success',
          summary: 'Removed',
          detail: `"${feature.name}" removed from the template.`,
        });
        this.reloadTemplateFeatures();
      },
    });
  }

  private load(): void {
    this.loading.set(true);
    forkJoin({
      types: this.typeService.list(),
      features: this.featureService.list(),
      templateFeatures: this.typeService.listTemplateFeatures(this.id()),
    }).subscribe({
      next: ({ types, features, templateFeatures }) => {
        this.type.set(types.find((type) => type.id === this.id()) ?? null);
        this.allFeatures.set(features);
        this.templateFeatures.set(templateFeatures);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  private reloadTemplateFeatures(): void {
    this.typeService.listTemplateFeatures(this.id()).subscribe((features) => {
      this.templateFeatures.set(features);
    });
  }
}
