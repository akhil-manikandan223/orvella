import { Component, inject, signal } from '@angular/core';
import { FormField, form, required } from '@angular/forms/signals';
import { InputPassword } from 'primeng/inputpassword';
import { IconField } from 'primeng/iconfield';
import { InputIcon } from 'primeng/inputicon';
import { ButtonDirective } from 'primeng/button';
import { MessageService } from 'primeng/api';

import { PASSWORD_CHANGER } from '../../../core/auth/password-changer';

interface ChangePasswordFormValue {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

@Component({
  selector: 'app-profile-security',
  imports: [InputPassword, IconField, InputIcon, ButtonDirective, FormField],
  templateUrl: './profile-security.html',
  styleUrl: './profile-security.scss',
})
export class ProfileSecurity {
  // Whose password this changes depends on which route loaded the screen -
  // see PASSWORD_CHANGER.
  private readonly passwordChanger = inject(PASSWORD_CHANGER);
  private readonly messageService = inject(MessageService);

  protected readonly submitting = signal(false);
  // Suppresses "required" messages on the fields this clears right after a
  // successful change - signal-forms has no "mark as untouched" API, so
  // without this the emptied-but-still-touched fields would immediately
  // show validation errors right after a successful submission.
  protected readonly justSucceeded = signal(false);

  protected readonly model = signal<ChangePasswordFormValue>({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  protected readonly passwordForm = form(this.model, (path) => {
    required(path.current_password, { message: 'Current password is required' });
    required(path.new_password, { message: 'New password is required' });
    required(path.confirm_password, { message: 'Please confirm your new password' });
  });

  protected async onSubmit(event: Event): Promise<void> {
    event.preventDefault();
    this.justSucceeded.set(false);

    if (this.passwordForm().invalid()) {
      this.passwordForm().markAsTouched();
      return;
    }

    const { current_password, new_password, confirm_password } = this.model();
    if (new_password !== confirm_password) {
      this.messageService.add({
        severity: 'error',
        summary: 'Passwords do not match',
        detail: 'New password and confirmation must be the same.',
      });
      return;
    }

    this.submitting.set(true);
    try {
      await this.passwordChanger.changePassword(current_password, new_password);
      this.messageService.add({
        severity: 'success',
        summary: 'Password changed',
        detail: 'Your password has been updated.',
      });
      this.model.set({ current_password: '', new_password: '', confirm_password: '' });
      this.justSucceeded.set(true);
    } finally {
      this.submitting.set(false);
    }
  }
}
