"""
计算执行服务

API 层使用此服务与沙箱交互。
屏蔽沙箱通信的细节。
同时管理用户输入历史和版本控制。
"""

import logging
from typing import Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.sandbox.client import get_sandbox_client
from app.db.dao.user_input_history_dao import (
    UserInputHistoryDAO,
    PublishedVersionDAO,
    InputCacheDAO,
)

logger = logging.getLogger(__name__)


class CalcExecutionService:
    """
    计算执行服务
    
    API 层的主要接口，负责：
    1. 与沙箱通信
    2. 管理执行会话
    3. 保存和管理用户输入历史
    4. 处理版本控制和缓存
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.sandbox_client = get_sandbox_client()
        self.db_session = db_session

    async def start_execution(
        self,
        user_id: str,
        file_path: str,
        func_name: str,
        session_id: str,
        params: dict[str, Any],
        load_from_cache: bool = True,
    ) -> dict:
        """
        启动计算执行

        先检查缓存的用户输入，如果存在则直接使用缓存的数据，
        否则从头开始执行。

        Args:
            user_id: 用户 ID
            file_path: 计算文件路径
            func_name: 计算函数名
            session_id: 会话 ID
            params: 传递给函数的参数
            load_from_cache: 是否加载缓存的输入

        Returns:
            执行结果字典，包含 status、session_id、ui/result/error 等
        """
        logger.info(
            f"Starting execution: user={user_id}, file={file_path}, "
            f"func={func_name}, session={session_id}"
        )

        # 尝试加载缓存的输入
        if load_from_cache and self.db_session:
            try:
                cache = await InputCacheDAO.get_cache(
                    self.db_session,
                    user_id,
                    file_path,
                    func_name,
                )
                if cache is not None:
                    logger.info(f"Loaded cached input for {file_path}.{func_name}")
            except Exception as e:
                logger.error(f"Error loading cache: {e}")

        result = await self.sandbox_client.execute(
            file_path=file_path,
            func_name=func_name,
            session_id=session_id,
            params=params,
        )

        logger.info(f"Execution started: {session_id}, status={result.get('status')}")
        return result

    async def resume_execution(
        self,
        user_id: str,
        session_id: str,
        user_input: dict[str, Any],
        file_path: Optional[str] = None,
        func_name: Optional[str] = None,
        step_number: int = 0,
        total_steps: int = 0,
    ) -> dict:
        """
        继续执行（用户提交 UI 后）

        会自动保存用户的输入到数据库。

        Args:
            user_id: 用户 ID
            session_id: 会话 ID
            user_input: 用户在 UI 中的输入
            file_path: 文件路径（用于保存到数据库）
            func_name: 函数名（用于保存到数据库）
            step_number: 步骤号
            total_steps: 总步骤数

        Returns:
            同 start_execution
        """
        logger.info(f"Resuming execution: user={user_id}, session={session_id}")

        # 首先继续执行
        result = await self.sandbox_client.resume(
            session_id=session_id,
            user_input=user_input,
        )

        # 保存用户输入到数据库
        if self.db_session and file_path and func_name:
            try:
                await UserInputHistoryDAO.save_input_history(
                    self.db_session,
                    user_id,
                    file_path,
                    func_name,
                    session_id,
                    user_input,
                    step_number,
                    total_steps,
                )
                await self.db_session.commit()
                logger.info(f"Saved input to history: {session_id}")
            except Exception as e:
                logger.error(f"Error saving input history: {e}")
                await self.db_session.rollback()

        logger.info(f"Execution resumed: {session_id}, status={result.get('status')}")
        return result

    async def complete_execution(
        self,
        user_id: str,
        session_id: str,
        file_path: str,
        func_name: str,
        final_result: str,
        execution_time: Optional[int] = None,
    ) -> None:
        """
        标记执行为完成

        保存最终结果到数据库。

        Args:
            user_id: 用户 ID
            session_id: 会话 ID
            file_path: 文件路径
            func_name: 函数名
            final_result: 最终的 HTML 结果
            execution_time: 执行耗时（毫秒）
        """
        if not self.db_session:
            return

        try:
            await UserInputHistoryDAO.complete_execution(
                self.db_session,
                user_id,
                file_path,
                func_name,
                session_id,
                final_result,
                execution_time,
            )
            await self.db_session.commit()
            logger.info(f"Marked execution as complete: {session_id}")
        except Exception as e:
            logger.error(f"Error completing execution: {e}")
            await self.db_session.rollback()

    async def cancel_execution(self, session_id: str) -> dict:
        """
        取消执行

        Args:
            session_id: 会话 ID
        """
        logger.info(f"Cancelling execution: {session_id}")
        return await self.sandbox_client.cancel(session_id)

    async def get_session_status(self, session_id: str) -> Optional[dict]:
        """
        获取会话状态

        Args:
            session_id: 会话 ID

        Returns:
            会话信息或 None
        """
        return await self.sandbox_client.get_session(session_id)

    async def get_all_sessions(self) -> list[dict]:
        """
        获取所有活跃会话

        Returns:
            会话列表
        """
        return await self.sandbox_client.get_sessions()

    async def invalidate_module_cache(self, file_path: str) -> dict:
        """
        使模块缓存失效

        当用户更新计算文件后调用此方法，
        以确保下次执行时重新加载最新代码。

        Args:
            file_path: 文件路径
        """
        logger.info(f"Invalidating cache: {file_path}")
        return await self.sandbox_client.invalidate_cache(file_path)

    # ==================== 版本控制相关方法 ====================

    async def get_execution_history(
        self,
        user_id: str,
        file_path: str,
        func_name: str,
        limit: int = 20,
    ) -> Optional[dict]:
        """
        获取执行历史

        包含所有完成的执行记录和已发布的版本。

        Args:
            user_id: 用户 ID
            file_path: 文件路径
            func_name: 函数名
            limit: 返回的最大条数

        Returns:
            包含历史信息的字典
        """
        if not self.db_session:
            return None

        try:
            history_records = await UserInputHistoryDAO.get_execution_history(
                self.db_session,
                user_id,
                file_path,
                func_name,
                limit,
            )

            if not history_records:
                return None

            latest = history_records[0]
            
            # 获取已发布的版本列表
            published = await PublishedVersionDAO.get_published_versions(
                self.db_session,
                user_id,
                file_path,
                func_name,
            )

            input_history = latest.input_history if latest.input_history else []
            published_list = [
                {
                    "version_name": v.version_name,
                    "version_number": v.version_number,
                    "published_at": v.published_at.isoformat(),
                    "description": v.version_description,
                    "use_count": v.use_count,
                }
                for v in published
            ]

            return {
                "file_path": file_path,
                "func_name": func_name,
                "last_execution_at": latest.updated_at.isoformat(),
                "input_history": input_history,
                "published_versions": published_list,
                "completion_percentage": 100.0 if latest.is_complete else 0.0,
                "total_executions": len(history_records),
            }
        except Exception as e:
            logger.error(f"Error getting execution history: {e}")
            return None

    async def publish_version(
        self,
        user_id: str,
        file_path: str,
        func_name: str,
        version_name: str,
        description: Optional[str] = None,
    ) -> Optional[dict]:
        """
        发布版本

        将完整的执行过程保存为可重复使用的版本。

        Args:
            user_id: 用户 ID
            file_path: 文件路径
            func_name: 函数名
            version_name: 版本名称
            description: 版本描述

        Returns:
            发布的版本信息
        """
        if not self.db_session:
            return None

        try:
            # 获取最新的历史记录
            latest = await UserInputHistoryDAO.get_latest_history(
                self.db_session,
                user_id,
                file_path,
                func_name,
            )

            if not latest or not latest.is_complete:
                logger.error(f"No completed execution history found for publishing")
                return None

            version = await PublishedVersionDAO.publish_version(
                self.db_session,
                user_id,
                file_path,
                func_name,
                version_name,
                list(latest.input_history) if latest.input_history else [],
                str(latest.final_result) if latest.final_result else "",
                dict(latest.parameters) if latest.parameters else None,
                int(latest.total_steps) if latest.total_steps else 0,
                int(latest.execution_time) if latest.execution_time else None,
                description,
                int(latest.id),
            )

            await self.db_session.commit()

            logger.info(
                f"Published version: {user_id}/{file_path}/{func_name}/"
                f"{version_name}"
            )

            return {
                "version_id": version.id,
                "version_name": version.version_name,
                "version_number": version.version_number,
                "published_at": version.published_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error publishing version: {e}")
            if self.db_session:
                await self.db_session.rollback()
            return None

    async def get_published_versions(
        self,
        user_id: str,
        file_path: str,
        func_name: str,
    ) -> list[dict]:
        """
        获取已发布的版本列表

        Args:
            user_id: 用户 ID
            file_path: 文件路径
            func_name: 函数名

        Returns:
            版本列表
        """
        if not self.db_session:
            return []

        try:
            versions = await PublishedVersionDAO.get_published_versions(
                self.db_session,
                user_id,
                file_path,
                func_name,
            )

            return [
                {
                    "version_id": v.id,
                    "version_name": v.version_name,
                    "version_number": v.version_number,
                    "description": v.version_description,
                    "published_at": v.published_at.isoformat(),
                    "use_count": v.use_count,
                    "total_steps": v.total_steps,
                }
                for v in versions
            ]
        except Exception as e:
            logger.error(f"Error getting published versions: {e}")
            return []

    async def restore_from_version(
        self,
        user_id: str,
        version_id: int,
    ) -> Optional[dict]:
        """
        从已发布的版本直接恢复完整结果

        不需要经过输入过程，直接返回该版本的最终结果。

        Args:
            user_id: 用户 ID
            version_id: 版本 ID

        Returns:
            包含最终结果的字典
        """
        if not self.db_session:
            return None

        try:
            from sqlalchemy import select
            from app.db.models.user_input_history import PublishedVersion
            
            stmt = select(PublishedVersion).where(
                PublishedVersion.id == version_id,
                PublishedVersion.user_id == user_id,
            )
            result = await self.db_session.execute(stmt)
            version = result.scalar_one_or_none()

            if not version:
                logger.error(f"Version not found: {version_id}")
                return None

            # 增加使用次数
            await PublishedVersionDAO.increment_use_count(self.db_session, version_id)
            await self.db_session.commit()

            return {
                "status": "completed",
                "version_id": version_id,
                "version_name": version.version_name,
                "result": version.final_result,
                "steps": version.total_steps,
                "restored_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error restoring from version: {e}")
            return None


# 全局服务实例
_service: Optional[CalcExecutionService] = None


def get_execution_service() -> CalcExecutionService:
    """获取全局执行服务实例"""
    global _service
    if _service is None:
        _service = CalcExecutionService()
    return _service


def set_execution_service(service: CalcExecutionService):
    """设置全局执行服务实例"""
    global _service
    _service = service
