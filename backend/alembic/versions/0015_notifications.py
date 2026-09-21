"""create notifications table

Revision ID: 0015_notifications
Revises: 0014_people
Create Date: 2026-09-18

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0015_notifications'
down_revision: str | None = '0014_people'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('tenant_user_id', sa.Uuid(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id'], ['tenants.id'], name=op.f('fk_notifications_tenant_id_tenants')
        ),
        sa.ForeignKeyConstraint(
            ['tenant_user_id'],
            ['tenant_users.id'],
            name=op.f('fk_notifications_tenant_user_id_tenant_users'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_notifications')),
    )
    op.create_index(op.f('ix_notifications_tenant_id'), 'notifications', ['tenant_id'])
    op.create_index(op.f('ix_notifications_tenant_user_id'), 'notifications', ['tenant_user_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_notifications_tenant_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_tenant_id'), table_name='notifications')
    op.drop_table('notifications')
