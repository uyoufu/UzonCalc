"""
Vue 单页应用中间件
将请求重定向到 index.html，用于支持 Vue Router 的 history 模式
"""

from pathlib import Path
from typing import Callable, List, Optional
from fastapi import Request
from starlette.responses import FileResponse
from config import logger


class VueSPAMiddleware:
    """
    Vue 单页应用中间件
    处理 Vue Router history 模式的路由回退
    """

    def __init__(self, wwwroot_path: Optional[str] = None):
        """
        初始化中间件

        Args:
            wwwroot_path: Vue 编译后文件的根目录，默认为 data/www
        """
        if wwwroot_path is None or wwwroot_path == "":
            wwwroot_path = "data/www"

        self.wwwroot_path = Path(wwwroot_path)
        self.index_file_path = self.wwwroot_path / "index.html"
        self._exist_names: List[str] = []

        # 检查 index.html 是否存在
        self.is_valid = self.index_file_path.exists()

        if not self.is_valid:
            logger.warning(
                f"Vue SPA middleware is disabled because index.html not found at: {self.index_file_path}"
            )
            return

        # 收集 wwwroot 目录下的所有文件和文件夹名称
        if self.wwwroot_path.exists():
            files = [f.name for f in self.wwwroot_path.iterdir() if f.is_file()]
            dirs = [d.name for d in self.wwwroot_path.iterdir() if d.is_dir()]
            self._exist_names.extend(files)
            self._exist_names.extend(dirs)

            logger.info(
                f"Vue SPA middleware initialized. Found {len(files)} files and {len(dirs)} directories in {wwwroot_path}"
            )
        else:
            logger.warning(f"Vue SPA wwwroot directory not found: {wwwroot_path}")

    async def __call__(self, request: Request, call_next: Callable):
        """
        中间件处理函数

        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理函数

        Returns:
            响应对象
        """
        # 如果中间件无效，直接传递
        if not self.is_valid:
            return await call_next(request)

        # 获取请求路径
        request_path = request.url.path

        # 如果是 API 路径或其他已处理的路径，先执行后续处理
        if request_path.startswith("/api") or request_path.startswith("/public"):
            return await call_next(request)

        # 尝试查找静态文件
        file_path = self.wwwroot_path / request_path.lstrip("/")

        # 如果请求的文件存在，直接返回
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        # 如果是根路径，返回 index.html
        if request_path == "/" or request_path == "":
            return FileResponse(self.index_file_path)

        # 获取路径的第一段
        path_parts = request_path.strip("/").split("/")
        first_path = path_parts[0] if path_parts else ""

        # 如果第一段在已存在的文件/文件夹列表中
        # 可能是访问子目录中的文件，交给后续处理
        if first_path in self._exist_names:
            return await call_next(request)

        # 否则，这是一个 Vue 路由，返回 index.html
        logger.debug(f"Vue SPA fallback: {request_path} -> index.html")
        return FileResponse(self.index_file_path)


def use_vue_spa_middleware(app, wwwroot_path: Optional[str] = None):
    """
    配置 Vue SPA 中间件

    Args:
        app: FastAPI 应用实例
        wwwroot_path: Vue 编译后文件的根目录，默认为 data/www
    """
    middleware = VueSPAMiddleware(wwwroot_path)

    # 如果中间件无效，不启用
    if not middleware.is_valid:
        return

    app.middleware("http")(middleware)
    logger.info("Vue SPA middleware enabled")
