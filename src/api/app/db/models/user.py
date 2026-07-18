"""User account table definitions."""

from enum import IntEnum, StrEnum

from sqlalchemy import CheckConstraint, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class UserStatus(IntEnum):
    """Describe whether a user may access the application."""

    Deleted = 0
    Active = 1
    Forbidden_login = 2


class UserRole(StrEnum):
    """Identify application roles assigned to a user."""

    Admin = "admin"
    Regular = "regular"


class User(BaseModel):
    """Persist authentication and profile information for an application user."""

    __tablename__ = "users"
    __table_args__ = (CheckConstraint("status IN (0, 1, 2)", name="status_values"),)

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nickName: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    salt: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[int] = mapped_column(
        nullable=False,
        default=UserStatus.Active.value,
        server_default=str(UserStatus.Active.value),
    )
    roles: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: [UserRole.Regular.value],
    )
