"""create attendance_records table

Revision ID: 0018_attendance_records
Revises: 0017_tenant_brand_color
Create Date: 2026-10-13

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0018_attendance_records'
down_revision: str | None = '0017_tenant_brand_color'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'attendance_records',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('person_id', sa.Uuid(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('present', 'absent', 'late', 'excused')",
            name=op.f('ck_attendance_records_status'),
        ),
        sa.ForeignKeyConstraint(
            ['tenant_id'], ['tenants.id'], name=op.f('fk_attendance_records_tenant_id_tenants')
        ),
        # CASCADE: attendance is meaningless without the person it belongs to,
        # unlike a department reference which is just an association.
        sa.ForeignKeyConstraint(
            ['person_id'],
            ['people.id'],
            name=op.f('fk_attendance_records_person_id_people'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_attendance_records')),
        sa.UniqueConstraint('person_id', 'date', name='uq_attendance_records_person_date'),
    )
    op.create_index(op.f('ix_attendance_records_tenant_id'), 'attendance_records', ['tenant_id'])
    op.create_index(op.f('ix_attendance_records_person_id'), 'attendance_records', ['person_id'])
    op.create_index(op.f('ix_attendance_records_date'), 'attendance_records', ['date'])


def downgrade() -> None:
    op.drop_index(op.f('ix_attendance_records_date'), table_name='attendance_records')
    op.drop_index(op.f('ix_attendance_records_person_id'), table_name='attendance_records')
    op.drop_index(op.f('ix_attendance_records_tenant_id'), table_name='attendance_records')
    op.drop_table('attendance_records')
