"""
数据库迁移和集成检查清单

使用此清单确保系统正确集成了用户输入历史功能。
"""

# 📋 集成检查清单

## ✅ 第一阶段：代码准备

- [ ] **拉取最新代码**
  - 所有新文件都已创建在正确位置：
    - `app/model/calc_execution_response.py`
    - `app/db/models/user_input_history.py`
    - `app/db/dao/user_input_history_dao.py`
    - `scripts/init_user_input_history.py`
    - `tests/test_user_input_history.py`
    - `docs/USER_INPUT_HISTORY_GUIDE.md`
    - `docs/OPTIMIZATION_SUMMARY.md`
    - `docs/QUICK_REFERENCE.md`

- [ ] **检查依赖**
  ```bash
  # 确保已安装必要的包
  pip list | grep -i sqlalchemy
  pip list | grep -i pydantic
  # 都应该显示已安装
  ```

- [ ] **更新 requirements.txt**（如需要）
  ```
  SQLAlchemy>=2.0.0
  sqlalchemy[asyncio]>=2.0.0
  aiomysql>=0.2.0  # 如使用 MySQL
  asyncpg>=0.28.0  # 如使用 PostgreSQL
  aiosqlite>=0.19.0  # 如使用 SQLite
  ```

---

## ✅ 第二阶段：数据库初始化

### 选项 A：使用初始化脚本（推荐）

```bash
# 1. 进入 API 目录
cd d:\Develop\Personal\UzonCalc\ui\api

# 2. 运行初始化脚本（选择一个数据库类型）
python scripts/init_user_input_history.py sqlite    # SQLite
# 或
python scripts/init_user_input_history.py mysql     # MySQL
# 或
python scripts/init_user_input_history.py postgresql # PostgreSQL

# 3. 检查输出
# 应该看到：
# ✅ 数据库表创建成功
# ✅ 创建的表: ['user_input_history', 'published_version', 'input_cache', ...]
```

### 选项 B：手动创建表（MySQL）

```sql
-- 执行以下 SQL 创建表

-- 用户输入历史表
CREATE TABLE IF NOT EXISTS user_input_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(64) NOT NULL,
    file_path VARCHAR(256) NOT NULL,
    func_name VARCHAR(128) NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    input_history JSON DEFAULT '[]',
    current_step INT DEFAULT 0,
    total_steps INT DEFAULT 0,
    final_result LONGTEXT,
    final_result_hash VARCHAR(64),
    is_complete BOOLEAN DEFAULT FALSE,
    is_draft BOOLEAN DEFAULT TRUE,
    draft_version_id INT,
    parameters JSON,
    execution_time INT,
    error_message LONGTEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at DATETIME,
    UNIQUE KEY uq_user_execution (user_id, file_path, func_name, session_id),
    INDEX idx_user_file_func (user_id, file_path, func_name),
    INDEX idx_user_created_at (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 已发布版本表
CREATE TABLE IF NOT EXISTS published_version (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(64) NOT NULL,
    file_path VARCHAR(256) NOT NULL,
    func_name VARCHAR(128) NOT NULL,
    version_name VARCHAR(128) NOT NULL,
    version_number INT DEFAULT 1,
    version_description LONGTEXT,
    input_history JSON NOT NULL,
    final_result LONGTEXT NOT NULL,
    final_result_hash VARCHAR(64) NOT NULL,
    parameters JSON,
    total_steps INT NOT NULL,
    execution_time INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_from_history_id INT,
    download_count INT DEFAULT 0,
    use_count INT DEFAULT 0,
    is_public BOOLEAN DEFAULT FALSE,
    INDEX idx_user_published (user_id, published_at),
    INDEX idx_file_version (file_path, func_name, version_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 输入缓存表
CREATE TABLE IF NOT EXISTS input_cache (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(64) NOT NULL,
    file_path VARCHAR(256) NOT NULL,
    func_name VARCHAR(128) NOT NULL,
    cached_input JSON NOT NULL,
    input_history_id INT NOT NULL,
    total_steps INT NOT NULL,
    completed_steps INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expires_at DATETIME,
    INDEX idx_cache_user_file (user_id, file_path, func_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 验证表创建

```bash
# 检查表是否创建成功
mysql -u root -p your_database -e "SHOW TABLES;" | grep -E "user_input|published|input_cache"

