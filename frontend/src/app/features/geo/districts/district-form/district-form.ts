import { Component, OnInit, inject, input, output, signal } from '@angular/core';
import { FormField, disabled, form, required } from '@angular/forms/signals';

import { DistrictService } from '../../../../core/data-access/district.service';
import { DistrictRead, StateRead } from '../../../../core/models/geo.model';
import { slugPattern } from '../../../../shared/validators/slug.validator';
import { ToastService } from '../../../../core/feedback/toast.service';
import { HlmButton } from '../../../../shared/ui/button';
import { HlmInput } from '../../../../shared/ui/input';
import { AppSelect } from '../../../../shared/ui/select';

interface DistrictFormValue {
  state_id: string;
  name: string;
  slug: string;
}

@Component({
  selector: 'app-district-form',
  imports: [HlmButton, HlmInput, AppSelect, FormField],
  templateUrl: './district-form.html',
  styleUrl: './district-form.scss',
})
export class DistrictForm implements OnInit {
  private readonly districtService = inject(DistrictService);
  private readonly toast = inject(ToastService);

  readonly district = input<DistrictRead | null>(null);
  readonly states = input.required<StateRead[]>();
  readonly saved = output<void>();
  readonly cancelled = output<void>();

  protected readonly submitting = signal(false);
  private isEditing = false;

  protected readonly model = signal<DistrictFormValue>({ state_id: '', name: '', slug: '' });

  protected readonly districtForm = form(this.model, (path) => {
    required(path.state_id, { message: 'State is required' });
    disabled(path.state_id, { when: () => this.isEditing });
    required(path.name, { message: 'Name is required' });
    required(path.slug, { message: 'Slug is required' });
    slugPattern(path.slug);
  });

  ngOnInit(): void {
    const district = this.district();
    if (district) {
      this.isEditing = true;
      this.model.set({ state_id: district.state_id, name: district.name, slug: district.slug });
    }
  }

  protected onSubmit(event: Event): void {
    event.preventDefault();
    if (this.districtForm().invalid()) {
      this.districtForm().markAsTouched();
      return;
    }

    this.submitting.set(true);
    const value = this.model();
    const existing = this.district();
    const request = existing
      ? this.districtService.update(existing.id, { name: value.name, slug: value.slug })
      : this.districtService.create(value);

    request.subscribe({
      next: () => {
        this.toast.show({
          severity: 'success',
          summary: 'Saved',
          detail: `District "${value.name}" saved.`,
        });
        this.saved.emit();
      },
      error: () => this.submitting.set(false),
    });
  }
}
