from fastapi import APIRouter
from app.response.response_result import ResponseResult, ok
from app.controller.system.system_dto import DesktopAutoLoginResDTO
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


@router.get("/desktop-auto-login")
async def get_desktop_auto_login() -> ResponseResult[DesktopAutoLoginResDTO]:
    """
    获取桌面端自动登录信息

    **功能说明:**
    - 仅在桌面端返回默认账号和密码

    **返回数据:**
    - enabled: 是否启用自动登录
    - username: 自动登录账号
    - password: 自动登录密码（明文）
    """
    if not app_config.is_desktop:
        return ok(data=DesktopAutoLoginResDTO(enabled=False, username="", password=""))

    return ok(
        data=DesktopAutoLoginResDTO(
            enabled=True,
            username=app_config.default_userId,
            password=app_config.default_password_plain,
        )
    )
