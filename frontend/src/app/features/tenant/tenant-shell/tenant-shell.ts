import { Component, OnDestroy, OnInit, computed, inject, signal, viewChild } from '@angular/core';
import { NgOptimizedImage } from '@angular/common';
import { RouterLink, RouterOutlet } from '@angular/router';
import { Avatar } from 'primeng/avatar';
import { ButtonDirective } from 'primeng/button';
import { OverlayBadge } from 'primeng/overlaybadge';
import { Popover } from 'primeng/popover';

import { NotificationService } from '../../../core/notifications/notification.service';
import { TenantAuthService } from '../../../core/tenant-auth/tenant-auth.service';
import { ThemeService } from '../../../core/theme/theme.service';
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
  imports: [
    RouterOutlet,
    RouterLink,
    Avatar,
    ButtonDirective,
    NgOptimizedImage,
    OverlayBadge,
    Popover,
    SidebarNav,
  ],
  templateUrl: './tenant-shell.html',
  styleUrl: './tenant-shell.scss',
})
export class TenantShell implements OnInit, OnDestroy {
  protected readonly tenantAuthService = inject(TenantAuthService);
  protected readonly notificationService = inject(NotificationService);
  // Drives the light/dark logo swap, same as the platform-admin topbar.
  protected readonly themeService = inject(ThemeService);

  protected readonly navGroups = TENANT_NAV_GROUPS;
  protected readonly sidebarOpen = signal(false);

  // Named refs, not viewChild(Popover): there are two popovers in this topbar
  // and an unnamed query would always return whichever comes first.
  private readonly notificationsPopoverRef = viewChild<Popover>('notificationsPopover');
  private readonly accountPopoverRef = viewChild<Popover>('accountPopover');

  protected readonly avatarLabel = computed(() => {
    const email = this.tenantAuthService.user()?.email;
    return email ? email[0].toUpperCase() : '?';
  });

  ngOnInit(): void {
    void this.notificationService.connect();
  }

  ngOnDestroy(): void {
    this.notificationService.disconnect();
  }

  protected toggleSidebar(): void {
    this.sidebarOpen.update((open) => !open);
  }

  protected closeSidebar(): void {
    this.sidebarOpen.set(false);
  }

  protected toggleNotifications(event: Event): void {
    this.notificationsPopoverRef()?.toggle(event);
  }

  protected toggleAccountMenu(event: Event): void {
    this.accountPopoverRef()?.toggle(event);
  }

  protected closeAccountMenu(): void {
    this.accountPopoverRef()?.hide();
  }

  protected markNotificationRead(id: string): void {
    void this.notificationService.markRead(id);
  }

  protected markAllNotificationsRead(): void {
    void this.notificationService.markAllRead();
  }

  protected logout(): void {
    this.tenantAuthService.logout();
  }
}
