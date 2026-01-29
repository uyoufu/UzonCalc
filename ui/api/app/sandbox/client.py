"""
沙箱客户端

API 层通过此客户端与沙箱通信。
支持本地和远程（容器）两种模式。
"""

from typing import Optional, Any
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# region 抽象接口


class SandboxClient(ABC):
    """沙箱客户端抽象接口"""

    @abstractmethod
    async def execute(
        self,
        file_path: str,
        func_name: str,
        session_id: str,
        params: dict[str, Any],
    ) -> dict:
        """执行计算函数"""
        pass

    @abstractmethod
    async def resume(
        self,
        session_id: str,
        user_input: dict[str, Any],
    ) -> dict:
        """继续执行"""
        pass

    @abstractmethod
    async def cancel(self, session_id: str) -> dict:
        """取消执行"""
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话状态"""
        pass

    @abstractmethod
    async def get_sessions(self) -> list[dict]:
        """获取所有会话"""
        pass

    @abstractmethod
    async def invalidate_cache(self, file_path: str) -> dict:
        """使缓存失效"""
        pass


# endregion

# region 本地客户端（进程内）


class LocalSandboxClient(SandboxClient):
    """
    本地沙箱客户端

    在同一进程中调用沙箱执行器。
    适合开发和单机部署。
    """

    def __init__(self, executor=None):
        """
        Args:
            executor: CalcSandboxExecutor 实例，
                      None 则使用全局实例
        """
        if executor is None:
            from .executor import get_executor

            self.executor = get_executor()
        else:
            self.executor = executor

    async def execute(
        self,
        file_path: str,
        func_name: str,
        session_id: str,
        params: dict[str, Any],
    ) -> dict:
        """执行计算函数"""
        try:
            status, ui, html = await self.executor.execute_function(
                file_path=file_path,
                func_name=func_name,
                session_id=session_id,
                params=params,
            )

            result = {
                "status": status.value,
                "session_id": session_id,
            }

            if ui:
                result["ui"] = {
                    "title": ui["title"],
                    "fields": ui["fields"],
                }

            if html:
                result["result"] = html

            return result

        except Exception as e:
            logger.error(f"LocalSandboxClient.execute error: {e}", exc_info=True)
            return {
                "status": "error",
                "session_id": session_id,
                "error": str(e),
            }

    async def resume(
        self,
        session_id: str,
        user_input: dict[str, Any],
    ) -> dict:
        """继续执行"""
        try:
            status, ui, html = await self.executor.resume_execution(
                session_id=session_id,
                user_input=user_input,
            )

            result = {
                "status": status.value,
                "session_id": session_id,
            }

            if ui:
                result["ui"] = {
                    "title": ui["title"],
                    "fields": ui["fields"],
                }

            if html:
                result["result"] = html

            return result

        except Exception as e:
            logger.error(f"LocalSandboxClient.resume error: {e}", exc_info=True)
            return {
                "status": "error",
                "session_id": session_id,
                "error": str(e),
            }

    async def cancel(self, session_id: str) -> dict:
        """取消执行"""
        try:
            self.executor.cancel_execution(session_id)
            return {
                "status": "cancelled",
                "session_id": session_id,
            }
        except Exception as e:
            logger.error(f"LocalSandboxClient.cancel error: {e}", exc_info=True)
            return {
                "status": "error",
                "session_id": session_id,
                "error": str(e),
            }

    async def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话状态"""
        return self.executor.get_session_status(session_id)

    async def get_sessions(self) -> list[dict]:
        """获取所有会话"""
        return self.executor.get_all_sessions()

    async def invalidate_cache(self, file_path: str) -> dict:
        """使缓存失效"""
        try:
            self.executor.invalidate_module_cache(file_path)
            return {
                "status": "ok",
                "message": f"Cache invalidated for {file_path}",
            }
        except Exception as e:
            logger.error(
                f"LocalSandboxClient.invalidate_cache error: {e}", exc_info=True
            )
            return {
                "status": "error",
                "error": str(e),
            }


# endregion

# region 远程客户端（HTTP）


class RemoteSandboxClient(SandboxClient):
    """
    远程沙箱客户端

    通过 HTTP 调用远程沙箱容器中的 RPC 接口。
    适合生产环境和分布式部署。
    """

    def __init__(self, base_url: str = "http://localhost:3346"):
        """
        Args:
            base_url: 沙箱服务的基础 URL
        """
        self.base_url = base_url
        # 延迟导入，避免依赖循环
        self._client = None

    async def _get_client(self):
        """获取 HTTP 客户端"""
        if self._client is None:
            import httpx

            self._client = httpx.AsyncClient(base_url=self.base_url)
        return self._client

    async def execute(
        self,
        file_path: str,
        func_name: str,
        session_id: str,
        params: dict[str, Any],
    ) -> dict:
        """执行计算函数"""
        try:
            client = await self._get_client()
            response = await client.post(
                "/sandbox/execute",
                json={
                    "file_path": file_path,
                    "func_name": func_name,
                    "session_id": session_id,
                    "params": params,
                },
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"RemoteSandboxClient.execute error: {e}", exc_info=True)
            return {
                "status": "error",
                "session_id": session_id,
                "error": str(e),
            }

    async def resume(
        self,
        session_id: str,
        user_input: dict[str, Any],
    ) -> dict:
        """继续执行"""
        try:
            client = await self._get_client()
            response = await client.post(
                "/sandbox/resume",
                json={
                    "session_id": session_id,
                    "user_input": user_input,
                },
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"RemoteSandboxClient.resume error: {e}", exc_info=True)
            return {
                "status": "error",
                "session_id": session_id,
                "error": str(e),
            }

    async def cancel(self, session_id: str) -> dict:
        """取消执行"""
        try:
            client = await self._get_client()
            response = await client.post(f"/sandbox/cancel/{session_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"RemoteSandboxClient.cancel error: {e}", exc_info=True)
            return {
                "status": "error",
                "session_id": session_id,
                "error": str(e),
            }

    async def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话状态"""
        try:
            client = await self._get_client()
            response = await client.get(f"/sandbox/session/{session_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"RemoteSandboxClient.get_session error: {e}", exc_info=True)
            return None

    async def get_sessions(self) -> list[dict]:
        """获取所有会话"""
        try:
            client = await self._get_client()
            response = await client.get("/sandbox/sessions")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"RemoteSandboxClient.get_sessions error: {e}", exc_info=True)
            return []

    async def invalidate_cache(self, file_path: str) -> dict:
        """使缓存失效"""
        try:
            client = await self._get_client()
            response = await client.post(
                "/sandbox/invalidate-cache",
                json={"file_path": file_path},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(
                f"RemoteSandboxClient.invalidate_cache error: {e}", exc_info=True
            )
            return {
                "status": "error",
                "error": str(e),
            }

    async def close(self):
        """关闭客户端连接"""
        if self._client:
            await self._client.aclose()


# endregion


# 全局沙箱客户端实例


_sandbox_client: Optional[SandboxClient] = None


def get_sandbox_client() -> SandboxClient:
    """获取全局沙箱客户端"""
    global _sandbox_client
    if _sandbox_client is None:
        _sandbox_client = LocalSandboxClient()
    return _sandbox_client


def set_sandbox_client(client: SandboxClient):
    """设置全局沙箱客户端"""
    global _sandbox_client
    _sandbox_client = client


# endregion
