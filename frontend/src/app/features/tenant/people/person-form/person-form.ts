import { Component, OnInit, inject, input, output, signal } from '@angular/core';
import { FormField, email, form, required } from '@angular/forms/signals';
import { ButtonDirective } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { Select } from 'primeng/select';
import { MessageService } from 'primeng/api';

import { DepartmentService } from '../../../../core/data-access/department.service';
import { LocationService } from '../../../../core/data-access/location.service';
import { PersonService } from '../../../../core/data-access/person.service';
import {
  DepartmentRead,
  LocationRead,
  PersonRead,
} from '../../../../core/models/organization.model';

interface PersonFormValue {
  first_name: string;
  last_name: string;
  category: string;
  email: string;
  phone: string;
  department_id: string | null;
  location_id: string | null;
}

@Component({
  selector: 'app-person-form',
  imports: [ButtonDirective, InputText, Select, FormField],
  templateUrl: './person-form.html',
  styleUrl: './person-form.scss',
})
export class PersonForm implements OnInit {
  private readonly personService = inject(PersonService);
  private readonly departmentService = inject(DepartmentService);
  private readonly locationService = inject(LocationService);
  private readonly messageService = inject(MessageService);

  readonly person = input<PersonRead | null>(null);
  readonly saved = output<void>();
  readonly cancelled = output<void>();

  protected readonly submitting = signal(false);
  protected readonly departments = signal<DepartmentRead[]>([]);
  protected readonly locations = signal<LocationRead[]>([]);

  protected readonly model = signal<PersonFormValue>({
    first_name: '',
    last_name: '',
    category: '',
    email: '',
    phone: '',
    department_id: null,
    location_id: null,
  });

  protected readonly personForm = form(this.model, (path) => {
    required(path.first_name, { message: 'First name is required' });
    required(path.last_name, { message: 'Last name is required' });
    required(path.category, { message: 'Category is required' });
    email(path.email, { message: 'Enter a valid email' });
  });

  constructor() {
    this.departmentService.list().subscribe((departments) => this.departments.set(departments));
    this.locationService.list().subscribe((locations) => this.locations.set(locations));
  }

  ngOnInit(): void {
    const person = this.person();
    if (person) {
      this.model.set({
        first_name: person.first_name,
        last_name: person.last_name,
        category: person.category,
        email: person.email ?? '',
        phone: person.phone ?? '',
        department_id: person.department_id,
        location_id: person.location_id,
      });
    }
  }

  protected onSubmit(event: Event): void {
    event.preventDefault();
    if (this.personForm().invalid()) {
      this.personForm().markAsTouched();
      return;
    }

    this.submitting.set(true);
    const value = this.model();
    const payload = {
      first_name: value.first_name,
      last_name: value.last_name,
      category: value.category,
      email: value.email || null,
      phone: value.phone || null,
      department_id: value.department_id,
      location_id: value.location_id,
    };
    const existing = this.person();
    const request = existing
      ? this.personService.update(existing.id, payload)
      : this.personService.create(payload);

    request.subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Saved',
          detail: `"${value.first_name} ${value.last_name}" saved.`,
        });
        this.saved.emit();
      },
      error: () => this.submitting.set(false),
    });
  }
}
