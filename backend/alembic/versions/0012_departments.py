"""create departments table

Revision ID: 0012_departments
Revises: 0011_refresh_tokens
Create Date: 2026-09-17

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0012_departments'
down_revision: str | None = '0011_refresh_tokens'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'departments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id'], ['tenants.id'], name=op.f('fk_departments_tenant_id_tenants')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_departments')),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_departments_tenant_name'),
    )
    op.create_index(op.f('ix_departments_tenant_id'), 'departments', ['tenant_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_departments_tenant_id'), table_name='departments')
    op.drop_table('departments')
