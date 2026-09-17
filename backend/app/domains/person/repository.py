import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.person.models import Person


class PersonRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, person_id: uuid.UUID) -> Person | None:
        result = await self._session.execute(select(Person).where(Person.id == person_id))
        return result.scalar_one_or_none()

    async def list_for_tenant(self, tenant_id: uuid.UUID) -> list[Person]:
        result = await self._session.execute(
            select(Person)
            .where(Person.tenant_id == tenant_id)
            .order_by(Person.last_name, Person.first_name)
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        first_name: str,
        last_name: str,
        category: str,
        email: str | None,
        phone: str | None,
        department_id: uuid.UUID | None,
        location_id: uuid.UUID | None,
    ) -> Person:
        person = Person(
            tenant_id=tenant_id,
            first_name=first_name,
            last_name=last_name,
            category=category,
            email=email,
            phone=phone,
            department_id=department_id,
            location_id=location_id,
        )
        self._session.add(person)
        await self._session.commit()
        await self._session.refresh(person)
        return person

    async def update(self, person: Person, **fields: object) -> Person:
        for field_name, value in fields.items():
            setattr(person, field_name, value)
        await self._session.commit()
        await self._session.refresh(person)
        return person

    async def delete(self, person: Person) -> None:
        await self._session.delete(person)
        await self._session.commit()
