"""add tenant profile fields (address, license number, logo, key contact)

Revision ID: 0003_tenant_profile_fields
Revises: 0002_taxonomy_feature_tenant
Create Date: 2026-08-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0003_tenant_profile_fields'
down_revision: str | None = '0002_taxonomy_feature_tenant'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PLACEHOLDER_TEXT_COLUMNS = {
    'address_line_1': 'TBD',
    'city': 'TBD',
    'country': 'TBD',
    'key_contact_name': 'TBD',
    'key_contact_email': 'tbd@example.com',
    'key_contact_phone': '0000000000',
}


def upgrade() -> None:
    # Nullable-typed columns first (no backfill needed).
    op.add_column('tenants', sa.Column('address_line_2', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('state', sa.String(length=100), nullable=True))
    op.add_column('tenants', sa.Column('postal_code', sa.String(length=20), nullable=True))
    op.add_column('tenants', sa.Column('logo_url', sa.String(length=500), nullable=True))

    # Required columns: add nullable, backfill any existing rows with a
    # placeholder, then tighten to NOT NULL - safe regardless of whether the
    # tenants table already has rows.
    for column_name in (
        'address_line_1',
        'city',
        'country',
        'key_contact_name',
        'key_contact_email',
        'key_contact_phone',
    ):
        length = {
            'address_line_1': 255,
            'city': 100,
            'country': 100,
            'key_contact_name': 150,
            'key_contact_email': 320,
            'key_contact_phone': 30,
        }[column_name]
        op.add_column('tenants', sa.Column(column_name, sa.String(length=length), nullable=True))
        op.execute(
            sa.text(
                f'UPDATE tenants SET {column_name} = :placeholder WHERE {column_name} IS NULL'
            ).bindparams(placeholder=_PLACEHOLDER_TEXT_COLUMNS[column_name])
        )
        op.alter_column('tenants', column_name, nullable=False)

    # license_number is unique, so a shared placeholder would collide across
    # multiple existing rows - derive one from each row's own id instead.
    op.add_column('tenants', sa.Column('license_number', sa.String(length=100), nullable=True))
    op.execute(
        "UPDATE tenants SET license_number = 'TBD-' || id::text WHERE license_number IS NULL"
    )
    op.alter_column('tenants', 'license_number', nullable=False)
    op.create_index(op.f('ix_tenants_license_number'), 'tenants', ['license_number'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_tenants_license_number'), table_name='tenants')
    op.drop_column('tenants', 'key_contact_phone')
    op.drop_column('tenants', 'key_contact_email')
    op.drop_column('tenants', 'key_contact_name')
    op.drop_column('tenants', 'logo_url')
    op.drop_column('tenants', 'license_number')
    op.drop_column('tenants', 'country')
    op.drop_column('tenants', 'postal_code')
    op.drop_column('tenants', 'state')
    op.drop_column('tenants', 'city')
    op.drop_column('tenants', 'address_line_2')
    op.drop_column('tenants', 'address_line_1')
