import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.tenant_user.models import TenantUser


class TenantUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> TenantUser | None:
        result = await self._session.execute(select(TenantUser).where(TenantUser.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_tenant_and_email(
        self, *, tenant_id: uuid.UUID, email: str
    ) -> TenantUser | None:
        result = await self._session.execute(
            select(TenantUser).where(
                TenantUser.tenant_id == tenant_id, TenantUser.email == email
            )
        )
        return result.scalar_one_or_none()

    async def list_for_tenant(self, tenant_id: uuid.UUID) -> list[TenantUser]:
        result = await self._session.execute(
            select(TenantUser).where(TenantUser.tenant_id == tenant_id).order_by(TenantUser.email)
        )
        return list(result.scalars().all())

    async def create(
        self, *, tenant_id: uuid.UUID, email: str, hashed_password: str, role: str = 'admin'
    ) -> TenantUser:
        user = TenantUser(
            tenant_id=tenant_id, email=email, hashed_password=hashed_password, role=role
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user
