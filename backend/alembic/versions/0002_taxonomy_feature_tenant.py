"""create organization taxonomy, feature catalog, and tenant tables

Revision ID: 0002_taxonomy_feature_tenant
Revises: 0001_create_platform_admins
Create Date: 2026-08-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0002_taxonomy_feature_tenant'
down_revision: str | None = '0001_create_platform_admins'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'organization_categories',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('slug', sa.String(length=150), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_organization_categories')),
    )
    op.create_index(
        op.f('ix_organization_categories_slug'), 'organization_categories', ['slug'], unique=True
    )

    op.create_table(
        'features',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("status IN ('active', 'deprecated')", name=op.f('ck_features_status')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_features')),
    )
    op.create_index(op.f('ix_features_key'), 'features', ['key'], unique=True)

    op.create_table(
        'organization_types',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_category_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('slug', sa.String(length=150), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['organization_category_id'],
            ['organization_categories.id'],
            name=op.f('fk_organization_types_organization_category_id_organization_categories'),
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_organization_types')),
        sa.UniqueConstraint(
            'organization_category_id',
            'slug',
            name=op.f('uq_organization_types_organization_category_id'),
        ),
    )
    op.create_index(
        op.f('ix_organization_types_organization_category_id'),
        'organization_types',
        ['organization_category_id'],
    )

    op.create_table(
        'organization_type_feature_templates',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_type_id', sa.Uuid(), nullable=False),
        sa.Column('feature_id', sa.Uuid(), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['organization_type_id'],
            ['organization_types.id'],
            name=op.f(
                'fk_organization_type_feature_templates_organization_type_id_organization_types'
            ),
        ),
        sa.ForeignKeyConstraint(
            ['feature_id'],
            ['features.id'],
            name=op.f('fk_organization_type_feature_templates_feature_id_features'),
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_organization_type_feature_templates')),
        sa.UniqueConstraint(
            'organization_type_id',
            'feature_id',
            name=op.f('uq_organization_type_feature_templates_organization_type_id'),
        ),
    )
    op.create_index(
        op.f('ix_organization_type_feature_templates_organization_type_id'),
        'organization_type_feature_templates',
        ['organization_type_id'],
    )
    op.create_index(
        op.f('ix_organization_type_feature_templates_feature_id'),
        'organization_type_feature_templates',
        ['feature_id'],
    )

    op.create_table(
        'tenants',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=63), nullable=False),
        sa.Column('organization_type_id', sa.Uuid(), nullable=False),
        sa.Column('max_users', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint('max_users IS NULL OR max_users > 0', name=op.f('ck_tenants_max_users')),
        sa.ForeignKeyConstraint(
            ['organization_type_id'],
            ['organization_types.id'],
            name=op.f('fk_tenants_organization_type_id_organization_types'),
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_tenants')),
    )
    op.create_index(op.f('ix_tenants_slug'), 'tenants', ['slug'], unique=True)
    op.create_index(op.f('ix_tenants_organization_type_id'), 'tenants', ['organization_type_id'])

    op.create_table(
        'tenant_features',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('feature_id', sa.Uuid(), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('configuration', sa.JSON(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id'], ['tenants.id'], name=op.f('fk_tenant_features_tenant_id_tenants')
        ),
        sa.ForeignKeyConstraint(
            ['feature_id'], ['features.id'], name=op.f('fk_tenant_features_feature_id_features')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_tenant_features')),
        sa.UniqueConstraint('tenant_id', 'feature_id', name=op.f('uq_tenant_features_tenant_id')),
    )
    op.create_index(op.f('ix_tenant_features_tenant_id'), 'tenant_features', ['tenant_id'])
    op.create_index(op.f('ix_tenant_features_feature_id'), 'tenant_features', ['feature_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_tenant_features_feature_id'), table_name='tenant_features')
    op.drop_index(op.f('ix_tenant_features_tenant_id'), table_name='tenant_features')
    op.drop_table('tenant_features')

    op.drop_index(op.f('ix_tenants_organization_type_id'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_slug'), table_name='tenants')
    op.drop_table('tenants')

    op.drop_index(
        op.f('ix_organization_type_feature_templates_feature_id'),
        table_name='organization_type_feature_templates',
    )
    op.drop_index(
        op.f('ix_organization_type_feature_templates_organization_type_id'),
        table_name='organization_type_feature_templates',
    )
    op.drop_table('organization_type_feature_templates')

    op.drop_index(
        op.f('ix_organization_types_organization_category_id'), table_name='organization_types'
    )
    op.drop_table('organization_types')

    op.drop_index(op.f('ix_features_key'), table_name='features')
    op.drop_table('features')

    op.drop_index(op.f('ix_organization_categories_slug'), table_name='organization_categories')
    op.drop_table('organization_categories')
