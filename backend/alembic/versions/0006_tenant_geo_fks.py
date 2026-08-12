"""replace tenants free-text country/state/city with FKs into geo masters

Revision ID: 0006_tenant_geo_fks
Revises: 0005_geo_masters
Create Date: 2026-08-12

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0006_tenant_geo_fks'
down_revision: str | None = '0005_geo_masters'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UNKNOWN_SLUG = 'unknown'


def upgrade() -> None:
    op.add_column('tenants', sa.Column('country_id', sa.Uuid(), nullable=True))
    op.add_column('tenants', sa.Column('state_id', sa.Uuid(), nullable=True))
    op.add_column('tenants', sa.Column('city_id', sa.Uuid(), nullable=True))

    connection = op.get_bind()

    # Existing tenants have placeholder free-text ('TBD') rather than real
    # geographic data (see migration 0003's backfill). Seed a generic
    # "Unknown" placeholder Country/State/City - a legitimate, visible
    # fallback any admin can also select for a tenant whose exact location
    # isn't known yet, not just a private migration artifact - and point
    # any such tenants at it. Real values are correctable via PATCH
    # afterward, same precedent as 0003's license_number/contact backfill.
    unknown_country_id = uuid.uuid4()
    connection.execute(
        sa.text('INSERT INTO countries (id, name, slug) VALUES (:id, :name, :slug)'),
        {'id': unknown_country_id, 'name': 'Unknown', 'slug': _UNKNOWN_SLUG},
    )
    unknown_state_id = uuid.uuid4()
    connection.execute(
        sa.text(
            'INSERT INTO states (id, country_id, name, slug) '
            'VALUES (:id, :country_id, :name, :slug)'
        ),
        {
            'id': unknown_state_id,
            'country_id': unknown_country_id,
            'name': 'Unknown',
            'slug': _UNKNOWN_SLUG,
        },
    )
    unknown_city_id = uuid.uuid4()
    connection.execute(
        sa.text(
            'INSERT INTO cities (id, state_id, name, slug) VALUES (:id, :state_id, :name, :slug)'
        ),
        {
            'id': unknown_city_id,
            'state_id': unknown_state_id,
            'name': 'Unknown',
            'slug': _UNKNOWN_SLUG,
        },
    )

    connection.execute(
        sa.text(
            'UPDATE tenants SET country_id = :country_id, city_id = :city_id '
            'WHERE country_id IS NULL'
        ),
        {'country_id': unknown_country_id, 'city_id': unknown_city_id},
    )
    # state_id is left NULL for existing tenants - their prior free-text
    # `state` column was already nullable and NULL here, so this preserves
    # "no state on record" rather than manufacturing false precision.

    op.alter_column('tenants', 'country_id', nullable=False)
    op.alter_column('tenants', 'city_id', nullable=False)

    op.create_foreign_key(
        op.f('fk_tenants_country_id_countries'), 'tenants', 'countries', ['country_id'], ['id']
    )
    op.create_foreign_key(
        op.f('fk_tenants_state_id_states'), 'tenants', 'states', ['state_id'], ['id']
    )
    op.create_foreign_key(
        op.f('fk_tenants_city_id_cities'), 'tenants', 'cities', ['city_id'], ['id']
    )
    op.create_index(op.f('ix_tenants_country_id'), 'tenants', ['country_id'])
    op.create_index(op.f('ix_tenants_state_id'), 'tenants', ['state_id'])
    op.create_index(op.f('ix_tenants_city_id'), 'tenants', ['city_id'])

    op.drop_column('tenants', 'country')
    op.drop_column('tenants', 'state')
    op.drop_column('tenants', 'city')


def downgrade() -> None:
    op.add_column('tenants', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('tenants', sa.Column('state', sa.String(length=100), nullable=True))
    op.add_column('tenants', sa.Column('country', sa.String(length=100), nullable=True))

    connection = op.get_bind()
    connection.execute(
        sa.text(
            'UPDATE tenants SET '
            'country = (SELECT name FROM countries WHERE countries.id = tenants.country_id), '
            'city = (SELECT name FROM cities WHERE cities.id = tenants.city_id), '
            'state = (SELECT name FROM states WHERE states.id = tenants.state_id)'
        )
    )
    op.alter_column('tenants', 'country', nullable=False)
    op.alter_column('tenants', 'city', nullable=False)

    op.drop_index(op.f('ix_tenants_city_id'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_state_id'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_country_id'), table_name='tenants')
    op.drop_constraint(op.f('fk_tenants_city_id_cities'), 'tenants', type_='foreignkey')
    op.drop_constraint(op.f('fk_tenants_state_id_states'), 'tenants', type_='foreignkey')
    op.drop_constraint(op.f('fk_tenants_country_id_countries'), 'tenants', type_='foreignkey')

    op.drop_column('tenants', 'city_id')
    op.drop_column('tenants', 'state_id')
    op.drop_column('tenants', 'country_id')
