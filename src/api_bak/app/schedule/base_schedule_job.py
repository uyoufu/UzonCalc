import asyncio
from enum import StrEnum


class TriggerType(StrEnum):
    """
    触发器类型
    """

    CRON = "cron"
    INTERVAL = "interval"
    DATE = "date"


class BaseScheduleJob:
    """
    基础定时器
    """

    def __init__(self, job_id: str):
        self.job_id = job_id

    def start(self):
        """
        启动定时器
        :return:
        """

        raise NotImplementedError("请在子类中实现该方法")

    async def run_async(self):
        """
        定时器执行的方法（异步）
        :return:
        """
        raise NotImplementedError("请在子类中实现该方法")
