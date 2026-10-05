"""add brand_color to tenants

Revision ID: 0017_tenant_brand_color
Revises: 0016_theme_preference
Create Date: 2026-09-23

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0017_tenant_brand_color'
down_revision: str | None = '0016_theme_preference'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nullable with no default: null means "inherit Orvella's own accent",
    # which is a meaningfully different state from any particular colour.
    op.add_column('tenants', sa.Column('brand_color', sa.String(length=7), nullable=True))


def downgrade() -> None:
    op.drop_column('tenants', 'brand_color')
