import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.feature.models import Feature


class FeatureRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, feature_id: uuid.UUID) -> Feature | None:
        result = await self._session.execute(select(Feature).where(Feature.id == feature_id))
        return result.scalar_one_or_none()

    async def list_by_ids(self, feature_ids: Sequence[uuid.UUID]) -> list[Feature]:
        if not feature_ids:
            return []
        result = await self._session.execute(select(Feature).where(Feature.id.in_(feature_ids)))
        return list(result.scalars().all())

    async def list_all(self) -> list[Feature]:
        result = await self._session.execute(select(Feature).order_by(Feature.name))
        return list(result.scalars().all())

    async def create(self, *, key: str, name: str, description: str | None, status: str) -> Feature:
        feature = Feature(key=key, name=name, description=description, status=status)
        self._session.add(feature)
        await self._session.commit()
        await self._session.refresh(feature)
        return feature

    async def update(self, feature: Feature, **fields: object) -> Feature:
        for field_name, value in fields.items():
            setattr(feature, field_name, value)
        await self._session.commit()
        await self._session.refresh(feature)
        return feature
