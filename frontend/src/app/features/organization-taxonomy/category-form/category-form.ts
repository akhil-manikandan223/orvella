import { Component, OnInit, inject, input, output, signal } from '@angular/core';
import { FormField, form, required } from '@angular/forms/signals';
import { ButtonDirective } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { MessageService } from 'primeng/api';

import { OrganizationCategoryService } from '../../../core/data-access/organization-category.service';
import { OrganizationCategoryRead } from '../../../core/models/organization-taxonomy.model';
import { slugPattern } from '../../../shared/validators/slug.validator';

interface CategoryFormValue {
  name: string;
  slug: string;
}

@Component({
  selector: 'app-category-form',
  imports: [ButtonDirective, InputText, FormField],
  templateUrl: './category-form.html',
  styleUrl: './category-form.scss',
})
export class CategoryForm implements OnInit {
  private readonly categoryService = inject(OrganizationCategoryService);
  private readonly messageService = inject(MessageService);

  readonly category = input<OrganizationCategoryRead | null>(null);
  readonly saved = output<void>();
  readonly cancelled = output<void>();

  protected readonly submitting = signal(false);

  protected readonly model = signal<CategoryFormValue>({ name: '', slug: '' });

  protected readonly categoryForm = form(this.model, (path) => {
    required(path.name, { message: 'Name is required' });
    required(path.slug, { message: 'Slug is required' });
    slugPattern(path.slug);
  });

  ngOnInit(): void {
    const category = this.category();
    if (category) {
      this.model.set({ name: category.name, slug: category.slug });
    }
  }

  protected onSubmit(event: Event): void {
    event.preventDefault();
    if (this.categoryForm().invalid()) {
      this.categoryForm().markAsTouched();
      return;
    }

    this.submitting.set(true);
    const value = this.model();
    const existing = this.category();
    const request = existing
      ? this.categoryService.update(existing.id, value)
      : this.categoryService.create(value);

    request.subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Saved',
          detail: `Category "${value.name}" saved.`,
        });
        this.saved.emit();
      },
      error: () => this.submitting.set(false),
    });
  }
}
