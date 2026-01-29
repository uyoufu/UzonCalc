"""
沙箱执行模块

负责在隔离的沙箱环境中执行 UzonCalc 代码。
该模块可以独立运行或在容器中运行。

核心职责：
1. 动态加载计算函数（支持文件变化检测）
2. 管理异步生成器执行生命周期
3. 处理 UI 中断和恢复
4. 与外部通过 RPC 通信
"""

from .executor import CalcSandboxExecutor
from .generator_manager import GeneratorManager
from .module_loader import SandboxModuleLoader

__all__ = [
    "CalcSandboxExecutor",
    "GeneratorManager",
    "SandboxModuleLoader",
]
