import { Component, inject } from '@angular/core';
import { ButtonDirective } from 'primeng/button';

import { ThemeService } from '../../core/theme/theme.service';

@Component({
  selector: 'app-theme-toggle',
  imports: [ButtonDirective],
  templateUrl: './theme-toggle.html',
  styleUrl: './theme-toggle.scss',
})
export class ThemeToggle {
  protected readonly themeService = inject(ThemeService);
}
