import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { NavGroup, SidebarNav } from '../sidebar-nav/sidebar-nav';
import { Topbar } from '../topbar/topbar';

const PLATFORM_ADMIN_NAV_GROUPS: NavGroup[] = [
  { label: 'Overview', items: [{ label: 'Dashboard', icon: 'pi pi-home', path: '/dashboard' }] },
  { label: 'Tenants', items: [{ label: 'Tenants', icon: 'pi pi-building', path: '/tenants' }] },
  {
    label: 'Organization Taxonomy',
    items: [
      { label: 'Categories', icon: 'pi pi-sitemap', path: '/organization-categories' },
      { label: 'Types', icon: 'pi pi-tags', path: '/organization-types' },
    ],
  },
  {
    label: 'Catalog',
    items: [{ label: 'Features', icon: 'pi pi-star', path: '/features' }],
  },
  {
    label: 'Geography',
    items: [
      { label: 'Countries', icon: 'pi pi-globe', path: '/geo/countries' },
      { label: 'States', icon: 'pi pi-map', path: '/geo/states' },
      { label: 'Districts', icon: 'pi pi-map-marker', path: '/geo/districts' },
      { label: 'Cities', icon: 'pi pi-building-columns', path: '/geo/cities' },
    ],
  },
  {
    label: 'Monitoring',
    items: [{ label: 'Audit Log', icon: 'pi pi-history', path: '/audit-logs' }],
  },
];

@Component({
  selector: 'app-shell',
  imports: [RouterOutlet, Topbar, SidebarNav],
  templateUrl: './shell.html',
  styleUrl: './shell.scss',
})
export class Shell {
  protected readonly navGroups = PLATFORM_ADMIN_NAV_GROUPS;
  protected readonly sidebarOpen = signal(false);

  protected toggleSidebar(): void {
    this.sidebarOpen.update((open) => !open);
  }

  protected closeSidebar(): void {
    this.sidebarOpen.set(false);
  }
}
