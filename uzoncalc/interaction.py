from typing import Any, Callable, Optional, TYPE_CHECKING
from contextvars import ContextVar
import asyncio


class InteractionState:
    """
    Holds state related to UI interaction within a CalcContext.
    """

    def __init__(self):
        # 外部调用输入字段数据
        self.input_future: Optional[asyncio.Future] = None
        # 内部调用返回结果
        self.result_future: Optional[asyncio.Future] = None

    def set_input_feature(self):
        """Initialize future for a UI request."""
        loop = asyncio.get_running_loop()
        if self.input_future is None or self.input_future.done():
            self.input_future = loop.create_future()

    async def wait_for_input(self) -> dict[str, dict[str, Any]]:
        """
        Wait for the input future to be completed.
        Returns:
            The input data dictionary provided by the user.
        """
        if self.input_future is None:
            raise RuntimeError("Input future not initialized")
        return await self.input_future

    def set_inputs(self, data: dict[str, dict[str, Any]]):
        """Set the result for the input future."""
        if self.input_future and not self.input_future.done():
            self.input_future.set_result(data)

    def set_result_future(self, future: asyncio.Future):
        """Set the result future for internal calls."""
        # 前一个可能未完成，直接覆盖
        # TODO: 是否需要取消前一个 future？
        self.result_future = future

    def set_result(self, result: Any):
        """Set the result for the result future."""
        if self.result_future and not self.result_future.done():
            self.result_future.set_result(result)
