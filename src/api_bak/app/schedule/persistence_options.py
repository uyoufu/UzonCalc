"""
APScheduler 持久化配置示例

由于 APScheduler 的 SQLAlchemyJobStore 不支持 SQLAlchemy 的异步引擎，
这里提供几种持久化方案供参考。
"""

# ============================================
# 方案 1: 使用单独的同步 SQLAlchemy 引擎
# ============================================


def create_sync_scheduler_with_sqlalchemy():
    """
    为 APScheduler 创建单独的同步 SQLAlchemy 引擎
    """
    import datetime
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.executors.pool import ThreadPoolExecutor
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
    from sqlalchemy import create_engine
    from config import app_config

    # 创建同步引擎（注意：不是 create_async_engine）
    # 将 postgresql+asyncpg:// 转换为 postgresql://
    database_url = app_config.database_url.replace("+asyncpg", "")
    sync_engine = create_engine(
        database_url,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,
    )

    jobstores = {"default": SQLAlchemyJobStore(engine=sync_engine)}

    executors = {"default": ThreadPoolExecutor(max_workers=10)}

    job_defaults = {
        "coalesce": False,
        "max_instances": 5,
    }

    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=datetime.timezone.utc,
    )

    return scheduler


# ============================================
# 方案 2: 使用 Redis 作为 JobStore
# ============================================


def create_scheduler_with_redis():
    """
    使用 Redis 作为任务存储
    需要安装: pip install apscheduler[redis] redis
    """
    import datetime
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.executors.pool import ThreadPoolExecutor
    from apscheduler.jobstores.redis import RedisJobStore

    jobstores = {
        "default": RedisJobStore(
            host="localhost",
            port=6379,
            db=0,
            password=None,  # 如果 Redis 有密码
        )
    }

    executors = {"default": ThreadPoolExecutor(max_workers=10)}

    job_defaults = {
        "coalesce": False,
        "max_instances": 5,
    }

    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=datetime.timezone.utc,
    )

    return scheduler


# ============================================
# 方案 3: 使用 MongoDB 作为 JobStore
# ============================================


def create_scheduler_with_mongodb():
    """
    使用 MongoDB 作为任务存储
    需要安装: pip install pymongo
    """
    import datetime
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.executors.pool import ThreadPoolExecutor
    from apscheduler.jobstores.mongodb import MongoDBJobStore
    from pymongo import MongoClient

    # 创建 MongoDB 客户端
    mongo_client = MongoClient(
        host="localhost",
        port=27017,
        username="your_username",  # 如果需要认证
        password="your_password",
    )

    jobstores = {
        "default": MongoDBJobStore(
            client=mongo_client,
            database="apscheduler",
            collection="jobs",
        )
    }

    executors = {"default": ThreadPoolExecutor(max_workers=10)}

    job_defaults = {
        "coalesce": False,
        "max_instances": 5,
    }

    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=datetime.timezone.utc,
    )

    return scheduler


# ============================================
# 方案 4: 使用内存存储（当前方案）
# ============================================


def create_scheduler_with_memory():
    """
    使用内存存储（默认方案）
    优点: 简单，无需额外依赖
    缺点: 应用重启后任务会丢失
    """
    import datetime
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.executors.pool import ThreadPoolExecutor
    from apscheduler.jobstores.memory import MemoryJobStore

    jobstores = {"default": MemoryJobStore()}

    executors = {"default": ThreadPoolExecutor(max_workers=10)}

    job_defaults = {
        "coalesce": False,
        "max_instances": 5,
    }

    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=datetime.timezone.utc,
    )

    return scheduler


# ============================================
# 如何替换当前的 scheduler.py
# ============================================

"""
要使用以上任一方案，请修改 scheduler.py 中的 start_scheduler() 函数：

1. 选择上面的某个方案
2. 替换 start_scheduler() 中的 jobstores 配置
3. 确保安装相应的依赖包

示例：使用方案 1（同步 SQLAlchemy）

def start_scheduler() -> AsyncIOScheduler:
    global __scheduler

    if __scheduler:
        return __scheduler

    from sqlalchemy import create_engine
    from config import app_config
    
    # 创建同步引擎
    database_url = app_config.database_url.replace("+asyncpg", "")
    sync_engine = create_engine(database_url, pool_size=5)
    
    jobstores = {
        "default": SQLAlchemyJobStore(engine=sync_engine)
    }
    
    # ... 其余代码保持不变
"""
