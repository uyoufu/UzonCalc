from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import os
import sys
from types import ModuleType
from typing import Optional, Any


_dynamic_import_lock = asyncio.Lock()


class _ModuleCache:
    """
    模块缓存，用于存储已加载的模块和文件元数据
    """

    def __init__(self):
        # 缓存结构: {script_path: {"module": ModuleType, "mtime": float, "hash": str}}
        self._cache: dict[str, dict[str, Any]] = {}

    def _get_file_hash(self, path: str) -> str:
        """计算文件内容的 SHA256 哈希值"""
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def get(self, script_path: str) -> Optional[ModuleType]:
        """获取缓存的模块（如果文件未修改）"""
        if script_path not in self._cache:
            return None

        cached = self._cache[script_path]
        try:
            current_mtime = os.path.getmtime(script_path)

            # 如果修改时间未变，直接返回缓存模块
            if current_mtime == cached["mtime"]:
                return cached["module"]

            # 修改时间变了，进一步检查内容哈希
            current_hash = self._get_file_hash(script_path)
            if current_hash == cached["hash"]:
                # 内容未变，更新修改时间并返回缓存模块
                cached["mtime"] = current_mtime
                return cached["module"]

            # 文件确实修改了，返回 None 表示需要重新加载
            return None

        except (OSError, IOError):
            # 文件可能被删除或无法访问
            return None

    def set(self, script_path: str, module: ModuleType) -> None:
        """缓存模块及其文件元数据"""
        try:
            mtime = os.path.getmtime(script_path)
            file_hash = self._get_file_hash(script_path)
            self._cache[script_path] = {
                "module": module,
                "mtime": mtime,
                "hash": file_hash,
            }
        except (OSError, IOError):
            # 无法获取文件信息，不缓存
            pass

    def clear(self, script_path: Optional[str] = None) -> None:
        """清除缓存（指定路径或全部）"""
        if script_path:
            self._cache.pop(script_path, None)
        else:
            self._cache.clear()


# 全局模块缓存实例
_module_cache = _ModuleCache()


class DynamicImportSession:
    """
    动态导入脚本，带缓存机制。
    - 如果文件内容未改变，直接返回缓存的模块，避免重复加载
    - 每次导入同名模块时会自动覆盖
    - 为了避免并发 runner 互相影响 sys.modules/sys.path，导入过程加全局锁
    - 模块会保留在 sys.modules 中，同名模块会被自动覆盖
    """

    def __init__(self, *, module_name: str, script_path: str, package_root: Optional[str] = None):
        self.module_name = module_name
        self.script_path = os.path.abspath(script_path)
        self.script_dir = os.path.dirname(self.script_path)
        self.package_root = os.path.abspath(package_root) if package_root else None

        self._inserted_sys_paths: list[str] = []
        self._locked: bool = False
        self._module: Optional[ModuleType] = None

    async def __aenter__(self) -> ModuleType:
        await _dynamic_import_lock.acquire()
        self._locked = True

        # 尝试从缓存获取模块
        cached_module = _module_cache.get(self.script_path)
        if cached_module is not None:
            self._module = cached_module
            return cached_module

        # 缓存未命中，需要加载模块
        # 先添加 package_root（如果有），再添加 script_dir
        if self.package_root and self.package_root not in sys.path:
            sys.path.insert(0, self.package_root)
            self._inserted_sys_paths.append(self.package_root)
        
        if self.script_dir and self.script_dir not in sys.path:
            sys.path.insert(0, self.script_dir)
            self._inserted_sys_paths.append(self.script_dir)

        spec = importlib.util.spec_from_file_location(
            self.module_name, self.script_path
        )
        if not spec or not spec.loader:
            raise ImportError(f"Could not load script: {self.script_path}")

        # 如果模块已存在，会被覆盖
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module

        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(spec.name, None)
            raise

        # 加载成功后缓存模块
        _module_cache.set(self.script_path, module)
        self._module = module
        return module

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            # 只清理 sys.path，不清理模块
            self._cleanup_sys_path()
        finally:
            if self._locked:
                _dynamic_import_lock.release()
                self._locked = False

    def _cleanup_sys_path(self) -> None:
        if not self._inserted_sys_paths:
            return

        # 尽量只撤销本 session 插入的路径，避免覆盖其它逻辑对 sys.path 的改动
        for path in self._inserted_sys_paths:
            while path in sys.path:
                sys.path.remove(path)
        self._inserted_sys_paths.clear()


def clear_module_cache(script_path: Optional[str] = None) -> None:
    """
    清除模块缓存。

    :param script_path: 要清除的脚本路径。如果为 None，清除所有缓存。
    """
    _module_cache.clear(script_path)


def get_cache_stats() -> dict[str, Any]:
    """
    获取缓存统计信息。

    :return: 包含缓存数量和文件路径列表的字典
    """
    return {
        "count": len(_module_cache._cache),
        "cached_files": list(_module_cache._cache.keys()),
    }
