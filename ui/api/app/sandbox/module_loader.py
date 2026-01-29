"""
沙箱模块加载器

支持：
- 动态导入 .py 文件
- 自动检测文件变化（mtime）
- 缓存管理
- 导入路径管理
"""

import importlib.util
import os
import sys
import inspect
from typing import Callable, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
from uzoncalc import *


class SandboxModuleLoader:
    """
    安全的模块加载器，支持动态加载和缓存管理
    """

    def __init__(
        self, safe_dirs: Optional[list[str]] = None, root_dir: Optional[str] = None
    ):
        """
        Args:
            safe_dirs: 允许加载的目录白名单（None 表示不限制）
            root_dir: 根目录路径，用于计算缓存 key 的相对路径（默认为当前工作目录）
        """
        self.safe_dirs = safe_dirs or []
        self.root_dir = os.path.abspath(root_dir or os.getcwd())
        # cache: {relative_path: (module, mtime, load_time)}
        self._cache: dict[str, Tuple[Any, float, datetime]] = {}

    def _validate_path(self, file_path: str) -> bool:
        """验证文件路径是否在白名单中"""
        if not self.safe_dirs:
            return True

        abs_path = os.path.abspath(file_path)
        return any(
            abs_path.startswith(os.path.abspath(safe_dir))
            for safe_dir in self.safe_dirs
        )

    def _get_mtime(self, file_path: str) -> float:
        """获取文件修改时间"""
        return os.path.getmtime(file_path)

    def _get_cache_key(self, abs_path: str) -> str:
        """计算相对于根目录的缓存 key"""
        try:
            return os.path.relpath(abs_path, self.root_dir)
        except ValueError:
            # 如果在不同的驱动器上，返回绝对路径
            return abs_path

    def _find_functions_with_decorator(self, module: Any) -> list[tuple[str, Callable]]:
        """查找模块中带有 @uzon_calc 装饰器的函数"""
        functions = []
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if getattr(obj, "_uzon_calc_entry", False):
                functions.append((name, obj))
        return functions

    def _has_decorator(self, func: Callable) -> bool:
        """检查函数是否有 @uzon_calc 装饰器

        通过检查 _uzon_calc_entry 属性来判断函数是否被 @uzon_calc 装饰器标记。
        该属性由 uzoncalc 包中的装饰器设置。
        """
        return getattr(func, "_uzon_calc_entry", False)

    def load_function(
        self,
        file_path: str,
        func_name: Optional[str] = None,
        force_reload: bool = False,
    ) -> Callable | list[tuple[str, Callable]]:
        """
        加载文件中的函数

        Args:
            file_path: Python 文件路径
            func_name: 函数名称（可选）。若为空，则查找所有带 @uzon_calc 装饰器的函数；
                      若非空，查找到函数后检查是否有 @uzon_calc 装饰器
            force_reload: 是否强制重新加载

        Returns:
            若 func_name 非空，返回函数对象；若 func_name 为空，返回 (name, func) 元组列表

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 路径不安全或函数不存在或函数无装饰器
            ImportError: 导入失败
        """
        # 路径验证
        if not self._validate_path(file_path):
            raise ValueError(f"Path not in safe directories: {file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        abs_path = os.path.abspath(file_path)
        cache_key = self._get_cache_key(abs_path)
        current_mtime = self._get_mtime(abs_path)

        # 检查缓存
        if not force_reload and cache_key in self._cache:
            module, cached_mtime, _ = self._cache[cache_key]
            if current_mtime == cached_mtime:
                return self._get_function_from_module(module, func_name)

        # 加载模块
        spec = importlib.util.spec_from_file_location(
            f"__sandbox_module_{abs(hash(abs_path))}",
            abs_path,
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from: {abs_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        # 缓存
        self._cache[cache_key] = (module, current_mtime, datetime.now())
        return self._get_function_from_module(module, func_name)

    def _get_function_from_module(
        self, module: Any, func_name: Optional[str]
    ) -> Callable | list[tuple[str, Callable]]:
        """从模块中获取函数

        Args:
            module: 导入的模块
            func_name: 可选的函数名。若为 None，返回所有带 @uzon_calc 装饰器的函数列表；
                      若指定，返回该函数（需验证其有装饰器）

        Returns:
            - func_name 为 None：返回 [(name, func), ...] 列表
            - func_name 非 None：返回单个函数对象

        Raises:
            ValueError: 函数不存在、不可调用或缺少装饰器
        """
        if func_name is None:
            # 查找所有带 @uzon_calc 装饰器的函数
            functions = self._find_functions_with_decorator(module)
            if not functions:
                raise ValueError(
                    "No functions with @uzon_calc decorator found in module"
                )
            return functions

        # 验证指定函数
        if not hasattr(module, func_name):
            raise ValueError(f"Function '{func_name}' not found in module")

        func = getattr(module, func_name)

        if not callable(func):
            raise ValueError(f"'{func_name}' is not a callable")

        if not self._has_decorator(func):
            raise ValueError(
                f"Function '{func_name}' does not have @uzon_calc decorator"
            )

        return func

    def get_cache_info(self) -> dict:
        """获取缓存信息"""
        return {
            "cached_modules": len(self._cache),
            "modules": [
                {
                    "path": path,
                    "loaded_at": load_time.isoformat(),
                    "mtime": mtime,
                }
                for path, (_, mtime, load_time) in self._cache.items()
            ],
        }

    def clear_cache(self, file_path: Optional[str] = None):
        """
        清除缓存

        Args:
            file_path: 指定文件路径清除，None 表示清除所有
        """
        if file_path is None:
            self._cache.clear()
        else:
            abs_path = os.path.abspath(file_path)
            cache_key = self._get_cache_key(abs_path)
            self._cache.pop(cache_key, None)

    def invalidate_cache(self, file_path: str):
        """强制使文件缓存失效"""
        self.clear_cache(file_path)
