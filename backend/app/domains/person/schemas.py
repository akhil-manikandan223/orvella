import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class PersonCreate(BaseModel):
    first_name: str
    last_name: str
    category: str
    email: EmailStr | None = None
    phone: str | None = None
    department_id: uuid.UUID | None = None
    location_id: uuid.UUID | None = None


class PersonUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    category: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    department_id: uuid.UUID | None = None
    location_id: uuid.UUID | None = None


class PersonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    category: str
    department_id: uuid.UUID | None
    location_id: uuid.UUID | None
    tenant_user_id: uuid.UUID | None
