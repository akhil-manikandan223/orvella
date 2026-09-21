import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    title: str
    message: str
    read_at: datetime | None
    created_at: datetime


class UnreadCountRead(BaseModel):
    unread_count: int
