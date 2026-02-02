import os
import time
import sys

from pathlib import Path
from gettext import gettext as _
from typing import Callable

from app.db.init_db import init_database
from app.db.manager import get_db_manager
from app.utils.dynamic_loader import load_routers_from_directory
from app.exception.custom_exception import CustomException, raise_ex
from app.response.response_result import fail
from app.controller.depends import get_request_token
from app.schedule.scheduler import start_scheduler, shutdown_scheduler
from utils.jwt_helper import verify_jwt

HERE = Path(__file__).resolve().parent
os.chdir(HERE)

from fastapi import FastAPI, Request
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
    await init_database()

    # migrations
    # run_migrations()

    # 启用定时器
    start_scheduler()

    yield

    try:
        db_manager = get_db_manager()
        await db_manager.shutdown()
        logger.info("Database connections closed successfully")

        # 关闭定时器
        shutdown_scheduler()
    except Exception as e:
        logger.error(f"Database shutdown error: {e}")

    # Release the resources
    logger.info("Application lifespan ended...")


app = FastAPI(lifespan=lifespan)

logger.info(f"Load controllers ...")
# 这部分为路由配置，每增加一个路由，都需要在这里进行配置
load_routers_from_directory("app/controller", app)
logger.info(f"All controllers loaded!")

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

logger.info(f"Initialize directories ...")
# 设置静态目录
# 若目录不存在，则创建一个
if not os.path.exists("data/public"):
    os.mkdir("data/public")
app.mount("/public", StaticFiles(directory="data/public"), name="public")

# 初始化其它所需要的目录
init_dirs = [
    "data/db",  # 数据库位置
]
for dir_name in init_dirs:
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
logger.info(f"Directories initialized!")


# 中间件，先添加，后执行
# 添加鉴权中间件
@app.middleware("http")
async def authentication(request: Request, call_next: Callable):
    # 忽略根路径和静态文件路径
    if request.url.path == "/":
        return await call_next(request)

    # # 允许 CORS 预检请求通过，不做鉴权
    # if request.method == "OPTIONS":
    #     return await call_next(request)

    # 忽略文件路径
    ignore_starts = [
        "/api/v1/user/sign-in",  # sign-in 不需要鉴权
        "/api/v1/system-info/version",  # 获取版本号不需要鉴权
        "/public",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    ]
    for ignore_start in ignore_starts:
        if request.url.path.startswith(ignore_start):
            return await call_next(request)

    # 获取 token 并验证
    try:
        token = get_request_token(request)
        if not verify_jwt(token):
            raise_ex(_("Authorization failed!"), 401)
    except CustomException:
        raise

    return await call_next(request)


# # 添加异常捕获中间件
@app.middleware("http")
async def catch_exception(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(e, exc_info=True)
        if isinstance(e, CustomException):
            payload = e.model_dump()
            response = JSONResponse(content=payload, status_code=e.code)
        else:
            r = fail(message=f"{type(e).__name__}: {str(e)}")
            response = JSONResponse(content=r.model_dump(), status_code=r.code)
    return response


# # 全局异常处理
# @app.exception_handler(CustomException)
# async def custom_exception_handler(request: Request, ex: CustomException):
#     return JSONResponse(
#         status_code=ex.code,
#         content=ex.model_dump(),
#     )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
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


@app.get("/")
async def home():
    """
    根路由
    :return:
    """
    return {"message": app_config.welcome}


logger.info(f"{app_config.app_name} launched successfully!")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app, host=app_config.host, port=app_config.port, log_level=app_config.log_level
    )
