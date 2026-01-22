"""插桩缓存管理器，隔离全局状态"""
import threading
import weakref
from types import FunctionType
from typing import Any, Callable, Optional


class InstrumentCache:
    """管理函数插桩缓存的单例类"""

    _instance: Optional["InstrumentCache"] = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self._cache: "weakref.WeakKeyDictionary[Callable[..., Any], FunctionType]" = (
            weakref.WeakKeyDictionary()
        )
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "InstrumentCache":
        """获取单例实例"""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例实例（主要用于测试）"""
        with cls._instance_lock:
            cls._instance = None

    def get(self, func: Callable[..., Any]) -> Optional[FunctionType]:
        """获取缓存的插桩函数"""
        with self._lock:
            return self._cache.get(func)

    def set(self, func: Callable[..., Any], instrumented_func: FunctionType) -> None:
        """缓存插桩函数"""
        with self._lock:
            self._cache[func] = instrumented_func

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
