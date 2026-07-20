"""Create and run the UzonCalc HTTP API application."""

import os
import time
import sys
import logging
import socket

from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
os.chdir(HERE)

from app.db.init_db import init_database
from app.db.manager import get_db_manager
from app.utils.dynamic_loader import load_routers_from_directory
from app.exception.custom_exception import CustomException
from app.response.response_result import fail
from app.i18n import _
from app.middleware.authentication import (
    allow_anonymous,
    authenticate_non_api_request,
    require_route_authentication,
)
from app.middleware.i18n import i18n_middleware
from app.schedule.scheduler import start_scheduler, shutdown_scheduler
from app.middleware.vue_spa import use_vue_spa_middleware
from app.mcp.startup import (
    combine_lifespans,
    mount_mcp,
    init_tool_search,
    close_tool_search,
)
from app.service.playwright_service import close_playwright_service
from app.sandbox.core.backend_factory import close_sandbox_executor
from app.service.calc_execution_service import expire_orphaned_executions

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.concurrency import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from config import logger, app_config

# 初始化日志配置
logger.info(f"{app_config.app_name} launching...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    生命周期管理
    """

    logger.info("Lifespan startup tasks running...")
    logger.debug("Application startup tasks can be performed here.")

    # Initialize db
    db_initialized = await init_database()
    if not db_initialized:
        raise RuntimeError("Database initialization failed during startup")

    async with get_db_manager().session() as session:
        await expire_orphaned_executions(session)

    # migrations
    # run_migrations()

    # 启用定时器
    start_scheduler()

    # 初始化工具搜索索引（MCP 启用时）
    await init_tool_search()

    yield

    try:
        db_manager = get_db_manager()
        await db_manager.shutdown()
        logger.info("Database connections closed successfully")

        # 关闭定时器
        shutdown_scheduler()

        # 释放工具搜索资源
        await close_tool_search()

        # 释放 Playwright 浏览器缓存
        await close_playwright_service()

        # 终止仍在运行的计算会话并关闭远程连接池
        await close_sandbox_executor()
    except Exception as e:
        logger.error(f"Database shutdown error: {e}")

    # Release the resources
    logger.info("Application lifespan ended...")


# 将 MCP 的 lifespan 与主应用的 lifespan 进行合并，使得两者的生命周期能够正确管理
combined_lifespans = combine_lifespans(lifespan)

app = FastAPI(
    lifespan=combined_lifespans,
    dependencies=[Depends(require_route_authentication)],
)

logger.info("Load controllers ...")
# 这部分为路由配置，每增加一个路由，都需要在这里进行配置
load_routers_from_directory("app/controller", app)
logger.info("All controllers loaded!")

# region 函数名用作 operationId, 参考 https://fastapi.org.cn/advanced/path-operation-advanced-configuration/#openapi-operationid
from fastapi.routing import APIRoute


def use_route_names_as_operation_ids(app: FastAPI) -> None:
    """
    Simplify operation IDs so that generated API clients have simpler function
    names.

    Should be called only after all routes have been added.
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name  # in this case, 'read_items'


use_route_names_as_operation_ids(app)
# endregion

logger.info("Initialize directories ...")
# 设置静态目录
# 若目录不存在，则创建一个
if not os.path.exists("data/public"):
    os.makedirs("data/public")
app.mount("/public", StaticFiles(directory="data/public"), name="public")

# 初始化 Vue 前端目录
if not os.path.exists("data/www"):
    os.makedirs("data/www")

# 初始化其它所需要的目录
init_dirs = [
    "data/db",  # 数据库位置
]
for dir_name in init_dirs:
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
logger.info("Directories initialized!")


# 中间件，先添加，后执行
@app.middleware("http")
async def authentication(request: Request, call_next: Callable):
    """Authenticate mounted non-API applications outside FastAPI dependencies."""
    return await authenticate_non_api_request(request, call_next)


# # 添加异常捕获中间件
@app.middleware("http")
async def catch_exception(request: Request, call_next):
    """Convert application and framework exceptions into response envelopes."""
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(e, exc_info=True)
        if isinstance(e, CustomException):
            payload = e.model_dump()
            response = JSONResponse(content=payload, status_code=e.code)
        elif isinstance(e, HTTPException):
            r = fail(
                message=f"{type(e).__name__}: {_(str(e.detail))}",
                code=e.status_code,
            )
            response = JSONResponse(content=r.model_dump(), status_code=r.code)
        else:
            r = fail(message=f"{type(e).__name__}: {_(str(e))}")
            response = JSONResponse(content=r.model_dump(), status_code=r.code)
    return response


@app.middleware("http")
async def use_i18n(request: Request, call_next: Callable):
    """Select request-local gettext translations before route execution."""
    return await i18n_middleware(request, call_next)


# # 全局异常处理
# @app.exception_handler(CustomException)
# async def custom_exception_handler(request: Request, ex: CustomException):
#     return JSONResponse(
#         status_code=ex.code,
#         content=ex.model_dump(),
#     )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Measure request latency and expose it in a response header."""
    start_time = time.time()

    logger.debug(f"Start processing request: [{request.url}]")

    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    # 打印时间
    logger.debug(
        f"Finished processing request: [{request.url}] in {process_time} seconds"
    )
    return response


# 设置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加 Vue SPA 中间件（必须在所有路由和中间件配置之后）
# use_vue_spa_middleware(app, "data/www")


# 根路由仅在 Vue 前端不存在时提供 API 信息
if not os.path.exists("data/www/index.html"):

    @app.get("/")
    @allow_anonymous
    async def home():
        """
        根路由
        :return:
        """
        return {"message": app_config.welcome}


# region mcp
mount_mcp(app)
# endregion

logger.info(f"{app_config.app_name} launched successfully!")


def is_port_available(host: str, port: int) -> bool:
    """检查指定地址和端口是否可绑定。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def find_available_port(host: str, preferred_port: int, max_tries: int = 20) -> int:
    """在首选端口不可用时，向后探测可用端口。"""
    for port in range(preferred_port, preferred_port + max_tries + 1):
        if is_port_available(host, port):
            return port

    raise RuntimeError(
        f"No available port found for host {host} in range "
        f"{preferred_port}-{preferred_port + max_tries}"
    )


if __name__ == "__main__":
    import uvicorn

    run_port = app_config.port

    logger.info(
        f"Starting {app_config.app_name}, host {app_config.host}, port {run_port}..."
    )

    if app_config.is_dev:
        logger.info(
            "Detected development environment, starting in development mode with auto-reload..."
        )
        if not is_port_available(app_config.host, run_port):
            fallback_port = find_available_port(app_config.host, run_port + 1)
            logger.warning(
                "Port %s is already in use, switching development server to port %s.",
                run_port,
                fallback_port,
            )
            run_port = fallback_port

        # 关闭 watchfiles 的日志输出
        logging.getLogger("watchfiles.main").setLevel(logging.WARNING)
        uvicorn.run(
            "main:app",
            host=app_config.host,
            port=run_port,
            log_level=logging.DEBUG,
            reload=True,
            reload_excludes=["*.log", "*.md"],
        )
    else:
        logger.info("Detected production environment, starting in normal mode...")
        uvicorn.run(
            app,
            host=app_config.host,
            port=run_port,
            log_level=app_config.log_level,
        )
