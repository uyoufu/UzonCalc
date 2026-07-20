"""Encrypt sensitive persisted locators using the configured service secret."""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from config import app_config


def encrypt_persisted_secret(value: str) -> str:
    """Encrypt one UTF-8 value for application-owned database storage.

    Args:
        value: Plaintext secret.

    Returns:
        Authenticated URL-safe ciphertext.

    Raises:
        ValueError: If the supplied value is empty.
    """
    if not value:
        raise ValueError("Persisted secret cannot be empty")
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_persisted_secret(value: str) -> str:
    """Decrypt one application-owned database secret.

    Args:
        value: Authenticated URL-safe ciphertext.

    Returns:
        Decrypted UTF-8 value.

    Raises:
        ValueError: If the ciphertext is corrupt or signed by another secret.
    """
    try:
        return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError, UnicodeEncodeError) as error:
        raise ValueError("Persisted secret cannot be decrypted") from error


def _fernet() -> Fernet:
    """Build the deterministic Fernet primitive for persisted locators."""
    digest = hashlib.sha256(
        f"uzoncalc:persisted-secret:{app_config.token_secret}".encode("utf-8")
    ).digest()
    return Fernet(base64.urlsafe_b64encode(digest))
