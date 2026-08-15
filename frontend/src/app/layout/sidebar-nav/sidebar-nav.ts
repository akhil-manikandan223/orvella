import { Component, output } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

interface NavItem {
  label: string;
  icon: string;
  path: string;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
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
  selector: 'app-sidebar-nav',
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './sidebar-nav.html',
  styleUrl: './sidebar-nav.scss',
})
export class SidebarNav {
  readonly navigated = output<void>();

  protected readonly groups = NAV_GROUPS;
}
