import { Component, computed, inject } from '@angular/core';
import { BrnSonnerToaster } from '@spartan-ng/brain/sonner';

import { ThemeService } from '../theme/theme.service';

/** Mounted once in the app root; ToastService pushes into it. Follows the app theme. */
@Component({
  selector: 'app-toaster',
  imports: [BrnSonnerToaster],
  template: `
    <brn-sonner-toaster
      position="top-right"
      [theme]="theme()"
      [closeButton]="true"
      [richColors]="true"
      offset="72px"
      [style]="toasterStyle"
    />
  `,
})
export class Toaster {
  private readonly themeService = inject(ThemeService);

  protected readonly theme = computed(() =>
    this.themeService.mode() === 'dark' ? 'dark' : 'light',
  );

  /** Sonner reads these custom properties; pointing them at the tokens keeps toasts on-brand. */
  protected readonly toasterStyle = {
    '--font-family': 'var(--orv-font-sans)',
    '--border-radius': '10px',
    '--normal-bg': 'var(--popover)',
    '--normal-border': 'var(--border)',
    '--normal-text': 'var(--popover-foreground)',
    '--success-bg': 'var(--success-surface)',
    '--success-border': 'var(--success-surface)',
    '--success-text': 'var(--success)',
    '--error-bg': 'var(--danger-surface)',
    '--error-border': 'var(--danger-surface)',
    '--error-text': 'var(--danger)',
    '--warning-bg': 'var(--warning-surface)',
    '--warning-border': 'var(--warning-surface)',
    '--warning-text': 'var(--warning)',
    '--info-bg': 'var(--info-surface)',
    '--info-border': 'var(--info-surface)',
    '--info-text': 'var(--info)',
  };
}
