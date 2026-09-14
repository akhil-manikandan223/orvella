import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { FormField, form, required } from '@angular/forms/signals';
import { ButtonDirective } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { InputPassword } from 'primeng/inputpassword';
import { IconField } from 'primeng/iconfield';
import { InputIcon } from 'primeng/inputicon';

import { TenantAuthService } from '../../../core/tenant-auth/tenant-auth.service';

interface LoginFormValue {
  email: string;
  password: string;
}

function titleCaseFromSlug(hostname: string): string {
  const label = hostname.split('.')[0] ?? '';
  return label
    .split('-')
    .filter(Boolean)
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(' ');
}

@Component({
  selector: 'app-tenant-login-page',
  imports: [ButtonDirective, InputText, InputPassword, IconField, InputIcon, FormField],
  templateUrl: './tenant-login-page.html',
  styleUrl: './tenant-login-page.scss',
})
export class TenantLoginPage {
  private readonly tenantAuthService = inject(TenantAuthService);
  private readonly router = inject(Router);

  protected readonly submitting = signal(false);

  // Best-effort greeting derived purely from the subdomain, for display
  // only - the actual tenant name/identity is resolved and enforced
  // server-side on every request, never trusted from this.
  protected readonly tenantGreeting = titleCaseFromSlug(window.location.hostname) || 'your organization';

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
      await this.tenantAuthService.login(email, password);
      await this.router.navigateByUrl('/dashboard');
    } finally {
      this.submitting.set(false);
    }
  }
}
