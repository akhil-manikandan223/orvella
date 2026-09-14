"""create tenant_users table

Revision ID: 0008_tenant_users
Revises: 0007_table_column_preferences
Create Date: 2026-09-14

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0008_tenant_users'
down_revision: str | None = '0007_table_column_preferences'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'tenant_users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id'], ['tenants.id'], name=op.f('fk_tenant_users_tenant_id_tenants')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_tenant_users')),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_tenant_users_tenant_email'),
    )
    op.create_index(op.f('ix_tenant_users_tenant_id'), 'tenant_users', ['tenant_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_tenant_users_tenant_id'), table_name='tenant_users')
    op.drop_table('tenant_users')
