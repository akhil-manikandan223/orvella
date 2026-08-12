import uuid

from pydantic import BaseModel, ConfigDict


class OrganizationCategoryCreate(BaseModel):
    name: str
    slug: str


class OrganizationCategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None


class OrganizationCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str


class OrganizationTypeCreate(BaseModel):
    organization_category_id: uuid.UUID
    name: str
    slug: str


class OrganizationTypeUpdate(BaseModel):
    # organization_category_id deliberately excluded - reassigning a type to
    # a different category is a bigger structural change than a rename.
    name: str | None = None
    slug: str | None = None


class OrganizationTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_category_id: uuid.UUID
    name: str
    slug: str
