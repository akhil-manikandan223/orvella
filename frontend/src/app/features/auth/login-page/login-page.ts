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
