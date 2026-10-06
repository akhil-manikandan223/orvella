import { Component, input } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { PageHeader } from '../../../shared/page-header/page-header';
import { ProfileNavItem } from './profile-nav';

@Component({
  selector: 'app-profile-page',
  imports: [PageHeader, RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './profile-page.html',
  styleUrl: './profile-page.scss',
})
export class ProfilePage {
  /** Bound from the route's `data` via withComponentInputBinding(); the tenant
   * shell passes a shorter list, since a TenantUser has no General tab worth
   * showing.
   *
   * Every route that loads this MUST supply `data.navItems`. A default here
   * would not survive: with component input binding the router walks the
   * component's inputs (not the route's data keys) and, under the default
   * `unmatchedInputBehavior: 'alwaysUndefined'`, actively sets any input the
   * route doesn't provide to undefined - which silently emptied this nav. */
  readonly navItems = input<ProfileNavItem[]>([]);
}
