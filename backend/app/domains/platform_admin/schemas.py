import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr

ThemePreference = Literal['light', 'dark', 'system']


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class PlatformAdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    theme_preference: ThemePreference


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ThemePreferenceUpdate(BaseModel):
    theme_preference: ThemePreference
