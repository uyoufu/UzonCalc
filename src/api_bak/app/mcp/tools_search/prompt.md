# 工具搜索与动态路由方案

## 核心架构

采用 **多路召回（Multi-way Recall）** 与 **混合检索（Hybrid Search）** 机制，结合关系型数据库（SQLite/PostgreSQL）与向量数据库（Qdrant），实现高准确度、低延迟的工具动态搜索系统。

## 1. 存储与索引设计 (Storage & Indexing)

### 1.1 常规数据库 (SQLite / PostgreSQL)

- **职责**: 作为 Single Source of Truth，存储工具的完整数据（ID、名称、描述、入参Schema、实际函数调用映射），并承担 BM25 / 词频检索引擎的角色。
- **机制**:
  - **SQLite 方案**: 使用 `FTS5` (Full-Text Search) 虚拟表扩展，建立工具名称和特征描述的倒排索引，原生支持高效的 BM25 排序。
  - **PostgreSQL 方案**: 使用 `to_tsvector` 和 `tsquery` 构建全文检索能力，可辅以 `pg_trgm` 插件处理模糊短尾匹配。

### 1.2 向量数据库 (Qdrant)

- **职责**: 捕捉用户口语化查询的意图，支撑同义词和上下文语义模糊匹配。
- **机制**:
  - **模型选型**: 采用轻量且强大的中文 Embeddings 模型（如 `bge-small-zh-v1.5`）。
  - **灌库/更新**: 只有在系统初始化或新工具注册时，提前把工具组合文本（如 `"名称: xxx, 描述: yyy, 标签: zzz"`）转化为高维稠密向量并预计算存入 Qdrant。坚决避免查询时的动态全量 Embedding。
  - **Payload（元数据）冗余**: 将工具的关键分类（如 `category: "mechanics"`）冗余入 Qdrant 的 Payload 属性中，以便后续进行混合过滤。

## 2. 检索流程 (Retrieval Pipeline)

当主站收到工具检索 Query 时，通过协程（如 FastAPI 中的 `asyncio.gather`）同时对两路存储发起并发召回：

### 2.1 向量检索 (Dense Retrieval - 关注语义关联)

1. 将用户的 Query 交给相同的 BGE 模型实时生成单条向量嵌入。
2. 带入可选的前置上下文条件（利用 Qdrant 的 Payload 过滤特性，例如剔除未启用的工具）。
3. 使用余弦相似度（Cosine）或内积（Dot）找出在向量空间中最接近的 **Top-K候选**（推荐 K=20），并获得它们的分数与排名。

### 2.2 BM25 全文检索 (Sparse Retrieval - 关注精准词命中)

1. 对 Query 进行标准化和简单的分词预处理。
2. 传递给 SQLite/Postgres 的全文检索引擎。
3. 这一路优势在于它对专有名词、规范编码（如 "GB50017"）、工程特定缩写特别敏感，同样获取得分最高的 **Top-K候选**。

## 3. 混合排序与融合 (Hybrid Re-ranking)

因为向量余弦相似度（如 0.85）与 BM25 的得分（如 12.5）属于不同维度量纲，无法直接相加，所以必须采用**基于排序的融合打分机制**。

**倒数秩融合算法 (Reciprocal Rank Fusion, RRF)**:
算法公式：`RRF_Score = 1 / (c + Rank_Dense) + 1 / (c + Rank_Sparse)`

- `Rank_Dense` 是某工具在 Qdrant 检索出的名次（第 1 名、第 2 名...）。
- `Rank_Sparse` 是同一个工具在 DB 全文检索中的名次。
- _常数 `c` （通常经验值为 60）用于平滑异常高的单路名次影响。_

**排序输出**: 计算整合后，按照 RRF 去重降序排列所有被任意一路召回的工具，截取最终分数排名前 3-5 的工具集合返回给编排引擎或模型侧。
