from fastapi import APIRouter
from app.response.response_result import ResponseResult, ok
from config import app_config

router = APIRouter(
    prefix="/v1/system-info",
    tags=["system-info"],
)


@router.get("/version")
async def get_version() -> ResponseResult[str]:
    """
    获取系统版本号

    **功能说明:**
    - 返回当前系统的版本号字符串

    **返回数据:**
    - version: 系统版本号
    """
    return ok(data=app_config.version)
