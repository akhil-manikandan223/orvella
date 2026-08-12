"""create audit_logs table

Revision ID: 0004_audit_logs
Revises: 0003_tenant_profile_fields
Create Date: 2026-08-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0004_audit_logs'
down_revision: str | None = '0003_tenant_profile_fields'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('actor_type', sa.String(length=50), nullable=True),
        sa.Column('actor_id', sa.Uuid(), nullable=True),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=True),
        sa.Column('changes', sa.JSON(), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "action IN ('create', 'update', 'delete')", name=op.f('ck_audit_logs_action')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs')),
    )
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'])
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'])
    op.create_index(op.f('ix_audit_logs_tenant_id'), 'audit_logs', ['tenant_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_tenant_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_type'), table_name='audit_logs')
    op.drop_table('audit_logs')
