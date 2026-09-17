import re
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    environment: str = 'local'

    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = 'HS256'
    # Short-lived on purpose: refresh_token_expire_days below is what
    # actually keeps a user signed in. A leaked access token self-expires
    # quickly; the refresh token is the one that can be revoked server-side.
    jwt_access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    cors_origins: str = 'http://localhost:6200'

    backend_port: int = 8000

    base_domain: str = 'orvella.com'

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]

    @property
    def cors_origin_regex(self) -> str:
        """Allow the bare base domain and any single-label tenant subdomain.

        e.g. base_domain='localtest.me' matches http://localhost:6200,
        http://localtest.me:6200, and http://saihospital.localtest.me:6200
        (any scheme/port) - needed because tenant subdomains aren't known
        ahead of time, so a fixed allow-list (cors_origins_list) can't cover
        them.
        """
        escaped = re.escape(self.base_domain.strip().lower())
        return rf'^https?://([a-z0-9-]+\.)?{escaped}(:\d+)?$'


@lru_cache
def get_settings() -> Settings:
    return Settings()
