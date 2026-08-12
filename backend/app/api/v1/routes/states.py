import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSessionDep, get_current_platform_admin
from app.core.slugs import InvalidSlugError
from app.domains.geo.repository import CountryRepository, StateRepository
from app.domains.geo.schemas import StateCreate, StateRead, StateUpdate
from app.domains.geo.service import (
    CountryNotFoundError,
    StateNotFoundError,
    create_state,
    list_states,
    update_state,
)

router = APIRouter(
    prefix='/platform-admin/states',
    tags=['geo'],
    dependencies=[Depends(get_current_platform_admin)],
)


@router.post('', response_model=StateRead, status_code=status.HTTP_201_CREATED)
async def create_state_endpoint(payload: StateCreate, db: DbSessionDep) -> StateRead:
    state_repository = StateRepository(db)
    country_repository = CountryRepository(db)
    try:
        state = await create_state(
            state_repository,
            country_repository,
            country_id=payload.country_id,
            name=payload.name,
            slug=payload.slug,
        )
    except CountryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Country not found') from exc
    return StateRead.model_validate(state)


@router.get('', response_model=list[StateRead])
async def list_states_endpoint(
    db: DbSessionDep, country_id: uuid.UUID | None = None
) -> list[StateRead]:
    repository = StateRepository(db)
    states = await list_states(repository, country_id=country_id)
    return [StateRead.model_validate(state) for state in states]


@router.patch('/{state_id}', response_model=StateRead)
async def update_state_endpoint(
    state_id: uuid.UUID, payload: StateUpdate, db: DbSessionDep
) -> StateRead:
    repository = StateRepository(db)
    try:
        state = await update_state(repository, state_id, **payload.model_dump(exclude_unset=True))
    except StateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'State not found') from exc
    except InvalidSlugError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return StateRead.model_validate(state)
