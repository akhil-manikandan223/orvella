import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { FormField, form, required } from '@angular/forms/signals';

import { BrandService } from '../../../core/branding/brand.service';
import { TenantAuthService } from '../../../core/tenant-auth/tenant-auth.service';
import { HeroFeatureRead } from '../../../core/models/tenant-user.model';
import { HlmButton } from '../../../shared/ui/button';

interface LoginFormValue {
  email: string;
  password: string;
}

interface HeroTile {
  index: string;
  icon: string;
  title: string;
  category: string | null;
}

// Feature rows have no icon of their own (they're admin-defined, open-ended
// capabilities, not a fixed catalog) - this is purely a rotating set of
// icons for visual variety on the hero tiles, not tied to feature meaning.
const HERO_ICONS = [
  'pi-star',
  'pi-bolt',
  'pi-shield',
  'pi-compass',
  'pi-heart',
  'pi-gem',
  'pi-gauge',
  'pi-flag',
];

function titleCaseFromSlug(hostname: string): string {
  const label = hostname.split('.')[0] ?? '';
  return label
    .split('-')
    .filter(Boolean)
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(' ');
}

function toHeroTiles(features: HeroFeatureRead[]): HeroTile[] {
  return features.map((feature, i) => ({
    index: String(i + 1).padStart(2, '0'),
    icon: `pi ${HERO_ICONS[i % HERO_ICONS.length]}`,
    title: feature.name,
    category: feature.description,
  }));
}

@Component({
  selector: 'app-tenant-login-page',
  imports: [HlmButton, FormField],
  templateUrl: './tenant-login-page.html',
  styleUrl: './tenant-login-page.scss',
})
export class TenantLoginPage implements OnInit {
  private readonly tenantAuthService = inject(TenantAuthService);
  private readonly brandService = inject(BrandService);
  private readonly router = inject(Router);

  protected readonly submitting = signal(false);

  protected readonly showPassword = signal(false);

  /** The tenant's own logo in the corner when they have one; otherwise their
   * initial and name, with "Powered by Orvella" below as attribution. */
  protected readonly logoUrl = this.brandService.logoUrl;

  // Best-effort greeting derived purely from the subdomain, shown until the
  // real tenant name loads - the actual tenant identity is resolved and
  // enforced server-side on every request, never trusted from this.
  protected readonly tenantGreeting = signal(
    titleCaseFromSlug(window.location.hostname) || 'your organization',
  );
  protected readonly tenantInitial = computed(
    () => this.tenantGreeting().trim().charAt(0).toUpperCase() || 'O',
  );
  protected readonly heroTiles = signal<HeroTile[]>([]);

  protected readonly model = signal<LoginFormValue>({ email: '', password: '' });
  protected readonly loginForm = form(this.model, (path) => {
    required(path.email, { message: 'Email is required' });
    required(path.password, { message: 'Password is required' });
  });

  async ngOnInit(): Promise<void> {
    try {
      const context = await this.tenantAuthService.getLoginContext();
      this.tenantGreeting.set(context.tenant.name);
      this.heroTiles.set(toHeroTiles(context.hero_features));
      // Branding has to come from this public endpoint - the login page is
      // reached before there's any session to read it from.
      this.brandService.apply(context.tenant);
    } catch {
      // Login still works without this - the feature list is decorative,
      // and the subdomain-derived greeting above already covers this case.
    }
  }

  protected async onSubmit(event: Event): Promise<void> {
    event.preventDefault();
    if (this.loginForm().invalid()) {
      this.loginForm().markAsTouched();
      return;
    }

    this.submitting.set(true);
    try {
      const { email, password } = this.model();
      await this.tenantAuthService.login(email, password);
      await this.router.navigateByUrl('/dashboard');
    } finally {
      this.submitting.set(false);
    }
  }
}
