"""Application business exceptions and response conversion."""

from ..response.response_result import ResponseResult
from typing import NoReturn

from app.i18n import _


class CustomException(Exception):
    """Carry localized user text and a stable machine-readable error code."""

    def __init__(self, code, message, data, error_code: str | None = None):
        """Initialize a business exception.

        Args:
            code: HTTP status code.
            message: Localized user-facing message.
            data: Optional structured diagnostics.
            error_code: Stable machine-readable error code.
        """
        super().__init__(message)
        self.__code = code
        self.__message = message
        self.__data = data
        self.__ok = code == 200
        self.__error_code = error_code

    @property
    def message(self):
        """Return the localized user-facing error message."""
        return self.__message

    @property
    def data(self):
        """Return optional structured error diagnostics."""
        return self.__data

    @property
    def code(self):
        """Return the HTTP status code."""
        return self.__code

    @property
    def error_code(self) -> str | None:
        """Return the stable machine-readable error code."""
        return self.__error_code

    def model_dump(self):
        """
        转换成 json
        :return:
        """
        return ResponseResult(
            ok=self.__ok,
            data=self.__data,
            message=self.__message,
            code=self.__code,
            errorCode=self.__error_code,
        ).model_dump(exclude_none=True)


# 抛出异常，没有返回值
def raise_ex(
    message: str,
    code: int = 500,
    data=None,
    error_code: str | None = None,
) -> NoReturn:
    """
    抛出异常
    :param message:
    :param code:
    :param data:
    """
    raise CustomException(code, _(message), data, error_code)
