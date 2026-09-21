import uuid

from fastapi import WebSocket


class NotificationConnectionManager:
    """Tracks live notification WebSocket connections, keyed by tenant_user_id.

    In-memory and per-process: fine for a single backend instance, but a
    notification created on process A will never reach a socket held open on
    process B. Once the app actually runs multiple backend replicas, this
    needs a shared pub/sub (e.g. Redis) behind the same interface - noted
    here rather than solved now, since nothing in this deployment runs more
    than one instance yet.
    """

    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, set[WebSocket]] = {}

    def connect(self, tenant_user_id: uuid.UUID, websocket: WebSocket) -> None:
        self._connections.setdefault(tenant_user_id, set()).add(websocket)

    def disconnect(self, tenant_user_id: uuid.UUID, websocket: WebSocket) -> None:
        sockets = self._connections.get(tenant_user_id)
        if sockets is None:
            return
        sockets.discard(websocket)
        if not sockets:
            del self._connections[tenant_user_id]

    async def send_to_user(self, tenant_user_id: uuid.UUID, payload: dict) -> None:
        sockets = self._connections.get(tenant_user_id)
        if not sockets:
            return
        for websocket in list(sockets):
            try:
                await websocket.send_json(payload)
            except Exception:  # noqa: BLE001 - a dead/broken socket must not break the others
                self.disconnect(tenant_user_id, websocket)


notification_connections = NotificationConnectionManager()
