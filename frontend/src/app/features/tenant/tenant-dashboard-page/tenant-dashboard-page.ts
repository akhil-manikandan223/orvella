import { Component, inject } from '@angular/core';

import { TenantAuthService } from '../../../core/tenant-auth/tenant-auth.service';

@Component({
  selector: 'app-tenant-dashboard-page',
  imports: [],
  templateUrl: './tenant-dashboard-page.html',
  styleUrl: './tenant-dashboard-page.scss',
})
export class TenantDashboardPage {
  protected readonly tenantAuthService = inject(TenantAuthService);
}
