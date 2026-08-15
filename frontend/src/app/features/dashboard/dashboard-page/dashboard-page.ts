import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ButtonDirective } from 'primeng/button';

import { AuditLogService } from '../../../core/data-access/audit-log.service';
import { CityService } from '../../../core/data-access/city.service';
import { CountryService } from '../../../core/data-access/country.service';
import { DistrictService } from '../../../core/data-access/district.service';
import { FeatureService } from '../../../core/data-access/feature.service';
import { OrganizationCategoryService } from '../../../core/data-access/organization-category.service';
import { OrganizationTypeService } from '../../../core/data-access/organization-type.service';
import { StateService } from '../../../core/data-access/state.service';
import { TenantService } from '../../../core/data-access/tenant.service';
import { AuditLogRead } from '../../../core/models/audit-log.model';
import { EmptyState } from '../../../shared/empty-state/empty-state';

interface CalendarCell {
  day: number | null;
  isToday: boolean;
}

type ActivityKind = 'created' | 'updated' | 'deleted' | 'assigned' | 'removed';

interface ActivityEntry {
  entry: AuditLogRead;
  kind: ActivityKind;
  verb: string;
  detail: string;
}

interface EntityNameLookup {
  tenants: Map<string, string>;
  features: Map<string, string>;
  organizationTypes: Map<string, string>;
  organizationCategories: Map<string, string>;
  countries: Map<string, string>;
  states: Map<string, string>;
  districts: Map<string, string>;
  cities: Map<string, string>;
}

type UpdateDiff = { old: unknown; new: unknown };

function isUpdateDiff(value: unknown): value is UpdateDiff {
  return typeof value === 'object' && value !== null && 'new' in value;
}

function readChangedId(changes: Record<string, unknown>, key: string): string | null {
  const raw = changes[key];
  if (typeof raw === 'string') {
    return raw;
  }
  if (isUpdateDiff(raw) && typeof raw.new === 'string') {
    return raw.new;
  }
  return null;
}

const ENTITY_TYPE_LABELS: Record<string, string> = {
  tenants: 'tenant',
  features: 'feature',
  organization_types: 'organization type',
  organization_categories: 'organization category',
  countries: 'country',
  states: 'state',
  districts: 'district',
  cities: 'city',
};

function humanizeEntityType(entityType: string): string {
  return ENTITY_TYPE_LABELS[entityType] ?? entityType.replace(/_/g, ' ');
}

function resolveEntityName(
  entry: AuditLogRead,
  lookup: EntityNameLookup,
): string {
  const nameFromChanges = readChangedId(entry.changes, 'name');
  if (nameFromChanges) {
    return nameFromChanges;
  }

  const namesByEntityType: Record<string, Map<string, string>> = {
    tenants: lookup.tenants,
    features: lookup.features,
    organization_types: lookup.organizationTypes,
    organization_categories: lookup.organizationCategories,
    countries: lookup.countries,
    states: lookup.states,
    districts: lookup.districts,
    cities: lookup.cities,
  };
  const resolved = namesByEntityType[entry.entity_type]?.get(entry.entity_id);
  return resolved ?? `this ${humanizeEntityType(entry.entity_type)}`;
}

function describeActivity(entry: AuditLogRead, lookup: EntityNameLookup): ActivityEntry {
  if (entry.entity_type === 'tenant_features') {
    const featureId = readChangedId(entry.changes, 'feature_id');
    const tenantId = readChangedId(entry.changes, 'tenant_id');
    const featureName = (featureId && lookup.features.get(featureId)) || 'a feature';
    const tenantName = (tenantId && lookup.tenants.get(tenantId)) || 'a tenant';

    const enabledChange = entry.changes['enabled'];
    const wasRemoved = entry.action === 'delete' || (isUpdateDiff(enabledChange) && enabledChange.new === false);

    return wasRemoved
      ? { entry, kind: 'removed', verb: 'Removed', detail: `${featureName} from ${tenantName}` }
      : { entry, kind: 'assigned', verb: 'Assigned', detail: `${featureName} to ${tenantName}` };
  }

  const name = resolveEntityName(entry, lookup);
  if (entry.action === 'create') {
    return { entry, kind: 'created', verb: 'Created', detail: name };
  }
  if (entry.action === 'delete') {
    return { entry, kind: 'deleted', verb: 'Deleted', detail: name };
  }
  return { entry, kind: 'updated', verb: 'Updated', detail: name };
}

const WEEKDAY_LABELS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];
const MONTH_LABELS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

