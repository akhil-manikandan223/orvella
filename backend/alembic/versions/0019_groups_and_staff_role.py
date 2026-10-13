"""create group tables and allow the 'staff' tenant-user role

Revision ID: 0019_groups_and_staff_role
Revises: 0018_attendance_records
Create Date: 2026-10-13

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0019_groups_and_staff_role'
down_revision: str | None = '0018_attendance_records'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'groups',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('department_id', sa.Uuid(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        # SET NULL, not CASCADE: reorganising departments must not delete the
        # groups - and with them the attendance scope - hanging off them.
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_groups_tenant_name'),
    )
    op.create_index(op.f('ix_groups_tenant_id'), 'groups', ['tenant_id'])

    op.create_table(
        'group_members',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('group_id', sa.Uuid(), nullable=False),
        sa.Column('person_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['person_id'], ['people.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'person_id', name='uq_group_members_group_person'),
    )
    op.create_index(op.f('ix_group_members_group_id'), 'group_members', ['group_id'])
    op.create_index(op.f('ix_group_members_person_id'), 'group_members', ['person_id'])

    op.create_table(
        'group_supervisors',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('group_id', sa.Uuid(), nullable=False),
        sa.Column('tenant_user_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_user_id'], ['tenant_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'group_id', 'tenant_user_id', name='uq_group_supervisors_group_user'
        ),
    )
    op.create_index(op.f('ix_group_supervisors_group_id'), 'group_supervisors', ['group_id'])
    op.create_index(
        op.f('ix_group_supervisors_tenant_user_id'), 'group_supervisors', ['tenant_user_id']
    )

    # 'staff' is the homeroom-teacher role added alongside these tables. The
    # check constraint has to be recreated - Postgres has no ALTER CHECK.
    op.drop_constraint('ck_tenant_users_role', 'tenant_users', type_='check')
    op.create_check_constraint(
        'ck_tenant_users_role', 'tenant_users', "role IN ('admin', 'staff', 'member')"
    )


def downgrade() -> None:
    # Any existing staff user would violate the narrower constraint, so demote
    # them first - 'member' keeps their read access and drops the ability to
    # mark attendance, which is the safe direction.
    op.execute("UPDATE tenant_users SET role = 'member' WHERE role = 'staff'")
    op.drop_constraint('ck_tenant_users_role', 'tenant_users', type_='check')
    op.create_check_constraint(
        'ck_tenant_users_role', 'tenant_users', "role IN ('admin', 'member')"
    )

    op.drop_index(op.f('ix_group_supervisors_tenant_user_id'), table_name='group_supervisors')
    op.drop_index(op.f('ix_group_supervisors_group_id'), table_name='group_supervisors')
    op.drop_table('group_supervisors')
    op.drop_index(op.f('ix_group_members_person_id'), table_name='group_members')
    op.drop_index(op.f('ix_group_members_group_id'), table_name='group_members')
    op.drop_table('group_members')
    op.drop_index(op.f('ix_groups_tenant_id'), table_name='groups')
    op.drop_table('groups')
