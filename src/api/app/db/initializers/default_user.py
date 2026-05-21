from sqlalchemy import select

from app.db.models.user import UserRole
from app.service.user_service import register_user
from .base import BaseInitializer
from config import logger, app_config
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import User


class InitDefaultUser(BaseInitializer):
    async def initialize(self, session: AsyncSession):
        # 判断是否存在默认用户
        user = await session.scalar(
            select(User).where(User.username == app_config.default_userId)
        )
        if user:
            logger.info("Default user already exists, skipping creation.")
            return

        # 创建默认用户
        await register_user(
            username=app_config.default_userId,
            password=app_config.default_password,
            session=session,
            roles=[UserRole.Admin.value],  # 默认用户为管理员
        )
