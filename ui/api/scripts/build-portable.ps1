# ============================================
# 便携式打包脚本
# ============================================
# 功能：创建可分发的便携式应用包
# 不使用 PyInstaller，而是打包完整的运行环境
# ============================================

param(
    [string]$OutputName = "UzonCalc-Portable",
    [string]$PythonVersion = "3.11.9"
)

$ErrorActionPreference = "Stop"

# 路径配置
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
$DIST_DIR = Join-Path $PROJECT_ROOT "dist"
$OUTPUT_DIR = Join-Path $DIST_DIR $OutputName

function Write-Info {
    param([string]$message)
    Write-Host "[INFO] $message" -ForegroundColor Green
}

function Write-Step {
    param([string]$message)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $message -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

# ============================================
# 步骤 1: 设置嵌入式 Python
# ============================================

Write-Step "步骤 1: 设置嵌入式 Python 环境"

$setupScript = Join-Path $SCRIPT_DIR "setup-embedded-python.ps1"
if (Test-Path $setupScript) {
    & $setupScript -PythonVersion $PythonVersion
} else {
    Write-Error "未找到 setup-embedded-python.ps1"
    exit 1
}

# ============================================
# 步骤 2: 创建输出目录
# ============================================

Write-Step "步骤 2: 创建输出目录"

if (Test-Path $OUTPUT_DIR) {
    Write-Info "清理旧的输出目录..."
    Remove-Item -Recurse -Force $OUTPUT_DIR
}

New-Item -ItemType Directory -Path $OUTPUT_DIR | Out-Null
Write-Info "输出目录: $OUTPUT_DIR"

# ============================================
# 步骤 3: 复制必要文件
# ============================================

Write-Step "步骤 3: 复制项目文件"

# 要复制的目录和文件
$itemsToCopy = @(
    "app",
    "config",
    "data",
    "utils",
    "main.py",
    "requirements.txt",
    "python-embedded"
)

foreach ($item in $itemsToCopy) {
    $sourcePath = Join-Path $PROJECT_ROOT $item
    if (Test-Path $sourcePath) {
        Write-Info "复制: $item"
        
        if (Test-Path $sourcePath -PathType Container) {
            # 目录
            Copy-Item -Path $sourcePath -Destination $OUTPUT_DIR -Recurse -Force
        } else {
            # 文件
            Copy-Item -Path $sourcePath -Destination $OUTPUT_DIR -Force
        }
    } else {
        Write-Host "  跳过（不存在）: $item" -ForegroundColor Yellow
    }
}

# ============================================
# 步骤 4: 创建启动脚本
# ============================================

Write-Step "步骤 4: 创建启动脚本"

# Windows 批处理启动脚本
$startBat = @"
@echo off
chcp 65001 >nul
title UzonCalc API Server

echo ========================================
echo UzonCalc API 后台服务
echo ========================================
echo.

echo [信息] 启动服务...
echo.

cd /d "%~dp0"

REM 使用嵌入式 Python 启动
python-embedded\python.exe -m uvicorn main:app --host 127.0.0.1 --port 3346

pause
"@

$startBat | Out-File -FilePath (Join-Path $OUTPUT_DIR "启动服务.bat") -Encoding ASCII

# PowerShell 启动脚本（更强大）
$startPs1 = @"
# UzonCalc API 后台服务启动脚本
`$ErrorActionPreference = "Stop"

# 切换到脚本所在目录
Set-Location `$PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "UzonCalc API 后台服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查嵌入式 Python
`$pythonExe = Join-Path `$PSScriptRoot "python-embedded\python.exe"
if (-not (Test-Path `$pythonExe)) {
    Write-Host "[错误] 未找到 Python: `$pythonExe" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[信息] Python: `$pythonExe" -ForegroundColor Green
Write-Host "[信息] 启动服务..." -ForegroundColor Green
Write-Host ""

# 启动服务
& `$pythonExe -m uvicorn main:app --host 127.0.0.1 --port 3346 --log-level info

pause
"@

$startPs1 | Out-File -FilePath (Join-Path $OUTPUT_DIR "启动服务.ps1") -Encoding UTF8

# ============================================
# 步骤 5: 创建说明文档
# ============================================

Write-Step "步骤 5: 创建说明文档"

$readme = @"
# UzonCalc API - 便携式版本

## 简介

这是 UzonCalc API 的便携式版本，无需安装 Python 即可运行。

## 系统要求

- Windows 10/11 (64位)
- 至少 200MB 磁盘空间

## 使用方法

### 方法 1: 双击批处理文件（推荐新手）

直接双击 `启动服务.bat` 即可启动服务。

### 方法 2: PowerShell 脚本

右键点击 `启动服务.ps1`，选择"使用 PowerShell 运行"。

### 方法 3: 手动启动

```bash
cd /d <解压目录>
python-embedded\python.exe -m uvicorn main:app --host 127.0.0.1 --port 3346
```

## 访问方式

启动后，在浏览器中访问：

- API 文档: http://127.0.0.1:3346/docs
- 主页: http://127.0.0.1:3346/

## 停止服务

在命令行窗口中按 `Ctrl + C` 即可停止服务。

## 目录结构

```
UzonCalc-Portable/
├── python-embedded/     # 嵌入式 Python 环境
├── app/                 # 应用代码
├── config/              # 配置文件
├── data/                # 数据文件
├── main.py              # 主程序入口
├── 启动服务.bat         # Windows 启动脚本
├── 启动服务.ps1         # PowerShell 启动脚本
└── README.txt           # 本文件
```

## 注意事项

1. 首次运行可能需要几秒钟初始化数据库
2. 确保端口 3346 未被其他程序占用
3. 不要删除或修改 `python-embedded` 目录

## 故障排查

### 端口被占用

如果提示端口被占用，请：
1. 找到占用端口的程序并关闭
2. 或修改配置文件使用其他端口

### Python 未找到

确保 `python-embedded` 目录完整，如有问题请重新解压。

## 技术支持

如遇问题，请访问项目主页或联系技术支持。

---

版本: 1.0.0
日期: $(Get-Date -Format "yyyy-MM-dd")
"@

$readme | Out-File -FilePath (Join-Path $OUTPUT_DIR "README.txt") -Encoding UTF8

# ============================================
# 步骤 6: 清理不必要的文件
# ============================================

Write-Step "步骤 6: 清理不必要的文件"

$excludePatterns = @(
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".git",
    ".gitignore",
    "*.log"
)

foreach ($pattern in $excludePatterns) {
    Write-Info "清理: $pattern"
    Get-ChildItem -Path $OUTPUT_DIR -Filter $pattern -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

# ============================================
# 步骤 7: 计算大小
# ============================================

Write-Step "打包完成"

$size = (Get-ChildItem -Path $OUTPUT_DIR -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB

Write-Info "输出目录: $OUTPUT_DIR"
Write-Info "总大小: $([Math]::Round($size, 2)) MB"
Write-Host ""
Write-Host "后续步骤：" -ForegroundColor Cyan
Write-Host "  1. 测试运行: cd '$OUTPUT_DIR' && .\启动服务.bat"
Write-Host "  2. 压缩打包: 将整个 '$OutputName' 文件夹压缩为 .zip"
Write-Host "  3. 分发给用户: 用户解压后即可运行"
Write-Host ""
