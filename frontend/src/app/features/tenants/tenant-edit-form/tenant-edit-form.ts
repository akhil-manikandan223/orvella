import { Component, OnInit, inject, input, output, signal } from '@angular/core';
import { FormField, disabled, email, form, required } from '@angular/forms/signals';
import { ButtonDirective } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { Select } from 'primeng/select';
import { MessageService } from 'primeng/api';

import { CityService } from '../../../core/data-access/city.service';
import { CountryService } from '../../../core/data-access/country.service';
import { StateService } from '../../../core/data-access/state.service';
import { TenantService } from '../../../core/data-access/tenant.service';
import { CityRead, CountryRead, StateRead } from '../../../core/models/geo.model';
import { TenantRead } from '../../../core/models/tenant.model';

interface TenantEditFormValue {
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
  selector: 'app-tenant-edit-form',
  imports: [ButtonDirective, InputText, Select, FormField],
  templateUrl: './tenant-edit-form.html',
  styleUrl: './tenant-edit-form.scss',
})
export class TenantEditForm implements OnInit {
  private readonly tenantService = inject(TenantService);
  private readonly countryService = inject(CountryService);
  private readonly stateService = inject(StateService);
  private readonly cityService = inject(CityService);
  private readonly messageService = inject(MessageService);

  readonly tenant = input<TenantRead | null>(null);
  readonly saved = output<void>();
  readonly cancelled = output<void>();

  protected readonly submitting = signal(false);
  protected readonly countries = signal<CountryRead[]>([]);
  protected readonly states = signal<StateRead[]>([]);
  protected readonly cities = signal<CityRead[]>([]);

  protected readonly model = signal<TenantEditFormValue>({
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
    this.countryService.list().subscribe((countries) => this.countries.set(countries));
  }

  ngOnInit(): void {
    const tenant = this.tenant();
    if (!tenant) {
      return;
    }

    if (tenant.country_id) {
      this.stateService.list(tenant.country_id).subscribe((states) => this.states.set(states));
    }
    if (tenant.state_id) {
      this.cityService.list(tenant.state_id).subscribe((cities) => this.cities.set(cities));
    }

    this.model.set({
      max_users: tenant.max_users,
      address_line_1: tenant.address_line_1,
      address_line_2: tenant.address_line_2 ?? '',
      country_id: tenant.country_id,
      state_id: tenant.state_id,
      city_id: tenant.city_id,
      postal_code: tenant.postal_code ?? '',
      license_number: tenant.license_number,
      logo_url: tenant.logo_url ?? '',
      key_contact_name: tenant.key_contact_name,
      key_contact_email: tenant.key_contact_email,
      key_contact_phone: tenant.key_contact_phone,
    });
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

  protected onSubmit(event: Event): void {
    event.preventDefault();
    if (this.tenantForm().invalid()) {
      this.tenantForm().markAsTouched();
      return;
    }

    this.submitting.set(true);
    const value = this.model();
    this.tenantService
      .update(this.tenant()!.id, {
        max_users: value.max_users,
        address_line_1: value.address_line_1,
        address_line_2: value.address_line_2 || null,
        country_id: value.country_id,
        state_id: value.state_id,
        city_id: value.city_id ?? undefined,
        postal_code: value.postal_code || null,
        license_number: value.license_number,
        logo_url: value.logo_url || null,
        key_contact_name: value.key_contact_name,
        key_contact_email: value.key_contact_email,
        key_contact_phone: value.key_contact_phone,
      })
      .subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Saved',
            detail: 'Tenant profile updated.',
          });
          this.saved.emit();
        },
        error: () => this.submitting.set(false),
      });
  }
}
