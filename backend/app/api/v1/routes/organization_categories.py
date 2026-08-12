import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSessionDep, get_current_platform_admin
from app.core.slugs import InvalidSlugError
from app.domains.organization_taxonomy.repository import OrganizationCategoryRepository
from app.domains.organization_taxonomy.schemas import (
    OrganizationCategoryCreate,
    OrganizationCategoryRead,
    OrganizationCategoryUpdate,
)
from app.domains.organization_taxonomy.service import (
    CategoryNotFoundError,
    create_category,
    list_categories,
    update_category,
)

router = APIRouter(
    prefix='/platform-admin/organization-categories',
    tags=['organization-taxonomy'],
    dependencies=[Depends(get_current_platform_admin)],
)


@router.post('', response_model=OrganizationCategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category_endpoint(
    payload: OrganizationCategoryCreate, db: DbSessionDep
) -> OrganizationCategoryRead:
    repository = OrganizationCategoryRepository(db)
    category = await create_category(repository, name=payload.name, slug=payload.slug)
    return OrganizationCategoryRead.model_validate(category)


@router.get('', response_model=list[OrganizationCategoryRead])
async def list_categories_endpoint(db: DbSessionDep) -> list[OrganizationCategoryRead]:
    repository = OrganizationCategoryRepository(db)
    categories = await list_categories(repository)
    return [OrganizationCategoryRead.model_validate(category) for category in categories]


@router.patch('/{category_id}', response_model=OrganizationCategoryRead)
async def update_category_endpoint(
    category_id: uuid.UUID, payload: OrganizationCategoryUpdate, db: DbSessionDep
) -> OrganizationCategoryRead:
    repository = OrganizationCategoryRepository(db)
    try:
        category = await update_category(
            repository, category_id, **payload.model_dump(exclude_unset=True)
        )
    except CategoryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Organization category not found') from exc
    except InvalidSlugError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return OrganizationCategoryRead.model_validate(category)
