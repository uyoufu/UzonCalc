from datetime import datetime, timedelta
from typing import List

from pydantic import BaseModel
from config import app_config
import jwt
from .date_time_helper import get_utc_now


class TokenPayloads(BaseModel):
    """访问令牌负载数据模型"""

    oid: str
    id: int
    username: str
    roles: List[str]
    type: str | None = None
    iat: datetime | None = None
    exp: datetime | None = None


def generate_jwt(payloads: TokenPayloads, expires_in: int = 3600) -> str:
    """
    生成JWT token

    :param payload: 要编码到token中的数据
    :param expires_in: token过期时间（秒），默认为1小时
    :return: JWT token字符串
    """
    secret = app_config.token_secret
    algorithm = "HS256"
    now = get_utc_now()
    payloads.iat = now
    payloads.exp = now + timedelta(seconds=expires_in)
    token = jwt.encode(payloads.model_dump(), secret, algorithm=algorithm)
    return token


def verify_jwt(token: str) -> TokenPayloads | None:
    """
    验证JWT token

    :param token: JWT token字符串
    :return: 如果token有效，返回payload字典；否则返回None
    """
    secret = app_config.token_secret
    algorithm = "HS256"
    try:
        payload = jwt.decode(token.strip(), secret, algorithms=[algorithm])
        return TokenPayloads(**payload)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
