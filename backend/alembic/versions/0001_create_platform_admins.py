"""create platform_admins

Revision ID: 0001_create_platform_admins
Revises:
Create Date: 2026-08-11

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0001_create_platform_admins'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'platform_admins',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_platform_admins')),
    )
    op.create_index(op.f('ix_platform_admins_email'), 'platform_admins', ['email'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_platform_admins_email'), table_name='platform_admins')
    op.drop_table('platform_admins')
