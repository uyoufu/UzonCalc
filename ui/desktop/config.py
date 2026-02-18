"""
配置管理模块
从 app.ini 文件中读取应用程序配置
"""

import os
import configparser
from pathlib import Path


class Config:
    """应用程序配置类"""

    def __init__(self, config_file="app.ini"):
        """
        初始化配置

        Args:
            config_file: 配置文件路径，默认为 'app.ini'
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        # 获取当前文件所在目录
        current_dir = Path(__file__).parent
        config_path = current_dir / self.config_file

        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        self.config.read(config_path, encoding="utf-8")

    @property
    def version(self) -> str:
        """应用程序版本"""
        return self.config.get("app", "version", fallback="1.0.0")

    @property
    def name(self) -> str:
        """应用程序名称"""
        return self.config.get("app", "name", fallback="uzoncalc")

    @property
    def ui_url(self) -> str:
        """UI 地址"""
        return self.config.get("app", "uiUrl", fallback="http://localhost:3346/")

    @property
    def width(self) -> int:
        """窗口宽度"""
        return self.config.getint("app", "width", fallback=1200)

    @property
    def height(self) -> int:
        """窗口高度"""
        return self.config.getint("app", "height", fallback=800)

    def get(self, section: str, option: str, fallback=None):
        """
        获取配置项

        Args:
            section: 配置节
            option: 配置项
            fallback: 默认值

        Returns:
            配置值
        """
        return self.config.get(section, option, fallback=fallback)

    def reload(self):
        """重新加载配置"""
        self._load_config()


# 创建全局配置实例
config = Config()


if __name__ == "__main__":
    # 测试配置读取
    print(f"应用名称: {config.name}")
    print(f"应用版本: {config.version}")
    print(f"UI 地址: {config.ui_url}")
    print(f"窗口宽度: {config.width}")
    print(f"窗口高度: {config.height}")
