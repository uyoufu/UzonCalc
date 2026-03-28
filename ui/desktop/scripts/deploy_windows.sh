#!/usr/bin/env bash

echo "===================================="
echo "  UzonCalc Desktop 部署工具 (Windows)"
echo "===================================="
echo "提示：Windows 平台编译建议在 Windows 系统上运行此脚本。"
echo
echo -n "是否继续？[y/N] "
read -r confirm
if [[ ! "$confirm" =~ ^[yY]$ ]]; then
  echo "已取消。"
  exit 0
fi
echo

python deploy.py --platform windows

echo
echo "部署完成！按回车键退出..."
read
