import { Component, OnInit, inject, input, output, signal } from '@angular/core';
import { FormField, form, required } from '@angular/forms/signals';
import { ButtonDirective } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { Textarea } from 'primeng/textarea';
import { MessageService } from 'primeng/api';

import { LocationService } from '../../../../core/data-access/location.service';
import { LocationRead } from '../../../../core/models/organization.model';

interface LocationFormValue {
  name: string;
  address: string;
}

@Component({
  selector: 'app-location-form',
  imports: [ButtonDirective, InputText, Textarea, FormField],
  templateUrl: './location-form.html',
  styleUrl: './location-form.scss',
})
export class LocationForm implements OnInit {
  private readonly locationService = inject(LocationService);
  private readonly messageService = inject(MessageService);

  readonly location = input<LocationRead | null>(null);
  readonly saved = output<void>();
  readonly cancelled = output<void>();

  protected readonly submitting = signal(false);

  protected readonly model = signal<LocationFormValue>({ name: '', address: '' });

  protected readonly locationForm = form(this.model, (path) => {
    required(path.name, { message: 'Name is required' });
  });

  ngOnInit(): void {
    const location = this.location();
    if (location) {
      this.model.set({ name: location.name, address: location.address ?? '' });
    }
  }

  protected onSubmit(event: Event): void {
    event.preventDefault();
    if (this.locationForm().invalid()) {
      this.locationForm().markAsTouched();
      return;
    }

    this.submitting.set(true);
    const value = this.model();
    const payload = { name: value.name, address: value.address || null };
    const existing = this.location();
    const request = existing
      ? this.locationService.update(existing.id, payload)
      : this.locationService.create(payload);

    request.subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Saved',
          detail: `Location "${value.name}" saved.`,
        });
        this.saved.emit();
      },
      error: () => this.submitting.set(false),
    });
  }
}
