import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormField, form, required } from '@angular/forms/signals';

import { AuthService } from '../../../core/auth/auth.service';
import { HlmButton } from '../../../shared/ui/button';

interface LoginFormValue {
  email: string;
  password: string;
}

/** The panel's 3x3 mosaic, as primary scale steps (see .login__tile--*). */
const TILES = ['600', '500', '800', '800', 'white', '600', '500', '800', '400'];

@Component({
  selector: 'app-login-page',
  imports: [HlmButton, FormField],
  templateUrl: './login-page.html',
  styleUrl: './login-page.scss',
})
export class LoginPage {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  protected readonly submitting = signal(false);
  protected readonly showPassword = signal(false);
  protected readonly tiles = TILES;

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
