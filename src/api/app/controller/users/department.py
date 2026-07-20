"""Administrator HTTP endpoints for the department tree."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.depends import get_session, require_server_admin
from app.controller.users.organization_dto import (
    DepartmentCreateDTO,
    DepartmentMoveDTO,
    DepartmentResDTO,
    DepartmentUpdateDTO,
)
from app.db.models.user import User
from app.response.response_result import ResponseResult, ok
from app.service import department_service

router = APIRouter(prefix="/v1/admin/departments", tags=["admin-departments"])


@router.get("")
async def list_departments(
    _admin: User = Depends(require_server_admin),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[list[DepartmentResDTO]]:
    """List the active flat department tree."""
    return ok(data=await department_service.list_departments(session))


@router.post("")
async def create_department(
    request: DepartmentCreateDTO,
    _admin: User = Depends(require_server_admin),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[DepartmentResDTO]:
    """Create one department tree node."""
    return ok(data=await department_service.create_department(request, session))


@router.put("/{departmentOid}")
async def update_department(
    departmentOid: str,
    request: DepartmentUpdateDTO,
    _admin: User = Depends(require_server_admin),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[DepartmentResDTO]:
    """Rename one department tree node."""
    return ok(
        data=await department_service.update_department(departmentOid, request, session)
    )


@router.put("/{departmentOid}/position")
async def move_department(
    departmentOid: str,
    request: DepartmentMoveDTO,
    _admin: User = Depends(require_server_admin),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[DepartmentResDTO]:
    """Move one department tree node."""
    return ok(
        data=await department_service.move_department(departmentOid, request, session)
    )


@router.delete("/{departmentOid}")
async def delete_department(
    departmentOid: str,
    _admin: User = Depends(require_server_admin),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    """Delete one empty leaf department."""
    await department_service.delete_department(departmentOid, session)
    return ok()
