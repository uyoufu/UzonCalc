from enum import IntEnum, StrEnum
from sqlalchemy import (
    JSON,
    Column,
    Integer,
    String,
    Boolean,
    Text,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel


class UserStatus(IntEnum):
    Deleted = 0
    Active = 1
    Forbidden_login = 2


class UserRole(StrEnum):
    Admin = "admin"
    Regular = "regular"


class User(BaseModel):
    """users table model with enhanced status and type fields"""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    salt: Mapped[str] = mapped_column(String(255), nullable=False)

    # account status (active / inactive / suspended / pending) stored as integer
    status: Mapped[int] = mapped_column(
        Integer, nullable=False, default=UserStatus.Active.value, index=True
    )
    roles: Mapped[list[str]] = mapped_column(JSON, default=[UserRole.Regular.value])
