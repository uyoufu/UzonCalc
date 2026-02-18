"""
UzonCalc Desktop Deployment Script

支持平台: Windows, macOS, Linux
"""

import argparse
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

# 导入版本信息工具
try:
    from version_info import generate_version_info
    HAS_VERSION_INFO = True
except ImportError:
    HAS_VERSION_INFO = False

# 导入配置（如果存在）
try:
    from deploy_config import (
        PYTHON_VERSION,
        DESKTOP_EXCLUDE,
        API_EXCLUDE,
        USE_MIRROR,
        PYTHON_MIRROR_URLS,
        USE_PIP_MIRROR,
        PIP_MIRROR_URL,
    )
    CONFIG_LOADED = True
except ImportError:
    CONFIG_LOADED = False
    PYTHON_VERSION = "3.11"
    DESKTOP_EXCLUDE = ["__pycache__", "scrips", ".pytest_cache", "build", "dist"]
    API_EXCLUDE = ["__pycache__", "*.pyc", ".pytest_cache", "build", "logs", "data/db/*.db"]
    USE_MIRROR = False
    PYTHON_MIRROR_URLS = {}
    USE_PIP_MIRROR = False
    PIP_MIRROR_URL = ""

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
PUBLISH_DIR = ROOT_DIR / "publish"
UI_DESKTOP_DIR = ROOT_DIR / "ui" / "desktop"
UI_API_DIR = ROOT_DIR / "ui" / "api"
UI_WEB_DIR = ROOT_DIR / "ui" / "web"
UZONCALC_DIR = ROOT_DIR / "uzoncalc"

# Python Embedded 下载链接（Windows）
PYTHON_EMBEDDED_URLS = {
    "3.11": "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip",
    "3.12": "https://www.python.org/ftp/python/3.12.3/python-3.12.3-embed-amd64.zip",
}


def print_step(step_name):
    """打印步骤信息"""
    print(f"\n{'='*60}")
    print(f"  {step_name}")
    print(f"{'='*60}\n")


def create_publish_dir(platform):
    """创建发布目录"""
    print_step(f"创建 {platform} 发布目录")
    
    platform_dir = PUBLISH_DIR / platform.lower()
    
    # 如果目录存在，先删除
    if platform_dir.exists():
        print(f"删除已存在的目录: {platform_dir}")
        shutil.rmtree(platform_dir)
    
    # 创建新目录
    platform_dir.mkdir(parents=True, exist_ok=True)
    print(f"创建目录: {platform_dir}")
    
    return platform_dir


def copy_desktop_files(platform_dir):
    """复制 desktop 文件"""
    print_step("复制 ui/desktop 文件")
    
    desktop_target = platform_dir / "desktop"
    desktop_target.mkdir(exist_ok=True)
    
    # 复制文件，排除某些目录
    exclude_dirs = set(DESKTOP_EXCLUDE)
    
    for item in UI_DESKTOP_DIR.iterdir():
        if item.name in exclude_dirs:
            continue
        
        target = desktop_target / item.name
        
        if item.is_file():
            print(f"复制文件: {item.name}")
            shutil.copy2(item, target)
        elif item.is_dir():
            print(f"复制目录: {item.name}")
            shutil.copytree(item, target, ignore=shutil.ignore_patterns("__pycache__"))


