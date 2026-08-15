import { Component, inject, output } from '@angular/core';
import { NgOptimizedImage } from '@angular/common';
import { ButtonDirective } from 'primeng/button';

import { AuthService } from '../../core/auth/auth.service';
import { ThemeService } from '../../core/theme/theme.service';
import { ThemeToggle } from '../theme-toggle/theme-toggle';

@Component({
  selector: 'app-topbar',
  imports: [NgOptimizedImage, ButtonDirective, ThemeToggle],
  templateUrl: './topbar.html',
  styleUrl: './topbar.scss',
})
export class Topbar {
  protected readonly authService = inject(AuthService);
  protected readonly themeService = inject(ThemeService);

  readonly menuToggle = output<void>();
}
