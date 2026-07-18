import io
import os
import uuid

from fastapi import APIRouter, Depends, UploadFile, File
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.depends import get_session, get_current_user
from app.response.response_result import ResponseResult, ok
from config import logger
from app.exception.custom_exception import raise_ex
import app.service.user_service as user_service

from .user_dto import (
    UserSignInDTO,
    UserSignInResponseDTO,
    ChangePasswordDTO,
    UserDetailDTO,
    UserProfileUpdateDTO,
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


@router.get("/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[UserDetailDTO]:
    """Return the authenticated user's safe profile."""
    return ok(data=await user_service.get_user_detail(current_user.id, session))


@router.put("/me")
async def update_current_user_profile(
    data: UserProfileUpdateDTO,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[UserDetailDTO]:
    """Update the authenticated user's editable profile fields."""
    return ok(
        data=await user_service.update_user_profile(
            current_user.id, data.nickName, session
        )
    )


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
    allowed_media_types = {"image/png", "image/jpeg", "image/webp"}
    if avatar.content_type not in allowed_media_types:
        raise_ex("Avatar must be a PNG, JPEG, or WebP image", code=415)
    content = await avatar.read(2 * 1024 * 1024 + 1)
    if len(content) > 2 * 1024 * 1024:
        raise_ex("Avatar exceeds the 2 MiB limit", code=413)
    try:
        with Image.open(io.BytesIO(content)) as source:
            source.load()
            normalized = ImageOps.fit(source.convert("RGB"), (512, 512))
    except (UnidentifiedImageError, OSError, ValueError):
        raise_ex("Avatar image is invalid", code=400)

    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex}.png"
    avatars_dir = "data/public/avatars"
    os.makedirs(avatars_dir, exist_ok=True)
    file_path = os.path.join(avatars_dir, filename)
    normalized.save(file_path, format="PNG", optimize=True)
    avatar_url = f"/public/avatars/{filename}"
    previous_avatar = current_user.avatar
    await user_service.update_user_avatar(current_user.id, avatar_url, session)
    if previous_avatar and previous_avatar.startswith("/public/avatars/"):
        previous_path = os.path.join("data", previous_avatar.removeprefix("/public/"))
        if os.path.isfile(previous_path):
            os.remove(previous_path)
    logger.info(f"用户更新头像成功: user_id={current_user.id}, url={avatar_url}")
    return ok(data=avatar_url)
