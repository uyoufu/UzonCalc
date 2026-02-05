import configparser
import logging
import logging.config
import os

app_name = "uzoncalc"


# 当前文件所在目录
def setup_logger():
    # 获取日志保存位置，若不存在，则创建目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = f"{current_dir}/../logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.config.fileConfig(f"{current_dir}/logging.ini")

    return logging.getLogger(app_name)


logger = setup_logger()


class AppConfig:
    __config: configparser.ConfigParser
    env: str

    def __load_config_files(self):
        """
        加载多个配置
        :return:
        """
        self.env = "prod"

        config_dir = os.path.dirname(__file__)
        dot_env_path = os.path.join(config_dir, ".env")
        if os.path.exists(dot_env_path):
            with open(dot_env_path, "r") as file:
                self.env = file.read().strip()

        config_paths = [
            os.path.join(config_dir, "app.ini"),
            os.path.join(config_dir, f"app.{self.env}.ini"),
        ]

        # 获取环境变量 xxx-ENV 值
        env_name = app_name.upper() + "-ENV"
        pro_env = os.getenv(env_name)
        if pro_env:
            config_paths.append(f"config/app.{pro_env}.ini")
        logger.info(
            f"Current environment: {self.env}, env variable: {pro_env}, config files: {config_paths}"
        )

        # 初始化配置文件
        conf = configparser.ConfigParser()
        for _, config_path in enumerate(config_paths):
            conf.read(config_path, encoding="utf-8")

        logger.info("Config loaded successfully.")
        return conf

    def __init__(self):
        # 获取配置文件
        # 从 config/.env 文件中读取字符串
        conf = self.__load_config_files()
        self.__config = conf

    def __new__(cls) -> "AppConfig":
        if not hasattr(cls, "_instance"):
            cls._instance = super(AppConfig, cls).__new__(cls)
        return cls._instance

    def get(self, section: str, option: str):
        """
        读取配置
        """
        return self.__config.get(section, option)

    # region app 配置
    @property
    def version(self) -> str:
        return self.get("app", "version")

    @property
    def app_name(self) -> str:
        return self.get("app", "name")

    @property
    def welcome(self) -> str:
        return self.get("app", "welcome")

    @property
    def is_desktop(self) -> bool:
        """是否为桌面版本"""
        try:
            return self.__config.getboolean("app", "desktop")
        except (configparser.NoOptionError, configparser.NoSectionError):
            return False

    @property
    def host(self) -> str:
        return self.get("app", "host")

    @property
    def port(self) -> int:
        return self.__config.getint("app", "port")

    @property
    def token_secret(self) -> str:
        return self.get("app", "token_secret")

    @property
    def allow_origins(self) -> list[str]:
        origins = self.get("app", "allow_origins")
        return [origin.strip() for origin in origins.split(",")]

    # endregion

    # region log
    @property
    def log_level(self) -> int:
        return logging.getLevelNamesMapping().get(
            self.get("log", "level"), logging.INFO
        )

    # endregion

    # region database
    @property
    def postgres_enabled(self) -> bool:
        return self.__config.getboolean("postgres", "enabled")

    @property
    def sqlite_enabled(self) -> bool:
        return self.__config.getboolean("sqlite", "enabled")

    @property
    def postgres_host(self) -> str:
        return self.get("postgres", "host")

    @property
    def postgres_port(self) -> int:
        return self.__config.getint("postgres", "port")

    @property
    def postgres_user(self) -> str:
        return self.get("postgres", "user")

    @property
    def postgres_password(self) -> str:
        return self.get("postgres", "password")

    @property
    def postgres_database(self) -> str:
        return self.get("postgres", "database")

    @property
    def sqlite_source(self) -> str:
        return self.get("sqlite", "source")

    def get_db_connection(self) -> str:
        """
        根据配置自动创建数据库连接字符串
        优先顺序: postgres > sqlite
        若都不启用，则抛出异常
        """
        if self.postgres_enabled:
            # 使用 postgresql 连接字符串格式: postgresql://user:password@host:port/database
            connection_str = (
                f"postgresql://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
            )
            logger.info(
                f"Using PostgreSQL connection: {self.postgres_host}:{self.postgres_port}"
            )
            return connection_str
        elif self.sqlite_enabled:
            logger.info(f"Using SQLite connection: {self.sqlite_source}")
            return self.sqlite_source
        else:
            raise ValueError(
                "No database configured. Please enable either PostgreSQL or SQLite in config file."
            )

    # endregion

    # region user
    @property
    def default_userId(self) -> str:
        return self.get("user", "default_userId")

    @property
    def default_password(self) -> str:
        password = self.get("user", "default_password")
        # 进行 sha256 加密
        import hashlib

        sha256_hash = hashlib.sha256()
        sha256_hash.update(password.encode("utf-8"))
        return sha256_hash.hexdigest()

    # endregion

    # region sandbox
    @property
    def sandbox_mode(self) -> str:
        """获取 sandbox 执行模式: local 或 remote"""
        return self.get("sandbox", "mode")

    @property
    def sandbox_safe_dirs(self) -> list[str]:
        dirs = self.get("sandbox", "safe_dirs")
        return [d.strip() for d in dirs.split(",") if d.strip()]

    @property
    def sandbox_session_timeout(self) -> int:
        return self.__config.getint("sandbox", "session_timeout")

    @property
    def sandbox_remote_url(self) -> str:
        """获取远程 sandbox 服务地址"""
        return self.get("sandbox", "remote_url")

    @property
    def sandbox_remote_timeout(self) -> float:
        """获取远程调用超时时间（秒）"""
        return self.__config.getfloat("sandbox", "remote_timeout")

    # endregion


app_config = AppConfig()
