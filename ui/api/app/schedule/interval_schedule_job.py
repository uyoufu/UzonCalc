from .base_schedule_job import BaseScheduleJob, TriggerType


class BaseIntervalScheduleJob(BaseScheduleJob):
    """
    基础 Interval 定时器
    """

    def __init__(self, job_id: str, interval: int):
        """
        初始化 Interval 定时器
        :param job_id: 定时器 ID
        :param interval: 间隔时间（秒）
        """
        super().__init__(job_id)
        self.interval = interval

    def start(self):
        """
        启动定时器
        :return:
        """

        from .scheduler import start_scheduler

        scheduler = start_scheduler()
        scheduler.add_job(
            func=self.run_async,
            trigger=TriggerType.INTERVAL,
            id=self.job_id,
            replace_existing=True,
            seconds=self.interval,
        )
