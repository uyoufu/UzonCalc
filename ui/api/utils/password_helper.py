import hashlib
import hmac
import secrets

from app.exception.custom_exception import raise_ex
from config import logger

_PBKDF2_ITERATIONS = 210_000
_PBKDF2_ALGORITHM = "sha256"
_SALT_BYTES = 16


def _derive_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        _PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )


def hash_password(password: str) -> tuple[str, str]:
    """
    使用 PBKDF2-SHA256 加密密码，并生成唯一的 salt

    :param password: 原始密码
    :return: (加密后的密码, salt值)
    """
    if not password:
        raise_ex("Password cannot be empty")

    salt = secrets.token_bytes(_SALT_BYTES)
    hashed_password = _derive_password(password, salt)
    logger.info("密码加密成功")
    return hashed_password.hex(), salt.hex()


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

    try:
        salt_bytes = bytes.fromhex(salt)
        expected_hash = bytes.fromhex(hashed_password)
    except ValueError:
        return False

    actual_hash = _derive_password(password, salt_bytes)
    return hmac.compare_digest(actual_hash, expected_hash)