def download_python_embedded(platform_dir, python_version="3.11"):
    """下载并安装 Python Embedded 版本（仅 Windows）"""
    print_step(f"下载 Python {python_version} Embedded")
    
    # 选择下载链接
    if USE_MIRROR and python_version in PYTHON_MIRROR_URLS:
        url = PYTHON_MIRROR_URLS[python_version]
        print(f"使用镜像下载")
    else:
        url = PYTHON_EMBEDDED_URLS.get(python_version)
    
    if not url:
        raise ValueError(f"不支持的 Python 版本: {python_version}")
    
    python_dir = platform_dir / "python"
    python_dir.mkdir(exist_ok=True)
    
    zip_path = platform_dir / "python-embedded.zip"
    
    # 下载
    print(f"正在下载: {url}")
    try:
        urllib.request.urlretrieve(url, zip_path)
        print(f"下载完成: {zip_path}")
    except Exception as e:
        print(f"下载失败: {e}")
        if not USE_MIRROR:
            print("提示: 可以在 deploy_config.py 中启用镜像下载")
        raise
    
    # 解压
    print(f"正在解压到: {python_dir}")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(python_dir)
    
    # 删除 zip 文件
    zip_path.unlink()
    print("解压完成")
    
    # 修改 python311._pth 文件以启用 site-packages
    pth_files = list(python_dir.glob("python*._pth"))
    if pth_files:
        pth_file = pth_files[0]
        print(f"修改 {pth_file.name} 以启用 site-packages")
        
        content = pth_file.read_text()
        # 取消注释 import site
        content = content.replace("#import site", "import site")
        # 添加 Lib/site-packages 路径
        if "Lib/site-packages" not in content:
            content = "Lib/site-packages\n" + content
        pth_file.write_text(content)
    
    # 下载 get-pip.py
    print("下载 get-pip.py")
    get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
    get_pip_path = python_dir / "get-pip.py"
    urllib.request.urlretrieve(get_pip_url, get_pip_path)
    
    # 安装 pip
    print("安装 pip")
    python_exe = python_dir / "python.exe"
    subprocess.run([str(python_exe), str(get_pip_path)], check=True)
    
    # 删除 get-pip.py
    get_pip_path.unlink()
    
    return python_dir


def copy_project_files(platform_dir):
    """复制项目文件（uzoncalc, api）"""
    print_step("复制项目文件")
    
    # 复制 uzoncalc
    print("复制 uzoncalc")
    uzoncalc_target = platform_dir / "uzoncalc"
    if uzoncalc_target.exists():
        shutil.rmtree(uzoncalc_target)
    shutil.copytree(
        UZONCALC_DIR,
        uzoncalc_target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "*.egg-info", "cache")
    )
    
    # 复制 api
    print("复制 ui/api")
    api_target = platform_dir / "api"
    if api_target.exists():
        shutil.rmtree(api_target)
    
    # 构建排除模式
    ignore_patterns = list(set(API_EXCLUDE))
    
    shutil.copytree(
        UI_API_DIR,
        api_target,
        ignore=shutil.ignore_patterns(*ignore_patterns)
    )
    
    # 确保必要的目录存在
    (api_target / "data" / "calcs").mkdir(parents=True, exist_ok=True)
    (api_target / "data" / "db").mkdir(parents=True, exist_ok=True)
    (api_target / "logs").mkdir(parents=True, exist_ok=True)


def install_dependencies(platform_dir, platform):
    """安装依赖"""
    print_step("安装依赖")
    
    if platform.lower() == "windows":
        python_exe = platform_dir / "python" / "python.exe"
        pip_exe = platform_dir / "python" / "Scripts" / "pip.exe"
    else:
        # macOS 和 Linux 使用系统 Python
        python_exe = sys.executable
        pip_exe = "pip3"
    
    # 安装各个项目的依赖
    requirements_files = [
        (ROOT_DIR / "requirements.txt", "uzoncalc 核心依赖"),
        (platform_dir / "desktop" / "requirements.txt", "desktop 依赖"),
        (platform_dir / "api" / "requirements.txt", "api 依赖"),
    ]
    
    # 准备 pip 命令参数
    pip_args = [str(pip_exe), "install"]
    if USE_PIP_MIRROR and PIP_MIRROR_URL:
        pip_args.extend(["-i", PIP_MIRROR_URL])
        print(f"使用 pip 镜像: {PIP_MIRROR_URL}")
    
    for req_file, desc in requirements_files:
        if req_file.exists():
            print(f"\n安装 {desc}: {req_file}")
            cmd = pip_args + ["-r", str(req_file)]
            subprocess.run(cmd, check=True)
        else:
            print(f"警告: 未找到 {req_file}")


