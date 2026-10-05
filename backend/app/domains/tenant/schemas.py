import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domains.feature.schemas import FeatureRead

LoginHeroMode = Literal['default', 'featured']

# Validated on the way in so a malformed value can never reach the frontend,
# where it would be fed straight into a generated colour palette.
BrandColor = Annotated[str, Field(pattern=r'^#[0-9a-fA-F]{6}$')]


class TenantCreate(BaseModel):
    name: str
    slug: str
    organization_type_id: uuid.UUID
    max_users: int | None = None
    login_hero_mode: LoginHeroMode = 'default'

    address_line_1: str
    address_line_2: str | None = None
    country_id: uuid.UUID
    state_id: uuid.UUID | None = None
    city_id: uuid.UUID
    postal_code: str | None = None
    license_number: str
    logo_url: str | None = None
    brand_color: BrandColor | None = None
    key_contact_name: str
    key_contact_email: EmailStr
    key_contact_phone: str


class TenantUpdate(BaseModel):
    max_users: int | None = None
    is_active: bool | None = None
    login_hero_mode: LoginHeroMode | None = None

    address_line_1: str | None = None
    address_line_2: str | None = None
    country_id: uuid.UUID | None = None
    state_id: uuid.UUID | None = None
    city_id: uuid.UUID | None = None
    postal_code: str | None = None
    license_number: str | None = None
    logo_url: str | None = None
    brand_color: BrandColor | None = None
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
    login_hero_mode: LoginHeroMode

    address_line_1: str
    address_line_2: str | None
    country_id: uuid.UUID
    state_id: uuid.UUID | None
    city_id: uuid.UUID
    postal_code: str | None
    license_number: str
    logo_url: str | None
    brand_color: str | None
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
