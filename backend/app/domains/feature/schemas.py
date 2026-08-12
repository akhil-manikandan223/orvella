import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict


class FeatureCreate(BaseModel):
    key: str
    name: str
    description: str | None = None
    status: Literal['active', 'deprecated'] = 'active'


class FeatureUpdate(BaseModel):
    # key deliberately excluded - it's the stable machine-readable identifier,
    # not meant to be renamed via a casual update.
    name: str | None = None
    description: str | None = None
    status: Literal['active', 'deprecated'] | None = None


class FeatureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    name: str
    description: str | None
    status: str
