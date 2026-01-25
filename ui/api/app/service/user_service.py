from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.controller.users.user_dto import UserInfoDTO, UserSignInResponseDTO, get_access_token_payloads, get_refresh_token_payloads
from app.db.models.user import (
    User,
    UserStatus,
    UserRole
)
from app.exception.custom_exception import raise_ex
from utils.password_helper import hash_password, verify_password
from utils.jwt_helper import generate_jwt
from config import logger, app_config


async def sign_in(
    username: str, password: str, session: AsyncSession
) -> UserSignInResponseDTO:
    """
    用户登录
    :param username: 用户名
    :param password: 密码
    :param session: 数据库会话
    :return: 包含用户信息和 tokens 的字典
    """
    # 查询用户
    user: User | None = await session.scalar(
        select(User).where(User.username == username)
    )
    # 验证用户是否存在
    if not user:
        logger.warning(f"User not found - {username}")
        raise_ex("Username or password is incorrect", code=401)

    assert user is not None

    # assert user is not None
    # 验证用户是否被删除
    if user.status == UserStatus.Deleted.value:  # type: ignore
        logger.warning(f"User deleted - {username}")
        raise_ex("Username or password is incorrect", code=401)
    # 验证密码
    if not verify_password(password, user.password, user.salt):  # type: ignore
        logger.warning(f"User login failed: Incorrect password - {username}")
        raise_ex("Username or password is incorrect", code=401)
    # 生成 tokens
    access_token = generate_jwt(
        get_access_token_payloads(user),
        expires_in=3600,  # 1 小时
    )
    refresh_token = generate_jwt(
        get_refresh_token_payloads(user),
        expires_in=604800,  # 7 天
    )

    development_token = ""
    # 若是测试环境，生成一个长期有效的调试 token
    if app_config.env == "dev":
        development_token = generate_jwt(
            get_access_token_payloads(user),  # type: ignore
            expires_in=86400,  # 1天
        )

    logger.info(f"用户登录成功: {username}")
    # 返回用户信息和 tokens（不包含密码）
    return UserSignInResponseDTO(
        _id=user._id,
        id=user.id,
        userInfo=UserInfoDTO(
            _id=user._id,
            id=user.id,
            username=user.username,
            name=user.name,
            avatar=user.avatar,
            status=UserStatus(user.status),
        ),
        roles=user.roles,  # type: ignore
        access=[],
        accessToken=access_token,
        refreshToken=refresh_token,
        token=development_token,
        tokenType="Bearer",
    )


async def register_user(
    *,
    username: str,
    password: str,
    session: AsyncSession,
    roles: list[str] = [UserRole.Regular.value],
) -> User:
    """
    用户注册（创建用户）
    :param username: 用户名
    :param password: 密码，该密码应是 sha256 加密后的字符串
    :param session: 数据库会话
    :return: 新建用户的信息
    """
    # 检查用户名是否已存在
    existing_user: User | None = await session.scalar(
        select(User).where(User.username == username)
    )
    if existing_user:
        logger.warning(f"用户注册失败: 用户名已存在 - {username}")
        raise_ex("用户名已存在", code=400)
    # 加密密码
    hashed_password, salt = hash_password(password)
    # 创建新用户
    new_user = User(
        username=username,
        password=hashed_password,
        salt=salt,
        status=UserStatus.Active.value,
        roles=roles,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    logger.info(f"用户注册成功: {username}")
    return new_user


async def get_user_by_id(user_id: int, session: AsyncSession) -> Dict[str, Any]:
    """
    根据 ID 获取用户信息（不包含密码）
    :param user_id: 用户 ID
    :param session: 数据库会话
    :return: 用户信息
    """
    res = await session.execute(select(User).filter(User.id == user_id))
    user: User | None = res.scalars().first()
    if not user or user.status == UserStatus.Deleted.value:  # type: ignore
        raise_ex("用户不存在", code=404)
    return {
        "user_id": user.id,  # type: ignore
        "userId": user.username,  # type: ignore
        "roles": user.roles,  # type: ignore
        "status": user.status,  # type: ignore
    }


async def change_password(
    user_id: int, old_password: str, new_password: str, session: AsyncSession
) -> bool:
    """
    用户修改自己的密码
    :param user_id: 用户 ID
    :param old_password: 旧密码
    :param new_password: 新密码
    :param session: 数据库会话
    :return: 是否修改成功
    """
    res = await session.execute(select(User).filter(User.id == user_id))
    user: User | None = res.scalars().first()
    if not user:
        raise_ex("用户不存在", code=404)
    # 验证旧密码
    if not verify_password(old_password, user.password, user.salt):  # type: ignore
        logger.warning(f"修改密码失败: 旧密码错误 - user_id: {user_id}")
        raise_ex("旧密码错误", code=401)
    # 加密新密码
    hashed_password, salt = hash_password(new_password)
    # 更新密码和 salt
    user.password = hashed_password  # type: ignore
    user.salt = salt  # type: ignore
    await session.commit()
    logger.info(f"用户修改密码成功: user_id: {user_id}")
    return True


async def reset_password(
    user_id: int, new_password: str, session: AsyncSession
) -> bool:
    """
    管理员为用户重置密码
    :param user_id: 用户 ID
    :param new_password: 新密码
    :param session: 数据库会话
    :return: 是否重置成功
    """
    res = await session.execute(select(User).filter(User.id == user_id))
    user: User | None = res.scalars().first()
    if not user:
        raise_ex("用户不存在", code=404)
    # 加密新密码
    hashed_password, salt = hash_password(new_password)
    # 更新密码和 salt
    user.password = hashed_password  # type: ignore
    user.salt = salt  # type: ignore
    await session.commit()
    logger.info(f"管理员重置用户密码成功: user_id: {user_id}")
    return True
