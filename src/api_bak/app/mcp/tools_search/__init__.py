"""
tools_search — 工具动态搜索模块

公共 API：
- ToolSearcher      : 混合检索主类
- init_searcher()   : 启动初始化（建立 FTS + 向量索引）
- close_searcher()  : 资源释放
- get_searcher()    : 获取全局搜索器实例
- ToolRecord        : 工具元数据记录
- FusedResult       : 融合检索结果
"""
from .models import FusedResult, ToolRecord
from .searcher import ToolSearcher, close_searcher, get_searcher, init_searcher

__all__ = [
    "ToolSearcher",
    "init_searcher",
    "close_searcher",
    "get_searcher",
    "ToolRecord",
    "FusedResult",
]
