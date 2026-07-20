"""
打开系统文件管理器并定位到目标文件。
"""

import platform
import subprocess
from pathlib import Path


def show_in_file_explorer(target_file_path: str) -> None:
    """在系统文件管理器中显示目标文件或打开目标目录。

    Args:
        target_file_path: 目标文件或目录路径。

    Returns:
        None.

    Raises:
        FileNotFoundError: 目标路径不存在。
        subprocess.CalledProcessError: 系统文件管理器启动失败。
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

    explorer_target = target_path if target_path.is_dir() else target_path.parent
    subprocess.run(["xdg-open", str(explorer_target)], check=True)
