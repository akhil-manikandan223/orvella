import { Component, OnInit, computed, inject, input, output, signal } from '@angular/core';
import { FormField, form, required } from '@angular/forms/signals';
import { forkJoin, of, switchMap } from 'rxjs';

import { DepartmentService } from '../../../../core/data-access/department.service';
import { GroupService } from '../../../../core/data-access/group.service';
import { PersonService } from '../../../../core/data-access/person.service';
import { TenantUserService } from '../../../../core/data-access/tenant-user.service';
import { GroupRead } from '../../../../core/models/group.model';
import { DepartmentRead, PersonRead } from '../../../../core/models/organization.model';
import { TenantUserRead } from '../../../../core/models/tenant-user.model';
import { ToastService } from '../../../../core/feedback/toast.service';
import { HlmButton } from '../../../../shared/ui/button';
import { HlmInput } from '../../../../shared/ui/input';

interface GroupFormValue {
  name: string;
  description: string;
}

type Section = 'details' | 'members' | 'supervisors';

@Component({
  selector: 'app-group-form',
  imports: [HlmButton, HlmInput, FormField],
  templateUrl: './group-form.html',
  styleUrl: './group-form.scss',
})
export class GroupForm implements OnInit {
  private readonly groupService = inject(GroupService);
  private readonly personService = inject(PersonService);
  private readonly departmentService = inject(DepartmentService);
  private readonly tenantUserService = inject(TenantUserService);
  private readonly toast = inject(ToastService);

  readonly group = input<GroupRead | null>(null);
  readonly saved = output<void>();
  readonly cancelled = output<void>();

  protected readonly submitting = signal(false);
  protected readonly loading = signal(true);
  protected readonly section = signal<Section>('details');

  protected readonly departments = signal<DepartmentRead[]>([]);
  protected readonly people = signal<PersonRead[]>([]);
  protected readonly users = signal<TenantUserRead[]>([]);

  protected readonly departmentId = signal<string>('');
  protected readonly memberIds = signal<ReadonlySet<string>>(new Set());
  protected readonly supervisorIds = signal<ReadonlySet<string>>(new Set());
  protected readonly peopleSearch = signal('');

  protected readonly model = signal<GroupFormValue>({ name: '', description: '' });

  protected readonly groupForm = form(this.model, (path) => {
    required(path.name, { message: 'Name is required' });
  });

  protected readonly visiblePeople = computed(() => {
    const term = this.peopleSearch().trim().toLowerCase();
    const people = this.people();
    if (!term) {
      return people;
    }
    return people.filter((person) =>
      `${person.first_name} ${person.last_name}`.toLowerCase().includes(term),
    );
  });

  /** Only admins and staff can mark attendance at all, so supervising is
   * offered for those roles - a member would be given a class they could
   * never take. */
  protected readonly eligibleSupervisors = computed(() =>
    this.users().filter((user) => user.is_active && user.role !== 'member'),
  );

  ngOnInit(): void {
    const group = this.group();
    if (group) {
      this.model.set({ name: group.name, description: group.description ?? '' });
      this.departmentId.set(group.department_id ?? '');
    }

    forkJoin({
      departments: this.departmentService.list(),
      people: this.personService.list(),
      users: this.tenantUserService.listMine(),
      detail: group ? this.groupService.get(group.id) : of(null),
    }).subscribe({
      next: ({ departments, people, users, detail }) => {
        this.departments.set(departments);
        this.people.set(people);
        this.users.set(users);
        if (detail) {
          this.memberIds.set(new Set(detail.member_ids));
          this.supervisorIds.set(new Set(detail.supervisor_ids));
        }
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  protected personName(person: PersonRead): string {
    return `${person.first_name} ${person.last_name}`;
  }

  protected toggleMember(personId: string): void {
    this.memberIds.update((current) => toggle(current, personId));
  }

  protected toggleSupervisor(userId: string): void {
    this.supervisorIds.update((current) => toggle(current, userId));
  }

  protected selectAllVisible(): void {
    this.memberIds.update((current) => {
      const next = new Set(current);
      for (const person of this.visiblePeople()) {
        next.add(person.id);
      }
      return next;
    });
  }

  protected clearMembers(): void {
    this.memberIds.set(new Set());
  }

  protected onSubmit(event: Event): void {
    event.preventDefault();
    if (this.groupForm().invalid()) {
      this.groupForm().markAsTouched();
      this.section.set('details');
      return;
    }

    this.submitting.set(true);
    const value = this.model();
    const payload = {
      name: value.name,
      description: value.description || null,
      department_id: this.departmentId() || null,
    };
    const existing = this.group();
    const save = existing
      ? this.groupService.update(existing.id, payload)
      : this.groupService.create(payload);

    // Membership and supervision are separate endpoints because they replace
    // whole lists; chained off the save so a new group gets its roster in the
    // same action the user thinks of as one.
    save
      .pipe(
        switchMap((group) =>
          forkJoin({
            members: this.groupService.setMembers(group.id, [...this.memberIds()]),
            supervisors: this.groupService.setSupervisors(group.id, [...this.supervisorIds()]),
          }),
        ),
      )
      .subscribe({
        next: () => {
          this.toast.show({
            severity: 'success',
            summary: 'Saved',
            detail: `Group "${value.name}" saved.`,
          });
          this.saved.emit();
        },
        error: () => this.submitting.set(false),
      });
  }
}

function toggle(current: ReadonlySet<string>, id: string): ReadonlySet<string> {
  const next = new Set(current);
  if (!next.delete(id)) {
    next.add(id);
  }
  return next;
}
