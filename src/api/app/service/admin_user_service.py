"""Administrator-only user listing and account maintenance services."""

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.dto_base import PaginationDTO
from app.controller.users.organization_dto import (
    AdminUserCreateDTO,
    AdminUserListFilterDTO,
    AdminUserResDTO,
)
from app.db.models.department import Department, DepartmentUser
from app.db.models.user import User, UserRole, UserStatus
from app.exception.custom_exception import raise_ex
from app.service.department_service import descendant_department_ids, get_department
from app.service.user_service import register_user, reset_password


async def count_users(filters: AdminUserListFilterDTO, session: AsyncSession) -> int:
    """Count non-deleted users matching administrator filters."""
    conditions = await _user_conditions(filters, session)
    return await session.scalar(select(func.count(User.id)).where(*conditions)) or 0


async def list_users(
    filters: AdminUserListFilterDTO,
    pagination: PaginationDTO,
    session: AsyncSession,
) -> list[AdminUserResDTO]:
    """List one stable page of managed users with department memberships."""
    conditions = await _user_conditions(filters, session)
    sort_columns = {
        "username": User.username,
        "nickName": User.nickName,
        "status": User.status,
        "createdAt": User.createdAt,
    }
    sort_column = sort_columns.get(pagination.sortBy, User.createdAt)
    order = sort_column.desc() if pagination.descending else sort_column.asc()
    users = (
        await session.scalars(
            select(User)
            .where(*conditions)
            .order_by(order, User.id.desc() if pagination.descending else User.id)
            .offset(pagination.skip)
            .limit(pagination.limit)
        )
    ).all()
    return [await _user_response(user, session) for user in users]


async def create_user(
    request: AdminUserCreateDTO, session: AsyncSession
) -> AdminUserResDTO:
    """Create a regular user and assign all requested departments."""
    departments = await _resolve_departments(request.departmentOids, session)
    user = await register_user(
        username=request.username.strip(),
        password=request.password,
        nick_name=request.nickName.strip() if request.nickName else None,
        session=session,
    )
    for department in departments:
        session.add(DepartmentUser(departmentId=department.id, userId=user.id))
    await session.commit()
    return await _user_response(user, session)


async def set_user_status(
    administrator_id: int,
    user_oid: str,
    status: UserStatus,
    session: AsyncSession,
) -> AdminUserResDTO:
    """Enable or disable one user while protecting administrator availability."""
    if status not in {UserStatus.Active, UserStatus.Forbidden_login}:
        raise_ex("Only active and disabled statuses are supported", code=400)
    user = await _get_user(user_oid, session)
    if user.id == administrator_id and status is not UserStatus.Active:
        raise_ex("Administrators cannot disable their own account", code=409)
    if UserRole.Admin.value in user.roles and status is not UserStatus.Active:
        active_admins = (
            await session.scalars(
                select(User).where(User.status == UserStatus.Active.value)
            )
        ).all()
        if (
            sum(UserRole.Admin.value in candidate.roles for candidate in active_admins)
            <= 1
        ):
            raise_ex("The last active administrator cannot be disabled", code=409)
    user.status = status.value
    await session.commit()
    return await _user_response(user, session)


async def reset_user_password(
    user_oid: str, new_password: str, session: AsyncSession
) -> None:
    """Reset a managed user's password using the existing hashing service."""
    user = await _get_user(user_oid, session)
    await reset_password(user.id, new_password, session)


async def _user_conditions(
    filters: AdminUserListFilterDTO, session: AsyncSession
) -> list:
    """Build shared user-list predicates for count and item queries."""
    conditions = [User.status != UserStatus.Deleted.value]
    if filters.query:
        pattern = f"%{filters.query.strip()}%"
        conditions.append(
            or_(User.username.ilike(pattern), User.nickName.ilike(pattern))
        )
    if filters.departmentOid:
        department = await get_department(filters.departmentOid, session)
        department_ids = await descendant_department_ids(department.id, session)
        member_ids = select(DepartmentUser.userId).where(
            DepartmentUser.departmentId.in_(department_ids)
        )
        conditions.append(User.id.in_(member_ids))
    return conditions


async def _get_user(user_oid: str, session: AsyncSession) -> User:
    """Load one non-deleted user by public identifier."""
    user = await session.scalar(
        select(User).where(
            User.oid == user_oid, User.status != UserStatus.Deleted.value
        )
    )
    if user is None:
        raise_ex("User not found", code=404)
    return user


async def _resolve_departments(
    department_oids: list[str], session: AsyncSession
) -> list[Department]:
    """Resolve unique active department OIDs for user assignment."""
    if len(department_oids) != len(set(department_oids)):
        raise_ex("Department identifiers must be unique", code=400)
    departments = []
    for department_oid in department_oids:
        departments.append(await get_department(department_oid, session))
    return departments


async def _user_response(user: User, session: AsyncSession) -> AdminUserResDTO:
    """Convert a user model and memberships to the administrator response."""
    department_oids = list(
        await session.scalars(
            select(Department.oid)
            .join(DepartmentUser, DepartmentUser.departmentId == Department.id)
            .where(DepartmentUser.userId == user.id, Department.deletedAt.is_(None))
            .order_by(Department.sortOrder, Department.id)
        )
    )
    return AdminUserResDTO(
        userOid=user.oid,
        username=user.username,
        nickName=user.nickName,
        avatar=user.avatar,
        roles=list(user.roles),
        status=UserStatus(user.status),
        departmentOids=department_oids,
        createdAt=user.createdAt,
    )
