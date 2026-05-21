"""
远程 Sandbox 执行器

通过 HTTP 调用远程 sandbox 服务
"""

from typing import Any, Dict
import httpx
from app.sandbox.core.execution_result import ExecutionResult
from app.sandbox.core.executor_interface import ISandboxExecutor
from config import logger


class RemoteSandboxExecutor(ISandboxExecutor):
    """远程 HTTP 执行器"""

    def __init__(self, base_url: str, timeout: float = 300.0):
        """
        初始化远程执行器

        :param base_url: 远程 sandbox 服务地址，如 "http://sandbox-service:8001"
        :param timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def execute_script(
        self,
        script_path: str,
        defaults: Dict[str, Dict[str, Any]] | None = None,
        is_silent: bool = False,
        package_root: str | None = None,
    ) -> ExecutionResult:
        """执行脚本"""
        client = await self._get_client()

        try:
            payload = {
                "script_path": script_path,
                "defaults": defaults or {},
                "is_silent": is_silent,
            }
            if package_root is not None:
                payload["package_root"] = package_root
            
            response = await client.post(
                "/sandbox/execute",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return ExecutionResult(**data)
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error executing script: {e.response.status_code} - {e.response.text}"
            )
            raise RuntimeError(f"Remote execution failed: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error executing script: {e}")
            raise RuntimeError(f"Failed to connect to remote sandbox service: {e}")

    async def continue_execution(
        self,
        execution_id: str,
        defaults: Dict[str, Dict[str, Any]],
    ) -> ExecutionResult:
        """继续执行"""
        client = await self._get_client()

        try:
            response = await client.post(
                "/sandbox/continue",
                json={
                    "execution_id": execution_id,
                    "defaults": defaults,
                },
            )
            response.raise_for_status()
            data = response.json()
            return ExecutionResult(**data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Execution {execution_id} not found")
            logger.error(
                f"HTTP error continuing execution: {e.response.status_code} - {e.response.text}"
            )
            raise RuntimeError(f"Remote execution failed: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error continuing execution: {e}")
            raise RuntimeError(f"Failed to connect to remote sandbox service: {e}")

    async def terminate(self, execution_id: str) -> None:
        """终止执行"""
        client = await self._get_client()

        try:
            response = await client.post(
                "/sandbox/terminate",
                json={"execution_id": execution_id},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error terminating execution: {e.response.status_code} - {e.response.text}"
            )
            raise RuntimeError(f"Remote termination failed: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error terminating execution: {e}")
            raise RuntimeError(f"Failed to connect to remote sandbox service: {e}")

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
