# 数据库迁移说明

本目录用于管理 `src/api/app/db` 下 SQLAlchemy 模型对应的 Alembic 迁移。

## 自动生成迁移

推荐使用 Alembic 的 `--autogenerate` 生成候选迁移，再人工检查和调整。
这与 `dotnet ef migrations add` 的用途相似，但比较基准不同：

- `dotnet ef` 比较当前模型与模型快照。
- Alembic 比较当前配置数据库的结构与 `app.db.models.Base.metadata`。

因此，生成迁移前应确保：

1. 用于比较的数据库已执行到现有迁移的 `head`，但尚未通过其它方式应用本次模型变更。
2. 业务模型继承 `app.db.models.base.Base` 或 `BaseModel`。
3. 新增的模型模块已在 `app.db.models` 中导入，使 `env.py` 加载模型时能将表注册到统一的 `Base.metadata`。
4. `config/app.ini` 及当前环境配置指向用于生成迁移的数据库，不要直接使用生产数据库。

### 命令行生成

从仓库根目录进入 `src/api` 后执行：

```bash
cd src/api
uv run --package uzoncalc-api alembic \
  -c app/db/migration/alembic.ini \
  revision --autogenerate -m "说明"
```

Alembic 会在 `versions/` 下生成包含候选 `upgrade()` 和 `downgrade()` 操作的迁移文件。

### Python 调用

```python
from app.db.init_db import create_migration

create_migration("说明", autogenerate=True)
```

## 为什么生成的迁移是空的

以下情况会生成只有 `pass` 的迁移文件：

- 命令未传入 `--autogenerate`，或 Python 调用未传入 `autogenerate=True`。这是 Alembic 创建空迁移模板的正常行为。
- 当前配置数据库的结构已经与 `Base.metadata` 一致，没有可生成的差异。
- 新模型没有在 `app.db.models` 中导入，Alembic 未加载对应的表。
- 命令连接到了错误的数据库，或该数据库不是现有迁移对应的结构版本。

可先检查数据库版本和迁移 head：

```bash
uv run --package uzoncalc-api alembic \
  -c app/db/migration/alembic.ini current
uv run --package uzoncalc-api alembic \
  -c app/db/migration/alembic.ini heads
```

首次创建完整基线迁移时，应使用空数据库作为比较对象；如果空数据库中已经通过
`Base.metadata.create_all()` 建表，自动生成也会认为没有差异。

## 人工检查自动生成结果

自动生成只提供候选操作。提交迁移前至少检查：

1. `down_revision` 是否指向预期的上一版本。
2. `upgrade()` 和 `downgrade()` 是否完整且顺序正确。
3. 字段或表重命名是否被错误识别为“删除后重建”。
4. 外键、唯一约束、检查约束、索引和服务端默认值是否符合模型定义。
5. SQLite 和 PostgreSQL 是否都支持生成的 DDL；必要时使用 batch 操作或按方言处理。
6. 数据迁移、循环外键等无法可靠自动推断的逻辑是否已手动补充。

如果确实需要从空模板开始手写迁移，可以省略 `--autogenerate`：

```bash
uv run --package uzoncalc-api alembic \
  -c app/db/migration/alembic.ini \
  revision -m "说明"
```

## 启动自动迁移

应用启动时 `app.db.init_db.init_database()` 会在数据库健康检查后自动执行
`upgrade head`，然后再运行默认数据初始化。已有业务表但没有
`alembic_version` 的旧数据库不会自动 stamp，迁移会严格失败，以便人工处理。
