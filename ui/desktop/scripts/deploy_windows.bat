@echo off
chcp 65001 > nul
echo ====================================
echo   UzonCalc Desktop 部署工具 (Windows)
echo ====================================
echo.

python deploy.py --platform windows

echo.
echo 部署完成！按任意键退出...
pause > nul
