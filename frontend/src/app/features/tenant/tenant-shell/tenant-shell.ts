import { Component, inject } from '@angular/core';
import { NgOptimizedImage } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { ButtonDirective } from 'primeng/button';

import { TenantAuthService } from '../../../core/tenant-auth/tenant-auth.service';

@Component({
  selector: 'app-tenant-shell',
  imports: [RouterOutlet, ButtonDirective, NgOptimizedImage],
  templateUrl: './tenant-shell.html',
  styleUrl: './tenant-shell.scss',
})
export class TenantShell {
  protected readonly tenantAuthService = inject(TenantAuthService);

  protected logout(): void {
    this.tenantAuthService.logout();
  }
}
