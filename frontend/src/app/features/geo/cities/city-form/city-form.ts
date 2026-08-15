import { Component, OnInit, computed, effect, inject, input, output, signal } from '@angular/core';
import { FormField, disabled, form, required } from '@angular/forms/signals';
import { ButtonDirective } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { Select } from 'primeng/select';
import { MessageService } from 'primeng/api';

import { CityService } from '../../../../core/data-access/city.service';
import { CityRead, DistrictRead, StateRead } from '../../../../core/models/geo.model';
import { slugPattern } from '../../../../shared/validators/slug.validator';

interface CityFormValue {
  state_id: string;
  district_id: string | null;
  name: string;
  slug: string;
}

@Component({
  selector: 'app-city-form',
  imports: [ButtonDirective, InputText, Select, FormField],
  templateUrl: './city-form.html',
  styleUrl: './city-form.scss',
})
export class CityForm implements OnInit {
  private readonly cityService = inject(CityService);
  private readonly messageService = inject(MessageService);

  readonly city = input<CityRead | null>(null);
  readonly states = input.required<StateRead[]>();
  readonly districts = input.required<DistrictRead[]>();
  readonly saved = output<void>();
  readonly cancelled = output<void>();

  protected readonly submitting = signal(false);
  private isEditing = false;

  protected readonly model = signal<CityFormValue>({
    state_id: '',
    district_id: null,
    name: '',
    slug: '',
  });

  protected readonly filteredDistricts = computed(() =>
    this.districts().filter((district) => district.state_id === this.model().state_id),
  );

  protected readonly cityForm = form(this.model, (path) => {
    required(path.state_id, { message: 'State is required' });
    disabled(path.state_id, { when: () => this.isEditing });
    required(path.name, { message: 'Name is required' });
    required(path.slug, { message: 'Slug is required' });
    slugPattern(path.slug);
  });

  constructor() {
    effect(() => {
      const { state_id, district_id } = this.model();
      const stillValid = this.districts().some(
        (district) => district.id === district_id && district.state_id === state_id,
      );
      if (district_id && !stillValid) {
        this.model.update((current) => ({ ...current, district_id: null }));
      }
    });
  }

  ngOnInit(): void {
    const city = this.city();
    if (city) {
      this.isEditing = true;
      this.model.set({
        state_id: city.state_id,
        district_id: city.district_id,
        name: city.name,
        slug: city.slug,
      });
    }
  }

  protected onSubmit(event: Event): void {
    event.preventDefault();
    if (this.cityForm().invalid()) {
      this.cityForm().markAsTouched();
      return;
    }

    this.submitting.set(true);
    const value = this.model();
    const existing = this.city();
    const request = existing
      ? this.cityService.update(existing.id, {
          district_id: value.district_id,
          name: value.name,
          slug: value.slug,
        })
      : this.cityService.create(value);

    request.subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Saved',
          detail: `City "${value.name}" saved.`,
        });
        this.saved.emit();
      },
      error: () => this.submitting.set(false),
    });
  }
}
