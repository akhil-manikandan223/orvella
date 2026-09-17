"""create locations table

Revision ID: 0013_locations
Revises: 0012_departments
Create Date: 2026-09-17

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0013_locations'
down_revision: str | None = '0012_departments'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'locations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id'], ['tenants.id'], name=op.f('fk_locations_tenant_id_tenants')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_locations')),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_locations_tenant_name'),
    )
    op.create_index(op.f('ix_locations_tenant_id'), 'locations', ['tenant_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_locations_tenant_id'), table_name='locations')
    op.drop_table('locations')
