"""
生成器生命周期管理

在沙箱中管理异步生成器的执行状态。
每个计算会话对应一个生成器实例。
"""

import asyncio
from typing import Optional, Any, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """执行状态"""
    IDLE = "idle"                      # 空闲
    RUNNING = "running"                # 运行中
    WAITING_INPUT = "waiting_input"    # 等待用户输入
    COMPLETED = "completed"            # 已完成
    ERROR = "error"                    # 错误
    CANCELLED = "cancelled"            # 已取消


@dataclass
class GeneratorSession:
    """
    生成器会话管理
    """
    session_id: str
    generator: AsyncGenerator
    status: ExecutionStatus = ExecutionStatus.IDLE
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    timeout_seconds: int = 3600  # 1小时超时
    
    # 执行结果
    current_ui: Optional[dict] = None       # 当前等待的 UI
    accumulated_result: str = ""             # 积累的结果（HTML）
    error_message: Optional[str] = None      # 错误信息
    
    # 统计
    ui_steps: int = 0                        # 遇到的 UI 数量
    execution_time: float = 0                # 执行耗时（秒）

    def is_expired(self) -> bool:
        """检查会话是否过期"""
        elapsed = (datetime.now() - self.last_activity).total_seconds()
        return elapsed > self.timeout_seconds

    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = datetime.now()


