from .base_schedule_job import BaseScheduleJob, TriggerType


class BaseCronScheduleJob(BaseScheduleJob):
    """
    基础 Cron 定时器
    """

    def __init__(self, job_id: str, cron: str):
        """
        初始化 Cron 定时器
        :param job_id: 定时器 ID
        :param cron: Cron 表达式，格式为 "秒 分 时 日 月 周"
        """
        super().__init__(job_id)
        self.cron = cron

    def start(self):
        """
        启动定时器
        :return:
        """

        from .scheduler import start_scheduler

        scheduler = start_scheduler()
        scheduler.add_job(
            func=self.run_async,
            trigger=TriggerType.CRON,
            id=self.job_id,
            replace_existing=True,
            **self._parse_cron(self.cron),
        )

    def _parse_cron(self, cron: str):
        """
        解析 Cron 表达式
        :param cron: Cron 表达式，格式为 "秒 分 时 日 月 周"
        :return:
        """
        parts = cron.split()
        if len(parts) != 6:
            raise ValueError("Cron 表达式必须包含 6 个部分（秒 分 时 日 月 周）")

        # 参考 https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html
        return {
            "second": parts[0],  # 0-59
            "minute": parts[1],  # 0-59
            "hour": parts[2],  # 0-23
            "day": parts[3],  # 1-31
            "month": parts[4],  # 1-12
            "day_of_week": parts[5],  # 0-6 或 mon,tue,wed,thu,fri,sat,sun
        }
