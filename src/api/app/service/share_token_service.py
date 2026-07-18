"""Sign and verify stable public tokens for revocable share records."""

import base64
import hashlib
import hmac

from config import app_config


def create_signed_share_token(resource_kind: str, resource_oid: str) -> str:
    """Create a URL-safe token bound to one share record.

    Args:
        resource_kind: Stable namespace preventing cross-resource token reuse.
        resource_oid: Public identifier of the share record.

    Returns:
        URL-safe ``oid.signature`` token.

    Raises:
        None.
    """
    signature = _signature(resource_kind, resource_oid)
    return f"{resource_oid}.{signature}"


def verify_signed_share_token(resource_kind: str, token: str) -> str | None:
    """Validate a signed token and return its resource identifier.

    Args:
        resource_kind: Expected stable token namespace.
        token: Untrusted URL token.

    Returns:
        Resource OID when valid, otherwise ``None``.

    Raises:
        None.
    """
    try:
        resource_oid, signature = token.split(".", 1)
    except ValueError:
        return None
    if not hmac.compare_digest(signature, _signature(resource_kind, resource_oid)):
        return None
    return resource_oid


def _signature(resource_kind: str, resource_oid: str) -> str:
    """Return the compact HMAC signature for a namespaced resource."""
    message = f"{resource_kind}:{resource_oid}".encode("utf-8")
    digest = hmac.new(
        app_config.token_secret.encode("utf-8"), message, hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
