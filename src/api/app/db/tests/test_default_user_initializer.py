"""Regression tests for configurable default organization initialization."""

import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.initializers.default_user import InitDefaultUser
from app.db.models import BaseModel, Department, DepartmentUser, User
from app.db.models.user import UserRole
from config import app_config
from utils.password_helper import verify_password


def test_default_user_initializer_creates_idempotent_organization_seed() -> None:
    """The fresh-database initializer should create one complete default seed."""

    async def run_test() -> None:
        """Initialize twice and verify departments, users, roles, and membership."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        try:
            async with engine.begin() as connection:
                await connection.run_sync(BaseModel.metadata.create_all)
            session_factory = async_sessionmaker(engine, expire_on_commit=False)
            async with session_factory() as session:
                initializer = InitDefaultUser()
                await initializer.initialize(session)
                await initializer.initialize(session)

                departments = list(await session.scalars(select(Department)))
                users = list(await session.scalars(select(User).order_by(User.username)))
                membership_count = await session.scalar(
                    select(func.count()).select_from(DepartmentUser)
                )

                assert len(departments) == 1
                assert departments[0].name == app_config.default_department_name
                assert departments[0].parentId is None
                assert departments[0].sortOrder == 0
                assert [user.username for user in users] == sorted(
                    [app_config.default_userId, app_config.default_regular_userId]
                )
                assert membership_count == 2

                administrator = next(
                    user
                    for user in users
                    if user.username == app_config.default_userId
                )
                regular_user = next(
                    user
                    for user in users
                    if user.username == app_config.default_regular_userId
                )
                assert administrator.roles == [UserRole.Admin.value]
                assert regular_user.roles == [UserRole.Regular.value]
                assert verify_password(
                    app_config.default_password,
                    administrator.password,
                    administrator.salt,
                )
                assert verify_password(
                    app_config.default_regular_password,
                    regular_user.password,
                    regular_user.salt,
                )
        finally:
            await engine.dispose()

    asyncio.run(run_test())
