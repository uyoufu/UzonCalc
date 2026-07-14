"""
打开系统文件管理器并定位到目标文件。
"""

import platform
import subprocess
from pathlib import Path


def show_in_file_explorer(target_file_path: str) -> None:
    """
    在系统文件管理器中显示目标文件。

    :param target_file_path: 目标文件路径
    """
    target_path = Path(target_file_path)
    if not target_path.exists():
        raise FileNotFoundError(f"File not found: {target_file_path}")

    target_path = target_path.resolve()

    system_name = platform.system()

    if system_name == "Windows":
        result = subprocess.run(
            ["explorer.exe", f"/select,{str(target_path)}"],
            check=False,
        )
        return

    if system_name == "Darwin":
        subprocess.run(["open", "-R", str(target_path)], check=True)
        return

    subprocess.run(["xdg-open", str(target_path.parent)], check=True)
