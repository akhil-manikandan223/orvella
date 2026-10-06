import { Component, OnDestroy, OnInit, computed, inject, signal, viewChild } from '@angular/core';
import { NgOptimizedImage } from '@angular/common';
import { RouterLink, RouterOutlet } from '@angular/router';
import { BrnPopover, BrnPopoverContent, BrnPopoverTrigger } from '@spartan-ng/brain/popover';

import { NotificationService } from '../../../core/notifications/notification.service';
import { TenantAuthService } from '../../../core/tenant-auth/tenant-auth.service';
import { NavGroup, SidebarNav } from '../../../layout/sidebar-nav/sidebar-nav';
import { HlmButton } from '../../../shared/ui/button';

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
    HlmButton,
    NgOptimizedImage,
    BrnPopover,
    BrnPopoverContent,
    BrnPopoverTrigger,
    SidebarNav,
  ],
  templateUrl: './tenant-shell.html',
  styleUrl: './tenant-shell.scss',
})
export class TenantShell implements OnInit, OnDestroy {
  protected readonly tenantAuthService = inject(TenantAuthService);
  protected readonly notificationService = inject(NotificationService);

  protected readonly navGroups = TENANT_NAV_GROUPS;
  protected readonly sidebarOpen = signal(false);

  // Named refs, not viewChild(BrnPopover): there are two popovers in this
  // topbar and an unnamed query would always return whichever comes first.
  private readonly accountPopoverRef = viewChild('accountPopover', { read: BrnPopover });

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

  protected closeAccountMenu(): void {
    this.accountPopoverRef()?.close();
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
