# 数据库迁移说明

本目录用于管理 `ui/api/app/db` 下 SQLAlchemy 模型对应的 Alembic 迁移。

## 手动生成迁移的流程

迁移文件默认手动维护，避免自动生成结果在 SQLite 和 PostgreSQL 间产生不兼容 SQL：

1. 业务模型继承 `app.db.models.base.BaseModel`，或把独立 metadata 加入 `env.py`。
2. Alembic 执行 `env.py`。
3. `env.py` 读取项目数据库配置，并转换为 async driver URL。
4. 执行 `alembic revision -m "说明"` 生成空迁移文件。
5. 在 `versions/` 下手动补充 `upgrade()` 和 `downgrade()`。

## 迁移文件生成

``` bash
cd ui/api
alembic -c app/db/migration/alembic.ini revision -m "说明"
```

也可以在 Python 中调用：

``` python
from app.db.init_db import create_migration

create_migration("说明")
```

## 启动自动迁移

应用启动时 `app.db.init_db.init_database()` 会在数据库健康检查后自动执行
`upgrade head`，然后再运行默认数据初始化。已有业务表但没有
`alembic_version` 的旧数据库不会自动 stamp，迁移会严格失败，以便人工处理。
