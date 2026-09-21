"""add per-user theme_preference to platform_admins and tenant_users

Revision ID: 0016_theme_preference
Revises: 0015_notifications
Create Date: 2026-09-21

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0016_theme_preference'
down_revision: str | None = '0015_notifications'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # server_default so existing rows get 'system' rather than violating the
    # NOT NULL - it stays on the column, which is harmless and keeps raw
    # INSERTs (fixtures, seeds) working without naming the column.
    for table, constraint in (
        ('platform_admins', 'ck_platform_admins_theme_preference'),
        ('tenant_users', 'ck_tenant_users_theme_preference'),
    ):
        op.add_column(
            table,
            sa.Column(
                'theme_preference',
                sa.String(length=10),
                nullable=False,
                server_default='system',
            ),
        )
        op.create_check_constraint(
            constraint, table, "theme_preference IN ('light', 'dark', 'system')"
        )


def downgrade() -> None:
    for table, constraint in (
        ('platform_admins', 'ck_platform_admins_theme_preference'),
        ('tenant_users', 'ck_tenant_users_theme_preference'),
    ):
        op.drop_constraint(constraint, table, type_='check')
        op.drop_column(table, 'theme_preference')
