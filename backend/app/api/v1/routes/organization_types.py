import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSessionDep, get_current_platform_admin
from app.core.slugs import InvalidSlugError
from app.domains.feature.repository import FeatureRepository
from app.domains.feature.schemas import FeatureRead
from app.domains.feature.service import FeatureNotFoundError
from app.domains.organization_taxonomy.repository import (
    OrganizationCategoryRepository,
    OrganizationTypeFeatureTemplateRepository,
    OrganizationTypeRepository,
)
from app.domains.organization_taxonomy.schemas import (
    OrganizationTypeCreate,
    OrganizationTypeRead,
    OrganizationTypeUpdate,
)
from app.domains.organization_taxonomy.service import (
    CategoryNotFoundError,
    OrganizationTypeNotFoundError,
    TemplateEntryAlreadyExistsError,
    TemplateEntryNotFoundError,
    attach_feature_to_type,
    create_organization_type,
    detach_feature_from_type,
    list_organization_types,
    list_template_features,
    update_organization_type,
)

router = APIRouter(
    prefix='/platform-admin/organization-types',
    tags=['organization-taxonomy'],
    dependencies=[Depends(get_current_platform_admin)],
)


@router.post('', response_model=OrganizationTypeRead, status_code=status.HTTP_201_CREATED)
async def create_organization_type_endpoint(
    payload: OrganizationTypeCreate, db: DbSessionDep
) -> OrganizationTypeRead:
    type_repository = OrganizationTypeRepository(db)
    category_repository = OrganizationCategoryRepository(db)
    try:
        organization_type = await create_organization_type(
            type_repository,
            category_repository,
            organization_category_id=payload.organization_category_id,
            name=payload.name,
            slug=payload.slug,
        )
    except CategoryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Organization category not found') from exc
    return OrganizationTypeRead.model_validate(organization_type)


@router.get('', response_model=list[OrganizationTypeRead])
async def list_organization_types_endpoint(
    db: DbSessionDep, organization_category_id: uuid.UUID | None = None
) -> list[OrganizationTypeRead]:
    repository = OrganizationTypeRepository(db)
    types = await list_organization_types(
        repository, organization_category_id=organization_category_id
    )
    return [OrganizationTypeRead.model_validate(t) for t in types]


@router.patch('/{organization_type_id}', response_model=OrganizationTypeRead)
async def update_organization_type_endpoint(
    organization_type_id: uuid.UUID, payload: OrganizationTypeUpdate, db: DbSessionDep
) -> OrganizationTypeRead:
    repository = OrganizationTypeRepository(db)
    try:
        organization_type = await update_organization_type(
            repository, organization_type_id, **payload.model_dump(exclude_unset=True)
        )
    except OrganizationTypeNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Organization type not found') from exc
    except InvalidSlugError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return OrganizationTypeRead.model_validate(organization_type)


@router.post('/{organization_type_id}/features/{feature_id}', status_code=status.HTTP_201_CREATED)
async def attach_feature_to_type_endpoint(
    organization_type_id: uuid.UUID, feature_id: uuid.UUID, db: DbSessionDep
) -> None:
    template_repository = OrganizationTypeFeatureTemplateRepository(db)
    type_repository = OrganizationTypeRepository(db)
    feature_repository = FeatureRepository(db)
    try:
        await attach_feature_to_type(
            template_repository,
            type_repository,
            feature_repository,
            organization_type_id=organization_type_id,
            feature_id=feature_id,
        )
    except OrganizationTypeNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Organization type not found') from exc
    except FeatureNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Feature not found') from exc
    except TemplateEntryAlreadyExistsError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, 'Feature already attached to this type'
        ) from exc


@router.delete(
    '/{organization_type_id}/features/{feature_id}', status_code=status.HTTP_204_NO_CONTENT
)
async def detach_feature_from_type_endpoint(
    organization_type_id: uuid.UUID, feature_id: uuid.UUID, db: DbSessionDep
) -> None:
    template_repository = OrganizationTypeFeatureTemplateRepository(db)
    try:
        await detach_feature_from_type(
            template_repository, organization_type_id=organization_type_id, feature_id=feature_id
        )
    except TemplateEntryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Feature not attached to this type') from exc


@router.get('/{organization_type_id}/features', response_model=list[FeatureRead])
async def list_template_features_endpoint(
    organization_type_id: uuid.UUID, db: DbSessionDep
) -> list[FeatureRead]:
    template_repository = OrganizationTypeFeatureTemplateRepository(db)
    feature_repository = FeatureRepository(db)
    features = await list_template_features(
        template_repository, feature_repository, organization_type_id=organization_type_id
    )
    return [FeatureRead.model_validate(feature) for feature in features]
