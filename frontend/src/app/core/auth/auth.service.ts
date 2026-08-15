import { Service, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { environment } from '../../../environments/environment';
import { LoginRequest, PlatformAdminRead, TokenResponse } from '../models/platform-admin.model';

const SESSION_STORAGE_KEY = 'orvella.session';

interface StoredSession {
  token: string;
  admin: PlatformAdminRead;
}

@Service()
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  private readonly _token = signal<string | null>(null);
  private readonly _admin = signal<PlatformAdminRead | null>(null);

  readonly token = this._token.asReadonly();
  readonly admin = this._admin.asReadonly();
  readonly isAuthenticated = computed(() => this._token() !== null);

  constructor() {
    this.restoreSession();
  }

  async login(email: string, password: string): Promise<void> {
    const body: LoginRequest = { email, password };
    const tokenResponse = await firstValueFrom(
      this.http.post<TokenResponse>(`${environment.apiUrl}/auth/login`, body),
    );
    this._token.set(tokenResponse.access_token);

    const admin = await firstValueFrom(
      this.http.get<PlatformAdminRead>(`${environment.apiUrl}/auth/me`),
    );
    this._admin.set(admin);
    this.persistSession();
  }

  logout(): void {
    this._token.set(null);
    this._admin.set(null);
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
    this.router.navigateByUrl('/login');
  }

  private restoreSession(): void {
    const raw = sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) {
      return;
    }
    try {
      const stored = JSON.parse(raw) as StoredSession;
      this._token.set(stored.token);
      this._admin.set(stored.admin);
    } catch {
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
    }
  }

  private persistSession(): void {
    const token = this._token();
    const admin = this._admin();
    if (!token || !admin) {
      return;
    }
    const stored: StoredSession = { token, admin };
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(stored));
  }
}
