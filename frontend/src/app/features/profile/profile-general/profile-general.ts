import { Component, inject } from '@angular/core';

import { AuthService } from '../../../core/auth/auth.service';

@Component({
  selector: 'app-profile-general',
  templateUrl: './profile-general.html',
  styleUrl: './profile-general.scss',
})
export class ProfileGeneral {
  protected readonly authService = inject(AuthService);
}
