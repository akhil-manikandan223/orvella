import { Component, OnInit, inject, input, output, signal } from '@angular/core';
import { FormField, disabled, form, required } from '@angular/forms/signals';
import { ButtonDirective } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { Select } from 'primeng/select';
import { MessageService } from 'primeng/api';

import { StateService } from '../../../../core/data-access/state.service';
import { CountryRead, StateRead } from '../../../../core/models/geo.model';
import { slugPattern } from '../../../../shared/validators/slug.validator';

interface StateFormValue {
  country_id: string;
  name: string;
  slug: string;
}

@Component({
  selector: 'app-state-form',
  imports: [ButtonDirective, InputText, Select, FormField],
  templateUrl: './state-form.html',
  styleUrl: './state-form.scss',
})
export class StateForm implements OnInit {
  private readonly stateService = inject(StateService);
  private readonly messageService = inject(MessageService);

  readonly state = input<StateRead | null>(null);
  readonly countries = input.required<CountryRead[]>();
  readonly saved = output<void>();
  readonly cancelled = output<void>();

  protected readonly submitting = signal(false);
  private isEditing = false;

  protected readonly model = signal<StateFormValue>({ country_id: '', name: '', slug: '' });

  protected readonly stateForm = form(this.model, (path) => {
    required(path.country_id, { message: 'Country is required' });
    disabled(path.country_id, { when: () => this.isEditing });
    required(path.name, { message: 'Name is required' });
    required(path.slug, { message: 'Slug is required' });
    slugPattern(path.slug);
  });

  ngOnInit(): void {
    const state = this.state();
    if (state) {
      this.isEditing = true;
      this.model.set({ country_id: state.country_id, name: state.name, slug: state.slug });
    }
  }

  protected onSubmit(event: Event): void {
    event.preventDefault();
    if (this.stateForm().invalid()) {
      this.stateForm().markAsTouched();
      return;
    }

    this.submitting.set(true);
    const value = this.model();
    const existing = this.state();
    const request = existing
      ? this.stateService.update(existing.id, { name: value.name, slug: value.slug })
      : this.stateService.create(value);

    request.subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Saved',
          detail: `State "${value.name}" saved.`,
        });
        this.saved.emit();
      },
      error: () => this.submitting.set(false),
    });
  }
}
