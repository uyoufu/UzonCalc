"""后处理器管道 - 使用自动发现机制"""

import importlib
import pkgutil
from typing import List
from core.handcalc.post_handlers.base_post_handler import BasePostHandler


def get_default_post_handlers() -> List[BasePostHandler]:
    """自动发现并加载所有后处理器"""
    handlers: List[BasePostHandler] = []

    # 获取当前包
    package_name = "core.handcalc.post_handlers"
    package = importlib.import_module(package_name)

    # 遍历包中的所有模块
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        # 跳过基类和当前模块
        if module_name in ("base_post_handler", "post_pipeline"):
            continue

        try:
            # 动态导入模块
            module = importlib.import_module(f"{package_name}.{module_name}")

            # 查找 BasePostHandler 的子类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BasePostHandler)
                    and attr is not BasePostHandler
                ):
                    # 实例化并添加到列表
                    handlers.append(attr())
        except Exception:
            # 忽略导入错误，继续处理其他模块
            pass

    # 按优先级执行（数值越小越靠前），同优先级按类名稳定排序，避免不同平台导入顺序差异
    handlers.sort(key=lambda h: (getattr(h, "priority", 100), h.__class__.__name__))
    return handlers
