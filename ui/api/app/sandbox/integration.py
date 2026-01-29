"""
沙箱集成初始化

在 FastAPI 应用启动时调用此模块进行初始化。
"""

from typing import Optional
from app.sandbox.executor import CalcSandboxExecutor, get_executor, set_executor
from app.sandbox.client import (
    LocalSandboxClient,
    RemoteSandboxClient,
    get_sandbox_client,
    set_sandbox_client,
)

from config import logger, app_config


class SandboxConfig:
    """沙箱配置"""

    def __init__(
        self,
        mode: str = "local",  # "local" 或 "remote"
        safe_dirs: Optional[list[str]] = None,
        session_timeout: int = 360,
        sandbox_url: Optional[str] = None,
    ):
        """
        Args:
            mode: "local" (进程内) 或 "remote" (HTTP RPC)
            safe_dirs: 允许加载的目录白名单 (local 模式)
            session_timeout: 会话超时时间 (秒)
            sandbox_url: 沙箱服务地址 (remote 模式)
        """
        self.mode = mode
        self.safe_dirs = safe_dirs or []
        self.session_timeout = session_timeout
        self.sandbox_url = sandbox_url or "http://localhost:3346"

    def validate(self):
        """验证配置"""
        if self.mode not in ("local", "remote"):
            raise ValueError(f"Invalid mode: {self.mode}")
        if self.mode == "remote" and not self.sandbox_url:
            raise ValueError("sandbox_url is required for remote mode")


def get_sandbox_config() -> SandboxConfig:
    """从 app_config 获取沙箱配置"""
    return SandboxConfig(
        mode=app_config.sandbox_mode,
        safe_dirs=app_config.sandbox_safe_dirs,
        session_timeout=app_config.sandbox_session_timeout,
        sandbox_url=app_config.sandbox_url,
    )


async def initialize_sandbox(config: SandboxConfig):
    """
    初始化沙箱

    在 FastAPI app.on_event("startup") 中调用

    Args:
        config: SandboxConfig 对象
    """
    config.validate()
    logger.info(f"Initializing sandbox with mode: {config.mode}")

    if config.mode == "local":
        # 本地模式
        executor = CalcSandboxExecutor(
            safe_dirs=config.safe_dirs,
            session_timeout=config.session_timeout,
        )
        await executor.initialize()
        set_executor(executor)

        client = LocalSandboxClient(executor)
        set_sandbox_client(client)

        logger.info("Sandbox initialized in LOCAL mode")
        logger.info(f"Safe directories: {config.safe_dirs}")

    else:
        # 远程模式
        client = RemoteSandboxClient(base_url=config.sandbox_url)
        set_sandbox_client(client)

        logger.info("Sandbox initialized in REMOTE mode")
        logger.info(f"Sandbox URL: {config.sandbox_url}")


async def shutdown_sandbox():
    """
    关闭沙箱

    在 FastAPI app.on_event("shutdown") 中调用
    """
    logger.info("Shutting down sandbox")

    # 获取当前客户端
    client = get_sandbox_client()

    # 如果是本地执行器，需要关闭它
    try:
        executor = get_executor()
        if executor:
            await executor.shutdown()
            logger.info("Local executor shutdown")
    except Exception as e:
        logger.warning(f"Error shutting down executor: {e}")

    # 如果是远程客户端，关闭连接
    if isinstance(client, RemoteSandboxClient):
        try:
            await client.close()
            logger.info("Remote client connection closed")
        except Exception as e:
            logger.warning(f"Error closing remote client: {e}")


# ============================================================================
# 快速启动辅助函数
# ============================================================================


def create_local_sandbox_config(
    safe_dirs: Optional[list[str]] = None,
    session_timeout: int = 3600,
) -> SandboxConfig:
    """创建本地模式配置"""
    return SandboxConfig(
        mode="local",
        safe_dirs=safe_dirs,
        session_timeout=session_timeout,
    )


def create_remote_sandbox_config(
    sandbox_url: str,
    session_timeout: int = 3600,
) -> SandboxConfig:
    """创建远程模式配置"""
    return SandboxConfig(
        mode="remote",
        session_timeout=session_timeout,
        sandbox_url=sandbox_url,
    )