class GeneratorManager:
    """
    管理所有活跃的生成器会话
    """

    def __init__(self, cleanup_interval: int = 300):
        """
        Args:
            cleanup_interval: 清理过期会话的间隔（秒）
        """
        self._sessions: dict[str, GeneratorSession] = {}
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动后台清理任务"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("GeneratorManager cleanup task started")

    async def stop(self):
        """停止后台清理任务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("GeneratorManager cleanup task stopped")

    async def _cleanup_loop(self):
        """定期清理过期会话"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def _cleanup_expired(self):
        """清理过期会话"""
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired()
        ]
        for sid in expired:
            logger.info(f"Cleaning up expired session: {sid}")
            del self._sessions[sid]

    def create_session(
        self,
        session_id: str,
        generator: AsyncGenerator,
        timeout_seconds: int = 3600,
    ) -> GeneratorSession:
        """
        创建新的生成器会话

        Args:
            session_id: 会话 ID
            generator: 异步生成器
            timeout_seconds: 超时时间（秒）

        Returns:
            GeneratorSession 对象

        Raises:
            ValueError: 会话 ID 已存在
        """
        if session_id in self._sessions:
            raise ValueError(f"Session already exists: {session_id}")

        session = GeneratorSession(
            session_id=session_id,
            generator=generator,
            timeout_seconds=timeout_seconds,
        )
        self._sessions[session_id] = session
        logger.info(f"Created session: {session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[GeneratorSession]:
        """获取会话"""
        session = self._sessions.get(session_id)
        if session and session.is_expired():
            logger.warning(f"Session expired: {session_id}")
            del self._sessions[session_id]
            return None
        return session

    async def resume_session(
        self,
        session_id: str,
        user_input: dict,
    ) -> tuple[ExecutionStatus, Optional[dict], str]:
        """
        恢复会话执行

        Args:
            session_id: 会话 ID
            user_input: 用户在 UI 中的输入

        Returns:
            (status, current_ui_or_none, accumulated_html)

        Raises:
            ValueError: 会话不存在
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if session.status != ExecutionStatus.WAITING_INPUT:
            raise ValueError(f"Session is not waiting for input: {session_id}")

        session.update_activity()
        session.status = ExecutionStatus.RUNNING

        try:
            # 将用户输入发送给生成器，继续执行
            result = await session.generator.asend(user_input)  # type: ignore

            # 检查是否为 CalcContext（最后一个值）
            if hasattr(result, "to_html"):
                # 生成器完成，返回 CalcContext
                html = result.to_html() if hasattr(result, "to_html") else ""
                session.accumulated_result += html
                session.status = ExecutionStatus.COMPLETED
                return (ExecutionStatus.COMPLETED, None, session.accumulated_result)

            if result is None:
                # 生成器完成
                session.status = ExecutionStatus.COMPLETED
                return (ExecutionStatus.COMPLETED, None, session.accumulated_result)

            # 返回下一个 UI
            if isinstance(result, dict) and "title" in result:
                # UI 对象
                session.current_ui = result
                session.ui_steps += 1
                session.status = ExecutionStatus.WAITING_INPUT
                return (ExecutionStatus.WAITING_INPUT, result, session.accumulated_result)
            else:
                # 中间结果（HTML 片段）
                session.accumulated_result += str(result)
                # 继续执行
                return await self.resume_session(session_id, {})

        except StopAsyncIteration:
            session.status = ExecutionStatus.COMPLETED
            logger.info(f"Session completed: {session_id}")
            return (ExecutionStatus.COMPLETED, None, session.accumulated_result)

        except Exception as e:
            session.status = ExecutionStatus.ERROR
            session.error_message = str(e)
            logger.error(f"Error in session {session_id}: {e}", exc_info=True)
            raise

    async def start_session(
        self,
        session_id: str,
        generator: AsyncGenerator,
    ) -> tuple[ExecutionStatus, Optional[dict], str]:
        """
        启动新会话的执行

        Args:
            session_id: 会话 ID
            generator: 异步生成器

        Returns:
            (status, current_ui_or_none, accumulated_html)
        """
        session = self.create_session(session_id, generator)
        session.update_activity()
        session.status = ExecutionStatus.RUNNING

        try:
            # 首次运行生成器
            result = await generator.__anext__()

            # 检查是否为 CalcContext（最后一个值）
            if hasattr(result, "to_html"):
                # 生成器完成，返回 CalcContext
                html = result.to_html() if hasattr(result, "to_html") else ""
                session.accumulated_result += html
                session.status = ExecutionStatus.COMPLETED
                return (ExecutionStatus.COMPLETED, None, session.accumulated_result)

            if result is None:
                # 立即完成（无 UI）
                session.status = ExecutionStatus.COMPLETED
                return (ExecutionStatus.COMPLETED, None, session.accumulated_result)

            # 返回首个 UI
            if isinstance(result, dict) and "title" in result:
                session.current_ui = result
                session.ui_steps += 1
                session.status = ExecutionStatus.WAITING_INPUT
                return (ExecutionStatus.WAITING_INPUT, result, session.accumulated_result)
            else:
                # 中间结果
                session.accumulated_result += str(result)
                # 继续
                return await self.resume_session(session_id, {})

        except StopAsyncIteration:
            session.status = ExecutionStatus.COMPLETED
            return (ExecutionStatus.COMPLETED, None, session.accumulated_result)

        except Exception as e:
            session.status = ExecutionStatus.ERROR
            session.error_message = str(e)
            logger.error(f"Error starting session {session_id}: {e}", exc_info=True)
            raise

    def cancel_session(self, session_id: str):
        """取消会话"""
        session = self._sessions.get(session_id)
        if session:
            session.status = ExecutionStatus.CANCELLED
            del self._sessions[session_id]
            logger.info(f"Cancelled session: {session_id}")

    def get_all_sessions(self) -> list[dict]:
        """获取所有活跃会话信息"""
        return [
            {
                "session_id": s.session_id,
                "status": s.status.value,
                "created_at": s.created_at.isoformat(),
                "last_activity": s.last_activity.isoformat(),
                "ui_steps": s.ui_steps,
                "has_error": s.error_message is not None,
            }
            for s in self._sessions.values()
        ]

    def get_session_info(self, session_id: str) -> Optional[dict]:
        """获取单个会话详细信息"""
        session = self.get_session(session_id)
        if not session:
            return None

        return {
            "session_id": session.session_id,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "ui_steps": session.ui_steps,
            "current_ui": session.current_ui,
            "has_accumulated_result": len(session.accumulated_result) > 0,
            "error_message": session.error_message,
        }
