"""
生成版本信息文件
"""

import json
from datetime import datetime
from pathlib import Path
import subprocess


def get_git_info():
    """获取 Git 信息"""
    try:
        # 获取当前分支
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        # 获取最后一次提交的 hash
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        # 获取短 hash
        short_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        # 获取最后一次提交的时间
        commit_time = subprocess.check_output(
            ["git", "log", "-1", "--format=%cd", "--date=iso"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        return {
            "branch": branch,
            "commit": commit_hash,
            "short_commit": short_hash,
            "commit_time": commit_time,
        }
    except:
        return None


def generate_version_info(platform_dir, platform, version="1.0.0"):
    """生成版本信息文件"""
    git_info = get_git_info()
    
    version_info = {
        "version": version,
        "platform": platform,
        "build_time": datetime.now().isoformat(),
        "git": git_info,
    }
    
    # 写入版本文件
    version_file = platform_dir / "version.json"
    with open(version_file, "w", encoding="utf-8") as f:
        json.dump(version_info, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 生成版本信息: {version_file}")
    return version_info


if __name__ == "__main__":
    # 测试
    info = get_git_info()
    if info:
        print("Git 信息:")
        print(json.dumps(info, indent=2))
    else:
        print("无法获取 Git 信息")
