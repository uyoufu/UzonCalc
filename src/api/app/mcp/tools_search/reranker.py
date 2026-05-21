"""
倒数秩融合（Reciprocal Rank Fusion，RRF）

将向量检索（稠密）和 BM25 检索（稀疏）的结果融合为统一排名。

公式：RRF_Score = 1/(c + rank_dense) + 1/(c + rank_sparse)
"""
from .models import SearchResult, FusedResult

_C = 60  # 平滑常数，经验值


def _rrf(rank: int) -> float:
    """单路 RRF 贡献值，rank=0 表示未命中，贡献为 0"""
    return 1.0 / (_C + rank) if rank > 0 else 0.0


def fuse(
    dense: list[SearchResult],
    sparse: list[SearchResult],
    top_n: int = 5,
) -> list[FusedResult]:
    """
    融合两路检索结果并返回 top_n 条。

    :param dense:  向量检索结果（相关度降序）
    :param sparse: BM25 检索结果（相关度降序）
    :param top_n:  最终返回条数
    """
    # 构建 name -> 排名 的映射（1-indexed）
    dense_rank = {r.name: i + 1 for i, r in enumerate(dense)}
    sparse_rank = {r.name: i + 1 for i, r in enumerate(sparse)}

    all_names = set(dense_rank) | set(sparse_rank)
    results = [
        FusedResult(
            name=name,
            rrf_score=_rrf(dense_rank.get(name, 0)) + _rrf(sparse_rank.get(name, 0)),
            rank_dense=dense_rank.get(name, 0),
            rank_sparse=sparse_rank.get(name, 0),
        )
        for name in all_names
    ]

    results.sort(key=lambda r: r.rrf_score, reverse=True)
    return results[:top_n]
