import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

from app.domains.feature.schemas import FeatureRead


class TenantCreate(BaseModel):
    name: str
    slug: str
    organization_type_id: uuid.UUID
    max_users: int | None = None

    address_line_1: str
    address_line_2: str | None = None
    country_id: uuid.UUID
    state_id: uuid.UUID | None = None
    city_id: uuid.UUID
    postal_code: str | None = None
    license_number: str
    logo_url: str | None = None
    key_contact_name: str
    key_contact_email: EmailStr
    key_contact_phone: str


class TenantUpdate(BaseModel):
    max_users: int | None = None
    is_active: bool | None = None

    address_line_1: str | None = None
    address_line_2: str | None = None
    country_id: uuid.UUID | None = None
    state_id: uuid.UUID | None = None
    city_id: uuid.UUID | None = None
    postal_code: str | None = None
    license_number: str | None = None
    logo_url: str | None = None
    key_contact_name: str | None = None
    key_contact_email: EmailStr | None = None
    key_contact_phone: str | None = None


class TenantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    organization_type_id: uuid.UUID
    max_users: int | None
    is_active: bool

    address_line_1: str
    address_line_2: str | None
    country_id: uuid.UUID
    state_id: uuid.UUID | None
    city_id: uuid.UUID
    postal_code: str | None
    license_number: str
    logo_url: str | None
    key_contact_name: str
    key_contact_email: str
    key_contact_phone: str


class TenantFeatureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    feature_id: uuid.UUID
    enabled: bool


class TenantDetailRead(TenantRead):
    features: list[FeatureRead]


class TenantFeatureToggleRequest(BaseModel):
    enabled: bool
