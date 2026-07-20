"""Initialize the configurable default department and user accounts."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Department, DepartmentUser, User
from app.db.models.user import UserRole
from app.service.user_service import register_user
from config import app_config, logger

from .base import BaseInitializer


class InitDefaultUser(BaseInitializer):
    """Create the initial department, administrator, and regular user."""

    async def initialize(self, session: AsyncSession) -> None:
        """Ensure the complete default organization seed exists.

        Args:
            session: Database session used to query and create seed records.

        Returns:
            None.

        Raises:
            SQLAlchemyError: If a database operation fails.
        """
        department = await self._get_or_create_default_department(session)
        administrator = await self._get_or_create_default_user(
            username=app_config.default_userId,
            password=app_config.default_password,
            roles=[UserRole.Admin.value],
            session=session,
        )
        regular_user = await self._get_or_create_default_user(
            username=app_config.default_regular_userId,
            password=app_config.default_regular_password,
            roles=[UserRole.Regular.value],
            session=session,
        )
        await self._ensure_department_membership(department, administrator, session)
        await self._ensure_department_membership(department, regular_user, session)
        await session.commit()

    @staticmethod
    async def _get_or_create_default_department(
        session: AsyncSession,
    ) -> Department:
        """Return the active default root department, creating it when absent.

        Args:
            session: Database session used to query and create the department.

        Returns:
            Active default root department.

        Raises:
            SQLAlchemyError: If a database operation fails.
        """
        department = await session.scalar(
            select(Department).where(
                Department.parentId.is_(None),
                Department.name == app_config.default_department_name,
                Department.deletedAt.is_(None),
            )
        )
        if department is not None:
            return department
        department = Department(
            parentId=None,
            name=app_config.default_department_name,
            sortOrder=0,
        )
        session.add(department)
        await session.flush()
        logger.info("Created default department: %s", department.name)
        return department

    @staticmethod
    async def _get_or_create_default_user(
        *,
        username: str,
        password: str,
        roles: list[str],
        session: AsyncSession,
    ) -> User:
        """Return a configured default user, creating it when absent.

        Args:
            username: Configured login identifier.
            password: Pre-hashed configured password accepted by registration.
            roles: Roles assigned only when the user must be created.
            session: Database session used to query and create the user.

        Returns:
            Existing or newly registered user.

        Raises:
            SQLAlchemyError: If a database operation fails.
        """
        user = await session.scalar(select(User).where(User.username == username))
        if user is not None:
            logger.info("Default user already exists: %s", username)
            return user
        return await register_user(
            username=username,
            password=password,
            session=session,
            roles=roles,
        )

    @staticmethod
    async def _ensure_department_membership(
        department: Department,
        user: User,
        session: AsyncSession,
    ) -> None:
        """Ensure one default user belongs to the default department.

        Args:
            department: Default department receiving the user.
            user: Administrator or regular user to assign.
            session: Database session used to query and create membership.

        Returns:
            None.

        Raises:
            SQLAlchemyError: If a database operation fails.
        """
        membership = await session.scalar(
            select(DepartmentUser).where(
                DepartmentUser.departmentId == department.id,
                DepartmentUser.userId == user.id,
            )
        )
        if membership is None:
            session.add(
                DepartmentUser(departmentId=department.id, userId=user.id)
            )
