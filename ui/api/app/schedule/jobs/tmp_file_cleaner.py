"""
临时文件清理定时任务
"""

import logging

from app.schedule.cron_schedule_job import BaseCronScheduleJob
from app.db.manager import get_db_manager
from app.service.tmp_file.tmp_file_service import clean_expired_tmp_files


class TmpFileCleanerScheduleJob(BaseCronScheduleJob):
    """
    临时文件清理定时任务
    定期清理过期的临时文件和目录
    """

    def __init__(self):
        job_id = "tmp_file_cleaner_schedule_job"
        # Cron 表达式: 秒 分 时 日 月 周
        # 每小时的第 0 分钟执行一次
        cron = "0 0 * * * *"
        super().__init__(job_id, cron)

    async def run_async(self):
        """
        定时器执行的方法：清理过期的临时文件
        """
        logger = logging.getLogger("apscheduler")
        logger.info("开始执行临时文件清理任务")

        db_manager = get_db_manager()
        # 使用数据库会话
        async with db_manager.session() as session:
            deleted_count, failed_count = await clean_expired_tmp_files(session)
            logger.info(
                f"临时文件清理任务执行完成 - 成功: {deleted_count}, 失败: {failed_count}"
            )
