from __future__ import annotations
from typing import Any, List

from core.handcalc.formatters.formatted_ast_node import FormattedAstNode
from core.handcalc.formatters.html_formatter import HTMLFormatter
from core.handcalc.token_handlers.base_token_handler import BaseTokenHandler

from core.handcalc.token_handlers.assign_handler import AssignHandler
from core.handcalc.token_handlers.attribute_handler import AttributeHandler
from core.handcalc.token_handlers.binop_handler import BinOpHandler
from core.handcalc.token_handlers.binop_pint_handler import BinOpPintHandler
from core.handcalc.token_handlers.call_handler import CallHandler
from core.handcalc.token_handlers.constant_handler import ConstantHandler
from core.handcalc.token_handlers.py_operator_handler import (
    AddOperatorHandler,
    DivOperatorHandler,
    MultOperatorHandler,
    SubOperatorHandler,
    PowOperatorHandler,
)
from core.handcalc.token_handlers.name_load_handler import NameLoadHandler
from core.handcalc.token_handlers.name_store_handler import NameStoreHandler
from core.handcalc.token_handlers.unaryop_handler import UnaryOpHandler


class TokenHandlerFactory:
    def __init__(self):
        self.handlers: List[BaseTokenHandler] = []
        self.is_sorted = True

        # 注册内置处理器
        self.__register_builtin_handlers()

        # 格式化器实例
        self.formatter = HTMLFormatter()

    # 注册系统内置处理器
    def __register_builtin_handlers(self):
        """
        集中注册所有内置的处理器
        方便维护和扩展
        """
        handler_types = [
            AssignHandler,
            AttributeHandler,
            BinOpHandler,
            BinOpPintHandler,
            CallHandler,
            ConstantHandler,
            NameLoadHandler,
            NameStoreHandler,
            UnaryOpHandler,
            AddOperatorHandler,
            SubOperatorHandler,
            MultOperatorHandler,
            DivOperatorHandler,
            PowOperatorHandler,
        ]
        for handler_type in handler_types:
            self.register_handler(handler_type)

    def register_handler(self, handler_type: type[BaseTokenHandler]) -> None:
        self.handlers.append(handler_type(self))
        self.is_sorted = False

    def handle(
        self, ast_node: Any, parent: Any | None = None
    ) -> FormattedAstNode | None:
        # 仅在需要时排序处理器
        if not self.is_sorted:
            self.handlers.sort(key=lambda h: h.order)
            self.is_sorted = True

        # 只调用第一个匹配的处理器
        for handler in self.handlers:
            if not handler.can_handle(ast_node, parent=parent):
                continue

            # 传入 self 作为 factory 参数
            result = handler.handle(ast_node, parent=parent)
            if result is not None:
                return result

        return None
