import { Service, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import { environment } from '../../../environments/environment';
import { NotificationRead, UnreadCountRead } from '../models/notification.model';
import { TenantAuthService } from '../tenant-auth/tenant-auth.service';

const BASE_URL = `${environment.apiUrl}/tenant/notifications`;
const RECONNECT_DELAY_MS = 3000;

/**
 * Owns the tenant user's notification inbox: an initial REST fetch plus a
 * live WebSocket connection that pushes newly created notifications as they
 * happen. A single instance is shared app-wide (providedIn: 'root' via
 * @Service) and is connected/disconnected by TenantShell, which mirrors the
 * authenticated session's own lifetime.
 */
@Service()
export class NotificationService {
  private readonly http = inject(HttpClient);
  private readonly tenantAuthService = inject(TenantAuthService);

  private readonly _notifications = signal<NotificationRead[]>([]);
  private readonly _unreadCount = signal(0);
  readonly notifications = this._notifications.asReadonly();
  readonly unreadCount = this._unreadCount.asReadonly();

  private socket: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private intentionalClose = false;

  async connect(): Promise<void> {
    await Promise.all([this.loadNotifications(), this.loadUnreadCount()]);
    if (
      this.socket &&
      (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }
    this.openSocket();
  }

  disconnect(): void {
    this.intentionalClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.socket?.close();
    this.socket = null;
    this._notifications.set([]);
    this._unreadCount.set(0);
  }

  async markRead(id: string): Promise<void> {
    const updated = await firstValueFrom(
      this.http.post<NotificationRead>(`${BASE_URL}/${id}/read`, {}),
    );
    this._notifications.update((list) => list.map((n) => (n.id === id ? updated : n)));
    await this.loadUnreadCount();
  }

  async markAllRead(): Promise<void> {
    await firstValueFrom(this.http.post<void>(`${BASE_URL}/read-all`, {}));
    const now = new Date().toISOString();
    this._notifications.update((list) =>
      list.map((n) => (n.read_at ? n : { ...n, read_at: now })),
    );
    this._unreadCount.set(0);
  }

  private async loadNotifications(): Promise<void> {
    try {
      const notifications = await firstValueFrom(this.http.get<NotificationRead[]>(BASE_URL));
      this._notifications.set(notifications);
    } catch {
      // Best-effort - the bell just stays at whatever it last had.
    }
  }

  private async loadUnreadCount(): Promise<void> {
    try {
      const response = await firstValueFrom(
        this.http.get<UnreadCountRead>(`${BASE_URL}/unread-count`),
      );
      this._unreadCount.set(response.unread_count);
    } catch {
      // Best-effort.
    }
  }

  /**
   * The token travels as a query param, not an Authorization header - the
   * browser's WebSocket constructor can't set custom headers on the
   * handshake request.
   */
  private openSocket(): void {
    const token = this.tenantAuthService.token();
    if (!token) {
      return;
    }
    this.intentionalClose = false;

    const url = new URL(`${environment.apiUrl}/tenant/notifications/ws`, window.location.href);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    url.searchParams.set('token', token);

    const socket = new WebSocket(url.toString());
    this.socket = socket;

    socket.onmessage = (event: MessageEvent<string>) => {
      try {
        const payload = JSON.parse(event.data) as { event: string; data: NotificationRead };
        if (payload.event === 'notification') {
          this._notifications.update((list) => [payload.data, ...list]);
          this._unreadCount.update((count) => count + 1);
        }
      } catch {
        // Ignore malformed frames.
      }
    };

    socket.onclose = () => {
      if (this.socket !== socket || this.intentionalClose) {
        return;
      }
      this.scheduleReconnect();
    };

    socket.onerror = () => socket.close();
  }

  /**
   * A closed socket could mean the access token expired mid-connection (it's
   * only checked once, at the handshake) - refresh() gets a live token
   * before the next attempt rather than retrying the one that just failed.
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return;
    }
    this.reconnectTimer = setTimeout(async () => {
      this.reconnectTimer = null;
      if (this.intentionalClose) {
        return;
      }
      await this.tenantAuthService.refresh();
      this.openSocket();
    }, RECONNECT_DELAY_MS);
  }
}
