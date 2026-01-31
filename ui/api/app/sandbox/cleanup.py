"""
资源清理模块
负责清理动态加载的模块、上下文对象等资源
"""
import sys
import gc
from typing import Optional
from config import logger


class ResourceCleaner:
    """资源清理器，负责清理执行过程中产生的各种资源"""

    @staticmethod
    def cleanup_module(module_name: str) -> bool:
        """
        清理动态加载的模块
        
        :param module_name: 要清理的模块名称
        :return: 是否成功清理
        """
        try:
            if module_name in sys.modules:
                module = sys.modules[module_name]
                
                # 清理模块中的全局变量
                if hasattr(module, '__dict__'):
                    module.__dict__.clear()
                
                # 从 sys.modules 中移除
                del sys.modules[module_name]
                
                # 手动触发垃圾回收
                gc.collect()
                
                logger.debug(f"Successfully cleaned up module: {module_name}")
                return True
        except Exception as e:
            logger.error(f"Error cleaning up module {module_name}: {e}")
            return False
        
        return True

    @staticmethod
    def cleanup_context(ctx) -> None:
        """
        清理 CalcContext 对象，释放其持有的资源
        
        :param ctx: CalcContext 实例
        """
        try:
            if ctx is None:
                return
            
            # 清理 context 中可能持有的大对象
            if hasattr(ctx, 'interaction') and ctx.interaction:
                ctx.interaction = None
            
            if hasattr(ctx, 'vars') and ctx.vars:
                ctx.vars.clear()
            
            # 清理其他可能的资源
            if hasattr(ctx, '__dict__'):
                for key in list(ctx.__dict__.keys()):
                    try:
                        delattr(ctx, key)
                    except:
                        pass
            
            logger.debug("Successfully cleaned up CalcContext")
        except Exception as e:
            logger.error(f"Error cleaning up context: {e}")

    @staticmethod
    def cleanup_task(task) -> None:
        """
        清理 asyncio.Task
        
        :param task: asyncio.Task 实例
        """
        try:
            if task and not task.done():
                task.cancel()
            logger.debug("Successfully cleaned up task")
        except Exception as e:
            logger.error(f"Error cleaning up task: {e}")

    @staticmethod
    def cleanup_future(future) -> None:
        """
        清理未完成的 Future
        
        :param future: asyncio.Future 实例
        """
        try:
            if future and not future.done():
                # 如果 future 还没有完成，设置一个取消异常
                future.cancel()
            logger.debug("Successfully cleaned up future")
        except Exception as e:
            logger.error(f"Error cleaning up future: {e}")

    @classmethod
    def cleanup_all(
        cls,
        module_name: Optional[str] = None,
        ctx=None,
        task=None,
        future=None,
    ) -> None:
        """
        清理所有资源
        
        :param module_name: 模块名称
        :param ctx: CalcContext 实例
        :param task: asyncio.Task 实例
        :param future: asyncio.Future 实例
        """
        if module_name:
            cls.cleanup_module(module_name)
        
        if ctx:
            cls.cleanup_context(ctx)
        
        if task:
            cls.cleanup_task(task)
        
        if future:
            cls.cleanup_future(future)
        
        # 强制垃圾回收
        gc.collect()
        logger.debug("Completed cleanup_all")
