"""Administrator HTTP endpoints for managed user accounts."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.depends import get_session, require_server_admin
from app.controller.dto_base import PaginationDTO
from app.controller.users.organization_dto import (
    AdminUserCreateDTO,
    AdminUserListFilterDTO,
    AdminUserResDTO,
    AdminUserResetPasswordDTO,
    AdminUserStatusDTO,
)
from app.db.models.user import User
from app.response.response_result import ResponseResult, ok
from app.service import admin_user_service

router = APIRouter(prefix="/v1/admin/users", tags=["admin-users"])


@router.get("/count")
async def count_users(
    filters: Annotated[AdminUserListFilterDTO, Depends()],
    _admin: User = Depends(require_server_admin),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[int]:
    """Count managed users matching the supplied filters."""
    return ok(data=await admin_user_service.count_users(filters, session))


@router.get("/items")
async def list_users(
    filters: Annotated[AdminUserListFilterDTO, Depends()],
    pagination: Annotated[PaginationDTO, Depends()],
    _admin: User = Depends(require_server_admin),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[list[AdminUserResDTO]]:
    """List one page of managed users."""
    return ok(data=await admin_user_service.list_users(filters, pagination, session))


@router.post("")
async def create_user(
    request: AdminUserCreateDTO,
    _admin: User = Depends(require_server_admin),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[AdminUserResDTO]:
    """Create one regular managed user."""
    return ok(data=await admin_user_service.create_user(request, session))


@router.put("/{userOid}/status")
async def set_user_status(
    userOid: str,
    request: AdminUserStatusDTO,
    admin: User = Depends(require_server_admin),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[AdminUserResDTO]:
    """Enable or disable one managed user."""
    return ok(
        data=await admin_user_service.set_user_status(
            admin.id, userOid, request.status, session
        )
    )


@router.post("/{userOid}/reset-password")
async def reset_user_password(
    userOid: str,
    request: AdminUserResetPasswordDTO,
    _admin: User = Depends(require_server_admin),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    """Reset one managed user's password."""
    await admin_user_service.reset_user_password(userOid, request.newPassword, session)
    return ok()
