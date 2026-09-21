import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr

TenantUserRole = Literal['admin', 'member']
ThemePreference = Literal['light', 'dark', 'system']


class TenantLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TenantTokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class TenantUserCreate(BaseModel):
    email: EmailStr
    password: str
    role: TenantUserRole = 'admin'


class TenantChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class TenantUserUpdate(BaseModel):
    email: EmailStr | None = None
    role: TenantUserRole | None = None
    is_active: bool | None = None


class TenantUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    role: TenantUserRole
    is_active: bool
    theme_preference: ThemePreference


class TenantThemePreferenceUpdate(BaseModel):
    theme_preference: ThemePreference


class TenantContextRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str


class TenantMeRead(BaseModel):
    user: TenantUserRead
    tenant: TenantContextRead


class HeroFeatureRead(BaseModel):
    """A feature as shown on the tenant login page's hero tiles.

    Deliberately just key/name/description - the same shape regardless of
    whether it came from the tenant's own enabled features or the full
    platform catalog, so the frontend doesn't need to know which.
    """

    key: str
    name: str
    description: str | None


class TenantLoginContextRead(BaseModel):
    """Public, pre-login info for the tenant login page.

    Which features end up in hero_features depends on the tenant's
    login_hero_mode - 'default' returns every active platform feature,
    'featured' returns only this tenant's own enabled features. See
    GET /tenant/auth/context.
    """

    tenant: TenantContextRead
    hero_features: list[HeroFeatureRead]
