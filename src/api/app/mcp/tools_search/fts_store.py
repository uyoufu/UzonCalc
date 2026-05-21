"""
FTS 稀疏检索（BM25）—— SQLAlchemy 实现，兼容 PostgreSQL 与 SQLite

* SQLite    : 复用应用主库引擎，持久化 tools_fts FTS5 虚拟表 + bm25()，
              每次启动仅增量更新（新增/变更/删除），得分越高越相关。
* PostgreSQL: 使用应用主库，持久化 tools_fts 表，tsvector GENERATED ALWAYS AS
              + GIN 索引 + ts_rank()，得分越高越相关。

根据 app_config 中 postgres_enabled 自动选择后端。
"""

import re
import logging
from abc import ABC, abstractmethod

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from .models import ToolRecord, SearchResult

logger = logging.getLogger(__name__)


# ─────────────────────────── 公共接口 ───────────────────────────


class FtsStore:
    """FTS 全文检索存储门面，根据配置自动选择 PostgreSQL 或 SQLite 后端"""

    def __init__(self) -> None:
        self._backend: _FtsBackend = _create_backend()

    async def init(self) -> None:
        await self._backend.init()

    async def close(self) -> None:
        await self._backend.close()

    async def index(self, tools: list[ToolRecord]) -> None:
        """将工具列表写入 FTS 索引"""
        await self._backend.index(tools)

    async def search(self, query: str, top_k: int = 20) -> list[SearchResult]:
        """全文检索，返回按相关度降序排列的结果"""
        return await self._backend.search(query, top_k)


def _create_backend() -> "_FtsBackend":
    """依据 app_config 选择后端"""
    from config.config import app_config

    if app_config.postgres_enabled:
        logger.info("FtsStore: using PostgreSQL tsvector backend")
        return _PostgresFtsBackend()
    else:
        logger.info("FtsStore: using SQLite FTS5 (persistent, incremental) backend")
        return _SqliteFtsBackend()


# ─────────────────────────── 抽象后端 ───────────────────────────


