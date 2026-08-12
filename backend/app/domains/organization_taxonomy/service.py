import uuid

from app.core.slugs import MAX_TAXONOMY_SLUG_LENGTH, validate_slug_format
from app.domains.feature.models import Feature
from app.domains.feature.repository import FeatureRepository
from app.domains.feature.service import FeatureNotFoundError
from app.domains.organization_taxonomy.models import OrganizationCategory, OrganizationType
from app.domains.organization_taxonomy.repository import (
    OrganizationCategoryRepository,
    OrganizationTypeFeatureTemplateRepository,
    OrganizationTypeRepository,
)


class CategoryNotFoundError(Exception):
    pass


class OrganizationTypeNotFoundError(Exception):
    pass


class TemplateEntryNotFoundError(Exception):
    pass


class TemplateEntryAlreadyExistsError(Exception):
    pass


async def create_category(
    repository: OrganizationCategoryRepository, *, name: str, slug: str
) -> OrganizationCategory:
    validate_slug_format(slug, max_length=MAX_TAXONOMY_SLUG_LENGTH)
    return await repository.create(name=name, slug=slug)


async def list_categories(repository: OrganizationCategoryRepository) -> list[OrganizationCategory]:
    return await repository.list_all()


async def update_category(
    repository: OrganizationCategoryRepository, category_id: uuid.UUID, **fields: object
) -> OrganizationCategory:
    category = await repository.get_by_id(category_id)
    if category is None:
        raise CategoryNotFoundError
    if fields.get('slug') is not None:
        validate_slug_format(fields['slug'], max_length=MAX_TAXONOMY_SLUG_LENGTH)
    return await repository.update(category, **fields)


async def create_organization_type(
    type_repository: OrganizationTypeRepository,
    category_repository: OrganizationCategoryRepository,
    *,
    organization_category_id: uuid.UUID,
    name: str,
    slug: str,
) -> OrganizationType:
    validate_slug_format(slug, max_length=MAX_TAXONOMY_SLUG_LENGTH)
    category = await category_repository.get_by_id(organization_category_id)
    if category is None:
        raise CategoryNotFoundError
    return await type_repository.create(
        organization_category_id=organization_category_id, name=name, slug=slug
    )


async def list_organization_types(
    repository: OrganizationTypeRepository, *, organization_category_id: uuid.UUID | None
) -> list[OrganizationType]:
    return await repository.list_all(organization_category_id=organization_category_id)


async def update_organization_type(
    repository: OrganizationTypeRepository, organization_type_id: uuid.UUID, **fields: object
) -> OrganizationType:
    organization_type = await repository.get_by_id(organization_type_id)
    if organization_type is None:
        raise OrganizationTypeNotFoundError
    if fields.get('slug') is not None:
        validate_slug_format(fields['slug'], max_length=MAX_TAXONOMY_SLUG_LENGTH)
    return await repository.update(organization_type, **fields)


async def attach_feature_to_type(
    template_repository: OrganizationTypeFeatureTemplateRepository,
    type_repository: OrganizationTypeRepository,
    feature_repository: FeatureRepository,
    *,
    organization_type_id: uuid.UUID,
    feature_id: uuid.UUID,
) -> None:
    if await type_repository.get_by_id(organization_type_id) is None:
        raise OrganizationTypeNotFoundError
    if await feature_repository.get_by_id(feature_id) is None:
        raise FeatureNotFoundError
    if (
        await template_repository.get(
            organization_type_id=organization_type_id, feature_id=feature_id
        )
        is not None
    ):
        raise TemplateEntryAlreadyExistsError
    await template_repository.attach(
        organization_type_id=organization_type_id, feature_id=feature_id
    )


async def detach_feature_from_type(
    template_repository: OrganizationTypeFeatureTemplateRepository,
    *,
    organization_type_id: uuid.UUID,
    feature_id: uuid.UUID,
) -> None:
    entry = await template_repository.get(
        organization_type_id=organization_type_id, feature_id=feature_id
    )
    if entry is None:
        raise TemplateEntryNotFoundError
    await template_repository.detach(entry)


async def list_template_features(
    template_repository: OrganizationTypeFeatureTemplateRepository,
    feature_repository: FeatureRepository,
    *,
    organization_type_id: uuid.UUID,
) -> list[Feature]:
    feature_ids = await template_repository.list_feature_ids_for_type(organization_type_id)
    return await feature_repository.list_by_ids(feature_ids)
