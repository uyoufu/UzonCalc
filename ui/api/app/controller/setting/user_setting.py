"""
用户设置控制器
处理用户设置的 CRUD 操作
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional, Any
from app.controller.depends import get_session, get_token_payload
from app.controller.setting.setting_dto import UserSettingUpsertDTO
from app.response.response_result import ResponseResult, ok
from app.service import user_setting_service
from config import logger
from utils.jwt_helper import TokenPayloads

router = APIRouter(
    prefix="/v1/user-settings",
    tags=["user-settings"],
)


@router.get("/{key}")
async def get_user_setting(
    key: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[Optional[dict[str, Any]]]:
    """
    获取用户设置的 value

    **功能说明:**
    - 根据 key 获取指定的用户设置的 value
    - 只能获取自己的设置
    - 如果设置不存在，返回 null

    **认证:**
    - 需要有效的 Authorization token

    **路径参数:**
    - key: 设置键名

    **返回数据:**
    - 设置的 value（JSON 对象），如果不存在返回 null
    """
    value = await user_setting_service.get_user_setting(
        tokenPayloads.id, key, session
    )
    logger.debug(f"获取用户设置: userId={tokenPayloads.id}, key={key}, exists={value is not None}")
    return ok(data=value)


@router.put("/{key}")
async def upsert_user_setting(
    key: str,
    data: UserSettingUpsertDTO,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[dict[str, Any]]:
    """
    更新或创建用户设置（Upsert）

    **功能说明:**
    - 更新指定 key 的用户设置
    - 如果设置不存在则自动创建
    - 只能更新自己的设置

    **认证:**
    - 需要有效的 Authorization token

    **路径参数:**
    - key: 设置键名

    **请求参数:**
    - value: 设置值，JSON 对象（必填）
    - description: 设置描述（可选）

    **返回数据:**
    - 设置的 value（JSON 对象）
    """
    value = await user_setting_service.upsert_user_setting(
        tokenPayloads.id, key, data.value, data.description, session
    )
    logger.info(f"Upsert 用户设置: userId={tokenPayloads.id}, key={key}")
    return ok(data=value)


@router.delete("/{key}")
async def delete_user_setting(
    key: str,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> ResponseResult[None]:
    """
    删除用户设置

    **功能说明:**
    - 删除指定 key 的用户设置
    - 只能删除自己的设置

    **认证:**
    - 需要有效的 Authorization token

    **路径参数:**
    - key: 设置键名

    **错误处理:**
    - 404: 设置不存在
    """
    await user_setting_service.delete_user_setting(
        tokenPayloads.id, key, session
    )
    logger.info(f"删除用户设置: userId={tokenPayloads.id}, key={key}")
    return ok(data=None)
