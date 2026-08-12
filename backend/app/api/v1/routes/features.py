import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSessionDep, get_current_platform_admin
from app.domains.feature.repository import FeatureRepository
from app.domains.feature.schemas import FeatureCreate, FeatureRead, FeatureUpdate
from app.domains.feature.service import (
    FeatureNotFoundError,
    create_feature,
    list_features,
    update_feature,
)

router = APIRouter(
    prefix='/platform-admin/features',
    tags=['features'],
    dependencies=[Depends(get_current_platform_admin)],
)


@router.post('', response_model=FeatureRead, status_code=status.HTTP_201_CREATED)
async def create_feature_endpoint(payload: FeatureCreate, db: DbSessionDep) -> FeatureRead:
    repository = FeatureRepository(db)
    feature = await create_feature(
        repository,
        key=payload.key,
        name=payload.name,
        description=payload.description,
        status=payload.status,
    )
    return FeatureRead.model_validate(feature)


@router.get('', response_model=list[FeatureRead])
async def list_features_endpoint(db: DbSessionDep) -> list[FeatureRead]:
    repository = FeatureRepository(db)
    features = await list_features(repository)
    return [FeatureRead.model_validate(feature) for feature in features]


@router.patch('/{feature_id}', response_model=FeatureRead)
async def update_feature_endpoint(
    feature_id: uuid.UUID, payload: FeatureUpdate, db: DbSessionDep
) -> FeatureRead:
    repository = FeatureRepository(db)
    try:
        feature = await update_feature(
            repository, feature_id, **payload.model_dump(exclude_unset=True)
        )
    except FeatureNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Feature not found') from exc
    return FeatureRead.model_validate(feature)
