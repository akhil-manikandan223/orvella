import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { TenantAuthService } from './tenant-auth.service';

// No `redirectTo` query param here (unlike the platform-admin authGuard):
// there's only one route behind this guard right now (/dashboard), so it'd
// always resolve to the same place. Worth reintroducing once Phase 4 gives
// the tenant side more than one page to return to.
export const tenantAuthGuard: CanActivateFn = () => {
  const tenantAuthService = inject(TenantAuthService);
  const router = inject(Router);

  if (tenantAuthService.isAuthenticated()) {
    return true;
  }

  return router.createUrlTree(['/login']);
};
