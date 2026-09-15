import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { PageHeader } from '../../../shared/page-header/page-header';

interface ProfileNavItem {
  label: string;
  icon: string;
  path: string;
}

const NAV_ITEMS: ProfileNavItem[] = [
  { label: 'General', icon: 'pi pi-user', path: 'general' },
  { label: 'Appearance', icon: 'pi pi-palette', path: 'appearance' },
  { label: 'Privacy & Security', icon: 'pi pi-lock', path: 'security' },
];

@Component({
  selector: 'app-profile-page',
  imports: [PageHeader, RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './profile-page.html',
  styleUrl: './profile-page.scss',
})
export class ProfilePage {
  protected readonly navItems = NAV_ITEMS;
}
