from typing import AsyncGenerator
from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.manager import get_db_manager
from app.db.models.user import User, UserStatus
from app.exception.custom_exception import raise_ex
from utils.jwt_helper import TokenPayloads, verify_jwt
from config import logger


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    depend for getting a database session
    it yields an AsyncSession instance from the db manager
    """
    async with get_db_manager().session() as session:
        yield session


def get_request_token(request: Request) -> str:
    """
    从请求头或查询参数中获取 token

    优先从 Authorization 请求头获取，如果不存在，则从查询参数中获取。
    支持 "Bearer token" 格式或直接 token

    :param request: FastAPI Request 对象
    :param authorization: Authorization 请求头
    :return: token 字符串
    :raises: CustomException 如果 token 不存在或无效
    """
    token: str | None = request.headers.get("Authorization")

    # 首先尝试从 Authorization 请求头获取
    if not token:
        # 如果请求头中没有，则从查询参数中获取
        token = request.query_params.get("token")

    if not token:
        raise_ex("Authorization header or token parameter is required", code=401)

    token = token.strip()  # type: ignore
    # 如果包含空格，则取空格后的部分（处理 "Bearer token" 格式）
    if " " in token:
        token = token.split(" ")[1]

    return token


def get_token_payload(token: str = Depends(get_request_token)) -> TokenPayloads:
    """
    验证并解析 token，返回 payload

    :param token: JWT token 字符串
    :return: token 中的 payload 数据
    :raises: CustomException 如果 token 无效或过期
    """
    payload = verify_jwt(token)
    if not payload:
        raise_ex("Invalid or expired token", code=401)
    return payload  # type: ignore


async def get_current_user(
    payload: TokenPayloads = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    获取当前登录用户

    依赖链:
    - get_token_from_header: 从请求头获取 token
    - get_token_payload: 验证并解析 token
    - 查询数据库获取完整用户信息

    :param payload: token 中的 payload 数据
    :param session: 数据库会话
    :return: 当前用户对象
    :raises: CustomException 如果用户不存在或已被删除
    """
    user_id = payload.oid
    if not user_id:
        logger.warning("Token payload missing user ID")
        raise_ex("Invalid token: missing user ID", code=401)

    # 从数据库查询完整用户信息
    result = await session.execute(select(User).where(User.oid == user_id))
    user = result.scalars().first()

    if not user:
        logger.warning(f"User not found: {user_id}")
        raise_ex("User not found", code=404)

    assert user is not None  # 帮助类型检查器理解

    if user.status == UserStatus.Deleted:
        logger.warning(f"User deleted: {user_id}")
        raise_ex("User has been deleted", code=403)

    return user  # type: ignore
