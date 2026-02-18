# UzonCalc Desktop 部署配置

# Python 版本配置（仅 Windows）
PYTHON_VERSION = "3.11"  # 可选: "3.11", "3.12"

# 需要排除的文件和目录（复制时忽略）
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".git",
    ".gitignore",
    "*.log",
    "build",
    "dist",
    "*.egg-info",
    ".vscode",
    ".idea",
]

# Desktop 排除目录
DESKTOP_EXCLUDE = [
    "__pycache__",
    "scrips",  # 部署脚本不需要打包
    ".pytest_cache",
    "build",
    "dist",
]

# API 排除模式
API_EXCLUDE = [
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    "build",
    "logs",  # 日志文件夹
    "data/db/*.db",  # 数据库文件
    "data/calcs/*",  # 计算结果文件
]

# Web 构建配置
WEB_BUILD_COMMAND = ["npm", "run", "build"]
WEB_SOURCE_DIR = "dist/spa"
WEB_TARGET_DIR = "api/data/www"

# Python Embedded 下载镜像（可选）
# 如果官方下载慢，可以使用镜像
USE_MIRROR = False
PYTHON_MIRROR_URLS = {
    "3.11": "https://npm.taobao.org/mirrors/python/3.11.9/python-3.11.9-embed-amd64.zip",
    "3.12": "https://npm.taobao.org/mirrors/python/3.12.3/python-3.12.3-embed-amd64.zip",
}

# pip 镜像配置
USE_PIP_MIRROR = False
PIP_MIRROR_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
