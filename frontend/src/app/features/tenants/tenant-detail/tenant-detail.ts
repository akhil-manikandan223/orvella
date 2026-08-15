import { Component, computed, inject, input, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { ButtonDirective } from 'primeng/button';
import { ConfirmationService, MessageService } from 'primeng/api';

import { CityService } from '../../../core/data-access/city.service';
import { CountryService } from '../../../core/data-access/country.service';
import { OrganizationTypeService } from '../../../core/data-access/organization-type.service';
import { StateService } from '../../../core/data-access/state.service';
import { TenantService } from '../../../core/data-access/tenant.service';
import { CityRead, CountryRead, StateRead } from '../../../core/models/geo.model';
import { OrganizationTypeRead } from '../../../core/models/organization-taxonomy.model';
import { TenantDetailRead } from '../../../core/models/tenant.model';
import { PageHeader } from '../../../shared/page-header/page-header';
import { StatusBadge } from '../../../shared/status-badge/status-badge';
import { TenantFeatureToggles } from '../tenant-feature-toggles/tenant-feature-toggles';

@Component({
  selector: 'app-tenant-detail',
  imports: [ButtonDirective, PageHeader, RouterLink, StatusBadge, TenantFeatureToggles],
  templateUrl: './tenant-detail.html',
  styleUrl: './tenant-detail.scss',
})
export class TenantDetail implements OnInit {
  private readonly tenantService = inject(TenantService);
  private readonly organizationTypeService = inject(OrganizationTypeService);
  private readonly countryService = inject(CountryService);
  private readonly stateService = inject(StateService);
  private readonly cityService = inject(CityService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly messageService = inject(MessageService);

  readonly id = input.required<string>();

  protected readonly tenant = signal<TenantDetailRead | null>(null);
  protected readonly organizationTypes = signal<OrganizationTypeRead[]>([]);
  protected readonly countries = signal<CountryRead[]>([]);
  protected readonly states = signal<StateRead[]>([]);
  protected readonly cities = signal<CityRead[]>([]);
  protected readonly loading = signal(false);

  protected readonly organizationTypeName = computed(() => {
    const tenant = this.tenant();
    if (!tenant) {
      return '—';
    }
    return (
      this.organizationTypes().find((type) => type.id === tenant.organization_type_id)?.name ??
      '—'
    );
  });

  protected readonly countryName = computed(() => {
    const tenant = this.tenant();
    if (!tenant) {
      return '—';
    }
    return this.countries().find((country) => country.id === tenant.country_id)?.name ?? '—';
  });

  protected readonly stateName = computed(() => {
    const tenant = this.tenant();
    if (!tenant?.state_id) {
      return '—';
    }
    return this.states().find((state) => state.id === tenant.state_id)?.name ?? '—';
  });

  protected readonly cityName = computed(() => {
    const tenant = this.tenant();
    if (!tenant) {
      return '—';
    }
    return this.cities().find((city) => city.id === tenant.city_id)?.name ?? '—';
  });

  protected readonly formattedAddress = computed(() => {
    const tenant = this.tenant();
    if (!tenant) {
      return '—';
    }
    const parts = [
      tenant.address_line_1,
      tenant.address_line_2,
      this.cityName(),
      tenant.state_id ? this.stateName() : null,
      this.countryName(),
      tenant.postal_code,
    ];
    return parts.filter(Boolean).join(', ');
  });

  constructor() {
    forkJoin({
      types: this.organizationTypeService.list(),
      countries: this.countryService.list(),
      states: this.stateService.list(),
      cities: this.cityService.list(),
    }).subscribe(({ types, countries, states, cities }) => {
      this.organizationTypes.set(types);
      this.countries.set(countries);
      this.states.set(states);
      this.cities.set(cities);
    });
  }

  ngOnInit(): void {
    this.load();
  }

  protected confirmDeactivate(): void {
    const tenant = this.tenant();
    if (!tenant) {
      return;
    }
    this.confirmationService.confirm({
      header: 'Deactivate Tenant',
      message: `Deactivate "${tenant.name}"? Its users will immediately lose access to the platform.`,
      icon: 'pi pi-exclamation-triangle',
      acceptButtonProps: { severity: 'danger' },
      accept: () => this.setActive(false),
    });
  }

  protected activate(): void {
    this.setActive(true);
  }

  private setActive(isActive: boolean): void {
    this.tenantService.update(this.id(), { is_active: isActive }).subscribe(() => {
      this.messageService.add({
        severity: 'success',
        summary: isActive ? 'Tenant activated' : 'Tenant deactivated',
        detail: isActive
          ? 'The tenant can access the platform again.'
          : 'The tenant no longer has access to the platform.',
      });
      this.load();
    });
  }

  protected load(): void {
    this.loading.set(true);
    this.tenantService.get(this.id()).subscribe({
      next: (tenant) => {
        this.tenant.set(tenant);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
