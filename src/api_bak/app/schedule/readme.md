# 定时任务模块 (Schedule Module)

本模块提供了基于 APScheduler 的定时任务管理功能，支持 Cron 和 Interval 两种触发方式。

## 目录结构

```
app/schedule/
├── __init__.py              # 模块初始化
├── base_schedule_job.py     # 基础定时任务类
├── cron_schedule_job.py     # Cron 定时任务基类
├── interval_schedule_job.py # Interval 定时任务基类
├── scheduler.py             # 调度器管理
├── jobs/                    # 具体的定时任务
│   ├── __init__.py
│   └── tmp_file_cleaner.py  # 临时文件清理任务
└── README.md               # 使用文档
```

## 快速开始

### 1. 初始化调度器

在 FastAPI 应用启动时初始化调度器：

```python
from app.schedule.scheduler import use_scheduler

# 在 lifespan 或 startup 事件中调用
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动调度器
    scheduler = use_scheduler()
    
    yield
    
    # 关闭调度器
    from app.schedule.scheduler import shutdown_scheduler
    shutdown_scheduler()
```

### 2. 创建定时任务

#### 使用 Cron 表达式

```python
from app.schedule.cron_schedule_job import BaseCronScheduleJob

class MyScheduleJob(BaseCronScheduleJob):
    def __init__(self):
        job_id = "my_schedule_job"
        # Cron 表达式: 秒 分 时 日 月 周
        # 每天凌晨 2 点执行
        cron = "0 0 2 * * *"
        super().__init__(job_id, cron)
    
    async def run_async(self):
        # 你的任务逻辑
        print("执行定时任务")
```

#### 使用 Interval 间隔

```python
from app.schedule.interval_schedule_job import BaseIntervalScheduleJob

class MyIntervalJob(BaseIntervalScheduleJob):
    def __init__(self):
        job_id = "my_interval_job"
        # 每 300 秒（5 分钟）执行一次
        interval = 300
        super().__init__(job_id, interval)
    
    async def run_async(self):
        # 你的任务逻辑
        print("执行间隔任务")
```

### 3. 注册定时任务

在 `scheduler.py` 的 `_register_schedule_jobs()` 函数中注册你的任务：

```python
def _register_schedule_jobs():
    from .jobs.tmp_file_cleaner import TmpFileCleanerScheduleJob
    from .jobs.my_job import MyScheduleJob
    
    job_classes = [
        TmpFileCleanerScheduleJob,
        MyScheduleJob,  # 添加你的任务
    ]
    
    for job_class in job_classes:
        job_instance = job_class()
        job_instance.start()
        logging.info(f"注册定时任务: {job_instance.job_id}")
```

## Cron 表达式说明

Cron 表达式格式：`秒 分 时 日 月 周`

| 字段 | 允许值 | 特殊字符 |
|-----|--------|---------|
| 秒  | 0-59   | * / , - |
| 分  | 0-59   | * / , - |
| 时  | 0-23   | * / , - |
| 日  | 1-31   | * / , - |
| 月  | 1-12   | * / , - |
| 周  | 0-6    | * / , - |

### 常用示例

```python
# 每小时执行一次（整点）
"0 0 * * * *"

# 每天凌晨 2 点执行
"0 0 2 * * *"

# 每周一上午 9 点执行
"0 0 9 * * 1"

# 每 30 分钟执行一次
"0 */30 * * * *"

# 工作日每小时执行
"0 0 * * * 1-5"
```

## 内置任务

### 临时文件清理任务 (TmpFileCleanerScheduleJob)

自动清理数据库中标记为过期的临时文件和目录。

- **任务 ID**: `tmp_file_cleaner_schedule_job`
- **执行周期**: 每小时整点执行一次
- **功能**:
  - 查询数据库中过期且未删除的临时文件
  - 删除文件系统中的对应文件或目录
  - 清理空目录
  - 更新数据库记录状态

#### 使用方法

1. 在数据库中插入临时文件记录：

```python
from app.db.models.tmp_file import TmpFile
from app.db.manager import get_db_manager
import datetime

async def create_tmp_file(file_path: str, expire_hours: int = 24):
    """创建临时文件记录"""
    db_manager = get_db_manager()
    
    async with db_manager.session() as session:
        tmp_file = TmpFile(
            file_path=file_path,
            file_type="pdf",
            is_directory=False,
            expire_time=datetime.datetime.now(datetime.timezone.utc) 
                       + datetime.timedelta(hours=expire_hours),
            remark="临时生成的 PDF 文件"
        )
        session.add(tmp_file)
        await session.commit()
```

2. 定时任务会自动清理过期文件

## 数据库表结构

### tmp_files 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | Integer | 主键 |
| oid | String(24) | 对象 ID |
| file_path | String(500) | 文件路径（绝对路径）|
| file_type | String(50) | 文件类型 |
| file_size | Integer | 文件大小（字节）|
| is_directory | Boolean | 是否为目录 |
| expire_time | DateTime | 过期时间（UTC）|
| remark | Text | 备注信息 |
| is_deleted | Boolean | 是否已删除 |
| deleted_at | DateTime | 删除时间 |
| createdAt | DateTime | 创建时间 |

## 依赖安装

```bash
pip install apscheduler sqlalchemy
```

## 注意事项

1. **时区设置**: 所有时间使用 UTC 时区
2. **任务存储**: 使用内存存储（MemoryJobStore），应用重启后任务会重新注册
3. **并发控制**: 默认最多 5 个任务实例同时运行
4. **错误处理**: 任务执行失败会记录日志，不影响其他任务
5. **数据库初始化**: 确保在启动调度器前已初始化数据库

> **注意**: 由于 APScheduler 的 SQLAlchemy 存储不支持异步引擎，当前使用内存存储。如果需要任务持久化，可以考虑：
> - 使用 Redis 作为 jobstore（需要安装 `redis` 和 `apscheduler[redis]`）
> - 使用 MongoDB 作为 jobstore（需要安装 `pymongo`）
> - 为 APScheduler 创建单独的同步数据库连接

## 调试和日志

调度器使用 Python logging 模块，logger 名称为 `apscheduler`。

```python
import logging

# 设置日志级别
logging.getLogger("apscheduler").setLevel(logging.INFO)
```

## 高级配置

在 `scheduler.py` 中可以自定义调度器配置：

```python
executors = {
    "default": ThreadPoolExecutor(max_workers=20)  # 增加工作线程
}

job_defaults = {
    "coalesce": True,       # 合并错过的任务
    "max_instances": 10,    # 增加最大实例数
}
```

## 常见问题

### 1. 任务没有执行？

- 检查调度器是否已启动
- 检查 Cron 表达式是否正确
- 查看日志是否有错误信息

### 2. 如何停止某个任务？

```python
from app.schedule.scheduler import use_scheduler

scheduler = use_scheduler()
scheduler.remove_job('job_id')
```

### 3. 如何手动触发任务？

```python
from app.schedule.jobs.tmp_file_cleaner import TmpFileCleanerScheduleJob

job = TmpFileCleanerScheduleJob()
await job.run_async()
```

## 扩展阅读

- [APScheduler 官方文档](https://apscheduler.readthedocs.io/)
- [Cron 表达式详解](https://en.wikipedia.org/wiki/Cron)
