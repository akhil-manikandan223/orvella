"""create refresh_tokens table

Revision ID: 0011_refresh_tokens
Revises: 0010_tenant_user_roles
Create Date: 2026-09-16

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0011_refresh_tokens'
down_revision: str | None = '0010_tenant_user_roles'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('subject_type', sa.String(length=20), nullable=False),
        sa.Column('subject_id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=True),
        sa.Column(
            'issued_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('replaced_by_id', sa.Uuid(), nullable=True),
        sa.CheckConstraint(
            "subject_type IN ('platform_admin', 'tenant_user')",
            name=op.f('ck_refresh_tokens_subject_type'),
        ),
        sa.ForeignKeyConstraint(
            ['replaced_by_id'],
            ['refresh_tokens.id'],
            name=op.f('fk_refresh_tokens_replaced_by_id_refresh_tokens'),
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_refresh_tokens')),
        sa.UniqueConstraint('token_hash', name=op.f('uq_refresh_tokens_token_hash')),
    )
    op.create_index(
        op.f('ix_refresh_tokens_subject_type'), 'refresh_tokens', ['subject_type']
    )
    op.create_index(op.f('ix_refresh_tokens_subject_id'), 'refresh_tokens', ['subject_id'])
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'])


def downgrade() -> None:
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_subject_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_subject_type'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
