import uuid

from pydantic import BaseModel, ConfigDict


class CountryCreate(BaseModel):
    name: str
    slug: str


class CountryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None


class CountryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str


class StateCreate(BaseModel):
    country_id: uuid.UUID
    name: str
    slug: str


class StateUpdate(BaseModel):
    # country_id deliberately excluded - reassigning a state to a different
    # country is a bigger structural change than a rename.
    name: str | None = None
    slug: str | None = None


class StateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    country_id: uuid.UUID
    name: str
    slug: str


class DistrictCreate(BaseModel):
    state_id: uuid.UUID
    name: str
    slug: str


class DistrictUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None


class DistrictRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    state_id: uuid.UUID
    name: str
    slug: str


class CityCreate(BaseModel):
    state_id: uuid.UUID
    district_id: uuid.UUID | None = None
    name: str
    slug: str


class CityUpdate(BaseModel):
    district_id: uuid.UUID | None = None
    name: str | None = None
    slug: str | None = None


class CityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    state_id: uuid.UUID
    district_id: uuid.UUID | None
    name: str
    slug: str
