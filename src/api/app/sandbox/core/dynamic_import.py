from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Optional, Any

_dynamic_import_lock = asyncio.Lock()
_BUNDLE_RUNTIME_PACKAGE_NAMES = ("__uzon_deps__",)


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

    def __init__(
        self,
        *,
        module_name: str,
        script_path: str,
        package_root: Optional[str] = None,
        source_root: Optional[str] = None,
    ):
        self.module_name = module_name
        self.script_path = os.path.abspath(script_path)
        self.script_dir = os.path.dirname(self.script_path)
        self.package_root = os.path.abspath(package_root) if package_root else None
        self.source_root = os.path.abspath(source_root) if source_root else None

        self._inserted_sys_paths: list[str] = []
        self._locked: bool = False
        self._module: Optional[ModuleType] = None
        self._replaced_private_modules: dict[str, ModuleType] = {}
        self._installed_runtime_packages: set[str] = set()
        self._baseline_module_names: set[str] = set()
        self._workspace_package_name = (
            module_name.split(".", 1)[0]
            if source_root and module_name.startswith("__uzon_workspace_")
            else None
        )

    def _release_lock_if_needed(self) -> None:
        if self._locked:
            _dynamic_import_lock.release()
            self._locked = False

    async def __aenter__(self) -> ModuleType:
        await _dynamic_import_lock.acquire()
        self._locked = True

        spec = None
        try:
            # 托管工作区通过合成包解析相对导入，不污染进程级 sys.path。
            if not self._workspace_package_name:
                for import_path in (
                    self.package_root,
                    self.source_root,
                    self.script_dir,
                ):
                    if import_path and import_path not in sys.path:
                        sys.path.insert(0, import_path)
                        self._inserted_sys_paths.append(import_path)

            self._baseline_module_names = set(sys.modules)
            self._install_bundle_runtime_packages()
            self._install_workspace_package()

            if self.module_name == self._workspace_package_name:
                package_module = sys.modules[self.module_name]
                _module_cache.set(self.script_path, package_module)
                self._module = package_module
                return package_module

            cached_module = _module_cache.get(self.script_path)
            if cached_module is not None:
                sys.modules[self.module_name] = cached_module
                self._module = cached_module
                return cached_module

            parent_module = self.module_name.rpartition(".")[0]
            if parent_module:
                importlib.import_module(parent_module)
            spec = importlib.util.spec_from_file_location(
                self.module_name,
                self.script_path,
                submodule_search_locations=(
                    [self.script_dir]
                    if Path(self.script_path).name == "__init__.py"
                    else None
                ),
            )
            if not spec or not spec.loader:
                raise ImportError(f"Could not load script: {self.script_path}")

            # 如果模块已存在，会被覆盖
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module

            spec.loader.exec_module(module)

            # 加载成功后缓存模块
            _module_cache.set(self.script_path, module)
            self._module = module
            return module
        except Exception:
            if spec is not None:
                sys.modules.pop(spec.name, None)
            # 注意：__aenter__ 抛异常时，不会调用 __aexit__，必须在这里释放锁并清理路径
            try:
                self._cleanup_import_environment()
            finally:
                self._release_lock_if_needed()
            raise

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            self._cleanup_import_environment()
        finally:
            self._release_lock_if_needed()

    def _cleanup_sys_path(self) -> None:
        if not self._inserted_sys_paths:
            return

        # 尽量只撤销本 session 插入的路径，避免覆盖其它逻辑对 sys.path 的改动
        for path in self._inserted_sys_paths:
            while path in sys.path:
                sys.path.remove(path)
        self._inserted_sys_paths.clear()

    def _install_workspace_package(self) -> None:
        """Install the synthetic package representing the workspace root.

        Args:
            None.

        Returns:
            None.

        Raises:
            ImportError: If the required root ``__init__.py`` cannot be loaded.
        """
        if not self._workspace_package_name or not self.source_root:
            return
        init_path = Path(self.source_root) / "__init__.py"
        if not init_path.is_file():
            raise ImportError("Workspace root __init__.py is missing")
        spec = importlib.util.spec_from_file_location(
            self._workspace_package_name,
            init_path,
            submodule_search_locations=[self.source_root],
        )
        if spec is None or spec.loader is None:
            raise ImportError("Could not load workspace root package")
        package = importlib.util.module_from_spec(spec)
        sys.modules[self._workspace_package_name] = package
        spec.loader.exec_module(package)

    def _install_bundle_runtime_packages(self) -> None:
        """Install private package roots materialized inside an execution bundle.

        Args:
            None.

        Returns:
            None.

        Raises:
            ImportError: If a private package marker cannot be loaded.
        """
        if not self._workspace_package_name or not self.package_root:
            return
        for package_name in _BUNDLE_RUNTIME_PACKAGE_NAMES:
            init_path = Path(self.package_root) / package_name / "__init__.py"
            if not init_path.is_file():
                continue
            package_prefix = f"{package_name}."
            for module_name in list(sys.modules):
                if module_name != package_name and not module_name.startswith(
                    package_prefix
                ):
                    continue
                module = sys.modules.pop(module_name, None)
                if module is not None:
                    self._replaced_private_modules[module_name] = module
            spec = importlib.util.spec_from_file_location(
                package_name,
                init_path,
                submodule_search_locations=[str(init_path.parent)],
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load bundle package: {package_name}")
            package = importlib.util.module_from_spec(spec)
            sys.modules[package_name] = package
            self._installed_runtime_packages.add(package_name)
            spec.loader.exec_module(package)

    def _cleanup_import_environment(self) -> None:
        """Remove session modules, restore host modules, and undo inserted paths.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        package_prefix = (
            f"{self._workspace_package_name}." if self._workspace_package_name else ""
        )
        runtime_prefixes = tuple(
            f"{package_name}." for package_name in self._installed_runtime_packages
        )
        for module_name in list(sys.modules):
            if module_name == self._workspace_package_name or (
                package_prefix and module_name.startswith(package_prefix)
            ):
                sys.modules.pop(module_name, None)
                continue
            if module_name in self._installed_runtime_packages or module_name.startswith(
                runtime_prefixes
            ):
                sys.modules.pop(module_name, None)
                continue
            if module_name in self._baseline_module_names:
                continue
            module = sys.modules.get(module_name)
            module_file = getattr(module, "__file__", None)
            if module_file and self.source_root:
                try:
                    Path(module_file).resolve().relative_to(Path(self.source_root))
                except (OSError, ValueError):
                    continue
                sys.modules.pop(module_name, None)
        sys.modules.update(self._replaced_private_modules)
        self._replaced_private_modules.clear()
        self._installed_runtime_packages.clear()
        self._baseline_module_names.clear()
        self._cleanup_sys_path()


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
