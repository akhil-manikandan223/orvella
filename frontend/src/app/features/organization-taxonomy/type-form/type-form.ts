import { Component, OnInit, inject, input, output, signal } from '@angular/core';
import { FormField, disabled, form, required } from '@angular/forms/signals';
import { ButtonDirective } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { Select } from 'primeng/select';
import { MessageService } from 'primeng/api';

import { OrganizationTypeService } from '../../../core/data-access/organization-type.service';
import {
  OrganizationCategoryRead,
  OrganizationTypeRead,
} from '../../../core/models/organization-taxonomy.model';
import { slugPattern } from '../../../shared/validators/slug.validator';

interface TypeFormValue {
  organization_category_id: string;
  name: string;
  slug: string;
}

@Component({
  selector: 'app-type-form',
  imports: [ButtonDirective, InputText, Select, FormField],
  templateUrl: './type-form.html',
  styleUrl: './type-form.scss',
})
export class TypeForm implements OnInit {
  private readonly typeService = inject(OrganizationTypeService);
  private readonly messageService = inject(MessageService);

  readonly type = input<OrganizationTypeRead | null>(null);
  readonly categories = input.required<OrganizationCategoryRead[]>();
  readonly saved = output<void>();
  readonly cancelled = output<void>();

  protected readonly submitting = signal(false);
  private isEditing = false;

  protected readonly model = signal<TypeFormValue>({
    organization_category_id: '',
    name: '',
    slug: '',
  });

  protected readonly typeForm = form(this.model, (path) => {
    required(path.organization_category_id, { message: 'Category is required' });
    disabled(path.organization_category_id, { when: () => this.isEditing });
    required(path.name, { message: 'Name is required' });
    required(path.slug, { message: 'Slug is required' });
    slugPattern(path.slug);
  });

  ngOnInit(): void {
    const type = this.type();
    if (type) {
      this.isEditing = true;
      this.model.set({
        organization_category_id: type.organization_category_id,
        name: type.name,
        slug: type.slug,
      });
    }
  }

  protected onSubmit(event: Event): void {
    event.preventDefault();
    if (this.typeForm().invalid()) {
      this.typeForm().markAsTouched();
      return;
    }

    this.submitting.set(true);
    const value = this.model();
    const existing = this.type();
    const request = existing
      ? this.typeService.update(existing.id, { name: value.name, slug: value.slug })
      : this.typeService.create(value);

    request.subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Saved',
          detail: `Type "${value.name}" saved.`,
        });
        this.saved.emit();
      },
      error: () => this.submitting.set(false),
    });
  }
}
