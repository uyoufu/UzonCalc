from pydantic import BaseModel, Field
from typing import Optional, List

from app.db.models.user import User, UserStatus
from utils.jwt_helper import TokenPayloads


class UserSignInDTO(BaseModel):
    # 用户名
    username: str
    # 密码
    password: str
    # Pydantic 配置，允许额外字段
    model_config = {"extra": "allow"}


class UserInfoDTO(BaseModel):
    _id: str
    id: int
    username: str
    name: str | None
    avatar: str | None
    status: UserStatus


class UserSignInResponseDTO(BaseModel):
    """用户登录响应数据模型"""

    _id: str
    # 用户 ID
    id: int
    # 用户角色列表
    roles: List[str]
    # 访问权限列表
    access: List[str]
    # 访问令牌
    accessToken: str
    # 刷新令牌
    refreshToken: str
    # 测试令牌
    token: Optional[str] = None
    # 令牌类型
    tokenType: str = Field(default="Bearer")
    userInfo: UserInfoDTO


def get_access_token_payloads(user: User) -> TokenPayloads:
    """Return the payload for access token generation."""
    return TokenPayloads(
        _id=user._id,
        id=user.id,
        username=user.username,
        type="access",
        roles=user.roles,
    )


def get_refresh_token_payloads(user: User) -> TokenPayloads:
    """Return the payload for refresh token generation."""
    access_payloads = get_access_token_payloads(user)
    access_payloads.type = "refresh"
    return access_payloads
