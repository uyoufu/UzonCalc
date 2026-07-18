"""Department-tree persistence and validation services."""

import datetime
from typing import cast

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.users.organization_dto import (
    DepartmentCreateDTO,
    DepartmentMoveDTO,
    DepartmentResDTO,
    DepartmentUpdateDTO,
)
from app.db.models.department import Department, DepartmentUser
from app.exception.custom_exception import raise_ex


async def list_departments(session: AsyncSession) -> list[DepartmentResDTO]:
    """List every active department as flat parent-linked nodes."""
    departments = (
        await session.scalars(
            select(Department)
            .where(Department.deletedAt.is_(None))
            .order_by(Department.parentId, Department.sortOrder, Department.id)
        )
    ).all()
    parent_oids = {department.id: department.oid for department in departments}
    return [
        _department_response(department, parent_oids.get(department.parentId))
        for department in departments
    ]


async def create_department(
    request: DepartmentCreateDTO, session: AsyncSession
) -> DepartmentResDTO:
    """Create a department at the end of the selected sibling group."""
    parent = await _optional_department(request.parentOid, session)
    await _ensure_unique_sibling_name(
        parent.id if parent else None, request.name, None, session
    )
    maximum = await session.scalar(
        select(func.max(Department.sortOrder)).where(
            _parent_condition(parent.id if parent else None),
            Department.deletedAt.is_(None),
        )
    )
    department = Department(
        parentId=parent.id if parent else None,
        name=request.name.strip(),
        sortOrder=(maximum or 0) + 1,
    )
    session.add(department)
    await session.commit()
    await session.refresh(department)
    return _department_response(department, parent.oid if parent else None)


async def update_department(
    department_oid: str, request: DepartmentUpdateDTO, session: AsyncSession
) -> DepartmentResDTO:
    """Rename one department without changing its tree position."""
    department = await get_department(department_oid, session)
    await _ensure_unique_sibling_name(
        department.parentId, request.name, department.id, session
    )
    department.name = request.name.strip()
    await session.commit()
    parent = await session.get(Department, department.parentId)
    return _department_response(department, parent.oid if parent else None)


async def move_department(
    department_oid: str, request: DepartmentMoveDTO, session: AsyncSession
) -> DepartmentResDTO:
    """Move a department while rejecting self-parenting and descendant cycles."""
    department = await get_department(department_oid, session)
    parent = await _optional_department(request.parentOid, session)
    if parent is not None:
        ancestor = parent
        while ancestor is not None:
            if ancestor.id == department.id:
                raise_ex("Department move would create a cycle", code=409)
            ancestor = await session.get(Department, ancestor.parentId)
    await _ensure_unique_sibling_name(
        parent.id if parent else None, department.name, department.id, session
    )
    department.parentId = parent.id if parent else None
    department.sortOrder = request.sortOrder
    await session.commit()
    return _department_response(department, parent.oid if parent else None)


async def delete_department(department_oid: str, session: AsyncSession) -> None:
    """Soft-delete one empty leaf department."""
    department = await get_department(department_oid, session)
    child_count = await session.scalar(
        select(func.count(Department.id)).where(
            Department.parentId == department.id, Department.deletedAt.is_(None)
        )
    )
    member_count = await session.scalar(
        select(func.count())
        .select_from(DepartmentUser)
        .where(DepartmentUser.departmentId == department.id)
    )
    if child_count or member_count:
        raise_ex("Department must be empty before deletion", code=409)
    department.deletedAt = datetime.datetime.now(datetime.timezone.utc)
    await session.commit()


async def get_department(department_oid: str, session: AsyncSession) -> Department:
    """Load one active department by public identifier."""
    department = await session.scalar(
        select(Department).where(
            Department.oid == department_oid, Department.deletedAt.is_(None)
        )
    )
    if department is None:
        raise_ex("Department not found", code=404)
    return cast(Department, department)


async def descendant_department_ids(
    department_id: int, session: AsyncSession
) -> set[int]:
    """Return one department and all active descendants without dialect-specific SQL."""
    departments = (
        await session.scalars(select(Department).where(Department.deletedAt.is_(None)))
    ).all()
    children: dict[int | None, list[int]] = {}
    for department in departments:
        children.setdefault(department.parentId, []).append(department.id)
    result: set[int] = set()
    pending = [department_id]
    while pending:
        current = pending.pop()
        if current in result:
            continue
        result.add(current)
        pending.extend(children.get(current, []))
    return result


async def _optional_department(
    department_oid: str | None, session: AsyncSession
) -> Department | None:
    """Resolve an optional department public identifier."""
    if department_oid is None:
        return None
    return await get_department(department_oid, session)


async def _ensure_unique_sibling_name(
    parent_id: int | None,
    name: str,
    excluded_id: int | None,
    session: AsyncSession,
) -> None:
    """Reject an active duplicate name in one sibling group."""
    conditions = [
        _parent_condition(parent_id),
        Department.name == name.strip(),
        Department.deletedAt.is_(None),
    ]
    if excluded_id is not None:
        conditions.append(Department.id != excluded_id)
    if await session.scalar(select(Department.id).where(*conditions)) is not None:
        raise_ex("Department name already exists under this parent", code=409)


def _parent_condition(parent_id: int | None):
    """Return a SQL predicate matching one nullable parent identifier."""
    return (
        Department.parentId.is_(None)
        if parent_id is None
        else Department.parentId == parent_id
    )


def _department_response(
    department: Department, parent_oid: str | None
) -> DepartmentResDTO:
    """Convert a department model to its public response."""
    return DepartmentResDTO(
        departmentOid=department.oid,
        parentOid=parent_oid,
        name=department.name,
        sortOrder=department.sortOrder,
        createdAt=department.createdAt,
        updatedAt=department.updatedAt,
    )
