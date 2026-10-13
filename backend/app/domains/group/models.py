import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Group(Base):
    """A set of people with someone responsible for them.

    Deliberately not called 'Class': the same primitive is a school's
    Grade 10-A, a gym's training batch, a hospital ward or an office team.
    Keeping it generic is what stops Orvella becoming a school product
    (see ORVELLA_PROJECT_PLAN.md #17: no industry-specific behavior in the
    core platform where configuration will do).

    Distinct from Department: a college student belongs to a department
    (Commerce) AND a section (B.Com 2A), and only the latter has a homeroom
    teacher. department_id links the two when it's useful, nothing more.
    """

    __tablename__ = 'groups'
    __table_args__ = (UniqueConstraint('tenant_id', 'name', name='uq_groups_tenant_name'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('tenants.id'), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # SET NULL, like Person's: departments get reorganised, and that must not
    # delete the groups hanging off them.
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('departments.id', ondelete='SET NULL'), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class GroupMember(Base):
    """A person's membership of a group."""

    __tablename__ = 'group_members'
    __table_args__ = (
        UniqueConstraint('group_id', 'person_id', name='uq_group_members_group_person'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('groups.id', ondelete='CASCADE'), index=True, nullable=False
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('people.id', ondelete='CASCADE'), index=True, nullable=False
    )


class GroupSupervisor(Base):
    """A tenant user responsible for a group - the homeroom teacher.

    This is the row the attendance scope is derived from: a non-admin may
    only mark the people in groups they appear here for.
    """

    __tablename__ = 'group_supervisors'
    __table_args__ = (
        UniqueConstraint('group_id', 'tenant_user_id', name='uq_group_supervisors_group_user'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('groups.id', ondelete='CASCADE'), index=True, nullable=False
    )
    tenant_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('tenant_users.id', ondelete='CASCADE'),
        index=True,
        nullable=False,
    )
