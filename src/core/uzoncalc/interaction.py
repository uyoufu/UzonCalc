"""Async interaction state owned by a calculation context."""

from typing import Any
import asyncio

InputValues = dict[str, dict[str, Any]]


class InteractionState:
    """Hold pending UI input and execution-result futures."""

    def __init__(self) -> None:
        """Initialize an interaction state without pending futures."""
        # 外部调用输入字段数据
        self.input_future: asyncio.Future[InputValues] | None = None
        # 内部调用返回结果
        self.result_future: asyncio.Future[Any] | None = None

    def set_input_future(self) -> asyncio.Future[InputValues]:
        """Create or return the pending future for a UI request.

        Returns:
            Pending future that receives the next UI input payload.

        Raises:
            RuntimeError: If called without a running event loop.
        """
        loop = asyncio.get_running_loop()
        if self.input_future is None or self.input_future.done():
            self.input_future = loop.create_future()
        return self.input_future

    async def wait_for_input(self) -> InputValues:
        """Wait for the input future to be completed.

        Returns:
            The input data dictionary provided by the user.

        Raises:
            RuntimeError: If the input future has not been initialized.
        """
        if self.input_future is None:
            raise RuntimeError("Input future not initialized")
        return await self.input_future

    def set_inputs(self, data: InputValues) -> None:
        """Resolve the pending input future when one exists.

        Args:
            data: Input values grouped by UI window title.

        Returns:
            None.

        Raises:
            No exceptions are intentionally raised.
        """
        if self.input_future and not self.input_future.done():
            self.input_future.set_result(data)

    def set_result_future(self, future: asyncio.Future[Any]) -> None:
        """Set the result future without discarding pending consumers.

        Args:
            future: Future that receives execution results.

        Returns:
            None.

        Raises:
            RuntimeError: If a different result future is still pending.
        """
        if (
            self.result_future is not None
            and not self.result_future.done()
            and self.result_future is not future
        ):
            raise RuntimeError("Cannot replace a pending result future")
        self.result_future = future

    def set_result(self, result: Any) -> None:
        """Resolve the pending execution-result future when one exists.

        Args:
            result: Execution state or payload delivered to the caller.

        Returns:
            None.

        Raises:
            No exceptions are intentionally raised.
        """
        if self.result_future and not self.result_future.done():
            self.result_future.set_result(result)
