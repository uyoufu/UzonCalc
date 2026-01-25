import bcrypt
from app.exception.custom_exception import raise_ex
from config import logger


def hash_password(password: str) -> tuple[str, str]:
    """
    使用 bcrypt 加密密码，并生成唯一的 salt

    :param password: 原始密码
    :return: (加密后的密码, salt值)
    """
    if not password:
        raise_ex("Password cannot be empty")

    # 生成随机的 salt
    salt = bcrypt.gensalt(rounds=12)
    # 加密密码
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    logger.info(f"密码加密成功")
    return hashed_password.decode("utf-8"), salt.decode("utf-8")


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    验证密码是否匹配

    :param password: 原始密码
    :param hashed_password: 加密后的密码    
    :param salt: 用于加密的 salt
    :return: 是否匹配
    """
    if not hashed_password or not password or not salt:
        return False

    # 使用相同的 salt 加密输入的密码
    hashed_input_password = bcrypt.hashpw(
        password.encode("utf-8"), salt.encode("utf-8")
    )
    is_match = hashed_input_password.decode("utf-8") == hashed_password
    return is_match
