"""Regression tests for explicit anonymous endpoints and default JWT protection."""

import asyncio
from types import SimpleNamespace

from fastapi import Depends, FastAPI, Request
import httpx
import pytest
from starlette.responses import JSONResponse, Response

from app.controller.calc.calc_report_import import (
    download_remote_calc_report_link,
    preview_remote_calc_report_link,
)
from app.controller.calc.calc_report_instance import (
    get_public_calc_report_instance,
    get_public_calc_report_instance_result,
)
from app.controller.calc.calc_report_share import (
    export_shared_calc_report,
    get_shared_calc_report_result,
    preview_shared_calc_report,
)
from app.controller.calc.code_format import format_python_with_ruff
from app.controller.calc.toc_page_numbers import get_toc_page_numbers
from app.controller.depends import get_optional_token_payload
from app.controller.desktop.desktop_controller import select_local_file
from app.controller.system.system_info import (
    get_desktop_auto_login,
    get_version,
)
from app.controller.users.user import sign_in
from app.exception.custom_exception import CustomException
from app.middleware import authentication
from app.middleware.authentication import (
    allow_anonymous,
    authenticate_non_api_request,
    is_anonymous_endpoint,
    require_route_authentication,
)


def create_auth_test_app() -> FastAPI:
    """Create a minimal application using the production authentication policy.

    Returns:
        A FastAPI application with public, optional, and protected routes.

    Raises:
        None.
    """
    app = FastAPI(dependencies=[Depends(require_route_authentication)])

    @app.exception_handler(CustomException)
    async def on_custom_exception(
        _request: Request, exception: CustomException
    ) -> JSONResponse:
        """Convert a custom authentication exception into its HTTP response."""
        return JSONResponse(
            status_code=exception.code, content=exception.model_dump()
        )

    @app.get("/anonymous")
    @allow_anonymous
    async def anonymous_route() -> dict[str, bool]:
        """Return a response without requiring authentication."""
        return {"ok": True}

    @app.get("/optional")
    @allow_anonymous
    async def optional_route(
        payload=Depends(get_optional_token_payload),
    ) -> dict[str, bool]:
        """Report whether optional authentication resolved a payload."""
        return {"isAuthenticated": payload is not None}

    @app.get("/protected")
    async def protected_route() -> dict[str, bool]:
        """Return a response only after global authentication succeeds."""
        return {"ok": True}

    return app


async def request_app(
    app: FastAPI, path: str, headers: dict[str, str] | None = None
) -> httpx.Response:
    """Send one in-process request to a FastAPI application.

    Args:
        app: ASGI application under test.
        path: Request path.
        headers: Optional request headers.

    Returns:
        The completed HTTP response.

    Raises:
        Exception: Propagates unhandled application errors.
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        return await client.get(path, headers=headers)


def test_anonymous_endpoint_bypasses_default_authentication() -> None:
    """A marked endpoint should be reachable without a token."""
    response = asyncio.run(request_app(create_auth_test_app(), "/anonymous"))

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_unmarked_endpoint_requires_authentication() -> None:
    """An unmarked endpoint should reject a request without credentials."""
    response = asyncio.run(request_app(create_auth_test_app(), "/protected"))

    assert response.status_code == 401


def test_unmarked_endpoint_accepts_valid_authentication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A protected endpoint should pass after global JWT validation."""
    monkeypatch.setattr(
        authentication, "verify_jwt", lambda _token: SimpleNamespace(id=1)
    )

    response = asyncio.run(
        request_app(
            create_auth_test_app(),
            "/protected",
            headers={"Authorization": "Bearer valid-token"},
        )
    )

    assert response.status_code == 200


def test_optional_auth_allows_missing_token() -> None:
    """A marked optional-auth endpoint should receive no anonymous payload."""
    response = asyncio.run(request_app(create_auth_test_app(), "/optional"))

    assert response.status_code == 200
    assert response.json() == {"isAuthenticated": False}


def test_optional_auth_rejects_invalid_provided_token() -> None:
    """Optional authentication must reject an invalid supplied credential."""
    response = asyncio.run(
        request_app(
            create_auth_test_app(),
            "/optional",
            headers={"Authorization": "Bearer invalid-token"},
        )
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "endpoint",
    [
        sign_in,
        get_version,
        get_desktop_auto_login,
        preview_remote_calc_report_link,
        download_remote_calc_report_link,
        get_public_calc_report_instance,
        get_public_calc_report_instance_result,
        preview_shared_calc_report,
        get_shared_calc_report_result,
        export_shared_calc_report,
    ],
)
def test_public_controller_endpoints_are_explicitly_marked(endpoint: object) -> None:
    """Every intended public controller endpoint should carry the marker."""
    assert is_anonymous_endpoint(endpoint)


@pytest.mark.parametrize(
    "endpoint",
    [format_python_with_ruff, get_toc_page_numbers, select_local_file],
)
def test_unannotated_utility_endpoints_remain_protected(endpoint: object) -> None:
    """Previously middleware-protected utility endpoints must remain private."""
    assert not is_anonymous_endpoint(endpoint)


def test_api_requests_skip_non_api_middleware() -> None:
    """API requests should defer authentication to the global dependency."""
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/protected",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("test", 80),
            "client": ("test", 123),
        }
    )

    async def call_next(_request: Request) -> Response:
        """Return a sentinel response when middleware permits the request."""
        return Response(status_code=204)

    response = asyncio.run(authenticate_non_api_request(request, call_next))

    assert response.status_code == 204


def test_mounted_non_api_request_remains_protected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The engineering mount should still require a token in web mode."""
    monkeypatch.setattr(
        authentication, "app_config", SimpleNamespace(is_desktop=False)
    )
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/engineering/mcp",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("test", 80),
            "client": ("test", 123),
        }
    )

    async def call_next(_request: Request) -> Response:
        """Fail if protected mounted traffic reaches the downstream app."""
        raise AssertionError("Protected mounted request reached call_next")

    with pytest.raises(CustomException) as exception_info:
        asyncio.run(authenticate_non_api_request(request, call_next))

    assert exception_info.value.code == 401
