"""
清理发布目录脚本
"""

import argparse
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
PUBLISH_DIR = ROOT_DIR / "publish"


def clean_platform(platform):
    """清理指定平台的发布目录"""
    platform_dir = PUBLISH_DIR / platform.lower()
    
    if platform_dir.exists():
        print(f"正在清理目录: {platform_dir}")
        shutil.rmtree(platform_dir)
        print(f"✓ 已清理 {platform} 平台发布目录")
    else:
        print(f"目录不存在: {platform_dir}")


def clean_all():
    """清理所有发布目录"""
    if PUBLISH_DIR.exists():
        print(f"正在清理所有发布目录: {PUBLISH_DIR}")
        shutil.rmtree(PUBLISH_DIR)
        print("✓ 已清理所有发布目录")
    else:
        print(f"发布目录不存在: {PUBLISH_DIR}")


def main():
    parser = argparse.ArgumentParser(description="清理 UzonCalc Desktop 发布目录")
    
    parser.add_argument(
        "--platform",
        choices=["windows", "macos", "linux", "all"],
        help="要清理的平台 (all 表示清理所有平台)"
    )
    
    args = parser.parse_args()
    
    if not args.platform:
        parser.print_help()
        return
    
    if args.platform == "all":
        clean_all()
    else:
        clean_platform(args.platform)


if __name__ == "__main__":
    main()
