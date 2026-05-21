"""
函数调用过滤模块

管理需要隐藏的函数调用（如 await UI 等），
这些函数调用不会在计算书中显示输出。
"""

from __future__ import annotations

import ast
from typing import Callable, Optional, Set


# 函数调用过滤器类型定义
# 返回 True 表示应该隐藏该函数调用
CallFilterFunction = Callable[[ast.Call], bool]


class CallFilterRegistry:
    """函数调用过滤器注册表"""

    def __init__(self) -> None:
        # 简单的函数名集合（不带参数检查）
        self._simple_filters: Set[str] = set()
        # 复杂的过滤器函数（可以检查参数等）
        self._advanced_filters: list[CallFilterFunction] = []
        self._register_builtin_filters()

    def _register_builtin_filters(self) -> None:
        """注册内置的函数调用过滤器"""

        # UI 相关函数不应显示
        self.register_simple("UI")

        # 可以添加更多内置过滤器
        # self.register_simple("hide")
        # self.register_simple("show")

    def register_simple(self, func_name: str) -> None:
        """
        注册简单的函数名过滤器（仅根据函数名判断）

        Args:
            func_name: 需要隐藏的函数名称
        """
        self._simple_filters.add(func_name)

    def unregister_simple(self, func_name: str) -> None:
        """
        取消注册简单的函数名过滤器

        Args:
            func_name: 函数名称
        """
        self._simple_filters.discard(func_name)

    def register_advanced(self, filter_func: CallFilterFunction) -> None:
        """
        注册高级过滤器函数（可以进行复杂的判断）

        Args:
            filter_func: 过滤器函数，接收 AST Call 节点，返回是否应该隐藏
        """
        self._advanced_filters.append(filter_func)

    def should_hide_call(self, node: ast.Call) -> bool:
        """
        判断函数调用是否应该被隐藏

        Args:
            node: AST Call 节点

        Returns:
            是否应该隐藏该函数调用
        """
        # 提取函数名
        func_name = self._extract_func_name(node)

        # 检查简单过滤器
        if func_name and func_name in self._simple_filters:
            return True

        # 检查高级过滤器
        for filter_func in self._advanced_filters:
            try:
                if filter_func(node):
                    return True
            except Exception:
                # 过滤器异常时不隐藏，保证安全
                continue

        return False

    def _extract_func_name(self, node: ast.Call) -> Optional[str]:
        """
        从 Call 节点中提取函数名

        Args:
            node: AST Call 节点

        Returns:
            函数名称，如果无法提取则返回 None
        """
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            # 处理如 obj.method() 的情况
            return node.func.attr
        return None

    def list_simple_filters(self) -> list[str]:
        """
        列出所有简单过滤器的函数名

        Returns:
            函数名列表
        """
        return list(self._simple_filters)


# 全局函数调用过滤器注册表实例
_global_call_filter_registry: Optional[CallFilterRegistry] = None


def get_call_filter_registry() -> CallFilterRegistry:
    """获取全局函数调用过滤器注册表实例（单例模式）"""
    global _global_call_filter_registry
    if _global_call_filter_registry is None:
        _global_call_filter_registry = CallFilterRegistry()
    return _global_call_filter_registry


# 便捷函数
def register_hidden_function(func_name: str) -> None:
    """
    注册需要隐藏的函数名（便捷函数）

    Args:
        func_name: 函数名称
    """
    get_call_filter_registry().register_simple(func_name)


def register_call_filter(filter_func: CallFilterFunction) -> None:
    """
    注册高级调用过滤器（便捷函数）

    Args:
        filter_func: 过滤器函数
    """
    get_call_filter_registry().register_advanced(filter_func)


def should_hide_call(node: ast.Call) -> bool:
    """
    判断函数调用是否应该被隐藏（便捷函数）

    Args:
        node: AST Call 节点

    Returns:
        是否应该隐藏该函数调用
    """
    return get_call_filter_registry().should_hide_call(node)


# 示例：注册带 await 的 UI 调用过滤器
def _is_awaited_ui_call(parent_node: Optional[ast.AST], call_node: ast.Call) -> bool:
    """
    判断是否为 await UI(...) 形式的调用

    Args:
        parent_node: 父节点（如果有）
        call_node: Call 节点

    Returns:
        是否为 awaited UI 调用
    """
    # 检查是否为 UI 函数
    if isinstance(call_node.func, ast.Name) and call_node.func.id == "UI":
        # 检查父节点是否为 Await
        if parent_node and isinstance(parent_node, ast.Await):
            return True
    return False