class _FtsBackend(ABC):
    @abstractmethod
    async def init(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...

    @abstractmethod
    async def index(self, tools: list[ToolRecord]) -> None: ...

    @abstractmethod
    async def search(self, query: str, top_k: int) -> list[SearchResult]: ...


# ─────────────────────────── SQLite FTS5 ───────────────────────────

_SQLITE_DDL = text(
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS tools_fts
    USING fts5(name UNINDEXED, description, category, tokenize='unicode61')
"""
)

_SQLITE_INSERT = text(
    "INSERT INTO tools_fts(name, description, category) VALUES (:name, :description, :category)"
)

_SQLITE_SEARCH = text(
    """
    SELECT name, bm25(tools_fts) AS score
    FROM tools_fts
    WHERE tools_fts MATCH :query
    ORDER BY score
    LIMIT :top_k
"""
)


class _SqliteFtsBackend(_FtsBackend):
    """基于 SQLite FTS5 的 BM25 检索后端（持久化，增量更新）"""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None

    async def init(self) -> None:
        from app.db.manager import get_db_manager

        self._engine = get_db_manager().engine
        async with self._engine.connect() as conn:
            await conn.execute(_SQLITE_DDL)
            await conn.commit()

    async def close(self) -> None:
        # 不负责关闭主引擎
        self._engine = None

    async def index(self, tools: list[ToolRecord]) -> None:
        assert self._engine is not None, "FtsStore not initialized"
        async with self._engine.connect() as conn:
            # 读取已索引数据
            result = await conn.execute(
                text("SELECT name, description, category FROM tools_fts")
            )
            existing: dict[str, tuple[str, str]] = {
                row[0]: (row[1], row[2]) for row in result.fetchall()
            }
            new_map = {t.name: t for t in tools}

            # 删除已移除的工具
            for name in set(existing) - set(new_map):
                await conn.execute(
                    text("DELETE FROM tools_fts WHERE name = :name"), {"name": name}
                )

            # 新增 / 更新（FTS5 不支持 UPDATE，先删后插）
            for name, tool in new_map.items():
                new_val = (tool.description, tool.category)
                if name not in existing:
                    await conn.execute(
                        _SQLITE_INSERT,
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "category": tool.category,
                        },
                    )
                elif existing[name] != new_val:
                    await conn.execute(
                        text("DELETE FROM tools_fts WHERE name = :name"), {"name": name}
                    )
                    await conn.execute(
                        _SQLITE_INSERT,
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "category": tool.category,
                        },
                    )

            await conn.commit()

    async def search(self, query: str, top_k: int) -> list[SearchResult]:
        assert self._engine is not None, "FtsStore not initialized"
        safe_query = _escape_fts5_query(query)
        if not safe_query:
            return []
        async with self._engine.connect() as conn:
            result = await conn.execute(
                _SQLITE_SEARCH, {"query": safe_query, "top_k": top_k}
            )
            rows = result.fetchall()
        # bm25 返回负值，取反转为正向得分
        return [SearchResult(name=row[0], score=-row[1]) for row in rows]


# ─────────────────────────── PostgreSQL tsvector ───────────────────────────

_PG_DDL = text(
    """
    CREATE TABLE IF NOT EXISTS tools_fts (
        name        TEXT PRIMARY KEY,
        description TEXT,
        category    TEXT,
        tsv         TSVECTOR GENERATED ALWAYS AS (
                        to_tsvector('simple',
                            COALESCE(description, '') || ' ' || COALESCE(category, ''))
                    ) STORED
    )
"""
)

_PG_GIN_INDEX = text(
    "CREATE INDEX IF NOT EXISTS tools_fts_tsv_idx ON tools_fts USING GIN (tsv)"
)

_PG_TRUNCATE = text("TRUNCATE TABLE tools_fts")

_PG_INSERT = text(
    """
    INSERT INTO tools_fts(name, description, category)
    VALUES (:name, :description, :category)
    ON CONFLICT (name) DO UPDATE
        SET description = EXCLUDED.description,
            category    = EXCLUDED.category
"""
)

_PG_SEARCH = text(
    """
    SELECT name, ts_rank(tsv, query) AS score
    FROM tools_fts, websearch_to_tsquery('simple', :query) AS query
    WHERE tsv @@ query
    ORDER BY score DESC
    LIMIT :top_k
"""
)


class _PostgresFtsBackend(_FtsBackend):
    """基于 PostgreSQL tsvector + GIN 索引的全文检索后端"""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None

    async def init(self) -> None:
        from app.db.manager import get_db_manager

        self._engine = get_db_manager().engine
        async with self._engine.connect() as conn:
            await conn.execute(_PG_DDL)
            await conn.execute(_PG_GIN_INDEX)
            await conn.commit()

    async def close(self) -> None:
        # 不负责关闭主引擎
        self._engine = None

    async def index(self, tools: list[ToolRecord]) -> None:
        assert self._engine is not None, "FtsStore not initialized"
        async with self._engine.connect() as conn:
            await conn.execute(_PG_TRUNCATE)
            if tools:
                await conn.execute(
                    _PG_INSERT,
                    [
                        {
                            "name": t.name,
                            "description": t.description,
                            "category": t.category,
                        }
                        for t in tools
                    ],
                )
            await conn.commit()

    async def search(self, query: str, top_k: int) -> list[SearchResult]:
        assert self._engine is not None, "FtsStore not initialized"
        if not query.strip():
            return []
        async with self._engine.connect() as conn:
            result = await conn.execute(_PG_SEARCH, {"query": query, "top_k": top_k})
            rows = result.fetchall()
        return [SearchResult(name=row[0], score=float(row[1])) for row in rows]


# ─────────────────────────── 工具函数 ───────────────────────────


def _escape_fts5_query(query: str) -> str:
    """将用户输入转为 FTS5 安全查询（保留中英文、数字，去除 FTS5 操作符）"""
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", query)
    return " ".join(tokens)
