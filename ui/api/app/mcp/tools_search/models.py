"""工具搜索数据模型"""
from dataclasses import dataclass, field


@dataclass
class ToolRecord:
    """工具的可检索记录，存储于 FTS 和向量库中"""

    name: str
    description: str
    category: str = ""

    @property
    def index_text(self) -> str:
        """拼接用于建立索引的文本"""
        return f"名称: {self.name}, 描述: {self.description}, 分类: {self.category}"


@dataclass
class SearchResult:
    """单路检索结果：(工具名, 得分)"""

    name: str
    score: float


@dataclass
class FusedResult:
    """RRF 融合后的最终结果"""

    name: str
    rrf_score: float
    rank_dense: int = 0   # 向量检索排名，0 表示未命中
    rank_sparse: int = 0  # BM25 检索排名，0 表示未命中
