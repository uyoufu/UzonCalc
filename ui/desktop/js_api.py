from logger import logger


class JsApi:
    """JavaScript API - 提供给前端调用的接口"""

    def __init__(self, service_manager):
        self.service_manager = service_manager

    def ping(self):
        """测试接口"""
        logger.info("Received ping from frontend")
        return "pong"

    def get_api_status(self):
        """获取 API 服务状态"""
        status = self.service_manager.get_status()
        logger.info(f"API status requested: {status}")
        return status

    def restart_api(self):
        """重启 API 服务"""
        logger.info("Restarting API service from frontend")
        return self.service_manager.restart()
