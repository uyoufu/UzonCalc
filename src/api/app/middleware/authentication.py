"""Define explicit anonymous-route markers and default request authentication."""

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from fastapi import Request
from starlette.responses import Response

from app.controller.depends import get_request_token
from app.exception.custom_exception import raise_ex
from app.i18n import _
from config import app_config
from utils.jwt_helper import verify_jwt


_ALLOW_ANONYMOUS_ATTRIBUTE = "__uzoncalc_allow_anonymous__"
EndpointCallable = TypeVar("EndpointCallable", bound=Callable[..., Any])
CallNext = Callable[[Request], Awaitable[Response]]


def allow_anonymous(endpoint: EndpointCallable) -> EndpointCallable:
    """Mark one FastAPI endpoint as accessible without authentication.

    Args:
        endpoint: Path-operation function to expose anonymously.

    Returns:
        The same endpoint with the anonymous-access marker attached.

    Raises:
        None.
    """
    setattr(endpoint, _ALLOW_ANONYMOUS_ATTRIBUTE, True)
    return endpoint


def is_anonymous_endpoint(endpoint: object | None) -> bool:
    """Return whether an endpoint carries the anonymous-access marker.

    Args:
        endpoint: Resolved endpoint object from the ASGI request scope.

    Returns:
        ``True`` when the endpoint was decorated with :func:`allow_anonymous`.

    Raises:
        None.
    """
    return bool(getattr(endpoint, _ALLOW_ANONYMOUS_ATTRIBUTE, False))


def require_route_authentication(request: Request) -> None:
    """Enforce JWT authentication unless the resolved endpoint allows anonymity.

    FastAPI dependencies run after route matching, so ``scope["endpoint"]`` is
    available here even though it is unavailable to outer HTTP middleware.

    Args:
        request: Current request with its resolved endpoint in the ASGI scope.

    Returns:
        None after the route is authorized.

    Raises:
        CustomException: If a protected route has no valid JWT.
    """
    if is_anonymous_endpoint(request.scope.get("endpoint")):
        return
    _verify_request_jwt(request)


async def authenticate_non_api_request(
    request: Request, call_next: CallNext
) -> Response:
    """Preserve authentication for mounted non-API applications.

    API path operations are authenticated by the global FastAPI dependency,
    while mounted applications such as the engineering MCP remain outside that
    dependency boundary and retain the previous middleware protection.

    Args:
        request: Current HTTP request.
        call_next: Next ASGI middleware or application handler.

    Returns:
        The downstream HTTP response when access is allowed.

    Raises:
        CustomException: If a protected non-API request has no valid JWT.
    """
    if request.url.path.startswith("/api/"):
        return await call_next(request)

    if request.url.path == "/":
        return await call_next(request)

    if app_config.is_desktop:
        return await call_next(request)

    ignored_path_prefixes = (
        "/public",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    )
    if request.url.path.startswith(ignored_path_prefixes):
        return await call_next(request)

    _verify_request_jwt(request)
    return await call_next(request)


def _verify_request_jwt(request: Request) -> None:
    """Validate the JWT carried by one request.

    Args:
        request: Request containing a bearer header or token query parameter.

    Returns:
        None when the token is valid.

    Raises:
        CustomException: If the token is absent, invalid, or expired.
    """
    token = get_request_token(request)
    if not verify_jwt(token):
        raise_ex(_("Authorization failed!"), code=401)
