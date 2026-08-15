import { Component, OnInit, inject, input, output, signal } from '@angular/core';
import { FormField, disabled, form, required } from '@angular/forms/signals';
import { ButtonDirective } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { Textarea } from 'primeng/textarea';
import { Select } from 'primeng/select';
import { MessageService } from 'primeng/api';

import { FeatureService } from '../../../core/data-access/feature.service';
import { FeatureRead, FeatureStatus } from '../../../core/models/feature.model';
import { slugPattern } from '../../../shared/validators/slug.validator';

const STATUS_OPTIONS: { label: string; value: FeatureStatus }[] = [
  { label: 'Active', value: 'active' },
  { label: 'Deprecated', value: 'deprecated' },
];

interface FeatureFormValue {
  key: string;
  name: string;
  description: string;
  status: FeatureStatus;
}

@Component({
  selector: 'app-feature-form',
  imports: [ButtonDirective, InputText, Textarea, Select, FormField],
  templateUrl: './feature-form.html',
  styleUrl: './feature-form.scss',
})
export class FeatureForm implements OnInit {
  private readonly featureService = inject(FeatureService);
  private readonly messageService = inject(MessageService);

  readonly feature = input<FeatureRead | null>(null);
  readonly saved = output<void>();
  readonly cancelled = output<void>();

  protected readonly submitting = signal(false);
  protected readonly statusOptions = STATUS_OPTIONS;
  private isEditing = false;

  protected readonly model = signal<FeatureFormValue>({
    key: '',
    name: '',
    description: '',
    status: 'active',
  });

  protected readonly featureForm = form(this.model, (path) => {
    required(path.key, { message: 'Key is required' });
    disabled(path.key, { when: () => this.isEditing });
    slugPattern(path.key);
    required(path.name, { message: 'Name is required' });
  });

  ngOnInit(): void {
    const feature = this.feature();
    if (feature) {
      this.isEditing = true;
      this.model.set({
        key: feature.key,
        name: feature.name,
        description: feature.description ?? '',
        status: feature.status,
      });
    }
  }

  protected onSubmit(event: Event): void {
    event.preventDefault();
    if (this.featureForm().invalid()) {
      this.featureForm().markAsTouched();
      return;
    }

    this.submitting.set(true);
    const value = this.model();
    const existing = this.feature();
    const request = existing
      ? this.featureService.update(existing.id, {
          name: value.name,
          description: value.description || null,
          status: value.status,
        })
      : this.featureService.create({
          key: value.key,
          name: value.name,
          description: value.description || null,
          status: value.status,
        });

    request.subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Saved',
          detail: `Feature "${value.name}" saved.`,
        });
        this.saved.emit();
      },
      error: () => this.submitting.set(false),
    });
  }
}
