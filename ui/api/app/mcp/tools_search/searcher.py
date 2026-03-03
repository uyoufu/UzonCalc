"""
工具搜索编排器（主入口）

并发发起稀疏（BM25）和稠密（向量）检索，通过 RRF 融合后返回最相关工具名列表。
"""

import asyncio
import logging

from .fts_store import FtsStore
from .indexer import build_indexes, extract_tools
from .models import FusedResult, SearchResult, ToolRecord
from .reranker import fuse
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class ToolSearcher:
    """
    混合检索搜索器，整合 BM25 和向量检索。
    向量存储为可选项；若未配置则退化为纯 BM25 模式。
    """

    def __init__(
        self,
        fts: FtsStore,
        tool_map: dict[str, ToolRecord],
        vector: VectorStore | None = None,
    ) -> None:
        self._fts = fts
        self._vector = vector
        self._tool_map = tool_map  # name -> ToolRecord

    async def search(self, query: str, top_n: int = 5) -> list[FusedResult]:
        """
        并发执行稀疏检索与稠密检索，通过 RRF 融合返回 top_n 结果。

        :param query: 用户查询文本
        :param top_n: 返回条数
        :return: 按 RRF 得分降序排列的 FusedResult 列表
        """
        tasks = [self._fts.search(query)]
        if self._vector:
            tasks.append(self._vector.search(query))

        raw = await asyncio.gather(*tasks, return_exceptions=True)

        sparse: list[SearchResult] = _safe_results(raw[0])
        dense: list[SearchResult] = _safe_results(raw[1]) if len(raw) > 1 else []

        if not dense:
            # 仅 BM25 模式：直接按稀疏得分截断
            return [
                FusedResult(name=r.name, rrf_score=r.score, rank_sparse=i + 1)
                for i, r in enumerate(sparse[:top_n])
            ]

        return fuse(dense, sparse, top_n=top_n)


# ---------------------------------------------------------------------------
# 模块级单例（供 MCP 应用使用）
# ---------------------------------------------------------------------------

_searcher: ToolSearcher | None = None


def get_searcher() -> ToolSearcher:
    if _searcher is None:
        raise RuntimeError("ToolSearcher 尚未初始化，请先调用 init_searcher()")
    return _searcher


async def init_searcher(vector: VectorStore | None = None) -> ToolSearcher:
    """启动时调用，创建全局搜索器实例并建立索引"""
    global _searcher

    tools = extract_tools()
    tool_map = {t.name: t for t in tools}

    fts = FtsStore()
    await fts.init()
    await build_indexes(fts, vector, tools=tools)
    _searcher = ToolSearcher(fts, tool_map, vector)
    logger.info("ToolSearcher 初始化完成")
    return _searcher


async def close_searcher() -> None:
    """关闭时调用，释放资源"""
    global _searcher
    if _searcher is None:
        return
    await _searcher._fts.close()
    if _searcher._vector:
        await _searcher._vector.close()
    _searcher = None
    logger.info("ToolSearcher 已关闭")


# ---------------------------------------------------------------------------
# 私有辅助
# ---------------------------------------------------------------------------


def _safe_results(result) -> list[SearchResult]:
    """将 gather 结果安全转为列表，异常则返回空"""
    if isinstance(result, Exception):
        logger.warning("检索异常，降级处理: %s", result)
        return []
    return result or []
