import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormField, form, required } from '@angular/forms/signals';
import { ButtonDirective } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { InputPassword } from 'primeng/inputpassword';
import { IconField } from 'primeng/iconfield';
import { InputIcon } from 'primeng/inputicon';

import { AuthService } from '../../../core/auth/auth.service';

interface LoginFormValue {
  email: string;
  password: string;
}

interface ModuleTile {
  index: string;
  icon: string;
  title: string;
  category: string;
}

const MODULES: ModuleTile[] = [
  { index: '01', icon: 'pi pi-building', title: 'Tenants', category: 'Organizations' },
  { index: '02', icon: 'pi pi-tags', title: 'Organization Types', category: 'Taxonomy' },
  { index: '03', icon: 'pi pi-sitemap', title: 'Categories', category: 'Classification' },
  { index: '04', icon: 'pi pi-star', title: 'Features', category: 'Capabilities' },
  { index: '05', icon: 'pi pi-globe', title: 'Countries', category: 'Geography' },
  { index: '06', icon: 'pi pi-map', title: 'States', category: 'Geography' },
  { index: '07', icon: 'pi pi-map-marker', title: 'Districts', category: 'Geography' },
  { index: '08', icon: 'pi pi-building-columns', title: 'Cities', category: 'Geography' },
  { index: '09', icon: 'pi pi-history', title: 'Audit Log', category: 'Compliance' },
  { index: '10', icon: 'pi pi-chart-bar', title: 'Dashboard', category: 'Overview' },
];

@Component({
  selector: 'app-login-page',
  imports: [ButtonDirective, InputText, InputPassword, IconField, InputIcon, FormField],
  templateUrl: './login-page.html',
  styleUrl: './login-page.scss',
})
export class LoginPage {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  protected readonly submitting = signal(false);
  protected readonly modules = MODULES;
  protected readonly currentYear = new Date().getFullYear();

  protected readonly model = signal<LoginFormValue>({ email: '', password: '' });
  protected readonly loginForm = form(this.model, (path) => {
    required(path.email, { message: 'Email is required' });
    required(path.password, { message: 'Password is required' });
  });

  protected async onSubmit(event: Event): Promise<void> {
    event.preventDefault();
    if (this.loginForm().invalid()) {
      this.loginForm().markAsTouched();
      return;
    }

    this.submitting.set(true);
    try {
      const { email, password } = this.model();
      await this.authService.login(email, password);
      const redirectTo = this.route.snapshot.queryParamMap.get('redirectTo');
      await this.router.navigateByUrl(redirectTo || '/dashboard');
    } finally {
      this.submitting.set(false);
    }
  }
}