# 应该显示：
# input_cache
# published_version
# user_input_history
```

---

## ✅ 第三阶段：应用集成

### 1. 更新 FastAPI 应用启动代码

编辑 `app/main.py` 或应用初始化文件：

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.models.user_input_history import Base
from app.service.calc_execution_service import set_execution_service

async def startup_event():
    """应用启动事件"""
    
    # 1. 创建异步引擎
    DATABASE_URL = "mysql+aiomysql://user:password@localhost/dbname"
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    # 2. 创建会话工厂
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    # 3. 创建所有表（如果不存在）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 4. 存储会话工厂供后续使用
    app.state.db_session_factory = async_session
    app.state.engine = engine
    
    logger.info("✅ 数据库初始化完成")

async def shutdown_event():
    """应用关闭事件"""
    if hasattr(app.state, 'engine'):
        await app.state.engine.dispose()
    logger.info("✅ 数据库连接关闭")

# 在 FastAPI 应用中注册事件
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)
```

### 2. 创建数据库会话依赖

编辑 `app/controller/depends.py`：

```python
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

# 获取全局会话工厂
def get_session_factory():
    from main import app
    return app.state.db_session_factory

async def get_session() -> AsyncSession:
    """获取数据库会话"""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 3. 更新 API 路由

在 API 端点中使用会话：

```python
from app.controller.depends import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

@router.post("/start")
async def start_calc_execution(
    file_path: str,
    func_name: str,
    session_id: str,
    params: Optional[dict] = None,
    load_from_cache: bool = True,
    tokenPayloads: TokenPayloads = Depends(get_token_payload),
    db_session: AsyncSession = Depends(get_session),  # ← 添加此行
) -> ResponseResult[dict]:
    """启动计算执行"""
    
    service = get_execution_service()
    service.db_session = db_session  # ← 传入数据库会话
    
    result = await service.start_execution(
        user_id=str(tokenPayloads.id),
        file_path=file_path,
        func_name=func_name,
        session_id=session_id,
        params=params or {},
        load_from_cache=load_from_cache,
    )
    
    return ok(data=result)
```

---

## ✅ 第四阶段：测试

### 1. 单元测试

```bash
# 运行单元测试
pytest tests/test_user_input_history.py -v

# 应该看到：
# test_save_input_history PASSED
# test_complete_execution PASSED
# test_get_latest_history PASSED
# test_publish_version PASSED
# test_restore_from_version PASSED
# ... (所有测试都 PASSED)
```

### 2. 集成测试

```bash
# 启动 FastAPI 服务
python -m uvicorn app.main:app --reload

# 在另一个终端运行集成测试
curl -X POST http://localhost:8000/v1/calc/execution/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "examples/calc.py",
    "func_name": "calculate",
    "session_id": "test_sess_1",
    "params": {"x": 10},
    "load_from_cache": false
  }'

# 应该得到 200 OK 响应，包含 UI 或结果
```

### 3. 手动验证

```bash
# 1. 启动服务
python -m uvicorn app.main:app --reload

# 2. 测试启动执行
curl -X POST http://localhost:8000/v1/calc/execution/start \
  -H "Authorization: Bearer test_token" \
  -d '{"file_path":"calc.py","func_name":"calculate","session_id":"test_1","load_from_cache":true}'

# 3. 测试执行历史
curl -X GET "http://localhost:8000/v1/calc/execution/execution-history?file_path=calc.py&func_name=calculate" \
  -H "Authorization: Bearer test_token"

# 4. 测试发布版本
curl -X POST http://localhost:8000/v1/calc/execution/publish \
  -H "Authorization: Bearer test_token" \
  -d '{"file_path":"calc.py","func_name":"calculate","version_name":"v1.0"}'

