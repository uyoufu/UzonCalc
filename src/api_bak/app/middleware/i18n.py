from typing import Callable

from fastapi import Request
from starlette.responses import Response

from app.i18n import reset_locale, select_locale, set_locale


async def i18n_middleware(request: Request, call_next: Callable) -> Response:
    locale = select_locale(
        request.query_params.get("lang"),
        request.headers.get("Accept-Language"),
    )
    request.state.locale = locale
    token = set_locale(locale)
    try:
        return await call_next(request)
    finally:
        reset_locale(token)
