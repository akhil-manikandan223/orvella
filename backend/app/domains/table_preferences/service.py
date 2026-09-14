import uuid

from app.domains.table_preferences.models import TableColumnPreference
from app.domains.table_preferences.repository import TableColumnPreferenceRepository


async def get_table_column_preference(
    repository: TableColumnPreferenceRepository, *, platform_admin_id: uuid.UUID, table_key: str
) -> TableColumnPreference | None:
    return await repository.get(platform_admin_id=platform_admin_id, table_key=table_key)


async def set_table_column_preference(
    repository: TableColumnPreferenceRepository,
    *,
    platform_admin_id: uuid.UUID,
    table_key: str,
    visible_columns: list[str],
) -> TableColumnPreference:
    return await repository.upsert(
        platform_admin_id=platform_admin_id,
        table_key=table_key,
        visible_columns=visible_columns,
    )
