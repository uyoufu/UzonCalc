"""DTOs for department trees and administrator user management."""

import datetime

from pydantic import Field

from app.controller.dto_base import BaseDTO
from app.db.models.user import UserStatus


class DepartmentCreateDTO(BaseDTO):
    """Create one department beneath an optional parent."""

    name: str = Field(min_length=1, max_length=100)
    parentOid: str | None = None


class DepartmentUpdateDTO(BaseDTO):
    """Update one department's display name."""

    name: str = Field(min_length=1, max_length=100)


class DepartmentMoveDTO(BaseDTO):
    """Move one department beneath a parent at a sibling position."""

    parentOid: str | None = None
    sortOrder: int = Field(ge=0)


class DepartmentResDTO(BaseDTO):
    """Return one flat department-tree node."""

    departmentOid: str
    parentOid: str | None
    name: str
    sortOrder: int
    createdAt: datetime.datetime
    updatedAt: datetime.datetime


class AdminUserCreateDTO(BaseDTO):
    """Create one managed user with initial department memberships."""

    username: str = Field(min_length=1, max_length=50)
    nickName: str | None = Field(default=None, max_length=50)
    password: str = Field(min_length=1)
    departmentOids: list[str] = Field(default_factory=list)


class AdminUserListFilterDTO(BaseDTO):
    """Filter managed users by text and department subtree."""

    query: str | None = None
    departmentOid: str | None = None


class AdminUserStatusDTO(BaseDTO):
    """Enable or disable one managed user."""

    status: UserStatus


class AdminUserResetPasswordDTO(BaseDTO):
    """Replace one managed user's password hash input."""

    newPassword: str = Field(min_length=1)


class AdminUserResDTO(BaseDTO):
    """Return one managed user and all direct department memberships."""

    userOid: str
    username: str
    nickName: str | None
    avatar: str | None
    roles: list[str]
    status: UserStatus
    departmentOids: list[str]
    createdAt: datetime.datetime
