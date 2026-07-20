"""Department tree and user-membership table definitions."""

import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, BaseModel


class Department(BaseModel):
    """Persist one node in the organization department tree."""

    __tablename__ = "department"
    __table_args__ = (
        Index(
            "uq_department_active_root_name",
            "name",
            unique=True,
            sqlite_where=text('"parentId" IS NULL AND "deletedAt" IS NULL'),
            postgresql_where=text('"parentId" IS NULL AND "deletedAt" IS NULL'),
        ),
        Index(
            "uq_department_active_parent_name",
            "parentId",
            "name",
            unique=True,
            sqlite_where=text('"parentId" IS NOT NULL AND "deletedAt" IS NULL'),
            postgresql_where=text('"parentId" IS NOT NULL AND "deletedAt" IS NULL'),
        ),
        Index("ix_department_parent_sort", "parentId", "sortOrder"),
    )

    parentId: Mapped[int | None] = mapped_column(
        ForeignKey("department.id", ondelete="RESTRICT"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sortOrder: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    updatedAt: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    deletedAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class DepartmentUser(Base):
    """Associate one user with one of their departments."""

    __tablename__ = "department_user"

    departmentId: Mapped[int] = mapped_column(
        ForeignKey("department.id", ondelete="CASCADE"), primary_key=True
    )
    userId: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
