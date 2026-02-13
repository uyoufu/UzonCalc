"""
用户设置服务层
负责用户设置的业务逻辑处理
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.user_setting import UserSetting
from app.exception.custom_exception import raise_ex
from config import logger


async def _get_user_setting_model(
    user_id: int, key: str, session: AsyncSession
) -> Optional[UserSetting]:
    """
    根据 key 获取用户设置模型对象（内部使用）

    :param user_id: 用户 ID
    :param key: 设置键名
    :param session: 数据库会话
    :return: 用户设置对象，如果不存在返回 None
    """
    result = await session.execute(
        select(UserSetting).where(
            (UserSetting.userId == user_id) & (UserSetting.key == key)
        )
    )
    setting = result.scalars().first()
    return setting


async def get_user_setting(
    user_id: int, key: str, session: AsyncSession
) -> Optional[dict]:
    """
    根据 key 获取用户设置的 value

    :param user_id: 用户 ID
    :param key: 设置键名
    :param session: 数据库会话
    :return: 设置值（JSON 格式），如果不存在返回 None
    """
    setting = await _get_user_setting_model(user_id, key, session)
    if setting:
        return setting.value
    return None


async def upsert_user_setting(
    user_id: int,
    key: str,
    value: dict,
    description: Optional[str],
    session: AsyncSession,
) -> dict:
    """
    更新用户设置，如果不存在则创建（Upsert）

    :param user_id: 用户 ID
    :param key: 设置键名
    :param value: 设置值（JSON 格式）
    :param description: 设置描述
    :param session: 数据库会话
    :return: 设置值（JSON 格式）
    """
    setting = await _get_user_setting_model(user_id, key, session)

    if setting:
        # 更新现有设置
        setting.value = value
        if description is not None:
            setting.description = description
        await session.commit()
        await session.refresh(setting)
        logger.info(f"更新用户设置: userId={user_id}, key={key}")
    else:
        # 创建新设置
        setting = UserSetting(
            userId=user_id, key=key, value=value, description=description
        )
        session.add(setting)
        await session.commit()
        await session.refresh(setting)
        logger.info(f"创建用户设置: userId={user_id}, key={key}")

    return setting.value


async def delete_user_setting(user_id: int, key: str, session: AsyncSession) -> None:
    """
    删除用户设置

    :param user_id: 用户 ID
    :param key: 设置键名
    :param session: 数据库会话
    """
    setting = await _get_user_setting_model(user_id, key, session)

    if not setting:
        raise_ex(f"User setting with key '{key}' not found", code=404)

    await session.delete(setting)
    await session.commit()
    logger.info(f"删除用户设置: userId={user_id}, key={key}")
