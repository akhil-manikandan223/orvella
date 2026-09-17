import { Component, OnInit, inject, input, output, signal } from '@angular/core';
import { FormField, form, required } from '@angular/forms/signals';
import { ButtonDirective } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { Textarea } from 'primeng/textarea';
import { MessageService } from 'primeng/api';

import { DepartmentService } from '../../../../core/data-access/department.service';
import { DepartmentRead } from '../../../../core/models/organization.model';

interface DepartmentFormValue {
  name: string;
  description: string;
}

@Component({
  selector: 'app-department-form',
  imports: [ButtonDirective, InputText, Textarea, FormField],
  templateUrl: './department-form.html',
  styleUrl: './department-form.scss',
})
export class DepartmentForm implements OnInit {
  private readonly departmentService = inject(DepartmentService);
  private readonly messageService = inject(MessageService);

  readonly department = input<DepartmentRead | null>(null);
  readonly saved = output<void>();
  readonly cancelled = output<void>();

  protected readonly submitting = signal(false);

  protected readonly model = signal<DepartmentFormValue>({ name: '', description: '' });

  protected readonly departmentForm = form(this.model, (path) => {
    required(path.name, { message: 'Name is required' });
  });

  ngOnInit(): void {
    const department = this.department();
    if (department) {
      this.model.set({ name: department.name, description: department.description ?? '' });
    }
  }

  protected onSubmit(event: Event): void {
    event.preventDefault();
    if (this.departmentForm().invalid()) {
      this.departmentForm().markAsTouched();
      return;
    }

    this.submitting.set(true);
    const value = this.model();
    const payload = { name: value.name, description: value.description || null };
    const existing = this.department();
    const request = existing
      ? this.departmentService.update(existing.id, payload)
      : this.departmentService.create(payload);

    request.subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Saved',
          detail: `Department "${value.name}" saved.`,
        });
        this.saved.emit();
      },
      error: () => this.submitting.set(false),
    });
  }
}
