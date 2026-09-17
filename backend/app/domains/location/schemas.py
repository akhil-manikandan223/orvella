import uuid

from pydantic import BaseModel, ConfigDict


class LocationCreate(BaseModel):
    name: str
    address: str | None = None


class LocationUpdate(BaseModel):
    name: str | None = None
    address: str | None = None


class LocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    address: str | None
