"""
工具索引构建器

从 FastMCP 注册的工具中提取元数据，写入 FTS 和向量索引。
"""

import logging

from .fts_store import FtsStore
from .models import ToolRecord
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


async def extract_tools() -> list[ToolRecord]:
    """
    从 FastMCP 已注册的工具中提取 ToolRecord 列表。
    category 从工具函数的模块路径中推断（最后一个包名）。
    """
    from app.mcp.tools.loader import get_all_tools

    tools = await get_all_tools()
    records: list[ToolRecord] = []

    for tool in tools:
        description = tool.description or ""
        # 获取工具函数
        fn = _get_attr(tool, "fn") or _get_attr(tool, "_fn")
        category = _infer_category(fn)
        records.append(
            ToolRecord(name=tool.name, description=description, category=category)
        )

    logger.info("提取工具元数据完成，共 %d 条", len(records))
    return records


async def build_indexes(
    fts: FtsStore,
    vector: VectorStore | None = None,
    tools: list[ToolRecord] | None = None,
) -> None:
    """
    构建 FTS 索引；若提供了向量存储，则同时构建向量索引。
    :param tools: 可选的预提取工具列表，避免重复提取。
    """
    if tools is None:
        tools = await extract_tools()

    await fts.index(tools)
    logger.info("FTS 索引构建完成")

    if vector is not None:
        await vector.index(tools)
        logger.info("向量索引构建完成")


# ---------------------------------------------------------------------------
# 私有辅助
# ---------------------------------------------------------------------------


def _get_attr(obj: object, *attrs: str, default=None):
    """依次尝试多个属性名，返回第一个非 None 值"""
    for attr in attrs:
        val = getattr(obj, attr, None)
        if val is not None:
            return val
    return default


def _infer_category(fn) -> str:
    """从函数的 __module__ 推断工具分类，取倒数第二个包名"""
    if fn is None:
        return ""
    module: str = getattr(fn, "__module__", "") or ""
    parts = module.split(".")
    # app.mcp.tools.<category>.core  →  parts[-2]
    return parts[-2] if len(parts) >= 2 else ""
