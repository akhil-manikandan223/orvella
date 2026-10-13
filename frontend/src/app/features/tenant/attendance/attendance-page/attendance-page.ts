import { Component, TemplateRef, computed, inject, signal, viewChild } from '@angular/core';
import { forkJoin } from 'rxjs';

import { AttendanceService } from '../../../../core/data-access/attendance.service';
import { DepartmentService } from '../../../../core/data-access/department.service';
import { GroupService } from '../../../../core/data-access/group.service';
import { PersonService } from '../../../../core/data-access/person.service';
import { TenantAuthService } from '../../../../core/tenant-auth/tenant-auth.service';
import { AttendanceStatus, AttendanceSummaryRead } from '../../../../core/models/attendance.model';
import { GroupRead } from '../../../../core/models/group.model';
import { DepartmentRead, PersonRead } from '../../../../core/models/organization.model';
import { ToastService } from '../../../../core/feedback/toast.service';
import { DataTable } from '../../../../shared/data-table/data-table';
import { DataTableColumn } from '../../../../shared/data-table/data-table.model';
import { PageHeader } from '../../../../shared/page-header/page-header';

type Tab = 'mark' | 'summary';

/** One person's row on the marking sheet. */
interface RosterRow {
  person_id: string;
  name: string;
  category: string;
  department: string;
  status: AttendanceStatus;
}

interface SummaryRow extends AttendanceSummaryRead {
  name: string;
}

const STATUS_OPTIONS: { value: AttendanceStatus; short: string; label: string }[] = [
  { value: 'present', short: 'P', label: 'Present' },
  { value: 'absent', short: 'A', label: 'Absent' },
  { value: 'late', short: 'L', label: 'Late' },
  { value: 'excused', short: 'E', label: 'Excused' },
];

function toIsoDate(value: Date): string {
  // Local calendar date, not UTC: toISOString() would roll the date backwards
  // for anyone east of Greenwich in the evening, marking the wrong day.
  const offset = value.getTimezoneOffset() * 60_000;
  return new Date(value.getTime() - offset).toISOString().slice(0, 10);
}

@Component({
  selector: 'app-attendance-page',
  imports: [PageHeader, DataTable],
  templateUrl: './attendance-page.html',
  styleUrl: './attendance-page.scss',
})
export class AttendancePage {
  private readonly attendanceService = inject(AttendanceService);
  private readonly personService = inject(PersonService);
  private readonly departmentService = inject(DepartmentService);
  private readonly groupService = inject(GroupService);
  private readonly tenantAuthService = inject(TenantAuthService);
  private readonly toast = inject(ToastService);

  protected readonly statusOptions = STATUS_OPTIONS;
  protected readonly activeTab = signal<Tab>('mark');
  protected readonly loading = signal(false);
  protected readonly saving = signal(false);

  /** Both roles mark; what differs is who they may mark. An admin covers the
   * whole tenant, a staff member only the groups they supervise - and that
   * narrowing is enforced by the API, not by this flag. */
  protected readonly canMark = computed(() => {
    const role = this.tenantAuthService.user()?.role;
    return role === 'admin' || role === 'staff';
  });

  private readonly isAdmin = computed(() => this.tenantAuthService.user()?.role === 'admin');

  // ---- Mark tab ----
  protected readonly date = signal(toIsoDate(new Date()));
  protected readonly departmentFilter = signal<string>('');
  protected readonly departments = signal<DepartmentRead[]>([]);
  private readonly people = signal<PersonRead[]>([]);
  private readonly statuses = signal<Record<string, AttendanceStatus>>({});

  // ---- Groups ----
  protected readonly groups = signal<GroupRead[]>([]);
  protected readonly groupFilter = signal<string>('');
  /** group id -> person ids, filled from /groups/supervised for staff and
   * fetched on demand when an admin picks a group. */
  private readonly groupMembers = signal<Record<string, string[]>>({});
  /** The people a staff user may mark at all, or null for an admin (no
   * restriction). An empty set means they supervise nothing - which has to
   * show an empty roster, never the whole tenant. */
  private readonly supervisedPersonIds = signal<ReadonlySet<string> | null>(null);

  /** True once the day has been saved at least once - lets the UI say whether
   * a day has actually been taken, rather than silently showing defaults. */
  protected readonly dayAlreadyMarked = signal(false);

  private readonly statusCellTpl =
    viewChild.required<TemplateRef<{ $implicit: RosterRow }>>('statusCell');

  protected readonly roster = computed<RosterRow[]>(() => {
    const departmentNames = new Map(this.departments().map((d) => [d.id, d.name]));
    const statuses = this.statuses();
    const filter = this.departmentFilter();
    const scope = this.supervisedPersonIds();
    const selectedGroup = this.groupFilter();
    const members = selectedGroup ? new Set(this.groupMembers()[selectedGroup] ?? []) : null;

    return this.people()
      .filter((person) => scope === null || scope.has(person.id))
      .filter((person) => members === null || members.has(person.id))
      .filter((person) => !filter || person.department_id === filter)
      .map((person) => ({
        person_id: person.id,
        name: `${person.first_name} ${person.last_name}`,
        category: person.category,
        department: (person.department_id && departmentNames.get(person.department_id)) || '—',
        // Defaults to present: the roster is saved in full, so every person
        // ends up with a record and monthly totals stay correct.
        status: statuses[person.id] ?? 'present',
      }));
  });