function buildCalendarWeeks(today: Date): CalendarCell[][] {
  const year = today.getFullYear();
  const month = today.getMonth();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstWeekday = new Date(year, month, 1).getDay();

  const cells: CalendarCell[] = [
    ...Array.from({ length: firstWeekday }, () => ({ day: null, isToday: false })),
    ...Array.from({ length: daysInMonth }, (_, i) => ({
      day: i + 1,
      isToday: i + 1 === today.getDate(),
    })),
  ];

  while (cells.length % 7 !== 0) {
    cells.push({ day: null, isToday: false });
  }

  const weeks: CalendarCell[][] = [];
  for (let i = 0; i < cells.length; i += 7) {
    weeks.push(cells.slice(i, i + 7));
  }
  return weeks;
}

@Component({
  selector: 'app-dashboard-page',
  imports: [EmptyState, DatePipe, RouterLink, ButtonDirective],
  templateUrl: './dashboard-page.html',
  styleUrl: './dashboard-page.scss',
})
export class DashboardPage {
  private readonly tenantService = inject(TenantService);
  private readonly organizationTypeService = inject(OrganizationTypeService);
  private readonly organizationCategoryService = inject(OrganizationCategoryService);
  private readonly featureService = inject(FeatureService);
  private readonly auditLogService = inject(AuditLogService);
  private readonly countryService = inject(CountryService);
  private readonly stateService = inject(StateService);
  private readonly districtService = inject(DistrictService);
  private readonly cityService = inject(CityService);

  protected readonly tenants = toSignal(this.tenantService.list(), { initialValue: [] });
  protected readonly organizationTypes = toSignal(this.organizationTypeService.list(), {
    initialValue: [],
  });
  protected readonly organizationCategories = toSignal(this.organizationCategoryService.list(), {
    initialValue: [],
  });
  protected readonly features = toSignal(this.featureService.list(), { initialValue: [] });
  protected readonly auditLogs = toSignal(this.auditLogService.list(), { initialValue: [] });
  private readonly countries = toSignal(this.countryService.list(), { initialValue: [] });
  private readonly states = toSignal(this.stateService.list(), { initialValue: [] });
  private readonly districts = toSignal(this.districtService.list(), { initialValue: [] });
  private readonly cities = toSignal(this.cityService.list(), { initialValue: [] });

  protected readonly activeTenantCount = computed(
    () => this.tenants().filter((tenant) => tenant.is_active).length,
  );
  protected readonly totalTenantCount = computed(() => this.tenants().length);
  protected readonly inactiveTenantCount = computed(
    () => this.totalTenantCount() - this.activeTenantCount(),
  );

  protected readonly organizationTypeCount = computed(() => this.organizationTypes().length);
  protected readonly organizationCategoryCount = computed(() => this.organizationCategories().length);

  protected readonly featureCount = computed(() => this.features().length);
  protected readonly deprecatedFeatureCount = computed(
    () => this.features().filter((feature) => feature.status === 'deprecated').length,
  );

  protected readonly auditEventsTodayCount = computed(() => {
    const today = new Date().toDateString();
    return this.auditLogs().filter((entry) => new Date(entry.created_at).toDateString() === today)
      .length;
  });

  private readonly entityNameLookup = computed<EntityNameLookup>(() => ({
    tenants: new Map(this.tenants().map((tenant) => [tenant.id, tenant.name])),
    features: new Map(this.features().map((feature) => [feature.id, feature.name])),
    organizationTypes: new Map(this.organizationTypes().map((type) => [type.id, type.name])),
    organizationCategories: new Map(
      this.organizationCategories().map((category) => [category.id, category.name]),
    ),
    countries: new Map(this.countries().map((country) => [country.id, country.name])),
    states: new Map(this.states().map((state) => [state.id, state.name])),
    districts: new Map(this.districts().map((district) => [district.id, district.name])),
    cities: new Map(this.cities().map((city) => [city.id, city.name])),
  }));

  protected readonly recentActivity = computed<ActivityEntry[]>(() => {
    const lookup = this.entityNameLookup();
    return this.auditLogs()
      .slice(0, 8)
      .map((entry) => describeActivity(entry, lookup));
  });

  protected readonly weekdayLabels = WEEKDAY_LABELS;
  protected readonly monthLabel: string;
  protected readonly calendarWeeks: CalendarCell[][];

  constructor() {
    const today = new Date();
    this.monthLabel = `${MONTH_LABELS[today.getMonth()]} ${today.getFullYear()}`;
    this.calendarWeeks = buildCalendarWeeks(today);
  }
}
