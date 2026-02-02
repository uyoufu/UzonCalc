"""
定时任务使用示例
"""
import datetime
from pathlib import Path


# ============================================
# 示例 1: 创建临时文件记录
# ============================================

async def example_create_tmp_file():
    """
    创建临时文件记录示例
    """
    from app.db.models.tmp_file import TmpFile
    from app.db.manager import get_db_manager

    db_manager = get_db_manager()

    # 创建一个 24 小时后过期的临时文件记录
    async with db_manager.session() as session:
        tmp_file = TmpFile(
            file_path="/path/to/temp/file.pdf",
            file_type="pdf",
            file_size=1024000,  # 1MB
            is_directory=False,
            expire_time=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=24),
            remark="用户生成的临时 PDF 文件",
        )
        session.add(tmp_file)
        await session.commit()
        print(f"创建临时文件记录: {tmp_file.file_path}")


# ============================================
# 示例 2: 创建临时目录记录
# ============================================

async def example_create_tmp_directory():
    """
    创建临时目录记录示例
    """
    from app.db.models.tmp_file import TmpFile
    from app.db.manager import get_db_manager

    db_manager = get_db_manager()

    async with db_manager.session() as session:
        tmp_dir = TmpFile(
            file_path="/path/to/temp/export_folder",
            is_directory=True,
            expire_time=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=48),  # 48 小时后过期
            remark="导出的临时文件夹",
        )
        session.add(tmp_dir)
        await session.commit()
        print(f"创建临时目录记录: {tmp_dir.file_path}")


# ============================================
# 示例 3: 自定义 Cron 定时任务
# ============================================

from app.schedule.cron_schedule_job import BaseCronScheduleJob


class DailyReportScheduleJob(BaseCronScheduleJob):
    """
    每天生成报告的定时任务
    """

    def __init__(self):
        job_id = "daily_report_schedule_job"
        # 每天早上 8 点执行
        cron = "0 0 8 * * *"
        super().__init__(job_id, cron)

    async def run_async(self):
        import logging

        logger = logging.getLogger("apscheduler")
        logger.info("开始生成每日报告...")

        # 你的报告生成逻辑
        # ...

        logger.info("每日报告生成完成")


# ============================================
# 示例 4: 自定义 Interval 定时任务
# ============================================

from app.schedule.interval_schedule_job import BaseIntervalScheduleJob


class DataSyncScheduleJob(BaseIntervalScheduleJob):
    """
    数据同步定时任务
    """

    def __init__(self):
        job_id = "data_sync_schedule_job"
        # 每 5 分钟执行一次
        interval = 300  # 秒
        super().__init__(job_id, interval)

    async def run_async(self):
        import logging

        logger = logging.getLogger("apscheduler")
        logger.info("开始数据同步...")

        # 你的数据同步逻辑
        # ...

        logger.info("数据同步完成")


# ============================================
# 示例 5: 查询过期的临时文件
# ============================================

async def example_query_expired_files():
    """
    查询过期的临时文件
    """
    from app.db.models.tmp_file import TmpFile
    from app.db.manager import get_db_manager
    from sqlalchemy import select, and_

    db_manager = get_db_manager()

    async with db_manager.session() as session:
        current_time = datetime.datetime.now(datetime.timezone.utc)

        stmt = select(TmpFile).where(
            and_(TmpFile.is_deleted == False, TmpFile.expire_time <= current_time)
        )

        result = await session.execute(stmt)
        expired_files = result.scalars().all()

        print(f"找到 {len(expired_files)} 个过期文件")
        for file in expired_files:
            print(f"  - {file.file_path} (过期时间: {file.expire_time})")


# ============================================
# 示例 6: 手动触发临时文件清理
# ============================================

async def example_manual_cleanup():
    """
    手动触发临时文件清理
    """
    from app.schedule.jobs.tmp_file_cleaner import TmpFileCleanerScheduleJob

    job = TmpFileCleanerScheduleJob()
    await job.run_async()
    print("手动清理完成")


# ============================================
# 示例 7: 在 FastAPI 中集成定时任务
# ============================================

from fastapi import FastAPI
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期管理
    """
    # 启动时初始化调度器
    from app.schedule.scheduler import start_scheduler

    print("启动定时任务调度器...")
    scheduler = start_scheduler()

    yield

    # 关闭时停止调度器
    from app.schedule.scheduler import shutdown_scheduler

    print("关闭定时任务调度器...")
    shutdown_scheduler()


# 创建 FastAPI 应用
# app = FastAPI(lifespan=lifespan)


# ============================================
# 示例 8: 创建带文件的临时文件记录
# ============================================

async def example_create_file_with_record(content: bytes, expire_hours: int = 24):
    """
    创建实际文件并记录到数据库
    """
    import os
    from app.db.models.tmp_file import TmpFile
    from app.db.manager import get_db_manager

    # 创建临时文件目录
    temp_dir = Path("data/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"temp_{timestamp}.pdf"
    file_path = temp_dir / file_name

    # 写入文件
    file_path.write_bytes(content)
    file_size = file_path.stat().st_size

    # 记录到数据库
    db_manager = get_db_manager()
    async with db_manager.session() as session:
        tmp_file = TmpFile(
            file_path=str(file_path.absolute()),
            file_type="pdf",
            file_size=file_size,
            is_directory=False,
            expire_time=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=expire_hours),
            remark="API 生成的临时文件",
        )
        session.add(tmp_file)
        await session.commit()

    print(f"创建临时文件: {file_path}")
    return str(file_path.absolute())


# ============================================
# 示例 9: 批量创建临时文件记录
# ============================================

async def example_batch_create_tmp_files(file_paths: list[str], expire_hours: int = 24):
    """
    批量创建临时文件记录
    """
    from app.db.models.tmp_file import TmpFile
    from app.db.manager import get_db_manager

    db_manager = get_db_manager()
    expire_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        hours=expire_hours
    )

    async with db_manager.session() as session:
        for file_path in file_paths:
            tmp_file = TmpFile(
                file_path=file_path,
                is_directory=False,
                expire_time=expire_time,
                remark="批量创建的临时文件",
            )
            session.add(tmp_file)

        await session.commit()
        print(f"批量创建了 {len(file_paths)} 个临时文件记录")
