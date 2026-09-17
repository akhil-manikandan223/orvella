"""create people table

Revision ID: 0014_people
Revises: 0013_locations
Create Date: 2026-09-17

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0014_people'
down_revision: str | None = '0013_locations'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'people',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('first_name', sa.String(length=150), nullable=False),
        sa.Column('last_name', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=True),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('department_id', sa.Uuid(), nullable=True),
        sa.Column('location_id', sa.Uuid(), nullable=True),
        sa.Column('tenant_user_id', sa.Uuid(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id'], ['tenants.id'], name=op.f('fk_people_tenant_id_tenants')
        ),
        sa.ForeignKeyConstraint(
            ['department_id'],
            ['departments.id'],
            name=op.f('fk_people_department_id_departments'),
            ondelete='SET NULL',
        ),
        sa.ForeignKeyConstraint(
            ['location_id'],
            ['locations.id'],
            name=op.f('fk_people_location_id_locations'),
            ondelete='SET NULL',
        ),
        sa.ForeignKeyConstraint(
            ['tenant_user_id'],
            ['tenant_users.id'],
            name=op.f('fk_people_tenant_user_id_tenant_users'),
            ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_people')),
        sa.UniqueConstraint('tenant_user_id', name=op.f('uq_people_tenant_user_id')),
    )
    op.create_index(op.f('ix_people_tenant_id'), 'people', ['tenant_id'])
    op.create_index(op.f('ix_people_department_id'), 'people', ['department_id'])
    op.create_index(op.f('ix_people_location_id'), 'people', ['location_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_people_location_id'), table_name='people')
    op.drop_index(op.f('ix_people_department_id'), table_name='people')
    op.drop_index(op.f('ix_people_tenant_id'), table_name='people')
    op.drop_table('people')
