"""add tenant_users.role

Revision ID: 0010_tenant_user_roles
Revises: 0009_tenant_login_hero_mode
Create Date: 2026-09-16

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0010_tenant_user_roles'
down_revision: str | None = '0009_tenant_login_hero_mode'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # server_default='admin' both fills existing rows and matches every
    # tenant user's previous de facto capability (Phase 3 had a single
    # implicit admin role) - nobody's access silently narrows on upgrade.
    op.add_column(
        'tenant_users',
        sa.Column('role', sa.String(length=20), nullable=False, server_default='admin'),
    )
    op.create_check_constraint(
        'ck_tenant_users_role',
        'tenant_users',
        "role IN ('admin', 'member')",
    )


def downgrade() -> None:
    op.drop_constraint('ck_tenant_users_role', 'tenant_users', type_='check')
    op.drop_column('tenant_users', 'role')
