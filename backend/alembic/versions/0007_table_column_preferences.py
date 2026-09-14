"""create table_column_preferences table

Revision ID: 0007_table_column_preferences
Revises: 0006_tenant_geo_fks
Create Date: 2026-08-16

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0007_table_column_preferences'
down_revision: str | None = '0006_tenant_geo_fks'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'table_column_preferences',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('platform_admin_id', sa.Uuid(), nullable=False),
        sa.Column('table_key', sa.String(length=100), nullable=False),
        sa.Column('visible_columns', sa.JSON(), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['platform_admin_id'],
            ['platform_admins.id'],
            name=op.f('fk_table_column_preferences_platform_admin_id_platform_admins'),
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_table_column_preferences')),
        sa.UniqueConstraint(
            'platform_admin_id',
            'table_key',
            name='uq_table_column_preferences_admin_table',
        ),
    )
    op.create_index(
        op.f('ix_table_column_preferences_platform_admin_id'),
        'table_column_preferences',
        ['platform_admin_id'],
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_table_column_preferences_platform_admin_id'),
        table_name='table_column_preferences',
    )
    op.drop_table('table_column_preferences')
