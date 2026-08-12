"""create geo master tables (countries, states, districts, cities) and seed data

Revision ID: 0005_geo_masters
Revises: 0004_audit_logs
Create Date: 2026-08-12

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.domains.geo.seed_data import (
    INDIA_DISTRICTS_BY_STATE,
    INDIA_MAJOR_CITIES,
    INDIA_SLUG,
    INDIA_STATES,
    WORLD_COUNTRIES,
)

revision: str = '0005_geo_masters'
down_revision: str | None = '0004_audit_logs'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'countries',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('slug', sa.String(length=150), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_countries')),
    )
    op.create_index(op.f('ix_countries_slug'), 'countries', ['slug'], unique=True)

    op.create_table(
        'states',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('country_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('slug', sa.String(length=150), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['country_id'], ['countries.id'], name=op.f('fk_states_country_id_countries')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_states')),
        sa.UniqueConstraint('country_id', 'slug', name=op.f('uq_states_country_id')),
    )
    op.create_index(op.f('ix_states_country_id'), 'states', ['country_id'])

    op.create_table(
        'districts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('state_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('slug', sa.String(length=150), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['state_id'], ['states.id'], name=op.f('fk_districts_state_id_states')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_districts')),
        sa.UniqueConstraint('state_id', 'slug', name=op.f('uq_districts_state_id')),
    )
    op.create_index(op.f('ix_districts_state_id'), 'districts', ['state_id'])

    op.create_table(
        'cities',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('state_id', sa.Uuid(), nullable=False),
        sa.Column('district_id', sa.Uuid(), nullable=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('slug', sa.String(length=150), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['state_id'], ['states.id'], name=op.f('fk_cities_state_id_states')
        ),
        sa.ForeignKeyConstraint(
            ['district_id'], ['districts.id'], name=op.f('fk_cities_district_id_districts')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_cities')),
        sa.UniqueConstraint('state_id', 'slug', name=op.f('uq_cities_state_id')),
    )
    op.create_index(op.f('ix_cities_state_id'), 'cities', ['state_id'])
    op.create_index(op.f('ix_cities_district_id'), 'cities', ['district_id'])

    _seed(
        countries_table=sa.table(
            'countries', sa.column('id'), sa.column('name'), sa.column('slug')
        ),
        states_table=sa.table(
            'states', sa.column('id'), sa.column('country_id'), sa.column('name'), sa.column('slug')
        ),
        districts_table=sa.table(
            'districts',
            sa.column('id'),
            sa.column('state_id'),
            sa.column('name'),
            sa.column('slug'),
        ),
        cities_table=sa.table(
            'cities',
            sa.column('id'),
            sa.column('state_id'),
            sa.column('district_id'),
            sa.column('name'),
            sa.column('slug'),
        ),
    )


def _seed(*, countries_table, states_table, districts_table, cities_table) -> None:
    country_id_by_slug: dict[str, uuid.UUID] = {}
    country_rows = []
    for name, slug in WORLD_COUNTRIES:
        country_id = uuid.uuid4()
        country_id_by_slug[slug] = country_id
        country_rows.append({'id': country_id, 'name': name, 'slug': slug})
    op.bulk_insert(countries_table, country_rows)

    india_country_id = country_id_by_slug[INDIA_SLUG]

    state_id_by_slug: dict[str, uuid.UUID] = {}
    state_rows = []
    for name, slug in INDIA_STATES:
        state_id = uuid.uuid4()
        state_id_by_slug[slug] = state_id
        state_rows.append(
            {'id': state_id, 'country_id': india_country_id, 'name': name, 'slug': slug}
        )
    op.bulk_insert(states_table, state_rows)

    district_id_by_state_and_slug: dict[tuple[str, str], uuid.UUID] = {}
    district_rows = []
    for state_slug, districts in INDIA_DISTRICTS_BY_STATE.items():
        state_id = state_id_by_slug[state_slug]
        for name, slug in districts:
            district_id = uuid.uuid4()
            district_id_by_state_and_slug[(state_slug, slug)] = district_id
            district_rows.append(
                {'id': district_id, 'state_id': state_id, 'name': name, 'slug': slug}
            )
    op.bulk_insert(districts_table, district_rows)

    city_rows = []
    for name, slug, state_slug, district_slug in INDIA_MAJOR_CITIES:
        state_id = state_id_by_slug[state_slug]
        district_id = (
            district_id_by_state_and_slug.get((state_slug, district_slug))
            if district_slug is not None
            else None
        )
        city_rows.append(
            {
                'id': uuid.uuid4(),
                'state_id': state_id,
                'district_id': district_id,
                'name': name,
                'slug': slug,
            }
        )
    op.bulk_insert(cities_table, city_rows)


def downgrade() -> None:
    op.drop_index(op.f('ix_cities_district_id'), table_name='cities')
    op.drop_index(op.f('ix_cities_state_id'), table_name='cities')
    op.drop_table('cities')

    op.drop_index(op.f('ix_districts_state_id'), table_name='districts')
    op.drop_table('districts')

    op.drop_index(op.f('ix_states_country_id'), table_name='states')
    op.drop_table('states')

    op.drop_index(op.f('ix_countries_slug'), table_name='countries')
    op.drop_table('countries')
