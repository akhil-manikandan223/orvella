import uuid

from app.domains.feature.models import Feature
from app.domains.feature.repository import FeatureRepository


class FeatureNotFoundError(Exception):
    pass


async def create_feature(
    repository: FeatureRepository, *, key: str, name: str, description: str | None, status: str
) -> Feature:
    return await repository.create(key=key, name=name, description=description, status=status)


async def list_features(repository: FeatureRepository) -> list[Feature]:
    return await repository.list_all()


async def update_feature(
    repository: FeatureRepository, feature_id: uuid.UUID, **fields: object
) -> Feature:
    feature = await repository.get_by_id(feature_id)
    if feature is None:
        raise FeatureNotFoundError
    return await repository.update(feature, **fields)
