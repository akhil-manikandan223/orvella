from fastapi import APIRouter, Depends

from app.api.deps import CurrentPlatformAdminDep, DbSessionDep, get_current_platform_admin
from app.domains.table_preferences.repository import TableColumnPreferenceRepository
from app.domains.table_preferences.schemas import (
    TableColumnPreferenceRead,
    TableColumnPreferenceUpsert,
)
from app.domains.table_preferences.service import (
    get_table_column_preference,
    set_table_column_preference,
)

router = APIRouter(
    prefix='/platform-admin/table-preferences',
    tags=['table-preferences'],
    dependencies=[Depends(get_current_platform_admin)],
)


@router.get('/{table_key}', response_model=TableColumnPreferenceRead | None)
async def get_table_preference_endpoint(
    table_key: str, db: DbSessionDep, admin: CurrentPlatformAdminDep
) -> TableColumnPreferenceRead | None:
    repository = TableColumnPreferenceRepository(db)
    preference = await get_table_column_preference(
        repository, platform_admin_id=admin.id, table_key=table_key
    )
    if preference is None:
        return None
    return TableColumnPreferenceRead.model_validate(preference)


@router.put('/{table_key}', response_model=TableColumnPreferenceRead)
async def set_table_preference_endpoint(
    table_key: str,
    payload: TableColumnPreferenceUpsert,
    db: DbSessionDep,
    admin: CurrentPlatformAdminDep,
) -> TableColumnPreferenceRead:
    repository = TableColumnPreferenceRepository(db)
    preference = await set_table_column_preference(
        repository,
        platform_admin_id=admin.id,
        table_key=table_key,
        visible_columns=payload.visible_columns,
    )
    return TableColumnPreferenceRead.model_validate(preference)
