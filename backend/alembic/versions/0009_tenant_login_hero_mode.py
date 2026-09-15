"""add tenants.login_hero_mode

Revision ID: 0009_tenant_login_hero_mode
Revises: 0008_tenant_users
Create Date: 2026-09-15

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0009_tenant_login_hero_mode'
down_revision: str | None = '0008_tenant_users'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'tenants',
        sa.Column(
            'login_hero_mode',
            sa.String(length=20),
            nullable=False,
            server_default='default',
        ),
    )
    op.create_check_constraint(
        'ck_tenants_login_hero_mode',
        'tenants',
        "login_hero_mode IN ('default', 'featured')",
    )


def downgrade() -> None:
    op.drop_constraint('ck_tenants_login_hero_mode', 'tenants', type_='check')
    op.drop_column('tenants', 'login_hero_mode')
