from typing import Any, Callable, Optional
from contextvars import ContextVar
import asyncio
from .utils.ui import Window

# Observer callback for context creation (used by sandbox runner)
_execution_observer: ContextVar[Optional[Callable[[Any], None]]] = ContextVar(
    "execution_observer", default=None
)


class InteractionState:
    """
    Holds state related to UI interaction within a CalcContext.
    """

    def __init__(self):
        self.input_future: Optional[asyncio.Future] = None
        self.required_ui: Window | None = None  # Window definition

    @property
    def is_waiting_for_input(self) -> bool:
        """Check if the context is currently waiting for input."""
        return (
            self.required_ui is not None
            and self.input_future is not None
            and not self.input_future.done()
        )

    def prepare_request(self):
        """Initialize future for a UI request."""
        loop = asyncio.get_running_loop()
        if self.input_future is None or self.input_future.done():
            self.input_future = loop.create_future()

    async def wait_for_input(self) -> dict:
        """
        Wait for the input future to be completed.
        Returns:
            The input data dictionary provided by the user.
        """
        if self.input_future is None:
            raise RuntimeError("Input future not initialized")
        return await self.input_future

    def set_input(self, data: dict):
        """Set the result for the input future."""
        if self.input_future and not self.input_future.done():
            self.input_future.set_result(data)

    def clear(self):
        """Clear the interaction state."""
        self.required_ui = None
        self.input_future = None


def notify_observer(ctx: Any):
    """Notify the execution observer if one is set."""
    observer = _execution_observer.get()
    if observer:
        observer(ctx)
