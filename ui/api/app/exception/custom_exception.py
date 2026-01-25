from ..response.response_result import ResponseResult


class CustomException(Exception):
    def __init__(self, code, message, data):
        super().__init__(message)
        self.__code = code
        self.__message = message
        self.__data = data
        self.__ok = code == 200

    @property
    def message(self):
        return self.__message

    @property
    def data(self):
        return self.__data

    @property
    def code(self):
        return self.__code

    def model_dump(self):
        """
        转换成 json
        :return:
        """
        return ResponseResult(
            ok=self.__ok, data=self.__data, message=self.__message, code=self.__code
        ).model_dump(exclude_none=True)


def raise_ex(message, code=500, data=None):
    """
    抛出异常
    :param message:
    :param code:
    :param data:
    """
    raise CustomException(code, message, data)
