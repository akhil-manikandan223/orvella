import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class TenantLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TenantTokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class TenantUserCreate(BaseModel):
    email: EmailStr
    password: str


class TenantUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    is_active: bool


class TenantContextRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str


class TenantMeRead(BaseModel):
    user: TenantUserRead
    tenant: TenantContextRead
