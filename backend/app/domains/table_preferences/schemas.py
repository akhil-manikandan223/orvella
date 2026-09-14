from pydantic import BaseModel, ConfigDict


class TableColumnPreferenceUpsert(BaseModel):
    visible_columns: list[str]


class TableColumnPreferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    table_key: str
    visible_columns: list[str]
