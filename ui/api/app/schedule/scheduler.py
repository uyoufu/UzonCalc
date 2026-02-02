import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore

from config import logger

# 不要直接导入，使用 use_scheduler 方法获取
__scheduler: AsyncIOScheduler | None = None


# 在初始化 FastAPI 的时候调用，并将返回的 scheduler 赋给 app
def start_scheduler() -> AsyncIOScheduler:
    """
    获取或创建调度器实例
    """
    global __scheduler

    if __scheduler:
        return __scheduler

    # APScheduler 不支持异步引擎，使用内存存储
    # 注意：内存存储意味着任务不会持久化，应用重启后需要重新注册
    jobstores = {"default": MemoryJobStore()}
    executors = {"default": ThreadPoolExecutor(max_workers=10)}

    job_defaults = {
        "coalesce": False,  # 是否合并错过的任务
        "max_instances": 5,  # 同一任务的最大实例数
    }

    # 使用 AsyncIOScheduler
    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=datetime.timezone.utc,
    )

    __scheduler = scheduler

    logger.info("Loading schedule...")

    # 注册定时任务
    _register_schedule_jobs()

    # 注意这里一定要调用 start 启动 scheduler
    scheduler.start()
    logger.info("Scheduler started!")

    return __scheduler


def _register_schedule_jobs():
    """
    注册定时任务
    在这里手动注册所有需要执行的定时任务
    """
    from .base_schedule_job import BaseScheduleJob

    # 导入具体的定时任务类
    from .jobs.tmp_file_cleaner import TmpFileCleanerScheduleJob

    # 在这里添加需要注册的任务类
    job_classes = [
        TmpFileCleanerScheduleJob,  # 临时文件清理任务
        # 可以在这里添加更多任务...
    ]

    for job_class in job_classes:
        job_instance: BaseScheduleJob = job_class()
        job_instance.start()
        logger.info(f"Registered schedule job: {job_instance.job_id}")


def shutdown_scheduler():
    """
    关闭调度器
    """
    global __scheduler
    if __scheduler:
        __scheduler.shutdown()
        logger.info("Scheduler shutdown")