def create_start_script(platform_dir, platform):
    """创建启动脚本"""
    print_step("创建启动脚本")
    
    if platform.lower() == "windows":
        # 创建 start.bat
        script_path = platform_dir / "start.bat"
        script_content = """@echo off
chcp 65001 > nul
echo Starting UzonCalc Desktop Application...
echo.

set PYTHONPATH=%~dp0uzoncalc;%~dp0api;%PYTHONPATH%

cd /d "%~dp0desktop"
"%~dp0python\\python.exe" app.py

pause
"""
        script_path.write_text(script_content, encoding="utf-8")
        print(f"创建启动脚本: {script_path}")
        
    elif platform.lower() == "macos":
        # 创建 start.sh
        script_path = platform_dir / "start.sh"
        script_content = """#!/bin/bash
echo "Starting UzonCalc Desktop Application..."
echo

export PYTHONPATH="$(dirname "$0")/uzoncalc:$(dirname "$0")/api:$PYTHONPATH"

cd "$(dirname "$0")/desktop"
python3 app.py
"""
        script_path.write_text(script_content, encoding="utf-8")
        script_path.chmod(0o755)
        print(f"创建启动脚本: {script_path}")
        
    elif platform.lower() == "linux":
        # 创建 start.sh
        script_path = platform_dir / "start.sh"
        script_content = """#!/bin/bash
echo "Starting UzonCalc Desktop Application..."
echo

export PYTHONPATH="$(dirname "$0")/uzoncalc:$(dirname "$0")/api:$PYTHONPATH"

cd "$(dirname "$0")/desktop"
python3 app.py
"""
        script_path.write_text(script_content, encoding="utf-8")
        script_path.chmod(0o755)
        print(f"创建启动脚本: {script_path}")


def build_web_frontend(platform_dir):
    """构建 Web 前端"""
    print_step("构建 Web 前端")
    
    # 切换到 web 目录
    os.chdir(UI_WEB_DIR)
    
    # 执行 npm run build
    print("执行 npm run build")
    subprocess.run(["npm", "run", "build"], check=True, shell=True)
    
    # 复制构建文件到 api/data/www
    www_source = UI_WEB_DIR / "dist" / "spa"
    www_target = platform_dir / "api" / "data" / "www"
    
    if www_target.exists():
        shutil.rmtree(www_target)
    
    print(f"复制前端文件: {www_source} -> {www_target}")
    shutil.copytree(www_source, www_target)
    
    print("Web 前端构建完成")


def deploy(platform, python_version=None, skip_web_build=False):
    """执行部署"""
    # 如果没有指定版本，使用配置文件中的默认值
    if python_version is None:
        python_version = PYTHON_VERSION
    
    print(f"\n开始部署 UzonCalc Desktop - {platform} 平台")
    print(f"项目根目录: {ROOT_DIR}")
    if CONFIG_LOADED:
        print("✓ 已加载配置文件: deploy_config.py")
    
    # 1. 创建发布目录
    platform_dir = create_publish_dir(platform)
    
    # 2. 复制 desktop 文件
    copy_desktop_files(platform_dir)
    
    # 3. 下载 Python Embedded（仅 Windows）
    if platform.lower() == "windows":
        download_python_embedded(platform_dir, python_version)
    
    # 4. 复制项目文件
    copy_project_files(platform_dir)
    
    # 5. 安装依赖
    install_dependencies(platform_dir, platform)
    
    # 6. 创建启动脚本
    create_start_script(platform_dir, platform)
    
    # 7. 构建 Web 前端
    if not skip_web_build:
        build_web_frontend(platform_dir)
    else:
        print_step("跳过 Web 前端构建")
    
    # 8. 生成版本信息
    if HAS_VERSION_INFO:
        print_step("生成版本信息")
        version_info = generate_version_info(platform_dir, platform)
        print(f"版本: {version_info.get('version')}")
        if version_info.get('git'):
            print(f"Git: {version_info['git']['short_commit']} ({version_info['git']['branch']})")
    
    print_step("部署完成!")
    print(f"发布目录: {platform_dir}")
    print(f"\n启动应用:")
    if platform.lower() == "windows":
        print(f"  {platform_dir / 'start.bat'}")
    else:
        print(f"  {platform_dir / 'start.sh'}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="UzonCalc Desktop 部署脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python deploy.py --platform windows
  python deploy.py --platform macos --skip-web-build
  python deploy.py --platform linux --python-version 3.12
        """
    )
    
    parser.add_argument(
        "--platform",
        required=True,
        choices=["windows", "macos", "linux"],
        help="目标平台"
    )
    
    parser.add_argument(
        "--python-version",
        default="3.11",
        choices=["3.11", "3.12"],
        help="Python Embedded 版本 (仅 Windows, 默认: 3.11)"
    )
    
    parser.add_argument(
        "--skip-web-build",
        action="store_true",
        help="跳过 Web 前端构建"
    )
    
    args = parser.parse_args()
    
    try:
        deploy(args.platform, args.python_version, args.skip_web_build)
    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
