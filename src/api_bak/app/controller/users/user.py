from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.depends import get_session, get_current_user
from app.response.response_result import ResponseResult, ok
from config import logger
import app.service.user_service as user_service

from .user_dto import (
    UserSignInDTO,
    UserSignInResponseDTO,
    ChangePasswordDTO,
    UserDetailDTO,
)
from app.db.models.user import User

router = APIRouter(
    prefix="/v1/user",
    tags=["user"],
)


@router.post("/sign-in")
async def sign_in(
    data: UserSignInDTO, session: AsyncSession = Depends(get_session)
) -> ResponseResult[UserSignInResponseDTO]:
    """
    用户登录

    **功能说明:**
    - 验证用户名和密码
    - 登录成功返回用户信息和访问令牌、刷新令牌
    - 不返回密码字段

    **请求参数:**
    - username: 用户名
    - password: 密码

    **返回数据:**
    - user_id: 用户ID
    - username: 用户名
    - roles: 用户角色列表
    - access_token: 访问令牌（有效期1小时）
    - refresh_token: 刷新令牌（有效期7天）
    - token_type: 令牌类型（固定为Bearer）
    """

    # 调用 Service 层完成登录业务逻辑
    result = await user_service.sign_in(data.username, data.password, session)
    logger.info(f"用户登录请求处理完成: {data.username}")
    # 返回成功响应
    return ok(data=result)


@router.get("/info/{username}")
async def get_user_info(
    username: str,
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[UserDetailDTO]:
    """
    获取用户信息

    **功能说明:**
    - 根据用户名获取用户信息
    - 不返回密码和盐字段

    **请求参数:**
    - username: 用户名

    **返回数据:**
    - 用户信息（不包含密码和盐）
    """
    result = await user_service.get_user_by_username(username, session)
    logger.info(f"获取用户信息: {username}")
    return ok(data=result)


@router.put("/password")
async def change_password(
    data: ChangePasswordDTO,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ResponseResult[bool]:
    """
    修改密码

    **功能说明:**
    - 用户修改自己的密码
    - 需要验证旧密码

    **请求参数:**
    - oldPassword: 旧密码（已加密）
    - newPassword: 新密码（已加密）

    **返回数据:**
    - newPassword: 新密码（已加密，用于前端显示）
    """
    await user_service.change_password(
        current_user.id, data.oldPassword, data.newPassword, session  # type: ignore
    )
    logger.info(f"用户修改密码成功: user_id={current_user.id}")  # type: ignore
    return ok(data=True)


@router.post("/avatar")
async def update_avatar(
    avatar: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ResponseResult[str]:
    """
    更新用户头像

    **功能说明:**
    - 上传用户头像图片
    - 保存到服务器 public 目录
    - 返回头像 URL

    **请求参数:**
    - avatar: 头像文件

    **返回数据:**
    - 头像 URL
    """
    import os
    import uuid
    from config import app_config

    # 生成唯一文件名
    file_ext = os.path.splitext(avatar.filename or "avatar.png")[1]
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex}{file_ext}"  # type: ignore

    # 确保 public/avatars 目录存在
    avatars_dir = "data/public/avatars"
    os.makedirs(avatars_dir, exist_ok=True)

    # 保存文件
    file_path = os.path.join(avatars_dir, filename)
    with open(file_path, "wb") as f:
        content = await avatar.read()
        f.write(content)

    # 生成 URL
    avatar_url = f"/public/avatars/{filename}"

    # 更新数据库
    await user_service.update_user_avatar(current_user.id, avatar_url, session)  # type: ignore

    logger.info(f"用户更新头像成功: user_id={current_user.id}, url={avatar_url}")  # type: ignore
    return ok(data=avatar_url)
