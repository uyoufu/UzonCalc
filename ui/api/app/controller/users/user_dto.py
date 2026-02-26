from pydantic import BaseModel, Field
from typing import Optional, List

from app.controller.dto_base import BaseDTO
from app.db.models.user import User, UserStatus
from utils.jwt_helper import TokenPayloads


class UserSignInDTO(BaseDTO):
    # 用户名
    username: str
    # 密码
    password: str
    # Pydantic 配置，允许额外字段
    model_config = {"extra": "allow"}


class UserInfoDTO(BaseDTO):
    oid: str
    id: int
    username: str
    name: str | None
    avatar: str | None
    status: UserStatus


class UserSignInResponseDTO(BaseDTO):
    """用户登录响应数据模型"""

    oid: str
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
    # 是否为本地登录，即单机版本的自动登录
    isLocalhost: bool = Field(default=False)


def get_access_token_payloads(user: User) -> TokenPayloads:
    """Return the payload for access token generation."""
    # support validating from an ORM model instance's attributes
    payloads = TokenPayloads.model_validate(user, from_attributes=True)
    payloads.type = "access"
    return payloads


def get_refresh_token_payloads(user: User) -> TokenPayloads:
    """Return the payload for refresh token generation."""
    access_payloads = get_access_token_payloads(user)
    access_payloads.type = "refresh"
    return access_payloads


class ChangePasswordDTO(BaseDTO):
    """修改密码请求数据模型"""

    oldPassword: str
    newPassword: str


class ChangePasswordResponseDTO(BaseDTO):
    """修改密码响应数据模型"""

    newPassword: str


class UserDetailDTO(BaseDTO):
    """用户详细信息数据模型（不包含密码和盐）"""

    id: int
    oid: str
    username: str
    name: str | None
    avatar: str | None
    roles: List[str]
    status: int
    createAt: str | None
    isSuperAdmin: bool
