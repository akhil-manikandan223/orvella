// Kept apart from profile-page.ts so app.routes.ts can import the nav data
// without statically pulling the ProfilePage component (and its whole import
// graph) into the initial bundle - the route itself lazy-loads the component.

export interface ProfileNavItem {
  label: string;
  icon: string;
  path: string;
}

export const PLATFORM_ADMIN_PROFILE_NAV_ITEMS: ProfileNavItem[] = [
  { label: 'General', icon: 'pi pi-user', path: 'general' },
  { label: 'Appearance', icon: 'pi pi-palette', path: 'appearance' },
  { label: 'Privacy & Security', icon: 'pi pi-lock', path: 'security' },
];
