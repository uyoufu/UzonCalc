from typing import Dict, Any, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from app.controller.users.user_dto import (
    UserInfoDTO,
    UserSignInResponseDTO,
    UserDetailDTO,
    get_access_token_payloads,
    get_refresh_token_payloads,
)
from app.db.models.user import User, UserStatus, UserRole
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

    user = cast(User, user)

    if user.status != UserStatus.Active.value:
        logger.warning(f"User is not active - {username}")
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

    access = [app_config.get_api_host_type()]
    if UserRole.Admin.value in user.roles:
        access.append(UserRole.Admin.value)
    user_count = await session.scalar(
        select(func.count(User.id)).where(User.status != UserStatus.Deleted.value)
    )
    if (user_count or 0) > 1:
        access.append("is_multi_user")

    logger.info(f"用户登录成功: {username}")
    # 返回用户信息和 tokens（不包含密码）
    return UserSignInResponseDTO(
        oid=user.oid,
        id=user.id,
        userInfo=UserInfoDTO(
            oid=user.oid,
            id=user.id,
            username=user.username,
            nickName=user.nickName,
            avatar=user.avatar,
            status=UserStatus(user.status),
            roles=list(user.roles),
        ),
        roles=user.roles,  # type: ignore
        access=access,
        accessToken=access_token,
        refreshToken=refresh_token,
        token=development_token,
        tokenType="Bearer",
        isLocalhost=app_config.is_desktop,
    )


async def register_user(
    *,
    username: str,
    password: str,
    session: AsyncSession,
    roles: list[str] | None = None,
    nick_name: str | None = None,
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
        raise_ex("Username already exists", code=400)
    # 加密密码
    hashed_password, salt = hash_password(password)
    # 创建新用户
    new_user = User(
        username=username,
        nickName=nick_name,
        password=hashed_password,
        salt=salt,
        status=UserStatus.Active.value,
        roles=roles or [UserRole.Regular.value],
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
        raise_ex("User not found", code=404)
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
        raise_ex("User not found", code=404)
    # 验证旧密码
    if not verify_password(old_password, user.password, user.salt):  # type: ignore
        logger.warning(f"修改密码失败: 旧密码错误 - user_id: {user_id}")
        raise_ex("Old password is incorrect", code=401)
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
        raise_ex("User not found", code=404)
    # 加密新密码
    hashed_password, salt = hash_password(new_password)
    # 更新密码和 salt
    user.password = hashed_password  # type: ignore
    user.salt = salt  # type: ignore
    await session.commit()
    logger.info(f"管理员重置用户密码成功: user_id: {user_id}")
    return True


async def get_user_detail(user_id: int, session: AsyncSession) -> UserDetailDTO:
    """Return the current user's complete safe profile.

    Args:
        user_id: Authenticated database user identifier.
        session: Active database session.

    Returns:
        Profile fields that do not expose password material.

    Raises:
        CustomException: If the user no longer exists.
    """
    user = await session.get(User, user_id)
    if user is None or user.status == UserStatus.Deleted.value:
        raise_ex("User not found", code=404)
    return UserDetailDTO(
        id=user.id,
        oid=user.oid,
        username=user.username,
        nickName=user.nickName,
        avatar=user.avatar,
        roles=list(user.roles),
        status=user.status,
        createdAt=user.createdAt,
        isSuperAdmin=UserRole.Admin.value in user.roles,
    )


async def update_user_profile(
    user_id: int, nick_name: str, session: AsyncSession
) -> UserDetailDTO:
    """Update the current user's nickname and return the new profile.

    Args:
        user_id: Authenticated database user identifier.
        nick_name: Validated non-blank display nickname.
        session: Active database session.

    Returns:
        The updated safe profile.

    Raises:
        CustomException: If the user no longer exists.
    """
    user = await session.get(User, user_id)
    if user is None or user.status == UserStatus.Deleted.value:
        raise_ex("User not found", code=404)
    user.nickName = nick_name.strip()
    await session.commit()
    return await get_user_detail(user_id, session)


async def update_user_avatar(
    user_id: int, avatar_url: str, session: AsyncSession
) -> bool:
    """
    更新用户头像
    :param user_id: 用户 ID
    :param avatar_url: 头像 URL
    :param session: 数据库会话
    :return: 是否更新成功
    """
    res = await session.execute(select(User).filter(User.id == user_id))
    user: User | None = res.scalars().first()
    if not user:
        raise_ex("User not found", code=404)
    # 更新头像
    user.avatar = avatar_url  # type: ignore
    await session.commit()
    logger.info(f"用户更新头像成功: user_id: {user_id}")
    return True
