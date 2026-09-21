import uuid

from app.core.security import hash_password, verify_password
from app.domains.tenant_user.models import TenantUser
from app.domains.tenant_user.repository import TenantUserRepository


class InvalidCredentialsError(Exception):
    pass


class TenantUserAlreadyExistsError(Exception):
    pass


class TenantUserNotFoundError(Exception):
    pass


async def authenticate_tenant_user(
    repository: TenantUserRepository, *, tenant_id: uuid.UUID, email: str, password: str
) -> TenantUser:
    normalized_email = email.strip().lower()
    user = await repository.get_by_tenant_and_email(tenant_id=tenant_id, email=normalized_email)
    if user is None or not user.is_active or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError
    return user


async def create_tenant_user(
    repository: TenantUserRepository,
    *,
    tenant_id: uuid.UUID,
    email: str,
    password: str,
    role: str = 'admin',
) -> TenantUser:
    normalized_email = email.strip().lower()
    if await repository.get_by_tenant_and_email(tenant_id=tenant_id, email=normalized_email):
        raise TenantUserAlreadyExistsError
    return await repository.create(
        tenant_id=tenant_id,
        email=normalized_email,
        hashed_password=hash_password(password),
        role=role,
    )


async def list_tenant_users(
    repository: TenantUserRepository, *, tenant_id: uuid.UUID
) -> list[TenantUser]:
    return await repository.list_for_tenant(tenant_id)


async def change_tenant_user_password(
    repository: TenantUserRepository,
    user: TenantUser,
    *,
    current_password: str,
    new_password: str,
) -> TenantUser:
    if not verify_password(current_password, user.hashed_password):
        raise InvalidCredentialsError
    return await repository.update(user, hashed_password=hash_password(new_password))


async def update_tenant_user(
    repository: TenantUserRepository,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    **fields: object,
) -> TenantUser:
    user = await repository.get_by_id(user_id)
    if user is None or user.tenant_id != tenant_id:
        raise TenantUserNotFoundError

    email = fields.get('email')
    if email is not None:
        normalized_email = str(email).strip().lower()
        existing = await repository.get_by_tenant_and_email(
            tenant_id=tenant_id, email=normalized_email
        )
        if existing is not None and existing.id != user_id:
            raise TenantUserAlreadyExistsError
        fields['email'] = normalized_email

    return await repository.update(user, **fields)
