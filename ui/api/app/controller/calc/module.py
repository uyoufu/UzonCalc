from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.depends import get_session
from app.response.response_result import ResponseResult, ok
from config import logger
import app.service.user_service as user_service

router = APIRouter(
    prefix="/v1/calc/module",
    tags=["calc_module"],
)


@router.post("")
async def upload_module(
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

    async with session:
        # 调用 Service 层完成登录业务逻辑
        result = await user_service.sign_in(data.username, data.password, session)
        logger.info(f"用户登录请求处理完成: {data.username}")
        # 返回成功响应
        return ok(data=result)
