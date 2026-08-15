import { Routes } from '@angular/router';

import { authGuard } from './core/auth/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login-page/login-page').then((m) => m.LoginPage),
  },
  {
    path: '',
    loadComponent: () => import('./layout/shell/shell').then((m) => m.Shell),
    canActivate: [authGuard],
    canActivateChild: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./features/dashboard/dashboard-page/dashboard-page').then(
            (m) => m.DashboardPage,
          ),
      },
      {
        path: 'tenants',
        loadComponent: () =>
          import('./features/tenants/tenant-list/tenant-list').then((m) => m.TenantList),
      },
      {
        path: 'tenants/new',
        loadComponent: () =>
          import('./features/tenants/tenant-create/tenant-create').then((m) => m.TenantCreate),
      },
      {
        path: 'tenants/:id',
        loadComponent: () =>
          import('./features/tenants/tenant-detail/tenant-detail').then((m) => m.TenantDetail),
      },
      {
        path: 'geo/countries',
        loadComponent: () =>
          import('./features/geo/countries/country-list/country-list').then(
            (m) => m.CountryList,
          ),
      },
      {
        path: 'geo/states',
        loadComponent: () =>
          import('./features/geo/states/state-list/state-list').then((m) => m.StateList),
      },
      {
        path: 'geo/districts',
        loadComponent: () =>
          import('./features/geo/districts/district-list/district-list').then(
            (m) => m.DistrictList,
          ),
      },
      {
        path: 'geo/cities',
        loadComponent: () =>
          import('./features/geo/cities/city-list/city-list').then((m) => m.CityList),
      },
      {
        path: 'features',
        loadComponent: () =>
          import('./features/feature-catalog/feature-list/feature-list').then(
            (m) => m.FeatureList,
          ),
      },
      {
        path: 'organization-categories',
        loadComponent: () =>
          import('./features/organization-taxonomy/category-list/category-list').then(
            (m) => m.CategoryList,
          ),
      },
      {
        path: 'organization-types',
        loadComponent: () =>
          import('./features/organization-taxonomy/type-list/type-list').then((m) => m.TypeList),
      },
      {
        path: 'organization-types/:id/template',
        loadComponent: () =>
          import(
            './features/organization-taxonomy/type-feature-template/type-feature-template'
          ).then((m) => m.TypeFeatureTemplate),
      },
      {
        path: 'audit-logs',
        loadComponent: () =>
          import('./features/audit-log/audit-log-list/audit-log-list').then(
            (m) => m.AuditLogList,
          ),
      },
    ],
  },
  { path: '**', redirectTo: 'dashboard' },
];