  /** A teacher with no class needs to be told that, not shown "add people
   * first" - the people exist, they're just not theirs to mark. */
  protected readonly emptyRosterMessage = computed(() => {
    if (this.supervisedPersonIds()?.size === 0) {
      return 'You do not supervise any groups yet. Ask an administrator to assign you one.';
    }
    if (this.groupFilter()) {
      return 'No one in this group yet.';
    }
    return 'No people to mark. Add people first.';
  });

  protected readonly tally = computed(() => {
    const counts = { present: 0, absent: 0, late: 0, excused: 0 };
    for (const row of this.roster()) {
      counts[row.status] += 1;
    }
    return counts;
  });

  protected readonly markColumns = computed<DataTableColumn<RosterRow>[]>(() => [
    { field: 'name', header: 'Name', sortable: true },
    { field: 'category', header: 'Category', sortable: true, hideOnNarrow: true },
    { field: 'department', header: 'Department', hideOnNarrow: true },
    { field: 'status', header: 'Status', template: this.statusCellTpl(), width: '16rem' },
  ]);

  // ---- Summary tab ----
  protected readonly summaryStart = signal(toIsoDate(firstOfThisMonth()));
  protected readonly summaryEnd = signal(toIsoDate(new Date()));
  private readonly summaries = signal<AttendanceSummaryRead[]>([]);

  protected readonly summaryRows = computed<SummaryRow[]>(() => {
    const names = new Map(
      this.people().map((p) => [p.id, `${p.first_name} ${p.last_name}`] as const),
    );
    return this.summaries().map((summary) => ({
      ...summary,
      name: names.get(summary.person_id) ?? 'Unknown',
    }));
  });

  protected readonly summaryColumns: DataTableColumn<SummaryRow>[] = [
    { field: 'name', header: 'Name', sortable: true },
    { field: 'present', header: 'Present', sortable: true, align: 'right' },
    { field: 'absent', header: 'Absent', sortable: true, align: 'right' },
    { field: 'late', header: 'Late', sortable: true, align: 'right', hideOnNarrow: true },
    { field: 'excused', header: 'Excused', sortable: true, align: 'right', hideOnNarrow: true },
    { field: 'total', header: 'Marked days', sortable: true, align: 'right' },
  ];

  constructor() {
    this.loadGroups();
    this.loadDay();
  }

  protected onGroupChange(groupId: string): void {
    this.groupFilter.set(groupId);
    // An admin's group list comes without rosters (one query, not one per
    // group), so fetch this one's membership the first time it's picked.
    if (groupId && this.groupMembers()[groupId] === undefined) {
      this.groupService.get(groupId).subscribe((group) => {
        this.groupMembers.update((current) => ({
          ...current,
          [group.id]: group.member_ids,
        }));
      });
    }
  }

  private loadGroups(): void {
    if (this.isAdmin()) {
      this.groupService.list().subscribe((groups) => this.groups.set(groups));
      return;
    }

    // Start closed, not open: until the supervised groups come back the
    // roster shows nobody rather than briefly flashing the whole tenant.
    this.supervisedPersonIds.set(new Set());
    this.groupService.supervised().subscribe((groups) => {
      this.groups.set(groups);
      this.groupMembers.set(
        Object.fromEntries(groups.map((group) => [group.id, group.member_ids])),
      );
      this.supervisedPersonIds.set(new Set(groups.flatMap((group) => group.member_ids)));
    });
  }

  protected selectTab(tab: Tab): void {
    this.activeTab.set(tab);
    if (tab === 'summary') {
      this.loadSummary();
    }
  }

  protected onDateChange(value: string): void {
    this.date.set(value);
    this.loadDay();
  }

  protected setStatus(personId: string, status: AttendanceStatus): void {
    this.statuses.update((current) => ({ ...current, [personId]: status }));
  }

  protected markAllPresent(): void {
    this.statuses.update((current) => {
      const next = { ...current };
      for (const row of this.roster()) {
        next[row.person_id] = 'present';
      }
      return next;
    });
  }

  protected saveDay(): void {
    const rows = this.roster();
    if (rows.length === 0) {
      return;
    }
    this.saving.set(true);
    this.attendanceService
      .markDay({
        date: this.date(),
        records: rows.map((row) => ({ person_id: row.person_id, status: row.status })),
      })
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.dayAlreadyMarked.set(true);
          this.toast.show({
            severity: 'success',
            summary: 'Attendance saved',
            detail: `${rows.length} ${rows.length === 1 ? 'person' : 'people'} marked for ${this.date()}.`,
          });
        },
        error: () => this.saving.set(false),
      });
  }

  protected loadDay(): void {
    this.loading.set(true);
    forkJoin({
      people: this.personService.list(),
      departments: this.departmentService.list(),
      records: this.attendanceService.listForDate(this.date()),
    }).subscribe({
      next: ({ people, departments, records }) => {
        this.people.set(people);
        this.departments.set(departments);
        // Anything already recorded wins over the present-by-default; the
        // rest fall back in the roster computed.
        this.statuses.set(
          Object.fromEntries(records.map((record) => [record.person_id, record.status])),
        );
        this.dayAlreadyMarked.set(records.length > 0);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  protected loadSummary(): void {
    this.loading.set(true);
    this.attendanceService.summary(this.summaryStart(), this.summaryEnd()).subscribe({
      next: (summaries) => {
        this.summaries.set(summaries);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}

function firstOfThisMonth(): Date {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), 1);
}
