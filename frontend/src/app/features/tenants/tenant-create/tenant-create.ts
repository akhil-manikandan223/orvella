import { Component, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormField, disabled, email, form, required } from '@angular/forms/signals';
import { ButtonDirective } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { Select } from 'primeng/select';
import { MessageService } from 'primeng/api';

import { CityService } from '../../../core/data-access/city.service';
import { CountryService } from '../../../core/data-access/country.service';
import { OrganizationCategoryService } from '../../../core/data-access/organization-category.service';
import { OrganizationTypeService } from '../../../core/data-access/organization-type.service';
import { StateService } from '../../../core/data-access/state.service';
import { TenantService } from '../../../core/data-access/tenant.service';
import { CityRead, CountryRead, StateRead } from '../../../core/models/geo.model';
import {
  OrganizationCategoryRead,
  OrganizationTypeRead,
} from '../../../core/models/organization-taxonomy.model';
import { PageHeader } from '../../../shared/page-header/page-header';
import { slugPattern } from '../../../shared/validators/slug.validator';

interface TenantCreateFormValue {
  name: string;
  slug: string;
  organization_type_id: string;
  max_users: number | null;
  address_line_1: string;
  address_line_2: string;
  country_id: string;
  state_id: string | null;
  city_id: string | null;
  postal_code: string;
  license_number: string;
  logo_url: string;
  key_contact_name: string;
  key_contact_email: string;
  key_contact_phone: string;
}

@Component({
  selector: 'app-tenant-create',
  imports: [ButtonDirective, InputText, Select, FormField, PageHeader, RouterLink],
  templateUrl: './tenant-create.html',
  styleUrl: './tenant-create.scss',
})
export class TenantCreate {
  private readonly tenantService = inject(TenantService);
  private readonly organizationCategoryService = inject(OrganizationCategoryService);
  private readonly organizationTypeService = inject(OrganizationTypeService);
  private readonly countryService = inject(CountryService);
  private readonly stateService = inject(StateService);
  private readonly cityService = inject(CityService);
  private readonly messageService = inject(MessageService);
  private readonly router = inject(Router);

  protected readonly submitting = signal(false);
  protected readonly organizationCategories = signal<OrganizationCategoryRead[]>([]);
  protected readonly organizationTypes = signal<OrganizationTypeRead[]>([]);
  protected readonly countries = signal<CountryRead[]>([]);
  protected readonly states = signal<StateRead[]>([]);
  protected readonly cities = signal<CityRead[]>([]);

  // UI-only filter: a tenant only stores organization_type_id, not a category,
  // so this never gets submitted - it just narrows the Type dropdown below.
  protected readonly categoryFilter = form(signal<string | null>(null));

  protected readonly filteredOrganizationTypes = computed(() => {
    const categoryId = this.categoryFilter().value();
    if (!categoryId) {
      return [];
    }
    return this.organizationTypes().filter(
      (type) => type.organization_category_id === categoryId,
    );
  });

  protected readonly model = signal<TenantCreateFormValue>({
    name: '',
    slug: '',
    organization_type_id: '',
    max_users: null,
    address_line_1: '',
    address_line_2: '',
    country_id: '',
    state_id: null,
    city_id: null,
    postal_code: '',
    license_number: '',
    logo_url: '',
    key_contact_name: '',
    key_contact_email: '',
    key_contact_phone: '',
  });

  protected readonly tenantForm = form(this.model, (path) => {
    required(path.name, { message: 'Name is required' });
    required(path.slug, { message: 'Slug is required' });
    slugPattern(path.slug);
    required(path.organization_type_id, { message: 'Organization type is required' });
    disabled(path.organization_type_id, { when: () => !this.categoryFilter().value() });

    required(path.address_line_1, { message: 'Address is required' });
    required(path.country_id, { message: 'Country is required' });
    disabled(path.state_id, { when: () => !this.model().country_id });
    disabled(path.city_id, { when: () => !this.model().state_id });
    required(path.city_id, { message: 'City is required' });

    required(path.license_number, { message: 'License number is required' });
    required(path.key_contact_name, { message: 'Contact name is required' });
    required(path.key_contact_email, { message: 'Contact email is required' });
    email(path.key_contact_email);
    required(path.key_contact_phone, { message: 'Contact phone is required' });
  });

  constructor() {
    this.organizationCategoryService
      .list()
      .subscribe((categories) => this.organizationCategories.set(categories));
    this.organizationTypeService.list().subscribe((types) => this.organizationTypes.set(types));
    this.countryService.list().subscribe((countries) => this.countries.set(countries));
  }

  protected onCategoryChanged(): void {
    this.model.update((current) => ({ ...current, organization_type_id: '' }));
  }

  protected onCountryChanged(countryId: string | null): void {
    this.states.set([]);
    this.cities.set([]);
    this.model.update((current) => ({ ...current, state_id: null, city_id: null }));
    if (countryId) {
      this.stateService.list(countryId).subscribe((states) => this.states.set(states));
    }
  }

  protected onStateChanged(stateId: string | null): void {
    this.cities.set([]);
    this.model.update((current) => ({ ...current, city_id: null }));
    if (stateId) {
      this.cityService.list(stateId).subscribe((cities) => this.cities.set(cities));
    }
  }

  protected onSubmit(event?: Event): void {
    event?.preventDefault();
    if (this.tenantForm().invalid()) {
      this.tenantForm().markAsTouched();
      return;
    }

    this.submitting.set(true);
    const value = this.model();
    this.tenantService
      .create({
        name: value.name,
        slug: value.slug,
        organization_type_id: value.organization_type_id,
        max_users: value.max_users,
        address_line_1: value.address_line_1,
        address_line_2: value.address_line_2 || null,
        country_id: value.country_id,
        state_id: value.state_id,
        city_id: value.city_id ?? '',
        postal_code: value.postal_code || null,
        license_number: value.license_number,
        logo_url: value.logo_url || null,
        key_contact_name: value.key_contact_name,
        key_contact_email: value.key_contact_email,
        key_contact_phone: value.key_contact_phone,
      })
      .subscribe({
        next: (tenant) => {
          this.messageService.add({
            severity: 'success',
            summary: 'Tenant created',
            detail: `"${tenant.name}" was created successfully.`,
          });
          this.router.navigate(['/tenants', tenant.id]);
        },
        error: () => this.submitting.set(false),
      });
  }
}
