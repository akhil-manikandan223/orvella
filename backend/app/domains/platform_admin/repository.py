import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.platform_admin.models import PlatformAdmin


class PlatformAdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, admin_id: uuid.UUID) -> PlatformAdmin | None:
        result = await self._session.execute(
            select(PlatformAdmin).where(PlatformAdmin.id == admin_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> PlatformAdmin | None:
        result = await self._session.execute(
            select(PlatformAdmin).where(PlatformAdmin.email == email)
        )
        return result.scalar_one_or_none()

    async def create(self, *, email: str, hashed_password: str) -> PlatformAdmin:
        admin = PlatformAdmin(email=email, hashed_password=hashed_password)
        self._session.add(admin)
        await self._session.commit()
        await self._session.refresh(admin)
        return admin
