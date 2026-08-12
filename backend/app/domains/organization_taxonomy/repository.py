import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.organization_taxonomy.models import (
    OrganizationCategory,
    OrganizationType,
    OrganizationTypeFeatureTemplate,
)


class OrganizationCategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, category_id: uuid.UUID) -> OrganizationCategory | None:
        result = await self._session.execute(
            select(OrganizationCategory).where(OrganizationCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[OrganizationCategory]:
        result = await self._session.execute(
            select(OrganizationCategory).order_by(OrganizationCategory.name)
        )
        return list(result.scalars().all())

    async def create(self, *, name: str, slug: str) -> OrganizationCategory:
        category = OrganizationCategory(name=name, slug=slug)
        self._session.add(category)
        await self._session.commit()
        await self._session.refresh(category)
        return category

    async def update(
        self, category: OrganizationCategory, **fields: object
    ) -> OrganizationCategory:
        for field_name, value in fields.items():
            setattr(category, field_name, value)
        await self._session.commit()
        await self._session.refresh(category)
        return category


class OrganizationTypeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, type_id: uuid.UUID) -> OrganizationType | None:
        result = await self._session.execute(
            select(OrganizationType).where(OrganizationType.id == type_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self, *, organization_category_id: uuid.UUID | None
    ) -> list[OrganizationType]:
        query = select(OrganizationType).order_by(OrganizationType.name)
        if organization_category_id is not None:
            query = query.where(
                OrganizationType.organization_category_id == organization_category_id
            )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(
        self, *, organization_category_id: uuid.UUID, name: str, slug: str
    ) -> OrganizationType:
        organization_type = OrganizationType(
            organization_category_id=organization_category_id, name=name, slug=slug
        )
        self._session.add(organization_type)
        await self._session.commit()
        await self._session.refresh(organization_type)
        return organization_type

    async def update(
        self, organization_type: OrganizationType, **fields: object
    ) -> OrganizationType:
        for field_name, value in fields.items():
            setattr(organization_type, field_name, value)
        await self._session.commit()
        await self._session.refresh(organization_type)
        return organization_type


class OrganizationTypeFeatureTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self, *, organization_type_id: uuid.UUID, feature_id: uuid.UUID
    ) -> OrganizationTypeFeatureTemplate | None:
        result = await self._session.execute(
            select(OrganizationTypeFeatureTemplate).where(
                OrganizationTypeFeatureTemplate.organization_type_id == organization_type_id,
                OrganizationTypeFeatureTemplate.feature_id == feature_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_feature_ids_for_type(self, organization_type_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self._session.execute(
            select(OrganizationTypeFeatureTemplate.feature_id).where(
                OrganizationTypeFeatureTemplate.organization_type_id == organization_type_id
            )
        )
        return list(result.scalars().all())

    async def attach(
        self, *, organization_type_id: uuid.UUID, feature_id: uuid.UUID
    ) -> OrganizationTypeFeatureTemplate:
        entry = OrganizationTypeFeatureTemplate(
            organization_type_id=organization_type_id, feature_id=feature_id
        )
        self._session.add(entry)
        await self._session.commit()
        await self._session.refresh(entry)
        return entry

    async def detach(self, entry: OrganizationTypeFeatureTemplate) -> None:
        await self._session.delete(entry)
        await self._session.commit()
