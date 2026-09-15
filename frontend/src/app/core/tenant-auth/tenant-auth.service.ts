import { Service, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  TenantContextRead,
  TenantLoginContextRead,
  TenantLoginRequest,
  TenantMeRead,
  TenantTokenResponse,
  TenantUserRead,
} from '../models/tenant-user.model';

// Deliberately a different key from AuthService's 'orvella.session' - the
// two must never collide if a platform admin and a tenant user are ever
// signed in within the same browser (e.g. two tabs, one per subdomain).
const SESSION_STORAGE_KEY = 'orvella.tenant-session';

interface StoredTenantSession {
  token: string;
  user: TenantUserRead;
  tenant: TenantContextRead;
}

@Service()
export class TenantAuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  private readonly _token = signal<string | null>(null);
  private readonly _user = signal<TenantUserRead | null>(null);
  private readonly _tenant = signal<TenantContextRead | null>(null);

  readonly token = this._token.asReadonly();
  readonly user = this._user.asReadonly();
  readonly tenant = this._tenant.asReadonly();
  readonly isAuthenticated = computed(() => this._token() !== null);

  constructor() {
    this.restoreSession();
  }

  /** Public (no auth) - used by the tenant login page to render its hero tiles. */
  getLoginContext(): Promise<TenantLoginContextRead> {
    return firstValueFrom(
      this.http.get<TenantLoginContextRead>(`${environment.apiUrl}/tenant/auth/context`),
    );
  }

  async login(email: string, password: string): Promise<void> {
    const body: TenantLoginRequest = { email, password };
    const tokenResponse = await firstValueFrom(
      this.http.post<TenantTokenResponse>(`${environment.apiUrl}/tenant/auth/login`, body),
    );
    this._token.set(tokenResponse.access_token);

    const me = await firstValueFrom(
      this.http.get<TenantMeRead>(`${environment.apiUrl}/tenant/auth/me`),
    );
    this._user.set(me.user);
    this._tenant.set(me.tenant);
    this.persistSession();
  }

  logout(): void {
    this._token.set(null);
    this._user.set(null);
    this._tenant.set(null);
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
    this.router.navigateByUrl('/login');
  }

  private restoreSession(): void {
    const raw = sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) {
      return;
    }
    try {
      const stored = JSON.parse(raw) as StoredTenantSession;
      this._token.set(stored.token);
      this._user.set(stored.user);
      this._tenant.set(stored.tenant);
    } catch {
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
    }
  }

  private persistSession(): void {
    const token = this._token();
    const user = this._user();
    const tenant = this._tenant();
    if (!token || !user || !tenant) {
      return;
    }
    const stored: StoredTenantSession = { token, user, tenant };
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(stored));
  }
}