# 5. 测试恢复版本
curl -X POST http://localhost:8000/v1/calc/execution/restore-from-version \
  -H "Authorization: Bearer test_token" \
  -d '{"version_id":1}'
```

---

## ✅ 第五阶段：监控和维护

### 1. 检查数据库大小

```sql
-- 检查各表的数据量
SELECT 
    'user_input_history' as table_name,
    COUNT(*) as record_count
FROM user_input_history
UNION ALL
SELECT 
    'published_version',
    COUNT(*) 
FROM published_version
UNION ALL
SELECT 
    'input_cache',
    COUNT(*) 
FROM input_cache;
```

### 2. 清理过期缓存

```bash
# 创建定时任务（例如 cron）来清理过期缓存
python scripts/cleanup_expired_caches.py

# 或在 FastAPI 中定期运行
from app.db.dao.user_input_history_dao import InputCacheDAO

async def cleanup_task():
    """定期清理过期缓存"""
    from sqlalchemy.ext.asyncio import AsyncSession
    
    async with async_session() as session:
        deleted = await InputCacheDAO.delete_expired_caches(session)
        logger.info(f"清理了 {deleted} 个过期缓存")
```

### 3. 监控性能

```python
# 添加性能监控日志
import time

async def resume_execution(...):
    start = time.time()
    
    # ... 执行逻辑 ...
    
    elapsed = time.time() - start
    logger.info(f"执行耗时: {elapsed:.2f}s")
```

---

## 🔍 故障排查

### 问题 1：表创建失败

```
错误：Access denied for user 'root'@'localhost'
```

**解决：** 检查数据库连接字符串和权限
```bash
# 测试连接
mysql -u root -p -h localhost

# 检查用户权限
GRANT ALL PRIVILEGES ON uzoncalc.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
```

### 问题 2：ORM 映射错误

```
错误：No module named 'app.db.models.user_input_history'
```

**解决：** 确保 `__init__.py` 文件存在
```bash
touch app/db/models/__init__.py
touch app/db/dao/__init__.py
touch app/model/__init__.py
```

### 问题 3：缓存不加载

```python
# 检查缓存是否存在
async with async_session() as session:
    cache = await InputCacheDAO.get_cache(
        session, 
        user_id="user_1",
        file_path="calc.py",
        func_name="calculate"
    )
    print(f"缓存: {cache}")  # 应该不为 None
```

### 问题 4：版本恢复返回 None

```python
# 检查版本是否存在且未过期
async with async_session() as session:
    versions = await PublishedVersionDAO.get_published_versions(
        session,
        user_id="user_1",
        file_path="calc.py",
        func_name="calculate"
    )
    print(f"版本: {versions}")  # 应该至少有一个版本
```

---

## 📊 性能基准

运行基准测试以验证性能：

```python
# tests/benchmark.py
import asyncio
import time

async def benchmark_cache_load():
    """基准测试：缓存加载"""
    start = time.time()
    
    # 执行 1000 次缓存查询
    for i in range(1000):
        cache = await InputCacheDAO.get_cache(
            session,
            user_id=f"user_{i % 10}",
            file_path="calc.py",
            func_name="calculate"
        )
    
    elapsed = time.time() - start
    avg_time = elapsed / 1000 * 1000  # 转换为毫秒
    print(f"平均缓存查询时间: {avg_time:.2f}ms")
    assert avg_time < 5, "缓存查询过慢"

# 运行基准测试
asyncio.run(benchmark_cache_load())
```

---

## 📝 清单总结

- [ ] 代码准备完成
- [ ] 数据库表创建成功
- [ ] 应用启动代码更新
- [ ] 会话依赖注入配置
- [ ] API 路由集成数据库会话
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试通过
- [ ] 性能验证完成
- [ ] 监控和日志配置完成

---

## 🚀 部署清单

- [ ] 备份现有数据库
- [ ] 在测试环境验证
- [ ] 在预发布环境验证
- [ ] 监控告警配置
- [ ] 回滚计划准备
- [ ] 在生产环境部署

---

**更新时间：** 2026-01-29  
**作者：** UzonCalc Team  
**版本：** 1.0
