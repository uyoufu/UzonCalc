"""Common API response envelopes."""

from typing import Generic, TypeVar
from pydantic import BaseModel, SerializerFunctionWrapHandler, model_serializer

from app.i18n import _

T = TypeVar("T")


class ResponseResult(BaseModel, Generic[T]):
    """Wrap successful and failed API responses in one stable shape."""

    ok: bool
    data: T | None = None
    message: str | None = None
    code: int = 200
    errorCode: str | None = None

    @model_serializer(mode="wrap")
    def serialize_response(self, handler: SerializerFunctionWrapHandler) -> dict:
        """Omit an absent machine error code from the public JSON envelope.

        Args:
            handler: Pydantic's standard model serializer.

        Returns:
            Serialized response with ``errorCode`` only when populated.
        """
        payload = handler(self)
        if self.errorCode is None:
            payload.pop("errorCode", None)
        return payload


def ok(
    data: T | None = None, message: str = "success", code: int = 200
) -> ResponseResult[T]:
    """Build a localized successful response.

    Args:
        data: Optional response payload.
        message: Stable English gettext message ID.
        code: HTTP-compatible business status code.

    Returns:
        Successful response envelope.
    """
    return ResponseResult[T](ok=True, data=data, message=_(message), code=code)


def fail(
    message: str | None = None,
    data: T | None = None,
    code: int = 500,
    error_code: str | None = None,
) -> ResponseResult[T]:
    """Build a localized failed response.

    Args:
        message: Stable English gettext message ID.
        data: Optional structured diagnostics.
        code: HTTP-compatible business status code.
        error_code: Stable machine-readable error code.

    Returns:
        Failed response envelope.
    """
    return ResponseResult[T](
        ok=False,
        data=data,
        message=_(message) if message else message,
        code=code,
        errorCode=error_code,
    )
