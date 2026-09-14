import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.table_preferences.models import TableColumnPreference


class TableColumnPreferenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self, *, platform_admin_id: uuid.UUID, table_key: str
    ) -> TableColumnPreference | None:
        result = await self._session.execute(
            select(TableColumnPreference).where(
                TableColumnPreference.platform_admin_id == platform_admin_id,
                TableColumnPreference.table_key == table_key,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self, *, platform_admin_id: uuid.UUID, table_key: str, visible_columns: list[str]
    ) -> TableColumnPreference:
        existing = await self.get(platform_admin_id=platform_admin_id, table_key=table_key)
        if existing is not None:
            existing.visible_columns = visible_columns
            await self._session.commit()
            await self._session.refresh(existing)
            return existing

        preference = TableColumnPreference(
            platform_admin_id=platform_admin_id,
            table_key=table_key,
            visible_columns=visible_columns,
        )
        self._session.add(preference)
        await self._session.commit()
        await self._session.refresh(preference)
        return preference
