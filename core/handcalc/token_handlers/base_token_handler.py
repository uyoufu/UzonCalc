from __future__ import annotations

import ast
from typing import Any
from core.handcalc.formatters.formatted_ast_node import FormattedAstNode

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.handcalc.token_handlers.handlers_factory import TokenHandlerFactory


class BaseTokenHandler:
    # 默认顺序
    # 数值越小优先级越高，只会调用第一个匹配的处理器
    order: int = 10000

    def __init__(self) -> None:
        self.ignore_tokens = set()

    def can_handle(self, ast_token: Any) -> bool:
        """
        Determine if this handler can process the given token.
        """
        if ast_token in self.ignore_tokens:
            return False

        return self.can_handle_core(ast_token)

    def can_handle_core(self, ast_token: Any) -> bool:
        raise NotImplementedError("Subclasses must implement can_handle_core method.")

    def handle(
        self, ast_token: Any, handlers: "TokenHandlerFactory"
    ) -> FormattedAstNode | None:
        """
        Process the given token and return the result.
        """
        raise NotImplementedError("Subclasses must implement handle method.")
