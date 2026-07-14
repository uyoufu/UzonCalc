# 判断数据库
from typing import Callable
from fastapi import FastAPI
from config.config import app_config


def combine_lifespans(main_lifespan: Callable):
    """
    Combine the lifespans of the main application and the MCP application.

    :param main_lifespan: The lifespan function of the main application.
    :return: A combined lifespan function if MCP is enabled, otherwise the main lifespan function.
    """
    if not app_config.mcp_enabled:
        return main_lifespan

    from app.mcp.mcp_app import mcp_app
    from fastmcp.utilities.lifespan import (
        combine_lifespans as fastmcp_combine_lifespans,
    )

    return fastmcp_combine_lifespans(main_lifespan, mcp_app.lifespan)


def mount_mcp(app: FastAPI):
    """
    Mount the MCP application to the main FastAPI app if MCP is enabled in the configuration.
    """
    if not app_config.mcp_enabled:
        return

    from app.mcp.mcp_app import mcp_app

    app.mount("/engineering", mcp_app)


async def init_tool_search() -> None:
    """
    初始化工具搜索索引（FTS + 可选向量库）。
    应在应用启动后调用。
    """
    if not app_config.mcp_enabled:
        return

    from app.mcp.tools_search import init_searcher
    from app.mcp.tools_search.embedder import HttpEmbedder
    from app.mcp.tools_search.vector_store import VectorStore

    vector = None
    embed_url = app_config.mcp_embed_url
    if embed_url:
        try:
            embedder = HttpEmbedder(url=embed_url, model=app_config.mcp_embed_model)
            vector = VectorStore(url=app_config.get_mcp_qdrant_url, embedder=embedder)
            await vector.init()
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(
                "向量存储初始化失败，降级为纯 BM25 模式: %s", e
            )
            vector = None

    await init_searcher(vector=vector)


async def close_tool_search() -> None:
    """关闭工具搜索索引，释放资源"""
    if not app_config.mcp_enabled:
        return

    from app.mcp.tools_search import close_searcher

    await close_searcher()
