"""
Qdrant 向量稠密检索

依赖可选库 qdrant-client，未安装时降级为仅 BM25 模式。
安装：pip install qdrant-client
"""

import logging
from typing import TYPE_CHECKING

from .embedder import Embedder
from .models import ToolRecord, SearchResult

if TYPE_CHECKING:
    from qdrant_client import AsyncQdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)

COLLECTION = "mcp_tools"
VECTOR_SIZE = 512  # bge-small-zh-v1.5 维度


class VectorStore:
    """基于 Qdrant 的稠密向量检索存储"""

    def __init__(self, url: str, embedder: Embedder) -> None:
        try:
            from qdrant_client import AsyncQdrantClient

            self._client: "AsyncQdrantClient" = AsyncQdrantClient(url=url)
        except ImportError as e:
            raise RuntimeError(
                "qdrant-client 未安装，请执行 pip install qdrant-client"
            ) from e
        self._embedder = embedder

    async def init(self) -> None:
        """确保 collection 存在，若不存在则创建"""
        from qdrant_client.models import Distance, VectorParams

        collections = await self._client.get_collections()
        names = [c.name for c in collections.collections]
        if COLLECTION not in names:
            await self._client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )

    async def index(self, tools: list[ToolRecord]) -> None:
        """将工具向量化并写入 Qdrant"""
        from qdrant_client.models import PointStruct

        # 清除旧数据
        await self._client.delete_collection(COLLECTION)
        await self.init()

        points = []
        for idx, tool in enumerate(tools):
            vector = await self._embedder.embed(tool.index_text)
            points.append(
                PointStruct(
                    id=idx,
                    vector=vector,
                    payload={"name": tool.name, "category": tool.category},
                )
            )

        if points:
            await self._client.upsert(collection_name=COLLECTION, points=points)
        logger.info("向量索引完成，共 %d 条工具", len(points))

    async def search(self, query: str, top_k: int = 20) -> list[SearchResult]:
        """使用余弦相似度检索最近邻工具"""
        vector = await self._embedder.embed(query)
        result = await self._client.query_points(
            collection_name=COLLECTION,
            query=vector,
            limit=top_k,
        )
        return [
            SearchResult(name=h.payload["name"], score=h.score) for h in result.points
        ]

    async def close(self) -> None:
        await self._client.close()
