from typing import TypeVar, Generic
from pydantic import BaseModel

from app.i18n import _

T = TypeVar("T")


class ResponseResult(BaseModel, Generic[T]):
    ok: bool
    data: T | None = None
    message: str | None = None
    code: int = 200


def ok(
    data: T | None = None, message: str = "success", code: int = 200
) -> ResponseResult[T]:
    return ResponseResult[T](ok=True, data=data, message=_(message), code=code)


def fail(
    message: str | None = None, data: T | None = None, code: int = 500
) -> ResponseResult[T]:
    return ResponseResult[T](
        ok=False, data=data, message=_(message) if message else message, code=code
    )
