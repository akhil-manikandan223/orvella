from app.core.security import verify_password
from app.domains.platform_admin.models import PlatformAdmin
from app.domains.platform_admin.repository import PlatformAdminRepository


class InvalidCredentialsError(Exception):
    pass


async def authenticate_platform_admin(
    repository: PlatformAdminRepository, *, email: str, password: str
) -> PlatformAdmin:
    normalized_email = email.strip().lower()
    admin = await repository.get_by_email(normalized_email)
    if admin is None or not admin.is_active or not verify_password(password, admin.hashed_password):
        raise InvalidCredentialsError
    return admin
