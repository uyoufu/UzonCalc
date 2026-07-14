import datetime


def get_utc_now():
    """
    获取当前 UTC 时间
    :return: UTC 时间的 datetime 对象
    """
    return datetime.datetime.now(datetime.timezone.utc)
