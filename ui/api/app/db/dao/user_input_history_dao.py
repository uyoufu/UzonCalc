"""
用户输入历史数据访问层 (DAO)

提供对输入历史、缓存和版本的数据库操作。
"""

from sqlalchemy import select, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import hashlib
import logging

from app.db.models.user_input_history import (
    UserInputHistory,
    PublishedVersion,
    InputCache,
)

logger = logging.getLogger(__name__)


class UserInputHistoryDAO:
    """用户输入历史数据访问对象"""

    @staticmethod
    async def save_input_history(
        session: AsyncSession,
        user_id: str,
        file_path: str,
        func_name: str,
        session_id: str,
        input_data: Dict[str, Any],
        step_number: int,
        total_steps: int,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> UserInputHistory:
        """
        保存用户输入历史

        :param session: 数据库会话
        :param user_id: 用户 ID
        :param file_path: 文件路径
        :param func_name: 函数名称
        :param session_id: 执行会话 ID
        :param input_data: 用户输入的字段数据
        :param step_number: 步骤号
        :param total_steps: 总步骤数
        :param parameters: 初始参数
        :return: UserInputHistory 对象
        """
        # 查询或创建历史记录
        stmt = select(UserInputHistory).where(
            and_(
                UserInputHistory.user_id == user_id,
                UserInputHistory.file_path == file_path,
                UserInputHistory.func_name == func_name,
                UserInputHistory.session_id == session_id,
            )
        )
        result = await session.execute(stmt)
        history = result.scalar_one_or_none()

        if history is None:
            # 创建新的历史记录
            history = UserInputHistory(
                user_id=user_id,
                file_path=file_path,
                func_name=func_name,
                session_id=session_id,
                input_history=[],
                total_steps=total_steps,
                parameters=parameters or {},
            )
            session.add(history)
            await session.flush()

        # 添加新的输入步骤
        input_entry = {
            "step_number": step_number,
            "field_values": input_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if history.input_history is None:
            history.input_history = []

        history.input_history.append(input_entry)
        history.current_step = step_number
        history.total_steps = total_steps
        history.updated_at = datetime.utcnow()

        await session.flush()
        return history

    @staticmethod
    async def complete_execution(
        session: AsyncSession,
        user_id: str,
        file_path: str,
        func_name: str,
        session_id: str,
        final_result: str,
        execution_time: Optional[int] = None,
    ) -> UserInputHistory:
        """
        标记执行为完成

        :param session: 数据库会话
        :param user_id: 用户 ID
        :param file_path: 文件路径
        :param func_name: 函数名称
        :param session_id: 执行会话 ID
        :param final_result: 最终的 HTML 结果
        :param execution_time: 执行耗时（毫秒）
        :return: UserInputHistory 对象
        """
        stmt = select(UserInputHistory).where(
            and_(
                UserInputHistory.user_id == user_id,
                UserInputHistory.file_path == file_path,
                UserInputHistory.func_name == func_name,
                UserInputHistory.session_id == session_id,
            )
        )
        result = await session.execute(stmt)
        history = result.scalar_one()

        history.is_complete = True
        history.is_draft = True
        history.final_result = final_result
        history.final_result_hash = hashlib.sha256(final_result.encode()).hexdigest()
        history.execution_time = execution_time
        history.completed_at = datetime.utcnow()
        history.updated_at = datetime.utcnow()

        await session.flush()
        return history

    @staticmethod
    async def get_latest_history(
        session: AsyncSession,
        user_id: str,
        file_path: str,
        func_name: str,
        include_unpublished: bool = True,
    ) -> Optional[UserInputHistory]:
        """
        获取最新的输入历史

        :param session: 数据库会话
        :param user_id: 用户 ID
        :param file_path: 文件路径
        :param func_name: 函数名称
        :param include_unpublished: 是否包含未发布的历史
        :return: UserInputHistory 对象或 None
        """
        query = select(UserInputHistory).where(
            and_(
                UserInputHistory.user_id == user_id,
                UserInputHistory.file_path == file_path,
                UserInputHistory.func_name == func_name,
                UserInputHistory.is_complete == True,
            )
        )

        if not include_unpublished:
            query = query.where(UserInputHistory.is_draft == False)

        query = query.order_by(desc(UserInputHistory.updated_at)).limit(1)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_execution_history(
        session: AsyncSession,
        user_id: str,
        file_path: str,
        func_name: str,
        limit: int = 20,
    ) -> List[UserInputHistory]:
        """
        获取执行历史列表

        :param session: 数据库会话
        :param user_id: 用户 ID
        :param file_path: 文件路径
        :param func_name: 函数名称
        :param limit: 返回的最大条数
        :return: UserInputHistory 列表
        """
        stmt = (
            select(UserInputHistory)
            .where(
                and_(
                    UserInputHistory.user_id == user_id,
                    UserInputHistory.file_path == file_path,
                    UserInputHistory.func_name == func_name,
                    UserInputHistory.is_complete == True,
                )
            )
            .order_by(desc(UserInputHistory.updated_at))
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()


class PublishedVersionDAO:
    """已发布版本数据访问对象"""

    @staticmethod
    async def publish_version(
        session: AsyncSession,
        user_id: str,
        file_path: str,
        func_name: str,
        version_name: str,
        input_history: List[Dict[str, Any]],
        final_result: str,
        parameters: Optional[Dict[str, Any]],
        total_steps: int,
        execution_time: Optional[int] = None,
        description: Optional[str] = None,
        history_id: Optional[int] = None,
    ) -> PublishedVersion:
        """
        发布新版本

        :param session: 数据库会话
        :param user_id: 用户 ID
        :param file_path: 文件路径
        :param func_name: 函数名称
        :param version_name: 版本名称
        :param input_history: 完整的输入历史
        :param final_result: 最终的 HTML 结果
        :param parameters: 初始参数
        :param total_steps: 总步骤数
        :param execution_time: 执行耗时
        :param description: 版本描述
        :param history_id: 来自的历史记录 ID
        :return: PublishedVersion 对象
        """
        # 获取当前最大版本号
        stmt = (
            select(PublishedVersion)
            .where(
                and_(
                    PublishedVersion.user_id == user_id,
                    PublishedVersion.file_path == file_path,
                    PublishedVersion.func_name == func_name,
                )
            )
            .order_by(desc(PublishedVersion.version_number))
            .limit(1)
        )
        result = await session.execute(stmt)
        latest = result.scalar_one_or_none()
        next_version = (latest.version_number + 1) if latest else 1

        version = PublishedVersion(
            user_id=user_id,
            file_path=file_path,
            func_name=func_name,
            version_name=version_name,
            version_number=next_version,
            version_description=description,
            input_history=input_history,
            final_result=final_result,
            final_result_hash=hashlib.sha256(final_result.encode()).hexdigest(),
            parameters=parameters,
            total_steps=total_steps,
            execution_time=execution_time,
            created_from_history_id=history_id,
        )

        session.add(version)
        await session.flush()

        # 更新关联的历史记录
        if history_id:
            stmt = select(UserInputHistory).where(
                UserInputHistory.id == history_id
            )
            result = await session.execute(stmt)
            history = result.scalar_one_or_none()
            if history:
                history.is_draft = False
                history.draft_version_id = version.id
                await session.flush()

        return version

    @staticmethod
    async def get_published_versions(
        session: AsyncSession,
        user_id: str,
        file_path: str,
        func_name: str,
        limit: int = 10,
    ) -> List[PublishedVersion]:
        """
        获取已发布的版本列表

        :param session: 数据库会话
        :param user_id: 用户 ID
        :param file_path: 文件路径
        :param func_name: 函数名称
        :param limit: 返回的最大条数
        :return: PublishedVersion 列表
        """
        stmt = (
            select(PublishedVersion)
            .where(
                and_(
                    PublishedVersion.user_id == user_id,
                    PublishedVersion.file_path == file_path,
                    PublishedVersion.func_name == func_name,
                )
            )
            .order_by(desc(PublishedVersion.published_at))
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_version_by_name(
        session: AsyncSession,
        user_id: str,
        file_path: str,
        func_name: str,
        version_name: str,
    ) -> Optional[PublishedVersion]:
        """
        按版本名称获取版本

        :param session: 数据库会话
        :param user_id: 用户 ID
        :param file_path: 文件路径
        :param func_name: 函数名称
        :param version_name: 版本名称
        :return: PublishedVersion 对象或 None
        """
        stmt = select(PublishedVersion).where(
            and_(
                PublishedVersion.user_id == user_id,
                PublishedVersion.file_path == file_path,
                PublishedVersion.func_name == func_name,
                PublishedVersion.version_name == version_name,
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def increment_use_count(
        session: AsyncSession,
        version_id: int,
    ) -> None:
        """
        增加版本使用次数

        :param session: 数据库会话
        :param version_id: 版本 ID
        """
        stmt = select(PublishedVersion).where(PublishedVersion.id == version_id)
        result = await session.execute(stmt)
        version = result.scalar_one()

        version.use_count += 1
        version.updated_at = datetime.utcnow()
        await session.flush()


class InputCacheDAO:
    """输入缓存数据访问对象"""

    @staticmethod
    async def save_cache(
        session: AsyncSession,
        user_id: str,
        file_path: str,
        func_name: str,
        cached_input: Dict[str, Any],
        input_history_id: int,
        total_steps: int,
        completed_steps: int,
        cache_ttl_hours: int = 72,
    ) -> InputCache:
        """
        保存输入缓存

        :param session: 数据库会话
        :param user_id: 用户 ID
        :param file_path: 文件路径
        :param func_name: 函数名称
        :param cached_input: 缓存的输入数据
        :param input_history_id: 历史记录 ID
        :param total_steps: 总步骤数
        :param completed_steps: 已完成的步骤数
        :param cache_ttl_hours: 缓存过期时间（小时）
        :return: InputCache 对象
        """
        # 查找或创建缓存
        stmt = select(InputCache).where(
            and_(
                InputCache.user_id == user_id,
                InputCache.file_path == file_path,
                InputCache.func_name == func_name,
            )
        )
        result = await session.execute(stmt)
        cache = result.scalar_one_or_none()

        now = datetime.utcnow()
        expires_at = now + timedelta(hours=cache_ttl_hours)

        if cache is None:
            cache = InputCache(
                user_id=user_id,
                file_path=file_path,
                func_name=func_name,
                cached_input=cached_input,
                input_history_id=input_history_id,
                total_steps=total_steps,
                completed_steps=completed_steps,
                expires_at=expires_at,
            )
            session.add(cache)
        else:
            cache.cached_input = cached_input
            cache.input_history_id = input_history_id
            cache.total_steps = total_steps
            cache.completed_steps = completed_steps
            cache.updated_at = now
            cache.expires_at = expires_at

        await session.flush()
        return cache

    @staticmethod
    async def get_cache(
        session: AsyncSession,
        user_id: str,
        file_path: str,
        func_name: str,
    ) -> Optional[InputCache]:
        """
        获取有效的缓存

        :param session: 数据库会话
        :param user_id: 用户 ID
        :param file_path: 文件路径
        :param func_name: 函数名称
        :return: InputCache 对象或 None
        """
        stmt = select(InputCache).where(
            and_(
                InputCache.user_id == user_id,
                InputCache.file_path == file_path,
                InputCache.func_name == func_name,
                or_(
                    InputCache.expires_at == None,
                    InputCache.expires_at > datetime.utcnow(),
                ),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_expired_caches(
        session: AsyncSession,
    ) -> int:
        """
        删除已过期的缓存

        :param session: 数据库会话
        :return: 删除的缓存数量
        """
        stmt = select(InputCache).where(
            InputCache.expires_at < datetime.utcnow()
        )
        result = await session.execute(stmt)
        caches = result.scalars().all()

        for cache in caches:
            await session.delete(cache)

        await session.flush()
        return len(caches)
