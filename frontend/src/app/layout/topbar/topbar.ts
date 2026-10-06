import { Component, computed, inject, output, viewChild } from '@angular/core';
import { NgOptimizedImage } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BrnPopover, BrnPopoverContent, BrnPopoverTrigger } from '@spartan-ng/brain/popover';

import { AuthService } from '../../core/auth/auth.service';

/** Platform-admin topbar. Styles: shared/styles/_app-topbar.scss (shared with TenantShell). */
@Component({
  selector: 'app-topbar',
  imports: [NgOptimizedImage, BrnPopover, BrnPopoverContent, BrnPopoverTrigger, RouterLink],
  templateUrl: './topbar.html',
})
export class Topbar {
  protected readonly authService = inject(AuthService);

  readonly menuToggle = output<void>();

  private readonly accountPopoverRef = viewChild(BrnPopover);

  protected readonly avatarLabel = computed(() => {
    const email = this.authService.admin()?.email;
    return email ? email[0].toUpperCase() : '?';
  });

  protected closeAccountMenu(): void {
    this.accountPopoverRef()?.close();
  }
}
