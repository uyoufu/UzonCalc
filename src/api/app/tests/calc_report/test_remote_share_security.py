"""Security tests for cross-backend public share URL validation."""

import asyncio
import socket

import pytest

from app.exception.custom_exception import CustomException
from app.service.remote_share_service import _remote_share_endpoints


def test_remote_share_requires_https() -> None:
    """A remote link must not downgrade transport security."""
    with pytest.raises(CustomException, match="HTTPS"):
        asyncio.run(
            _remote_share_endpoints(
                "http://example.com/v1/calc-report/shared/token/preview"
            )
        )


def test_remote_share_rejects_private_dns_destination(monkeypatch) -> None:
    """A public-looking hostname resolving privately must be rejected."""

    def private_address(*_args, **_kwargs):
        """Return one loopback TCP address for the DNS validation path."""
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]

    monkeypatch.setattr(socket, "getaddrinfo", private_address)
    with pytest.raises(CustomException, match="public IP"):
        asyncio.run(
            _remote_share_endpoints(
                "https://example.com/v1/calc-report/shared/token/preview"
            )
        )


def test_remote_share_derives_fixed_endpoints(monkeypatch) -> None:
    """A safe source may only select the fixed preview/archive/result routes."""

    def public_address(*_args, **_kwargs):
        """Return one globally routable test address for DNS validation."""
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]

    monkeypatch.setattr(socket, "getaddrinfo", public_address)
    endpoints = asyncio.run(
        _remote_share_endpoints(
            "https://example.com/base/v1/calc-report/shared/token/import"
        )
    )

    assert endpoints == {
        "preview": "https://example.com/base/v1/calc-report/shared/token/preview",
        "archive": "https://example.com/base/v1/calc-report/shared/token/archive",
        "result": "https://example.com/base/v1/calc-report/shared/token/result",
    }
