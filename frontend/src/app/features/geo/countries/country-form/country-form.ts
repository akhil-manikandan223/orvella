import { Component, OnInit, inject, input, output, signal } from '@angular/core';
import { FormField, form, required } from '@angular/forms/signals';

import { CountryService } from '../../../../core/data-access/country.service';
import { CountryRead } from '../../../../core/models/geo.model';
import { slugPattern } from '../../../../shared/validators/slug.validator';
import { ToastService } from '../../../../core/feedback/toast.service';
import { HlmButton } from '../../../../shared/ui/button';
import { HlmInput } from '../../../../shared/ui/input';

interface CountryFormValue {
  name: string;
  slug: string;
}

@Component({
  selector: 'app-country-form',
  imports: [HlmButton, HlmInput, FormField],
  templateUrl: './country-form.html',
  styleUrl: './country-form.scss',
})
export class CountryForm implements OnInit {
  private readonly countryService = inject(CountryService);
  private readonly toast = inject(ToastService);

  readonly country = input<CountryRead | null>(null);
  readonly saved = output<void>();
  readonly cancelled = output<void>();

  protected readonly submitting = signal(false);

  protected readonly model = signal<CountryFormValue>({ name: '', slug: '' });

  protected readonly countryForm = form(this.model, (path) => {
    required(path.name, { message: 'Name is required' });
    required(path.slug, { message: 'Slug is required' });
    slugPattern(path.slug);
  });

  ngOnInit(): void {
    const country = this.country();
    if (country) {
      this.model.set({ name: country.name, slug: country.slug });
    }
  }

  protected onSubmit(event: Event): void {
    event.preventDefault();
    if (this.countryForm().invalid()) {
      this.countryForm().markAsTouched();
      return;
    }

    this.submitting.set(true);
    const value = this.model();
    const existing = this.country();
    const request = existing
      ? this.countryService.update(existing.id, value)
      : this.countryService.create(value);

    request.subscribe({
      next: () => {
        this.toast.show({
          severity: 'success',
          summary: 'Saved',
          detail: `Country "${value.name}" saved.`,
        });
        this.saved.emit();
      },
      error: () => this.submitting.set(false),
    });
  }
}
