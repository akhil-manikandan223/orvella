import { Component, inject, signal } from '@angular/core';
import { NgOptimizedImage } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { ButtonDirective } from 'primeng/button';

import { TenantAuthService } from '../../../core/tenant-auth/tenant-auth.service';
import { NavGroup, SidebarNav } from '../../../layout/sidebar-nav/sidebar-nav';

const TENANT_NAV_GROUPS: NavGroup[] = [
  { label: 'Overview', items: [{ label: 'Dashboard', icon: 'pi pi-home', path: '/dashboard' }] },
  {
    label: 'Organization',
    items: [
      { label: 'People', icon: 'pi pi-users', path: '/people' },
      { label: 'Departments', icon: 'pi pi-sitemap', path: '/departments' },
      { label: 'Locations', icon: 'pi pi-map-marker', path: '/locations' },
    ],
  },
];

@Component({
  selector: 'app-tenant-shell',
  imports: [RouterOutlet, ButtonDirective, NgOptimizedImage, SidebarNav],
  templateUrl: './tenant-shell.html',
  styleUrl: './tenant-shell.scss',
})
export class TenantShell {
  protected readonly tenantAuthService = inject(TenantAuthService);

  protected readonly navGroups = TENANT_NAV_GROUPS;
  protected readonly sidebarOpen = signal(false);

  protected toggleSidebar(): void {
    this.sidebarOpen.update((open) => !open);
  }

  protected closeSidebar(): void {
    this.sidebarOpen.set(false);
  }

  protected logout(): void {
    this.tenantAuthService.logout();
  }
}
