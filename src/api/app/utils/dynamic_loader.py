import os
import importlib.util
import inspect
import sys
import logging
from typing import Any, Type, List, Optional
from pathlib import Path

from fastapi import FastAPI
from config import logger


def _normalize_module_name(module_path: str) -> str:
    """
    规范化模块名称

    Args:
        module_path: 模块文件路径

    Returns:
        规范化后的模块名称
    """
    return module_path.replace("\\", "/").replace("/", ".").replace(".py", "")


def import_module(module_path: str) -> Any:
    """
    动态导入模块

    Args:
        module_path: 模块文件的完整路径

    Returns:
        导入的模块对象

    Raises:
        FileNotFoundError: 当模块文件不存在时
        ImportError: 当模块导入失败时
    """
    if not os.path.isfile(module_path):
        raise FileNotFoundError(f"Module file not found: {module_path}")

    if not module_path.endswith(".py"):
        raise ValueError(f"Module path must be a Python file: {module_path}")

    module_name = _normalize_module_name(module_path)

    # 检查模块是否已经加载
    if module_name in sys.modules:
        logger.debug(f"Module already loaded: {module_name}")
        return sys.modules[module_name]

    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create module spec for: {module_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        logger.debug(f"Module successfully loaded: {module_name}")
        return module
    except Exception as e:
        # 清理已注册的模块
        if module_name in sys.modules:
            del sys.modules[module_name]
        logger.error(f"Failed to load module {module_path}: {e}", exc_info=True)
        raise ImportError(f"Failed to load module {module_path}") from e


def _filter_python_files(
    directory: str, ignore_files: Optional[List[str]] = None
) -> List[str]:
    """
    从目录中过滤出有效的Python文件，包括子目录

    Args:
        directory: 目录路径
        ignore_files: 需要忽略的文件名列表

    Returns:
        有效的Python文件列表（相对于directory的路径）

    Raises:
        NotADirectoryError: 当目录不存在时
    """
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"Directory not found: {directory}")

    ignore_files = ignore_files or []
    valid_files = []

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if (
                filename.endswith(".py")
                and filename != "__init__.py"
                and filename not in ignore_files
            ):
                # 获取相对于directory的路径
                rel_path = os.path.relpath(os.path.join(root, filename), directory)
                valid_files.append(rel_path)

    return valid_files


def load_routers_from_directory(
    directory: str, app: FastAPI, prefix: str = "/api"
) -> int:
    """
    从指定目录加载路由

    Args:
        directory: 包含路由模块的目录
        app: FastAPI 应用实例
        prefix: 路由前缀，默认为 "/api"

    Returns:
        成功加载的路由数

    Raises:
        NotADirectoryError: 当目录不存在时
        TypeError: 当app不是FastAPI实例时
    """
    if not isinstance(app, FastAPI):
        raise TypeError("app must be an instance of FastAPI")

    routers_loaded = 0

    try:
        for filename in _filter_python_files(directory):
            module_path = os.path.join(directory, filename)
            try:
                module = import_module(module_path)
                if hasattr(module, "router"):
                    app.include_router(module.router, prefix=prefix)
                    logger.info(f"Router loaded from {filename}")
                    routers_loaded += 1
            except (ImportError, AttributeError) as e:
                logger.warning(f"Failed to load router from {filename}: {e}")
                continue
    except NotADirectoryError:
        raise

    logger.info(f"Total routers loaded: {routers_loaded}")
    return routers_loaded


def find_subclasses_in_directory(
    directory: str, base_class: Type[Any], ignore_files: Optional[List[str]] = None
) -> List[Type[Any]]:
    """
    从指定目录中查找所有继承自 base_class 的类

    Args:
        directory: 要搜索的目录
        base_class: 基类
        ignore_files: 需要忽略的文件名列表

    Returns:
        找到的所有子类列表

    Raises:
        NotADirectoryError: 当目录不存在时
        TypeError: 当base_class不是类时
    """
    if not isinstance(base_class, type):
        raise TypeError("base_class must be a class")

    subclasses: List[Type[Any]] = []
    ignore_files = ignore_files or []

    try:
        for filename in _filter_python_files(directory, ignore_files):
            module_path = os.path.join(directory, filename)
            try:
                module = import_module(module_path)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # 检查是否是base_class的子类且不是base_class本身
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, base_class)
                        and obj is not base_class
                        and obj.__module__ == module.__name__
                    ):
                        subclasses.append(obj)
                        logger.debug(f"Found subclass {obj.__name__} in {filename}")
            except (ImportError, TypeError) as e:
                logger.warning(f"Error processing {filename}: {e}")
                continue
    except NotADirectoryError:
        raise

    logger.info(f"Found {len(subclasses)} subclasses of {base_class.__name__}")
    return subclasses


def import_subclasses_in_directory(
    directory: str, ignore_files: Optional[List[str]] = None
) -> int:
    """
    导入所有的模块（用于加载子类）

    Args:
        directory: 要导入模块的目录
        ignore_files: 需要忽略的文件名列表

    Returns:
        成功导入的模块数

    Raises:
        NotADirectoryError: 当目录不存在时
    """
    modules_imported = 0
    ignore_files = ignore_files or []

    try:
        for filename in _filter_python_files(directory, ignore_files):
            module_path = os.path.join(directory, filename)
            try:
                import_module(module_path)
                logger.debug(f"Module imported: {filename}")
                modules_imported += 1
            except ImportError as e:
                logger.warning(f"Failed to import {filename}: {e}")
                continue
    except NotADirectoryError:
        raise

    logger.info(f"Total modules imported: {modules_imported}")
    return modules_imported
