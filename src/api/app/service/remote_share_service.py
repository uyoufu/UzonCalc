"""Fetch public cross-backend shares through an SSRF-resistant HTTP boundary."""

from __future__ import annotations

import asyncio
import ipaddress
import json
import os
import re
import socket
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_share_dto import SharePreviewResDTO
from app.exception.custom_exception import raise_ex
from config import app_config

_SHARE_PATH_PATTERN = re.compile(
    r"^(?P<prefix>.*?/v1/calc-report)/shared/(?P<token>[^/]+)"
    r"(?:/(?:preview|import|archive|result))?/?$"
)
_MAX_REDIRECTS = 3
_PREVIEW_MAX_BYTES = 1024 * 1024


async def fetch_remote_share_preview(source: str) -> SharePreviewResDTO:
    """Fetch and validate an anonymous public share preview.

    Args:
        source: Remote backend preview, import, archive, or share base URL.

    Returns:
        Validated preview with an absolute remote result URL.

    Raises:
        CustomException: If the source is unsafe, inaccessible, or malformed.
    """
    endpoints = await _remote_share_endpoints(source)
    payload = await _fetch_limited(endpoints["preview"], _PREVIEW_MAX_BYTES)
    try:
        envelope = json.loads(payload)
        preview_data = envelope["data"]
        if not envelope.get("ok") or not isinstance(preview_data, dict):
            raise ValueError("remote response is not successful")
        execution = preview_data.get("recentExecution")
        if isinstance(execution, dict) and isinstance(execution.get("htmlPath"), str):
            execution["htmlPath"] = endpoints["result"]
        return SharePreviewResDTO.model_validate(preview_data)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise_ex(
            f"Remote share preview is invalid: {error}",
            code=502,
            error_code=CalcErrorCode.ARCHIVE_INVALID,
        )


async def fetch_remote_share_archive(source: str) -> tuple[bytes, str]:
    """Download a bounded public v4 archive and return its canonical source.

    Args:
        source: Remote backend preview, import, archive, or share base URL.

    Returns:
        Archive bytes and canonical preview URL used for future synchronization.

    Raises:
        CustomException: If the remote endpoint is unsafe or unavailable.
    """
    endpoints = await _remote_share_endpoints(source)
    archive_bytes = await _fetch_limited(
        endpoints["archive"], app_config.calc_report_max_total_size
    )
    return archive_bytes, endpoints["preview"]


async def _remote_share_endpoints(source: str) -> dict[str, str]:
    """Validate one source URL and derive fixed public-share endpoints.

    Args:
        source: User-provided remote share URL.

    Returns:
        Absolute preview, archive, and result endpoints.

    Raises:
        CustomException: If the URL shape or network destination is unsafe.
    """
    normalized = _normalize_url(source)
    await _validate_network_destination(normalized)
    parsed = urlsplit(normalized)
    match = _SHARE_PATH_PATTERN.fullmatch(parsed.path)
    if match is None:
        raise_ex("Remote share URL path is invalid", code=400)
    base_path = f"{match.group('prefix')}/shared/{match.group('token')}"
    return {
        suffix: urlunsplit(
            (parsed.scheme, parsed.netloc, f"{base_path}/{suffix}", "", "")
        )
        for suffix in ("preview", "archive", "result")
    }


async def _fetch_limited(url: str, max_bytes: int) -> bytes:
    """Fetch one URL with bounded redirects and response size.

    Args:
        url: Already validated initial HTTPS URL.
        max_bytes: Maximum accepted response bytes.

    Returns:
        Complete response bytes within the limit.

    Raises:
        CustomException: If a redirect, status, network error, or size is invalid.
    """
    current_url = url
    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=httpx.Timeout(15.0, connect=5.0),
            trust_env=False,
        ) as client:
            for redirect_count in range(_MAX_REDIRECTS + 1):
                await _validate_network_destination(current_url)
                async with client.stream("GET", current_url) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location or redirect_count >= _MAX_REDIRECTS:
                            raise_ex("Remote share redirect limit exceeded", code=502)
                        current_url = _normalize_url(urljoin(current_url, location))
                        continue
                    if response.status_code != 200:
                        raise_ex(
                            "Remote public share is unavailable",
                            code=502,
                            data={"remoteStatus": response.status_code},
                        )
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > max_bytes:
                        raise_ex(
                            "Remote share response exceeds the size limit", code=413
                        )
                    chunks: list[bytes] = []
                    total_size = 0
                    async for chunk in response.aiter_bytes():
                        total_size += len(chunk)
                        if total_size > max_bytes:
                            raise_ex(
                                "Remote share response exceeds the size limit", code=413
                            )
                        chunks.append(chunk)
                    return b"".join(chunks)
    except httpx.HTTPError as error:
        raise_ex(f"Remote share request failed: {error}", code=502)
    raise_ex("Remote public share is unavailable", code=502)


def _normalize_url(source: str) -> str:
    """Normalize a credential-free HTTPS URL.

    Args:
        source: Untrusted URL string.

    Returns:
        Canonical URL without a fragment.

    Raises:
        CustomException: If syntax, scheme, credentials, or host is invalid.
    """
    try:
        parsed = urlsplit(source.strip())
        port = parsed.port
    except ValueError as error:
        raise_ex(f"Remote share URL is invalid: {error}", code=400)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise_ex("Remote shares require an HTTPS URL", code=400)
    if parsed.username or parsed.password:
        raise_ex("Remote share URLs cannot contain credentials", code=400)
    hostname = parsed.hostname.encode("idna").decode("ascii").lower().rstrip(".")
    allowed_hosts = {
        value.strip().encode("idna").decode("ascii").lower().rstrip(".")
        for value in os.getenv("UZONCALC_REMOTE_SHARE_ALLOWED_HOSTS", "").split(",")
        if value.strip()
    }
    if allowed_hosts and hostname not in allowed_hosts:
        raise_ex("Remote share host is not allowed", code=403)
    netloc = f"[{hostname}]" if ":" in hostname else hostname
    if port is not None:
        netloc = f"{netloc}:{port}"
    return urlunsplit(("https", netloc, parsed.path or "/", parsed.query, ""))


async def _validate_network_destination(url: str) -> None:
    """Resolve a URL host and reject every non-public destination address.

    Args:
        url: Normalized HTTPS URL.

    Returns:
        None after all resolved addresses are confirmed globally routable.

    Raises:
        CustomException: If DNS fails or any destination address is non-public.
    """
    parsed = urlsplit(url)
    hostname = parsed.hostname
    if hostname is None:
        raise_ex("Remote share host is missing", code=400)
    try:
        literal = ipaddress.ip_address(hostname)
        addresses = {literal}
    except ValueError:
        try:
            records = await asyncio.to_thread(
                socket.getaddrinfo,
                hostname,
                parsed.port or 443,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as error:
            raise_ex(f"Remote share DNS lookup failed: {error}", code=502)
        addresses = {ipaddress.ip_address(record[4][0]) for record in records}
    if not addresses or any(not address.is_global for address in addresses):
        raise_ex("Remote share destination must use public IP addresses", code=403)
