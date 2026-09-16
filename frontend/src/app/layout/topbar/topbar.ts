import { Component, computed, inject, output, viewChild } from '@angular/core';
import { NgOptimizedImage } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ButtonDirective } from 'primeng/button';
import { Avatar } from 'primeng/avatar';
import { Popover } from 'primeng/popover';

import { AuthService } from '../../core/auth/auth.service';
import { ThemeService } from '../../core/theme/theme.service';

@Component({
  selector: 'app-topbar',
  imports: [NgOptimizedImage, ButtonDirective, Avatar, Popover, RouterLink],
  templateUrl: './topbar.html',
  styleUrl: './topbar.scss',
})
export class Topbar {
  protected readonly authService = inject(AuthService);
  protected readonly themeService = inject(ThemeService);

  readonly menuToggle = output<void>();

  protected readonly accountPopoverRef = viewChild(Popover);

  protected readonly avatarLabel = computed(() => {
    const email = this.authService.admin()?.email;
    return email ? email[0].toUpperCase() : '?';
  });

  protected toggleAccountMenu(event: Event): void {
    this.accountPopoverRef()?.toggle(event);
  }

  protected closeAccountMenu(): void {
    this.accountPopoverRef()?.hide();
  }
}
