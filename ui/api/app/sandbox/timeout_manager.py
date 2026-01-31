"""
超时管理模块
负责管理脚本执行超时和用户输入等待超时
"""
import asyncio
from typing import Optional, Callable, Any, Awaitable, TypeVar
from config import logger

T = TypeVar('T')


class TimeoutError(Exception):
    """超时异常"""
    pass


class TimeoutManager:
    """超时管理器"""
    
    # 默认超时时间（秒）
    DEFAULT_EXECUTION_TIMEOUT = 300  # 5 分钟
    DEFAULT_INPUT_TIMEOUT = 600  # 10 分钟（用户输入可以等待更长时间）
    
    @staticmethod
    async def with_timeout(
        coro: Awaitable[T],
        timeout: float,
        error_message: Optional[str] = None,
    ) -> T:
        """
        为协程添加超时控制
        
        :param coro: 要执行的协程
        :param timeout: 超时时间（秒）
        :param error_message: 超时错误消息
        :return: 协程的返回值
        :raises TimeoutError: 当执行超时时
        """
        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            msg = error_message or f"Operation timed out after {timeout} seconds"
            logger.warning(msg)
            raise TimeoutError(msg)
        except Exception as e:
            logger.error(f"Error during timeout operation: {e}")
            raise

    @classmethod
    async def execute_with_timeout(
        cls,
        func: Callable[..., Awaitable[T]],
        timeout: Optional[float] = None,
        *args,
        **kwargs,
    ) -> T:
        """
        执行函数并添加超时控制
        
        :param func: 要执行的异步函数
        :param timeout: 超时时间（秒），默认为 DEFAULT_EXECUTION_TIMEOUT
        :param args: 函数参数
        :param kwargs: 函数关键字参数
        :return: 函数的返回值
        """
        timeout = timeout or cls.DEFAULT_EXECUTION_TIMEOUT
        error_msg = f"Script execution timed out after {timeout} seconds"
        
        return await cls.with_timeout(
            func(*args, **kwargs),
            timeout=timeout,
            error_message=error_msg,
        )

    @classmethod
    async def wait_for_input_with_timeout(
        cls,
        future: asyncio.Future,
        timeout: Optional[float] = None,
    ) -> Any:
        """
        等待用户输入，带超时控制
        
        :param future: 等待的 Future 对象
        :param timeout: 超时时间（秒），默认为 DEFAULT_INPUT_TIMEOUT
        :return: Future 的结果
        """
        timeout = timeout or cls.DEFAULT_INPUT_TIMEOUT
        error_msg = f"Waiting for user input timed out after {timeout} seconds"
        
        return await cls.with_timeout(
            future,
            timeout=timeout,
            error_message=error_msg,
        )

    @staticmethod
    def create_timeout_task(
        coro: Awaitable[T],
        timeout: float,
        callback: Optional[Callable[[Exception], None]] = None,
    ) -> asyncio.Task:
        """
        创建一个带超时的任务
        
        :param coro: 要执行的协程
        :param timeout: 超时时间（秒）
        :param callback: 超时或异常时的回调函数
        :return: asyncio.Task
        """
        async def wrapped():
            try:
                return await asyncio.wait_for(coro, timeout=timeout)
            except asyncio.TimeoutError as e:
                error = TimeoutError(f"Task timed out after {timeout} seconds")
                if callback:
                    callback(error)
                raise error
            except Exception as e:
                if callback:
                    callback(e)
                raise
        
        return asyncio.create_task(wrapped())
