import uuid

from pydantic import BaseModel, ConfigDict


class GroupCreate(BaseModel):
    name: str
    description: str | None = None
    department_id: uuid.UUID | None = None


class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    department_id: uuid.UUID | None = None


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: str | None
    department_id: uuid.UUID | None


class GroupDetailRead(GroupRead):
    member_ids: list[uuid.UUID]
    supervisor_ids: list[uuid.UUID]


class GroupMembersUpdate(BaseModel):
    """The full membership, not a delta - the UI edits a roster as a whole."""

    person_ids: list[uuid.UUID]


class GroupSupervisorsUpdate(BaseModel):
    tenant_user_ids: list[uuid.UUID]
