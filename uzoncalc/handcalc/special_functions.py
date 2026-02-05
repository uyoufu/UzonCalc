"""
特殊函数格式化模块

管理特殊函数名称（如 abs, sqrt 等）的格式化规则，
提供统一的注册和查询接口，方便扩展与维护。
"""

from __future__ import annotations

import ast
from typing import Callable, Optional, Sequence
from . import ir


# 特殊函数格式化器类型定义
SpecialFunctionFormatter = Callable[[str, Sequence[ir.MathNode]], Optional[ir.MathNode]]


class SpecialFunctionRegistry:
    """特殊函数格式化器注册表"""

    def __init__(self) -> None:
        self._formatters: dict[str, SpecialFunctionFormatter] = {}
        self._register_builtin_formatters()

    def _register_builtin_formatters(self) -> None:
        """注册内置的特殊函数格式化器"""
        
        # abs 函数：转换为绝对值符号 |x|
        def format_abs(func_name: str, args: Sequence[ir.MathNode]) -> Optional[ir.MathNode]:
            if len(args) == 1:
                return ir.mrow([ir.mo("|"), args[0], ir.mo("|")])
            return None
        
        # sqrt 函数：转换为平方根符号 √x
        def format_sqrt(func_name: str, args: Sequence[ir.MathNode]) -> Optional[ir.MathNode]:
            if len(args) == 1:
                return ir.msqrt(args[0])
            return None

        # 注册格式化器
        self.register("abs", format_abs)
        self.register("sqrt", format_sqrt)
        self.register("math.sqrt", format_sqrt)

    def register(self, func_name: str, formatter: SpecialFunctionFormatter) -> None:
        """
        注册特殊函数格式化器
        
        Args:
            func_name: 函数名称（如 "abs", "sqrt", "math.sqrt"）
            formatter: 格式化器函数，接收函数名和参数列表，返回格式化后的 IR 节点
        """
        self._formatters[func_name] = formatter

    def unregister(self, func_name: str) -> None:
        """
        取消注册特殊函数格式化器
        
        Args:
            func_name: 函数名称
        """
        self._formatters.pop(func_name, None)

    def format(self, func_name: str, args: Sequence[ir.MathNode]) -> Optional[ir.MathNode]:
        """
        尝试使用注册的格式化器格式化函数调用
        
        Args:
            func_name: 函数名称
            args: 参数列表（已转换为 IR 节点）
        
        Returns:
            格式化后的 IR 节点，如果没有匹配的格式化器则返回 None
        """
        formatter = self._formatters.get(func_name)
        if formatter is not None:
            return formatter(func_name, args)
        return None

    def is_special_function(self, func_name: str) -> bool:
        """
        检查函数名是否为已注册的特殊函数
        
        Args:
            func_name: 函数名称
        
        Returns:
            是否为特殊函数
        """
        return func_name in self._formatters

    def list_registered_functions(self) -> list[str]:
        """
        列出所有已注册的特殊函数名称
        
        Returns:
            特殊函数名称列表
        """
        return list(self._formatters.keys())


# 全局特殊函数注册表实例
_global_registry: Optional[SpecialFunctionRegistry] = None


def get_special_function_registry() -> SpecialFunctionRegistry:
    """获取全局特殊函数注册表实例（单例模式）"""
    global _global_registry
    if _global_registry is None:
        _global_registry = SpecialFunctionRegistry()
    return _global_registry


# 便捷函数
def register_special_function(func_name: str, formatter: SpecialFunctionFormatter) -> None:
    """
    注册特殊函数格式化器（便捷函数）
    
    Args:
        func_name: 函数名称
        formatter: 格式化器函数
    """
    get_special_function_registry().register(func_name, formatter)


def format_special_function(func_name: str, args: Sequence[ir.MathNode]) -> Optional[ir.MathNode]:
    """
    尝试格式化特殊函数（便捷函数）
    
    Args:
        func_name: 函数名称
        args: 参数列表（已转换为 IR 节点）
    
    Returns:
        格式化后的 IR 节点，如果没有匹配的格式化器则返回 None
    """
    return get_special_function_registry().format(func_name, args)
